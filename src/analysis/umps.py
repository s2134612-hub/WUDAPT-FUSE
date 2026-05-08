"""
计算城市形态参数（Urban Morphological Parameters, UMPs）。

输入: 建筑 polygon (UTM 投影，米制)
输出: 100m 网格上的 UMPs 栅格

UMPs 列表:
  BSF (Building Surface Fraction)        建筑底面积占比
  MBH (Mean Building Height)              建筑平均高度
  SBH (Std of Building Height)            建筑高度标准差
  MBW (Mean Building Width)               建筑平均宽度
  BV  (Building Volume m^3 per 100m grid) 总建筑体积
  GFA (Gross Floor Area m^2)              总建筑面积（楼层加成）
  PSF (Pervious Surface Fraction)          可渗透面积占比 = 1 - BSF - WSF - 路面
  WSF (Water Surface Fraction)             水面占比（来自 LCZ 17）
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from shapely.strtree import STRtree
from rasterio.features import rasterize
import rasterio
from rasterio.transform import from_bounds


def make_grid_polygons(bounds, resolution_m=100, crs="EPSG:32650"):
    """
    生成 100m × 100m 矢量网格（用于 GeoDataFrame 操作）

    Parameters
    ----------
    bounds : tuple
        (minx, miny, maxx, maxy) in meters (UTM)
    resolution_m : int
    crs : str

    Returns
    -------
    GeoDataFrame with grid_id, geometry
    """
    minx, miny, maxx, maxy = bounds
    nx = int(np.ceil((maxx - minx) / resolution_m))
    ny = int(np.ceil((maxy - miny) / resolution_m))

    cells = []
    grid_ids = []
    for j in range(ny):
        for i in range(nx):
            x0 = minx + i * resolution_m
            y0 = miny + j * resolution_m
            cell = box(x0, y0, x0 + resolution_m, y0 + resolution_m)
            cells.append(cell)
            grid_ids.append(j * nx + i)

    grid = gpd.GeoDataFrame(
        {'grid_id': grid_ids, 'i': [g % nx for g in grid_ids], 'j': [g // nx for g in grid_ids]},
        geometry=cells,
        crs=crs
    )
    return grid, nx, ny


def compute_umps_from_buildings(buildings_gdf, bounds, resolution_m=100,
                                 use_strtree=True, log=None):
    """
    从建筑 GDF 计算 100m 网格上的 UMPs。

    Parameters
    ----------
    buildings_gdf : GeoDataFrame
        必含列: 'geometry', 'area_m2', 'height', 'volume_m3'
    bounds : tuple (minx, miny, maxx, maxy)
        UTM 投影下的研究区边界
    resolution_m : int
    use_strtree : bool
        用空间索引加速

    Returns
    -------
    dict[str, np.ndarray]
        每个 key 是一个 UMP，值是 (ny, nx) 矩阵
    """
    if log is None:
        import logging
        log = logging.getLogger(__name__)

    minx, miny, maxx, maxy = bounds
    nx = int(np.ceil((maxx - minx) / resolution_m))
    ny = int(np.ceil((maxy - miny) / resolution_m))
    log.info(f"  网格: {ny} × {nx} = {ny*nx:,} 个 100m 栅格")

    # 初始化输出
    bsf = np.zeros((ny, nx), dtype=np.float32)
    bldg_count = np.zeros((ny, nx), dtype=np.int32)
    sum_height = np.zeros((ny, nx), dtype=np.float64)
    sum_height_sq = np.zeros((ny, nx), dtype=np.float64)
    sum_width = np.zeros((ny, nx), dtype=np.float64)
    sum_volume = np.zeros((ny, nx), dtype=np.float64)
    sum_gfa = np.zeros((ny, nx), dtype=np.float64)

    cell_area = resolution_m ** 2

    # 用 STRtree 加速空间查询
    if use_strtree:
        log.info("  构建 STRtree...")
        strtree = STRtree(list(buildings_gdf.geometry))
        building_array = buildings_gdf.reset_index(drop=True)

    # 对每个建筑：找到它跨越的栅格，按 footprint 占比累加
    log.info("  计算每个建筑的栅格归属（rasterize 法）...")

    # 用 rasterio.features.rasterize 高效完成
    transform = from_bounds(minx, miny, maxx, maxy, nx, ny)

    # 对每个建筑，rasterize 它的 footprint，然后用结果累加
    # 但有 100 万个建筑这种方法太慢，用矢量方式：

    # 简化：先把 footprint area 用 rasterize 累加（按面积权重）
    # rasterize 的 'all_touched' 模式会让一个建筑分配给所有它接触的栅格
    # 这里我们用另一种策略：按建筑质心归类

    log.info("  按建筑质心快速归类...")
    centroids = buildings_gdf.geometry.centroid
    cx = np.array([p.x for p in centroids])
    cy = np.array([p.y for p in centroids])

    # 计算每个建筑落在哪个栅格
    i_idx = ((cx - minx) / resolution_m).astype(int)
    j_idx = ((cy - miny) / resolution_m).astype(int)

    # 边界保护
    valid = (i_idx >= 0) & (i_idx < nx) & (j_idx >= 0) & (j_idx < ny)
    log.info(f"  落在网格内的建筑: {valid.sum():,} / {len(buildings_gdf):,}")

    i_idx = i_idx[valid]
    j_idx = j_idx[valid]
    area = buildings_gdf['area_m2'].values[valid]
    height = buildings_gdf['height'].values[valid]
    volume = buildings_gdf['volume_m3'].values[valid]

    # 估算建筑宽度：sqrt(area)
    width = np.sqrt(area)

    # GFA: area × levels (假设 height/3m = levels)
    gfa = area * np.maximum(height / 3.0, 1.0)

    # 累加到栅格
    log.info("  累加建筑属性到栅格...")
    for k in range(len(i_idx)):
        i, j = i_idx[k], j_idx[k]
        bsf[j, i] += area[k]
        bldg_count[j, i] += 1
        sum_height[j, i] += height[k]
        sum_height_sq[j, i] += height[k] ** 2
        sum_width[j, i] += width[k]
        sum_volume[j, i] += volume[k]
        sum_gfa[j, i] += gfa[k]

    # 转换 BSF 为占比
    bsf_frac = bsf / cell_area
    bsf_frac = np.clip(bsf_frac, 0, 1)

    # MBH = sum_height / count
    with np.errstate(divide='ignore', invalid='ignore'):
        mbh = np.where(bldg_count > 0, sum_height / bldg_count, 0)
        mean_h_sq = np.where(bldg_count > 0, sum_height_sq / bldg_count, 0)
        sbh = np.sqrt(np.maximum(mean_h_sq - mbh ** 2, 0))
        mbw = np.where(bldg_count > 0, sum_width / bldg_count, 0)

    bv = sum_volume  # m^3 per cell
    gfa_grid = sum_gfa  # m^2 per cell

    log.info("  完成 UMP 计算")
    log.info(f"    BSF 范围: {bsf_frac.min():.3f} - {bsf_frac.max():.3f}")
    log.info(f"    MBH 范围: {mbh[mbh>0].min() if (mbh>0).any() else 0:.2f} - {mbh.max():.2f} m")
    log.info(f"    BV 总和:  {bv.sum()/1e9:.2f} 千立方米")

    return {
        'BSF': bsf_frac.astype(np.float32),
        'MBH': mbh.astype(np.float32),
        'SBH': sbh.astype(np.float32),
        'MBW': mbw.astype(np.float32),
        'BV':  bv.astype(np.float32),
        'GFA': gfa_grid.astype(np.float32),
        'BLDG_COUNT': bldg_count,
    }


def compute_svf_simple(bsf, mbh, h0=10.0):
    """
    简化版 Sky View Factor 估算（基于 BSF 和 MBH）。

    SVF ≈ 1 - BSF × atan(MBH / h0) / (π/2)

    h0 是参考街道宽度（约 10m）。
    """
    arctan_term = np.arctan(mbh / h0)
    svf = 1 - bsf * arctan_term / (np.pi / 2)
    return np.clip(svf, 0, 1).astype(np.float32)


def compute_psf_from_lcz(lcz_array, bsf):
    """
    从 LCZ + BSF 估算可渗透面积占比 (PSF)。

    经验法则:
      PSF = 1 - BSF - 路面占比 - WSF
    其中路面占比按 LCZ 类型估算
    """
    # LCZ 类型对应的不透水路面占比（粗略）
    impervious_map = {
        1:  0.50, 2:  0.45, 3:  0.40, 4:  0.30, 5:  0.30, 6:  0.25,
        7:  0.40, 8:  0.45, 9:  0.10, 10: 0.50,
        11: 0.05, 12: 0.10, 13: 0.10, 14: 0.20, 15: 0.80,
        16: 0.20, 17: 0.00,
    }

    impervious_pct = np.zeros_like(bsf)
    for lcz_id, pct in impervious_map.items():
        impervious_pct[lcz_array == lcz_id] = pct

    psf = 1 - bsf - impervious_pct
    psf = np.clip(psf, 0, 1)

    # 水域强制 PSF = 0
    psf[lcz_array == 17] = 0

    return psf.astype(np.float32)


def compute_wsf_from_lcz(lcz_array):
    """从 LCZ 17 估算 WSF。"""
    return (lcz_array == 17).astype(np.float32)


if __name__ == "__main__":
    print("UMPs 模块测试")
    # 简单单元测试
    import logging
    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("umps_test")

    # 模拟 5 栋建筑
    from shapely.geometry import Polygon
    polys = [
        Polygon([(50, 50), (70, 50), (70, 70), (50, 70)]),  # 在 (0,0) cell
        Polygon([(150, 50), (170, 50), (170, 70), (150, 70)]),  # 在 (1,0) cell
        Polygon([(50, 150), (70, 150), (70, 170), (50, 170)]),  # 在 (0,1) cell
    ]
    buildings = gpd.GeoDataFrame(
        {
            'area_m2': [400, 400, 400],
            'height': [30, 50, 20],
            'volume_m3': [12000, 20000, 8000],
        },
        geometry=polys,
        crs="EPSG:32650"
    )

    bounds = (0, 0, 200, 200)  # 200m x 200m -> 4 cells
    umps = compute_umps_from_buildings(buildings, bounds, resolution_m=100, log=log)
    print("\nBSF:")
    print(umps['BSF'])
    print("\nMBH:")
    print(umps['MBH'])
    print("\nSBH:")
    print(umps['SBH'])
