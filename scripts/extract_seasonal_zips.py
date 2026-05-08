"""解压 ERA5 季节 zip 到对应月份子目录"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import zipfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAW_DATA_DIR
from src.utils.logging import get_logger

log = get_logger("extract_seasonal")


def main():
    era5_dir = RAW_DATA_DIR / "era5"
    months = ['01', '04', '07', '10']

    for month in months:
        nc_file = era5_dir / f"era5_heat_shenzhen_2020_{month}.nc"
        if not nc_file.exists():
            log.warning(f"  缺失: {nc_file.name}")
            continue

        # 检查是 ZIP
        with open(nc_file, 'rb') as f:
            magic = f.read(4)

        extract_dir = era5_dir / f"extracted_{month}"
        if magic == b'PK\x03\x04':
            extract_dir.mkdir(parents=True, exist_ok=True)
            existing = list(extract_dir.glob("ECMWF_utci_*.nc"))
            if len(existing) >= 28:  # 至少 28 天
                log.info(f"  {month}: 已解压 ({len(existing)} 文件)")
                continue
            log.info(f"  解压 {nc_file.name}...")
            with zipfile.ZipFile(nc_file, 'r') as zf:
                zf.extractall(extract_dir)
            new = list(extract_dir.glob("ECMWF_utci_*.nc"))
            log.info(f"  {month}: 解压完成 ({len(new)} 文件)")
        else:
            log.info(f"  {month}: 不是 ZIP，跳过")

    log.info("\n所有季节解压完成")


if __name__ == "__main__":
    main()
