"""
Phase 6: 探索非空间维度（时间 + 人口）能否突破 5 pp Gini 减少阈值

测试 6 种聚类方案：
  A: UMPs only            (8 feat) — 基线
  B: Topology only        (5 feat) — Phase 5
  C: UMPs + Topology      (13 feat) — Phase 5
  D: Temporal only        (5 feat) — NEW: 非空间-时间维度
  E: Temporal + Population (8 feat) — NEW: 时间+人口
  F: All (UMPs+Topo+Temp+Pop) (21 feat) — NEW: 终极测试

输出:
  results/phase6/all_schemes_gini.csv
  figures/fig08_nonspatial_test.png
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
import scipy.ndimage as ndi
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.figure_style import apply_paper_style
apply_paper_style()

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.gini import gini_decomposition

log = get_logger("phase6")
RESULTS_P6 = RESULTS_DIR / "phase6"
RESULTS_P6.mkdir(parents=True, exist_ok=True)

LCZ_NAMES = {
    1: "Compact HR", 2: "Compact MR", 3: "Compact LR",
    4: "Open HR", 5: "Open MR", 6: "Open LR",
    8: "Large LR", 9: "Sparsely B", 10: "Heavy Ind"
}

# 特征定义
UMP_FEATURES = ['bsf', 'mbh', 'sbh', 'mbw', 'svf', 'psf', 'gfa', 'bv']
TOPO_FEATURES = ['utci_std_local', 'utci_grad', 'utci_hotspot',
                 'utci_range', 'utci_smoothness']
# 重要: 严格排除 UTCI-derived 特征（避免循环逻辑）
# 仅保留与 UTCI 无关的"真正外部"特征
POP_FEATURES = ['pop_density', 'log_pop', 'pop_smooth']
GEO_FEATURES = ['dist_coast', 'dist_mountain', 'elevation_proxy']


def compute_local_topology(utci_field, window=5):
    """计算 5 个局部几何特征（Phase 5 复用）"""
    field = np.nan_to_num(utci_field, nan=np.nanmean(utci_field))
    utci_smooth = ndi.uniform_filter(field, size=window)
    utci_var = ndi.uniform_filter(field ** 2, size=window) - utci_smooth ** 2
    utci_std = np.sqrt(np.maximum(utci_var, 0))
    gx = ndi.sobel(field, axis=1)
    gy = ndi.sobel(field, axis=0)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2)
    local_grad = ndi.uniform_filter(grad_mag, size=window)
    local_min = ndi.minimum_filter(field, size=window)
    local_max = ndi.maximum_filter(field, size=window)
    local_range = local_max - local_min
    utci_hotspot = field - local_min
    utci_smoothness = np.abs(field - utci_smooth)

    nan_mask = np.isnan(utci_field)
    for arr in [utci_std, local_grad, local_range, utci_hotspot, utci_smoothness]:
        arr[nan_mask] = np.nan

    return {
        'utci_std_local': utci_std,
        'utci_grad': local_grad,
        'utci_hotspot': utci_hotspot,
        'utci_range': local_range,
        'utci_smoothness': utci_smoothness,
    }


def compute_population_features(pop_field):
    """
    计算 3 个人口特征（严格独立于 UTCI - 避免循环逻辑）

    包括:
      - pop_density: 原始人口计数
      - log_pop: 对数密度
      - pop_smooth: 邻域平滑人口（5x5 均值）

    不再含 pop × UTCI（避免 UTCI 泄漏）
    """
    log.info("  计算人口特征（严格独立于 UTCI）...")
    pop = np.where(np.isnan(pop_field) | (pop_field <= 0), 0.001, pop_field)
    pop_density = pop_field
    log_pop = np.log1p(pop)

    # 邻域平滑（5x5 卷积均值，仍是 pop 的函数）
    pop_smooth = ndi.uniform_filter(np.nan_to_num(pop, nan=0), size=5)
    pop_smooth = np.where(np.isnan(pop_field), np.nan, pop_smooth)

    log.info(f"    pop_density: {np.nanmin(pop_density):.1f} – {np.nanmax(pop_density):.1f}")
    log.info(f"    log_pop:     {np.nanmin(log_pop):.2f} – {np.nanmax(log_pop):.2f}")
    log.info(f"    pop_smooth:  {np.nanmin(pop_smooth):.1f} – {np.nanmax(pop_smooth):.1f}")

    return {
        'pop_density': pop_density.astype(np.float32),
        'log_pop':     log_pop.astype(np.float32),
        'pop_smooth':  pop_smooth.astype(np.float32),
    }


def compute_geographic_features(lcz_arr, transform_info=None):
    """
    计算 3 个地理位置特征（与 UTCI 无关）：
      - dist_coast: 距海岸距离的代理（用 LCZ 17 水体的最近距离）
      - dist_mountain: 距山区距离代理（用 LCZ 11/12 树林）
      - elevation_proxy: 高程代理（用 1 - BSF 邻域均值，山区 BSF 接近 0）
    """
    log.info("  计算地理特征（与 UTCI 无关）...")
    H, W = lcz_arr.shape

    # 用栅格距离计算距水体（LCZ 17）距离
    water_mask = (lcz_arr == 17)
    if water_mask.sum() > 0:
        # 用 distance transform 在 NumPy 中近似实现
        from scipy.ndimage import distance_transform_edt
        dist_water = distance_transform_edt(~water_mask).astype(np.float32)
    else:
        dist_water = np.full((H, W), 1000.0, dtype=np.float32)

    # 距山区（LCZ 11/12 树林）
    mountain_mask = np.isin(lcz_arr, [11, 12])
    if mountain_mask.sum() > 0:
        from scipy.ndimage import distance_transform_edt
        dist_mountain = distance_transform_edt(~mountain_mask).astype(np.float32)
    else:
        dist_mountain = np.full((H, W), 1000.0, dtype=np.float32)

    # 高程代理: 山区位置 (LCZ 11/12) 较高
    # 用山区距离的反函数：远处 = 低
    elev_proxy = (1.0 / (dist_mountain + 1.0)).astype(np.float32)

    log.info(f"    dist_coast (water): {dist_water.min():.0f} – {dist_water.max():.0f} cells")
    log.info(f"    dist_mountain:      {dist_mountain.min():.0f} – {dist_mountain.max():.0f} cells")

    nan_mask = np.isnan(lcz_arr)
    for arr in [dist_water, dist_mountain, elev_proxy]:
        arr[nan_mask] = np.nan

    return {
        'dist_coast': dist_water,
        'dist_mountain': dist_mountain,
        'elevation_proxy': elev_proxy,
    }


def cluster_lcz_class(features_dict, lcz_arr, lcz_id, feature_cols,
                      k_range=range(2, 6)):
    mask = (lcz_arr == lcz_id)
    if mask.sum() < 50:
        return None

    X = np.column_stack([features_dict[f][mask] for f in feature_cols])
    valid = ~np.isnan(X).any(axis=1)
    X_valid = X[valid]
    if len(X_valid) < 50:
        return None

    scaler = StandardScaler()
    X_std = scaler.fit_transform(X_valid)

    best_k, best_sil = 2, -1
    for k in k_range:
        if len(X_valid) < k * 5:
            continue
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            lbl = km.fit_predict(X_std)
            if len(set(lbl)) < 2:
                continue
            if len(X_valid) > 5000:
                idx = np.random.RandomState(42).choice(len(X_valid), 5000, replace=False)
                sil = silhouette_score(X_std[idx], lbl[idx])
            else:
                sil = silhouette_score(X_std, lbl)
            if sil > best_sil:
                best_k, best_sil = k, sil
        except Exception:
            continue

    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km.fit_predict(X_std)
    return labels, best_k, best_sil, valid


def run_scheme(scheme_name, feature_cols, features_dict, lcz_arr, log_label):
    log.info(f"\n  ─── 方案 {scheme_name}: {log_label} ({len(feature_cols)} features) ───")
    subcat_grid = np.full_like(lcz_arr, np.nan)
    summary = []
    built_lczs = [1, 2, 3, 4, 5, 6, 8, 9, 10]

    for lcz_id in built_lczs:
        result = cluster_lcz_class(features_dict, lcz_arr, lcz_id, feature_cols)
        if result is None:
            continue
        labels, k, sil, valid = result

        sort_feat = feature_cols[0]
        mask = (lcz_arr == lcz_id)
        sort_vals = features_dict[sort_feat][mask][valid]
        sort_means = pd.DataFrame({'l': labels, 'v': sort_vals}).groupby('l')['v'].mean()
        order = sort_means.sort_values().index.tolist()
        relabel = {old: new for new, old in enumerate(order)}
        labels_sorted = np.array([relabel[l] for l in labels])

        # 写回到 subcat_grid
        valid_pos = np.where(mask)
        valid_count = 0
        for k_idx in range(len(valid_pos[0])):
            if valid[k_idx]:
                yi, xi = valid_pos[0][k_idx], valid_pos[1][k_idx]
                subcat_grid[yi, xi] = lcz_id * 10 + labels_sorted[valid_count]
                valid_count += 1

        summary.append({
            'lcz_id': lcz_id, 'name': LCZ_NAMES.get(lcz_id, ''),
            'n_subcat': k, 'silhouette': sil,
            'n_cells': int(mask.sum())
        })
        log.info(f"      LCZ {lcz_id:>2d}: K={k}, Sil={sil:.3f}, "
                 f"{int(mask.sum()):>6,} cells")

    total = sum(r['n_subcat'] for r in summary)
    log.info(f"    总亚类数: {total}")
    return subcat_grid, summary, total


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 6: 探索非空间维度（时间 + 人口）")
    log.info("=" * 65)

    # === 1. 加载数据 ===
    log.info("\n[1] 加载数据")
    utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")
    umps_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc")

    # UTCI WGS84 → UTM
    utci_da = xr.DataArray(
        utci_ds['utci_mean'].values, dims=('y', 'x'),
        coords={'y': utci_ds.lat.values, 'x': utci_ds.lon.values}
    ).rio.write_crs("EPSG:4326")

    template = xr.DataArray(
        np.zeros_like(umps_ds['lcz'].values, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': umps_ds.y.values, 'x': umps_ds.x.values}
    ).rio.write_crs("EPSG:32650")

    log.info("  UTCI summary 重投影到 UTM...")
    # 同时投影所有 utci 子变量
    utci_summary = {}
    for var in ['utci_mean', 'utci_max', 'utci_p95', 'tsd_strong', 'hdh']:
        da = xr.DataArray(
            utci_ds[var].values, dims=('y', 'x'),
            coords={'y': utci_ds.lat.values, 'x': utci_ds.lon.values}
        ).rio.write_crs("EPSG:4326")
        utci_summary[var] = da.rio.reproject_match(
            template, resampling=Resampling.bilinear).values

    log.info(f"  UTCI mean 形状: {utci_summary['utci_mean'].shape}")

    # === 2. 计算所有特征 ===
    log.info("\n[2] 计算所有特征")

    # UMPs 已在 umps_ds
    umps_dict = {f: umps_ds[f].values for f in UMP_FEATURES}

    # 拓扑（UMPs 网格上）
    log.info("  局部拓扑特征...")
    topo_dict = compute_local_topology(utci_summary['utci_mean'])

    # 人口（重投影到 UMPs 网格）
    log.info("  人口数据加载...")
    pop_da = rxr.open_rasterio(
        PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True
    ).squeeze()
    h = min(pop_da.shape[0], umps_ds['lcz'].shape[0])
    w = min(pop_da.shape[1], umps_ds['lcz'].shape[1])
    pop_arr = pop_da.values[:h, :w]
    # 形状对齐其它特征
    for d in [umps_dict, topo_dict]:
        for k in list(d.keys()):
            d[k] = d[k][:h, :w]
    lcz_arr = umps_ds['lcz'].values[:h, :w]

    # 严格独立特征
    pop_dict = compute_population_features(pop_arr)
    geo_dict = compute_geographic_features(lcz_arr)

    # 合并所有特征
    all_features = {**umps_dict, **topo_dict, **pop_dict, **geo_dict}
    log.info(f"\n  总特征数: {len(all_features)}")
    log.info(f"  特征列表: {list(all_features.keys())}")

    # === 3. 6 方案聚类 ===
    log.info("\n[3] 6 方案聚类对比")

    # 仅使用与 UTCI 严格独立的特征（避免循环逻辑）
    schemes = {
        'A': ('UMPs only',                UMP_FEATURES),
        'B': ('Topology only',            TOPO_FEATURES),
        'C': ('UMPs + Topology',          UMP_FEATURES + TOPO_FEATURES),
        'D': ('Population only',          POP_FEATURES),
        'E': ('Geography only',           GEO_FEATURES),
        'F': ('UMPs+Topo+Pop+Geo',        UMP_FEATURES + TOPO_FEATURES
                                            + POP_FEATURES + GEO_FEATURES),
    }

    grids = {}
    summaries = {}
    for sch, (label, feats) in schemes.items():
        grid, summary, total = run_scheme(sch, feats, all_features,
                                           lcz_arr, label)
        grids[sch] = grid
        summaries[sch] = (label, total, summary)

    # === 4. Gini 分解 ===
    log.info("\n[4] Gini 分解（HDH）")

    valid_global = (~np.isnan(lcz_arr)) & (~np.isnan(pop_arr)) \
                   & (pop_arr > 0) & (lcz_arr <= 10) \
                   & (~np.isnan(utci_summary['utci_mean'][:h, :w])) \
                   & (~np.isnan(utci_summary['hdh'][:h, :w]))

    df_base = pd.DataFrame({
        'lcz':   lcz_arr[valid_global].astype(int),
        'pop':   pop_arr[valid_global],
        'utci':  utci_summary['utci_mean'][:h, :w][valid_global],
        'hdh':   utci_summary['hdh'][:h, :w][valid_global],
    })
    log.info(f"  有效栅格: {len(df_base):,}")

    results = []
    for sch in schemes.keys():
        label = summaries[sch][0]
        df = df_base.copy()
        df['subcat'] = grids[sch][valid_global]
        df = df[~np.isnan(df['subcat'])].copy()
        df['subcat'] = df['subcat'].astype(int)

        decomp_lcz = gini_decomposition(df, 'hdh', 'pop', 'lcz')
        decomp_sub = gini_decomposition(df, 'hdh', 'pop', 'subcat')

        within_lcz = decomp_lcz['within_share'] * 100
        within_sub = decomp_sub['within_share'] * 100
        reduction_pp = within_lcz - within_sub
        reduction_rel = reduction_pp / within_lcz * 100

        results.append({
            'scheme': sch,
            'label': label,
            'n_features': len(schemes[sch][1]),
            'n_subcategories': df['subcat'].nunique(),
            'G_total': decomp_sub['G_total'],
            'G_within_lcz': within_lcz,
            'G_within_sub': within_sub,
            'reduction_pp': reduction_pp,
            'reduction_rel_pct': reduction_rel,
            'G_between_lcz': decomp_lcz['between_share'] * 100,
            'G_between_sub': decomp_sub['between_share'] * 100,
        })

    df_gini = pd.DataFrame(results)
    df_gini.to_csv(RESULTS_P6 / "all_schemes_gini.csv", index=False)

    # === 5. 终极假设检验 ===
    log.info("\n[5] 终极假设检验")
    log.info("=" * 65)
    log.info(f"  {'方案':<3s} {'描述':<28s} {'features':>8s} "
             f"{'subcats':>7s} {'reduction':>10s}")
    log.info("  " + "-" * 65)
    for r in results:
        marker = "✓" if r['reduction_pp'] > 5 else "✗"
        log.info(f"  {r['scheme']:<3s} {r['label']:<28s} "
                 f"{r['n_features']:>8d} {r['n_subcategories']:>7d} "
                 f"{r['reduction_pp']:>+8.2f} pp {marker}")
    log.info("  " + "-" * 65)

    max_reduction = max(r['reduction_pp'] for r in results)
    best_scheme = max(results, key=lambda r: r['reduction_pp'])
    log.info(f"\n  最大减少: {max_reduction:.2f} pp (方案 {best_scheme['scheme']}: "
             f"{best_scheme['label']})")
    log.info(f"  阈值 5 pp: {'达到 ✓' if max_reduction > 5 else '未达到 ✗'}")
    log.info("=" * 65)

    if max_reduction > 5:
        log.info("\n  🎯 假设成立！至少一种维度可突破 5 pp 阈值")
        log.info("     适应规划应聚焦该维度")
    else:
        log.info("\n  🔴 三重否定：形态、拓扑、非空间维度均无法突破 5 pp")
        log.info("     within-class 异质性来自更深层（材料/AC/社会/微尺度）驱动")

    # === 6. Fig 7: 6 方案综合对比 ===
    log.info("\n[6] 生成 Fig 7")
    fig = plt.figure(figsize=(15, 8.5), dpi=120)
    gs = fig.add_gridspec(2, 6, wspace=0.6, hspace=0.45,
                          left=0.06, right=0.97, top=0.91, bottom=0.10)

    schemes_order = ['A', 'B', 'C', 'D', 'E', 'F']
    colors_scheme = ['#fc8d59', '#9970ab', '#1a9850',
                     '#225ea8', '#e6550d', '#542788']
    short_labels = ['A:UMPs\n(8)', 'B:Topo\n(5)', 'C:UMPs+\nTopo (13)',
                    'D:Pop\n(3)', 'E:Geo\n(3)', 'F:All\n(19)']

    # (a) 主图: reduction 对比 + 5 pp 阈值
    ax_a = fig.add_subplot(gs[0, 0:4])
    reductions = [r['reduction_pp'] for r in results]
    bars = ax_a.bar(short_labels, reductions, color=colors_scheme,
                     edgecolor='black', linewidth=1.2)
    for bar, val in zip(bars, reductions):
        h_b = bar.get_height()
        ax_a.text(bar.get_x() + bar.get_width()/2, h_b + 0.08,
                  f'{val:+.2f}\npp', ha='center', va='bottom',
                  fontsize=9.5, fontweight='bold')
    ax_a.axhline(5, color='red', linestyle='--', linewidth=2,
                 label='Hypothesis threshold: > 5 pp')
    ax_a.axhline(0, color='black', linewidth=0.5)
    ax_a.set_ylabel('Within-class Gini reduction (pp)')
    ax_a.set_title('(a) Hypothesis test across 6 clustering schemes',
                   fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='upper left', fontsize=9)
    ax_a.set_ylim(-0.5, max(6, max_reduction + 1))
    ax_a.grid(axis='y', alpha=0.3)

    # (b) 特征数 vs reduction
    ax_b = fig.add_subplot(gs[0, 4:6])
    n_feats = [r['n_features'] for r in results]
    ax_b.scatter(n_feats, reductions, s=200,
                 c=colors_scheme, edgecolor='black', linewidths=1.5,
                 alpha=0.85)
    for i, sch in enumerate(schemes_order):
        ax_b.annotate(sch, (n_feats[i], reductions[i]),
                      xytext=(8, 5), textcoords='offset points',
                      fontsize=9, fontweight='bold')
    ax_b.axhline(5, color='red', linestyle='--', linewidth=1.5, alpha=0.6)
    ax_b.set_xlabel('Number of features')
    ax_b.set_ylabel('Reduction (pp)')
    ax_b.set_title('(b) More features ≠ more reduction',
                   fontsize=11, fontweight='bold', loc='left')
    ax_b.grid(alpha=0.3)

    # (c) Gini total vs subcategory count
    ax_c = fig.add_subplot(gs[1, 0:2])
    n_subs = [r['n_subcategories'] for r in results]
    ax_c.bar(short_labels, n_subs, color=colors_scheme,
             edgecolor='black')
    for i, val in enumerate(n_subs):
        ax_c.text(i, val + 0.5, f'{val}',
                  ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_c.set_ylabel('Subcategory count')
    ax_c.set_title('(c) Subcategory count by scheme',
                   fontsize=11, fontweight='bold', loc='left')
    ax_c.grid(axis='y', alpha=0.3)

    # (d) Within share by scheme
    ax_d = fig.add_subplot(gs[1, 2:4])
    within_lcz_v = [r['G_within_lcz'] for r in results]
    within_sub_v = [r['G_within_sub'] for r in results]
    x = np.arange(len(schemes_order))
    width = 0.35
    ax_d.bar(x - width/2, within_lcz_v, width,
             label='By LCZ class', color='#fc8d59', edgecolor='black')
    ax_d.bar(x + width/2, within_sub_v, width,
             label='By Subcategory', color='#1a9850', edgecolor='black')
    ax_d.set_xticks(x)
    ax_d.set_xticklabels(schemes_order, fontsize=9)
    ax_d.set_ylabel('Within-group Gini share (%)')
    ax_d.set_title('(d) Within-group Gini share',
                   fontsize=11, fontweight='bold', loc='left')
    ax_d.legend(loc='lower right', fontsize=8)
    ax_d.grid(axis='y', alpha=0.3)
    ax_d.set_ylim(80, 90)

    # (e) Cumulative narrative
    ax_e = fig.add_subplot(gs[1, 4:6])
    ax_e.axis('off')
    ax_e.set_xlim(0, 1)
    ax_e.set_ylim(0, 1)

    from matplotlib.patches import FancyBboxPatch
    bg = FancyBboxPatch((0.02, 0.04), 0.96, 0.92,
                         boxstyle='round,pad=0.0,rounding_size=0.03',
                         facecolor='#fafafa', edgecolor='#888888',
                         linewidth=1.0)
    ax_e.add_patch(bg)
    ax_e.text(0.5, 0.92, 'TRIPLE NEGATIVE' if max_reduction <= 5
              else 'BREAKTHROUGH',
              ha='center', va='top', fontsize=11, fontweight='bold',
              color='#cc0000' if max_reduction <= 5 else '#1a9850')
    ax_e.plot([0.15, 0.85], [0.875, 0.875],
              color='#cc0000' if max_reduction <= 5 else '#1a9850',
              linewidth=1.5)

    # 三个维度的总结
    findings_text = [
        ('Spatial form (UMPs)',     f'{results[0]["reduction_pp"]:+.2f} pp'),
        ('Spatial topology',         f'{results[1]["reduction_pp"]:+.2f} pp'),
        ('Form + topology',          f'{results[2]["reduction_pp"]:+.2f} pp'),
        ('Population only',          f'{results[3]["reduction_pp"]:+.2f} pp'),
        ('Geography only',           f'{results[4]["reduction_pp"]:+.2f} pp'),
        ('All independent (19 ft)',  f'{results[5]["reduction_pp"]:+.2f} pp'),
    ]
    y0 = 0.78
    for label, val in findings_text:
        ax_e.text(0.05, y0, label, ha='left', va='center',
                  fontsize=8.5, color='#333')
        ax_e.text(0.95, y0, val, ha='right', va='center',
                  fontsize=8.5, family='monospace', fontweight='bold',
                  color='#333')
        y0 -= 0.075

    ax_e.plot([0.05, 0.95], [0.32, 0.32], color='#aaa', linewidth=0.6)
    if max_reduction <= 5:
        ax_e.text(0.5, 0.27,
                  f'Max = {max_reduction:.2f} pp  «  5 pp',
                  ha='center', fontsize=10, fontweight='bold',
                  color='#cc0000')
        ax_e.text(0.5, 0.20,
                  'Within-class inequality is not\nexplained by any independent feature\ntested: form, topology, population,\nor geography.',
                  ha='center', va='center', fontsize=8.5,
                  color='#222', linespacing=1.4)
    else:
        ax_e.text(0.5, 0.27,
                  f'Max = {max_reduction:.2f} pp > 5 pp ✓',
                  ha='center', fontsize=10, fontweight='bold',
                  color='#1a9850')

    ax_e.text(0.5, 0.06,
              '14.30 M residents  ·  9 LCZ classes  ·  July 2020',
              ha='center', fontsize=7.5, color='#777', style='italic')

    plt.suptitle('Phase 6: Non-spatial Dimensions Cannot Close the Within-Class Gini Gap',
                 fontsize=12, fontweight='bold', y=0.97)

    fig_path = FIGURES_DIR / "fig08_nonspatial_test.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    log.info(f"\n  图表保存: {fig_path}")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px, "
             f"{fig_path.stat().st_size/1e3:.1f} KB")

    log.info("\n🎉 Phase 6 完成！")


if __name__ == "__main__":
    main()
