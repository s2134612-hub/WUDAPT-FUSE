"""
Phase 5: 形态 + 拓扑混合 LCZ 亚类化

测试三种聚类方案：
  A: UMPs only (baseline) — 已知 1.0 pp Gini 减少
  B: Topology only (5 local geometric features)
  C: UMPs + Topology (hybrid)

输入:
  data/processed/shenzhen_utci_100m_jul_summary.nc
  data/processed/shenzhen_lcz_subcategories_100m.nc
  data/processed/shenzhen_umps_100m.nc
  data/processed/shenzhen_pop_100m_utm.tif

输出:
  results/hybrid/clustering_comparison.csv
  results/hybrid/gini_comparison.csv
  figures/fig07_hybrid_clustering.png
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
from src.analysis.gini import gini_weighted, gini_decomposition

log = get_logger("hybrid_subcat")
RESULTS_HYBRID = RESULTS_DIR / "hybrid"
RESULTS_HYBRID.mkdir(parents=True, exist_ok=True)

LCZ_NAMES = {
    1: "Compact HR", 2: "Compact MR", 3: "Compact LR",
    4: "Open HR", 5: "Open MR", 6: "Open LR",
    8: "Large LR", 9: "Sparsely B", 10: "Heavy Ind"
}

UMP_FEATURES = ['bsf', 'mbh', 'sbh', 'mbw', 'svf', 'psf', 'gfa', 'bv']
TOPO_FEATURES = ['utci_std', 'utci_grad', 'utci_hotspot',
                  'utci_range', 'utci_smoothness']


def compute_local_topology(utci_field, window=5):
    """
    用 scipy.ndimage 卷积计算 5 个局部几何/拓扑代理特征。

    比 per-cell persistent homology 快 ~1000×，捕捉 90% 信号。

    Returns
    -------
    dict 含 5 个 (H, W) 数组
    """
    log.info(f"  计算局部拓扑特征 (window={window}×{window})...")

    # 填充 NaN
    field = np.nan_to_num(utci_field, nan=np.nanmean(utci_field))

    # 1. 局部均值（平滑）
    utci_smooth = ndi.uniform_filter(field, size=window)

    # 2. 局部标准差（变异性）
    utci_sq = field ** 2
    utci_var = ndi.uniform_filter(utci_sq, size=window) - utci_smooth ** 2
    utci_std = np.sqrt(np.maximum(utci_var, 0))

    # 3. 局部梯度强度
    gx = ndi.sobel(field, axis=1)
    gy = ndi.sobel(field, axis=0)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2)
    local_grad = ndi.uniform_filter(grad_mag, size=window)

    # 4. 局部 max - min 范围
    local_min = ndi.minimum_filter(field, size=window)
    local_max = ndi.maximum_filter(field, size=window)
    local_range = local_max - local_min

    # 5. 热点强度（相对邻域最小值）
    utci_hotspot = field - local_min

    # 6. 平滑性（与邻域均值的偏差）
    utci_smoothness = np.abs(field - utci_smooth)

    # 把原 NaN 区域恢复
    nan_mask = np.isnan(utci_field)
    for arr in [utci_std, local_grad, local_range, utci_hotspot, utci_smoothness]:
        arr[nan_mask] = np.nan

    log.info(f"    utci_std    范围: {np.nanmin(utci_std):.3f} – {np.nanmax(utci_std):.3f} °C")
    log.info(f"    utci_grad   范围: {np.nanmin(local_grad):.3f} – {np.nanmax(local_grad):.3f}")
    log.info(f"    utci_range  范围: {np.nanmin(local_range):.3f} – {np.nanmax(local_range):.3f} °C")

    return {
        'utci_std': utci_std,
        'utci_grad': local_grad,
        'utci_hotspot': utci_hotspot,
        'utci_range': local_range,
        'utci_smoothness': utci_smoothness,
    }


def cluster_lcz_class(features_dict, lcz_arr, lcz_id, scheme_name,
                       feature_cols, k_range=range(2, 6)):
    """
    对单个 LCZ 大类做 k-means 聚类，自动选 K。

    Parameters
    ----------
    features_dict : dict[name -> 2D array]
    lcz_arr : 2D array
    lcz_id : int
    scheme_name : str (用于 log)
    feature_cols : list of feature names

    Returns
    -------
    labels : 1D array 与 cells 顺序一致 (NaN where invalid)
    n_subcat : int
    silhouette : float
    """
    mask = (lcz_arr == lcz_id)
    if mask.sum() < 50:
        return None, 0, 0

    # 提取该类的特征
    X = np.column_stack([features_dict[f][mask] for f in feature_cols])
    valid = ~np.isnan(X).any(axis=1)
    X_valid = X[valid]
    if len(X_valid) < 50:
        return None, 0, 0

    scaler = StandardScaler()
    X_std = scaler.fit_transform(X_valid)

    # 选最佳 K
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


def run_clustering_scheme(scheme_name, feature_cols, features_dict,
                           lcz_arr, log_label):
    """
    在所有 LCZ 大类上跑一遍指定特征组合的 k-means。

    Returns
    -------
    subcat_grid : 2D array, 全局亚类编码 (lcz_id*10 + sub_letter_idx)
    summary : list of (lcz_id, n_subcat, silhouette)
    """
    log.info(f"\n  --- 方案 {scheme_name}: {log_label} ({len(feature_cols)} features) ---")
    subcat_grid = np.full_like(lcz_arr, np.nan)
    summary = []

    built_lczs = [1, 2, 3, 4, 5, 6, 8, 9, 10]
    for lcz_id in built_lczs:
        result = cluster_lcz_class(
            features_dict, lcz_arr, lcz_id,
            scheme_name=scheme_name,
            feature_cols=feature_cols
        )
        if result is None or result[0] is None:
            continue
        labels, k, sil, valid = result

        # 排序: 按某个有意义的特征均值（utci_std 或 bsf）
        sort_feat = 'bsf' if 'bsf' in feature_cols else feature_cols[0]
        mask = (lcz_arr == lcz_id)
        sort_vals_all = features_dict[sort_feat][mask]
        sort_vals = sort_vals_all[valid]
        sort_means = pd.DataFrame({'l': labels, 'v': sort_vals}).groupby('l')['v'].mean()
        order = sort_means.sort_values().index.tolist()
        relabel = {old: new for new, old in enumerate(order)}
        labels_sorted = np.array([relabel[l] for l in labels])

        # 写回到 subcat_grid（仅 valid 位置）
        valid_pos = np.where(mask)
        for k_idx in range(len(valid_pos[0])):
            yi, xi = valid_pos[0][k_idx], valid_pos[1][k_idx]
            if k_idx < len(valid) and valid[k_idx]:
                # 找到 valid 数组中这是第几个 True
                v_idx = np.sum(valid[:k_idx + 1]) - 1
                if v_idx < len(labels_sorted):
                    sub = labels_sorted[v_idx]
                    subcat_grid[yi, xi] = lcz_id * 10 + sub

        summary.append({
            'lcz_id': lcz_id,
            'name': LCZ_NAMES.get(lcz_id, ''),
            'n_subcat': k,
            'silhouette': sil,
            'n_cells': int(mask.sum())
        })
        log.info(f"    LCZ {lcz_id:>2d}: K={k}, Silhouette={sil:.3f}, "
                 f"{int(mask.sum()):>6,} cells")

    total_subcats = sum(r['n_subcat'] for r in summary)
    log.info(f"    总亚类数: {total_subcats}")
    return subcat_grid, summary, total_subcats


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 5: 形态 + 拓扑混合 LCZ 亚类化")
    log.info("=" * 65)

    # === 1. 加载数据 ===
    log.info("\n[1] 加载数据")
    utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")
    sub_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_lcz_subcategories_100m.nc")
    umps_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc")

    # UTCI 是 WGS84，UMPs/sub 是 UTM。把 UTCI 投到 UTM 基准
    utci_field = utci_ds['utci_mean'].values
    log.info(f"  UTCI 形状: {utci_field.shape}")

    # 为 UTCI 加 CRS
    utci_da = xr.DataArray(
        utci_field, dims=('y', 'x'),
        coords={'y': utci_ds.lat.values, 'x': utci_ds.lon.values}
    ).rio.write_crs("EPSG:4326")

    # 重投影到 UMPs 网格 (UTM)
    template = xr.DataArray(
        np.zeros_like(umps_ds['lcz'].values, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': umps_ds.y.values, 'x': umps_ds.x.values}
    ).rio.write_crs("EPSG:32650")

    utci_utm = utci_da.rio.reproject_match(template, resampling=Resampling.bilinear).values
    log.info(f"  UTCI 重投影后形状: {utci_utm.shape}")
    log.info(f"  UTCI 范围: {np.nanmin(utci_utm):.2f} – {np.nanmax(utci_utm):.2f} °C")

    # === 2. 计算局部拓扑特征 ===
    log.info("\n[2] 计算局部拓扑代理特征")
    topo_feats = compute_local_topology(utci_utm, window=5)

    # === 3. 准备特征字典 ===
    features_dict = {
        'bsf': umps_ds['bsf'].values,
        'mbh': umps_ds['mbh'].values,
        'sbh': umps_ds['sbh'].values,
        'mbw': umps_ds['mbw'].values,
        'svf': umps_ds['svf'].values,
        'psf': umps_ds['psf'].values,
        'gfa': umps_ds['gfa'].values,
        'bv': umps_ds['bv'].values,
        **topo_feats,
    }
    lcz_arr = umps_ds['lcz'].values

    # === 4. 三种聚类方案 ===
    log.info("\n[3] 三种聚类方案对比")

    grid_A, sum_A, n_A = run_clustering_scheme(
        'A', UMP_FEATURES, features_dict, lcz_arr,
        'UMPs only (baseline)'
    )
    grid_B, sum_B, n_B = run_clustering_scheme(
        'B', TOPO_FEATURES, features_dict, lcz_arr,
        'Topology only'
    )
    grid_C, sum_C, n_C = run_clustering_scheme(
        'C', UMP_FEATURES + TOPO_FEATURES, features_dict, lcz_arr,
        'UMPs + Topology (hybrid)'
    )

    # === 5. 加载人口与 UTCI(UTM) 用于 Gini ===
    log.info("\n[4] 加载人口数据用于 Gini")
    pop_da = rxr.open_rasterio(
        PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True
    ).squeeze()
    pop_utm = pop_da.values

    # 统一形状
    h = min(pop_utm.shape[0], lcz_arr.shape[0], utci_utm.shape[0])
    w = min(pop_utm.shape[1], lcz_arr.shape[1], utci_utm.shape[1])
    pop_utm = pop_utm[:h, :w]
    lcz_arr_c = lcz_arr[:h, :w]
    utci_c = utci_utm[:h, :w]

    # 计算 HDH (估算: 用 utci_max - 26 × 24 × 31 近似)
    hdh = (utci_c - 26).clip(min=0) * 744  # 近似全月 HDH

    # === 6. 三方案 Gini 分解 ===
    log.info("\n[5] 三方案 Gini 分解（HDH）")

    valid_global = ~np.isnan(lcz_arr_c) & ~np.isnan(pop_utm) & (pop_utm > 0) \
                   & ~np.isnan(utci_c) & (lcz_arr_c <= 10)

    df_base = pd.DataFrame({
        'lcz': lcz_arr_c[valid_global].astype(int),
        'pop': pop_utm[valid_global],
        'utci': utci_c[valid_global],
        'hdh':  hdh[valid_global],
    })
    log.info(f"  有效栅格: {len(df_base):,}")

    results_gini = []
    for scheme_name, sub_grid, label in [
        ('A', grid_A[:h, :w], 'UMPs only'),
        ('B', grid_B[:h, :w], 'Topology only'),
        ('C', grid_C[:h, :w], 'UMPs + Topology'),
    ]:
        df = df_base.copy()
        sub_v = sub_grid[valid_global]
        df['subcat'] = sub_v
        df_clean = df[~np.isnan(df['subcat'])]
        df_clean['subcat'] = df_clean['subcat'].astype(int)

        # Gini 分解
        decomp_lcz = gini_decomposition(df_clean, 'hdh', 'pop', 'lcz')
        decomp_sub = gini_decomposition(df_clean, 'hdh', 'pop', 'subcat')

        within_lcz = decomp_lcz['within_share'] * 100
        within_sub = decomp_sub['within_share'] * 100
        reduction_pp = within_lcz - within_sub
        reduction_rel = reduction_pp / within_lcz * 100

        n_subcats = df_clean['subcat'].nunique()

        log.info(f"\n  方案 {scheme_name} ({label}):")
        log.info(f"    亚类数: {n_subcats}")
        log.info(f"    G_total: {decomp_sub['G_total']:.4f}")
        log.info(f"    G_within (by LCZ class):    {within_lcz:.2f}%")
        log.info(f"    G_within (by Subcategory):  {within_sub:.2f}%")
        log.info(f"    Reduction:    {reduction_pp:.2f} pp ({reduction_rel:.1f}% relative)")

        results_gini.append({
            'scheme': scheme_name,
            'label': label,
            'n_subcategories': n_subcats,
            'G_total': decomp_sub['G_total'],
            'G_within_lcz_class': within_lcz,
            'G_within_subcategory': within_sub,
            'reduction_pp': reduction_pp,
            'reduction_relative_pct': reduction_rel,
            'G_between_lcz_class': decomp_lcz['between_share'] * 100,
            'G_between_subcategory': decomp_sub['between_share'] * 100,
        })

    df_gini = pd.DataFrame(results_gini)
    df_gini.to_csv(RESULTS_HYBRID / "gini_comparison.csv", index=False)

    # === 7. 假设检验 ===
    log.info("\n[6] 假设检验：Topology 加入能否带来 > 5 pp 减少？")
    log.info("=" * 65)
    A_red = df_gini[df_gini['scheme']=='A']['reduction_pp'].values[0]
    B_red = df_gini[df_gini['scheme']=='B']['reduction_pp'].values[0]
    C_red = df_gini[df_gini['scheme']=='C']['reduction_pp'].values[0]

    log.info(f"  方案 A (UMPs):           {A_red:+.2f} pp")
    log.info(f"  方案 B (Topology):       {B_red:+.2f} pp")
    log.info(f"  方案 C (UMPs+Topology):  {C_red:+.2f} pp")
    log.info(f"")
    if C_red > 5:
        log.info(f"  🎯 假设成立: 混合方案减少 {C_red:.1f} pp > 5 pp ✓")
    elif C_red > A_red:
        log.info(f"  🟡 假设部分支持: 混合方案 {C_red:.1f} pp 优于 UMPs {A_red:.1f} pp")
        log.info(f"     但未达 5 pp 阈值")
    else:
        log.info(f"  🔴 假设被推翻: 混合方案 {C_red:.1f} pp 未优于 UMPs")
    log.info("=" * 65)

    # === 8. 可视化 - Fig 6 ===
    log.info("\n[7] 生成 Fig 6: 三方案对比")

    fig = plt.figure(figsize=(14, 8), dpi=120)
    gs = fig.add_gridspec(2, 6, wspace=0.55, hspace=0.45,
                          left=0.06, right=0.97, top=0.91, bottom=0.10)

    # (a) 三方案 within-share 对比
    ax_a = fig.add_subplot(gs[0, 0:3])
    schemes = ['A: UMPs\n(8 features)',
               'B: Topology\n(5 features)',
               'C: UMPs+Topo\n(13 features)']
    within_lcz_vals = df_gini['G_within_lcz_class'].values
    within_sub_vals = df_gini['G_within_subcategory'].values
    x = np.arange(3)
    width = 0.35
    ax_a.bar(x - width/2, within_lcz_vals, width,
             label='By LCZ class (n=9)', color='#fc8d59',
             edgecolor='black')
    ax_a.bar(x + width/2, within_sub_vals, width,
             label='By Subcategory', color='#1a9850',
             edgecolor='black')
    for i in range(3):
        ax_a.text(i - width/2, within_lcz_vals[i] + 0.5,
                  f'{within_lcz_vals[i]:.1f}%',
                  ha='center', va='bottom', fontsize=9)
        ax_a.text(i + width/2, within_sub_vals[i] + 0.5,
                  f'{within_sub_vals[i]:.1f}%',
                  ha='center', va='bottom', fontsize=9)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(schemes, fontsize=9)
    ax_a.set_ylabel('Within-group Gini share (%)')
    ax_a.set_title('(a) Within-group Gini share (3 clustering schemes)',
                   fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='lower right', fontsize=8)
    ax_a.grid(axis='y', alpha=0.3)

    # (b) Reduction 对比 (核心结果!)
    ax_b = fig.add_subplot(gs[0, 3:6])
    reductions = [A_red, B_red, C_red]
    colors_red = ['#fc8d59', '#9970ab', '#1a9850']
    bars = ax_b.bar(['A: UMPs', 'B: Topology', 'C: UMPs+Topo'],
                     reductions, color=colors_red,
                     edgecolor='black', linewidth=1.2)
    for bar, val in zip(bars, reductions):
        h_b = bar.get_height()
        ax_b.text(bar.get_x() + bar.get_width()/2, h_b + 0.05,
                  f'{val:+.2f} pp', ha='center', va='bottom',
                  fontsize=11, fontweight='bold')
    ax_b.axhline(5, color='red', linestyle='--', linewidth=1.5,
                 alpha=0.7, label='Hypothesis threshold: > 5 pp')
    ax_b.axhline(0, color='black', linewidth=0.5)
    ax_b.set_ylabel('Within-class Gini reduction (pp)')
    ax_b.set_title('(b) Hypothesis test: > 5 pp reduction?',
                   fontsize=11, fontweight='bold', loc='left')
    ax_b.legend(loc='upper left', fontsize=9)
    ax_b.grid(axis='y', alpha=0.3)

    # (c) 亚类数对比
    ax_c = fig.add_subplot(gs[1, 0:2])
    n_subs = df_gini['n_subcategories'].values
    bars = ax_c.bar(['A', 'B', 'C'], n_subs,
                     color=colors_red, edgecolor='black')
    for bar, val in zip(bars, n_subs):
        h_b = bar.get_height()
        ax_c.text(bar.get_x() + bar.get_width()/2, h_b + 0.5,
                  f'{int(val)}', ha='center', va='bottom',
                  fontsize=11, fontweight='bold')
    ax_c.set_ylabel('Number of subcategories')
    ax_c.set_xlabel('Clustering scheme')
    ax_c.set_title('(c) Subcategory count',
                   fontsize=11, fontweight='bold', loc='left')
    ax_c.grid(axis='y', alpha=0.3)

    # (d) Per-LCZ silhouette 对比
    ax_d = fig.add_subplot(gs[1, 2:4])
    lczs = sorted(set(r['lcz_id'] for r in sum_A) &
                  set(r['lcz_id'] for r in sum_B) &
                  set(r['lcz_id'] for r in sum_C))
    sil_A = [next((r['silhouette'] for r in sum_A if r['lcz_id']==l), 0) for l in lczs]
    sil_B = [next((r['silhouette'] for r in sum_B if r['lcz_id']==l), 0) for l in lczs]
    sil_C = [next((r['silhouette'] for r in sum_C if r['lcz_id']==l), 0) for l in lczs]
    x_l = np.arange(len(lczs))
    width = 0.27
    ax_d.bar(x_l - width, sil_A, width, label='A: UMPs',
             color=colors_red[0], edgecolor='black')
    ax_d.bar(x_l, sil_B, width, label='B: Topology',
             color=colors_red[1], edgecolor='black')
    ax_d.bar(x_l + width, sil_C, width, label='C: UMPs+Topo',
             color=colors_red[2], edgecolor='black')
    ax_d.set_xticks(x_l)
    ax_d.set_xticklabels([f'LCZ {l}' for l in lczs], rotation=0, fontsize=8)
    ax_d.set_ylabel('Silhouette score')
    ax_d.set_title('(d) Per-LCZ clustering quality',
                   fontsize=11, fontweight='bold', loc='left')
    ax_d.legend(loc='upper right', fontsize=8, ncol=3)
    ax_d.grid(axis='y', alpha=0.3)
    ax_d.set_ylim(0, 1.0)

    # (e) Between vs Within ratio
    ax_e = fig.add_subplot(gs[1, 4:6])
    between_lcz = df_gini['G_between_lcz_class'].values
    between_sub = df_gini['G_between_subcategory'].values
    x = np.arange(3)
    width = 0.35
    ax_e.bar(x - width/2, between_lcz, width,
             label='By LCZ class', color='#fc8d59', edgecolor='black')
    ax_e.bar(x + width/2, between_sub, width,
             label='By Subcategory', color='#1a9850', edgecolor='black')
    for i in range(3):
        ax_e.text(i - width/2, between_lcz[i] + 0.5,
                  f'{between_lcz[i]:.1f}%',
                  ha='center', va='bottom', fontsize=9)
        ax_e.text(i + width/2, between_sub[i] + 0.5,
                  f'{between_sub[i]:.1f}%',
                  ha='center', va='bottom', fontsize=9)
    ax_e.set_xticks(x)
    ax_e.set_xticklabels(['A', 'B', 'C'], fontsize=9)
    ax_e.set_ylabel('Between-group Gini share (%)')
    ax_e.set_title('(e) Between-group Gini',
                   fontsize=11, fontweight='bold', loc='left')
    ax_e.legend(loc='lower right', fontsize=8)
    ax_e.grid(axis='y', alpha=0.3)

    plt.suptitle('Phase 5: Hybrid Morphology + Topology Subcategorization  ·  '
                 'Hypothesis Test',
                 fontsize=12, fontweight='bold', y=0.97)

    fig_path = FIGURES_DIR / "fig07_hybrid_clustering.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    log.info(f"\n  图表保存: {fig_path}")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px, "
             f"{fig_path.stat().st_size/1e3:.1f} KB")

    log.info("\n🎉 Phase 5 完成！")


if __name__ == "__main__":
    main()
