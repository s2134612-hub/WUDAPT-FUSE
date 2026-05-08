"""
下载 4 季节代表月份的 ERA5-HEAT
  - Jan 2020 (winter, 无海陆风, 弱热)
  - Apr 2020 (spring, 过渡)
  - Jul 2020 (summer, 已有)
  - Oct 2020 (autumn, 过渡)

总共下载 3 个月（July 已有）
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import SHENZHEN_BBOX, RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("download_seasons")


def download_era5_month(year, month, output_path):
    import cdsapi
    if output_path.exists():
        log.info(f"  已存在: {output_path.name}")
        return True

    days = [f'{d:02d}' for d in range(1, 32)]
    log.info(f"\n  下载 {year}-{month}...")
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
        size_mb = output_path.stat().st_size / 1e6
        log.info(f"  ✓ 下载完成: {output_path.name} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        log.error(f"  下载失败: {e}")
        return False


def main():
    ensure_dirs()
    log.info("=" * 60)
    log.info("ERA5-HEAT 多季节下载（Jan, Apr, Oct 2020）")
    log.info("=" * 60)

    out_dir = RAW_DATA_DIR / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)

    months_to_download = ['01', '04', '10']
    for month in months_to_download:
        out_path = out_dir / f"era5_heat_shenzhen_2020_{month}.nc"
        download_era5_month(2020, month, out_path)

    log.info("\n所有季节下载完成")


if __name__ == "__main__":
    main()
