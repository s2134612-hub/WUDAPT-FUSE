"""
WUDAPT-FUSE Hello-World 脚本

跑通最简流程，验证开发环境工作正常：
  1. 加载 LCZ 样本
  2. 模拟 UTCI 计算
  3. 计算最简单的拓扑特征
  4. 输出图表

运行: python scripts/hello_world.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import matplotlib.pyplot as plt

from src.utils.config import (
    SHENZHEN_BBOX, RAW_DATA_DIR, FIGURES_DIR, ensure_dirs
)
from src.utils.logging import get_logger
from src.utils.utci import compute_utci, estimate_mrt_simple, utci_polynomial_fast

log = get_logger("hello_world")


def step1_demo_utci():
    """演示 UTCI 计算"""
    log.info("=== Step 1: UTCI 计算演示 ===")

    # 模拟一个 100×100 的 UTCI 场（深圳子区域）
    np.random.seed(42)
    H, W = 100, 100

    # 模拟 AT, RH, WS, SVF 字段（带空间结构）
    x = np.linspace(0, 1, W)
    y = np.linspace(0, 1, H)
    X, Y = np.meshgrid(x, y)

    # 中心是高建筑（高 BSF, 低 SVF, 高温），边缘是公园（低 BSF, 高 SVF, 低温）
    distance = np.sqrt((X - 0.5)**2 + (Y - 0.5)**2)

    AT = 32 - 4 * distance + np.random.normal(0, 0.5, (H, W))    # 28-32°C
    RH = 60 + 10 * distance + np.random.normal(0, 2, (H, W))     # 60-70%
    WS = 1.0 + 1.5 * distance + np.random.normal(0, 0.2, (H, W))  # 1-2.5 m/s
    SVF = 0.3 + 0.4 * distance + np.random.normal(0, 0.05, (H, W))  # 0.3-0.7

    # 计算 UTCI（用快速多项式版）
    MRT = estimate_mrt_simple(AT, SVF)
    UTCI = utci_polynomial_fast(AT, RH, WS, MRT)

    log.info(f"  UTCI 范围: {UTCI.min():.1f} - {UTCI.max():.1f} °C")
    log.info(f"  UTCI 均值: {UTCI.mean():.2f} °C")

    return AT, RH, WS, SVF, UTCI


def step2_topology_demo(utci_field):
    """演示拓扑数据分析"""
    log.info("=== Step 2: TDA 演示 ===")

    try:
        import gudhi
    except ImportError:
        log.warning("  GUDHI 未安装，跳过 TDA")
        return None

    # 计算 cubical complex 持续同调
    cc = gudhi.CubicalComplex(top_dimensional_cells=utci_field)
    cc.compute_persistence()
    diagrams = cc.persistence()

    # 提取 H_0, H_1
    h0 = [(b, d) for dim, (b, d) in diagrams if dim == 0]
    h1 = [(b, d) for dim, (b, d) in diagrams if dim == 1]

    log.info(f"  连通分量 (β₀): {len(h0)}")
    log.info(f"  一维洞 (β₁): {len(h1)}")

    if h1:
        max_lifetime = max(d - b for b, d in h1)
        log.info(f"  最长洞寿命: {max_lifetime:.2f} °C")

    return diagrams


def step3_visualize(AT, RH, WS, SVF, UTCI, diagrams):
    """生成可视化图表"""
    log.info("=== Step 3: 可视化 ===")

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    # AT
    im0 = axes[0, 0].imshow(AT, cmap='Reds', origin='lower')
    axes[0, 0].set_title('Air Temperature (°C)')
    plt.colorbar(im0, ax=axes[0, 0])

    # RH
    im1 = axes[0, 1].imshow(RH, cmap='Blues', origin='lower')
    axes[0, 1].set_title('Relative Humidity (%)')
    plt.colorbar(im1, ax=axes[0, 1])

    # WS
    im2 = axes[0, 2].imshow(WS, cmap='Greens', origin='lower')
    axes[0, 2].set_title('Wind Speed (m/s)')
    plt.colorbar(im2, ax=axes[0, 2])

    # SVF
    im3 = axes[1, 0].imshow(SVF, cmap='Purples', origin='lower')
    axes[1, 0].set_title('Sky View Factor')
    plt.colorbar(im3, ax=axes[1, 0])

    # UTCI
    im4 = axes[1, 1].imshow(UTCI, cmap='RdYlBu_r', origin='lower')
    axes[1, 1].set_title('UTCI (°C) — Combined Effect')
    plt.colorbar(im4, ax=axes[1, 1])

    # Persistence diagram
    if diagrams:
        ax = axes[1, 2]
        h0 = [(b, d) for dim, (b, d) in diagrams if dim == 0 and d != float('inf')]
        h1 = [(b, d) for dim, (b, d) in diagrams if dim == 1]

        if h0:
            b0, d0 = zip(*h0)
            ax.scatter(b0, d0, c='blue', alpha=0.6, label=f'H₀ (n={len(h0)})')
        if h1:
            b1, d1 = zip(*h1)
            ax.scatter(b1, d1, c='red', alpha=0.6, label=f'H₁ (n={len(h1)})')

        # 对角线
        lim = [UTCI.min() - 1, UTCI.max() + 1]
        ax.plot(lim, lim, 'k--', alpha=0.3)
        ax.set_xlabel('Birth')
        ax.set_ylabel('Death')
        ax.set_title('Persistence Diagram')
        ax.legend()
    else:
        axes[1, 2].text(0.5, 0.5, 'GUDHI not available',
                       ha='center', va='center', transform=axes[1, 2].transAxes)
        axes[1, 2].set_title('Persistence Diagram (skipped)')

    plt.tight_layout()
    output_path = FIGURES_DIR / "hello_world.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    log.info(f"  图表保存到: {output_path}")
    plt.close()


def main():
    ensure_dirs()
    log.info("=" * 50)
    log.info("WUDAPT-FUSE Hello-World")
    log.info("=" * 50)

    AT, RH, WS, SVF, UTCI = step1_demo_utci()
    diagrams = step2_topology_demo(UTCI)
    step3_visualize(AT, RH, WS, SVF, UTCI, diagrams)

    log.info("\n🎉 Hello-World 完成！")
    log.info(f"   查看输出图表: {FIGURES_DIR}/hello_world.png")
    log.info("\n下一步: 运行 python scripts/download_sample.py 下载真实数据")


if __name__ == "__main__":
    main()
