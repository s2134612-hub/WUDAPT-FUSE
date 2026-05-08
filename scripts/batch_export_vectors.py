"""
批量为已存在的 figure 生成 SVG + PDF 矢量版本。

策略:
  1. 每个生成脚本通过 subprocess 单独启动（避免模块状态污染）
  2. 用 sitecustomize 钩子让子进程的 matplotlib.savefig 自动多格式保存
  3. 每个脚本完成后切换到下一个

调用:
  python scripts/batch_export_vectors.py [fig_id ...]
  例:
    python scripts/batch_export_vectors.py            # 全部 fig03-fig12
    python scripts/batch_export_vectors.py 3 4 5      # 仅指定图号

注意:
  - fig01 和 fig02 已经在自身脚本中输出 PNG/SVG/PDF，不在此处理
  - 各脚本可能涉及计算 (TDA、聚类等)，单脚本耗时数十秒到数分钟
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
import time
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'
FIGURES_DIR = PROJECT_ROOT / 'figures'

# 项目使用 miniconda env "wudapt" 中的 Python (有 scipy/sklearn/gudhi 等)
# 系统默认 python 没有这些包，所以必须显式用 env 中的 python
CONDA_ENV_PYTHON = Path(r"C:/Users/13950/miniconda3/envs/wudapt/python.exe")
PYTHON_EXE = str(CONDA_ENV_PYTHON if CONDA_ENV_PYTHON.exists() else sys.executable)

# === 配置：每张图对应的生成脚本 ===
FIG_SCRIPTS = {
    3:  'utci_inequality.py',
    4:  'lcz_subcategories.py',
    5:  'subcategory_inequality.py',
    6:  'tda_analysis.py',
    7:  'hybrid_subcategorization.py',
    8:  'phase6_nonspatial.py',
    9:  'phase6_5_physical_mechanism.py',
    10: 'phase7_diurnal_validation.py',
    11: 'phase7_seasonal_validation.py',
    12: 'multicity_analysis.py',
}

# === 子进程启动器 (Python 代码注入到子进程，作为 -c 参数) ===
# 它先 monkey-patch matplotlib，再 exec 目标脚本
SUBPROCESS_RUNNER = '''
import os, sys, runpy
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pathlib import Path

# === Monkey-patch ===
_orig_plt_savefig = plt.savefig
_orig_fig_savefig = Figure.savefig

def _save_extras(saver_fn, fname, *args, **kwargs):
    fname_str = str(fname)
    if not fname_str.lower().endswith(".png"):
        return
    base = Path(fname_str).with_suffix("")
    vec_kwargs = {k: v for k, v in kwargs.items() if k != "dpi"}
    for ext in ["svg", "pdf"]:
        out = base.with_suffix("." + ext)
        try:
            saver_fn(out, *args, format=ext, **vec_kwargs)
            print(f"    [extra] {out.name}  {out.stat().st_size/1e3:.1f} KB")
        except PermissionError:
            print(f"    [extra] {out.name} 被锁定 (跳过)")
        except Exception as e:
            print(f"    [extra] {out.name} 失败: {type(e).__name__}: {e}")

def _patched_plt(fname, *args, **kwargs):
    result = _orig_plt_savefig(fname, *args, **kwargs)
    _save_extras(_orig_plt_savefig, fname, *args, **kwargs)
    return result

def _patched_fig(self, fname, *args, **kwargs):
    result = _orig_fig_savefig(self, fname, *args, **kwargs)
    def _saver(out, *a, **kw):
        return _orig_fig_savefig(self, out, *a, **kw)
    _save_extras(_saver, fname, *args, **kwargs)
    return result

plt.savefig = _patched_plt
Figure.savefig = _patched_fig

# === 执行目标脚本 ===
SCRIPT_PATH = sys.argv[1]
runpy.run_path(SCRIPT_PATH, run_name="__main__")
'''


# ────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────
def run_one(fig_id, script_name, timeout_sec=900):
    """通过 subprocess 启动单个生成脚本（隔离模块状态）"""
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"  ✗ 脚本不存在: {script_path}")
        return False

    print(f"\n{'=' * 70}")
    print(f"Fig {fig_id} ← {script_name}")
    print('=' * 70)

    t0 = time.time()
    try:
        result = subprocess.run(
            [PYTHON_EXE, '-c', SUBPROCESS_RUNNER, str(script_path)],
            cwd=str(PROJECT_ROOT),
            timeout=timeout_sec,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8',
                  'KMP_DUPLICATE_LIB_OK': 'TRUE'},
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
        )
        elapsed = time.time() - t0
        stdout = result.stdout or ''
        stderr = result.stderr or ''

        if result.returncode != 0:
            print(f"\n  ✗ 失败 ({elapsed:.1f}s, exit={result.returncode})")
            stdout_tail = stdout.splitlines()[-30:]
            stderr_tail = stderr.splitlines()[-30:]
            if stdout_tail:
                print("--- stdout (last 30 lines) ---")
                print('\n'.join(stdout_tail))
            if stderr_tail:
                print("--- stderr (last 30 lines) ---")
                print('\n'.join(stderr_tail))
            return False

        # 提取每行包含 "[extra]" 的行打印
        extra_lines = [ln for ln in stdout.splitlines() if '[extra]' in ln]
        print(f"  ⏱ {elapsed:.1f}s")
        if extra_lines:
            print(f"  矢量版本已生成:")
            for ln in extra_lines:
                print(f"    {ln.strip()}")
        else:
            print(f"  (脚本完成但未检测到 [extra] 标记 — 可能 PNG 直接保存)")
        return True
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(f"\n  ✗ 超时 ({elapsed:.1f}s, 超过 {timeout_sec}s)")
        return False
    except Exception as e:
        elapsed = time.time() - t0
        import traceback
        traceback.print_exc()
        print(f"\n  ✗ 异常 ({elapsed:.1f}s): {type(e).__name__}: {e}")
        return False


def main():
    if len(sys.argv) > 1:
        try:
            fig_ids = [int(x) for x in sys.argv[1:]]
        except ValueError:
            print("错误: 参数应为整数（fig 编号）")
            return 1
    else:
        fig_ids = sorted(FIG_SCRIPTS.keys())

    print(f"批量导出 SVG + PDF 矢量版本")
    print(f"目标: Fig {', '.join(str(i) for i in fig_ids)}")

    results = {}
    t_total_start = time.time()

    for fig_id in fig_ids:
        if fig_id not in FIG_SCRIPTS:
            print(f"  ✗ Fig {fig_id} 未配置脚本")
            results[fig_id] = False
            continue
        results[fig_id] = run_one(fig_id, FIG_SCRIPTS[fig_id])

    # === 汇总报告 ===
    print('\n' + '=' * 70)
    print('汇总报告')
    print('=' * 70)
    total_time = time.time() - t_total_start
    success_n = sum(1 for v in results.values() if v)
    print(f"\n总耗时: {total_time:.1f}s")
    print(f"成功: {success_n} / {len(results)}")
    for fid, ok in results.items():
        mark = '✓' if ok else '✗'
        print(f"  {mark} Fig {fid:2d} ← {FIG_SCRIPTS.get(fid, '???')}")

    # 列出 figures/ 中所有矢量文件
    print(f"\nfigures/ 中的矢量文件:")
    for ext in ['svg', 'pdf']:
        files = sorted(FIGURES_DIR.glob(f'fig*.{ext}'))
        for f in files:
            size_kb = f.stat().st_size / 1e3
            print(f"  • {f.name:<40} {size_kb:>7.1f} KB ({ext.upper()})")

    return 0 if success_n == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
