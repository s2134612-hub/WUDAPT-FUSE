"""调试 UTCI 与 pop 网格对齐。"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import xarray as xr
import rioxarray as rxr
from rasterio.enums import Resampling

from src.utils.config import PROCESSED_DATA_DIR

print("[1] 加载 UTCI summary")
utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")
print(f"  UTCI shape: {utci_ds['utci_mean'].shape}")
print(f"  UTCI CRS: {utci_ds.rio.crs if hasattr(utci_ds, 'rio') else 'no rio'}")
print(f"  UTCI dims: {dict(utci_ds.sizes)}")
print(f"  UTCI coords: {list(utci_ds.coords)}")

# 检查 lat/lon
print(f"  lat (y): {utci_ds.lat.values[:3]} ... {utci_ds.lat.values[-3:]}")
print(f"  lon (x): {utci_ds.lon.values[:3]} ... {utci_ds.lon.values[-3:]}")

# 检查是否有 NaN
utci_mean = utci_ds['utci_mean'].values
print(f"  UTCI valid: {(~np.isnan(utci_mean)).sum()} / {utci_mean.size}")
print(f"  UTCI range: {np.nanmin(utci_mean):.2f} - {np.nanmax(utci_mean):.2f}")

# 检查 LCZ
lcz = utci_ds['lcz'].values
print(f"  LCZ valid: {(~np.isnan(lcz)).sum()} / {lcz.size}")

print("\n[2] 加载 pop UTM")
pop_utm = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif", masked=True).squeeze()
print(f"  Pop UTM shape: {pop_utm.shape}")
print(f"  Pop UTM CRS:   {pop_utm.rio.crs}")
pop_utm_vals = pop_utm.values
print(f"  Pop UTM valid: {(~np.isnan(pop_utm_vals) & (pop_utm_vals > 0)).sum()}")

print("\n[3] 重投影 pop 到 WGS84")
pop_wgs = pop_utm.rio.reproject("EPSG:4326")
print(f"  Pop WGS shape: {pop_wgs.shape}")
print(f"  Pop WGS lat range: {pop_wgs.y.values[-1]:.4f} - {pop_wgs.y.values[0]:.4f}")
print(f"  Pop WGS lon range: {pop_wgs.x.values[0]:.4f} - {pop_wgs.x.values[-1]:.4f}")

print("\n[4] UTCI 数据集是否有 rio CRS?")
# UTCI 的坐标用了 lat/lon 名字，但作为变量
# 我们需要明确告诉 rioxarray 哪个是空间维度
print(f"  utci_ds.lat coords: {utci_ds.lat.dims}")
print(f"  utci_ds.lon coords: {utci_ds.lon.dims}")

# 试试给 UTCI 设 CRS 和重命名维度
utci_da = utci_ds['utci_mean'].copy()
print(f"\n  utci_mean dims: {utci_da.dims}")

# 把 lat/lon coords 设为维度坐标
utci_with_xy = utci_da.assign_coords(x=('x', utci_ds.lon.values), y=('y', utci_ds.lat.values))
utci_with_xy = utci_with_xy.rio.write_crs("EPSG:4326")
print(f"  After write_crs: CRS = {utci_with_xy.rio.crs}")

print("\n[5] 重投影 pop 匹配 UTCI 网格")
pop_aligned = pop_utm.rio.reproject_match(utci_with_xy, resampling=Resampling.bilinear)
print(f"  Pop aligned shape: {pop_aligned.shape}")
print(f"  Pop aligned CRS: {pop_aligned.rio.crs}")

pop_arr = pop_aligned.values.squeeze() if pop_aligned.values.ndim == 3 else pop_aligned.values
print(f"  Pop aligned valid > 0: {((~np.isnan(pop_arr)) & (pop_arr > 0)).sum()}")
print(f"  Pop aligned range: {np.nanmin(pop_arr):.2f} - {np.nanmax(pop_arr):.2f}")
print(f"  Pop aligned sum: {np.nansum(pop_arr):,.0f}")

# 三者交集
valid = (~np.isnan(utci_mean)) & (~np.isnan(lcz)) & (~np.isnan(pop_arr)) & (pop_arr > 0)
print(f"\n[6] 三者交集有效栅格: {valid.sum():,}")

if valid.sum() == 0:
    print("\n  调试信息:")
    print(f"    UTCI not nan: {(~np.isnan(utci_mean)).sum()}")
    print(f"    LCZ not nan:  {(~np.isnan(lcz)).sum()}")
    print(f"    Pop not nan:  {(~np.isnan(pop_arr)).sum()}")
    print(f"    Pop > 0:      {(pop_arr > 0).sum()}")

    # UTCI valid mask
    utci_mask = ~np.isnan(utci_mean)
    print(f"\n    UTCI valid 区域内的 pop 值统计:")
    if utci_mask.sum() > 0:
        pops_in_utci = pop_arr[utci_mask]
        print(f"      均值: {np.nanmean(pops_in_utci):.2f}")
        print(f"      最大: {np.nanmax(pops_in_utci):.2f}")
        print(f"      非 NaN 数: {(~np.isnan(pops_in_utci)).sum()}")
        print(f"      > 0 数: {(pops_in_utci > 0).sum()}")
