"""
Gini 系数与 Lorenz 曲线计算。

支持：
1. 标准 Gini
2. 人口加权 Gini (Mookherjee-Shorrocks 1982)
3. 三层分解 Gini (Pyatt-Yitzhaki)
"""
import numpy as np
import pandas as pd


def gini_simple(values):
    """标准 Gini 系数（无加权）。"""
    if len(values) == 0:
        return np.nan
    values = np.sort(np.asarray(values, dtype=np.float64))
    n = len(values)
    cumvals = np.cumsum(values)
    if cumvals[-1] == 0:
        return 0.0
    return (n + 1 - 2 * np.sum(cumvals) / cumvals[-1]) / n


def gini_weighted(values, weights):
    """
    人口（或任意正权重）加权 Gini。

    Parameters
    ----------
    values : np.ndarray
        每个样本的指标值（如热暴露）
    weights : np.ndarray
        每个样本的权重（如人口）

    Returns
    -------
    G : float
        Gini 系数（[0, 1]）
    """
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)

    # 过滤无效值
    mask = (~np.isnan(values)) & (~np.isnan(weights)) & (weights > 0)
    values = values[mask]
    weights = weights[mask]

    if len(values) == 0:
        return np.nan

    # 排序
    order = np.argsort(values)
    values = values[order]
    weights = weights[order]

    # 累积权重和加权值
    W = weights.sum()
    if W == 0:
        return np.nan

    cumw = np.cumsum(weights)
    cumxw = np.cumsum(values * weights)

    if cumxw[-1] == 0:
        return 0.0

    # Gini 公式（trapezoid）
    # 推导自 Lorenz 曲线下面积
    # G = 1 - 2 * 加权 Lorenz 积分
    p = cumw / W
    L = cumxw / cumxw[-1]

    # 用梯形法积分
    p_prev = np.concatenate([[0], p[:-1]])
    L_prev = np.concatenate([[0], L[:-1]])
    area = 0.5 * np.sum((p - p_prev) * (L + L_prev))

    return 1 - 2 * area


def lorenz_curve(values, weights=None, n_points=100):
    """
    计算 Lorenz 曲线点。

    Returns
    -------
    p : np.ndarray
        累积人口（或权重）份额 [0, 1]
    L : np.ndarray
        累积指标份额 [0, 1]
    """
    values = np.asarray(values, dtype=np.float64)
    if weights is None:
        weights = np.ones_like(values)
    weights = np.asarray(weights, dtype=np.float64)

    mask = (~np.isnan(values)) & (~np.isnan(weights)) & (weights > 0)
    values = values[mask]
    weights = weights[mask]

    order = np.argsort(values)
    values = values[order]
    weights = weights[order]

    cumw = np.cumsum(weights)
    cumxw = np.cumsum(values * weights)

    p = cumw / cumw[-1]
    L = cumxw / cumxw[-1]

    # 加入起点
    p = np.concatenate([[0], p])
    L = np.concatenate([[0], L])

    return p, L


def gini_decomposition(df, value_col, weight_col, group_col):
    """
    Pyatt-Yitzhaki 类型 Gini 分解：
        G_total = G_between + G_within + G_overlap

    Parameters
    ----------
    df : pd.DataFrame
        每行一个样本
    value_col : str
        指标值列名
    weight_col : str
        权重列名（如人口）
    group_col : str
        分组列名（如 LCZ 类型）

    Returns
    -------
    dict
        { 'G_total', 'G_between', 'G_within', 'G_overlap',
          'between_share', 'within_share', 'overlap_share',
          'group_stats' }
    """
    df = df[[value_col, weight_col, group_col]].dropna()
    df = df[df[weight_col] > 0]

    if len(df) == 0:
        return None

    # 总 Gini
    G_total = gini_weighted(df[value_col].values, df[weight_col].values)

    # 各组统计
    group_stats = []
    for grp, gdf in df.groupby(group_col):
        n = len(gdf)
        w_sum = gdf[weight_col].sum()
        v_mean = np.average(gdf[value_col], weights=gdf[weight_col])
        g_within = gini_weighted(gdf[value_col].values, gdf[weight_col].values)
        group_stats.append({
            group_col: grp,
            'n_samples': n,
            'weight_sum': w_sum,
            'weight_share': w_sum / df[weight_col].sum(),
            'value_mean': v_mean,
            'gini_within': g_within if not np.isnan(g_within) else 0,
        })
    gs = pd.DataFrame(group_stats)

    # 全局加权均值
    grand_mean = np.average(df[value_col], weights=df[weight_col])

    # G_between: 按各组均值计算 Gini（替换组内异质性为 0）
    G_between = gini_weighted(gs['value_mean'].values, gs['weight_sum'].values)

    # G_within: ∑ s_g · (μ_g / μ) · G_g  (假设非重叠时)
    # 当组间有重叠时（即组的值范围相互交叉），分解会出现 G_overlap
    G_within_pure = sum(
        row['weight_share'] * (row['value_mean'] / grand_mean) * row['gini_within']
        for _, row in gs.iterrows()
    )

    # G_overlap = G_total - G_between - G_within_pure
    G_overlap = G_total - G_between - G_within_pure

    return {
        'G_total': G_total,
        'G_between': G_between,
        'G_within': G_within_pure,
        'G_overlap': G_overlap,
        'between_share': G_between / G_total if G_total > 0 else 0,
        'within_share': G_within_pure / G_total if G_total > 0 else 0,
        'overlap_share': G_overlap / G_total if G_total > 0 else 0,
        'grand_mean': grand_mean,
        'group_stats': gs,
    }


def atkinson_index(values, weights=None, epsilon=1.0):
    """
    Atkinson 不平等指数（替代度量）。

    epsilon : float
        不平等厌恶参数（>0），越大越关注尾部
    """
    values = np.asarray(values, dtype=np.float64)
    if weights is None:
        weights = np.ones_like(values)
    weights = np.asarray(weights, dtype=np.float64)

    mask = (~np.isnan(values)) & (~np.isnan(weights)) & (weights > 0) & (values > 0)
    values = values[mask]
    weights = weights[mask]

    if len(values) == 0:
        return np.nan

    mean = np.average(values, weights=weights)
    if epsilon == 1:
        eq_dist = np.exp(np.average(np.log(values), weights=weights))
    else:
        eq_dist = np.average(values ** (1 - epsilon), weights=weights) ** (1 / (1 - epsilon))

    return 1 - eq_dist / mean


if __name__ == "__main__":
    # 测试
    np.random.seed(42)

    print("=== 测试 1: 完全平等 ===")
    values = np.full(100, 50.0)
    print(f"  Gini = {gini_simple(values):.4f} (期望 0.0)")

    print("\n=== 测试 2: 完全不平等 ===")
    values = np.zeros(100)
    values[-1] = 100  # 1 人占有所有
    print(f"  Gini = {gini_simple(values):.4f} (期望接近 1.0)")

    print("\n=== 测试 3: 人口加权 ===")
    values = np.array([10, 20, 30, 40, 50])
    weights = np.array([100, 100, 100, 100, 100])
    print(f"  无加权 Gini = {gini_simple(values):.4f}")
    print(f"  加权 Gini   = {gini_weighted(values, weights):.4f}")

    print("\n=== 测试 4: 分解 ===")
    df = pd.DataFrame({
        'temp': [20, 22, 21, 30, 32, 31, 25, 27, 26],
        'pop':  [100, 200, 150, 300, 250, 200, 100, 150, 100],
        'lcz':  ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C']
    })
    result = gini_decomposition(df, 'temp', 'pop', 'lcz')
    print(f"  G_total:   {result['G_total']:.4f}")
    print(f"  G_between: {result['G_between']:.4f} ({result['between_share']:.1%})")
    print(f"  G_within:  {result['G_within']:.4f} ({result['within_share']:.1%})")
    print(f"  G_overlap: {result['G_overlap']:.4f} ({result['overlap_share']:.1%})")
    print(f"\n  组统计:")
    print(result['group_stats'].to_string(index=False))
