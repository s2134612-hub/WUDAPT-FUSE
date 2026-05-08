"""
将 LCZ 和 WorldPop 重投影对齐到统一的 100m × 100m 标准网格。

使用 EPSG:32650 (UTM Zone 50N)，深圳所在 UTM 带，米制。
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import rioxarray as rxr
from rasterio.enums import Resampling
from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SHENZHEN_BBOX, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("align_grids")


def main():
    ensure_dirs()
    log.info("=" * 60)
    log.info("数据网格对齐：LCZ + WorldPop -> 100m UTM 标准网格")
    log.info("=" * 60)

    lcz_path = RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif"
    pop_path = RAW_DATA_DIR / "worldpop" / "worldpop_shenzhen_100m.tif"

    out_lcz = PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif"
    out_pop = PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif"
    out_lcz.parent.mkdir(parents=True, exist_ok=True)

    # === Step 1: 加载 LCZ 并投影到 UTM ===
    log.info("\n[1] 加载 LCZ...")
    lcz = rxr.open_rasterio(lcz_path, masked=True)
    log.info(f"    原始 CRS: {lcz.rio.crs}")
    log.info(f"    原始形状: {lcz.shape}")

    log.info("    重投影到 EPSG:32650 (UTM 50N)，100m 分辨率...")
    lcz_utm = lcz.rio.reproject(
        "EPSG:32650",
        resolution=100,
        resampling=Resampling.nearest,  # LCZ 是分类，用最近邻
    )
    log.info(f"    UTM 形状: {lcz_utm.shape}")
    bounds = lcz_utm.rio.bounds()
    log.info(f"    UTM 范围: x={bounds[0]:.0f}-{bounds[2]:.0f}, y={bounds[1]:.0f}-{bounds[3]:.0f}")

    # === Step 2: 重投影 WorldPop 并对齐到 LCZ 网格 ===
    log.info("\n[2] 加载 WorldPop 并对齐...")
    pop = rxr.open_rasterio(pop_path, masked=True)
    log.info(f"    原始 CRS: {pop.rio.crs}")
    log.info(f"    原始形状: {pop.shape}")

    log.info("    重投影到 LCZ 的 UTM 网格...")
    pop_utm = pop.rio.reproject_match(
        lcz_utm,
        resampling=Resampling.bilinear,  # 人口可插值
    )
    log.info(f"    对齐后形状: {pop_utm.shape}")

    # === Step 3: 验证对齐 ===
    log.info("\n[3] 对齐验证:")
    aligned = lcz_utm.shape == pop_utm.shape
    log.info(f"    形状相同: {aligned} ({lcz_utm.shape} vs {pop_utm.shape})")
    log.info(f"    LCZ 边界: {lcz_utm.rio.bounds()}")
    log.info(f"    Pop 边界: {pop_utm.rio.bounds()}")

    # === Step 4: 保存 ===
    log.info(f"\n[4] 保存到 {PROCESSED_DATA_DIR}")
    lcz_utm.rio.to_raster(out_lcz, dtype="uint8")
    pop_utm.rio.to_raster(out_pop, dtype="float32")
    log.info(f"    {out_lcz.name}  ({out_lcz.stat().st_size/1e6:.1f} MB)")
    log.info(f"    {out_pop.name}  ({out_pop.stat().st_size/1e6:.1f} MB)")

    # === Step 5: 联合统计 ===
    log.info("\n[5] LCZ × 人口联合统计:")
    log.info("-" * 60)

    LCZ_NAMES = {
        1: "Compact high-rise", 2: "Compact mid-rise", 3: "Compact low-rise",
        4: "Open high-rise", 5: "Open mid-rise", 6: "Open low-rise",
        7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built",
        10: "Heavy industry", 11: "Dense trees", 12: "Scattered trees",
        13: "Bush, scrub", 14: "Low plants", 15: "Bare rock/paved",
        16: "Bare soil/sand", 17: "Water"
    }

    lcz_arr = lcz_utm.values[0]
    pop_arr = pop_utm.values[0]
    valid = (~np.isnan(lcz_arr)) & (~np.isnan(pop_arr))
    pop_arr_valid = np.where(valid, pop_arr, 0)

    print(f"\n  {'LCZ':<6} {'类型':<22} {'栅格数':>8} {'总人口':>12} {'均值/栅格':>10}")
    print("  " + "-" * 64)

    total_pop = 0
    lcz_int = lcz_arr.astype(np.int16)
    for u in sorted(np.unique(lcz_int[valid])):
        mask = (lcz_int == u) & valid
        n = mask.sum()
        p = pop_arr_valid[mask].sum()
        mean = p / n if n > 0 else 0
        total_pop += p
        name = LCZ_NAMES.get(int(u), "Unknown")[:20]
        print(f"  {int(u):>3d}    {name:<22} {n:>8,} {p:>12,.0f} {mean:>10.1f}")

    print("  " + "-" * 64)
    print(f"  总计:                          {valid.sum():>8,} {total_pop:>12,.0f}")

    log.info(f"\n[6] 关键洞察:")
    log.info("-" * 60)

    # 各 LCZ 类型的人口集中度
    high_pop_lczs = []
    for u in sorted(np.unique(lcz_int[valid])):
        if u <= 10:  # 仅建成区
            mask = (lcz_int == u) & valid
            p = pop_arr_valid[mask].sum()
            n = mask.sum()
            if n > 0:
                mean = p / n
                high_pop_lczs.append((int(u), n, p, mean))

    high_pop_lczs.sort(key=lambda x: x[3], reverse=True)
    log.info("\n  人口最密集的建成 LCZ (Top 5):")
    for u, n, p, mean in high_pop_lczs[:5]:
        name = LCZ_NAMES.get(u, "Unknown")[:25]
        log.info(f"    LCZ {u:>2d} {name:<27} {mean:>6.1f} 人/100m")

    log.info("\n🎉 数据对齐完成！可以开始 Phase 1 主分析了")
    log.info("\n下一步选项:")
    log.info("  A) 注册 ECMWF CDS 账号下载 ERA5-HEAT UTCI")
    log.info("  B) 用 OSM 计算 UMPs（建筑形态参数）")
    log.info("  C) 直接基于 LCZ + 人口做初步不平等分析")


if __name__ == "__main__":
    main()
