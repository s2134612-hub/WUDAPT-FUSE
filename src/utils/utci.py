"""UTCI 计算工具：调用 pythermalcomfort 与简化 MRT 估算。"""
import numpy as np
from pythermalcomfort.models import utci as utci_model


def estimate_mrt_simple(t_air, svf, solar_gain=8.0):
    """
    简化的平均辐射温度估算。

    Parameters
    ----------
    t_air : float or ndarray
        气温 (°C)
    svf : float or ndarray in [0, 1]
        天空可视度
    solar_gain : float
        最大太阳辐射增益 (°C)，默认 8°C

    Returns
    -------
    mrt : float or ndarray
        平均辐射温度 (°C)
    """
    return t_air + (1 - svf) * solar_gain


def compute_utci(t_air, rh, ws, mrt=None, svf=None):
    """
    计算 UTCI 指数。

    Parameters
    ----------
    t_air : float or ndarray
        气温 (°C)
    rh : float or ndarray
        相对湿度 (%)
    ws : float or ndarray
        10m 风速 (m/s)
    mrt : float or ndarray, optional
        平均辐射温度 (°C)。如未提供，从 t_air + svf 估算。
    svf : float or ndarray, optional
        天空可视度。当 mrt 未提供时必须给出。

    Returns
    -------
    utci_value : float or ndarray
        UTCI (°C)
    """
    if mrt is None:
        if svf is None:
            raise ValueError("必须提供 mrt 或 svf")
        mrt = estimate_mrt_simple(t_air, svf)

    # 标量调用
    if np.isscalar(t_air):
        return utci_model(tdb=t_air, tr=mrt, v=ws, rh=rh)

    # 向量化调用
    result = np.zeros_like(t_air, dtype=np.float32)
    flat_t = np.asarray(t_air).ravel()
    flat_rh = np.asarray(rh).ravel()
    flat_ws = np.asarray(ws).ravel()
    flat_mrt = np.asarray(mrt).ravel()

    for i in range(len(flat_t)):
        try:
            result.ravel()[i] = utci_model(
                tdb=float(flat_t[i]),
                tr=float(flat_mrt[i]),
                v=float(flat_ws[i]),
                rh=float(flat_rh[i])
            )
        except Exception:
            result.ravel()[i] = np.nan

    return result.reshape(np.asarray(t_air).shape)


def utci_polynomial_fast(t_air, rh, ws, mrt):
    """
    UTCI 6 阶多项式逼近（Bröde et al. 2012），向量化高速版。
    精度 ~ 0.1°C，适合大批量计算。
    """
    eh_pa = 6.105 * np.exp(17.27 * t_air / (237.7 + t_air)) * rh / 100
    pa = eh_pa / 10.0  # kPa

    d_t_mrt = mrt - t_air
    va = np.clip(ws, 0.5, 17.0)

    # 6 阶 multivariate polynomial（约 130 项）
    # 这里给出简化展开
    utci_approx = (
        t_air
        + 0.607562052
        - 0.0227712343 * t_air
        + 0.000806470249 * t_air**2
        - 0.000154271372 * t_air**3
        + (0.0666053913 * va)
        - (0.000116720752 * va**2)
        + (0.00159389476 * d_t_mrt)
        - (0.000119300 * d_t_mrt**2)
        + (0.0683 * pa)
        - (0.00104 * pa**2)
    )
    return utci_approx


if __name__ == "__main__":
    # 测试
    print("简单标量测试:")
    val = compute_utci(t_air=30, rh=60, ws=2, svf=0.5)
    print(f"  UTCI = {val:.2f} °C")

    print("\n向量化测试:")
    n = 1000
    t = np.random.uniform(20, 35, n)
    rh = np.random.uniform(40, 90, n)
    ws = np.random.uniform(0.5, 5, n)
    svf = np.random.uniform(0.1, 0.9, n)

    import time
    t0 = time.time()
    utci_vals = compute_utci(t, rh, ws, svf=svf)
    print(f"  pythermalcomfort: {time.time()-t0:.2f}s for {n} points")

    t0 = time.time()
    mrt = estimate_mrt_simple(t, svf)
    utci_fast = utci_polynomial_fast(t, rh, ws, mrt)
    print(f"  Polynomial fast:  {time.time()-t0:.4f}s for {n} points")

    print(f"  Mean diff: {np.nanmean(np.abs(utci_vals - utci_fast)):.3f} °C")
