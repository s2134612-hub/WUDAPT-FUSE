"""统一日志配置。"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def get_logger(name: str = "wudapt", level: str = "INFO",
               log_file: Path = None) -> logging.Logger:
    """创建格式化的 logger。"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # Console handler
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


if __name__ == "__main__":
    log = get_logger("test")
    log.info("Logger initialized")
    log.warning("Test warning")
