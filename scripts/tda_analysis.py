"""
Phase 4: TDA 拓扑数据分析 — 生成 Fig 6

输入:
  data/processed/shenzhen_utci_100m_jul_summary.nc
  data/processed/shenzhen_lcz_subcategories_100m.nc

输出:
  results/tda/persistence_features.csv
  results/tda/wasserstein_matrix.csv
  figures/fig06_tda_analysis.png
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.figure_style import apply_paper_style
apply_paper_style()

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.tda import (
    compute_persistence_diagram, persistence_features,
    persistence_image, sublevel_betti_curve, wasserstein_distance,
    filter_persistence
)

log = get_logger("tda_analysis")
RESULTS_TDA = RESULTS_DIR / "tda"
RESULTS_TDA.mkdir(parents=True, exist_ok=True)

LCZ_NAMES_SHORT = {
    1: "Compact HR", 2: "Compact MR", 3: "Compact LR",
    4: "Open HR", 5: "Open MR", 6: "Open LR",
    8: "Large LR", 9: "Sparsely B", 10: "Heavy Ind"
}


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 4: TDA 拓扑数据分析")
    log.info("=" * 65)

    # === 1. 加载 UTCI 与亚类网格 ===
    log.info("\n[1] 加载数据")
    utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")
    sub_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_lcz_subcategories_100m.nc")

    # UTCI 是 WGS84，subcat 是 UTM。把 subcat 投影到 UTCI 坐标
    utci_mean = utci_ds['utci_mean'].values
    log.info(f"  UTCI shape: {utci_mean.shape}")
    log.info(f"  UTCI 范围:  {np.nanmin(utci_mean):.2f} – {np.nanmax(utci_mean):.2f} °C")

    # 把 subcat 重投影到 UTCI 网格
    log.info("  对齐 subcategory 到 UTCI 网格...")
    template = xr.DataArray(
        np.zeros_like(utci_mean, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': utci_ds.lat.values, 'x': utci_ds.lon.values}
    ).rio.write_crs("EPSG:4326")

    sub_lcz = xr.DataArray(
        sub_ds['lcz'].values, dims=('y', 'x'),
        coords={'y': sub_ds.y.values, 'x': sub_ds.x.values}
    ).rio.write_crs("EPSG:32650")

    sub_lcz_aligned = sub_lcz.rio.reproject_match(
        template, resampling=Resampling.nearest
    ).values

    # === 2. City-wide 持续同调 ===
    log.info("\n[2] 全市 UTCI 持续同调")
    pd_city = compute_persistence_diagram(utci_mean)
    feats_city = persistence_features(pd_city, threshold=0.5)
    log.info(f"  全市 H_0 数: {feats_city['n_h0']:,}")
    log.info(f"  全市 H_1 数: {feats_city['n_h1']:,}")
    log.info(f"  Persistence Entropy: {feats_city['persistence_entropy']:.3f}")
    log.info(f"  n_significant (life>0.5): {feats_city['n_significant']}")

    # === 3. Sublevel filtration curve ===
    log.info("\n[3] Sublevel $\beta_0$/$\beta_1$ 曲线")
    thresholds, betti0, betti1 = sublevel_betti_curve(utci_mean, n_thresholds=40)
    log.info(f"  $\beta_0$ 峰值: {betti0.max()} @ T = {thresholds[betti0.argmax()]:.2f}")
    log.info(f"  $\beta_1$ 峰值: {betti1.max()} @ T = {thresholds[betti1.argmax()]:.2f}")

    # === 4. 各 LCZ 大类持续同调 ===
    log.info("\n[4] 各 LCZ 大类持续同调")

    # 对每个建成 LCZ，提取它的 UTCI 子区域
    lcz_pds = {}
    lcz_features = []
    built_lczs = [1, 2, 3, 4, 5, 6, 8, 9, 10]

    for lcz_id in built_lczs:
        mask = sub_lcz_aligned == lcz_id
        if mask.sum() < 100:
            log.warning(f"  LCZ {lcz_id}: 仅 {mask.sum()} 栅格，跳过")
            continue

        # 把该 LCZ 的 UTCI 提到一个最小包围盒
        rows = np.where(mask.any(axis=1))[0]
        cols = np.where(mask.any(axis=0))[0]
        r0, r1 = rows.min(), rows.max() + 1
        c0, c1 = cols.min(), cols.max() + 1

        # 子区域：保留 LCZ 内的 UTCI 值，其它设为 NaN（屏蔽）
        sub_field = np.where(mask, utci_mean, np.nan)[r0:r1, c0:c1]

        # 计算持续同调（NaN 会在 tda.py 内部用 max 填充）
        pd_lcz = compute_persistence_diagram(sub_field)
        feats = persistence_features(pd_lcz, threshold=0.3)

        lcz_pds[lcz_id] = pd_lcz
        lcz_features.append({
            'lcz_id': lcz_id,
            'name': LCZ_NAMES_SHORT.get(lcz_id, f"LCZ {lcz_id}"),
            'n_cells': int(mask.sum()),
            'patch_h': int(r1 - r0),
            'patch_w': int(c1 - c0),
            'n_h0': feats['n_h0'],
            'n_h1': feats['n_h1'],
            'max_lifetime_h0': feats['max_lifetime_h0'],
            'max_lifetime_h1': feats['max_lifetime_h1'],
            'total_lifetime_h0': feats['total_lifetime_h0'],
            'total_lifetime_h1': feats['total_lifetime_h1'],
            'persistence_entropy': feats['persistence_entropy'],
            'n_significant': feats['n_significant'],
        })
        log.info(f"  LCZ {lcz_id}: {mask.sum():>6,} 栅格, "
                 f"$\beta_0$={feats['n_h0']:>4d}, $\beta_1$={feats['n_h1']:>4d}, "
                 f"entropy={feats['persistence_entropy']:.2f}")

    df_features = pd.DataFrame(lcz_features)
    df_features.to_csv(RESULTS_TDA / "persistence_features.csv", index=False)
    log.info(f"\n  特征表保存: {RESULTS_TDA / 'persistence_features.csv'}")

    # === 5. Wasserstein 距离矩阵（H_1）===
    log.info("\n[5] Wasserstein 距离矩阵（H_1）")
    lcz_ids_used = [r['lcz_id'] for r in lcz_features]
    n = len(lcz_ids_used)
    W_mat = np.zeros((n, n))
    for i, l1 in enumerate(lcz_ids_used):
        for j, l2 in enumerate(lcz_ids_used):
            if i <= j:
                d = wasserstein_distance(lcz_pds[l1], lcz_pds[l2], dim=1, p=2)
                W_mat[i, j] = d
                W_mat[j, i] = d
    log.info(f"  距离矩阵: {n} × {n}, 范围 {W_mat.min():.2f}-{W_mat.max():.2f}")

    # 保存
    pd.DataFrame(W_mat,
                 columns=[f"LCZ{l}" for l in lcz_ids_used],
                 index=[f"LCZ{l}" for l in lcz_ids_used]).to_csv(
        RESULTS_TDA / "wasserstein_matrix.csv"
    )

    # === 6. 可视化 - Fig 5 (5 个面板：3 + 2 布局) ===
    log.info("\n[6] 生成 Fig 5 (5 panels)")
    fig = plt.figure(figsize=(14, 9), dpi=120)
    # 6 列基底，方便不均等分割
    # 上排: (a)(b)(c) 各 2 列；下排: (d)(e) 各 3 列
    gs = fig.add_gridspec(2, 6, wspace=0.55, hspace=0.42,
                           left=0.05, right=0.97, top=0.92, bottom=0.07)

    # ─── (a) Sublevel $\beta_0$/$\beta_1$ 曲线 ───
    ax_a = fig.add_subplot(gs[0, 0:2])
    ax_a.plot(thresholds, betti0, '-', color='#0571b0',
              linewidth=2, label=r'$\beta_0$ (components)')
    ax_a.plot(thresholds, betti1, '-', color='#d73027',
              linewidth=2, label=r'$\beta_1$ (loops)')
    ax_a.axvline(thresholds[betti0.argmax()], color='#0571b0',
                 linestyle=':', alpha=0.5)
    ax_a.axvline(thresholds[betti1.argmax()], color='#d73027',
                 linestyle=':', alpha=0.5)
    ax_a.set_xlabel('UTCI threshold (°C)')
    ax_a.set_ylabel('Number of topological features')
    ax_a.set_title('(a) Sublevel filtration of UTCI field',
                   fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='upper right', fontsize=8)
    ax_a.grid(alpha=0.3)

    # ─── (b) City-wide persistence diagram ───
    ax_b = fig.add_subplot(gs[0, 2:4])
    h0 = filter_persistence(pd_city, dim=0, exclude_inf=True)
    h1 = filter_persistence(pd_city, dim=1, exclude_inf=True)

    # 抽样以避免过密
    if len(h0) > 500:
        idx = np.random.RandomState(42).choice(len(h0), 500, replace=False)
        h0 = [h0[i] for i in idx]
    if len(h1) > 500:
        idx = np.random.RandomState(42).choice(len(h1), 500, replace=False)
        h1 = [h1[i] for i in idx]

    if h0:
        b0_arr = np.array([(b, d) for _, (b, d) in h0])
        ax_b.scatter(b0_arr[:, 0], b0_arr[:, 1],
                     s=10, c='#0571b0', alpha=0.5, edgecolor='none',
                     label=r'$H_0$ (n={})'.format(feats_city['n_h0']))
    if h1:
        b1_arr = np.array([(b, d) for _, (b, d) in h1])
        ax_b.scatter(b1_arr[:, 0], b1_arr[:, 1],
                     s=10, c='#d73027', alpha=0.5, edgecolor='none',
                     label=r'$H_1$ (n={})'.format(feats_city['n_h1']))

    # 对角线
    lim = [np.nanmin(utci_mean) - 0.5, np.nanmax(utci_mean) + 0.5]
    ax_b.plot(lim, lim, 'k--', alpha=0.4, linewidth=0.8)
    ax_b.set_xlabel('Birth (UTCI °C)')
    ax_b.set_ylabel('Death (UTCI °C)')
    ax_b.set_title('(b) City-wide persistence diagram',
                   fontsize=11, fontweight='bold', loc='left')
    ax_b.legend(loc='lower right', fontsize=8)
    ax_b.grid(alpha=0.3)

    # ─── (c) Per-LCZ persistence images (4 examples) ───
    # 用 GridSpecFromSubplotSpec 在 (0, 4:6) 内做 2x2 小图
    from matplotlib.gridspec import GridSpecFromSubplotSpec
    gs_c = GridSpecFromSubplotSpec(2, 2, subplot_spec=gs[0, 4:6],
                                    wspace=0.25, hspace=0.45)
    showcase_lczs = [1, 4, 8, 9]
    for k, lcz_id in enumerate(showcase_lczs):
        if lcz_id not in lcz_pds:
            continue
        ax_sub = fig.add_subplot(gs_c[k // 2, k % 2])
        pimg = persistence_image(lcz_pds[lcz_id], dim=1,
                                  resolution=15, sigma=0.1)
        ax_sub.imshow(pimg, cmap='viridis', origin='lower', aspect='auto')
        ax_sub.set_title(f"LCZ {lcz_id}",
                         fontsize=9, fontweight='bold', pad=2)
        ax_sub.set_xticks([])
        ax_sub.set_yticks([])

    # (c) 整体标题
    fig.text((gs[0, 4:6].get_position(fig).x0 +
              gs[0, 4:6].get_position(fig).x1) / 2,
             gs[0, 4:6].get_position(fig).y1 + 0.012,
             '(c) LCZ-class persistence images ($H_1$)',
             ha='center', va='bottom', fontsize=11, fontweight='bold')

    # ─── (d) Topological features heatmap ───
    ax_d = fig.add_subplot(gs[1, 0:3])
    feat_cols = ['n_h0', 'n_h1', 'max_lifetime_h1',
                  'persistence_entropy', 'n_significant']
    feat_labels = [r'$\beta_0$', r'$\beta_1$', r'Max $H_1$ life', 'Entropy', 'n significant']
    M = df_features[feat_cols].values.astype(float)
    # 列归一化（每个特征独立 0-1）
    M_norm = (M - M.min(axis=0)) / (M.max(axis=0) - M.min(axis=0) + 1e-12)
    im = ax_d.imshow(M_norm, aspect='auto', cmap='YlOrRd')
    ax_d.set_xticks(range(len(feat_labels)))
    ax_d.set_xticklabels(feat_labels, rotation=15, fontsize=8)
    ax_d.set_yticks(range(len(df_features)))
    ax_d.set_yticklabels(
        [f"LCZ {r['lcz_id']}" for _, r in df_features.iterrows()],
        fontsize=8
    )
    ax_d.set_title('(d) Topological feature heatmap (normalized)',
                   fontsize=11, fontweight='bold', loc='left')
    cbar = plt.colorbar(im, ax=ax_d, fraction=0.04, pad=0.02)
    cbar.set_label('Normalized', fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    # 在每格写数值
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            text_color = 'white' if M_norm[i, j] > 0.6 else 'black'
            ax_d.text(j, i, f"{M[i, j]:.0f}" if feat_cols[j] != 'persistence_entropy'
                      else f"{M[i, j]:.2f}",
                      ha='center', va='center',
                      fontsize=7, color=text_color)

    # ─── (e) Wasserstein distance matrix ───
    ax_e = fig.add_subplot(gs[1, 3:6])
    im2 = ax_e.imshow(W_mat, cmap='Blues')
    ax_e.set_xticks(range(n))
    ax_e.set_yticks(range(n))
    ax_e.set_xticklabels([f"LCZ {l}" for l in lcz_ids_used],
                         rotation=45, fontsize=8)
    ax_e.set_yticklabels([f"LCZ {l}" for l in lcz_ids_used], fontsize=8)
    ax_e.set_title('(e) $H_1$ Wasserstein distance matrix',
                   fontsize=11, fontweight='bold', loc='left')
    cbar2 = plt.colorbar(im2, ax=ax_e, fraction=0.04, pad=0.02)
    cbar2.set_label('Wasserstein-2 dist.', fontsize=8)
    cbar2.ax.tick_params(labelsize=7)
    # 写距离值
    for i in range(n):
        for j in range(n):
            if i != j:
                text_color = 'white' if W_mat[i, j] > W_mat.max() * 0.6 else 'black'
                ax_e.text(j, i, f"{W_mat[i, j]:.1f}",
                          ha='center', va='center',
                          fontsize=6, color=text_color)

    # 计算关键统计供论文使用（不再画 panel）
    max_w = W_mat[np.triu_indices(n, k=1)].max()
    min_w = W_mat[W_mat > 0].min()
    spread = max_w / min_w if min_w > 0 else 0

    plt.suptitle('Topological Data Analysis of 100-m UTCI Field  ·  Shenzhen, July 2020',
                 fontsize=12, fontweight='bold', y=0.98)

    fig_path = FIGURES_DIR / "fig06_tda_analysis.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    size_kb = fig_path.stat().st_size / 1e3
    log.info(f"\n  图表保存: {fig_path}")
    log.info(f"  文件大小: {size_kb:.1f} KB")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px")

    # === 7. 总结 ===
    log.info("\n" + "=" * 65)
    log.info("Phase 4 完成！TDA 分析关键结果:")
    log.info("=" * 65)
    log.info(f"  全市 $\beta_0$ 峰值:   {betti0.max()} @ {thresholds[betti0.argmax()]:.2f} °C")
    log.info(f"  全市 $\beta_1$ 峰值:   {betti1.max()} @ {thresholds[betti1.argmax()]:.2f} °C")
    log.info(f"  Persistence Entropy: {feats_city['persistence_entropy']:.3f}")
    log.info(f"  LCZ 间最大 W₂ 距离: {max_w:.2f}")
    log.info(f"  LCZ 间最小 W₂ 距离: {min_w:.2f}")
    log.info(f"  距离动态范围:    {spread:.1f}×")


if __name__ == "__main__":
    main()
