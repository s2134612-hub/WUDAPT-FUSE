"""
Fig 1 (v5 — 框架图独立后): 研究区与输入数据 (Shenzhen, GBA)

变化 (v4 → v5):
  - 移除原 panel (a) 工作流程图（已迁移到独立的 fig02_framework.{png,svg,pdf}）
  - 三张地图重新排版为单行，整体放大
  - 重新编号: (b) → (a) LCZ + ERA5 cells
            (c) → (b) WorldPop population
            (d) → (c) UTCI July 2020
  - 顶部增加统一的研究区与数据来源说明
  - LCZ 图例放在 (a) 正下方更紧凑
  - 同时输出 PNG / SVG / PDF 三种格式

调用方式:
  python scripts/make_fig01_concept.py
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import xarray as xr
import rioxarray as rxr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm

from src.utils.config import PROCESSED_DATA_DIR, FIGURES_DIR, SHENZHEN_BBOX
from src.utils.figure_style import apply_paper_style
apply_paper_style()

# === 加载数据 ===
print("加载数据...")
lcz = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_lcz_100m_utm.tif",
                         masked=True).squeeze()
pop = rxr.open_rasterio(PROCESSED_DATA_DIR / "shenzhen_pop_100m_utm.tif",
                         masked=True).squeeze()
utci_ds = xr.open_dataset(PROCESSED_DATA_DIR / "shenzhen_utci_100m_jul_summary.nc")

# === LCZ 颜色（Stewart-Oke 2012 标准）===
LCZ_COLORS = {
    1: '#8c0000', 2: '#d10000', 3: '#ff0000', 4: '#bf4d00',
    5: '#ff6600', 6: '#ff9955', 7: '#faee05', 8: '#bcbcbc',
    9: '#ffccaa', 10: '#555555',
    11: '#006a00', 12: '#00aa00', 13: '#648525', 14: '#b9db79',
    15: '#bababa', 16: '#fbf7ae', 17: '#6a6aff'
}
LCZ_NAMES_SHORT = {
    1: '1 CHR', 2: '2 CMR', 3: '3 CLR', 4: '4 OHR', 5: '5 OMR',
    6: '6 OLR', 7: '7 LWR', 8: '8 LLR', 9: '9 SB', 10: '10 HI',
    11: 'A DT', 12: 'B ST', 13: 'C BS', 14: 'D LP',
    15: 'E BR', 16: 'F BSa', 17: 'G Wat'
}


# ────────────────────────────────────────────────────────────
# Panel (a): LCZ 100m + ERA5 25km cells
# ────────────────────────────────────────────────────────────
def create_lcz_panel(ax, lcz_da):
    lcz_wgs = lcz_da.rio.reproject("EPSG:4326")
    lcz_arr = lcz_wgs.values
    lons = lcz_wgs.x.values
    lats = lcz_wgs.y.values

    lcz_ids = sorted(LCZ_COLORS.keys())
    colors = [LCZ_COLORS[i] for i in lcz_ids]
    cmap = ListedColormap(colors)
    bounds = [i - 0.5 for i in lcz_ids] + [lcz_ids[-1] + 0.5]
    norm = BoundaryNorm(bounds, cmap.N)

    extent = [lons.min(), lons.max(), lats.min(), lats.max()]
    ax.imshow(lcz_arr, extent=extent, cmap=cmap, norm=norm,
              origin='upper', interpolation='nearest', aspect='equal')

    # ERA5 25 km grid cell 边界
    era5_lons_centers = [113.75, 114.0, 114.25, 114.5]
    era5_lats_centers = [22.50, 22.75]
    era5_v_lines = [113.625, 113.875, 114.125, 114.375, 114.625]
    era5_h_lines = [22.375, 22.625, 22.875]
    for lon in era5_v_lines:
        ax.axvline(lon, color='black', linewidth=0.9,
                   linestyle='--', alpha=0.85)
    for lat in era5_h_lines:
        ax.axhline(lat, color='black', linewidth=0.9,
                   linestyle='--', alpha=0.85)

    # ERA5 中心点和 cell 编号
    for j, lat in enumerate(era5_lats_centers):
        for i, lon in enumerate(era5_lons_centers):
            cell_id = j * 4 + i + 1
            ax.plot(lon, lat, marker='+', color='white',
                    markersize=10, markeredgewidth=2.2, zorder=10)
            ax.text(lon, lat - 0.04, f'C{cell_id}',
                    fontsize=8, color='black', fontweight='bold',
                    ha='center', va='top',
                    bbox=dict(boxstyle='round,pad=0.2',
                              facecolor='white', edgecolor='black',
                              alpha=0.9, linewidth=0.5),
                    zorder=10)

    ax.set_xlim(SHENZHEN_BBOX['west'], SHENZHEN_BBOX['east'])
    ax.set_ylim(SHENZHEN_BBOX['south'], SHENZHEN_BBOX['north'])
    ax.set_xlabel('Longitude (°E)', fontsize=10)
    ax.set_ylabel('Latitude (°N)', fontsize=10)
    ax.set_title('(a)  Local Climate Zone (100 m)  +  ERA5 25 km cells',
                 fontsize=11.5, fontweight='bold', loc='left',
                 pad=8)
    ax.tick_params(labelsize=9)

    # 北箭头
    ax.annotate('', xy=(0.06, 0.97), xytext=(0.06, 0.86),
                xycoords='axes fraction',
                arrowprops=dict(arrowstyle='-|>', facecolor='black',
                                edgecolor='black', lw=1.5))
    ax.text(0.06, 0.83, 'N', transform=ax.transAxes,
            ha='center', va='top', fontsize=11, fontweight='bold')

    # 比例尺 (大约 10 km)
    # 深圳东西约 100 km，纬度 22.6° 经度 0.1° ≈ 10.3 km
    scale_y = SHENZHEN_BBOX['south'] + 0.025
    scale_x0 = SHENZHEN_BBOX['east'] - 0.18
    scale_x1 = scale_x0 + 0.10
    ax.plot([scale_x0, scale_x1], [scale_y, scale_y],
            color='black', linewidth=2.5, solid_capstyle='butt')
    ax.text((scale_x0 + scale_x1) / 2, scale_y + 0.012,
            '10 km', ha='center', va='bottom',
            fontsize=8.5, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                      edgecolor='none', alpha=0.85))


# ────────────────────────────────────────────────────────────
# Panel (b): Population
# ────────────────────────────────────────────────────────────
def create_pop_panel(ax, pop_da):
    pop_wgs = pop_da.rio.reproject("EPSG:4326")
    pop_arr = pop_wgs.values
    pop_arr = np.where(pop_arr <= 0, np.nan, pop_arr)
    lons = pop_wgs.x.values
    lats = pop_wgs.y.values

    extent = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(pop_arr, extent=extent, cmap='viridis',
                   origin='upper', vmin=0, vmax=200, aspect='equal')

    cbar = plt.colorbar(im, ax=ax, fraction=0.038, pad=0.03,
                        extend='max')
    cbar.set_label('Persons / 100 m cell', fontsize=9, labelpad=4)
    cbar.ax.tick_params(labelsize=8)

    # ERA5 网格细线
    for lon in [113.625, 113.875, 114.125, 114.375, 114.625]:
        ax.axvline(lon, color='white', linewidth=0.6,
                   linestyle=':', alpha=0.65)
    for lat in [22.375, 22.625, 22.875]:
        ax.axhline(lat, color='white', linewidth=0.6,
                   linestyle=':', alpha=0.65)

    ax.set_xlim(SHENZHEN_BBOX['west'], SHENZHEN_BBOX['east'])
    ax.set_ylim(SHENZHEN_BBOX['south'], SHENZHEN_BBOX['north'])
    ax.set_xlabel('Longitude (°E)', fontsize=10)
    ax.set_ylabel('Latitude (°N)', fontsize=10)
    ax.set_title('(b)  WorldPop 2020 (100 m)  ·  total 14.67 M',
                 fontsize=11.5, fontweight='bold', loc='left',
                 pad=8)
    ax.tick_params(labelsize=9)


# ────────────────────────────────────────────────────────────
# Panel (c): UTCI
# ────────────────────────────────────────────────────────────
def create_utci_panel(ax, utci_ds):
    utci_mean = utci_ds['utci_mean'].values
    lons = utci_ds.lon.values
    lats = utci_ds.lat.values

    extent = [lons.min(), lons.max(), lats.min(), lats.max()]
    im = ax.imshow(utci_mean, extent=extent, cmap='RdYlBu_r',
                   origin='upper', vmin=29.5, vmax=32.0, aspect='equal')

    cbar = plt.colorbar(im, ax=ax, fraction=0.038, pad=0.03)
    cbar.set_label('Mean UTCI (°C)', fontsize=9, labelpad=4)
    cbar.ax.tick_params(labelsize=8)

    # ERA5 网格
    for lon in [113.625, 113.875, 114.125, 114.375, 114.625]:
        ax.axvline(lon, color='white', linewidth=0.7,
                   linestyle='--', alpha=0.7)
    for lat in [22.375, 22.625, 22.875]:
        ax.axhline(lat, color='white', linewidth=0.7,
                   linestyle='--', alpha=0.7)

    ax.set_xlim(SHENZHEN_BBOX['west'], SHENZHEN_BBOX['east'])
    ax.set_ylim(SHENZHEN_BBOX['south'], SHENZHEN_BBOX['north'])
    ax.set_xlabel('Longitude (°E)', fontsize=10)
    ax.set_ylabel('Latitude (°N)', fontsize=10)
    ax.set_title('(c)  Synthesised UTCI (100 m)  ·  July 2020',
                 fontsize=11.5, fontweight='bold', loc='left',
                 pad=8)
    ax.tick_params(labelsize=9)

    # 统计标注 - 右下角
    ax.text(0.97, 0.03,
            'Mean 30.8 °C\nMax  41.6 °C\nTSD$_{\\rm max}$ 337 h',
            transform=ax.transAxes, ha='right', va='bottom',
            fontsize=8, family='monospace',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='#888888', alpha=0.92, linewidth=0.5))


# ────────────────────────────────────────────────────────────
# LCZ 图例 (横向放在底部)
# ────────────────────────────────────────────────────────────
def create_lcz_legend(fig):
    handles = []
    legend_order = [1, 2, 3, 4, 5, 6, 8, 9, 10,
                    11, 12, 14, 16, 17]
    for lcz_id in legend_order:
        patch = mpatches.Patch(facecolor=LCZ_COLORS[lcz_id],
                               edgecolor='black', linewidth=0.5,
                               label=LCZ_NAMES_SHORT[lcz_id])
        handles.append(patch)

    leg = fig.legend(handles=handles, loc='lower center',
                     ncol=14, fontsize=8.5,
                     frameon=True, edgecolor='#888888',
                     bbox_to_anchor=(0.5, 0.045),
                     title='LCZ classes  (Stewart & Oke 2012)',
                     title_fontsize=9.5,
                     handlelength=1.4, handleheight=1.0,
                     columnspacing=0.9)
    leg.get_frame().set_linewidth(0.6)


# ────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────
def main():
    print("生成 Fig 1 v5 (study site & input data, 3-panel single row)")

    # 单行 3 panel + 底部图例
    # Shenzhen bbox: 1° × 0.5° → 地图天然 2:1 横向
    # figsize 选择策略:
    #   - 单 panel 实际地图区 ~4.0" 宽 → 自然高度 ~2.0" (受 cbar 占用稍微变窄)
    #   - title (~0.4") + xlabel/ticks (~0.5") = 单 panel 总高 ~3"
    #   - 图例 + 主标题 + 副标题 ≈ 1.5"
    #   - 总图高 ≈ 4.5"
    fig = plt.figure(figsize=(14, 4.6), dpi=140)

    gs = fig.add_gridspec(
        1, 3,
        wspace=0.36,
        left=0.055, right=0.975,
        top=0.82, bottom=0.32
    )

    ax_a = fig.add_subplot(gs[0, 0])
    create_lcz_panel(ax_a, lcz)

    ax_b = fig.add_subplot(gs[0, 1])
    create_pop_panel(ax_b, pop)

    ax_c = fig.add_subplot(gs[0, 2])
    create_utci_panel(ax_c, utci_ds)

    # === LCZ 图例 (底部独立行) ===
    create_lcz_legend(fig)

    # === 整体标题 + 副标题 ===
    fig.suptitle('Study site and input data: Shenzhen, Greater Bay Area',
                 fontsize=13.5, fontweight='bold', y=0.97)
    fig.text(0.5, 0.91,
             'Three 100-m gridded layers underpin the WUDAPT-FUSE pipeline '
             '(framework in Fig. 2).  '
             'Dashed lines: ERA5-HEAT 25-km cells; C1–C8: parent-cell IDs.',
             ha='center', va='top', fontsize=9,
             style='italic', color='#444')

    # 保存为 3 种格式 (PDF 若被外部预览锁定，跳过)
    outputs = []

    fig_path = FIGURES_DIR / "fig01_concept.png"
    plt.savefig(fig_path, dpi=140, bbox_inches='tight',
                facecolor='white', pad_inches=0.15)
    outputs.append((fig_path, 'PNG'))

    svg_path = FIGURES_DIR / "fig01_concept.svg"
    plt.savefig(svg_path, bbox_inches='tight',
                facecolor='white', format='svg', pad_inches=0.15)
    outputs.append((svg_path, 'SVG'))

    pdf_path = FIGURES_DIR / "fig01_concept.pdf"
    try:
        plt.savefig(pdf_path, bbox_inches='tight',
                    facecolor='white', format='pdf', pad_inches=0.15)
        outputs.append((pdf_path, 'PDF'))
    except PermissionError:
        print(f"  ⚠ PDF 被外部程序占用 (跳过): {pdf_path.name}")

    plt.close()

    print(f"\n✓ Fig 1 v5 已生成 (study site & input data):")
    for p, label in outputs:
        print(f"  • {p.name:<28} {p.stat().st_size/1e3:>8.1f} KB   ({label})")

    from PIL import Image
    img = Image.open(fig_path)
    print(f"\n  PNG 尺寸: {img.size[0]} × {img.size[1]} px")

    return fig_path


if __name__ == "__main__":
    main()
