"""
为 3 个新城市准备 LCZ + WorldPop 子集（全局数据已有）。
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import rioxarray as rxr

from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.utils.cities import CITIES

log = get_logger("multicity_prepare")


def crop_lcz(city_key, lcz_global_path):
    cfg = CITIES[city_key]
    bbox = cfg['bbox']
    out_path = RAW_DATA_DIR / "lcz" / f"lcz_{city_key}_100m.tif"

    if out_path.exists():
        log.info(f"  ✓ {out_path.name} 已存在")
        return out_path

    log.info(f"  裁剪 LCZ: {cfg['name']}...")
    lcz = rxr.open_rasterio(lcz_global_path, masked=True)
    sub = lcz.rio.clip_box(
        minx=bbox['west'], miny=bbox['south'],
        maxx=bbox['east'], maxy=bbox['north']
    )
    sub.rio.to_raster(out_path)
    log.info(f"  ✓ {out_path.name}: {sub.shape}")
    return out_path


def reproject_to_utm(src_path, out_path, resolution_m=100,
                      crs="EPSG:32650"):
    """LCZ WGS84 -> UTM"""
    if out_path.exists():
        return out_path
    from rasterio.enums import Resampling
    da = rxr.open_rasterio(src_path, masked=True)
    da_utm = da.rio.reproject(crs, resolution=resolution_m,
                               resampling=Resampling.nearest)
    da_utm.rio.to_raster(out_path)
    log.info(f"  ✓ {out_path.name}: {da_utm.shape}")
    return out_path


def crop_pop(city_key, pop_global_path):
    """WorldPop 裁剪 + UTM"""
    cfg = CITIES[city_key]
    bbox = cfg['bbox']
    out_wgs = RAW_DATA_DIR / "worldpop" / f"worldpop_{city_key}_wgs.tif"
    out_utm = PROCESSED_DATA_DIR / f"{city_key}_pop_100m_utm.tif"

    if out_utm.exists():
        log.info(f"  ✓ {out_utm.name} 已存在")
        return out_utm

    log.info(f"  裁剪 WorldPop: {cfg['name']}...")
    pop = rxr.open_rasterio(pop_global_path, masked=True)
    sub = pop.rio.clip_box(
        minx=bbox['west'], miny=bbox['south'],
        maxx=bbox['east'], maxy=bbox['north']
    )
    sub.rio.to_raster(out_wgs)

    # UTM
    from rasterio.enums import Resampling
    sub_utm = sub.rio.reproject("EPSG:32650", resolution=100,
                                 resampling=Resampling.bilinear)
    sub_utm.rio.to_raster(out_utm)
    log.info(f"  ✓ {out_utm.name}: {sub_utm.shape}")
    return out_utm


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("GBA 多城市数据准备（LCZ + WorldPop）")
    log.info("=" * 65)

    lcz_global = RAW_DATA_DIR / "lcz" / "lcz_filter_v1.tif"
    pop_global = RAW_DATA_DIR / "worldpop" / "chn_ppp_2020.tif"

    if not lcz_global.exists():
        log.error(f"  缺少全球 LCZ: {lcz_global}")
        return
    if not pop_global.exists():
        log.error(f"  缺少全球 WorldPop: {pop_global}")
        return

    cities = ['guangzhou', 'dongguan', 'foshan']
    for city in cities:
        log.info(f"\n--- {city.upper()} ---")

        # LCZ
        lcz_wgs = crop_lcz(city, lcz_global)

        # LCZ UTM
        lcz_utm_path = PROCESSED_DATA_DIR / f"{city}_lcz_100m_utm.tif"
        reproject_to_utm(lcz_wgs, lcz_utm_path)

        # WorldPop
        crop_pop(city, pop_global)

    log.info("\n所有城市数据准备完成")


if __name__ == "__main__":
    main()
