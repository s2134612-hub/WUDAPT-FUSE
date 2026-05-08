"""
Phase 6.5: 地理位置突破的物理机制分析

回答四个问题:
  1. UTCI 随距海岸 / 距山区距离的梯度有多陡？
  2. 距海岸、距山区、高程 三个特征各自单独的 Gini 贡献？
  3. 在每个 LCZ 大类内, UTCI vs 地理距离的 Pearson 相关多强？
  4. 沿海 vs 内陆, 哪个有更强的"夜间缓解"信号 (低 TSD/HDH)?

输出:
  results/phase6_5/distance_gradient.csv
  results/phase6_5/feature_decomposition.csv
  figures/fig09_geography_mechanism.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
from rasterio.enums import Resampling
from scipy.ndimage import distance_transform_edt
from scipy.stats import pearsonr, spearmanr
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.figure_style import apply_paper_style
apply_paper_style()

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.gini import gini_decomposition

log = get_logger("phase6_5")
RESULTS_P65 = RESULTS_DIR / "phase6_5"
RESULTS_P65.mkdir(parents=True, exist_ok=True)

LCZ_NAMES = {
    1: "Compact HR", 2: "Compact MR", 3: "Compact LR",
    4: "Open HR", 5: "Open MR", 6: "Open LR",
    8: "Large LR", 9: "Sparsely B", 10: "Heavy Ind"
}

# 距离 bins (km, Shenzhen 实际范围 0-12 km)
COAST_BINS = [0, 0.5, 1.0, 2.0, 4.0, 8.0, 20.0]
COAST_LABELS = ['0-0.5', '0.5-1', '1-2', '2-4', '4-8', '8+']
MOUNTAIN_BINS = [0, 0.5, 1.0, 2.0, 4.0, 8.0, 20.0]
MOUNTAIN_LABELS = ['0-0.5', '0.5-1', '1-2', '2-4', '4-8', '8+']


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 6.5: 地理位置物理机制深入分析")
    log.info("=" * 65)

    # === 1. 加载数据 (UTM 网格) ===
    log.info("\n[1] 加载数据")
    utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")
    umps_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc")

    # UTCI 重投影到 UTM
    template = xr.DataArray(
        np.zeros_like(umps_ds['lcz'].values, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': umps_ds.y.values, 'x': umps_ds.x.values}
    ).rio.write_crs("EPSG:32650")

    log.info("  UTCI 重投影到 UTM...")
    utci_data = {}
    for var in ['utci_mean', 'utci_max', 'tsd_strong', 'hdh']:
        da = xr.DataArray(
            utci_ds[var].values, dims=('y', 'x'),
            coords={'y': utci_ds.lat.values, 'x': utci_ds.lon.values}
        ).rio.write_crs("EPSG:4326")
        utci_data[var] = da.rio.reproject_match(
            template, resampling=Resampling.bilinear).values

    # 加载人口
    pop_da = rxr.open_rasterio(
        PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True
    ).squeeze()

    # 形状对齐
    h = min(pop_da.shape[0], umps_ds['lcz'].shape[0])
    w = min(pop_da.shape[1], umps_ds['lcz'].shape[1])
    pop_arr = pop_da.values[:h, :w]
    lcz_arr = umps_ds['lcz'].values[:h, :w]
    for k in utci_data:
        utci_data[k] = utci_data[k][:h, :w]

    log.info(f"  形状: {(h, w)}, LCZ valid: {(~np.isnan(lcz_arr)).sum():,}")

    # === 2. 计算距离特征 ===
    log.info("\n[2] 计算距离特征")
    water_mask = (lcz_arr == 17)
    mountain_mask = np.isin(lcz_arr, [11, 12])

    dist_coast = distance_transform_edt(~water_mask).astype(np.float32) * 0.1  # 转 km
    dist_mountain = distance_transform_edt(~mountain_mask).astype(np.float32) * 0.1
    elevation = (1.0 / (dist_mountain + 0.1))  # 高程代理

    log.info(f"  距海岸:     {dist_coast.min():.2f} – {dist_coast.max():.2f} km")
    log.info(f"  距山区:     {dist_mountain.min():.2f} – {dist_mountain.max():.2f} km")

    # === 3. 构建分析 DataFrame ===
    log.info("\n[3] 构建分析数据表")
    valid = (~np.isnan(lcz_arr)) & (~np.isnan(pop_arr)) & (pop_arr > 0) \
            & (lcz_arr <= 10) & (~np.isnan(utci_data['utci_mean']))

    df = pd.DataFrame({
        'lcz':         lcz_arr[valid].astype(int),
        'pop':         pop_arr[valid],
        'utci':        utci_data['utci_mean'][valid],
        'utci_max':    utci_data['utci_max'][valid],
        'tsd':         utci_data['tsd_strong'][valid],
        'hdh':         utci_data['hdh'][valid],
        'd_coast':     dist_coast[valid],
        'd_mountain':  dist_mountain[valid],
        'elevation':   elevation[valid],
    })
    df['name'] = df['lcz'].map(LCZ_NAMES)
    df['tsd_per_hdh'] = df['tsd'] / (df['hdh'] + 1e-9)
    log.info(f"  有效栅格: {len(df):,}")

    # === 4. 距离梯度分析 ===
    log.info("\n[4] UTCI 沿距离梯度变化")

    # Coast bins
    df['coast_bin'] = pd.cut(df['d_coast'], bins=COAST_BINS,
                              labels=COAST_LABELS,
                              include_lowest=True)
    coast_stats = df.groupby('coast_bin').agg(
        utci_mean=('utci', 'mean'),
        utci_std=('utci', 'std'),
        hdh_mean=('hdh', 'mean'),
        n_cells=('utci', 'size'),
        pop_total=('pop', 'sum'),
    ).reset_index()
    log.info("\n  按距海岸分箱（全部 LCZ）:")
    log.info(coast_stats.to_string(index=False))

    # Mountain bins
    df['mountain_bin'] = pd.cut(df['d_mountain'], bins=MOUNTAIN_BINS,
                                  labels=MOUNTAIN_LABELS,
                                  include_lowest=True)
    mountain_stats = df.groupby('mountain_bin').agg(
        utci_mean=('utci', 'mean'),
        utci_std=('utci', 'std'),
        hdh_mean=('hdh', 'mean'),
        n_cells=('utci', 'size'),
        pop_total=('pop', 'sum'),
    ).reset_index()
    log.info("\n  按距山区分箱（全部 LCZ）:")
    log.info(mountain_stats.to_string(index=False))

    coast_stats.to_csv(RESULTS_P65 / "coast_distance_gradient.csv", index=False)
    mountain_stats.to_csv(RESULTS_P65 / "mountain_distance_gradient.csv", index=False)

    # === 5. 类内相关性（核心机制证据）===
    log.info("\n[5] 类内 UTCI vs 距离 相关性")
    correlations = []
    for lcz_id in sorted(df['lcz'].unique()):
        sub = df[df['lcz'] == lcz_id]
        if len(sub) < 30:
            continue
        r_coast, _ = pearsonr(sub['utci'], sub['d_coast'])
        r_mountain, _ = pearsonr(sub['utci'], sub['d_mountain'])
        r_elev, _ = pearsonr(sub['utci'], sub['elevation'])
        correlations.append({
            'lcz_id': lcz_id,
            'name': LCZ_NAMES.get(lcz_id, ''),
            'n_cells': len(sub),
            'r_coast': r_coast,
            'r_mountain': r_mountain,
            'r_elevation': r_elev,
            'mean_utci': sub['utci'].mean(),
        })
    df_corr = pd.DataFrame(correlations)
    df_corr.to_csv(RESULTS_P65 / "within_lcz_correlation.csv", index=False)

    log.info(f"\n  类内 UTCI vs 距离 Pearson 相关:")
    log.info(f"  {'LCZ':<3} {'name':<22} {'r_coast':>10} {'r_mountain':>11} {'r_elev':>10}")
    log.info("  " + "-" * 65)
    for _, r in df_corr.iterrows():
        log.info(f"  {int(r['lcz_id']):<3d} {r['name'][:20]:<22} "
                 f"{r['r_coast']:>10.3f} {r['r_mountain']:>11.3f} "
                 f"{r['r_elevation']:>10.3f}")

    # === 6. 单特征 Gini 分解 ===
    log.info("\n[6] 单特征 Gini 贡献分解")

    feature_results = []
    for feat_name, feat_label in [
        ('d_coast',     'Coast only'),
        ('d_mountain',  'Mountain only'),
        ('elevation',   'Elevation only'),
        # 二维组合
        ('d_coast+d_mountain', 'Coast + Mountain'),
        # 全 3 维 (前面已知 +10.81)
        ('all_geo',     'All 3 (Coast+Mountain+Elev)'),
    ]:
        log.info(f"\n  方案: {feat_label}")

        # 选定特征
        if feat_name == 'd_coast+d_mountain':
            features = ['d_coast', 'd_mountain']
        elif feat_name == 'all_geo':
            features = ['d_coast', 'd_mountain', 'elevation']
        else:
            features = [feat_name]

        # 对每个 LCZ 单独聚类
        subcat_grid = np.full(len(df), np.nan)
        n_subs_total = 0
        for lcz_id in sorted(df['lcz'].unique()):
            mask = (df['lcz'] == lcz_id).values
            if mask.sum() < 50:
                continue
            X = df.loc[mask, features].values
            X_std = StandardScaler().fit_transform(X)

            # 选 K
            best_k, best_score = 2, -np.inf
            for k in range(2, 6):
                if mask.sum() < k * 5:
                    continue
                try:
                    km = KMeans(n_clusters=k, random_state=42, n_init=10)
                    lbl = km.fit_predict(X_std)
                    if len(set(lbl)) < 2:
                        continue
                    inertia_per_cluster = km.inertia_ / k
                    score = -inertia_per_cluster   # 简化：越小越好
                    if score > best_score:
                        best_k, best_score = k, score
                except Exception:
                    continue

            km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            labels = km.fit_predict(X_std)

            # 全局编码
            subcat_grid[mask] = lcz_id * 10 + labels
            n_subs_total += best_k

        df_t = df.copy()
        df_t['subcat'] = subcat_grid
        df_t = df_t[~np.isnan(df_t['subcat'])]
        df_t['subcat'] = df_t['subcat'].astype(int)

        decomp_lcz = gini_decomposition(df_t, 'hdh', 'pop', 'lcz')
        decomp_sub = gini_decomposition(df_t, 'hdh', 'pop', 'subcat')

        within_lcz = decomp_lcz['within_share'] * 100
        within_sub = decomp_sub['within_share'] * 100
        reduction = within_lcz - within_sub

        log.info(f"    亚类数: {n_subs_total}")
        log.info(f"    G_within (LCZ):    {within_lcz:.2f}%")
        log.info(f"    G_within (Subcat): {within_sub:.2f}%")
        log.info(f"    减少:              {reduction:+.2f} pp")

        feature_results.append({
            'feature_set': feat_label,
            'n_features': len(features),
            'n_subcategories': n_subs_total,
            'G_within_lcz': within_lcz,
            'G_within_sub': within_sub,
            'reduction_pp': reduction,
        })

    df_feat = pd.DataFrame(feature_results)
    df_feat.to_csv(RESULTS_P65 / "feature_decomposition.csv", index=False)

    log.info("\n  单特征贡献分解:")
    log.info(df_feat.to_string(index=False))

    # === 7. 沿海 vs 内陆 昼夜代理 ===
    log.info("\n[7] 沿海 vs 内陆 昼夜模式代理（TSD / HDH 比例）")

    coast_inland = df.copy()
    coast_inland['region'] = pd.cut(
        coast_inland['d_coast'], bins=[0, 1, 3, 100],
        labels=['Coastal (<1 km)', 'Mid (1-3 km)', 'Inland (>3 km)'],
        include_lowest=True
    )
    region_stats = coast_inland.groupby('region').agg(
        utci_mean=('utci', 'mean'),
        tsd_mean=('tsd', 'mean'),
        hdh_mean=('hdh', 'mean'),
        tsd_per_hdh=('tsd_per_hdh', 'mean'),
        n_cells=('utci', 'size'),
    ).reset_index()
    log.info("\n  按距海岸分区:")
    log.info(region_stats.to_string(index=False))

    # === 8. Fig 8: 物理机制可视化 ===
    log.info("\n[8] 生成 Fig 8")
    fig = plt.figure(figsize=(15, 9), dpi=120)
    gs = fig.add_gridspec(2, 6, wspace=0.55, hspace=0.42,
                           left=0.06, right=0.97, top=0.92, bottom=0.08)

    # (a) UTCI 沿海岸距离梯度（按主要 LCZ 分线）
    ax_a = fig.add_subplot(gs[0, 0:2])
    important_lczs = [2, 4, 6, 8, 9]
    colors_lcz = plt.cm.tab10(np.arange(len(important_lczs)) / len(important_lczs))
    for lcz_id, c in zip(important_lczs, colors_lcz):
        sub = df[df['lcz'] == lcz_id]
        if len(sub) < 100:
            continue
        bin_means = sub.groupby('coast_bin', observed=True)['utci'].agg(['mean', 'std'])
        x = np.arange(len(bin_means))
        ax_a.errorbar(x, bin_means['mean'], yerr=bin_means['std'],
                       label=f"LCZ {lcz_id}", color=c, linewidth=1.5,
                       marker='o', markersize=5, capsize=2)
    ax_a.set_xticks(range(len(COAST_LABELS)))
    ax_a.set_xticklabels(COAST_LABELS, fontsize=8)
    ax_a.set_xlabel('Distance to coast (km)')
    ax_a.set_ylabel('Mean UTCI (°C)')
    ax_a.set_title('(a) UTCI gradient by coast distance',
                    fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='best', fontsize=8, ncol=1)
    ax_a.grid(alpha=0.3)

    # (b) UTCI 沿山区距离梯度
    ax_b = fig.add_subplot(gs[0, 2:4])
    for lcz_id, c in zip(important_lczs, colors_lcz):
        sub = df[df['lcz'] == lcz_id]
        if len(sub) < 100:
            continue
        bin_means = sub.groupby('mountain_bin', observed=True)['utci'].agg(['mean', 'std'])
        x = np.arange(len(bin_means))
        ax_b.errorbar(x, bin_means['mean'], yerr=bin_means['std'],
                       label=f"LCZ {lcz_id}", color=c, linewidth=1.5,
                       marker='s', markersize=5, capsize=2)
    ax_b.set_xticks(range(len(MOUNTAIN_LABELS)))
    ax_b.set_xticklabels(MOUNTAIN_LABELS, fontsize=8)
    ax_b.set_xlabel('Distance to mountain (km)')
    ax_b.set_ylabel('Mean UTCI (°C)')
    ax_b.set_title('(b) UTCI gradient by mountain distance',
                    fontsize=11, fontweight='bold', loc='left')
    ax_b.legend(loc='best', fontsize=8, ncol=1)
    ax_b.grid(alpha=0.3)

    # (c) 类内 Pearson r 热图
    ax_c = fig.add_subplot(gs[0, 4:6])
    feat_labels_c = ['r(coast)', 'r(mountain)', 'r(elevation)']
    M = df_corr[['r_coast', 'r_mountain', 'r_elevation']].values
    im = ax_c.imshow(M, cmap='RdBu_r', vmin=-0.6, vmax=0.6, aspect='auto')
    ax_c.set_xticks(range(len(feat_labels_c)))
    ax_c.set_xticklabels(feat_labels_c, rotation=15, fontsize=8)
    ax_c.set_yticks(range(len(df_corr)))
    ax_c.set_yticklabels([f"LCZ {int(r['lcz_id'])}" for _, r in df_corr.iterrows()],
                          fontsize=8)
    ax_c.set_title('(c) Within-LCZ Pearson r (UTCI ~ distance)',
                    fontsize=11, fontweight='bold', loc='left')
    cbar = plt.colorbar(im, ax=ax_c, fraction=0.04, pad=0.02)
    cbar.set_label('Pearson r', fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            text_color = 'white' if abs(M[i, j]) > 0.4 else 'black'
            ax_c.text(j, i, f"{M[i, j]:+.2f}",
                       ha='center', va='center',
                       fontsize=7, color=text_color)

    # (d) 单特征 Gini 贡献分解
    ax_d = fig.add_subplot(gs[1, 0:3])
    labels_d = df_feat['feature_set'].values
    reductions_d = df_feat['reduction_pp'].values
    colors_d = ['#5e9bd1', '#8ab37e', '#c47e5e', '#7a5d8d', '#cc0000']
    bars = ax_d.bar(range(len(labels_d)), reductions_d,
                     color=colors_d, edgecolor='black')
    for i, val in enumerate(reductions_d):
        ax_d.text(i, val + 0.2, f'{val:+.2f}\npp',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_d.axhline(5, color='red', linestyle='--', linewidth=1.5,
                  label='5 pp threshold')
    ax_d.set_xticks(range(len(labels_d)))
    ax_d.set_xticklabels(labels_d, rotation=12, fontsize=8.5, ha='right')
    ax_d.set_ylabel('Within-class Gini reduction (pp)')
    ax_d.set_title('(d) Single-feature Gini contribution decomposition',
                    fontsize=11, fontweight='bold', loc='left')
    ax_d.legend(loc='upper left', fontsize=9)
    ax_d.grid(axis='y', alpha=0.3)

    # (e) Coastal vs Mid vs Inland — UTCI / TSD / HDH 对比
    ax_e = fig.add_subplot(gs[1, 3:6])
    metrics_e = ['utci_mean', 'tsd_mean', 'hdh_mean']
    metric_labels = ['UTCI mean (°C)', 'TSD>32 (h)', 'HDH (°C·h)']
    region_data = [region_stats['utci_mean'].values,
                    region_stats['tsd_mean'].values,
                    region_stats['hdh_mean'].values]
    x = np.arange(len(region_stats))
    width = 0.27

    # 用次坐标轴显示不同尺度
    ax_e.bar(x - width, region_data[0], width, label='UTCI mean',
              color='#fc8d59', edgecolor='black')
    ax_e2 = ax_e.twinx()
    ax_e2.bar(x, region_data[1], width, label='TSD>32',
               color='#e6550d', edgecolor='black')
    ax_e2.bar(x + width, region_data[2] / 100, width, label='HDH/100',
               color='#a63603', edgecolor='black')

    ax_e.set_xticks(x)
    region_labels_actual = [str(r) for r in region_stats['region'].values]
    ax_e.set_xticklabels(region_labels_actual, fontsize=8)
    ax_e.set_ylabel('UTCI mean (°C)', color='#fc8d59')
    ax_e2.set_ylabel('TSD (h) / HDH/100 (°C·h)', color='#a63603')
    ax_e.set_title('(e) Coastal vs inland exposure ladder',
                    fontsize=11, fontweight='bold', loc='left')

    # 图例
    h1, l1 = ax_e.get_legend_handles_labels()
    h2, l2 = ax_e2.get_legend_handles_labels()
    ax_e.legend(h1 + h2, l1 + l2, loc='upper left', fontsize=8)
    ax_e.grid(axis='y', alpha=0.3)

    plt.suptitle('Phase 6.5: Physical Mechanism — Coast and Mountain Drive Within-Class Heat Inequality',
                  fontsize=12, fontweight='bold', y=0.97)

    fig_path = FIGURES_DIR / "fig09_geography_mechanism.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    log.info(f"\n  图表保存: {fig_path}")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px, "
              f"{fig_path.stat().st_size/1e3:.1f} KB")

    log.info("\n🎉 Phase 6.5 完成！")


if __name__ == "__main__":
    main()
