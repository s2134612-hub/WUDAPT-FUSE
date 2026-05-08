"""
将 ERA5-HEAT 25km UTCI 与 100m LCZ 网格融合，生成增强版 100m UTCI 数据集。

融合策略 (Phase 2):
  UTCI_100m(i, t) = UTCI_25km(parent_cell, t) + ΔAT_LCZ(i) - ΔAT_mean_in_parent_cell

其中:
  - UTCI_25km(parent_cell, t): 该 100m 栅格所在 25km ERA5 cell 的小时 UTCI
  - ΔAT_LCZ(i): 该 100m 栅格 LCZ 类型的热负担偏差（相对城市均值）

输出:
  data/processed/shenzhen_utci_100m_2020_07_15_21.nc  (5维: time, y, x)
  data/processed/shenzhen_utci_100m_jul_summary.nc   (汇总: mean/max/TSD)
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
from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.thermal_burden import LCZ_AT_JUL_K

log = get_logger("process_utci")


def load_and_merge_era5(era5_dir):
    """合并 7 天 ERA5-HEAT 文件为一个时序数据集"""
    log.info("[1] 加载 ERA5-HEAT 7 天数据")
    extracted = era5_dir / "extracted"
    nc_files = sorted(extracted.glob("ECMWF_utci_*.nc"))
    log.info(f"    找到 {len(nc_files)} 个文件")

    datasets = []
    for f in nc_files:
        ds = xr.open_dataset(f)
        datasets.append(ds)

    merged = xr.concat(datasets, dim='time')
    log.info(f"    合并形状: utci={merged.utci.shape}")
    log.info(f"    时间范围: {merged.time.min().values} - {merged.time.max().values}")
    log.info(f"    经度: {merged.lon.values}")
    log.info(f"    纬度: {merged.lat.values}")

    # UTCI 转换 K → °C
    merged['utci_C'] = merged['utci'] - 273.15

    return merged


def load_lcz_grid():
    """加载 100m LCZ 网格（已在 UTM 投影下）"""
    log.info("[2] 加载 LCZ 100m 网格 (UTM)")
    lcz_path = PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif"
    lcz = rxr.open_rasterio(lcz_path, masked=True).squeeze()
    log.info(f"    形状: {lcz.shape}")
    log.info(f"    CRS: {lcz.rio.crs}")
    return lcz


def reproject_lcz_to_lonlat(lcz_utm):
    """LCZ 从 UTM 转回 WGS84 (lon/lat) 以匹配 ERA5"""
    log.info("[3] LCZ 重投影 UTM -> WGS84")
    from rasterio.enums import Resampling
    lcz_wgs = lcz_utm.rio.reproject("EPSG:4326", resampling=Resampling.nearest)
    log.info(f"    新形状: {lcz_wgs.shape}")
    return lcz_wgs


def compute_lcz_thermal_anomaly(lcz_array, era5_lons, era5_lats, lcz_lons, lcz_lats):
    """
    对每个 ERA5 25km cell，计算它内部 LCZ 的城市热负担均值。

    Returns
    -------
    dict
        {(lat_idx, lon_idx): mean_AT_K_for_this_cell}
    """
    log.info("[4] 计算每个 ERA5 cell 内部的 LCZ 热负担均值")

    cell_means = {}
    cell_lcz_dist = {}

    # ERA5 cell 边界 (25km × 25km, lon: 0.25°, lat: 0.25°)
    for i_lat, era5_lat in enumerate(era5_lats):
        for i_lon, era5_lon in enumerate(era5_lons):
            # 找到这个 cell 内的 100m 栅格
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
                # 转 LCZ -> AT, 求均值
                cell_at = np.array([LCZ_AT_JUL_K.get(int(l), np.nan) for l in cell_lcz])
                cell_at = cell_at[~np.isnan(cell_at)]
                if len(cell_at) > 0:
                    cell_means[(i_lat, i_lon)] = float(cell_at.mean())
                    # LCZ 分布
                    unique, counts = np.unique(cell_lcz.astype(int), return_counts=True)
                    cell_lcz_dist[(i_lat, i_lon)] = dict(zip(unique.tolist(), counts.tolist()))

    log.info(f"    覆盖 {len(cell_means)} / {len(era5_lats)*len(era5_lons)} 个 ERA5 cells")
    return cell_means, cell_lcz_dist


def synthesize_100m_utci(era5_utci_C, lcz_array, era5_lons, era5_lats,
                         lcz_lons, lcz_lats, cell_lcz_means, time_idx=None):
    """
    生成 100m × time UTCI 数据（融合 ERA5 + LCZ 热负担）

    UTCI_100m(i, t) = UTCI_25km(parent, t) + (AT_LCZ(i) - AT_LCZ_mean(parent))

    时间维度: 如果 time_idx=None 则取所有时间，否则只算特定小时

    Returns
    -------
    utci_100m : np.ndarray  shape (T, Y, X) 或 (Y, X)
    """
    log.info("[5] 合成 100m UTCI")

    n_time = era5_utci_C.shape[0]
    Y, X = lcz_array.shape

    # LCZ -> AT lookup vectorized
    lcz_at = np.full((Y, X), np.nan, dtype=np.float32)
    for lcz_id, at_K in LCZ_AT_JUL_K.items():
        lcz_at[lcz_array == lcz_id] = at_K

    # 计算每个 100m 栅格属于哪个 ERA5 cell
    log.info("    构建 100m -> ERA5 cell 映射")
    cell_idx_lat = np.full(Y, -1, dtype=int)
    cell_idx_lon = np.full(X, -1, dtype=int)

    for i, lat in enumerate(lcz_lats):
        # 找最近的 ERA5 lat
        diffs = np.abs(era5_lats - lat)
        cell_idx_lat[i] = int(np.argmin(diffs))

    for i, lon in enumerate(lcz_lons):
        diffs = np.abs(era5_lons - lon)
        cell_idx_lon[i] = int(np.argmin(diffs))

    # 构建 ERA5 cell mean AT 栅格（与 100m LCZ 同形）
    cell_mean_at_grid = np.full((Y, X), np.nan, dtype=np.float32)
    for i in range(Y):
        for j in range(X):
            key = (cell_idx_lat[i], cell_idx_lon[j])
            if key in cell_lcz_means:
                cell_mean_at_grid[i, j] = cell_lcz_means[key]

    # LCZ 偏差 = AT_lcz - AT_cell_mean
    delta_at = lcz_at - cell_mean_at_grid

    log.info(f"    LCZ 偏差范围: {np.nanmin(delta_at):.2f} 到 {np.nanmax(delta_at):.2f} K")

    # 向量化合成 (从 nested loop 1 亿次 -> 一次 broadcast)
    # 索引广播
    i_idx = cell_idx_lat[:, None]  # (Y, 1)
    j_idx = cell_idx_lon[None, :]  # (1, X)

    # 边界保护
    max_lat = era5_utci_C.shape[1] - 1
    max_lon = era5_utci_C.shape[2] - 1
    i_idx = np.clip(i_idx, 0, max_lat)
    j_idx = np.clip(j_idx, 0, max_lon)

    if time_idx is None:
        log.info(f"    向量化合成 {n_time} 小时 UTCI 100m...")
        # era5_utci_C.values shape: (T, lat, lon)
        # 通过花式索引一次完成: shape (T, Y, X)
        utci_at_grid = era5_utci_C.values[:, i_idx, j_idx]  # (T, Y, X)
        utci_100m = utci_at_grid + delta_at[None, :, :]
        utci_100m = utci_100m.astype(np.float32)
        log.info(f"    向量化完成: {utci_100m.shape}")
    else:
        utci_25km_t = era5_utci_C.values[time_idx]  # (lat, lon)
        utci_100m = utci_25km_t[i_idx, j_idx] + delta_at
        utci_100m = utci_100m.astype(np.float32)

    return utci_100m, delta_at


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("ERA5-HEAT × LCZ 100m 融合（Phase 2）")
    log.info("=" * 65)

    era5_dir = RAW_DATA_DIR / "era5"

    # 1) 加载并合并 ERA5
    era5_ds = load_and_merge_era5(era5_dir)

    # 保存合并后的 ERA5
    merged_path = era5_dir / "era5_heat_shenzhen_2020_07_15_21_merged.nc"
    era5_ds.to_netcdf(merged_path)
    log.info(f"  合并文件保存: {merged_path}")

    # 2) 加载 LCZ (UTM)
    lcz_utm = load_lcz_grid()

    # 3) 重投影到 WGS84 以匹配 ERA5
    lcz_wgs = reproject_lcz_to_lonlat(lcz_utm)
    lcz_array = lcz_wgs.values
    lcz_lons = lcz_wgs.x.values
    lcz_lats = lcz_wgs.y.values
    log.info(f"    LCZ WGS84: lon {lcz_lons.min():.4f}-{lcz_lons.max():.4f}, "
             f"lat {lcz_lats.min():.4f}-{lcz_lats.max():.4f}")

    # 4) 计算 ERA5 cell 内部 LCZ 热负担均值
    cell_means, cell_lcz_dist = compute_lcz_thermal_anomaly(
        lcz_array,
        era5_ds.lon.values, era5_ds.lat.values,
        lcz_lons, lcz_lats
    )

    log.info("\n  ERA5 cells 内部 LCZ 分布 (前 4 个):")
    for k, v in list(cell_lcz_dist.items())[:4]:
        log.info(f"    Cell{k}: {dict(list(v.items())[:5])} ...")

    # 5) 合成 100m UTCI - 全部 168 小时
    utci_100m, delta_at = synthesize_100m_utci(
        era5_ds['utci_C'],
        lcz_array,
        era5_ds.lon.values, era5_ds.lat.values,
        lcz_lons, lcz_lats,
        cell_means
    )

    log.info(f"\n  合成 UTCI 100m 形状: {utci_100m.shape}")
    log.info(f"  UTCI 范围: {np.nanmin(utci_100m):.2f} - {np.nanmax(utci_100m):.2f} °C")

    # 6) 计算夏季 UTCI 汇总指标
    log.info("\n[6] 计算 UTCI 汇总指标 (per 100m grid)")

    utci_mean = np.nanmean(utci_100m, axis=0)
    utci_max = np.nanmax(utci_100m, axis=0)
    utci_p95 = np.nanpercentile(utci_100m, 95, axis=0)

    # TSD: 累计 UTCI > 32°C 小时数
    tsd_strong = np.nansum(utci_100m > 32, axis=0).astype(np.float32)
    tsd_moderate = np.nansum(utci_100m > 26, axis=0).astype(np.float32)

    # HDH: ∑(UTCI - 26) for UTCI > 26
    hdh_grid = np.where(utci_100m > 26, utci_100m - 26, 0)
    hdh = np.nansum(hdh_grid, axis=0)

    log.info(f"    UTCI 平均: {np.nanmean(utci_mean):.2f} °C, max: {np.nanmax(utci_max):.2f} °C")
    log.info(f"    TSD (UTCI>32°C): mean {np.nanmean(tsd_strong):.1f} hr, max {np.nanmax(tsd_strong):.0f} hr")
    log.info(f"    HDH:               mean {np.nanmean(hdh):.1f}, max {np.nanmax(hdh):.0f}")

    # 7) 保存为 NetCDF
    log.info("\n[7] 保存到 data/processed/")
    summary_ds = xr.Dataset(
        {
            'utci_mean': (('y', 'x'), utci_mean),
            'utci_max': (('y', 'x'), utci_max),
            'utci_p95': (('y', 'x'), utci_p95),
            'tsd_strong': (('y', 'x'), tsd_strong),
            'tsd_moderate': (('y', 'x'), tsd_moderate),
            'hdh': (('y', 'x'), hdh),
            'lcz': (('y', 'x'), lcz_array.astype(np.float32)),
        },
        coords={
            'lat': ('y', lcz_lats),
            'lon': ('x', lcz_lons),
        }
    )

    summary_path = PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc"
    summary_ds.to_netcdf(summary_path)
    log.info(f"    汇总: {summary_path}  ({summary_path.stat().st_size/1e6:.1f} MB)")

    log.info("\n🎉 完成！下一步: python scripts/utci_inequality.py")


if __name__ == "__main__":
    main()
