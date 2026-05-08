"""
拓扑数据分析模块（Topological Data Analysis, TDA）
基于持续同调（Persistent Homology）刻画 UTCI 热场的几何结构。

核心方法:
  1. Cubical Complex 持续同调（适用于 2D 栅格图像）
  2. 持续图（Persistence Diagram）特征提取
  3. Wasserstein 距离做拓扑相似性
  4. Persistence Statistics（β₀, β₁, 熵, 寿命）
"""
import numpy as np
import gudhi
from scipy.ndimage import label as scipy_label


def compute_persistence_diagram(utci_field, max_dim=1):
    """
    在 2D UTCI 场上计算 cubical complex 持续同调。

    Parameters
    ----------
    utci_field : np.ndarray (H, W)
        2D UTCI 场（NaN 值会自动用最大值填充）
    max_dim : int
        最高同调维度（默认 1: H_0 + H_1）

    Returns
    -------
    diag : list of (dim, (birth, death)) tuples
        持续图，每条记录一个拓扑特征
    """
    field = utci_field.copy().astype(np.float64)
    if np.any(np.isnan(field)):
        # 用全局最大值填 NaN（这样 NaN 区域不会形成拓扑特征）
        max_v = np.nanmax(field) + 1
        field = np.nan_to_num(field, nan=max_v)

    # Cubical Complex（图像式 sublevel filtration）
    cc = gudhi.CubicalComplex(top_dimensional_cells=field)
    cc.compute_persistence(homology_coeff_field=2)

    # 提取持续图
    pdiag = cc.persistence()  # list of (dim, (birth, death))
    return pdiag


def filter_persistence(pdiag, dim=None, min_lifetime=0.0,
                        exclude_inf=True):
    """从持续图中过滤特征。"""
    out = []
    for dim_d, (b, d) in pdiag:
        if dim is not None and dim_d != dim:
            continue
        if exclude_inf and d == float('inf'):
            continue
        lifetime = d - b
        if lifetime < min_lifetime:
            continue
        out.append((dim_d, (b, d)))
    return out


def persistence_features(pdiag, threshold=0.5):
    """
    提取持续图的标量特征。

    Returns
    -------
    dict 含:
      n_h0           : H_0 特征数（连通分量）
      n_h1           : H_1 特征数（一维洞）
      max_lifetime_h0
      max_lifetime_h1
      total_lifetime_h0
      total_lifetime_h1
      persistence_entropy
      n_significant   : 寿命 > threshold 的特征数
    """
    h0 = filter_persistence(pdiag, dim=0)
    h1 = filter_persistence(pdiag, dim=1)

    h0_lives = [d - b for _, (b, d) in h0]
    h1_lives = [d - b for _, (b, d) in h1]

    all_lives = h0_lives + h1_lives

    # Persistence Entropy
    if len(all_lives) > 0:
        L = sum(all_lives)
        if L > 0:
            probs = np.array(all_lives) / L
            entropy = -np.sum(probs * np.log(probs + 1e-12))
        else:
            entropy = 0.0
    else:
        entropy = 0.0

    n_sig = sum(1 for l in all_lives if l > threshold)

    return {
        'n_h0': len(h0),
        'n_h1': len(h1),
        'max_lifetime_h0': max(h0_lives) if h0_lives else 0.0,
        'max_lifetime_h1': max(h1_lives) if h1_lives else 0.0,
        'total_lifetime_h0': sum(h0_lives),
        'total_lifetime_h1': sum(h1_lives),
        'persistence_entropy': entropy,
        'n_significant': n_sig,
    }


def persistence_image(pdiag, dim=1, resolution=20,
                       sigma=0.05, weight=lambda x: x[1]):
    """
    生成 Persistence Image（持续图的栅格化表示）。

    Returns
    -------
    img : np.ndarray (resolution, resolution)
    """
    pts = np.array([(b, d - b) for dim_d, (b, d) in pdiag
                    if dim_d == dim and d != float('inf')])
    if len(pts) == 0:
        return np.zeros((resolution, resolution))

    # 网格
    b_min, b_max = 0.0, pts[:, 0].max() + 0.5
    p_min, p_max = 0.0, pts[:, 1].max() + 0.5
    x = np.linspace(b_min, b_max, resolution)
    y = np.linspace(p_min, p_max, resolution)
    XX, YY = np.meshgrid(x, y)

    img = np.zeros((resolution, resolution))
    for pt in pts:
        b, p = pt
        # Gaussian kernel
        gauss = np.exp(-((XX - b) ** 2 + (YY - p) ** 2) / (2 * sigma ** 2))
        img += weight((b, p)) * gauss

    return img


def wasserstein_distance(pd1, pd2, p=2, dim=None):
    """
    计算两个持续图的 p-Wasserstein 距离。
    """
    from gudhi.wasserstein import wasserstein_distance as gw_dist

    if dim is not None:
        pd1 = filter_persistence(pd1, dim=dim, exclude_inf=True)
        pd2 = filter_persistence(pd2, dim=dim, exclude_inf=True)

    arr1 = np.array([(b, d) for _, (b, d) in pd1]) if pd1 else np.empty((0, 2))
    arr2 = np.array([(b, d) for _, (b, d) in pd2]) if pd2 else np.empty((0, 2))

    if len(arr1) == 0 and len(arr2) == 0:
        return 0.0

    return gw_dist(arr1, arr2, order=p, internal_p=p)


def sublevel_betti_curve(utci_field, n_thresholds=50, t_min=None, t_max=None):
    """
    计算 sublevel filtration 下 β₀ 与 β₁ 随阈值的变化。

    Returns
    -------
    thresholds : np.ndarray
    betti0 : np.ndarray  (连通分量数)
    betti1 : np.ndarray  (一维洞数 = 用 Euler 特征数估算)
    """
    field = utci_field.copy()
    if t_min is None:
        t_min = np.nanmin(field)
    if t_max is None:
        t_max = np.nanmax(field)

    thresholds = np.linspace(t_min, t_max, n_thresholds)
    betti0 = np.zeros(n_thresholds, dtype=np.int32)
    betti1 = np.zeros(n_thresholds, dtype=np.int32)

    for i, t in enumerate(thresholds):
        # sublevel: cells with UTCI <= t
        mask = (field <= t).astype(np.int32)
        if mask.sum() == 0:
            continue
        # 连通分量数 (β₀)
        labels, n_comp = scipy_label(mask)
        betti0[i] = n_comp
        # β₁ 用 Euler 公式估算: V - E + F (近似)
        # 对 2D 栅格: β₁ = (n_holes_in_complement) ≈ (cells - components - bnd) / 4
        # 简化: 用反二值图的连通分量数 - 1 估计 β₁
        inv_mask = 1 - mask
        if inv_mask.sum() > 0:
            _, n_holes = scipy_label(inv_mask)
            # 内部洞数 ≈ 反图的非边界连通分量
            betti1[i] = max(0, n_holes - 1)

    return thresholds, betti0, betti1


def topology_feature_vector(utci_field, sigma=0.05, resolution=10):
    """
    把 2D UTCI 场转换为定长特征向量（用于聚类比较）。

    返回长度 ~ resolution^2 + 8 的向量
    """
    pdiag = compute_persistence_diagram(utci_field)

    # 1. 持续图像（H_1）
    pimg = persistence_image(pdiag, dim=1, resolution=resolution, sigma=sigma)
    pimg_flat = pimg.flatten() / (pimg.sum() + 1e-12)

    # 2. 标量特征
    feats = persistence_features(pdiag)
    scalar = np.array([
        feats['n_h0'],
        feats['n_h1'],
        feats['max_lifetime_h0'],
        feats['max_lifetime_h1'],
        feats['total_lifetime_h0'],
        feats['total_lifetime_h1'],
        feats['persistence_entropy'],
        feats['n_significant'],
    ])
    # Normalize
    if scalar.max() > 0:
        scalar = scalar / scalar.max()

    return np.concatenate([pimg_flat, scalar])


if __name__ == "__main__":
    # 简单测试
    np.random.seed(42)
    test_field = np.random.rand(50, 50) * 10 + 25  # 25-35 °C
    # 加几个明显的"冷岛"
    test_field[10:15, 10:15] = 22
    test_field[30:35, 30:35] = 23

    print("=== TDA 模块测试 ===")
    pd = compute_persistence_diagram(test_field)
    print(f"持续图特征数: {len(pd)}")

    feats = persistence_features(pd)
    print("\n持续特征:")
    for k, v in feats.items():
        print(f"  {k:25} = {v:.3f}" if isinstance(v, float)
              else f"  {k:25} = {v}")

    th, b0, b1 = sublevel_betti_curve(test_field, n_thresholds=20)
    print(f"\nSublevel curve: β₀ peak = {b0.max()}, β₁ peak = {b1.max()}")

    fvec = topology_feature_vector(test_field, resolution=8)
    print(f"\n特征向量长度: {len(fvec)}")
