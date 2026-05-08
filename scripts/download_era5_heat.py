"""
下载 ERA5-HEAT UTCI 数据。

提供两种下载策略：
  --week:    仅下载 2020-07-15 至 2020-07-21（一周，约 50 MB）— 快速验证
  --month:   下载 2020-07 全月（约 200 MB）— 适合演示
  --season:  下载 2020-07,08（夏季 2 个月，约 400 MB）— 论文用
  --year:    下载 2020 全年（约 2.5 GB）— 完整版

运行:
    python scripts/download_era5_heat.py --week
    python scripts/download_era5_heat.py --month
    python scripts/download_era5_heat.py --year
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import SHENZHEN_BBOX, RAW_DATA_DIR, ensure_dirs
from src.utils.logging import get_logger

log = get_logger("download_era5_heat")


def download_era5_heat(year, months, days, label, output_path):
    """
    下载 ERA5-HEAT UTCI 数据

    Args:
        year: 年份字符串，如 '2020'
        months: 月份列表，如 ['07']
        days: 日期列表，如 ['01','02',...]
        label: 任务标签
        output_path: 输出文件路径
    """
    import cdsapi

    log.info(f"  下载 {label}")
    log.info(f"  年份: {year}, 月份: {months}, 日期数: {len(days)}")

    if output_path.exists():
        size_mb = output_path.stat().st_size / 1e6
        log.info(f"  ✓ 文件已存在 ({size_mb:.1f} MB): {output_path}")
        return True

    try:
        c = cdsapi.Client()
        c.retrieve(
            'derived-utci-historical',
            {
                'variable': ['universal_thermal_climate_index'],
                'product_type': 'consolidated_dataset',
                'version': '1_1',
                'year': [year],
                'month': months,
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
        log.info(f"  ✓ 下载完成: {output_path} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        log.error(f"  下载失败: {e}")
        return False


def parse_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--week', action='store_true',
                       help='2020-07-15 至 2020-07-21（一周，~50 MB）')
    group.add_argument('--month', action='store_true',
                       help='2020-07 全月（~200 MB）')
    group.add_argument('--season', action='store_true',
                       help='2020-07/08（夏季 2 月，~400 MB）')
    group.add_argument('--year', action='store_true',
                       help='2020 全年（~2.5 GB）')
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dirs()

    out_dir = RAW_DATA_DIR / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info("ERA5-HEAT UTCI 下载（深圳区域）")
    log.info("=" * 60)

    if args.week:
        # 测试用：1 周
        days = [f'{d:02d}' for d in range(15, 22)]
        path = out_dir / "era5_heat_shenzhen_2020_07_15_21.nc"
        ok = download_era5_heat('2020', ['07'], days, "一周（2020-07-15~21）", path)

    elif args.month:
        # 演示用：1 月
        days = [f'{d:02d}' for d in range(1, 32)]
        path = out_dir / "era5_heat_shenzhen_2020_07.nc"
        ok = download_era5_heat('2020', ['07'], days, "1 月（2020-07）", path)

    elif args.season:
        # 主分析：夏季 2 月
        days = [f'{d:02d}' for d in range(1, 32)]
        path = out_dir / "era5_heat_shenzhen_2020_summer.nc"
        ok = download_era5_heat('2020', ['07', '08'], days, "夏季 2 月", path)

    elif args.year:
        # 完整：全年（拆分多次下载，每次 1 月）
        ok = True
        for month in [f'{m:02d}' for m in range(1, 13)]:
            days = [f'{d:02d}' for d in range(1, 32)]
            path = out_dir / f"era5_heat_shenzhen_2020_{month}.nc"
            log.info(f"\n--- 月份 {month}/12 ---")
            success = download_era5_heat('2020', [month], days, f"2020-{month}", path)
            ok = ok and success

    if ok:
        log.info("\n🎉 ERA5-HEAT 下载完成")
        log.info("\n查看数据:")
        log.info("  python -c \"import xarray as xr; ds=xr.open_dataset('your_file.nc'); print(ds)\"")
    else:
        log.info("\n部分失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
