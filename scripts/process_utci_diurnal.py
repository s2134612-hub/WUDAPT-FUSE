"""
重新合成 100m UTCI，按昼夜分别保存

时区: 深圳 = UTC+8
日间: SHT 08:00-20:00 = UTC 00:00-12:00 (12 小时/天)
夜间: SHT 20:00-08:00 = UTC 12:00-24:00 (12 小时/天)

输出:
  data/processed/shenzhen_utci_100m_jul_day_summary.nc
  data/processed/shenzhen_utci_100m_jul_night_summary.nc
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import xarray as xr
import rioxarray as rxr
from rasterio.enums import Resampling

from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.thermal_burden import LCZ_AT_JUL_K

log = get_logger("utci_diurnal")


def load_and_merge_era5(era5_dir):
    """加载并合并所有日 ERA5 文件"""
    extracted = era5_dir / "extracted"
    nc_files = sorted(extracted.glob("ECMWF_utci_*.nc"))
    log.info(f"  找到 {len(nc_files)} 个日文件")

    datasets = []
    for f in nc_files:
        ds = xr.open_dataset(f)
        datasets.append(ds)

    merged = xr.concat(datasets, dim='time')
    merged['utci_C'] = merged['utci'] - 273.15
    return merged


def synthesize_100m_utci(era5_utci_C, lcz_array, era5_lons, era5_lats,
                          lcz_lons, lcz_lats, cell_lcz_means):
    """向量化合成 100m UTCI（与 process_utci_to_grid.py 相同）"""
    n_time = era5_utci_C.shape[0]
    Y, X = lcz_array.shape

    # LCZ -> AT lookup
    lcz_at = np.full((Y, X), np.nan, dtype=np.float32)
    for lcz_id, at_K in LCZ_AT_JUL_K.items():
        lcz_at[lcz_array == lcz_id] = at_K

    # 100m -> ERA5 cell 映射
    cell_idx_lat = np.full(Y, -1, dtype=int)
    cell_idx_lon = np.full(X, -1, dtype=int)
    for i, lat in enumerate(lcz_lats):
        cell_idx_lat[i] = int(np.argmin(np.abs(era5_lats - lat)))
    for i, lon in enumerate(lcz_lons):
        cell_idx_lon[i] = int(np.argmin(np.abs(era5_lons - lon)))

    # ERA5 cell mean AT 网格
    cell_mean_at_grid = np.full((Y, X), np.nan, dtype=np.float32)
    for i in range(Y):
        for j in range(X):
            key = (cell_idx_lat[i], cell_idx_lon[j])
            if key in cell_lcz_means:
                cell_mean_at_grid[i, j] = cell_lcz_means[key]

    # 偏差
    delta_at = lcz_at - cell_mean_at_grid

    # 边界保护
    max_lat = era5_utci_C.shape[1] - 1
    max_lon = era5_utci_C.shape[2] - 1
    i_idx = np.clip(cell_idx_lat[:, None], 0, max_lat)
    j_idx = np.clip(cell_idx_lon[None, :], 0, max_lon)

    # 向量化合成
    log.info(f"  合成 {n_time} 小时 UTCI...")
    utci_at_grid = era5_utci_C.values[:, i_idx, j_idx]
    utci_100m = utci_at_grid + delta_at[None, :, :]
    return utci_100m.astype(np.float32)


def compute_summary(utci_subset, label):
    """计算 UTCI 子集的汇总指标"""
    n_hr = utci_subset.shape[0]
    log.info(f"  计算 {label} 汇总（{n_hr} 小时）...")
    return {
        'utci_mean': np.nanmean(utci_subset, axis=0),
        'utci_max':  np.nanmax(utci_subset, axis=0),
        'utci_p95':  np.nanpercentile(utci_subset, 95, axis=0),
        'tsd_strong':np.nansum(utci_subset > 32, axis=0).astype(np.float32),
        'hdh':       np.nansum(np.where(utci_subset > 26, utci_subset - 26, 0), axis=0),
        'n_hours':   n_hr,
    }


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("Phase 7 (L1): UTCI 昼夜分解合成")
    log.info("=" * 65)

    # === 1. 加载 ERA5 ===
    era5_dir = RAW_DATA_DIR / "era5"
    era5_ds = load_and_merge_era5(era5_dir)

    log.info(f"  时间范围: {era5_ds.time.min().values} 至 {era5_ds.time.max().values}")

    # === 2. 加载 LCZ ===
    lcz_path = PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif"
    lcz_utm = rxr.open_rasterio(lcz_path, masked=True).squeeze()
    lcz_wgs = lcz_utm.rio.reproject("EPSG:4326", resampling=Resampling.nearest)
    lcz_array = lcz_wgs.values
    lcz_lons = lcz_wgs.x.values
    lcz_lats = lcz_wgs.y.values

    # === 3. 计算 ERA5 cell 内部 LCZ 均值 ===
    log.info("\n[1] 计算 ERA5 cell 内部 LCZ 热负担均值")
    era5_lons = era5_ds.lon.values
    era5_lats = era5_ds.lat.values

    cell_means = {}
    for i_lat, era5_lat in enumerate(era5_lats):
        for i_lon, era5_lon in enumerate(era5_lons):
            lat_min = era5_lat - 0.125
            lat_max = era5_lat + 0.125
            lon_min = era5_lon - 0.125
            lon_max = era5_lon + 0.125

            mask = (
                (lcz_lats[:, None] >= lat_min) & (lcz_lats[:, None] < lat_max) &
                (lcz_lons[None, :] >= lon_min) & (lcz_lons[None, :] < lon_max)
            )
            cell_lcz = lcz_array[mask]
            cell_lcz = cell_lcz[~np.isnan(cell_lcz)]
            if len(cell_lcz) > 0:
                cell_at = np.array([LCZ_AT_JUL_K.get(int(l), np.nan) for l in cell_lcz])
                cell_at = cell_at[~np.isnan(cell_at)]
                if len(cell_at) > 0:
                    cell_means[(i_lat, i_lon)] = float(cell_at.mean())

    # === 4. 合成 100m UTCI（全部 744 小时）===
    log.info("\n[2] 合成 100m UTCI 全月 (744 小时)")
    utci_100m = synthesize_100m_utci(
        era5_ds['utci_C'], lcz_array,
        era5_lons, era5_lats,
        lcz_lons, lcz_lats, cell_means
    )
    log.info(f"  形状: {utci_100m.shape}")
    log.info(f"  范围: {np.nanmin(utci_100m):.2f} – {np.nanmax(utci_100m):.2f} °C")

    # === 5. 按 UTC 小时切分昼夜 ===
    # 深圳 SHT = UTC+8
    # 日间 (SHT 08-20) = UTC 00-12 (含 0,1,...,11)
    # 夜间 (SHT 20-08) = UTC 12-24 (含 12,13,...,23)
    log.info("\n[3] 按 UTC 切分昼夜")

    times = era5_ds.time.values
    utc_hours = np.array([t.astype('datetime64[h]').astype(int) % 24
                           for t in times])
    log.info(f"  唯一 UTC 小时: {np.unique(utc_hours)}")

    day_mask = (utc_hours >= 0) & (utc_hours < 12)
    night_mask = ~day_mask
    log.info(f"  日间小时数 (SHT 08-20): {day_mask.sum()}")
    log.info(f"  夜间小时数 (SHT 20-08): {night_mask.sum()}")

    utci_day = utci_100m[day_mask]
    utci_night = utci_100m[night_mask]

    # === 6. 计算 day / night 汇总 ===
    log.info("\n[4] 计算昼夜汇总指标")
    summary_day = compute_summary(utci_day, "DAY")
    summary_night = compute_summary(utci_night, "NIGHT")

    log.info(f"\n  DAY:   mean={np.nanmean(summary_day['utci_mean']):.2f} °C, "
             f"max={np.nanmax(summary_day['utci_max']):.2f} °C, "
             f"hdh_mean={np.nanmean(summary_day['hdh']):.0f}")
    log.info(f"  NIGHT: mean={np.nanmean(summary_night['utci_mean']):.2f} °C, "
             f"max={np.nanmax(summary_night['utci_max']):.2f} °C, "
             f"hdh_mean={np.nanmean(summary_night['hdh']):.0f}")

    # === 7. 保存 ===
    log.info("\n[5] 保存 NetCDF")
    for label, summary in [('day', summary_day), ('night', summary_night)]:
        ds_out = xr.Dataset(
            {
                'utci_mean':   (('y', 'x'), summary['utci_mean']),
                'utci_max':    (('y', 'x'), summary['utci_max']),
                'utci_p95':    (('y', 'x'), summary['utci_p95']),
                'tsd_strong':  (('y', 'x'), summary['tsd_strong']),
                'hdh':         (('y', 'x'), summary['hdh']),
                'lcz':         (('y', 'x'), lcz_array.astype(np.float32)),
            },
            coords={
                'lat': ('y', lcz_lats),
                'lon': ('x', lcz_lons),
            },
            attrs={'period': label, 'n_hours': summary['n_hours']}
        )
        out_path = PROCESSED_DATA_DIR / f"shenzhen_utci_100m_jul_{label}_summary.nc"
        ds_out.to_netcdf(out_path)
        log.info(f"  {out_path.name}: {out_path.stat().st_size/1e6:.1f} MB")

    log.info("\n🎉 昼夜分解合成完成")


if __name__ == "__main__":
    main()
