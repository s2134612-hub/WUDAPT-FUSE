"""
Phase 7 (L1): 昼夜物理机制验证

测试假设:
  H1: 海陆风 → Coast 效应在白天更强
  H2: 下沉冷气流 → Mountain 效应在夜间更强
  H3: 阴影 → Mountain 在白天也有效（但不如夜间）

输入:
  data/processed/shenzhen_utci_100m_jul_day_summary.nc
  data/processed/shenzhen_utci_100m_jul_night_summary.nc

输出:
  results/phase7/diurnal_gini_comparison.csv
  results/phase7/diurnal_correlation.csv
  figures/fig10_diurnal_mechanism.png
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
from scipy.stats import pearsonr
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

log = get_logger("phase7_diurnal")
RESULTS_P7 = RESULTS_DIR / "phase7"
RESULTS_P7.mkdir(parents=True, exist_ok=True)

LCZ_NAMES = {
    1: "Compact HR", 2: "Compact MR", 3: "Compact LR",
    4: "Open HR", 5: "Open MR", 6: "Open LR",
    8: "Large LR", 9: "Sparsely B", 10: "Heavy Ind"
}


def load_summary_to_utm(period):
    """加载 day/night summary 并重投影到 UTM"""
    src_path = PROCESSED_DATA_DIR / f"shenzhen_utci_100m_jul_{period}_summary.nc"
    ds = xr.open_dataset(src_path)

    # 先要 UTM 模板
    umps_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc")
    template = xr.DataArray(
        np.zeros_like(umps_ds['lcz'].values, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': umps_ds.y.values, 'x': umps_ds.x.values}
    ).rio.write_crs("EPSG:32650")

    out = {}
    for var in ['utci_mean', 'utci_max', 'tsd_strong', 'hdh']:
        da = xr.DataArray(
            ds[var].values, dims=('y', 'x'),
            coords={'y': ds.lat.values, 'x': ds.lon.values}
        ).rio.write_crs("EPSG:4326")
        out[var] = da.rio.reproject_match(
            template, resampling=Resampling.bilinear).values

    return out, umps_ds


def cluster_with_features(df, features, lcz_col='lcz'):
    """对每个 LCZ 类用指定特征 k-means"""
    subcat = np.full(len(df), np.nan)
    n_total = 0
    for lcz_id in sorted(df[lcz_col].unique()):
        mask = (df[lcz_col] == lcz_id).values
        if mask.sum() < 50:
            continue
        X = df.loc[mask, features].values
        X_std = StandardScaler().fit_transform(X)

        # 选 K (用 elbow proxy: lowest inertia)
        best_k = 5  # 固定 K=5 简化（保证可比）
        if mask.sum() < 25:
            best_k = 2

        km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = km.fit_predict(X_std)

        subcat[mask] = lcz_id * 10 + labels
        n_total += best_k

    return subcat, n_total


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 7 (L1): 昼夜物理机制验证")
    log.info("=" * 65)

    # === 1. 加载 day / night summary ===
    log.info("\n[1] 加载昼夜 UTCI summaries 并对齐到 UTM")
    day_data, umps_ds = load_summary_to_utm('day')
    night_data, _ = load_summary_to_utm('night')
    log.info(f"  Day  mean: {np.nanmean(day_data['utci_mean']):.2f} °C")
    log.info(f"  Night mean: {np.nanmean(night_data['utci_mean']):.2f} °C")
    log.info(f"  Δ (day - night): {np.nanmean(day_data['utci_mean']) - np.nanmean(night_data['utci_mean']):.2f} °C")

    # === 2. 加载几何特征 ===
    log.info("\n[2] 计算地理特征")
    pop_da = rxr.open_rasterio(
        PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True
    ).squeeze()
    h = min(pop_da.shape[0], umps_ds['lcz'].shape[0])
    w = min(pop_da.shape[1], umps_ds['lcz'].shape[1])
    pop_arr = pop_da.values[:h, :w]
    lcz_arr = umps_ds['lcz'].values[:h, :w]

    # day/night 数据也对齐
    for d in [day_data, night_data]:
        for k in d:
            d[k] = d[k][:h, :w]

    # 距离特征
    water_mask = (lcz_arr == 17)
    mountain_mask = np.isin(lcz_arr, [11, 12])
    dist_coast = distance_transform_edt(~water_mask).astype(np.float32) * 0.1  # km
    dist_mountain = distance_transform_edt(~mountain_mask).astype(np.float32) * 0.1

    # === 3. 构建 day & night DataFrame ===
    valid = (~np.isnan(lcz_arr)) & (~np.isnan(pop_arr)) & (pop_arr > 0) \
            & (lcz_arr <= 10) & (~np.isnan(day_data['utci_mean']))

    df_day = pd.DataFrame({
        'lcz': lcz_arr[valid].astype(int),
        'pop': pop_arr[valid],
        'utci': day_data['utci_mean'][valid],
        'hdh':  day_data['hdh'][valid],
        'tsd':  day_data['tsd_strong'][valid],
        'd_coast':    dist_coast[valid],
        'd_mountain': dist_mountain[valid],
    })
    df_night = df_day.copy()
    df_night['utci'] = night_data['utci_mean'][valid]
    df_night['hdh']  = night_data['hdh'][valid]
    df_night['tsd']  = night_data['tsd_strong'][valid]

    log.info(f"  有效栅格: {len(df_day):,}")

    # === 4. 类内 Pearson 相关 (day vs night) ===
    log.info("\n[3] 类内 UTCI vs 距离 Pearson 相关 (day vs night)")
    correlations = []
    for lcz_id in sorted(df_day['lcz'].unique()):
        sub_d = df_day[df_day['lcz'] == lcz_id]
        sub_n = df_night[df_night['lcz'] == lcz_id]
        if len(sub_d) < 30:
            continue
        r_coast_day, _ = pearsonr(sub_d['utci'], sub_d['d_coast'])
        r_coast_night, _ = pearsonr(sub_n['utci'], sub_n['d_coast'])
        r_mtn_day, _ = pearsonr(sub_d['utci'], sub_d['d_mountain'])
        r_mtn_night, _ = pearsonr(sub_n['utci'], sub_n['d_mountain'])
        correlations.append({
            'lcz_id': lcz_id, 'name': LCZ_NAMES.get(lcz_id, ''),
            'n_cells': len(sub_d),
            'r_coast_day': r_coast_day, 'r_coast_night': r_coast_night,
            'r_mountain_day': r_mtn_day, 'r_mountain_night': r_mtn_night,
        })
    df_corr = pd.DataFrame(correlations)
    df_corr.to_csv(RESULTS_P7 / "diurnal_correlation.csv", index=False)

    log.info(f"\n  类内 r 表 (按 LCZ):")
    log.info(f"  {'LCZ':<3} {'name':<22} {'r_coast_day':>12} {'r_coast_nt':>11} "
             f"{'r_mtn_day':>10} {'r_mtn_nt':>10}")
    log.info("  " + "-" * 75)
    for _, r in df_corr.iterrows():
        log.info(f"  {int(r['lcz_id']):<3d} {r['name'][:20]:<22} "
                 f"{r['r_coast_day']:>+12.3f} {r['r_coast_night']:>+11.3f} "
                 f"{r['r_mountain_day']:>+10.3f} {r['r_mountain_night']:>+10.3f}")

    # === 5. day / night Gini 减少对比 ===
    log.info("\n[4] day vs night Gini 减少 (Coast/Mountain/Both)")

    schemes = {
        'Coast only':    ['d_coast'],
        'Mountain only': ['d_mountain'],
        'Coast+Mountain': ['d_coast', 'd_mountain'],
    }

    gini_results = []
    for sch_name, feats in schemes.items():
        for period, df_p in [('day', df_day), ('night', df_night)]:
            subcat, n_subs = cluster_with_features(df_p, feats)
            df_t = df_p.copy()
            df_t['subcat'] = subcat
            df_t = df_t[~np.isnan(df_t['subcat'])]
            df_t['subcat'] = df_t['subcat'].astype(int)

            decomp_lcz = gini_decomposition(df_t, 'hdh', 'pop', 'lcz')
            decomp_sub = gini_decomposition(df_t, 'hdh', 'pop', 'subcat')
            within_lcz = decomp_lcz['within_share'] * 100
            within_sub = decomp_sub['within_share'] * 100
            reduction = within_lcz - within_sub

            log.info(f"  {sch_name:<18s} {period:>5s}: "
                     f"reduction = {reduction:+.2f} pp "
                     f"(within {within_lcz:.1f}% -> {within_sub:.1f}%)")

            gini_results.append({
                'scheme': sch_name,
                'period': period,
                'n_subcategories': n_subs,
                'G_within_lcz': within_lcz,
                'G_within_sub': within_sub,
                'reduction_pp': reduction,
                'G_total': decomp_sub['G_total'],
            })

    df_gini = pd.DataFrame(gini_results)
    df_gini.to_csv(RESULTS_P7 / "diurnal_gini_comparison.csv", index=False)

    # === 6. 物理机制判定 ===
    log.info("\n[5] 物理机制判定")

    coast_day = df_gini[(df_gini['scheme']=='Coast only') & (df_gini['period']=='day')]['reduction_pp'].values[0]
    coast_night = df_gini[(df_gini['scheme']=='Coast only') & (df_gini['period']=='night')]['reduction_pp'].values[0]
    mtn_day = df_gini[(df_gini['scheme']=='Mountain only') & (df_gini['period']=='day')]['reduction_pp'].values[0]
    mtn_night = df_gini[(df_gini['scheme']=='Mountain only') & (df_gini['period']=='night')]['reduction_pp'].values[0]

    log.info(f"\n  Coast effect:    day {coast_day:+.2f} pp, night {coast_night:+.2f} pp, "
             f"day/night ratio = {coast_day/max(coast_night,0.01):.2f}×")
    log.info(f"  Mountain effect: day {mtn_day:+.2f} pp, night {mtn_night:+.2f} pp, "
             f"day/night ratio = {mtn_day/max(mtn_night,0.01):.2f}×")

    log.info(f"\n  H1 (Sea breeze, day > night for coast):")
    if coast_day > coast_night:
        log.info(f"    ✓ 验证: Coast 日间 ({coast_day:.2f}) > 夜间 ({coast_night:.2f})")
    else:
        log.info(f"    ✗ 反驳: Coast 夜间 ({coast_night:.2f}) > 日间 ({coast_day:.2f})")
        log.info(f"    可能机制: 海洋热惯性 / 夜间海风延迟")

    log.info(f"\n  H2 (Katabatic, night > day for mountain):")
    if mtn_night > mtn_day:
        log.info(f"    ✓ 验证: Mountain 夜间 ({mtn_night:.2f}) > 日间 ({mtn_day:.2f})")
    else:
        log.info(f"    ✗ 反驳: Mountain 日间 ({mtn_day:.2f}) > 夜间 ({mtn_night:.2f})")
        log.info(f"    可能机制: 阴影主导 / 蒸散冷却 (白天)")

    # === 7. Fig 9: 昼夜物理机制可视化 ===
    log.info("\n[6] 生成 Fig 9")
    fig = plt.figure(figsize=(15, 8.5), dpi=120)
    gs = fig.add_gridspec(2, 6, wspace=0.55, hspace=0.45,
                           left=0.06, right=0.97, top=0.91, bottom=0.10)

    # (a) day/night Gini 减少柱状图
    ax_a = fig.add_subplot(gs[0, 0:3])
    sch_names = ['Coast only', 'Mountain only', 'Coast+Mountain']
    day_red = df_gini[df_gini['period']=='day'].set_index('scheme').loc[sch_names, 'reduction_pp'].values
    night_red = df_gini[df_gini['period']=='night'].set_index('scheme').loc[sch_names, 'reduction_pp'].values

    x = np.arange(len(sch_names))
    width = 0.35
    bars_d = ax_a.bar(x - width/2, day_red, width, label='Day (SHT 08-20)',
                       color='#fc8d59', edgecolor='black')
    bars_n = ax_a.bar(x + width/2, night_red, width, label='Night (SHT 20-08)',
                       color='#225ea8', edgecolor='black')
    for bar, val in zip(bars_d, day_red):
        ax_a.text(bar.get_x()+bar.get_width()/2, val+0.2,
                   f'{val:+.1f}', ha='center', va='bottom',
                   fontsize=9, fontweight='bold')
    for bar, val in zip(bars_n, night_red):
        ax_a.text(bar.get_x()+bar.get_width()/2, val+0.2,
                   f'{val:+.1f}', ha='center', va='bottom',
                   fontsize=9, fontweight='bold')
    ax_a.axhline(5, color='red', linestyle='--', linewidth=1.5,
                  label='5 pp threshold')
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(sch_names, fontsize=9)
    ax_a.set_ylabel('Within-class Gini reduction (pp)')
    ax_a.set_title('(a) Day vs Night Gini reduction by feature',
                    fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='upper left', fontsize=9)
    ax_a.grid(axis='y', alpha=0.3)

    # (b) 类内相关性热图 (day)
    ax_b = fig.add_subplot(gs[0, 3:5])
    M_day = df_corr[['r_coast_day', 'r_mountain_day']].values
    im_b = ax_b.imshow(M_day, cmap='RdBu_r', vmin=-0.6, vmax=0.6, aspect='auto')
    ax_b.set_xticks(range(2))
    ax_b.set_xticklabels(['r(coast)', 'r(mountain)'], fontsize=9)
    ax_b.set_yticks(range(len(df_corr)))
    ax_b.set_yticklabels([f"LCZ {int(r['lcz_id'])}" for _, r in df_corr.iterrows()],
                          fontsize=8)
    ax_b.set_title('(b) Day  $r$(UTCI ~ distance)',
                    fontsize=11, fontweight='bold', loc='left')
    cbar = plt.colorbar(im_b, ax=ax_b, fraction=0.06, pad=0.02)
    cbar.set_label('Pearson r', fontsize=8)
    cbar.ax.tick_params(labelsize=7)
    for i in range(M_day.shape[0]):
        for j in range(M_day.shape[1]):
            text_color = 'white' if abs(M_day[i, j]) > 0.4 else 'black'
            ax_b.text(j, i, f"{M_day[i, j]:+.2f}",
                       ha='center', va='center',
                       fontsize=7, color=text_color)

    # (c) 类内相关性热图 (night)
    ax_c = fig.add_subplot(gs[0, 5:6])
    M_night = df_corr[['r_coast_night', 'r_mountain_night']].values
    im_c = ax_c.imshow(M_night, cmap='RdBu_r', vmin=-0.6, vmax=0.6, aspect='auto')
    ax_c.set_xticks(range(2))
    ax_c.set_xticklabels(['r(coast)', 'r(mountain)'], fontsize=9)
    ax_c.set_yticks(range(len(df_corr)))
    ax_c.set_yticklabels([f"LCZ {int(r['lcz_id'])}" for _, r in df_corr.iterrows()],
                          fontsize=8)
    ax_c.set_title('(c) Night  $r$',
                    fontsize=11, fontweight='bold', loc='left')
    for i in range(M_night.shape[0]):
        for j in range(M_night.shape[1]):
            text_color = 'white' if abs(M_night[i, j]) > 0.4 else 'black'
            ax_c.text(j, i, f"{M_night[i, j]:+.2f}",
                       ha='center', va='center',
                       fontsize=7, color=text_color)

    # (d) day vs night UTCI 对比 (沿距海岸 bins)
    ax_d = fig.add_subplot(gs[1, 0:3])
    coast_bins = [0, 0.5, 1.0, 2.0, 4.0, 8.0]
    coast_labels = ['0-0.5', '0.5-1', '1-2', '2-4', '4-8']

    df_day['coast_bin'] = pd.cut(df_day['d_coast'], bins=coast_bins,
                                   labels=coast_labels, include_lowest=True)
    df_night['coast_bin'] = pd.cut(df_night['d_coast'], bins=coast_bins,
                                     labels=coast_labels, include_lowest=True)

    bin_day = df_day.groupby('coast_bin', observed=True)['utci'].mean()
    bin_night = df_night.groupby('coast_bin', observed=True)['utci'].mean()

    x_b = np.arange(len(coast_labels))
    ax_d.plot(x_b, bin_day, '-o', color='#fc8d59',
               linewidth=2, markersize=8, label='Day mean')
    ax_d.plot(x_b, bin_night, '-s', color='#225ea8',
               linewidth=2, markersize=8, label='Night mean')
    ax_d.set_xticks(x_b)
    ax_d.set_xticklabels(coast_labels, fontsize=9)
    ax_d.set_xlabel('Distance to coast (km)')
    ax_d.set_ylabel('Mean UTCI (°C)')
    ax_d.set_title('(d) Coast distance gradient: day vs night',
                    fontsize=11, fontweight='bold', loc='left')
    ax_d.legend(loc='best', fontsize=9)
    ax_d.grid(alpha=0.3)

    # (e) day vs night UTCI 对比 (沿距山区 bins)
    ax_e = fig.add_subplot(gs[1, 3:6])
    df_day['mtn_bin'] = pd.cut(df_day['d_mountain'], bins=coast_bins,
                                 labels=coast_labels, include_lowest=True)
    df_night['mtn_bin'] = pd.cut(df_night['d_mountain'], bins=coast_bins,
                                   labels=coast_labels, include_lowest=True)

    bin_day_m = df_day.groupby('mtn_bin', observed=True)['utci'].mean()
    bin_night_m = df_night.groupby('mtn_bin', observed=True)['utci'].mean()

    ax_e.plot(x_b, bin_day_m, '-o', color='#fc8d59',
               linewidth=2, markersize=8, label='Day mean')
    ax_e.plot(x_b, bin_night_m, '-s', color='#225ea8',
               linewidth=2, markersize=8, label='Night mean')
    ax_e.set_xticks(x_b)
    ax_e.set_xticklabels(coast_labels, fontsize=9)
    ax_e.set_xlabel('Distance to mountain (km)')
    ax_e.set_ylabel('Mean UTCI (°C)')
    ax_e.set_title('(e) Mountain distance gradient: day vs night',
                    fontsize=11, fontweight='bold', loc='left')
    ax_e.legend(loc='best', fontsize=9)
    ax_e.grid(alpha=0.3)

    plt.suptitle('Phase 7: Diurnal Validation of Physical Mechanism',
                  fontsize=12, fontweight='bold', y=0.97)

    fig_path = FIGURES_DIR / "fig10_diurnal_mechanism.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    log.info(f"\n  图表保存: {fig_path}")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px, "
              f"{fig_path.stat().st_size/1e3:.1f} KB")

    log.info("\n🎉 Phase 7 (L1) 完成！")


if __name__ == "__main__":
    main()
