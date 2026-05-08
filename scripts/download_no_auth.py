"""
下载无需注册账号的数据：
  1. Demuzere LCZ 地图（深圳裁剪）
  2. WorldPop 人口栅格
  3. SRTM DEM（备用 OpenTopography）

运行: python scripts/download_no_auth.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from src.utils.config import SHENZHEN_BBOX, RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("download_no_auth")


def download_with_progress(url, output_path, label="file"):
    """带进度条的下载"""
    log.info(f"  下载 {label}: {url}")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=900) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            last_pct = -1

            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=2 * 1024 * 1024):  # 2 MB
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = int(100 * downloaded / total)
                        if pct >= last_pct + 5:
                            log.info(f"    {pct}% ({downloaded/1e6:.1f}/{total/1e6:.1f} MB)")
                            last_pct = pct
        log.info(f"  完成: {output_path} ({output_path.stat().st_size/1e6:.1f} MB)")
        return True
    except Exception as e:
        log.error(f"  失败: {e}")
        if output_path.exists():
            output_path.unlink()
        return False


def download_lcz_map():
    """下载 Demuzere 全球 LCZ 地图，并裁剪到深圳"""
    log.info("=" * 60)
    log.info("[1/2] LCZ 地图（Demuzere et al. 2022 全球版）")
    log.info("=" * 60)

    global_path = RAW_DATA_DIR / "lcz" / "lcz_filter_v3.tif"
    sz_path = RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif"

    if sz_path.exists():
        log.info(f"  深圳 LCZ 已存在: {sz_path}")
        return True

    # 下载全球 LCZ - 多个备用 URL（Zenodo 偶尔不稳定）
    urls = [
        "https://zenodo.org/records/6364594/files/lcz_filter_v3.tif",
        "https://zenodo.org/records/8419340/files/lcz_filter_v3.tif",
        "https://zenodo.org/record/6364594/files/lcz_filter_v3.tif",
    ]

    if not global_path.exists():
        ok = False
        for url in urls:
            log.info(f"  尝试 URL: {url}")
            ok = download_with_progress(url, global_path, label="全球 LCZ (~380 MB)")
            if ok:
                break
            else:
                log.info(f"  此 URL 失败，尝试下一个...")
        if not ok:
            log.warning("  全部 Zenodo URL 失败。建议手动下载或稍后重试。")
            log.warning("  手动下载: https://zenodo.org/records/6364594")
            return False
    else:
        log.info(f"  全球 LCZ 已存在: {global_path}")

    # 裁剪深圳
    log.info("  裁剪到深圳...")
    try:
        import rioxarray as rxr
        lcz = rxr.open_rasterio(global_path, masked=True)

        sz_lcz = lcz.rio.clip_box(
            minx=SHENZHEN_BBOX['west'],
            miny=SHENZHEN_BBOX['south'],
            maxx=SHENZHEN_BBOX['east'],
            maxy=SHENZHEN_BBOX['north']
        )
        sz_lcz.rio.to_raster(sz_path)

        # 显示统计
        import numpy as np
        vals = sz_lcz.values.flatten()
        vals = vals[~np.isnan(vals)]
        unique, counts = np.unique(vals.astype(int), return_counts=True)
        log.info(f"  深圳 LCZ 完成: {sz_path}")
        log.info(f"  栅格大小: {sz_lcz.shape}")
        log.info(f"  LCZ 类型分布:")
        for u, c in zip(unique, counts):
            pct = 100 * c / vals.size
            log.info(f"    LCZ {int(u):2d}: {c:>7d} 栅格 ({pct:.1f}%)")
        return True
    except Exception as e:
        log.error(f"  裁剪失败: {e}")
        return False


def download_worldpop():
    """下载 WorldPop 100m 人口数据（中国子集）"""
    log.info("\n" + "=" * 60)
    log.info("[2/2] WorldPop 人口（2020 中国 100m）")
    log.info("=" * 60)

    full_path = RAW_DATA_DIR / "worldpop" / "chn_ppp_2020.tif"
    sz_path = RAW_DATA_DIR / "worldpop" / "worldpop_shenzhen_100m.tif"

    if sz_path.exists():
        log.info(f"  深圳 WorldPop 已存在: {sz_path}")
        return True

    if not full_path.exists():
        # WorldPop 100m 中国全国数据较大（~2 GB），改用约束版（受约束像素）
        url = "https://data.worldpop.org/GIS/Population/Global_2000_2020_Constrained/2020/BSGM/CHN/chn_ppp_2020_constrained.tif"

        log.info(f"  尝试下载约束版（~700 MB），可能需 20-40 分钟")
        ok = download_with_progress(url, full_path, label="WorldPop CHN")
        if not ok:
            log.warning("  WorldPop 下载失败（可能因网络/防火墙），可稍后再试")
            return False

    # 裁剪深圳
    log.info("  裁剪深圳...")
    try:
        import rioxarray as rxr
        pop = rxr.open_rasterio(full_path, masked=True)
        sz_pop = pop.rio.clip_box(
            minx=SHENZHEN_BBOX['west'],
            miny=SHENZHEN_BBOX['south'],
            maxx=SHENZHEN_BBOX['east'],
            maxy=SHENZHEN_BBOX['north']
        )
        sz_pop.rio.to_raster(sz_path)

        import numpy as np
        total_pop = float(np.nansum(sz_pop.values))
        log.info(f"  深圳 WorldPop 完成: {sz_path}")
        log.info(f"  栅格大小: {sz_pop.shape}")
        log.info(f"  总人口（栅格求和）: {total_pop:,.0f} 人")
        return True
    except Exception as e:
        log.error(f"  裁剪失败: {e}")
        return False


def main():
    ensure_dirs()
    log.info("\nWUDAPT-FUSE 无需注册数据下载\n")

    results = {
        'LCZ map':   download_lcz_map(),
        'WorldPop':  download_worldpop(),
    }

    log.info("\n" + "=" * 60)
    log.info("下载汇总:")
    for name, ok in results.items():
        log.info(f"  {'✓' if ok else '✗'} {name}")

    n_ok = sum(results.values())
    log.info(f"\n成功: {n_ok}/{len(results)}")

    if n_ok == len(results):
        log.info("\n🎉 所有无需注册的数据下载完成！")
        log.info("\n下一步: 注册 ECMWF CDS 后下载 ERA5-HEAT")
    else:
        log.info("\n部分失败，可手动重试或继续推进其他数据")


if __name__ == "__main__":
    main()
