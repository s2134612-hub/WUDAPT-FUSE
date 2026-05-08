"""下载 Dongguan 剩余的 2 个月（Jul, Oct）"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger
from src.utils.cities import CITIES

log = get_logger("dg_remaining")


def download(month):
    import cdsapi
    cfg = CITIES['dongguan']
    bbox = cfg['bbox']
    out_path = RAW_DATA_DIR / "era5" / f"era5_heat_dongguan_2020_{month}.nc"

    if out_path.exists():
        log.info(f"  ✓ {out_path.name} 已存在")
        return True

    log.info(f"  下载 Dongguan 2020-{month}...")
    days = [f'{d:02d}' for d in range(1, 32)]
    try:
        c = cdsapi.Client()
        c.retrieve('derived-utci-historical', {
            'variable': ['universal_thermal_climate_index'],
            'product_type': 'consolidated_dataset', 'version': '1_1',
            'year': ['2020'], 'month': [month], 'day': days,
            'area': [bbox['north'], bbox['west'], bbox['south'], bbox['east']],
            'format': 'netcdf'
        }, str(out_path))
        log.info(f"  ✓ {out_path.name} ({out_path.stat().st_size/1e6:.1f} MB)")
        return True
    except Exception as e:
        log.error(f"  失败: {e}")
        return False


def main():
    ensure_dirs()
    log.info("=" * 60)
    log.info("Dongguan 剩余下载（Jul + Oct）")
    log.info("=" * 60)

    for month in ['07', '10']:
        download(month)

    log.info("\n下载完成（DG）")


if __name__ == "__main__":
    main()
