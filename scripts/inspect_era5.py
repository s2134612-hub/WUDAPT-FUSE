"""检查已下载的 ERA5-HEAT 数据。"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import zipfile
import xarray as xr
import numpy as np

from src.utils.config import RAW_DATA_DIR
from src.utils.logging import get_logger

log = get_logger("inspect_era5")

ERA5_DIR = RAW_DATA_DIR / "era5"

print("=" * 60)
print("ERA5-HEAT 数据检查")
print("=" * 60)

# 列出所有文件
print("\n[1] 已有文件:")
for f in sorted(ERA5_DIR.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(ERA5_DIR)}: {f.stat().st_size/1024:.1f} KB")

# 尝试打开主数据文件
print("\n[2] 尝试打开数据:")

# 找到下载的 zip
zip_files = list(ERA5_DIR.glob("*.zip"))
nc_files = [f for f in ERA5_DIR.rglob("*.nc")]

print(f"  zip 文件: {len(zip_files)}")
print(f"  nc 文件:  {len(nc_files)}")

# 检查 zip 内容
if zip_files:
    zip_path = zip_files[0]
    print(f"\n  检查 ZIP: {zip_path.name}")
    with zipfile.ZipFile(zip_path, 'r') as z:
        for name in z.namelist():
            info = z.getinfo(name)
            print(f"    {name}: {info.file_size/1024:.1f} KB")

    # 解压（如果还没）
    extract_dir = ERA5_DIR / "extracted"
    extract_dir.mkdir(exist_ok=True)
    print(f"\n  解压到: {extract_dir}")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_dir)

# 列出解压后的文件
extract_dir = ERA5_DIR / "extracted"
if extract_dir.exists():
    print(f"\n[3] 解压目录内容:")
    for f in sorted(extract_dir.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(extract_dir)}: {f.stat().st_size/1024:.1f} KB")

    # 试图打开第一个 .nc
    nc_in_extract = list(extract_dir.rglob("*.nc"))
    if nc_in_extract:
        for nc_path in nc_in_extract:
            print(f"\n[4] 打开 {nc_path.name}:")
            try:
                ds = xr.open_dataset(nc_path)
                print(f"  Variables:   {list(ds.data_vars)}")
                print(f"  Dimensions:  {dict(ds.sizes)}")
                print(f"  Coords:      {list(ds.coords)}")

                # 找到数据变量
                for var_name in ds.data_vars:
                    var = ds[var_name]
                    print(f"\n  '{var_name}':")
                    print(f"    Shape: {var.shape}")
                    print(f"    Units: {var.attrs.get('units', 'unknown')}")
                    vals = var.values
                    valid = vals[~np.isnan(vals)] if vals.size > 0 else vals
                    if valid.size > 0:
                        print(f"    Min: {valid.min():.2f}, Max: {valid.max():.2f}, Mean: {valid.mean():.2f}")

                # 时间范围
                if 'valid_time' in ds.coords:
                    times = ds.valid_time.values
                    print(f"\n  Time range: {times.min()} - {times.max()}")
                    print(f"  Time count: {len(times)}")
                elif 'time' in ds.coords:
                    times = ds.time.values
                    print(f"\n  Time range: {times.min()} - {times.max()}")
                    print(f"  Time count: {len(times)}")

                # 经纬度
                lat_name = next((c for c in ['latitude', 'lat'] if c in ds.coords), None)
                lon_name = next((c for c in ['longitude', 'lon'] if c in ds.coords), None)
                if lat_name and lon_name:
                    print(f"\n  Lat: {ds[lat_name].min().item():.2f} - {ds[lat_name].max().item():.2f} ({ds[lat_name].size} 点)")
                    print(f"  Lon: {ds[lon_name].min().item():.2f} - {ds[lon_name].max().item():.2f} ({ds[lon_name].size} 点)")

                ds.close()
            except Exception as e:
                print(f"  ✗ 打开失败: {e}")
