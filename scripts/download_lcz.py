"""
专门下载 LCZ 地图（独立脚本，便于多次重试）。

运行: python scripts/download_lcz.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from src.utils.config import SHENZHEN_BBOX, RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("download_lcz")

# 正确的文件名（已通过 Zenodo API 验证）
URLS = [
    # 推荐：filter 版本（1.4 GB，已应用形态学滤波）
    "https://zenodo.org/api/records/6364594/files/lcz_filter_v1.tif/content",
    # 备选：原始版本（1.8 GB）
    "https://zenodo.org/api/records/6364594/files/lcz_v1.tif/content",
]


def try_download(url, output_path, max_attempts=3, timeout=900):
    """带重试的下载"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for attempt in range(1, max_attempts + 1):
        log.info(f"  尝试 {attempt}/{max_attempts}: {url}")
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                downloaded = 0
                last_pct = -1

                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=2 * 1024 * 1024):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = int(100 * downloaded / total)
                            if pct >= last_pct + 10:
                                log.info(f"    {pct}%  ({downloaded/1e6:.0f}/{total/1e6:.0f} MB)")
                                last_pct = pct

            log.info(f"  ✓ 下载完成: {output_path} ({output_path.stat().st_size/1e6:.1f} MB)")
            return True

        except Exception as e:
            log.warning(f"  尝试 {attempt} 失败: {e}")
            if output_path.exists():
                output_path.unlink()
            if attempt < max_attempts:
                wait = 30 * attempt
                log.info(f"  等待 {wait} 秒后重试...")
                time.sleep(wait)

    return False


def crop_to_shenzhen(global_path, sz_path):
    log.info(f"  裁剪到深圳...")
    try:
        import rioxarray as rxr
        import numpy as np

        lcz = rxr.open_rasterio(global_path, masked=True)
        sz_lcz = lcz.rio.clip_box(
            minx=SHENZHEN_BBOX['west'],
            miny=SHENZHEN_BBOX['south'],
            maxx=SHENZHEN_BBOX['east'],
            maxy=SHENZHEN_BBOX['north']
        )
        sz_lcz.rio.to_raster(sz_path)

        vals = sz_lcz.values.flatten()
        vals = vals[~np.isnan(vals)]
        unique, counts = np.unique(vals.astype(int), return_counts=True)

        log.info(f"  ✓ 深圳 LCZ 完成: {sz_path}")
        log.info(f"  栅格大小: {sz_lcz.shape}")
        log.info(f"\n  LCZ 类型分布:")
        for u, c in zip(unique, counts):
            pct = 100 * c / vals.size
            log.info(f"    LCZ {int(u):2d}: {c:>7d} 栅格 ({pct:.1f}%)")
        return True
    except Exception as e:
        log.error(f"  裁剪失败: {e}")
        return False


def main():
    ensure_dirs()
    global_path = RAW_DATA_DIR / "lcz" / "lcz_filter_v1.tif"
    sz_path = RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif"

    log.info("=" * 60)
    log.info("Demuzere LCZ 全球地图下载（v3, 100m）")
    log.info("=" * 60)

    if sz_path.exists():
        log.info(f"\n✓ 深圳 LCZ 已存在: {sz_path}")
        log.info("  如需重新下载，先删除该文件")
        return

    # 下载全球图
    if not global_path.exists():
        ok = False
        for url in URLS:
            if try_download(url, global_path):
                ok = True
                break

        if not ok:
            log.error("\n全部 URL 失败。请手动下载:")
            log.error("  1. 访问 https://zenodo.org/records/6364594")
            log.error("  2. 下载 lcz_filter_v3.tif")
            log.error(f"  3. 放到 {global_path}")
            log.error("  4. 重新运行本脚本")
            sys.exit(1)
    else:
        log.info(f"全球 LCZ 已存在: {global_path}")

    # 裁剪
    crop_to_shenzhen(global_path, sz_path)

    log.info("\n🎉 LCZ 下载与裁剪完成！")


if __name__ == "__main__":
    main()
