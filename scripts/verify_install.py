"""
WUDAPT-FUSE 环境验证脚本

运行: python scripts/verify_install.py
"""
import os
# Windows OpenMP 冲突解决方案 (PyTorch MKL vs conda libomp)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path

# 颜色输出
class C:
    G = '\033[92m'  # green
    Y = '\033[93m'  # yellow
    R = '\033[91m'  # red
    B = '\033[94m'  # blue
    END = '\033[0m'


def check(name, importer, required=True):
    """尝试导入并报告状态"""
    try:
        version = importer()
        print(f"  {C.G}✓{C.END} {name:<30} {version}")
        return True
    except ImportError as e:
        symbol = f"{C.R}✗{C.END}" if required else f"{C.Y}!{C.END}"
        status = "MISSING" if required else "OPTIONAL"
        print(f"  {symbol} {name:<30} [{status}]")
        return False
    except Exception as e:
        print(f"  {C.Y}?{C.END} {name:<30} 错误: {str(e)[:50]}")
        return False


def section(title):
    print(f"\n{C.B}━━━ {title} ━━━{C.END}")


def main():
    print(f"\n{C.B}╔══════════════════════════════════════════╗{C.END}")
    print(f"{C.B}║  WUDAPT-FUSE 环境验证                    ║{C.END}")
    print(f"{C.B}╚══════════════════════════════════════════╝{C.END}")

    print(f"\nPython: {sys.version.split()[0]}")
    print(f"路径:   {sys.executable}")

    results = []

    # 1. 科学计算核心
    section("1. 科学计算核心")
    results.append(check("numpy",
        lambda: __import__("numpy").__version__))
    results.append(check("scipy",
        lambda: __import__("scipy").__version__))
    results.append(check("pandas",
        lambda: __import__("pandas").__version__))
    results.append(check("xarray",
        lambda: __import__("xarray").__version__))
    results.append(check("dask",
        lambda: __import__("dask").__version__))

    # 2. 地理空间
    section("2. 地理空间")
    results.append(check("rasterio",
        lambda: __import__("rasterio").__version__))
    results.append(check("geopandas",
        lambda: __import__("geopandas").__version__))
    results.append(check("rioxarray",
        lambda: __import__("rioxarray").__version__))
    results.append(check("netCDF4",
        lambda: __import__("netCDF4").__version__))

    # 3. 深度学习
    section("3. 深度学习")
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        cuda_status = f"CUDA={cuda_avail}"
        if cuda_avail:
            cuda_status += f", GPU={torch.cuda.get_device_name(0)}"
        print(f"  {C.G}✓{C.END} {'torch':<30} {torch.__version__} ({cuda_status})")
        results.append(True)
    except ImportError:
        print(f"  {C.R}✗{C.END} {'torch':<30} [MISSING]")
        results.append(False)

    results.append(check("pytorch_lightning",
        lambda: __import__("pytorch_lightning").__version__))

    # neuralop (FNO)
    try:
        import neuralop
        ver = getattr(neuralop, '__version__', 'unknown')
        print(f"  {C.G}✓{C.END} {'neuralop (FNO)':<30} {ver}")
        results.append(True)
    except ImportError:
        print(f"  {C.R}✗{C.END} {'neuralop (FNO)':<30} [MISSING]")
        results.append(False)

    # 4. 拓扑数据分析
    section("4. 拓扑数据分析")
    results.append(check("gudhi",
        lambda: __import__("gudhi").__version__))
    results.append(check("ripser",
        lambda: __import__("ripser").__version__))

    try:
        import gtda
        ver = getattr(gtda, '__version__', 'unknown')
        print(f"  {C.G}✓{C.END} {'giotto-tda':<30} {ver}")
        results.append(True)
    except ImportError:
        print(f"  {C.Y}!{C.END} {'giotto-tda':<30} [OPTIONAL]")

    # 5. 因果推断
    section("5. 因果推断")
    results.append(check("econml",
        lambda: __import__("econml").__version__))
    results.append(check("dowhy",
        lambda: __import__("dowhy").__version__))

    try:
        import causallearn
        print(f"  {C.G}✓{C.END} {'causal-learn':<30} OK")
        results.append(True)
    except ImportError:
        print(f"  {C.Y}!{C.END} {'causal-learn':<30} [OPTIONAL]")

    # 6. 符号回归
    section("6. 符号回归")
    try:
        import pysr
        ver = getattr(pysr, '__version__', 'unknown')
        print(f"  {C.G}✓{C.END} {'pysr':<30} {ver}")
        print(f"      {C.Y}注: 首次使用需要 Julia 后端{C.END}")
        results.append(True)
    except ImportError:
        print(f"  {C.Y}!{C.END} {'pysr':<30} [OPTIONAL, 需 Julia]")

    # 7. 城市气候专用
    section("7. 城市气候专用")
    try:
        from pythermalcomfort.models import utci
        utci_test = utci(tdb=30, tr=35, v=2, rh=60)
        print(f"  {C.G}✓{C.END} {'pythermalcomfort':<30} UTCI test = {utci_test:.2f}")
        results.append(True)
    except ImportError:
        print(f"  {C.R}✗{C.END} {'pythermalcomfort':<30} [MISSING]")
        results.append(False)
    except Exception as e:
        print(f"  {C.Y}!{C.END} {'pythermalcomfort':<30} 已装但调用失败: {str(e)[:40]}")

    results.append(check("cdsapi",
        lambda: __import__("cdsapi").__version__))

    # 8. 空间统计
    section("8. 空间统计")
    results.append(check("pysal",
        lambda: __import__("pysal").__version__))
    results.append(check("esda",
        lambda: __import__("esda").__version__))
    results.append(check("statsmodels",
        lambda: __import__("statsmodels").__version__))

    # 总结
    section("汇总")
    n_pass = sum(results)
    n_total = len(results)
    pct = 100 * n_pass / n_total

    print(f"\n  通过: {n_pass}/{n_total} ({pct:.1f}%)")

    if n_pass == n_total:
        print(f"\n{C.G}🎉 所有核心组件就绪！可以开始 Phase 1。{C.END}")
        print(f"\n下一步: python scripts/download_sample.py")
        return 0
    elif pct >= 80:
        print(f"\n{C.Y}⚠  大部分组件就绪，有少量缺失（可能影响部分功能）{C.END}")
        return 0
    else:
        print(f"\n{C.R}❌ 关键依赖缺失，请检查 environment.yml{C.END}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
