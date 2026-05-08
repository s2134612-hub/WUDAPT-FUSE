"""Quick smoke test - prints minimal output."""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

results = {}
modules = [
    "numpy", "scipy", "pandas", "xarray",
    "rasterio", "geopandas", "rioxarray",
    "torch", "pytorch_lightning", "neuralop", "einops",
    "gudhi", "ripser", "gtda", "persim",
    "econml", "dowhy", "causallearn",
    "pythermalcomfort", "cdsapi",
    "pysal", "libpysal", "esda", "statsmodels",
    "xgboost", "shap", "lightgbm",
    "matplotlib", "seaborn",
]

ok = []
fail = []
for mod in modules:
    try:
        m = __import__(mod)
        ver = getattr(m, "__version__", "OK")
        ok.append((mod, str(ver)))
    except Exception as e:
        fail.append((mod, str(e)[:60]))

print(f"PASS: {len(ok)}/{len(modules)}")
for n, v in ok:
    print(f"  + {n}: {v}")
if fail:
    print(f"\nFAILED: {len(fail)}")
    for n, e in fail:
        print(f"  - {n}: {e}")

import torch
print(f"\nCUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
