"""
LCZ-based thermal burden (热负担) proxy.

直接采用文章一（Huang et al. 2026）Table 4 中深圳 7 月（湿季）的 LCZ-AT 均值，
作为 ERA5-HEAT UTCI 数据到位前的代理指标。

数据来源: Huang et al. 2026, SCS, Table 4
  "Average microclimate levels and the corresponding rankings of built-up
   LCZs based on XGBoost-enhanced datasets"

关于自然 LCZ (11-17) 的值：
  Paper 1 仅含建成 LCZ (1-10)。自然 LCZ 的值通过文献参考估算
  (Stewart & Oke 2012, Yang et al. 2019, Cai et al. 2018)
"""
import numpy as np


# 文章一 Table 4：Shenzhen 7 月（湿季）AT (K)
# 直接拷自 Huang et al. 2026 论文
PAPER1_AT_JUL_K = {
    1:  304.10,  # Compact high-rise
    2:  304.10,  # Compact mid-rise
    3:  304.07,  # Compact low-rise
    4:  304.07,  # Open high-rise (ranked LCZ 1 in Jul)
    5:  304.05,  # Open mid-rise
    6:  304.03,  # Open low-rise
    # LCZ 7 (Lightweight low-rise) - 文章一未列，深圳少见
    7:  304.00,  # 估算
    8:  303.94,  # Large low-rise
    9:  303.05,  # Sparsely built (最低)
    10: 303.91,  # Heavy industry
}

# 自然 LCZ 估算值 (基于文献，深圳湿季)
# Stewart & Oke 2012: 自然 LCZ 通常比城市 LCZ 低 0.5-2.0 K
NATURAL_AT_JUL_K = {
    11: 303.20,  # Dense trees - 林地，强蒸腾降温
    12: 303.40,  # Scattered trees
    13: 303.60,  # Bush, scrub
    14: 303.50,  # Low plants
    15: 304.20,  # Bare rock/paved (无植被增温)
    16: 304.00,  # Bare soil/sand
    17: 302.80,  # Water (水体最冷)
}

# 合并
LCZ_AT_JUL_K = {**PAPER1_AT_JUL_K, **NATURAL_AT_JUL_K}


def lcz_to_at(lcz_array, season='Jul'):
    """
    将 LCZ 类型栅格转换为气温场。

    Parameters
    ----------
    lcz_array : np.ndarray
        LCZ 类型栅格（1-17，可含 NaN）
    season : str
        季节标识，目前仅支持 'Jul'

    Returns
    -------
    at_array : np.ndarray
        与 lcz_array 同形状的气温场（K）
    """
    if season != 'Jul':
        raise NotImplementedError("仅支持 Jul（基于 Paper 1 Table 4）")

    out = np.full_like(lcz_array, np.nan, dtype=np.float32)

    for lcz_id, at_value in LCZ_AT_JUL_K.items():
        mask = (lcz_array == lcz_id)
        out[mask] = at_value

    return out


def compute_thermal_burden_index(at_array, baseline_K=302.0):
    """
    计算热负担指数（K above baseline）。

    Parameters
    ----------
    at_array : np.ndarray
        气温场（K）
    baseline_K : float
        基准温度（K），默认 302 K = 28.85°C，深圳 7 月最凉点

    Returns
    -------
    tbi : np.ndarray
        热负担指数（K）
    """
    return at_array - baseline_K


# 文献参考的 UHI 强度（用于敏感性分析）
# Stewart, Oke, Krayenhoff 2014 (IJOC)
LCZ_UHI_NIGHT_INTENSITY = {  # Average summer night UHI (K)
    1:  3.5,  2:  2.5,  3:  2.0,
    4:  1.5,  5:  1.5,  6:  1.0,
    7:  2.0,  8:  2.0,  9:  0.5,
    10: 2.5,
    11: 0.0,  12: 0.0,  13: 0.0,  14: 0.0,
    15: 1.0,  16: 0.5,  17: -0.5,
}


def lcz_thermal_metadata():
    """返回 LCZ 元数据 DataFrame。"""
    import pandas as pd

    LCZ_NAMES = {
        1: "Compact high-rise", 2: "Compact mid-rise", 3: "Compact low-rise",
        4: "Open high-rise", 5: "Open mid-rise", 6: "Open low-rise",
        7: "Lightweight low-rise", 8: "Large low-rise", 9: "Sparsely built",
        10: "Heavy industry", 11: "Dense trees", 12: "Scattered trees",
        13: "Bush, scrub", 14: "Low plants", 15: "Bare rock/paved",
        16: "Bare soil/sand", 17: "Water"
    }

    LCZ_TYPE = {
        **{i: "Built-up" for i in range(1, 11)},
        **{i: "Natural" for i in range(11, 18)},
    }

    rows = []
    for lcz in range(1, 18):
        rows.append({
            'lcz_id': lcz,
            'name': LCZ_NAMES[lcz],
            'type': LCZ_TYPE[lcz],
            'AT_jul_K': LCZ_AT_JUL_K[lcz],
            'AT_jul_C': LCZ_AT_JUL_K[lcz] - 273.15,
            'TBI_K': LCZ_AT_JUL_K[lcz] - 302.0,
            'UHI_night_K': LCZ_UHI_NIGHT_INTENSITY[lcz],
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = lcz_thermal_metadata()
    print("LCZ 热负担元数据:")
    print(df.to_string(index=False))

    print("\n按热负担排序 (Top 5):")
    print(df.nlargest(5, 'AT_jul_C')[['lcz_id', 'name', 'AT_jul_C', 'TBI_K']].to_string(index=False))

    print("\n按热负担排序 (Bottom 5):")
    print(df.nsmallest(5, 'AT_jul_C')[['lcz_id', 'name', 'AT_jul_C', 'TBI_K']].to_string(index=False))
