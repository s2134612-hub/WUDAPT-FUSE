# 数据源详细清单

---

## 数据汇总

| Tier | 数据源 | 用途 | 分辨率 | 大小 | 难度 |
|------|--------|------|-------|------|------|
| 1 | ERA5-HEAT | 大尺度先验 UTCI | 25km × 1h | ~ 200 MB | 🟢 易 |
| 1 | HiTiSEA UTCI | 区域 UTCI | 10km × 日 | ~ 50 MB | 🟢 易 |
| 2 | Landsat 8/9 | 30m LST 锚点 | 30m × 16d | ~ 5 GB | 🟢 易 |
| 2 | MODIS | 1km LST 高频 | 1km × 4×/d | ~ 2 GB | 🟢 易 |
| 2 | Sentinel-2 | 反射率/NDVI | 10m × 5d | ~ 10 GB | 🟡 中 |
| 3 | LCZ 地图 | 类型分类 | 100m | ~ 50 MB | 🟢 易 |
| 3 | UMPs | 形态参数 | 100m | ~ 200 MB | 🟡 中 (需计算) |
| 3 | DEM | 地形 | 30m | ~ 100 MB | 🟢 易 |
| 3 | OSM 建筑 | 建筑数据 | 矢量 | ~ 500 MB | 🟢 易 |
| 4 | MMS 站点 | 训练标签 | 站点 × 1min | ~ 100 MB | 🟠 较难 |
| - | WorldPop | 人口（应用） | 100m | ~ 100 MB | 🟢 易 |
| - | 七普 | 年龄结构 | 街道级 | ~ 10 MB | 🟢 易 |
| - | 链家房价 | 收入代理 | 小区级 | ~ 5 MB | 🟡 中 (需爬虫) |

**总数据量**: ~ 20-30 GB

---

## Tier 1: 大尺度先验数据

### 1.1 ERA5-HEAT

**简介**: ECMWF 全球热舒适指数数据集，含 UTCI 和 MRT。

**下载方式**:

```python
# 注册账号
# 1. https://cds.climate.copernicus.eu/
# 2. 获取 API key
# 3. 配置 ~/.cdsapirc:
#    url: https://cds.climate.copernicus.eu/api/v2
#    key: <UID>:<API-KEY>

import cdsapi

c = cdsapi.Client()

c.retrieve(
    'derived-utci-historical',
    {
        'variable': ['universal_thermal_climate_index'],
        'product_type': 'consolidated_dataset',
        'version': '1_1',
        'year': '2020',
        'month': [f'{m:02d}' for m in range(1, 13)],
        'day': [f'{d:02d}' for d in range(1, 32)],
        'area': [22.9, 113.7, 22.4, 114.7],  # N, W, S, E (Shenzhen)
        'format': 'netcdf'
    },
    'data/raw/era5_heat_shenzhen_2020.nc'
)
```

**数据规模**:
- 空间: 25km grid → 深圳约 4 × 4 网格
- 时间: 2020 年 8760 小时
- 大小: ~ 200 MB

### 1.2 HiTiSEA

**论文**: [Yan et al. 2021, Sci Data](https://www.nature.com/articles/s41597-021-01010-w)

**下载链接**: https://www.scidb.cn/en/detail?dataSetId=cd9ef91a90854e80a5e6614a0c89ce6e

**变量**: UTCI, MRT, Twb, Tg, AT, Hu, NET, Twbg

**注意**:
- HDF5 / NetCDF 格式
- 需注册"Science Data Bank"账号

```python
import xarray as xr

ds = xr.open_dataset('data/raw/HiTiSEA_2020.nc')
shenzhen_subset = ds.sel(
    lat=slice(22.9, 22.4),
    lon=slice(113.7, 114.7)
)
```

---

## Tier 2: 高分辨率遥感

### 2.1 Landsat 8/9

**最佳方案**: Google Earth Engine（自动云掩膜 + 大批量下载）

```python
import ee
ee.Initialize()

# Shenzhen 边界
shenzhen = ee.Geometry.Rectangle([113.7, 22.4, 114.7, 22.9])

# Landsat 8 LST
collection = (
    ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    .filterBounds(shenzhen)
    .filterDate('2020-01-01', '2020-12-31')
    .filter(ee.Filter.lt('CLOUD_COVER', 30))
)

# 选择 LST 波段（B10）
def to_lst(image):
    lst = image.select('ST_B10').multiply(0.00341802).add(149.0)
    lst = lst.subtract(273.15)  # 转 ℃
    return lst.copyProperties(image, ['system:time_start'])

lst_collection = collection.map(to_lst)

# 导出到 Drive
task = ee.batch.Export.image.toDrive(
    image=lst_collection.median().clip(shenzhen),
    description='landsat8_lst_shenzhen_2020',
    folder='WUDAPT_DATA',
    region=shenzhen,
    scale=30,
    crs='EPSG:32650'
)
task.start()
```

**备选**: USGS EarthExplorer https://earthexplorer.usgs.gov/

### 2.2 MODIS LST

```python
import ee

modis = (
    ee.ImageCollection("MODIS/061/MOD11A1")
    .filterBounds(shenzhen)
    .filterDate('2020-01-01', '2020-12-31')
    .select(['LST_Day_1km', 'LST_Night_1km'])
)
```

### 2.3 Sentinel-2

```python
sentinel = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(shenzhen)
    .filterDate('2020-01-01', '2020-12-31')
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
)

# NDVI
def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

sentinel_with_ndvi = sentinel.map(add_ndvi)
```

---

## Tier 3: 静态特征

### 3.1 LCZ 地图

**最权威**: Demuzere et al. 2022 全球 LCZ
**链接**: https://zenodo.org/records/8214467

```python
import requests

url = "https://zenodo.org/records/8214467/files/lcz_filter_v3.tif"
response = requests.get(url)
with open('data/raw/lcz_global.tif', 'wb') as f:
    f.write(response.content)

# 裁剪到深圳
import rioxarray
lcz = rioxarray.open_rasterio('data/raw/lcz_global.tif')
shenzhen_lcz = lcz.rio.clip_box(113.7, 22.4, 114.7, 22.9)
shenzhen_lcz.rio.to_raster('data/processed/lcz_shenzhen_100m.tif')
```

**备选**: WUDAPT Generator https://lcz-generator.rub.de/

### 3.2 UMPs（城市形态参数）

需要从建筑数据自行计算。10 个 UMPs：

| 参数 | 简称 | 计算方法 |
|------|------|---------|
| Building Surface Fraction | BSF | 100m 网格内建筑面积 / 网格面积 |
| Mean Building Height | MBH | 网格内所有建筑高度均值 |
| Standard Deviation of BH | SBH | 网格内建筑高度标准差 |
| Mean Building Width | MBW | 平均建筑宽度 |
| Building Volume | BV | ∑(footprint × height) |
| Gross Floor Area | GFA | ∑(footprint × floors) |
| Mean Street Width | MSW | 街道宽度均值 |
| Sky View Factor | SVF | 用 SkyHelios 或简化公式 |
| Pervious Surface Fraction | PSF | 透水面积比例 |
| Water Surface Fraction | WSF | 水面比例 |

**建筑数据源**:
- OpenStreetMap (`pyrosm` 包) - 免费但不完整
- 高德地图 API - 较完整，需 API key
- 百度地图 API - 较完整，需 API key
- 全球建筑数据 GHSL: https://ghsl.jrc.ec.europa.eu/

### 3.3 DEM

```python
# SRTM 30m
ee.Image('USGS/SRTMGL1_003')
```

---

## Tier 4: MMS 站点观测

### 4.1 数据来源

**深圳**: 116 个 MMS 站点，深圳气象局 (SZMB)
- 公开网址: http://weather.sz.gov.cn
- 实时数据 API（受限）

### 4.2 获取策略

**首选**: 联系深圳大学合作
**备选 1**: SZMB 官方申请
**备选 2**: Lattice Mining（爬取公开网页历史快照）
**备选 3**: 使用国家气象信息中心 CMA 数据：
- http://data.cma.cn/
- 公开 ~ 30 个站点（不够 116 个但可用）

### 4.3 数据格式（典型）

```csv
station_id, datetime, AT(°C), RH(%), WS(m/s), WD(°), Pressure(hPa)
SZMB_001, 2020-01-01 00:00, 15.3, 65.2, 1.8, 90, 1015.2
...
```

---

## 应用层数据

### A1. WorldPop 人口

```python
import requests
url = "https://data.worldpop.org/GIS/Population/Global_2000_2020/2020/CHN/chn_ppp_2020.tif"
# 下载并裁剪深圳
```

### A2. 七普数据

- 国家统计局: http://www.stats.gov.cn/
- 街道级人口、年龄结构、教育程度
- 需手动整理为 CSV

### A3. 链家房价（爬虫）

详见 `scripts/crawl_lianjia.py`

### A4. 高德 POI

```python
import requests
api_key = "YOUR_KEY"
url = "https://restapi.amap.com/v3/place/text"
params = {
    'key': api_key,
    'keywords': '医院',
    'city': '深圳',
    'output': 'json'
}
```

---

## 数据下载优先级

### 第一周必装数据（约 5 GB）

```
□ 1. ERA5-HEAT UTCI (Shenzhen 2020)
□ 2. HiTiSEA UTCI (Shenzhen 2020)
□ 3. Demuzere LCZ 100m
□ 4. SRTM DEM
□ 5. 1 个月样本 Landsat 8
```

### 第二周扩展数据（约 15 GB）

```
□ 6. Landsat 8 全年
□ 7. MODIS LST 全年
□ 8. Sentinel-2 全年（或精选月份）
□ 9. OpenStreetMap 建筑数据
```

### 第三周高级数据（约 5 GB）

```
□ 10. UMPs 计算（基于 OSM 建筑）
□ 11. WorldPop 人口
□ 12. 七普街道级数据
□ 13. 高德 POI（医疗、教育、商业）
```

### 第四周补充数据

```
□ 14. 链家房价爬虫
□ 15. 116 站点数据（视合作进展）
□ 16. NPP-VIIRS 夜间灯光
```

---

## 数据存储策略

```
data/
├── raw/                     # 原始下载（不修改）
│   ├── era5/
│   ├── hitisea/
│   ├── landsat/
│   ├── modis/
│   ├── lcz/
│   └── stations/
│
├── processed/               # 处理后
│   ├── shenzhen_2020.zarr  # 主数据集（统一基准）
│   ├── umps/                # 计算的 UMPs
│   └── splits/              # 训练/验证/测试集
│
└── external/                # 第三方
    ├── worldpop/
    ├── osm/
    └── poi/
```

**版本控制**:
- 用 DVC (Data Version Control) 跟踪大文件
- 元数据用 git 跟踪

---

**最后更新**: 2026-05-06
