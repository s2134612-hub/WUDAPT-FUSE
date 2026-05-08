"""
项目当前状态完整检查 - 仅文本输出，不生成图片。
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import rioxarray as rxr
from src.utils.config import RAW_DATA_DIR, SHENZHEN_BBOX

print("=" * 65)
print("WUDAPT-FUSE 项目状态报告")
print("=" * 65)

# ========== 1. 数据库存清单 ==========
print("\n[1] 已下载数据清单:")
print("-" * 65)

data_files = {
    "LCZ (深圳裁剪)": RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif",
    "LCZ (全球原始)": RAW_DATA_DIR / "lcz" / "lcz_filter_v1.tif",
    "WorldPop (深圳)": RAW_DATA_DIR / "worldpop" / "worldpop_shenzhen_100m.tif",
    "WorldPop (中国原始)": RAW_DATA_DIR / "worldpop" / "chn_ppp_2020.tif",
}

for name, path in data_files.items():
    if path.exists():
        size_mb = path.stat().st_size / 1e6
        print(f"  [OK] {name:<25} {size_mb:>8.1f} MB  {path.name}")
    else:
        print(f"  [--] {name:<25} {'缺失':>8}")

# ========== 2. LCZ 数据分析 ==========
print("\n[2] LCZ 深圳数据分析:")
print("-" * 65)

lcz_path = RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif"
if lcz_path.exists():
    lcz = rxr.open_rasterio(lcz_path, masked=True)
    print(f"  形状:          {lcz.shape}")
    print(f"  CRS:           {lcz.rio.crs}")
    bounds = lcz.rio.bounds()
    print(f"  范围 (lon):    {bounds[0]:.4f} - {bounds[2]:.4f}")
    print(f"  范围 (lat):    {bounds[1]:.4f} - {bounds[3]:.4f}")
    res = lcz.rio.resolution()
    print(f"  分辨率:        {res[0]*111000:.0f}m x {abs(res[1])*111000:.0f}m (近似)")

    vals = lcz.values.flatten()
    vals = vals[~np.isnan(vals)].astype(int)

    # LCZ 大类分布
    LCZ_NAMES = {
        1: "Compact high-rise (CHR)", 2: "Compact mid-rise (CMR)", 3: "Compact low-rise (CLR)",
        4: "Open high-rise (OHR)", 5: "Open mid-rise (OMR)", 6: "Open low-rise (OLR)",
        7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built", 10: "Heavy industry",
        11: "Dense trees", 12: "Scattered trees", 13: "Bush, scrub", 14: "Low plants",
        15: "Bare rock/paved", 16: "Bare soil/sand", 17: "Water"
    }

    unique, counts = np.unique(vals, return_counts=True)
    total = vals.size
    built_total = sum(c for u, c in zip(unique, counts) if u <= 10)
    nature_total = sum(c for u, c in zip(unique, counts) if u >= 11)

    print(f"\n  总有效栅格:   {total:,}")
    print(f"  建成区:       {built_total:,} ({100*built_total/total:.1f}%)")
    print(f"  自然/水域:    {nature_total:,} ({100*nature_total/total:.1f}%)")

    print(f"\n  类型分布 (Top 10):")
    sorted_idx = np.argsort(counts)[::-1][:10]
    for idx in sorted_idx:
        u = unique[idx]
        c = counts[idx]
        name = LCZ_NAMES.get(u, "Unknown")
        bar = "#" * int(40 * c / counts.max())
        print(f"    LCZ {u:>2d} {name:<25} {c:>7,} ({100*c/total:>5.1f}%) {bar}")

# ========== 3. WorldPop 数据分析 ==========
print("\n[3] WorldPop 深圳人口数据分析:")
print("-" * 65)

pop_path = RAW_DATA_DIR / "worldpop" / "worldpop_shenzhen_100m.tif"
if pop_path.exists():
    pop = rxr.open_rasterio(pop_path, masked=True)
    print(f"  形状:          {pop.shape}")
    print(f"  CRS:           {pop.rio.crs}")
    bounds = pop.rio.bounds()
    print(f"  范围 (lon):    {bounds[0]:.4f} - {bounds[2]:.4f}")
    print(f"  范围 (lat):    {bounds[1]:.4f} - {bounds[3]:.4f}")

    vals = pop.values.flatten()
    vals = vals[~np.isnan(vals)]
    print(f"\n  总人口:        {vals.sum():,.0f} 人")
    print(f"  人口最稠密栅格: {vals.max():.0f} 人/100m")
    print(f"  人口均值:      {vals.mean():.1f} 人/100m")
    print(f"  非零栅格数:    {(vals > 0).sum():,}")
    print(f"  无人区栅格数:  {(vals == 0).sum():,}")

# ========== 4. LCZ + WorldPop 兼容性检查 ==========
print("\n[4] 数据集对齐性检查:")
print("-" * 65)

if lcz_path.exists() and pop_path.exists():
    lcz_shape = lcz.shape
    pop_shape = pop.shape
    aligned = lcz_shape == pop_shape
    print(f"  LCZ 形状:     {lcz_shape}")
    print(f"  Pop 形状:     {pop_shape}")
    print(f"  形状一致:     {'是' if aligned else '否'}")

    if aligned:
        # 计算 LCZ 类型与人口的关联
        lcz_arr = lcz.values[0]
        pop_arr = pop.values[0]
        valid = ~np.isnan(lcz_arr) & ~np.isnan(pop_arr)

        print(f"\n  LCZ 类型 × 人口 (Top 5 LCZ):")
        print(f"  {'LCZ':<6} {'栅格数':>10} {'人口':>12} {'人口/栅格':>10}")
        lcz_unique = np.unique(lcz_arr[valid].astype(int))
        for u in sorted(lcz_unique)[:10]:
            mask = (lcz_arr == u) & valid
            n_pixels = mask.sum()
            total_pop = pop_arr[mask].sum()
            mean_pop = total_pop / n_pixels if n_pixels > 0 else 0
            print(f"  LCZ {u:<3d} {n_pixels:>10,} {total_pop:>12,.0f} {mean_pop:>10.1f}")

# ========== 5. 还需获取的数据 ==========
print("\n[5] 待获取数据:")
print("-" * 65)
todo_data = {
    "ERA5-HEAT UTCI": "需 ECMWF CDS 账号",
    "Landsat 8/9 LST": "需 Earth Engine 账号",
    "MODIS LST": "需 NASA Earthdata 账号",
    "MMS 站点观测": "需联系深圳气象局或合作课题组",
    "建筑数据 (UMPs)": "需 OSM 或高德 API",
}
for name, status in todo_data.items():
    print(f"  [TODO] {name:<20} - {status}")

# ========== 6. 下一步建议 ==========
print("\n" + "=" * 65)
print("下一步建议:")
print("=" * 65)
print("""
方案 A: 注册 ECMWF CDS 账号获取 ERA5-HEAT UTCI（最重要）
方案 B: 用现有 LCZ + WorldPop 先做不平等分析（不需 UTCI）
方案 C: 计算 UMPs（用 OSM 建筑数据，不需账号）
""")
