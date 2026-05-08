"""
批量下载 3 个城市 (Guangzhou, Dongguan, Foshan) 的 ERA5-HEAT 4 月数据。

每个城市 4 个月（Jan, Apr, Jul, Oct 2020），共 12 个文件。
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.utils.cities import CITIES

log = get_logger("multicity_download")

CITIES_TO_DOWNLOAD = ['guangzhou', 'dongguan', 'foshan']
MONTHS = ['01', '04', '07', '10']


def download_era5(city_key, year, month, output_path):
    import cdsapi
    if output_path.exists():
        log.info(f"  ✓ {output_path.name} 已存在")
        return True

    cfg = CITIES[city_key]
    bbox = cfg['bbox']
    days = [f'{d:02d}' for d in range(1, 32)]

    log.info(f"  下载 {cfg['name']} {year}-{month}...")
    try:
        c = cdsapi.Client()
        c.retrieve(
            'derived-utci-historical',
            {
                'variable': ['universal_thermal_climate_index'],
                'product_type': 'consolidated_dataset',
                'version': '1_1',
                'year': [str(year)],
                'month': [month],
                'day': days,
                'area': [bbox['north'], bbox['west'],
                         bbox['south'], bbox['east']],
                'format': 'netcdf'
            },
            str(output_path)
        )
        size_mb = output_path.stat().st_size / 1e6
        log.info(f"  ✓ {output_path.name} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        log.error(f"  下载失败: {e}")
        return False


def main():
    ensure_dirs()
    log.info("=" * 65)
    log.info(f"GBA 多城市 ERA5 下载 — {len(CITIES_TO_DOWNLOAD)} 城 × {len(MONTHS)} 月 = "
             f"{len(CITIES_TO_DOWNLOAD)*len(MONTHS)} 文件")
    log.info("=" * 65)

    base_dir = RAW_DATA_DIR / "era5"
    base_dir.mkdir(parents=True, exist_ok=True)

    total = len(CITIES_TO_DOWNLOAD) * len(MONTHS)
    success = 0

    for city in CITIES_TO_DOWNLOAD:
        log.info(f"\n--- {city.upper()} ---")
        for month in MONTHS:
            out_path = base_dir / f"era5_heat_{city}_2020_{month}.nc"
            ok = download_era5(city, 2020, month, out_path)
            if ok:
                success += 1

    log.info(f"\n下载汇总: {success}/{total} 成功")


if __name__ == "__main__":
    main()
