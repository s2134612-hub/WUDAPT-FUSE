"""Simple direct import test."""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys

# 真实导入测试
test_imports = [
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("pandas", "pandas"),
    ("xarray", "xarray"),
    ("rasterio", "rasterio"),
    ("geopandas", "geopandas"),
    ("rioxarray", "rioxarray"),
    ("torch (CUDA)", "torch"),
    ("pytorch_lightning", "pytorch_lightning"),
    ("neuraloperator", "neuralop"),  # 包名 neuraloperator, 导入名 neuralop
    ("einops", "einops"),
    ("gudhi", "gudhi"),
    ("ripser", "ripser"),
    ("giotto-tda", "gtda"),  # 导入名是 gtda
    ("scikit-tda", "sktda"),  # 可能不同
    ("persim", "persim"),
    ("econml", "econml"),
    ("dowhy", "dowhy"),
    ("causal-learn", "causallearn"),
    ("pythermalcomfort", "pythermalcomfort"),
    ("cdsapi", "cdsapi"),
    ("pysal", "pysal"),
    ("libpysal", "libpysal"),
    ("esda", "esda"),
    ("statsmodels", "statsmodels"),
    ("xgboost", "xgboost"),
    ("shap", "shap"),
    ("lightgbm", "lightgbm"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
]

success = 0
fail = 0
for name, module in test_imports:
    try:
        m = __import__(module)
        ver = getattr(m, "__version__", "OK")
        print(f"  OK   {name:<20} {ver}")
        success += 1
    except ImportError as e:
        print(f"  FAIL {name:<20} {e}")
        fail += 1
    except Exception as e:
        print(f"  WARN {name:<20} {type(e).__name__}: {e}")
        success += 1

print(f"\n{success}/{success+fail} packages OK")

# CUDA check
import torch
print(f"\nCUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU:  {torch.cuda.get_device_name(0)}")

# pythermalcomfort 实际调用
print("\n--- pythermalcomfort UTCI test ---")
try:
    from pythermalcomfort.models import utci
    val = utci(tdb=30, tr=35, v=2, rh=60)
    print(f"UTCI(30C, 35C MRT, 2m/s, 60%RH) = {val}")
except Exception as e:
    print(f"Failed: {e}")
