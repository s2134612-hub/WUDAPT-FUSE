"""
基于真实 UTCI 的热不平等分析（Phase 2 升级版）。

输入:
  data/processed/shenzhen_utci_100m_jul_summary.nc  (UTCI 汇总)
  data/processed/shenzhen_pop_100m_utm.tif          (人口)

输出:
  results/utci/utci_lcz_summary.csv
  results/utci/utci_gini_decomposition.csv
  figures/fig03_utci_inequality.png
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
from src.analysis.gini import gini_weighted, gini_decomposition, lorenz_curve, atkinson_index

log = get_logger("utci_inequality")
RESULTS_UTCI = RESULTS_DIR / "utci"
RESULTS_UTCI.mkdir(parents=True, exist_ok=True)


LCZ_NAMES = {
    1: "Compact high-rise", 2: "Compact mid-rise", 3: "Compact low-rise",
    4: "Open high-rise", 5: "Open mid-rise", 6: "Open low-rise",
    7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built",
    10: "Heavy industry", 11: "Dense trees", 12: "Scattered trees",
    13: "Bush, scrub", 14: "Low plants", 15: "Bare rock/paved",
    16: "Bare soil/sand", 17: "Water"
}


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 2: 真实 UTCI 不平等分析")
    log.info("=" * 65)

    # === 1. 加载 UTCI 汇总数据 ===
    log.info("\n[1] 加载 UTCI summary")
    utci_path = PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc"
    utci_ds = xr.open_dataset(utci_path)
    log.info(f"    Variables: {list(utci_ds.data_vars)}")
    log.info(f"    Shape: {utci_ds['utci_mean'].shape}")

    # 给 UTCI 数据集补充 CRS 与正式的 x/y 维度坐标
    utci_with_crs = utci_ds.assign_coords(
        x=('x', utci_ds.lon.values),
        y=('y', utci_ds.lat.values)
    )
    utci_with_crs = utci_with_crs.rio.write_crs("EPSG:4326")
    utci_template = utci_with_crs['utci_mean']

    # === 2. 加载并对齐人口数据 ===
    log.info("\n[2] 加载并对齐人口数据")
    pop_utm_path = PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif"
    pop_utm = rxr.open_rasterio(pop_utm_path, masked=True).squeeze()

    # 把 pop UTM 重投影并对齐到 UTCI WGS84 网格
    pop_aligned = pop_utm.rio.reproject_match(
        utci_template,
        resampling=Resampling.bilinear
    )
    pop_wgs = pop_aligned
    log.info(f"    Pop 对齐后形状: {pop_wgs.shape}")

    # === 3. 构建分析数据表 ===
    log.info("\n[3] 构建分析数据表（每行 = 1 个 100m 栅格）")

    utci_mean = utci_ds['utci_mean'].values
    utci_max = utci_ds['utci_max'].values
    utci_p95 = utci_ds['utci_p95'].values
    tsd_strong = utci_ds['tsd_strong'].values
    tsd_moderate = utci_ds['tsd_moderate'].values
    hdh = utci_ds['hdh'].values
    lcz = utci_ds['lcz'].values
    pop = pop_wgs.values

    valid = (
        ~np.isnan(utci_mean) & ~np.isnan(lcz) & ~np.isnan(pop) & (pop > 0)
    )
    log.info(f"    有效栅格数: {valid.sum():,}")

    df = pd.DataFrame({
        'lcz':         lcz[valid].astype(int),
        'pop':         pop[valid].astype(float),
        'utci_mean':   utci_mean[valid],
        'utci_max':    utci_max[valid],
        'utci_p95':    utci_p95[valid],
        'tsd_strong':  tsd_strong[valid],
        'tsd_moderate':tsd_moderate[valid],
        'hdh':         hdh[valid],
    })

    df['lcz_name'] = df['lcz'].map(LCZ_NAMES)
    df['lcz_type'] = np.where(df['lcz'] <= 10, 'Built-up', 'Natural')

    log.info(f"    总人口（有效栅格）: {df['pop'].sum():,.0f}")
    log.info(f"    人口加权 UTCI 均值: {np.average(df['utci_mean'], weights=df['pop']):.2f} °C")
    log.info(f"    人口加权 TSD 均值:  {np.average(df['tsd_strong'], weights=df['pop']):.1f} hr")

    # === 4. LCZ 层级统计 ===
    log.info("\n[4] LCZ 层级统计")
    lcz_summary = df.groupby('lcz').agg(
        name=('lcz_name', 'first'),
        type=('lcz_type', 'first'),
        n_grids=('pop', 'size'),
        total_pop=('pop', 'sum'),
        utci_mean=('utci_mean', 'mean'),
        utci_max=('utci_max', 'max'),
        tsd_strong=('tsd_strong', 'mean'),
        hdh=('hdh', 'mean'),
    ).reset_index()
    lcz_summary['pop_share'] = lcz_summary['total_pop'] / lcz_summary['total_pop'].sum()
    lcz_summary['weighted_exposure'] = lcz_summary['total_pop'] * lcz_summary['hdh']
    lcz_summary['exposure_share'] = lcz_summary['weighted_exposure'] / lcz_summary['weighted_exposure'].sum()
    lcz_summary = lcz_summary.sort_values('utci_mean', ascending=False)

    log.info("\n    LCZ × UTCI 暴露:")
    log.info("    " + "-" * 90)
    log.info(f"    {'LCZ':<4} {'类型':<22} {'人口':>10} {'占比':>6} {'UTCI均':>7} {'UTCI峰':>7} {'TSD':>6} {'HDH':>7} {'暴露占比':>8}")
    log.info("    " + "-" * 90)
    for _, r in lcz_summary.iterrows():
        log.info(
            f"    {int(r['lcz']):>3d}  {r['name'][:20]:<22} "
            f"{int(r['total_pop']):>10,} {r['pop_share']:>5.1%} "
            f"{r['utci_mean']:>7.2f} {r['utci_max']:>7.2f} "
            f"{r['tsd_strong']:>6.1f} {r['hdh']:>7.0f} "
            f"{r['exposure_share']:>7.1%}"
        )
    log.info("    " + "-" * 90)
    lcz_summary.to_csv(RESULTS_UTCI / "utci_lcz_summary.csv", index=False)

    # === 5. Gini 系数 ===
    log.info("\n[5] Gini 不平等系数（多指标）")
    log.info("-" * 65)

    metrics = {
        'utci_mean': 'UTCI 7-day mean (°C)',
        'utci_max':  'UTCI peak (°C)',
        'utci_p95':  'UTCI 95th percentile (°C)',
        'tsd_strong': 'Strong heat stress hours (UTCI>32°C)',
        'hdh':       'Heat Degree Hours (累计>26°C)',
    }

    gini_results = {}
    for col, desc in metrics.items():
        G = gini_weighted(df[col].values, df['pop'].values)
        gini_results[col] = G
        log.info(f"    {desc:<45} Gini = {G:.4f}")

    # Atkinson
    A_idx = atkinson_index(df['hdh'].values, df['pop'].values, epsilon=0.5)
    log.info(f"    Atkinson(epsilon=0.5)                          = {A_idx:.4f}")

    # === 6. 三层 Gini 分解 ===
    log.info("\n[6] Gini 三层分解（建成 vs 自然，按 LCZ 类型）")
    log.info("-" * 65)

    decomp_records = []
    for col in ['utci_mean', 'tsd_strong', 'hdh']:
        for group_col in ['lcz_type', 'lcz']:
            decomp = gini_decomposition(df, col, 'pop', group_col)
            log.info(f"\n  指标: {col}, 分组: {group_col}")
            log.info(f"    G_total:    {decomp['G_total']:.4f}")
            log.info(f"    G_between:  {decomp['G_between']:.4f}  ({decomp['between_share']:>5.1%})")
            log.info(f"    G_within:   {decomp['G_within']:.4f}  ({decomp['within_share']:>5.1%})")
            log.info(f"    G_overlap:  {decomp['G_overlap']:.4f}  ({decomp['overlap_share']:>5.1%})")
            decomp_records.append({
                'metric': col,
                'group': group_col,
                'G_total': decomp['G_total'],
                'G_between': decomp['G_between'],
                'G_within': decomp['G_within'],
                'G_overlap': decomp['G_overlap'],
                'between_share': decomp['between_share'],
                'within_share': decomp['within_share'],
                'overlap_share': decomp['overlap_share'],
            })

    pd.DataFrame(decomp_records).to_csv(
        RESULTS_UTCI / "utci_gini_decomposition.csv", index=False
    )

    # === 7. Lorenz 曲线 ===
    log.info("\n[7] Lorenz 曲线")
    p_mean, L_mean = lorenz_curve(df['utci_mean'].values, df['pop'].values)
    p_tsd, L_tsd = lorenz_curve(df['tsd_strong'].values, df['pop'].values)
    p_hdh, L_hdh = lorenz_curve(df['hdh'].values, df['pop'].values)

    pd.DataFrame({
        'cumpop': p_hdh,
        'L_utci_mean': np.interp(p_hdh, p_mean, L_mean),
        'L_tsd': np.interp(p_hdh, p_tsd, L_tsd),
        'L_hdh': L_hdh,
    }).to_csv(RESULTS_UTCI / "utci_lorenz_curves.csv", index=False)

    # === 8. 关键洞察 ===
    log.info("\n[8] 关键洞察 (相比 Path C 的代理 Gini = 0.0272)")
    log.info("-" * 65)

    G_utci_mean = gini_results['utci_mean']
    G_hdh = gini_results['hdh']
    G_tsd = gini_results['tsd_strong']

    log.info(f"\n  1) 人口加权 Gini (真实 UTCI): {G_utci_mean:.4f}")
    log.info(f"     vs Path C (LCZ-AT 代理):    0.0272")
    log.info(f"     提升倍数: {G_utci_mean/0.0272:.1f}x")

    # 最热 10%
    idx = np.searchsorted(p_hdh, 0.9)
    top10_hdh = 1 - L_hdh[idx] if idx < len(L_hdh) else 0
    log.info(f"\n  2) 最热 10% 人口承担 {top10_hdh:.1%} 的 HDH (vs Path C 10.5%)")

    # 最凉 50%
    idx50 = np.searchsorted(p_hdh, 0.5)
    bottom50 = L_hdh[idx50] if idx50 < len(L_hdh) else 0
    log.info(f"     最凉 50% 人口仅承担 {bottom50:.1%} 的 HDH (vs Path C 47.9%)")

    hot_lcz = lcz_summary.iloc[0]
    cool_lcz = lcz_summary.iloc[-1]
    delta_t = hot_lcz['utci_mean'] - cool_lcz['utci_mean']
    log.info(f"\n  3) 最热 LCZ {int(hot_lcz['lcz'])} ({hot_lcz['name']}): UTCI {hot_lcz['utci_mean']:.2f}°C, TSD {hot_lcz['tsd_strong']:.1f} hr")
    log.info(f"     最凉 LCZ {int(cool_lcz['lcz'])} ({cool_lcz['name']}): UTCI {cool_lcz['utci_mean']:.2f}°C, TSD {cool_lcz['tsd_strong']:.1f} hr")
    log.info(f"     极差 ΔUTCI = {delta_t:.2f} °C  (vs Path C 1.40°C)")

    log.info(f"\n  4) HDH 暴露贡献 Top 5 LCZ:")
    for _, r in lcz_summary.nlargest(5, 'weighted_exposure').iterrows():
        log.info(f"       LCZ {int(r['lcz']):>2d} {r['name'][:24]:<26} 贡献 {r['exposure_share']:>5.1%} 总 HDH 暴露")

    # === 9. 可视化 ===
    log.info("\n[9] 生成可视化图")
    fig = plt.figure(figsize=(13, 9), dpi=110)

    # (a) Lorenz 曲线 - 多指标
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.4, label='Equality')
    ax1.plot(p_mean, L_mean, '-', color='#fc8d59', linewidth=2,
             label=f"UTCI mean (G={G_utci_mean:.3f})")
    ax1.plot(p_tsd, L_tsd, '-', color='#d73027', linewidth=2,
             label=f"TSD>32°C (G={G_tsd:.3f})")
    ax1.plot(p_hdh, L_hdh, '-', color='#a50026', linewidth=2,
             label=f"HDH (G={G_hdh:.3f})")
    ax1.set_xlabel('Cumulative population share')
    ax1.set_ylabel('Cumulative thermal exposure share')
    ax1.set_title('(a) Lorenz curves (real UTCI)')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(alpha=0.3)

    # (b) Top 10 LCZ HDH 暴露贡献
    ax2 = fig.add_subplot(2, 3, 2)
    top10 = lcz_summary.nlargest(10, 'weighted_exposure')
    colors = ['#d73027' if t == 'Built-up' else '#1a9850' for t in top10['type']]
    ax2.barh(
        [f"LCZ {int(l)}: {n[:18]}" for l, n in zip(top10['lcz'], top10['name'])],
        top10['exposure_share'] * 100,
        color=colors, alpha=0.8, edgecolor='black'
    )
    ax2.set_xlabel('Share of total HDH exposure (%)')
    ax2.set_title('(b) Top 10 LCZ contribution to HDH')
    ax2.invert_yaxis()
    ax2.grid(axis='x', alpha=0.3)

    # (c) UTCI mean vs TSD scatter
    ax3 = fig.add_subplot(2, 3, 3)
    sub = lcz_summary[lcz_summary['type'] == 'Built-up'].sort_values('lcz')
    sizes = np.clip(sub['total_pop'] / 1e4, 30, 600)
    sc = ax3.scatter(sub['utci_mean'], sub['tsd_strong'],
                     s=sizes, c=sub['lcz'], cmap='tab10',
                     edgecolor='black', alpha=0.8)
    for _, r in sub.iterrows():
        ax3.annotate(f"LCZ{int(r['lcz'])}",
                     (r['utci_mean'], r['tsd_strong']),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax3.set_xlabel('Mean UTCI (°C)')
    ax3.set_ylabel('TSD > 32°C (hours)')
    ax3.set_title('(c) Built-up LCZ heat stress (size = pop)')
    ax3.grid(alpha=0.3)

    # (d) Gini 分解（UTCI mean by lcz_type）
    ax4 = fig.add_subplot(2, 3, 4)
    decomp_btype = [d for d in decomp_records if d['metric'] == 'utci_mean' and d['group'] == 'lcz_type'][0]
    components = ['Between\nLCZ types', 'Within\nLCZ types', 'Overlap']
    values_pct = [decomp_btype['between_share']*100,
                  decomp_btype['within_share']*100,
                  decomp_btype['overlap_share']*100]
    colors_d = ['#fc8d59', '#91bfdb', '#999999']
    bars = ax4.bar(components, values_pct, color=colors_d, edgecolor='black')
    for bar, val in zip(bars, values_pct):
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., h,
                 f'{val:.1f}%', ha='center', va='bottom' if h > 0 else 'top')
    ax4.axhline(0, color='black', linewidth=0.5)
    ax4.set_ylabel('Share of total Gini (%)')
    ax4.set_title(f"(d) UTCI Gini decomposition (G={decomp_btype['G_total']:.3f})")
    ax4.grid(axis='y', alpha=0.3)

    # (e) UTCI 分布直方图（人口加权）
    ax5 = fig.add_subplot(2, 3, 5)
    bins = np.linspace(df['utci_mean'].min(), df['utci_mean'].max(), 30)
    ax5.hist(df['utci_mean'], bins=bins, weights=df['pop'],
             color='#fc8d59', alpha=0.7, edgecolor='black', label='Pop weighted')
    ax5.axvline(np.average(df['utci_mean'], weights=df['pop']), color='red',
                linewidth=2, label=f"Mean = {np.average(df['utci_mean'], weights=df['pop']):.2f}°C")
    ax5.set_xlabel('Mean UTCI (°C)')
    ax5.set_ylabel('Population (cumulative)')
    ax5.set_title('(e) Population distribution of UTCI exposure')
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)

    # (f) 比较 Path C vs Phase 2 Gini
    ax6 = fig.add_subplot(2, 3, 6)
    methods = ['Path C\n(LCZ-AT proxy)', 'Phase 2\n(real UTCI)', 'Phase 2\n(TSD)', 'Phase 2\n(HDH)']
    ginis = [0.0272, G_utci_mean, G_tsd, G_hdh]
    colors_g = ['#999999', '#fc8d59', '#d73027', '#a50026']
    bars = ax6.bar(methods, ginis, color=colors_g, edgecolor='black')
    for bar, g in zip(bars, ginis):
        h = bar.get_height()
        ax6.text(bar.get_x() + bar.get_width()/2., h,
                 f'{g:.3f}', ha='center', va='bottom', fontsize=10)
    ax6.set_ylabel('Population-weighted Gini')
    ax6.set_title('(f) Gini comparison: proxy vs real UTCI')
    ax6.grid(axis='y', alpha=0.3)

    plt.suptitle('Phase 2: Real UTCI Thermal Inequality (Shenzhen, Jul 15-21, 2020)\n'
                 'ERA5-HEAT 25km × LCZ 100m fused via deviation injection',
                 fontsize=12, y=1.01)
    plt.tight_layout()

    fig_path = FIGURES_DIR / "fig03_utci_inequality.png"
    plt.savefig(fig_path, dpi=110, bbox_inches='tight')
    plt.close()
    log.info(f"    图表保存: {fig_path}")
    log.info(f"    文件大小: {fig_path.stat().st_size/1e3:.1f} KB")

    # === 10. 总结 ===
    log.info("\n" + "=" * 65)
    log.info("Phase 2 完成！主要产出:")
    log.info("=" * 65)
    log.info(f"  CSV 目录: {RESULTS_UTCI}")
    log.info(f"  图表:     {fig_path}")
    log.info(f"\n  Gini (UTCI mean): {G_utci_mean:.4f}  ({G_utci_mean/0.0272:.1f}x Path C)")
    log.info(f"  Gini (HDH):       {G_hdh:.4f}")
    log.info(f"  ΔUTCI 极差:       {delta_t:.2f} °C  ({delta_t/1.4:.1f}x Path C)")


if __name__ == "__main__":
    main()
