# 数据账号注册详细指南

需要注册 4 个账号（全部免费）。按优先级排序：

---

## 🥇 1. ECMWF Climate Data Store (CDS) — 最重要

**作用**: 下载 ERA5-HEAT UTCI（核心数据）

### 步骤

#### 1.1 注册账号
1. 访问: **https://cds.climate.copernicus.eu/**
2. 点击右上角 **"Login"** → **"Register"**
3. 填写邮箱 + 密码（建议用学术邮箱）
4. 邮件验证 → 完成注册

#### 1.2 接受 ERA5 Terms of Use
1. 登录后访问任意 ERA5 数据集页面，例如:
   https://cds.climate.copernicus.eu/cdsapp#!/dataset/derived-utci-historical
2. 滚动到底部 **"Terms of use"**
3. 勾选 **"I accept these terms"**

#### 1.3 获取 API Key
1. 登录后访问: **https://cds.climate.copernicus.eu/profile**
2. 在页面找到 **"API Token"** 部分
3. 复制完整的 Token（看起来像 `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）

#### 1.4 配置 ~/.cdsapirc

在 PowerShell 中执行（**替换 YOUR_API_KEY**）:

```powershell
$cdsapirc = @"
url: https://cds.climate.copernicus.eu/api
key: YOUR_API_KEY
"@
$cdsapirc | Out-File -FilePath "$env:USERPROFILE\.cdsapirc" -Encoding ascii
Get-Content "$env:USERPROFILE\.cdsapirc"
```

#### 1.5 验证配置
```powershell
& "$env:USERPROFILE\miniconda3\envs\wudapt\python.exe" -c "import cdsapi; c = cdsapi.Client(); print('OK')"
```

---

## 🥈 2. NASA Earthdata — 重要

**作用**: 下载 MODIS LST、SRTM DEM 等 NASA 数据

### 步骤

#### 2.1 注册
1. 访问: **https://urs.earthdata.nasa.gov/users/new**
2. 选择 "Register a new user"
3. 填写信息（建议学术机构）
4. 邮件验证

#### 2.2 配置 ~/.netrc

```powershell
$netrc = @"
machine urs.earthdata.nasa.gov
login YOUR_USERNAME
password YOUR_PASSWORD
"@
$netrc | Out-File -FilePath "$env:USERPROFILE\.netrc" -Encoding ascii
```

⚠️ **安全**: .netrc 包含明文密码，确保此文件权限正确。

---

## 🥉 3. Google Earth Engine — 推荐

**作用**: 高效下载 Landsat 8/9, Sentinel-2, MODIS（替代手工下载）

### 步骤

#### 3.1 注册
1. 访问: **https://earthengine.google.com/**
2. 点击 "Get Started"
3. 用 Google 账号登录
4. 申请使用（学术用户通常立即批准）

#### 3.2 创建 Cloud Project
1. 访问: https://console.cloud.google.com/
2. 创建新项目（如 "wudapt-fuse"）
3. 启用 Earth Engine API

#### 3.3 认证 Earth Engine

```powershell
& "$env:USERPROFILE\miniconda3\envs\wudapt\Scripts\earthengine.exe" authenticate --quiet
```

如认证不成功:
```powershell
& "$env:USERPROFILE\miniconda3\envs\wudapt\python.exe" -c "import ee; ee.Authenticate()"
```

会打开浏览器，登录并复制 token。

---

## 📊 4. USGS EarthExplorer — 备用

**作用**: 直接下载 Landsat 数据（备用，已有 GEE 后通常不必）

### 步骤

1. 访问: **https://earthexplorer.usgs.gov/**
2. 注册账号
3. 用于通过 `landsatxplore` 工具下载

---

## 5. 其他可选账号

### 5.1 高德开放平台（POI 数据）
- https://lbs.amap.com/
- 注册 → 创建应用 → 获取 Key
- 免费额度：5,000 次/天

### 5.2 百度地图开放平台（备选）
- https://lbsyun.baidu.com/

### 5.3 OpenTopography（高质量 DEM）
- https://opentopography.org/
- 不需账号即可下载较小区域

---

## 📋 注册进度追踪

完成后在此打勾：

```
□ ECMWF CDS 已注册
□ ECMWF API key 已配置 (~/.cdsapirc)
□ ECMWF Terms 已接受
□ NASA Earthdata 已注册
□ NASA .netrc 已配置
□ Google Earth Engine 已激活
□ Earth Engine 已认证
□ 高德地图 API key（可选）
```

---

## 🚨 常见问题

### Q1: ECMWF CDS API key 提示无效
- 确认 API key 完整复制（不要有多余空格）
- 确认 url 字段值正确（**https://cds.climate.copernicus.eu/api**，注意是 `/api` 不是 `/api/v2`）

### Q2: Earth Engine 认证失败
- 确保 Cloud Project 已创建
- 在浏览器中清除缓存重试
- 用学术机构 Google 账号

### Q3: NASA Earthdata 下载 401 错误
- .netrc 文件名必须正确（Windows 上是 `_netrc` 或 `.netrc`，根据工具）
- 也可以尝试在 PowerShell 中设置环境变量 `EARTHDATA_USERNAME` 和 `EARTHDATA_PASSWORD`

---

## ⏱️ 预计时间

```
ECMWF CDS:     5 分钟
NASA Earthdata: 5 分钟
Google Earth Engine: 10-15 分钟（含 Cloud Project）
全部完成:        约 20-30 分钟
```

---

## 完成后下一步

```powershell
# 1. 验证账号配置
& "$env:USERPROFILE\miniconda3\envs\wudapt\python.exe" "E:\Claude project\SCI5\WUDAPT-FUSE\scripts\check_accounts.py"

# 2. 运行下载脚本
& "$env:USERPROFILE\miniconda3\envs\wudapt\python.exe" "E:\Claude project\SCI5\WUDAPT-FUSE\scripts\download_with_auth.py"
```
