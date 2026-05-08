"""
LCZ 亚类聚类（k-means + Silhouette 选 K）。

输入:
  data/processed/shenzhen_umps_100m.nc

输出:
  data/processed/shenzhen_lcz_subcategories_100m.nc  含 'lcz_subcat' 整数标签
  results/subcategories/clustering_summary.csv
  figures/fig04_lcz_subcategories.png

每个建成 LCZ (1-10) 内部用 UMPs 做 k-means 聚类，
K 值从 2 到 5 中根据 Silhouette score 选择。
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import xarray as xr
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

log = get_logger("lcz_subcat")

LCZ_NAMES = {
    1: "Compact high-rise", 2: "Compact mid-rise", 3: "Compact low-rise",
    4: "Open high-rise", 5: "Open mid-rise", 6: "Open low-rise",
    7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built",
    10: "Heavy industry"
}

CLUSTER_FEATURES = ['bsf', 'mbh', 'sbh', 'mbw', 'svf', 'psf', 'gfa', 'bv']


def select_optimal_k(X, k_range=range(2, 6), random_state=42):
    """在多个 K 中选 Silhouette 最大的"""
    if len(X) < 50:
        return 2, 0.0  # 数据少，默认 2 类

    best_k, best_sil = 2, -1
    silhouettes = {}

    for k in k_range:
        if len(X) < k * 5:
            continue
        try:
            km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            labels = km.fit_predict(X)
            if len(set(labels)) < 2:
                continue
            # 大数据时仅采样 5000 个评估 silhouette（节省时间）
            if len(X) > 5000:
                idx = np.random.RandomState(random_state).choice(
                    len(X), 5000, replace=False
                )
                sil = silhouette_score(X[idx], labels[idx])
            else:
                sil = silhouette_score(X, labels)
            silhouettes[k] = sil
            if sil > best_sil:
                best_sil = sil
                best_k = k
        except Exception as e:
            log.warning(f"    k={k} 失败: {e}")

    return best_k, best_sil, silhouettes


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("LCZ 亚类聚类")
    log.info("=" * 65)

    # === 1. 加载 UMPs ===
    log.info("\n[1] 加载 UMPs")
    umps_path = PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc"
    if not umps_path.exists():
        log.error(f"  UMPs 文件不存在: {umps_path}")
        log.error(f"  请先运行: python scripts/compute_umps.py")
        return False

    ds = xr.open_dataset(umps_path)
    log.info(f"  UMP 变量: {list(ds.data_vars)}")
    log.info(f"  形状: {ds['bsf'].shape}")

    lcz = ds['lcz'].values
    H, W = lcz.shape

    # === 2. 对每个建成 LCZ 单独聚类 ===
    log.info("\n[2] 对每个建成 LCZ 进行 k-means")

    subcat_grid = np.full_like(lcz, np.nan)  # 大类 + 小类编码: lcz*10+sub_label
    subcat_id_grid = np.full_like(lcz, np.nan, dtype=np.int32)  # 全局唯一亚类 ID

    next_id = 0
    cluster_summary = []

    for lcz_id in range(1, 11):
        mask = (lcz == lcz_id)
        n_cells = mask.sum()
        if n_cells < 10:
            log.info(f"\n  LCZ {lcz_id}: 仅 {n_cells} 栅格，跳过")
            continue

        log.info(f"\n  LCZ {lcz_id} ({LCZ_NAMES[lcz_id]}): {n_cells:,} 栅格")

        # 提取这个 LCZ 类的 UMPs
        X = np.column_stack([ds[f].values[mask] for f in CLUSTER_FEATURES])

        # 跳过全 NaN 或 all-zero
        valid_mask = ~np.isnan(X).any(axis=1)
        X_valid = X[valid_mask]
        if len(X_valid) < 50:
            log.warning(f"    有效数据少 ({len(X_valid)})，跳过")
            continue

        # 标准化
        scaler = StandardScaler()
        X_std = scaler.fit_transform(X_valid)

        # 选 K
        best_k, best_sil, sils = select_optimal_k(X_std)
        log.info(f"    最佳 K={best_k}, Silhouette={best_sil:.3f}")
        log.info(f"    Silhouettes: {sils}")

        # 用最佳 K 做最终聚类
        km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        labels = km.fit_predict(X_std)

        # 排序：按 BSF 递增重命名标签（A=lowest BSF, B=next, etc.）
        cluster_means = pd.DataFrame(X_valid, columns=CLUSTER_FEATURES)
        cluster_means['_cl'] = labels
        order = cluster_means.groupby('_cl')['bsf'].mean().sort_values().index.tolist()
        relabel = {old: new for new, old in enumerate(order)}
        labels_sorted = np.array([relabel[l] for l in labels])

        # 把标签放回原网格（注意：valid_mask 是基于 mask 内的有效栅格）
        full_labels = np.full(n_cells, -1, dtype=np.int32)
        full_labels[valid_mask] = labels_sorted

        # 把 lcz_id*10 + sublabel 放到主网格中
        # 例如 LCZ 1 的 sub A = 11, sub B = 12, sub C = 13, sub D = 14
        valid_pos = np.where(mask)
        for k_idx in range(len(valid_pos[0])):
            yi, xi = valid_pos[0][k_idx], valid_pos[1][k_idx]
            sub = full_labels[k_idx]
            if sub >= 0:
                subcat_grid[yi, xi] = lcz_id * 10 + sub  # e.g., 11, 12, 13
                subcat_id_grid[yi, xi] = next_id + sub

        # 记录每个亚类的统计
        for sub_idx in range(best_k):
            sub_letter = chr(ord('A') + sub_idx)
            cell_mask_sub = full_labels == sub_idx
            n_sub = cell_mask_sub.sum()
            if n_sub > 0:
                row = {
                    'global_id': next_id + sub_idx,
                    'lcz_id': lcz_id,
                    'lcz_name': LCZ_NAMES[lcz_id],
                    'subcategory': f"{lcz_id}{sub_letter}",
                    'n_grids': int(n_sub),
                    'bsf_mean': float(X_valid[cell_mask_sub, 0].mean()),
                    'mbh_mean': float(X_valid[cell_mask_sub, 1].mean()),
                    'sbh_mean': float(X_valid[cell_mask_sub, 2].mean()),
                    'svf_mean': float(X_valid[cell_mask_sub, 4].mean()),
                    'psf_mean': float(X_valid[cell_mask_sub, 5].mean()),
                    'bv_mean':  float(X_valid[cell_mask_sub, 7].mean()),
                    'silhouette': float(best_sil),
                }
                cluster_summary.append(row)

        next_id += best_k

    # === 3. 保存亚类网格与统计 ===
    log.info("\n[3] 保存输出")

    # 保存为 NetCDF
    out_ds = xr.Dataset(
        {
            'lcz':         (('y', 'x'), lcz),
            'subcat_code': (('y', 'x'), subcat_grid.astype(np.float32)),  # e.g., 11, 12, 13
            'subcat_id':   (('y', 'x'), subcat_id_grid),  # global ID
        },
        coords={
            'y': ds.y.values,
            'x': ds.x.values,
        }
    )
    out_ds.attrs['source'] = 'k-means clustering of UMPs within each built-up LCZ'
    out_ds.attrs['features'] = ', '.join(CLUSTER_FEATURES)

    out_path = PROCESSED_DATA_DIR / "shenzhen_lcz_subcategories_100m.nc"
    out_ds.to_netcdf(out_path)
    log.info(f"  亚类网格: {out_path}")

    # 保存 summary CSV
    df_sum = pd.DataFrame(cluster_summary)
    summary_dir = RESULTS_DIR / "subcategories"
    summary_dir.mkdir(parents=True, exist_ok=True)
    csv_path = summary_dir / "clustering_summary.csv"
    df_sum.to_csv(csv_path, index=False)
    log.info(f"  统计: {csv_path}")
    log.info(f"  共 {len(df_sum)} 个亚类")

    log.info("\n[4] 亚类汇总:")
    log.info(df_sum[['subcategory', 'n_grids', 'bsf_mean', 'mbh_mean', 'svf_mean', 'silhouette']].to_string(index=False))

    # === 4. 可视化 ===
    log.info("\n[5] 生成图表")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), dpi=110)

    # (a) 亚类数量分布
    ax = axes[0, 0]
    n_sub_per_lcz = df_sum.groupby('lcz_id')['subcategory'].count()
    bars = ax.bar(n_sub_per_lcz.index, n_sub_per_lcz.values,
                  color=plt.cm.tab10(np.arange(len(n_sub_per_lcz))/10),
                  edgecolor='black')
    for bar, v in zip(bars, n_sub_per_lcz.values):
        ax.text(bar.get_x()+bar.get_width()/2, v+0.05, str(v),
                ha='center', va='bottom')
    ax.set_xlabel('LCZ class')
    ax.set_ylabel('Number of subcategories')
    ax.set_title('(a) Subcategories per built-up LCZ')
    ax.grid(axis='y', alpha=0.3)

    # (b) 亚类 BSF vs MBH 散点
    ax = axes[0, 1]
    for _, r in df_sum.iterrows():
        ax.scatter(r['bsf_mean'], r['mbh_mean'],
                   s=np.clip(r['n_grids']/50, 50, 800),
                   c=[plt.cm.tab10(r['lcz_id']/10)],
                   edgecolor='black', alpha=0.7)
        ax.annotate(r['subcategory'],
                   (r['bsf_mean'], r['mbh_mean']),
                   xytext=(3, 3), textcoords='offset points',
                   fontsize=8)
    ax.set_xlabel('BSF (Building Surface Fraction)')
    ax.set_ylabel('MBH (Mean Building Height, m)')
    ax.set_title('(b) Subcategory positions (size = n grids)')
    ax.grid(alpha=0.3)

    # (c) Silhouette per LCZ
    ax = axes[1, 0]
    sil_per_lcz = df_sum.groupby('lcz_id')['silhouette'].first()
    bars = ax.bar(sil_per_lcz.index, sil_per_lcz.values,
                  color=plt.cm.RdYlGn(sil_per_lcz.values/0.5),
                  edgecolor='black')
    ax.axhline(0.25, color='red', linestyle='--', label='Weak (0.25)')
    ax.axhline(0.5, color='green', linestyle='--', label='Strong (0.50)')
    ax.set_xlabel('LCZ class')
    ax.set_ylabel('Silhouette score')
    ax.set_title('(c) Clustering quality by LCZ')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # (d) UMP 雷达图（所有 LCZ 1 的亚类对比）
    ax = axes[1, 1]
    lcz1_subs = df_sum[df_sum['lcz_id'] == 1]
    if len(lcz1_subs) > 0:
        feats = ['bsf_mean', 'mbh_mean', 'sbh_mean', 'svf_mean', 'psf_mean']
        feat_labels = ['BSF', 'MBH', 'SBH', 'SVF', 'PSF']
        # 标准化每个 feature
        for i, r in lcz1_subs.iterrows():
            vals = [r[f] for f in feats]
            # 把 MBH/SBH 缩放到 0-1
            vals_norm = [
                vals[0],          # BSF [0,1]
                vals[1] / 100,    # MBH 0-100m
                vals[2] / 30,     # SBH 0-30m
                vals[3],          # SVF [0,1]
                vals[4],          # PSF [0,1]
            ]
            ax.plot(range(len(feats)), vals_norm, 'o-', label=r['subcategory'])
        ax.set_xticks(range(len(feats)))
        ax.set_xticklabels(feat_labels)
        ax.legend()
        ax.set_title('(d) LCZ 1 subcategories morphology')
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.3)
    else:
        ax.text(0.5, 0.5, 'No LCZ 1 data', ha='center', transform=ax.transAxes)

    plt.tight_layout()
    fig_path = FIGURES_DIR / "fig04_lcz_subcategories.png"
    plt.savefig(fig_path, dpi=110, bbox_inches='tight')
    plt.close()
    log.info(f"  图表保存: {fig_path}  ({fig_path.stat().st_size/1e3:.1f} KB)")

    log.info("\n🎉 LCZ 亚类聚类完成！")
    log.info(f"   总亚类数: {len(df_sum)}")
    log.info("\n下一步: python scripts/subcategory_inequality.py")
    return True


if __name__ == "__main__":
    main()
