"""
下载第一批样本数据：深圳 2020 年 7 月 1 周的核心数据。

运行: python scripts/download_sample.py
"""
import sys
from pathlib import Path

# 确保可以 import src
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import (
    SHENZHEN_BBOX, RAW_DATA_DIR, ensure_dirs
)
from src.utils.logging import get_logger

log = get_logger("download_sample", log_file=RAW_DATA_DIR.parent / "logs" / "download.log")


def download_era5_heat_sample():
    """下载深圳 2020-07 一周的 ERA5-HEAT UTCI"""
    log.info("=== 1/4 下载 ERA5-HEAT UTCI 样本 ===")

    try:
        import cdsapi
    except ImportError:
        log.error("cdsapi 未安装。先运行: conda activate wudapt")
        return False

    output_path = RAW_DATA_DIR / "era5" / "era5_heat_shenzhen_2020_07_01_07.nc"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        log.info(f"  文件已存在: {output_path}")
        return True

    try:
        c = cdsapi.Client()
        c.retrieve(
            'derived-utci-historical',
            {
                'variable': ['universal_thermal_climate_index'],
                'product_type': 'consolidated_dataset',
                'version': '1_1',
                'year': '2020',
                'month': '07',
                'day': [f'{d:02d}' for d in range(1, 8)],
                'area': [
                    SHENZHEN_BBOX['north'],
                    SHENZHEN_BBOX['west'],
                    SHENZHEN_BBOX['south'],
                    SHENZHEN_BBOX['east']
                ],
                'format': 'netcdf'
            },
            str(output_path)
        )
        log.info(f"  下载完成: {output_path}")
        log.info(f"  文件大小: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        return True
    except Exception as e:
        log.error(f"  下载失败: {e}")
        log.warning("  请确认已配置 ~/.cdsapirc")
        log.warning("  注册地址: https://cds.climate.copernicus.eu/")
        return False


def download_lcz_map():
    """下载 Demuzere 全球 LCZ 地图，并裁剪深圳"""
    log.info("=== 2/4 下载 LCZ 地图 ===")

    try:
        import requests
        import rioxarray
    except ImportError as e:
        log.error(f"依赖缺失: {e}")
        return False

    global_path = RAW_DATA_DIR / "lcz" / "lcz_filter_v3.tif"
    shenzhen_path = RAW_DATA_DIR / "lcz" / "lcz_shenzhen_100m.tif"
    global_path.parent.mkdir(parents=True, exist_ok=True)

    if shenzhen_path.exists():
        log.info(f"  深圳 LCZ 已存在: {shenzhen_path}")
        return True

    if not global_path.exists():
        url = "https://zenodo.org/records/8214467/files/lcz_filter_v3.tif"
        log.info(f"  下载全球 LCZ（约 380 MB）: {url}")
        try:
            r = requests.get(url, stream=True, timeout=300)
            r.raise_for_status()
            with open(global_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
            log.info(f"  全球 LCZ 下载完成")
        except Exception as e:
            log.error(f"  下载失败: {e}")
            return False

    # 裁剪
    log.info("  裁剪到深圳范围...")
    try:
        lcz = rioxarray.open_rasterio(global_path)
        sz_lcz = lcz.rio.clip_box(
            minx=SHENZHEN_BBOX['west'],
            miny=SHENZHEN_BBOX['south'],
            maxx=SHENZHEN_BBOX['east'],
            maxy=SHENZHEN_BBOX['north']
        )
        sz_lcz.rio.to_raster(shenzhen_path)
        log.info(f"  深圳 LCZ 裁剪完成: {shenzhen_path}")
        return True
    except Exception as e:
        log.error(f"  裁剪失败: {e}")
        return False


def download_dem():
    """下载 SRTM DEM"""
    log.info("=== 3/4 下载 SRTM DEM ===")

    try:
        import ee
    except ImportError:
        log.error("earthengine-api 未安装")
        return False

    output_path = RAW_DATA_DIR / "dem" / "srtm_shenzhen_30m.tif"
    if output_path.exists():
        log.info(f"  已存在: {output_path}")
        return True

    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.warning("  Google Earth Engine 需要先认证: earthengine authenticate")
    log.warning("  本步骤暂时跳过，可手动下载或下次运行")
    return False


def download_worldpop():
    """下载 WorldPop 100m 人口数据（应用层）"""
    log.info("=== 4/4 下载 WorldPop 人口（应用层）===")

    try:
        import requests
    except ImportError:
        log.error("requests 未安装")
        return False

    output_path = RAW_DATA_DIR / "worldpop" / "chn_ppp_2020.tif"
    if output_path.exists():
        log.info(f"  已存在: {output_path}")
        return True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    url = "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/CHN/chn_ppp_2020.tif"

    log.info(f"  下载 WorldPop 中国人口（约 700 MB，可能需要 30 分钟）")
    log.info(f"  URL: {url}")

    try:
        r = requests.get(url, stream=True, timeout=1800)
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = 100 * downloaded / total
                    if int(pct) % 10 == 0:
                        log.info(f"    {pct:.0f}% ({downloaded/1e6:.0f} MB)")

        log.info(f"  下载完成: {output_path}")
        return True
    except Exception as e:
        log.error(f"  下载失败: {e}")
        return False


def main():
    ensure_dirs()
    log.info("\n" + "=" * 60)
    log.info("WUDAPT-FUSE 样本数据下载开始")
    log.info("=" * 60)

    results = {
        'ERA5-HEAT': download_era5_heat_sample(),
        'LCZ map':   download_lcz_map(),
        'SRTM DEM':  download_dem(),
        'WorldPop':  download_worldpop(),
    }

    log.info("\n" + "=" * 60)
    log.info("下载汇总:")
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        log.info(f"  {status} {name}")

    n_ok = sum(results.values())
    log.info(f"\n成功: {n_ok}/{len(results)}")

    if n_ok == len(results):
        log.info("🎉 所有样本数据就绪，可以开始 Phase 1 主任务")
    elif n_ok >= 2:
        log.info("⚠ 部分数据缺失，可继续推进核心步骤")
    else:
        log.info("❌ 多数下载失败，请检查网络与账号配置")


if __name__ == "__main__":
    main()
