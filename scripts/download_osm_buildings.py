"""
从 OpenStreetMap 下载深圳建筑数据。

策略:
  1. 用 OSMnx 直接拉取 bbox 内的 building 要素
  2. 提取建筑高度/层数（如有）
  3. 保存为 GeoPackage（GPKG）便于后续处理
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox

from src.utils.config import SHENZHEN_BBOX, RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("download_osm")

OSM_DIR = RAW_DATA_DIR / "osm"
OSM_DIR.mkdir(parents=True, exist_ok=True)


def download_buildings():
    """下载 Shenzhen 全部 building 要素"""
    out_path = OSM_DIR / "shenzhen_buildings.gpkg"

    if out_path.exists():
        log.info(f"  已存在: {out_path}")
        gdf = gpd.read_file(out_path)
        log.info(f"  建筑数量: {len(gdf):,}")
        return gdf

    log.info("  从 OSM 拉取深圳建筑（可能需要 5-15 分钟）")
    log.info(f"  bbox: lat {SHENZHEN_BBOX['south']}-{SHENZHEN_BBOX['north']}, "
             f"lon {SHENZHEN_BBOX['west']}-{SHENZHEN_BBOX['east']}")

    # 配置 OSMnx
    ox.settings.timeout = 1800  # 30 分钟超时
    ox.settings.use_cache = True
    ox.settings.log_console = False

    # bbox 在 osmnx 2.x 中是 (left, bottom, right, top) = (W, S, E, N)
    bbox = (
        SHENZHEN_BBOX['west'],
        SHENZHEN_BBOX['south'],
        SHENZHEN_BBOX['east'],
        SHENZHEN_BBOX['north']
    )

    t0 = time.time()
    try:
        gdf = ox.features_from_bbox(
            bbox=bbox,
            tags={"building": True}
        )
    except Exception as e:
        log.error(f"  OSM 下载失败: {e}")
        return None

    elapsed = time.time() - t0
    log.info(f"  下载完成，用时 {elapsed:.0f} 秒")
    log.info(f"  建筑数量: {len(gdf):,}")

    # 仅保留 polygon/multipolygon
    geom_types = gdf.geometry.geom_type.value_counts()
    log.info(f"  几何类型: {dict(geom_types)}")
    gdf = gdf[gdf.geometry.geom_type.isin(['Polygon', 'MultiPolygon'])].copy()
    log.info(f"  保留 polygon: {len(gdf):,}")

    # 关键属性检查
    cols_of_interest = [
        'building', 'building:levels', 'building:height',
        'height', 'levels', 'roof:levels', 'roof:height',
        'amenity', 'name'
    ]
    available = [c for c in cols_of_interest if c in gdf.columns]
    log.info(f"  可用属性: {available}")

    # 仅保留必要列以减小文件
    keep_cols = ['geometry'] + available
    gdf = gdf[keep_cols].reset_index(drop=True)

    # 保存
    log.info(f"  保存到 {out_path}")
    gdf.to_file(out_path, driver='GPKG')
    size_mb = out_path.stat().st_size / 1e6
    log.info(f"  文件大小: {size_mb:.1f} MB")

    return gdf


def parse_building_height(gdf):
    """解析建筑高度（从多个属性优先级合并）"""
    log.info("\n[2] 解析建筑高度")

    n = len(gdf)
    height = np.full(n, np.nan, dtype=np.float32)

    # 优先级 1: 'building:height' 或 'height'
    for col in ['building:height', 'height']:
        if col in gdf.columns:
            mask = gdf[col].notna() & np.isnan(height)
            for idx in gdf[mask].index:
                try:
                    val = str(gdf.loc[idx, col]).replace('m', '').replace(' ', '').strip()
                    h = float(val)
                    if 0 < h < 1000:
                        height[idx] = h
                except (ValueError, TypeError):
                    pass

    n_height_direct = (~np.isnan(height)).sum()
    log.info(f"    直接高度属性: {n_height_direct:,} 个建筑")

    # 优先级 2: 'building:levels' × 3.0m/层
    for col in ['building:levels', 'levels']:
        if col in gdf.columns:
            mask = gdf[col].notna() & np.isnan(height)
            for idx in gdf[mask].index:
                try:
                    levels = float(gdf.loc[idx, col])
                    if 0 < levels < 200:
                        height[idx] = levels * 3.0
                except (ValueError, TypeError):
                    pass

    n_with_height = (~np.isnan(height)).sum()
    log.info(f"    含层数转换后: {n_with_height:,} ({100*n_with_height/n:.1f}%)")

    # 优先级 3: 默认按建筑面积估算（或填中位数）
    if n_with_height > 0:
        median_h = np.nanmedian(height)
        log.info(f"    已知高度中位数: {median_h:.1f} m")
        # 缺失值填中位数
        height[np.isnan(height)] = median_h

    gdf = gdf.copy()
    gdf['height'] = height
    return gdf


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("OSM Shenzhen 建筑数据下载")
    log.info("=" * 65)

    # 1) 下载
    gdf = download_buildings()
    if gdf is None or len(gdf) == 0:
        log.error("下载失败")
        return

    # 2) 解析高度
    gdf = parse_building_height(gdf)

    # 3) 投影到 UTM 50N（米制）
    log.info("\n[3] 投影到 UTM 50N (米制)")
    gdf_utm = gdf.to_crs("EPSG:32650")

    # 计算面积
    gdf_utm['area_m2'] = gdf_utm.geometry.area
    log.info(f"    建筑面积统计:")
    log.info(f"      数量: {len(gdf_utm):,}")
    log.info(f"      平均: {gdf_utm['area_m2'].mean():.1f} m²")
    log.info(f"      中位: {gdf_utm['area_m2'].median():.1f} m²")
    log.info(f"      总和: {gdf_utm['area_m2'].sum()/1e6:.1f} km²")

    # 估计体积
    gdf_utm['volume_m3'] = gdf_utm['area_m2'] * gdf_utm['height']

    # 保存 UTM 版本
    out_utm = OSM_DIR / "shenzhen_buildings_utm.gpkg"
    gdf_utm.to_file(out_utm, driver='GPKG')
    log.info(f"\n[4] UTM 版本保存: {out_utm}")
    log.info(f"   大小: {out_utm.stat().st_size/1e6:.1f} MB")

    log.info("\n🎉 OSM 建筑数据准备完成！")
    log.info("\n下一步: python scripts/compute_umps.py")


if __name__ == "__main__":
    main()
