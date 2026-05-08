"""
Phase 8: 跨 GBA 城市迁移测试

测试: Coast/Mountain Gini 减少在 4 城是否一致超过 5 pp 阈值
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
from src.utils.cities import CITIES
from src.analysis.gini import gini_decomposition

log = get_logger("multicity")
RESULTS_MC = RESULTS_DIR / "multicity"
RESULTS_MC.mkdir(parents=True, exist_ok=True)

MONTHS = ['01', '04', '07', '10']
SEASON_LABELS = {'01': 'Winter', '04': 'Spring', '07': 'Summer', '10': 'Autumn'}


def load_era5_for_city_month(city, month):
    """加载 ERA5 数据（处理 ZIP）"""
    era5_dir = RAW_DATA_DIR / "era5"
    main_file = era5_dir / f"era5_heat_{city}_2020_{month}.nc"

    if not main_file.exists():
        return None

    with open(main_file, 'rb') as f:
        magic = f.read(4)

    if magic == b'PK\x03\x04':
        extract_dir = era5_dir / f"extracted_{city}_{month}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        existing = list(extract_dir.glob("ECMWF_utci_*.nc"))
        if not existing:
            with zipfile.ZipFile(main_file, 'r') as zf:
                zf.extractall(extract_dir)
        nc_files = sorted(extract_dir.glob("ECMWF_utci_*.nc"))
    else:
        nc_files = [main_file]

    if not nc_files:
        return None

    datasets = [xr.open_dataset(f) for f in nc_files]
    if len(datasets) > 1:
        merged = xr.concat(datasets, dim='time')
    else:
        merged = datasets[0]
    merged['utci_C'] = merged['utci'] - 273.15
    return merged


def synthesize_utci_for_city(city, month):
    """合成某城市某月 100m UTCI（无 LCZ 偏差，简化）"""
    era5_ds = load_era5_for_city_month(city, month)
    if era5_ds is None:
        return None

    # 加载 LCZ
    lcz_utm_path = PROCESSED_DATA_DIR / f"{city}_lcz_100m_utm.tif"
    lcz_utm = rxr.open_rasterio(lcz_utm_path, masked=True).squeeze()
    lcz_wgs = lcz_utm.rio.reproject("EPSG:4326", resampling=Resampling.nearest)
    lcz_array = lcz_wgs.values
    lcz_lons = lcz_wgs.x.values
    lcz_lats = lcz_wgs.y.values

    Y, X = lcz_array.shape
    era5_lons = era5_ds.lon.values
    era5_lats = era5_ds.lat.values

    cell_idx_lat = np.zeros(Y, dtype=int)
    cell_idx_lon = np.zeros(X, dtype=int)
    for i, lat in enumerate(lcz_lats):
        cell_idx_lat[i] = int(np.argmin(np.abs(era5_lats - lat)))
    for i, lon in enumerate(lcz_lons):
        cell_idx_lon[i] = int(np.argmin(np.abs(era5_lons - lon)))

    max_lat = era5_ds.utci_C.shape[1] - 1
    max_lon = era5_ds.utci_C.shape[2] - 1
    i_idx = np.clip(cell_idx_lat[:, None], 0, max_lat)
    j_idx = np.clip(cell_idx_lon[None, :], 0, max_lon)

    utci_at_grid = era5_ds.utci_C.values[:, i_idx, j_idx].astype(np.float32)

    utci_mean = np.nanmean(utci_at_grid, axis=0)
    hdh = np.nansum(np.where(utci_at_grid > 26, utci_at_grid - 26, 0), axis=0)

    return {
        'utci_mean': utci_mean,
        'hdh': hdh,
        'lcz_wgs': lcz_array,
        'lcz_wgs_lons': lcz_lons,
        'lcz_wgs_lats': lcz_lats,
        'lcz_utm': lcz_utm,
    }


def run_city_analysis(city):
    """对某城市跑 4 季节分析"""
    log.info(f"\n{'='*60}")
    log.info(f"分析城市: {CITIES[city]['name']}")
    log.info(f"{'='*60}")

    # 加载城市 LCZ + Pop UTM
    lcz_utm_path = PROCESSED_DATA_DIR / f"{city}_lcz_100m_utm.tif"
    pop_utm_path = PROCESSED_DATA_DIR / f"{city}_pop_100m_utm.tif"

    lcz_utm = rxr.open_rasterio(lcz_utm_path, masked=True).squeeze()
    pop_utm = rxr.open_rasterio(pop_utm_path, masked=True).squeeze()

    # 形状对齐
    h = min(lcz_utm.shape[0], pop_utm.shape[0])
    w = min(lcz_utm.shape[1], pop_utm.shape[1])
    lcz_arr = lcz_utm.values[:h, :w]
    pop_arr = pop_utm.values[:h, :w]

    # 计算距离特征
    water_mask = (lcz_arr == 17)
    mountain_mask = np.isin(lcz_arr, [11, 12])

    if water_mask.sum() < 100:
        log.warning(f"  水体很少 ({water_mask.sum()} cells)，coast distance 可能无意义")
    if mountain_mask.sum() < 100:
        log.warning(f"  山区很少 ({mountain_mask.sum()} cells)，mountain distance 可能无意义")

    dist_coast = distance_transform_edt(~water_mask).astype(np.float32) * 0.1
    dist_mountain = distance_transform_edt(~mountain_mask).astype(np.float32) * 0.1

    # 城市模板（UTM）
    template = xr.DataArray(
        np.zeros_like(lcz_arr, dtype=np.float32),
        dims=('y', 'x'),
        coords={'y': lcz_utm.y.values[:h], 'x': lcz_utm.x.values[:w]}
    ).rio.write_crs("EPSG:32650")

    city_results = []
    for month in MONTHS:
        season = SEASON_LABELS[month]
        log.info(f"\n  --- {season} ({month}) ---")

        data = synthesize_utci_for_city(city, month)
        if data is None:
            log.warning(f"    数据缺失，跳过")
            continue

        # UTCI 重投影到 UTM
        utci_da = xr.DataArray(
            data['utci_mean'], dims=('y', 'x'),
            coords={'y': data['lcz_wgs_lats'], 'x': data['lcz_wgs_lons']}
        ).rio.write_crs("EPSG:4326")
        hdh_da = xr.DataArray(
            data['hdh'], dims=('y', 'x'),
            coords={'y': data['lcz_wgs_lats'], 'x': data['lcz_wgs_lons']}
        ).rio.write_crs("EPSG:4326")

        utci_utm = utci_da.rio.reproject_match(
            template, resampling=Resampling.bilinear).values
        hdh_utm = hdh_da.rio.reproject_match(
            template, resampling=Resampling.bilinear).values

        valid = (~np.isnan(lcz_arr)) & (~np.isnan(pop_arr)) & (pop_arr > 0) \
                & (lcz_arr <= 10) & (~np.isnan(hdh_utm))

        if valid.sum() < 1000:
            log.warning(f"    valid cells too few: {valid.sum()}")
            continue

        df = pd.DataFrame({
            'lcz': lcz_arr[valid].astype(int),
            'pop': pop_arr[valid],
            'utci': utci_utm[valid],
            'hdh': hdh_utm[valid],
            'd_coast': dist_coast[valid],
            'd_mountain': dist_mountain[valid],
        })

        # 跑 3 schemes
        schemes = {
            'Coast only': ['d_coast'],
            'Mountain only': ['d_mountain'],
            'Coast+Mountain': ['d_coast', 'd_mountain'],
        }

        for sch_name, feats in schemes.items():
            # k-means per LCZ class
            subcat = np.full(len(df), np.nan)
            for lcz_id in sorted(df['lcz'].unique()):
                mask = (df['lcz'] == lcz_id).values
                if mask.sum() < 50:
                    continue
                X = df.loc[mask, feats].values
                X_std = StandardScaler().fit_transform(X)
                k = min(4, mask.sum() // 5)
                if k < 2:
                    continue
                km = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = km.fit_predict(X_std)
                subcat[mask] = lcz_id * 10 + labels

            df_t = df.copy()
            df_t['subcat'] = subcat
            df_t = df_t[~np.isnan(df_t['subcat'])]
            df_t['subcat'] = df_t['subcat'].astype(int)

            decomp_lcz = gini_decomposition(df_t, 'hdh', 'pop', 'lcz')
            decomp_sub = gini_decomposition(df_t, 'hdh', 'pop', 'subcat')
            within_lcz = decomp_lcz['within_share'] * 100
            within_sub = decomp_sub['within_share'] * 100
            reduction = within_lcz - within_sub

            log.info(f"    {sch_name:<18s}: {reduction:+.2f} pp "
                     f"(within {within_lcz:.1f}% -> {within_sub:.1f}%)")

            city_results.append({
                'city': city,
                'city_name': CITIES[city]['name'],
                'month': month,
                'season': season,
                'utci_mean': df['utci'].mean(),
                'scheme': sch_name,
                'reduction_pp': reduction,
                'G_total': decomp_sub['G_total'],
                'G_within_lcz': within_lcz,
                'G_within_sub': within_sub,
                'n_cells': len(df),
            })

    return city_results


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 8: GBA 跨城市迁移测试")
    log.info("=" * 65)

    # 用 Shenzhen 已有结果作为参考
    cities = ['shenzhen', 'guangzhou', 'dongguan']

    all_results = []
    for city in cities:
        # Shenzhen 用已有 Phase 7 L2 结果
        if city == 'shenzhen':
            sz_csv = RESULTS_DIR / "phase7" / "seasonal_gini_comparison.csv"
            if sz_csv.exists():
                sz_df = pd.read_csv(sz_csv)
                # 转换格式
                # 把 SZ 月份标签统一为 'Winter/Spring/Summer/Autumn'
                month_to_season = {'Jan': 'Winter', 'Apr': 'Spring',
                                    'Jul': 'Summer', 'Oct': 'Autumn'}
                month_map = {'Jan': '01', 'Apr': '04', 'Jul': '07', 'Oct': '10'}
                for _, r in sz_df.iterrows():
                    season_short = r['season'].split(' ')[0]
                    season_full = month_to_season.get(season_short, season_short)
                    all_results.append({
                        'city': 'shenzhen',
                        'city_name': 'Shenzhen',
                        'month': month_map.get(season_short, '01'),
                        'season': season_full,
                        'utci_mean': r['utci_mean'],
                        'scheme': r['scheme'],
                        'reduction_pp': r['reduction_pp'],
                        'G_total': r['G_total'],
                        'G_within_lcz': r['G_within_lcz'],
                        'G_within_sub': r['G_within_sub'],
                        'n_cells': 144505,  # 已知
                    })
                log.info(f"\n  ✓ Shenzhen 用 Phase 7 L2 已有结果（{len(sz_df)} 行）")
                continue

        # 检查 ERA5 数据是否就绪
        ready = all(
            (RAW_DATA_DIR / "era5" / f"era5_heat_{city}_2020_{m}.nc").exists()
            for m in MONTHS
        )
        if not ready:
            log.warning(f"\n  {city}: ERA5 数据不全，跳过")
            continue

        results = run_city_analysis(city)
        all_results.extend(results)

    df_all = pd.DataFrame(all_results)
    df_all.to_csv(RESULTS_MC / "multicity_gini_comparison.csv", index=False)

    log.info("\n" + "=" * 65)
    log.info("跨城市汇总")
    log.info("=" * 65)
    pivot = df_all.pivot_table(
        index=['city_name', 'season'],
        columns='scheme',
        values='reduction_pp'
    )
    log.info("\n" + pivot.to_string())

    # === Fig 11 ===
    log.info("\n[Fig 11] 跨城市可视化")
    fig = plt.figure(figsize=(15, 8), dpi=120)
    gs = fig.add_gridspec(2, 4, wspace=0.4, hspace=0.45,
                           left=0.06, right=0.97, top=0.91, bottom=0.10)

    # (a) Coast+Mountain by city x season
    ax_a = fig.add_subplot(gs[0, 0:2])
    cm_data = df_all[df_all['scheme']=='Coast+Mountain']
    pivot_cm = cm_data.pivot(index='season', columns='city_name', values='reduction_pp')
    season_order = ['Winter', 'Spring', 'Summer', 'Autumn']
    pivot_cm = pivot_cm.reindex(season_order)
    pivot_cm.plot(kind='bar', ax=ax_a,
                   color=['#5e9bd1', '#8ab37e', '#c47e5e'],
                   edgecolor='black')
    ax_a.axhline(5, color='red', linestyle='--', linewidth=1.5)
    ax_a.set_xticklabels(season_order, rotation=0)
    ax_a.set_ylabel('Coast+Mountain Gini reduction (pp)')
    ax_a.set_title('(a) Coast+Mountain reduction across cities & seasons',
                    fontsize=11, fontweight='bold', loc='left')
    ax_a.legend(loc='upper left', fontsize=8, ncol=2)
    ax_a.grid(axis='y', alpha=0.3)

    # (b) Coast vs Mountain alone (mean across seasons)
    ax_b = fig.add_subplot(gs[0, 2:4])
    coast_means = df_all[df_all['scheme']=='Coast only'].groupby('city_name')['reduction_pp'].mean()
    mtn_means = df_all[df_all['scheme']=='Mountain only'].groupby('city_name')['reduction_pp'].mean()
    cities_order = ['Shenzhen', 'Guangzhou', 'Dongguan']
    coast_v = [coast_means.get(c, 0) for c in cities_order]
    mtn_v = [mtn_means.get(c, 0) for c in cities_order]
    x = np.arange(len(cities_order))
    width = 0.35
    ax_b.bar(x - width/2, coast_v, width, label='Coast only',
              color='#0571b0', edgecolor='black')
    ax_b.bar(x + width/2, mtn_v, width, label='Mountain only',
              color='#a6611a', edgecolor='black')
    for i in range(len(cities_order)):
        ax_b.text(i - width/2, coast_v[i] + 0.1, f'{coast_v[i]:.1f}',
                   ha='center', va='bottom', fontsize=8)
        ax_b.text(i + width/2, mtn_v[i] + 0.1, f'{mtn_v[i]:.1f}',
                   ha='center', va='bottom', fontsize=8)
    ax_b.axhline(5, color='red', linestyle='--', linewidth=1.5)
    ax_b.set_xticks(x)
    ax_b.set_xticklabels(cities_order, rotation=15)
    ax_b.set_ylabel('Mean reduction across 4 seasons (pp)')
    ax_b.set_title('(b) Single-feature mechanism strength by city',
                    fontsize=11, fontweight='bold', loc='left')
    ax_b.legend(loc='upper right', fontsize=9)
    ax_b.grid(axis='y', alpha=0.3)

    # (c) UTCI seasonal cycle by city
    ax_c = fig.add_subplot(gs[1, 0:2])
    utci_pivot = df_all.drop_duplicates(['city_name', 'season']).pivot(
        index='season', columns='city_name', values='utci_mean'
    ).reindex(season_order)
    utci_pivot.plot(ax=ax_c, marker='o', linewidth=2, markersize=8)
    ax_c.set_ylabel('Mean UTCI (°C)')
    ax_c.set_title('(c) Seasonal UTCI cycle (4 cities)',
                    fontsize=11, fontweight='bold', loc='left')
    ax_c.legend(loc='best', fontsize=9, ncol=2)
    ax_c.grid(alpha=0.3)

    # (d) % seasons passing 5 pp threshold per city
    ax_d = fig.add_subplot(gs[1, 2:4])
    cm_data_only = df_all[df_all['scheme']=='Coast+Mountain']
    pass_rate = (cm_data_only.groupby('city_name')
                  .apply(lambda x: (x['reduction_pp'] > 5).mean() * 100,
                         include_groups=False))
    pass_rate = pass_rate.reindex(cities_order)
    bars = ax_d.bar(cities_order, pass_rate.values,
                     color=['#5e9bd1', '#8ab37e', '#c47e5e'],
                     edgecolor='black')
    for bar, val in zip(bars, pass_rate.values):
        ax_d.text(bar.get_x() + bar.get_width()/2, val + 2,
                   f'{val:.0f}%', ha='center', va='bottom',
                   fontsize=11, fontweight='bold')
    ax_d.set_ylim(0, 110)
    ax_d.set_ylabel('% seasons passing 5 pp threshold')
    ax_d.set_title('(d) Cross-city robustness',
                    fontsize=11, fontweight='bold', loc='left')
    ax_d.set_xticklabels(cities_order, rotation=15)
    ax_d.grid(axis='y', alpha=0.3)

    plt.suptitle('Phase 8: GBA Cross-City Validation of Geographic Mechanism',
                  fontsize=12, fontweight='bold', y=0.97)

    fig_path = FIGURES_DIR / "fig12_multicity_validation.png"
    plt.savefig(fig_path, dpi=120, bbox_inches='tight', facecolor='white')
    plt.close()

    log.info(f"\n  Fig 12 保存: {fig_path}")
    from PIL import Image
    img = Image.open(fig_path)
    log.info(f"  尺寸: {img.size[0]} × {img.size[1]} px, {fig_path.stat().st_size/1e3:.1f} KB")

    log.info("\n🎉 Phase 8 (跨城市) 完成！")


if __name__ == "__main__":
    main()
