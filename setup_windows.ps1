# WUDAPT-FUSE Windows 11 安装脚本
# 使用方法: 在管理员 PowerShell 中执行
#   cd "E:\Claude project\SCI5\WUDAPT-FUSE"
#   .\setup_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  WUDAPT-FUSE 环境配置开始" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: 检查 Conda 是否已安装
Write-Host "`n[1/6] 检查 Miniconda/Anaconda..." -ForegroundColor Yellow
$condaCmd = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaCmd) {
    Write-Host "未检测到 Conda。请先从以下地址安装 Miniconda:" -ForegroundColor Red
    Write-Host "  https://docs.conda.io/en/latest/miniconda.html" -ForegroundColor Red
    Write-Host "或使用 winget:" -ForegroundColor Yellow
    Write-Host "  winget install Anaconda.Miniconda3" -ForegroundColor Yellow
    exit 1
}
Write-Host "  Conda 已安装: $((conda --version))" -ForegroundColor Green

# Step 2: 检查 NVIDIA GPU
Write-Host "`n[2/6] 检查 NVIDIA GPU..." -ForegroundColor Yellow
$nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvidiaSmi) {
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    Write-Host "  GPU 检测成功" -ForegroundColor Green
} else {
    Write-Host "  警告: 未检测到 NVIDIA GPU。FNO 训练将使用 CPU（很慢）。" -ForegroundColor Yellow
    Write-Host "  如有 NVIDIA 显卡，请安装最新驱动。" -ForegroundColor Yellow
}

# Step 3: 创建 Conda 环境
Write-Host "`n[3/6] 创建 wudapt Conda 环境..." -ForegroundColor Yellow
$envExists = (conda env list | Select-String "wudapt").Count -gt 0
if ($envExists) {
    $reply = Read-Host "环境 'wudapt' 已存在。是否删除重建? (y/N)"
    if ($reply -eq 'y') {
        conda env remove -n wudapt -y
        conda env create -f environment.yml
    } else {
        Write-Host "  跳过环境创建，使用现有环境" -ForegroundColor Yellow
    }
} else {
    conda env create -f environment.yml
}
Write-Host "  Conda 环境就绪" -ForegroundColor Green

# Step 4: 检查 Julia（PySR 依赖）
Write-Host "`n[4/6] 检查 Julia..." -ForegroundColor Yellow
$juliaCmd = Get-Command julia -ErrorAction SilentlyContinue
if (-not $juliaCmd) {
    Write-Host "  Julia 未安装。" -ForegroundColor Yellow
    Write-Host "  请运行: winget install JuliaLang.Julia" -ForegroundColor Yellow
    Write-Host "  或访问: https://julialang.org/downloads/" -ForegroundColor Yellow
    Write-Host "  （PySR 必需，但可稍后安装）" -ForegroundColor Yellow
} else {
    Write-Host "  Julia 已安装: $((julia --version))" -ForegroundColor Green
}

# Step 5: 配置 PySR 后端
Write-Host "`n[5/6] 配置 PySR Julia 后端..." -ForegroundColor Yellow
if ($juliaCmd) {
    & conda run -n wudapt python -c "import pysr; pysr.install()"
    Write-Host "  PySR 后端就绪" -ForegroundColor Green
} else {
    Write-Host "  跳过 PySR 配置（Julia 未安装）" -ForegroundColor Yellow
}

# Step 6: 验证安装
Write-Host "`n[6/6] 运行验证脚本..." -ForegroundColor Yellow
& conda run -n wudapt python scripts\verify_install.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  安装完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`n下一步:" -ForegroundColor Yellow
Write-Host "  1. conda activate wudapt" -ForegroundColor White
Write-Host "  2. 注册 ECMWF CDS 账号: https://cds.climate.copernicus.eu/" -ForegroundColor White
Write-Host "  3. 配置 ~/.cdsapirc" -ForegroundColor White
Write-Host "  4. python scripts\download_sample.py" -ForegroundColor White
