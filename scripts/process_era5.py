"""
处理 ERA5-HEAT 下载的 ZIP（含多个日 NetCDF），合并为单一文件并可视化。

运行: python scripts/process_era5.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from src.utils.config import RAW_DATA_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("process_era5")


def extract_zip(zip_path):
    """如果文件是 ZIP，解压到同名目录"""
    extract_dir = zip_path.parent / "extracted"
    extract_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    nc_files = sorted(extract_dir.glob("*.nc"))
    log.info(f"  提取出 {len(nc_files)} 个 NetCDF 文件")
    return nc_files


def merge_era5_daily(nc_files, output_path):
    """合并多个日 NC 文件为单一 NC"""
    log.info(f"  合并 {len(nc_files)} 个日文件...")

    datasets = []
    for nc in nc_files:
        ds = xr.open_dataset(nc)
        datasets.append(ds)

    # 沿时间轴合并
    merged = xr.concat(datasets, dim='time')

    # 排序
    if 'time' in merged.dims:
        merged = merged.sortby('time')

    log.info(f"  合并后维度: {dict(merged.dims)}")
    log.info(f"  变量: {list(merged.data_vars)}")

    merged.to_netcdf(output_path)
    log.info(f"  ✓ 合并文件: {output_path}")
    return merged


def plot_era5_utci(ds, output_path):
    """绘制 ERA5 UTCI 图"""
    log.info("  绘制 UTCI...")

    # 找 UTCI 变量
    utci_var = None
    for v in ds.data_vars:
        if 'utci' in v.lower() or 'thermal' in v.lower():
            utci_var = v
            break
    if utci_var is None:
        utci_var = list(ds.data_vars)[0]

    log.info(f"  UTCI 变量: {utci_var}")

    utci = ds[utci_var]
    log.info(f"  UTCI 维度: {utci.dims}, 形状: {utci.shape}")

    # ERA5 UTCI 单位是开尔文
    if utci.mean().values > 200:
        utci_c = utci - 273.15
        utci_c.attrs['units'] = '°C'
    else:
        utci_c = utci

    log.info(f"  UTCI 范围: {float(utci_c.min()):.1f} - {float(utci_c.max()):.1f} °C")

    # 时空展示
    n_times = utci_c.sizes.get('time', 0)
    log.info(f"  总时间步: {n_times}")

    fig, axes = plt.subplots(2, 4, figsize=(20, 9))
    sample_idx = np.linspace(0, n_times - 1, 8, dtype=int)

    vmin = float(utci_c.min())
    vmax = float(utci_c.max())

    # 找经纬度坐标名
    lon_name = next((c for c in ['longitude', 'lon', 'x'] if c in utci_c.coords), None)
    lat_name = next((c for c in ['latitude', 'lat', 'y'] if c in utci_c.coords), None)

    last_im = None
    for ax, t_idx in zip(axes.flat, sample_idx):
        snapshot = utci_c.isel(time=t_idx)

        if lon_name and lat_name:
            extent = [float(snapshot[lon_name].min()), float(snapshot[lon_name].max()),
                      float(snapshot[lat_name].min()), float(snapshot[lat_name].max())]
        else:
            extent = None

        last_im = ax.imshow(
            snapshot.values, cmap='RdYlBu_r', vmin=vmin, vmax=vmax,
            extent=extent, origin='upper', aspect='auto'
        )

        time_val = utci_c.time.values[t_idx]
        # 转 datetime 格式
        time_str = str(time_val)[:13]
        ax.set_title(time_str, fontsize=10)
        if lon_name:
            ax.set_xlabel('Longitude' if t_idx >= n_times - 4 else '')
        if lat_name and t_idx % 4 == 0:
            ax.set_ylabel('Latitude')

    fig.suptitle(
        f"Shenzhen ERA5-HEAT UTCI · 2020-07-15 to 07-21 · 25 km grid\n"
        f"Range: [{vmin:.1f}, {vmax:.1f}] °C",
        fontsize=14
    )

    cbar = fig.colorbar(last_im, ax=axes.ravel().tolist(), shrink=0.7,
                        label='UTCI (°C)', pad=0.02)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    log.info(f"  ✓ {output_path}")


def main():
    ensure_dirs()
    log.info("=" * 60)
    log.info("ERA5-HEAT 数据处理与可视化")
    log.info("=" * 60)

    raw_zip = RAW_DATA_DIR / "era5" / "era5_heat_shenzhen_2020_07_15_21.nc"
    merged_nc = RAW_DATA_DIR / "era5" / "era5_heat_shenzhen_2020_07_15_21_merged.nc"
    fig_path = FIGURES_DIR / "03_era5_heat_utci.png"

    if not raw_zip.exists():
        log.error(f"原始文件不存在: {raw_zip}")
        sys.exit(1)

    # 解压
    nc_files = extract_zip(raw_zip)

    # 合并
    if not merged_nc.exists():
        ds = merge_era5_daily(nc_files, merged_nc)
    else:
        ds = xr.open_dataset(merged_nc)
        log.info(f"  使用已合并文件: {merged_nc}")

    # 可视化
    plot_era5_utci(ds, fig_path)

    log.info("\n🎉 ERA5-HEAT 处理完成")


if __name__ == "__main__":
    main()
