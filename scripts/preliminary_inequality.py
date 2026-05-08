"""
Path C: 初步热不平等分析（基于 LCZ + WorldPop，无 UTCI）

输入:
  - data/processed/shenzhen_lcz_100m_utm.tif  (LCZ 类型)
  - data/processed/shenzhen_pop_100m_utm.tif  (WorldPop 人口)

输出:
  - results/preliminary/lcz_thermal_summary.csv
  - results/preliminary/gini_decomposition.csv
  - results/preliminary/lorenz_data.csv
  - figures/fig01_preliminary_inequality.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import rioxarray as rxr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.figure_style import apply_paper_style
apply_paper_style()

from src.utils.config import PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.thermal_burden import (
    LCZ_AT_JUL_K, lcz_to_at, compute_thermal_burden_index, lcz_thermal_metadata
)
from src.analysis.gini import (
    gini_weighted, gini_decomposition, lorenz_curve, atkinson_index
)

log = get_logger("preliminary_inequality")
RESULTS_PRE = RESULTS_DIR / "preliminary"
RESULTS_PRE.mkdir(parents=True, exist_ok=True)


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Path C: 初步热不平等分析")
    log.info("=" * 65)

    # === 1. 加载对齐数据 ===
    log.info("\n[1] 加载已对齐的 LCZ + WorldPop 栅格")
    lcz_path = PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif"
    pop_path = PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif"

    lcz_da = rxr.open_rasterio(lcz_path, masked=True).squeeze()
    pop_da = rxr.open_rasterio(pop_path, masked=True).squeeze()
    log.info(f"    LCZ 形状:  {lcz_da.shape}")
    log.info(f"    Pop 形状:  {pop_da.shape}")

    # === 2. 转 LCZ -> 气温 -> 热负担 ===
    log.info("\n[2] 计算热负担代理（LCZ -> AT, 7 月）")
    at_arr = lcz_to_at(lcz_da.values, season='Jul')
    tbi_arr = compute_thermal_burden_index(at_arr, baseline_K=302.0)
    log.info(f"    AT 范围: {np.nanmin(at_arr):.2f} - {np.nanmax(at_arr):.2f} K")
    log.info(f"    TBI 范围: {np.nanmin(tbi_arr):.2f} - {np.nanmax(tbi_arr):.2f} K")

    # === 3. 构建分析数据表 ===
    log.info("\n[3] 构建分析数据表（每行 = 1 个 100m 栅格）")
    pop_arr = pop_da.values

    valid = (~np.isnan(lcz_da.values)) & (~np.isnan(pop_arr)) & (pop_arr > 0)
    log.info(f"    有效栅格 (LCZ ∩ pop>0): {valid.sum():,}")

    df = pd.DataFrame({
        'lcz':   lcz_da.values[valid].astype(int),
        'pop':   pop_arr[valid].astype(float),
        'AT_K':  at_arr[valid].astype(float),
        'AT_C':  at_arr[valid].astype(float) - 273.15,
        'TBI_K': tbi_arr[valid].astype(float),
    })

    # 加 LCZ 类型标签
    LCZ_NAMES = {
        1: "Compact high-rise", 2: "Compact mid-rise", 3: "Compact low-rise",
        4: "Open high-rise", 5: "Open mid-rise", 6: "Open low-rise",
        7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built",
        10: "Heavy industry", 11: "Dense trees", 12: "Scattered trees",
        13: "Bush, scrub", 14: "Low plants", 15: "Bare rock/paved",
        16: "Bare soil/sand", 17: "Water"
    }
    df['lcz_name'] = df['lcz'].map(LCZ_NAMES)
    df['lcz_type'] = np.where(df['lcz'] <= 10, 'Built-up', 'Natural')

    log.info(f"    总人口: {df['pop'].sum():,.0f}")
    log.info(f"    总人口加权 AT 均值: {np.average(df['AT_C'], weights=df['pop']):.2f} °C")

    # === 4. LCZ 层级统计 ===
    log.info("\n[4] LCZ 类型层级统计")
    lcz_summary = df.groupby('lcz').agg(
        name=('lcz_name', 'first'),
        type=('lcz_type', 'first'),
        n_grids=('pop', 'size'),
        total_pop=('pop', 'sum'),
        AT_C=('AT_C', 'first'),
        TBI_K=('TBI_K', 'first'),
    ).reset_index()
    lcz_summary['pop_share'] = lcz_summary['total_pop'] / lcz_summary['total_pop'].sum()
    lcz_summary['exposure_score'] = lcz_summary['total_pop'] * lcz_summary['TBI_K']
    lcz_summary['exposure_share'] = lcz_summary['exposure_score'] / lcz_summary['exposure_score'].sum()
    lcz_summary = lcz_summary.sort_values('TBI_K', ascending=False)

    log.info("\n    LCZ 类型 × 暴露评分:")
    log.info("    " + "-" * 75)
    log.info(f"    {'LCZ':<4} {'类型':<22} {'人口':>10} {'人口占比':>9} {'AT(C)':>7} {'暴露评分':>10}")
    log.info("    " + "-" * 75)
    for _, r in lcz_summary.iterrows():
        log.info(
            f"    {int(r['lcz']):>3d}  {r['name'][:20]:<22} "
            f"{int(r['total_pop']):>10,} {r['pop_share']:>8.1%} "
            f"{r['AT_C']:>7.2f} {r['exposure_score']:>10,.0f}"
        )
    log.info("    " + "-" * 75)

    lcz_summary.to_csv(RESULTS_PRE / "lcz_thermal_summary.csv", index=False)
    log.info(f"\n    已保存: {RESULTS_PRE / 'lcz_thermal_summary.csv'}")

    # === 5. Gini 系数 ===
    log.info("\n[5] Gini 不平等系数")
    log.info("-" * 65)

    # 总 Gini
    G_overall = gini_weighted(df['TBI_K'].values, df['pop'].values)
    log.info(f"    总 Gini (TBI):       {G_overall:.4f}")

    # 用 AT_C 也算一次
    G_AT = gini_weighted(df['AT_C'].values, df['pop'].values)
    log.info(f"    总 Gini (AT_C):      {G_AT:.4f}")

    # Atkinson 索引
    A_idx = atkinson_index(df['TBI_K'].values, df['pop'].values, epsilon=0.5)
    log.info(f"    Atkinson 指数:      {A_idx:.4f}")

    # === 6. Gini 分解（按 LCZ 类型）===
    log.info("\n[6] Gini 分解：建成区 vs 自然区")
    decomp_type = gini_decomposition(df, 'TBI_K', 'pop', 'lcz_type')
    log.info(f"    G_total:    {decomp_type['G_total']:.4f}")
    log.info(f"    G_between:  {decomp_type['G_between']:.4f}  ({decomp_type['between_share']:.1%})")
    log.info(f"    G_within:   {decomp_type['G_within']:.4f}  ({decomp_type['within_share']:.1%})")
    log.info(f"    G_overlap:  {decomp_type['G_overlap']:.4f}  ({decomp_type['overlap_share']:.1%})")

    log.info("\n[6b] Gini 分解：按 LCZ 大类（17 类）")
    decomp_lcz = gini_decomposition(df, 'TBI_K', 'pop', 'lcz')
    log.info(f"    G_total:    {decomp_lcz['G_total']:.4f}")
    log.info(f"    G_between:  {decomp_lcz['G_between']:.4f}  ({decomp_lcz['between_share']:.1%})")
    log.info(f"    G_within:   {decomp_lcz['G_within']:.4f}  ({decomp_lcz['within_share']:.1%})")

    # 保存分解结果
    decomp_records = []
    for label, decomp in [('LCZ_type', decomp_type), ('LCZ_class', decomp_lcz)]:
        decomp_records.append({
            'level': label,
            'G_total': decomp['G_total'],
            'G_between': decomp['G_between'],
            'G_within': decomp['G_within'],
            'G_overlap': decomp['G_overlap'],
            'between_share': decomp['between_share'],
            'within_share': decomp['within_share'],
        })
    pd.DataFrame(decomp_records).to_csv(
        RESULTS_PRE / "gini_decomposition.csv", index=False
    )

    # === 7. Lorenz 曲线 ===
    log.info("\n[7] Lorenz 曲线点")
    p, L = lorenz_curve(df['TBI_K'].values, df['pop'].values)
    pd.DataFrame({'cumulative_pop': p, 'cumulative_exposure': L}).to_csv(
        RESULTS_PRE / "lorenz_data.csv", index=False
    )
    log.info(f"    Lorenz 曲线点数: {len(p)}")

    # === 8. 关键洞察 ===
    log.info("\n[8] 关键洞察")
    log.info("-" * 65)

    top10_pct_pop = (1 - p > 0.1).sum() / len(p)
    # 找到最热 10% 人口承担多少暴露
    idx = np.searchsorted(p, 0.9)
    top10_exposure_share = 1 - L[idx] if idx < len(L) else 0

    log.info(f"\n    1) 最热环境 10% 的人口承担了: {top10_exposure_share:.1%} 的总热暴露")

    # 最低 50% 人口
    idx50 = np.searchsorted(p, 0.5)
    bottom50_exposure_share = L[idx50] if idx50 < len(L) else 0
    log.info(f"    2) 最凉环境 50% 的人口仅承担: {bottom50_exposure_share:.1%} 的总热暴露")

    # 最热 LCZ 与最凉 LCZ 的人口加权 AT 差
    hot_lcz = lcz_summary.iloc[0]
    cool_lcz = lcz_summary.iloc[-1]
    log.info(f"\n    3) 最热 LCZ {int(hot_lcz['lcz'])} ({hot_lcz['name']}): {hot_lcz['AT_C']:.2f}°C, {int(hot_lcz['total_pop']):,} 人")
    log.info(f"    4) 最凉 LCZ {int(cool_lcz['lcz'])} ({cool_lcz['name']}): {cool_lcz['AT_C']:.2f}°C, {int(cool_lcz['total_pop']):,} 人")
    log.info(f"    5) 极差 ΔAT = {hot_lcz['AT_C'] - cool_lcz['AT_C']:.2f} °C")

    # 高曝露 LCZ 类型（Top 5 by exposure_score）
    log.info(f"\n    6) 总热暴露贡献 Top 5 LCZ 类型:")
    for _, r in lcz_summary.nlargest(5, 'exposure_score').iterrows():
        log.info(f"       LCZ {int(r['lcz']):>2d} {r['name'][:22]:<24} "
                 f"贡献 {r['exposure_share']:>5.1%} 总暴露")

    # === 9. 可视化（一张总图）===
    log.info("\n[9] 生成可视化图")
    fig = plt.figure(figsize=(12, 8), dpi=110)

    # (a) Lorenz 曲线
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.4, label='Equality line')
    ax1.plot(p, L, 'r-', linewidth=2, label=f'Lorenz curve\nGini={G_overall:.3f}')
    ax1.fill_between(p, p, L, color='red', alpha=0.15)
    ax1.set_xlabel('Cumulative population share')
    ax1.set_ylabel('Cumulative thermal exposure share')
    ax1.set_title(f'(a) Population-weighted Lorenz curve (Shenzhen, Jul)')
    ax1.legend(loc='upper left')
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.grid(alpha=0.3)

    # (b) LCZ 暴露贡献条形图
    ax2 = fig.add_subplot(2, 2, 2)
    top10 = lcz_summary.nlargest(10, 'exposure_score')
    colors = ['#d73027' if t == 'Built-up' else '#1a9850' for t in top10['type']]
    bars = ax2.barh(
        [f"LCZ {int(l)}: {n[:18]}" for l, n in zip(top10['lcz'], top10['name'])],
        top10['exposure_share'] * 100,
        color=colors, alpha=0.8, edgecolor='black'
    )
    ax2.set_xlabel('Share of total thermal exposure (%)')
    ax2.set_title('(b) Top 10 LCZ contribution to thermal exposure')
    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.3)

    # 加图例（手工）
    from matplotlib.patches import Patch
    ax2.legend(handles=[
        Patch(facecolor='#d73027', label='Built-up LCZ'),
        Patch(facecolor='#1a9850', label='Natural LCZ'),
    ], loc='lower right')

    # (c) 各 LCZ 平均 AT 与人口
    ax3 = fig.add_subplot(2, 2, 3)
    sub = lcz_summary[lcz_summary['type'] == 'Built-up'].sort_values('lcz')
    sizes = sub['total_pop'] / 1e4  # 万人
    ax3.scatter(sub['lcz'], sub['AT_C'],
                s=np.clip(sizes, 20, 500),
                c=sub['TBI_K'], cmap='Reds',
                edgecolor='black', alpha=0.8)
    for _, r in sub.iterrows():
        ax3.annotate(f"LCZ{int(r['lcz'])}",
                     (r['lcz'], r['AT_C']),
                     textcoords="offset points", xytext=(5, 5), fontsize=9)
    ax3.set_xlabel('LCZ class (Built-up)')
    ax3.set_ylabel('Air Temperature (°C)')
    ax3.set_title('(c) Built-up LCZ thermal levels (size = population)')
    ax3.grid(alpha=0.3)

    # (d) Gini 分解
    ax4 = fig.add_subplot(2, 2, 4)
    components = ['Between\nLCZ types', 'Within\nLCZ types', 'Overlap']
    values_pct = [decomp_type['between_share']*100,
                  decomp_type['within_share']*100,
                  decomp_type['overlap_share']*100]
    colors_d = ['#fc8d59', '#91bfdb', '#999999']
    bars = ax4.bar(components, values_pct, color=colors_d, edgecolor='black')
    for bar, val in zip(bars, values_pct):
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., h,
                 f'{val:.1f}%', ha='center', va='bottom' if h > 0 else 'top')
    ax4.axhline(0, color='black', linewidth=0.5)
    ax4.set_ylabel('Share of total Gini (%)')
    ax4.set_title(f'(d) Gini decomposition (Total G={decomp_type["G_total"]:.3f})')
    ax4.grid(axis='y', alpha=0.3)

    plt.suptitle('Preliminary Thermal Inequality Analysis (Shenzhen, Jul 2026)\n'
                 'Based on LCZ × WorldPop, AT proxy from Huang et al. 2026',
                 fontsize=12, y=1.02)
    plt.tight_layout()

    fig_path = FIGURES_DIR / "fig01_preliminary_inequality.png"
    plt.savefig(fig_path, dpi=110, bbox_inches='tight')
    plt.close()
    log.info(f"    图表保存: {fig_path}")
    log.info(f"    文件大小: {fig_path.stat().st_size / 1e3:.1f} KB")

    # === 10. 完结摘要 ===
    log.info("\n" + "=" * 65)
    log.info("Path C 完成！主要产出:")
    log.info("=" * 65)
    log.info(f"  CSV:  {RESULTS_PRE}")
    log.info(f"  图:   {fig_path}")
    log.info(f"\n  全市人口加权 Gini: {G_overall:.4f}")
    log.info(f"  最热与最凉 LCZ 极差: {hot_lcz['AT_C'] - cool_lcz['AT_C']:.2f} °C")
    log.info(f"\n  注: 当前用文章一 Table 4 的 LCZ-AT 值代替 UTCI；")
    log.info(f"       获取 ERA5-HEAT UTCI 后可升级为完整热舒适不平等。")


if __name__ == "__main__":
    main()
