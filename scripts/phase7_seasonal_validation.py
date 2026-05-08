"""
Phase 7 (L2): 季节稳健性验证

测试假设:
  - 地理效应（Coast/Mountain）在 4 季都成立
  - 海陆风强度因季节变化（夏季最强）
  - 山区效应较稳定（受地理几何而非季节性环流主导）

输入:
  data/raw/era5/era5_heat_shenzhen_2020_01.nc (Jan)
  data/raw/era5/era5_heat_shenzhen_2020_04.nc (Apr)
  data/raw/era5/era5_heat_shenzhen_2020_07.nc (Jul, 已合成)
  data/raw/era5/era5_heat_shenzhen_2020_10.nc (Oct)

输出:
  results/phase7/seasonal_gini_comparison.csv
  figures/fig11_seasonal_robustness.png
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
from rasterio.enums import Resampling
from scipy.ndimage import distance_transform_edt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.utils.figure_style import apply_paper_style
apply_paper_style()

from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.gini import gini_decomposition

log = get_logger("phase7_seasonal")
RESULTS_P7 = RESULTS_DIR / "phase7"
RESULTS_P7.mkdir(parents=True, exist_ok=True)

# 各月份的 LCZ-AT 基准值（从文献估算，基础温度反映季节性差异）
# Jan/winter: cool, Apr/spring: mild, Jul/summer: hot, Oct/autumn: warm
SEASONAL_AT_OFFSET = {
    '01': 290.0,  # winter (~17°C base)
    '04': 297.0,  # spring (~24°C base)
    '07': 302.0,  # summer (~29°C base, matches Paper 1 Table 4)
    '10': 298.0,  # autumn (~25°C base)
}


def extract_zip_to_nc(zip_path, extract_dir):
    """解压 ERA5 zip"""
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
    nc_files = sorted(extract_dir.glob("ECMWF_utci_*.nc"))
    return nc_files


def synthesize_utci_for_month(month, base_temp_K):
    """
    合成某月 100m UTCI（向量化）
    - 加载该月日数据
    - 用季节性基础温度 + LCZ 偏差注入
    """
    era5_dir = RAW_DATA_DIR / "era5"

    # 主文件可能是 ZIP 或 NC
    main_file = era5_dir / f"era5_heat_shenzhen_2020_{month}.nc"
    if not main_file.exists():
        log.warning(f"  缺失: {main_file.name}")
        return None

    # 检查是否是 ZIP
    with open(main_file, 'rb') as f:
        magic = f.read(4)

    if magic == b'PK\x03\x04':  # ZIP
        log.info(f"  解压 ZIP: {main_file.name}")
        extract_dir = era5_dir / f"extracted_{month}"
        nc_files = extract_zip_to_nc(main_file, extract_dir)
    else:
        # 直接 NC
        nc_files = [main_file]

    log.info(f"  加载 {len(nc_files)} 日文件")
    datasets = [xr.open_dataset(f) for f in nc_files]
    if len(datasets) > 1:
        merged = xr.concat(datasets, dim='time')
    else:
        merged = datasets[0]
    merged['utci_C'] = merged['utci'] - 273.15
    n_time = merged.utci.shape[0]
    log.info(f"  时间步: {n_time} 小时")

    # 加载 LCZ
    lcz_path = PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif"
    lcz_utm = rxr.open_rasterio(lcz_path, masked=True).squeeze()
    lcz_wgs = lcz_utm.rio.reproject("EPSG:4326", resampling=Resampling.nearest)
    lcz_array = lcz_wgs.values
    lcz_lons = lcz_wgs.x.values
    lcz_lats = lcz_wgs.y.values

    # 简化: 直接用 ERA5 cell 值作为 100m 值（无 LCZ 偏差注入）
    # 因为不同季节我们没有 LCZ-specific anomaly 数据
    era5_lons = merged.lon.values
    era5_lats = merged.lat.values
    Y, X = lcz_array.shape

    # 100m -> ERA5 cell 映射
    cell_idx_lat = np.zeros(Y, dtype=int)
    cell_idx_lon = np.zeros(X, dtype=int)
    for i, lat in enumerate(lcz_lats):
        cell_idx_lat[i] = int(np.argmin(np.abs(era5_lats - lat)))
    for i, lon in enumerate(lcz_lons):
        cell_idx_lon[i] = int(np.argmin(np.abs(era5_lons - lon)))

    max_lat = merged.utci_C.shape[1] - 1
    max_lon = merged.utci_C.shape[2] - 1
    i_idx = np.clip(cell_idx_lat[:, None], 0, max_lat)
    j_idx = np.clip(cell_idx_lon[None, :], 0, max_lon)

    log.info(f"  向量化合成 ...")
    utci_at_grid = merged.utci_C.values[:, i_idx, j_idx]  # (T, Y, X)
    utci_100m = utci_at_grid.astype(np.float32)

    log.info(f"  UTCI 范围: {np.nanmin(utci_100m):.2f} – {np.nanmax(utci_100m):.2f} °C")

    # 计算汇总
    utci_mean = np.nanmean(utci_100m, axis=0)
    hdh = np.nansum(np.where(utci_100m > 26, utci_100m - 26, 0), axis=0)

    return {
        'utci_mean': utci_mean,
        'hdh': hdh,
        'lcz': lcz_array,
        'lons': lcz_lons,
        'lats': lcz_lats,
        'n_hours': n_time,
    }


def reproject_to_utm(field, lons, lats, template):
    """将 WGS84 数组重投影到 UTM 模板"""
    da = xr.DataArray(field, dims=('y', 'x'),
                      coords={'y': lats, 'x': lons}).rio.write_crs("EPSG:4326")
    return da.rio.reproject_match(template, resampling=Resampling.bilinear).values


def cluster_with_features(df, features, k_force=4):
    """每个 LCZ 类用指定特征 k-means"""
    subcat = np.full(len(df), np.nan)
    for lcz_id in sorted(df['lcz'].unique()):
        mask = (df['lcz'] == lcz_id).values
        if mask.sum() < 50:
            continue
        X = df.loc[mask, features].values
        X_std = StandardScaler().fit_transform(X)
        k = min(k_force, max(2, mask.sum() // 5))
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_std)
        subcat[mask] = lcz_id * 10 + labels
    return subcat


def analyze_season(month, season_label, base_K, umps_ds, pop_arr_full,
                    dist_coast_full, dist_mountain_full):
    """单季节分析"""
    log.info(f"\n=== {season_label} ({month}) ===")
    data = synthesize_utci_for_month(month, base_K)
    if data is None:
        return None

    # 重投影到 UTM
    template = xr.DataArray(
        np.zeros_like(umps_ds['lcz'].values, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': umps_ds.y.values, 'x': umps_ds.x.values}
    ).rio.write_crs("EPSG:32650")

    utci_utm = reproject_to_utm(data['utci_mean'], data['lons'], data['lats'], template)
    hdh_utm = reproject_to_utm(data['hdh'], data['lons'], data['lats'], template)

    h, w = pop_arr_full.shape
    utci_utm = utci_utm[:h, :w]
    hdh_utm = hdh_utm[:h, :w]
    lcz_arr = umps_ds['lcz'].values[:h, :w]

    valid = (~np.isnan(lcz_arr)) & (~np.isnan(pop_arr_full)) & (pop_arr_full > 0) \
            & (lcz_arr <= 10) & (~np.isnan(hdh_utm))

    df = pd.DataFrame({
        'lcz': lcz_arr[valid].astype(int),
        'pop': pop_arr_full[valid],
        'utci': utci_utm[valid],
        'hdh': hdh_utm[valid],
        'd_coast': dist_coast_full[valid],
        'd_mountain': dist_mountain_full[valid],
    })

    # 跑 4 个 scheme
    schemes = {
        'Coast only': ['d_coast'],
        'Mountain only': ['d_mountain'],
        'Coast+Mountain': ['d_coast', 'd_mountain'],
    }

    season_results = []
    for sch_name, feats in schemes.items():
        subcat = cluster_with_features(df, feats)
        df_t = df.copy()
        df_t['subcat'] = subcat
        df_t = df_t[~np.isnan(df_t['subcat'])]
        df_t['subcat'] = df_t['subcat'].astype(int)

        decomp_lcz = gini_decomposition(df_t, 'hdh', 'pop', 'lcz')
        decomp_sub = gini_decomposition(df_t, 'hdh', 'pop', 'subcat')
        within_lcz = decomp_lcz['within_share'] * 100
        within_sub = decomp_sub['within_share'] * 100
        reduction = within_lcz - within_sub

        season_results.append({
            'season': season_label,
            'month': month,
            'utci_mean': df['utci'].mean(),
            'hdh_mean': df['hdh'].mean(),
            'scheme': sch_name,
            'G_total': decomp_sub['G_total'],
            'G_within_lcz': within_lcz,
            'G_within_sub': within_sub,
            'reduction_pp': reduction,
        })
        log.info(f"  {sch_name:<18s}: reduction = {reduction:+.2f} pp "
                 f"(G_total = {decomp_sub['G_total']:.4f})")

    return season_results


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 7 (L2): 季节稳健性验证")
    log.info("=" * 65)

    # 加载共用数据
    log.info("\n[准备] 加载共用数据")
    umps_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc")
    pop_da = rxr.open_rasterio(
        PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True
    ).squeeze()
    h = min(pop_da.shape[0], umps_ds['lcz'].shape[0])
    w = min(pop_da.shape[1], umps_ds['lcz'].shape[1])
    pop_arr = pop_da.values[:h, :w]
    lcz_arr = umps_ds['lcz'].values[:h, :w]

    water_mask = (lcz_arr == 17)
    mountain_mask = np.isin(lcz_arr, [11, 12])
    dist_coast_full = distance_transform_edt(~water_mask).astype(np.float32) * 0.1
    dist_mountain_full = distance_transform_edt(~mountain_mask).astype(np.float32) * 0.1
    pop_arr_full = pop_arr[:h, :w]

    # 4 季分析
    seasons = [
        ('01', 'Jan (Winter)', 290.0),
        ('04', 'Apr (Spring)', 297.0),
        ('07', 'Jul (Summer)', 302.0),
        ('10', 'Oct (Autumn)', 298.0),
    ]

    all_results = []
    for month, label, base_K in seasons:
        results = analyze_season(month, label, base_K, umps_ds,
                                  pop_arr_full, dist_coast_full, dist_mountain_full)
        if results:
            all_results.extend(results)

    df_all = pd.DataFrame(all_results)
    df_all.to_csv(RESULTS_P7 / "seasonal_gini_comparison.csv", index=False)

    # === Fig 10 ===
    log.info("\n[Fig 10] 季节稳健性可视化")
    fig = plt.figure(figsize=(14, 7), dpi=120)
    gs = fig.add_gridspec(1, 3, wspace=0.35,
                           left=0.06, right=0.97, top=0.88, bottom=0.13)

    # Pivot data
    pivot = df_all.pivot(index='season', columns='scheme', values='reduction_pp')

    # (a) Gini reduction across 4 seasons
    ax_a = fig.add_subplot(gs[0, 0])
    pivot.plot(kind='bar', ax=ax_a,
                color=['#5e9bd1', '#8ab37e', '#c47e5e'],
                edgecolor='black')
    ax_a.axhline(5, color='red', linestyle='--', linewidth=1.5,
                  label='5 pp threshold')
    ax_a.set_xlabel('Season')
    ax_a.set_ylabel('Within-class Gini reduction (pp)')
    ax_a.set_title('(a) Gini reduction by season',
                    fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='upper left', fontsize=8)
    ax_a.set_xticklabels(ax_a.get_xticklabels(), rotation=15)
    ax_a.grid(axis='y', alpha=0.3)

    # (b) UTCI mean by season
    ax_b = fig.add_subplot(gs[0, 1])
    season_utci = df_all.groupby('season')['utci_mean'].first()
    bars = ax_b.bar(season_utci.index, season_utci.values,
                     color=['#5e9bd1', '#8ab37e', '#c47e5e', '#7a5d8d'],
                     edgecolor='black')
    for bar, val in zip(bars, season_utci.values):
        ax_b.text(bar.get_x() + bar.get_width()/2, val + 0.3,
                   f'{val:.1f}°C',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_b.set_ylabel('Mean UTCI (°C)')
    ax_b.set_title('(b) Seasonal UTCI baseline',
                    fontsize=11, fontweight='bold', loc='left')
    ax_b.set_xticklabels(season_utci.index, rotation=15)
    ax_b.grid(axis='y', alpha=0.3)

    # (c) Coast vs Mountain seasonal stability
    ax_c = fig.add_subplot(gs[0, 2])
    coast_data = df_all[df_all['scheme']=='Coast only'].set_index('season')['reduction_pp']
    mtn_data = df_all[df_all['scheme']=='Mountain only'].set_index('season')['reduction_pp']
    x = np.arange(len(coast_data))
    ax_c.plot(x, coast_data.values, '-o', color='#0571b0',
               linewidth=2, markersize=10, label='Coast only')
    ax_c.plot(x, mtn_data.values, '-s', color='#a6611a',
               linewidth=2, markersize=10, label='Mountain only')
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(coast_data.index, rotation=15, fontsize=9)
    ax_c.axhline(5, color='red', linestyle='--', linewidth=1.5,
                  alpha=0.6, label='5 pp')
    ax_c.set_ylabel('Reduction (pp)')
    ax_c.set_title('(c) Mechanism stability across seasons',
                    fontsize=11, fontweight='bold', loc='left')
    ax_c.legend(loc='best', fontsize=9)
    ax_c.grid(alpha=0.3)

    plt.suptitle('Phase 7 (L2): Seasonal Robustness of Geographic Mechanism',
                  fontsize=12, fontweight='bold', y=0.97)

    fig_path = FIGURES_DIR / "fig11_seasonal_robustness.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    log.info(f"\n  图表保存: {fig_path}")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px, {fig_path.stat().st_size/1e3:.1f} KB")

    log.info("\n🎉 Phase 7 (L2) 完成！")
    log.info("\n季节对比总览:")
    log.info(pivot.to_string())


if __name__ == "__main__":
    main()
