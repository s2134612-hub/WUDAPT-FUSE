"""
可视化已下载的所有数据：
  1. LCZ 深圳分布图
  2. WorldPop 人口栅格
  3. ERA5-HEAT UTCI 时空分布

运行: python scripts/visualize_data.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm

from src.utils.config import RAW_DATA_DIR, FIGURES_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("visualize")


# LCZ 标准配色方案（Stewart-Oke 2012）
LCZ_COLORS = {
    1:  "#910613",  # Compact high-rise
    2:  "#D9081C",  # Compact mid-rise
    3:  "#FF0A22",  # Compact low-rise
    4:  "#C54F1E",  # Open high-rise
    5:  "#FF6628",  # Open mid-rise
    6:  "#FF985E",  # Open low-rise
    7:  "#FDED3F",  # Lightweight low-rise
    8:  "#BBBBBB",  # Large low-rise
    9:  "#FFCBAB",  # Sparsely built
    10: "#565656",  # Heavy industry
    11: "#006A18",  # Dense trees (A)
    12: "#00A926",  # Scattered trees (B)
    13: "#628432",  # Bush, scrub (C)
    14: "#B5DA7F",  # Low plants (D)
    15: "#000000",  # Bare rock/paved (E)
    16: "#FCF7B1",  # Bare soil/sand (F)
    17: "#656BFA",  # Water (G)
}

LCZ_LABELS = {
    1: "1: Compact high-rise",  2: "2: Compact mid-rise",
    3: "3: Compact low-rise",   4: "4: Open high-rise",
    5: "5: Open mid-rise",      6: "6: Open low-rise",
    7: "7: Lightweight",        8: "8: Large low-rise",
    9: "9: Sparsely built",     10: "10: Heavy industry",
    11: "A: Dense trees",       12: "B: Scattered trees",
    13: "C: Bush",              14: "D: Low plants",
    15: "E: Bare rock/paved",   16: "F: Bare soil/sand",
    17: "G: Water",
}


def plot_lcz():
    log.info("绘制 LCZ 地图...")

    lcz_path = RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif"
    if not lcz_path.exists():
        log.error(f"  LCZ 文件不存在: {lcz_path}")
        return None

    import rioxarray as rxr
    lcz = rxr.open_rasterio(lcz_path).squeeze()
    data = lcz.values

    # 构建 colormap
    bounds = list(LCZ_COLORS.keys()) + [18]
    colors = [LCZ_COLORS[k] for k in sorted(LCZ_COLORS.keys())]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(np.array(bounds) - 0.5, ncolors=len(colors))

    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(
        data,
        cmap=cmap,
        norm=norm,
        extent=[float(lcz.x.min()), float(lcz.x.max()),
                float(lcz.y.min()), float(lcz.y.max())]
    )

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Shenzhen Local Climate Zones (100 m, Demuzere et al. 2022)")

    # 图例
    patches = [mpatches.Patch(color=LCZ_COLORS[k], label=LCZ_LABELS[k])
               for k in sorted(LCZ_COLORS.keys())]
    ax.legend(handles=patches, bbox_to_anchor=(1.02, 1), loc='upper left',
              fontsize=8, frameon=False)

    output = FIGURES_DIR / "01_lcz_shenzhen.png"
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()
    log.info(f"  ✓ {output}")
    return output


def plot_worldpop():
    log.info("绘制 WorldPop 人口...")

    wp_path = RAW_DATA_DIR / "worldpop" / "worldpop_shenzhen_100m.tif"
    if not wp_path.exists():
        log.warning(f"  WorldPop 子集不存在: {wp_path}")
        log.info(f"  先生成子集...")

        full_path = RAW_DATA_DIR / "worldpop" / "chn_ppp_2020.tif"
        if not full_path.exists():
            log.error(f"  WorldPop 全国数据也不存在: {full_path}")
            return None

        from src.utils.config import SHENZHEN_BBOX
        import rioxarray as rxr
        pop = rxr.open_rasterio(full_path, masked=True)
        sz_pop = pop.rio.clip_box(
            minx=SHENZHEN_BBOX['west'],
            miny=SHENZHEN_BBOX['south'],
            maxx=SHENZHEN_BBOX['east'],
            maxy=SHENZHEN_BBOX['north']
        )
        sz_pop.rio.to_raster(wp_path)
        log.info(f"  深圳 WorldPop 子集生成: {wp_path}")

    import rioxarray as rxr
    wp = rxr.open_rasterio(wp_path, masked=True).squeeze()
    data = wp.values

    fig, ax = plt.subplots(figsize=(14, 7))

    # 用 log 变换以便看清低人口区
    data_log = np.log1p(np.where(data > 0, data, 0))

    im = ax.imshow(
        data_log,
        cmap='YlOrRd',
        extent=[float(wp.x.min()), float(wp.x.max()),
                float(wp.y.min()), float(wp.y.max())]
    )

    cbar = plt.colorbar(im, ax=ax, fraction=0.04)
    cbar.set_label("log(1 + Population per 100 m grid)")

    total_pop = float(np.nansum(data))
    ax.set_title(f"Shenzhen Population (WorldPop 2020, 100m) — Total: {total_pop:,.0f}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    output = FIGURES_DIR / "02_worldpop_shenzhen.png"
    plt.tight_layout()
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()
    log.info(f"  ✓ {output}")
    return output


def plot_era5_heat():
    log.info("绘制 ERA5-HEAT UTCI...")

    era5_path = RAW_DATA_DIR / "era5" / "era5_heat_shenzhen_2020_07_15_21.nc"
    if not era5_path.exists():
        log.error(f"  ERA5 文件不存在: {era5_path}")
        return None

    import xarray as xr
    ds = xr.open_dataset(era5_path)
    log.info(f"  数据变量: {list(ds.data_vars)}")
    log.info(f"  维度: {dict(ds.dims)}")

    # 找到 UTCI 变量
    utci_var = None
    for vname in ds.data_vars:
        if 'utci' in vname.lower() or 'thermal' in vname.lower():
            utci_var = vname
            break
    if utci_var is None:
        utci_var = list(ds.data_vars)[0]

    log.info(f"  使用变量: {utci_var}")

    # 转换为摄氏度（ERA5 UTCI 是开尔文）
    utci = ds[utci_var]
    if utci.mean().values > 200:  # 还是开尔文
        utci = utci - 273.15

    # 4 张子图：4 个不同时刻
    fig, axes = plt.subplots(2, 4, figsize=(20, 8))

    n_times = utci.sizes.get('valid_time', utci.sizes.get('time', 0))
    n_show = min(8, n_times)
    sample_indices = np.linspace(0, n_times - 1, n_show, dtype=int)

    time_dim = 'valid_time' if 'valid_time' in utci.dims else 'time'
    vmin, vmax = float(utci.min()), float(utci.max())

    for ax, t_idx in zip(axes.flat, sample_indices):
        snapshot = utci.isel({time_dim: t_idx})
        im = ax.imshow(
            snapshot.values,
            cmap='RdYlBu_r',
            vmin=vmin, vmax=vmax,
            extent=[float(utci.longitude.min()) if 'longitude' in utci.dims
                    else float(utci.x.min()),
                    float(utci.longitude.max()) if 'longitude' in utci.dims
                    else float(utci.x.max()),
                    float(utci.latitude.min()) if 'latitude' in utci.dims
                    else float(utci.y.min()),
                    float(utci.latitude.max()) if 'latitude' in utci.dims
                    else float(utci.y.max())]
        )
        time_val = utci[time_dim].values[t_idx]
        ax.set_title(str(time_val)[:13])

    fig.suptitle("Shenzhen ERA5-HEAT UTCI (2020-07-15 to 07-21)\n"
                 f"Range: [{vmin:.1f}, {vmax:.1f}] °C", fontsize=14)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.6, label="UTCI (°C)")

    output = FIGURES_DIR / "03_era5_heat_utci.png"
    plt.savefig(output, dpi=150, bbox_inches='tight')
    plt.close()
    log.info(f"  ✓ {output}")
    return output


def main():
    ensure_dirs()
    log.info("=" * 60)
    log.info("WUDAPT-FUSE 数据可视化")
    log.info("=" * 60)

    figures = []
    for fn in [plot_lcz, plot_worldpop, plot_era5_heat]:
        try:
            result = fn()
            if result:
                figures.append(result)
        except Exception as e:
            log.error(f"  失败: {e}")

    log.info(f"\n生成图表: {len(figures)}")
    for f in figures:
        log.info(f"  - {f}")


if __name__ == "__main__":
    main()
