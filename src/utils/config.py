"""项目全局配置。"""
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# 结果与图表
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"

# 配置目录
CONFIGS_DIR = PROJECT_ROOT / "configs"

# 研究区域: 深圳
SHENZHEN_BBOX = {
    "north": 22.90,
    "south": 22.40,
    "east": 114.70,
    "west": 113.70,
    "epsg": "EPSG:4326",      # 输入坐标系
    "epsg_proj": "EPSG:32650"  # 投影坐标系（UTM 50N）
}

# 时间范围
STUDY_PERIOD = {
    "start": "2020-01-01",
    "end": "2020-12-31",
    "freq": "1H"  # 1 小时
}

# 目标分辨率
TARGET_RESOLUTION_M = 100

# LCZ 类型
LCZ_TYPES = list(range(1, 11))  # 1-10 (建成 LCZ)
LCZ_NAMES = {
    1: "Compact high-rise",
    2: "Compact mid-rise",
    3: "Compact low-rise",
    4: "Open high-rise",
    5: "Open mid-rise",
    6: "Open low-rise",
    7: "Lightweight low-rise",
    8: "Large low-rise",
    9: "Sparsely built",
    10: "Heavy industry",
}

# 10 个 UMPs
UMP_NAMES = [
    "BSF",  # Building Surface Fraction
    "MBH",  # Mean Building Height
    "SBH",  # Standard Deviation of Building Height
    "MBW",  # Mean Building Width
    "BV",   # Building Volume
    "GFA",  # Gross Floor Area
    "MSW",  # Mean Street Width
    "SVF",  # Sky View Factor
    "PSF",  # Pervious Surface Fraction
    "WSF",  # Water Surface Fraction
]

# 116 个 MMS 站点（占位，实际加载时需 CSV）
MMS_STATIONS_FILE = RAW_DATA_DIR / "stations" / "shenzhen_116_stations.csv"


def ensure_dirs():
    """确保所有目录存在。"""
    for d in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR,
              RESULTS_DIR, FIGURES_DIR, CONFIGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Data dir:     {DATA_DIR}")
    print(f"Shenzhen bbox: {SHENZHEN_BBOX}")
