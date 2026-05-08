"""
ERA5 全月下载完成后的全流程自动化:
  1. 解压全月 ZIP
  2. 处理 UTCI 100m (向量化版)
  3. 重新跑不平等分析
  4. 与 1 周版本对比

运行: python scripts/full_pipeline_july.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import zipfile
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.config import RAW_DATA_DIR
from src.utils.logging import get_logger

log = get_logger("full_pipeline")
SCRIPT_DIR = Path(__file__).parent
PYTHON = sys.executable


def step_extract_zip():
    """解压所有 ERA5 ZIP 到 extracted/"""
    log.info("\n" + "=" * 60)
    log.info("[Step 1] 解压全月 ERA5 ZIP")
    log.info("=" * 60)

    era5_dir = RAW_DATA_DIR / "era5"
    extracted = era5_dir / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)

    zip_files = list(era5_dir.glob("*.nc.zip")) + list(era5_dir.glob("*.zip"))
    log.info(f"  找到 {len(zip_files)} 个 ZIP 文件")

    nc_count_before = len(list(extracted.glob("*.nc")))
    log.info(f"  解压前 .nc 文件数: {nc_count_before}")

    for z in zip_files:
        log.info(f"  解压: {z.name}")
        with zipfile.ZipFile(z, 'r') as zf:
            zf.extractall(extracted)

    nc_count_after = len(list(extracted.glob("*.nc")))
    log.info(f"  解压后 .nc 文件数: {nc_count_after}")
    log.info(f"  新增文件: {nc_count_after - nc_count_before}")

    return nc_count_after


def step_process_utci():
    """运行 process_utci_to_grid.py"""
    log.info("\n" + "=" * 60)
    log.info("[Step 2] 处理 UTCI 100m (向量化版)")
    log.info("=" * 60)

    cmd = [PYTHON, str(SCRIPT_DIR / "process_utci_to_grid.py")]
    log.info(f"  运行: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        log.error(f"失败:\n{result.stderr[-500:]}")
        return False

    # 输出最后几行
    last_lines = result.stdout.strip().split('\n')[-10:]
    for line in last_lines:
        log.info(f"  {line}")
    return True


def step_inequality():
    """运行 utci_inequality.py"""
    log.info("\n" + "=" * 60)
    log.info("[Step 3] 不平等分析（全月版）")
    log.info("=" * 60)

    cmd = [PYTHON, str(SCRIPT_DIR / "utci_inequality.py")]
    log.info(f"  运行: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        log.error(f"失败:\n{result.stderr[-500:]}")
        return False

    last_lines = result.stdout.strip().split('\n')[-15:]
    for line in last_lines:
        log.info(f"  {line}")
    return True


def main():
    log.info("=" * 65)
    log.info("ERA5 7月全月 → 处理 → 分析 全流程")
    log.info("=" * 65)

    # Step 1: 解压
    nc_count = step_extract_zip()
    if nc_count < 30:
        log.warning(f"⚠ 仅 {nc_count} 个 .nc 文件，可能未下载完整全月")

    # Step 2: 处理
    if not step_process_utci():
        log.error("处理失败，退出")
        return

    # Step 3: 不平等分析
    if not step_inequality():
        log.error("分析失败，退出")
        return

    log.info("\n" + "=" * 65)
    log.info("🎉 全月分析完成！")
    log.info("=" * 65)
    log.info("\n关键产出:")
    log.info("  data/processed/shenzhen_utci_100m_jul_summary.nc  (全月)")
    log.info("  results/utci/utci_lcz_summary.csv")
    log.info("  results/utci/utci_gini_decomposition.csv")
    log.info("  figures/fig03_utci_inequality.png")


if __name__ == "__main__":
    main()
