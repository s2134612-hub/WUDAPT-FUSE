"""
计算深圳 100m 网格上的 10 个 UMPs。

输入:
  data/raw/osm/shenzhen_buildings_utm.gpkg     (OSM 建筑)
  data/processed/shenzhen_lcz_100m_utm.tif      (LCZ 类型)

输出:
  data/processed/shenzhen_umps_100m.nc          (含 7+ 个 UMP 变量)
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import xarray as xr
import geopandas as gpd
import rioxarray as rxr

from src.utils.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.analysis.umps import (
    compute_umps_from_buildings, compute_svf_simple,
    compute_psf_from_lcz, compute_wsf_from_lcz
)

log = get_logger("compute_umps")


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info("UMPs 计算（10 个城市形态参数）")
    log.info("=" * 65)

    # === 1. 加载 OSM 建筑（UTM）===
    log.info("\n[1] 加载 OSM 建筑")
    buildings_path = RAW_DATA_DIR / "osm" / "shenzhen_buildings_utm.gpkg"
    if not buildings_path.exists():
        log.error(f"  建筑文件不存在: {buildings_path}")
        log.error(f"  请先运行: python scripts/download_osm_buildings.py")
        return False

    buildings = gpd.read_file(buildings_path)
    log.info(f"  建筑数量: {len(buildings):,}")
    log.info(f"  CRS: {buildings.crs}")

    # === 2. 加载 LCZ（UTM）===
    log.info("\n[2] 加载 LCZ 100m UTM")
    lcz_path = PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif"
    lcz_da = rxr.open_rasterio(lcz_path, masked=True).squeeze()
    log.info(f"  LCZ 形状: {lcz_da.shape}")

    # 用 LCZ 边界作为 UMP 计算的网格基准
    bounds = lcz_da.rio.bounds()
    log.info(f"  研究区: {bounds}")
    transform = lcz_da.rio.transform()
    res = abs(transform.a)
    log.info(f"  分辨率: {res:.0f} m")

    # === 3. 计算 UMPs（基于建筑） ===
    log.info("\n[3] 计算建筑相关 UMPs")
    umps = compute_umps_from_buildings(
        buildings,
        bounds=bounds,
        resolution_m=int(res),
        log=log
    )

    bsf = umps['BSF']
    mbh = umps['MBH']
    sbh = umps['SBH']
    mbw = umps['MBW']
    bv = umps['BV']
    gfa = umps['GFA']
    bldg_count = umps['BLDG_COUNT']

    # === 4. 派生 UMPs ===
    log.info("\n[4] 派生 SVF / PSF / WSF")

    # SVF
    svf = compute_svf_simple(bsf, mbh, h0=10.0)
    log.info(f"  SVF: 平均 {svf.mean():.3f}, 最小 {svf.min():.3f}")

    # 注意: UMP 数组的 (j, i) 顺序是从下往上 (UTM, north-up)
    # 但 LCZ 的 (y, x) 顺序是从上往下 (rasterio 默认)
    # 必须把 UMP 翻转或对齐
    log.info("  对齐 UMP 与 LCZ 网格方向...")
    bsf = np.flipud(bsf)
    mbh = np.flipud(mbh)
    sbh = np.flipud(sbh)
    mbw = np.flipud(mbw)
    bv = np.flipud(bv)
    gfa = np.flipud(gfa)
    bldg_count = np.flipud(bldg_count)
    svf = np.flipud(svf)

    # 检查形状对齐
    lcz_arr = lcz_da.values
    log.info(f"  LCZ shape: {lcz_arr.shape}, UMP shape: {bsf.shape}")

    # 处理可能的尺寸不匹配（边界条件）
    target_shape = lcz_arr.shape
    def fit(arr, target):
        # 裁切或填充到目标形状
        out = np.zeros(target, dtype=arr.dtype)
        h = min(arr.shape[0], target[0])
        w = min(arr.shape[1], target[1])
        out[:h, :w] = arr[:h, :w]
        return out

    bsf = fit(bsf, target_shape)
    mbh = fit(mbh, target_shape)
    sbh = fit(sbh, target_shape)
    mbw = fit(mbw, target_shape)
    bv = fit(bv, target_shape)
    gfa = fit(gfa, target_shape)
    bldg_count = fit(bldg_count, target_shape)
    svf = fit(svf, target_shape)

    # 派生 PSF & WSF
    psf = compute_psf_from_lcz(lcz_arr, bsf)
    wsf = compute_wsf_from_lcz(lcz_arr)

    log.info(f"  PSF 平均: {np.nanmean(psf):.3f}")
    log.info(f"  WSF 比例: {np.nansum(wsf) / wsf.size * 100:.1f}%")

    # === 5. 简化 Mean Street Width (MSW)
    # 简化估算: MSW 与 BSF 反相关；BSF 高 -> 街道窄
    msw = 30.0 - 25.0 * bsf  # BSF=0 -> 30m, BSF=1 -> 5m
    msw = np.clip(msw, 5, 60).astype(np.float32)

    # === 6. 保存为 NetCDF ===
    log.info("\n[5] 保存 UMPs NetCDF")

    # 使用 LCZ 网格的坐标
    out_ds = xr.Dataset(
        {
            'lcz':       (('y', 'x'), lcz_arr.astype(np.float32)),
            'bsf':       (('y', 'x'), bsf),
            'mbh':       (('y', 'x'), mbh),
            'sbh':       (('y', 'x'), sbh),
            'mbw':       (('y', 'x'), mbw),
            'bv':        (('y', 'x'), bv),
            'gfa':       (('y', 'x'), gfa),
            'svf':       (('y', 'x'), svf),
            'psf':       (('y', 'x'), psf),
            'wsf':       (('y', 'x'), wsf),
            'msw':       (('y', 'x'), msw),
            'bldg_count':(('y', 'x'), bldg_count.astype(np.int32)),
        },
        coords={
            'y': lcz_da.y.values,
            'x': lcz_da.x.values,
        }
    )

    # 写 CRS metadata
    out_ds.attrs['crs'] = 'EPSG:32650'
    out_ds.attrs['resolution_m'] = int(res)
    out_ds.attrs['source'] = 'OpenStreetMap buildings + Demuzere LCZ'

    out_path = PROCESSED_DATA_DIR / "shenzhen_umps_100m.nc"
    out_ds.to_netcdf(out_path)
    log.info(f"  已保存: {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")

    # === 7. 统计概览 ===
    log.info("\n[6] UMPs 统计概览（按 LCZ 类型）")

    LCZ_NAMES = {
        1: "Compact high-rise", 2: "Compact mid-rise", 3: "Compact low-rise",
        4: "Open high-rise", 5: "Open mid-rise", 6: "Open low-rise",
        7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built",
        10: "Heavy industry"
    }

    log.info(f"\n  {'LCZ':<5} {'类型':<24} {'BSF':>6} {'MBH':>6} {'SVF':>6} {'PSF':>6} {'BV/cell':>10}")
    log.info("  " + "-" * 70)
    for lcz_id in range(1, 11):
        mask = (lcz_arr == lcz_id)
        n = mask.sum()
        if n > 0:
            bsf_mean = bsf[mask].mean()
            mbh_mean = mbh[mask][mbh[mask] > 0].mean() if (mbh[mask] > 0).any() else 0
            svf_mean = svf[mask].mean()
            psf_mean = psf[mask].mean()
            bv_mean = bv[mask].mean()
            log.info(f"  {lcz_id:<5} {LCZ_NAMES[lcz_id][:22]:<24} "
                     f"{bsf_mean:>6.3f} {mbh_mean:>6.1f} {svf_mean:>6.3f} {psf_mean:>6.3f} "
                     f"{bv_mean:>10.0f}")

    log.info("\n🎉 UMPs 计算完成！")
    log.info("\n下一步: python scripts/lcz_subcategories.py")
    return True


if __name__ == "__main__":
    main()
