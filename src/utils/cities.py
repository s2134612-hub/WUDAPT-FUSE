"""
GBA 城市配置 — 跨城市对比测试

每个城市定义:
  - 地理边界（bbox）
  - LCZ 基础温度（季节性）
  - 期望机制特征（用于 narrative）
"""

CITIES = {
    'shenzhen': {
        'name': 'Shenzhen',
        'name_cn': '深圳',
        'bbox': {
            'north': 22.90, 'south': 22.40,
            'east': 114.70, 'west': 113.70
        },
        'population_2020': 17_560_000,
        'description': '海湾+北山，强地理梯度',
        'expected_dominant': 'Mountain',  # 预期主导机制
    },
    'guangzhou': {
        'name': 'Guangzhou',
        'name_cn': '广州',
        'bbox': {
            'north': 23.95, 'south': 22.55,
            'east': 114.05, 'west': 112.95
        },
        'population_2020': 18_810_000,
        'description': '内陆+少海岸+多山区（白云山、流溪河），更强山地效应',
        'expected_dominant': 'Mountain',  # 预期山区效应更强
    },
    'dongguan': {
        'name': 'Dongguan',
        'name_cn': '东莞',
        'bbox': {
            'north': 23.20, 'south': 22.65,
            'east': 114.25, 'west': 113.45
        },
        'population_2020': 10_466_000,
        'description': '工业平原城市，少山+较远海岸，预测两机制都减弱',
        'expected_dominant': 'Coast',
    },
    'foshan': {
        'name': 'Foshan',
        'name_cn': '佛山',
        'bbox': {
            'north': 23.60, 'south': 22.85,
            'east': 113.40, 'west': 112.50
        },
        'population_2020': 9_490_000,
        'description': '内陆河网城市，淡水体效应可能替代海岸效应',
        'expected_dominant': 'Coast',  # 用河网代理"水体"
    },
}


def get_city(name):
    """获取城市配置"""
    name = name.lower()
    if name not in CITIES:
        raise ValueError(f"未知城市: {name}. 可选: {list(CITIES.keys())}")
    return CITIES[name]


def list_cities():
    """列出所有城市"""
    return list(CITIES.keys())


if __name__ == "__main__":
    print("=" * 60)
    print("GBA 跨城市配置")
    print("=" * 60)
    for key, cfg in CITIES.items():
        print(f"\n{cfg['name']} ({cfg['name_cn']})")
        print(f"  人口: {cfg['population_2020']/1e6:.1f} M")
        print(f"  边界: lat {cfg['bbox']['south']}-{cfg['bbox']['north']}, "
              f"lon {cfg['bbox']['west']}-{cfg['bbox']['east']}")
        print(f"  描述: {cfg['description']}")
        print(f"  预期主导: {cfg['expected_dominant']}")
