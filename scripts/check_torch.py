"""Check PyTorch and CUDA setup."""
import os
# Workaround for OpenMP conflict on Windows (PyTorch MKL vs conda libomp)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch

print(f"PyTorch:        {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version:   {torch.version.cuda}")

if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    cc = torch.cuda.get_device_capability(0)
    print(f"GPU:            {gpu_name}")
    print(f"GPU memory:     {gpu_mem:.1f} GB")
    print(f"Compute capability: {cc[0]}.{cc[1]}")

    # 简单 GPU 计算测试
    x = torch.randn(1000, 1000, device='cuda')
    y = x @ x.T
    print(f"GPU matmul test: shape {tuple(y.shape)}, mean {y.mean().item():.3f} OK")
else:
    print("⚠ CUDA not available, will use CPU (much slower)")
