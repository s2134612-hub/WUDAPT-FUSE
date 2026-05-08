"""
独立科研框架图: WUDAPT-FUSE Framework (v4 — 整体优化)

按 6 层次展示研究的完整科学逻辑链:
  L0: Research Question (top)
  L1: Data Foundation (4 sources)
  L2: UTCI Synthesis Method
  L3: Hypothesis Testing (4 parallel tests with PASS/FAIL)
  L4: Mechanism Validation (3 validation dimensions)
  L5: Conclusion (bottom)

v4 改进 (相对 v3):
  - 删除所有 Arial 不支持的 Unicode 符号 (✓ ✗ ★ ⟨ ⟩)
    数学公式用 mathtext \\overline{} 替代 ⟨ ⟩
    PASS/FAIL 仅保留文字, 颜色 + 加粗已能传达成功/失败
  - 统一线条粗细等级:
    · bus 主干 1.4
    · 单线 stage 转移 1.8
    · H4 强调 2.6
    · H1-H3 虚线弱化 0.8
  - 统一箭头大小:
    · 标准 head_width=5, head_length=7
    · 强调 head_width=6, head_length=9
  - 阶段间距匀称: L0→L1, L1→L2, L2→L3, L3→L4, L4→L5 各 ~5 plot units
  - 加大盒边框 linewidth (1.5 → 1.6) 提升清晰度
  - 移除 H4 标题中的 "★" (绿色 + PASS 已足以突出)
"""
import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

from src.utils.figure_style import apply_paper_style
apply_paper_style()

from src.utils.config import FIGURES_DIR


# 颜色规范 (色盲友好)
C = {
    'data':       {'face': '#dceaf2', 'edge': '#0571b0'},  # 蓝
    'method':     {'face': '#fde6cf', 'edge': '#ce682f'},  # 橙
    'test_fail':  {'face': '#fddbc7', 'edge': '#b2182b'},  # 红浅
    'test_pass':  {'face': '#ccebc5', 'edge': '#2ca25f'},  # 绿浅
    'validate':   {'face': '#efd8e9', 'edge': '#a6611a'},  # 紫
    'conclude':   {'face': '#fef0d9', 'edge': '#cc4c02'},  # 暖橙突出
    'question':   {'face': '#f0f0f0', 'edge': '#444444'},  # 灰
    'stage_1':    {'face': '#0571b0', 'edge': '#0571b0'},  # 蓝深
    'stage_2':    {'face': '#ce682f', 'edge': '#ce682f'},  # 橙深
    'stage_3':    {'face': '#a04050', 'edge': '#a04050'},  # 红深
    'stage_4':    {'face': '#a6611a', 'edge': '#a6611a'},  # 紫深
}

# === 统一线条/箭头规格 ===
LW_BUS = 1.4        # bus 总线
LW_STAGE = 1.8      # 单线阶段转移
LW_H4 = 2.6         # H4 强调箭头
LW_H_DASH = 0.8     # H1-H3 虚线弱化
LW_BOX = 1.6        # 所有盒子边框

ARROW_STD = '-|>,head_width=5,head_length=7'
ARROW_STRONG = '-|>,head_width=6,head_length=9'
ARROW_SMALL = '-|>,head_width=4,head_length=5'


# ────────────────────────────────────────────────────────────
# 绘图原语
# ────────────────────────────────────────────────────────────
def add_box_with_lines(ax, x, y, w, h, color_key,
                        title=None, lines=None,
                        title_size=10, content_size=8,
                        title_color=None, alpha=1.0,
                        title_y_offset=2.0,
                        line_height=2.5,
                        content_y_offset=5.0,
                        content_align='center',
                        ):
    """
    绘制圆角彩色框 + 标题 + 多行内容（用显式 plot-unit 偏移避免重叠）
    """
    c = C[color_key]
    if title_color is None:
        title_color = c['edge']

    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.4,rounding_size=1.5",
        facecolor=c['face'], edgecolor=c['edge'],
        linewidth=LW_BOX, alpha=alpha, zorder=2
    )
    ax.add_patch(box)

    cx = x + w / 2
    box_top = y + h

    if title:
        ax.text(cx, box_top - title_y_offset, title,
                ha='center', va='center',
                fontsize=title_size, fontweight='bold',
                color=title_color, zorder=3)

    if lines:
        for i, ln in enumerate(lines):
            yy = box_top - content_y_offset - i * line_height
            if content_align == 'left':
                ax.text(x + 2.5, yy, ln,
                        ha='left', va='center',
                        fontsize=content_size, color='#222', zorder=3)
            else:
                ax.text(cx, yy, ln,
                        ha='center', va='center',
                        fontsize=content_size, color='#222', zorder=3)


def add_stage_label(ax, y_center, stage_num, stage_name, color_key,
                     w=11, h=10, x_left=1):
    """左侧 STAGE 标签栏"""
    c = C[color_key]
    rect = Rectangle(
        (x_left, y_center - h / 2), w, h,
        facecolor=c['face'], edgecolor=c['edge'],
        linewidth=LW_BOX, zorder=2
    )
    ax.add_patch(rect)
    cx = x_left + w / 2
    ax.text(cx, y_center + 2.7, f'STAGE {stage_num}',
            ha='center', va='center',
            fontsize=10, fontweight='bold', color='white', zorder=3)
    ax.text(cx, y_center - 1.6, stage_name,
            ha='center', va='center',
            fontsize=10.5, fontweight='bold', color='white',
            linespacing=1.0, zorder=3)


def vertical_arrow(ax, x, y1, y2, color='#666', lw=LW_STAGE,
                    arrow_style=ARROW_STD, alpha=1.0):
    """简单垂直箭头"""
    arr = FancyArrowPatch(
        (x, y1), (x, y2),
        arrowstyle=arrow_style,
        mutation_scale=1, color=color, linewidth=lw,
        alpha=alpha, capstyle='butt', joinstyle='miter',
        zorder=1.5
    )
    ax.add_patch(arr)


def merge_arrows_to_target(ax, source_xs, source_y, target_x, target_y,
                            bus_y, color='#666', lw=LW_BUS, alpha=0.85,
                            arrow_style=ARROW_STD):
    """N 源汇聚到 1 目标 (横平竖直 bus 拓扑)"""
    # 1. 各源垂直下落到 bus
    for sx in source_xs:
        ax.plot([sx, sx], [source_y, bus_y],
                color=color, linewidth=lw, alpha=alpha,
                solid_capstyle='butt', zorder=1.5)
    # 2. 横向 bus
    bus_left = min(source_xs + [target_x])
    bus_right = max(source_xs + [target_x])
    ax.plot([bus_left, bus_right], [bus_y, bus_y],
            color=color, linewidth=lw, alpha=alpha,
            solid_capstyle='butt', zorder=1.5)
    # 3. 主干向下到 target (带箭头)
    arr = FancyArrowPatch(
        (target_x, bus_y), (target_x, target_y),
        arrowstyle=arrow_style,
        mutation_scale=1, color=color, linewidth=lw + 0.4,
        alpha=alpha, zorder=1.5
    )
    ax.add_patch(arr)


def split_bus_with_arrows(ax, source_x, source_y, target_xs, target_y,
                           bus_y, color='#666', lw=LW_BUS, alpha=0.85,
                           arrow_style=ARROW_STD):
    """1 源分叉到 N 目标 (主干 + 横 bus + N 分支箭头)"""
    # 1. 主干垂直下落
    ax.plot([source_x, source_x], [source_y, bus_y],
            color=color, linewidth=lw, alpha=alpha,
            solid_capstyle='butt', zorder=1.5)
    # 2. 横向 bus
    bus_left = min(target_xs + [source_x])
    bus_right = max(target_xs + [source_x])
    ax.plot([bus_left, bus_right], [bus_y, bus_y],
            color=color, linewidth=lw, alpha=alpha,
            solid_capstyle='butt', zorder=1.5)
    # 3. 各分支垂直下落 (带箭头)
    for tx in target_xs:
        arr = FancyArrowPatch(
            (tx, bus_y), (tx, target_y),
            arrowstyle=arrow_style,
            mutation_scale=1, color=color, linewidth=lw + 0.2,
            alpha=alpha, zorder=1.5
        )
        ax.add_patch(arr)


# ────────────────────────────────────────────────────────────
# 主流程
# ────────────────────────────────────────────────────────────
def main():
    print("生成科研框架图 v4 (整体优化)...")

    fig = plt.figure(figsize=(15, 13.5), dpi=130)
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # ============================================================
    # 全局 y 坐标 (统一阶段间距 ~5 plot units)
    # ============================================================
    # L0 Research Question: y=92.0–98.5 (h=6.5)
    # L0→L1 单线:           y=87.5–91.5 (gap 4.0)
    # L1 Data sources:      y=77.0–87.0 (h=10.0)
    # L1→L2 merge bus:      y=72.5 bus, target=70.5
    # L2 UTCI Synthesis:    y=62.0–70.5 (h=8.5)
    # L2→L3 split bus:      y=56.5 bus, italic 60.0
    # L3 Hypothesis test:   y=33.0–54.0 (h=21.0)
    # L3→L4 H4 bus:         y=29.5 bus
    # L4 Validation:        y=14.0–28.0 (h=14.0)
    # L4→L5 merge bus:      y=11.0 bus, target=9.5
    # L5 Conclusion:        y=1.0–9.5 (h=8.5)

    # ============================================================
    # L0: Research Question
    # ============================================================
    add_box_with_lines(
        ax, x=15, y=92, w=83, h=6.5, color_key='question',
        title='RESEARCH QUESTION',
        lines=['Can morphology-driven LCZ subcategorization explain '
               'within-class urban thermal exposure inequality '
               'at the 100-m neighborhood scale?'],
        title_size=11, content_size=10,
        title_y_offset=1.8, content_y_offset=4.4,
    )

    # L0 → L1 单线
    vertical_arrow(ax, x=56.5, y1=91.6, y2=87.5,
                    color='#888', lw=LW_STAGE)

    # ============================================================
    # L1: Data Foundation (4 数据源)
    # ============================================================
    add_stage_label(ax, y_center=82, stage_num=1,
                     stage_name='Data\nFusion', color_key='stage_1')

    data_sources = [
        ('ERA5-HEAT',     ['25 km × 1 h',
                           'UTCI Reanalysis',
                           '(Copernicus CDS)']),
        ('LCZ Map',       ['100 m',
                           'Demuzere 2022',
                           '17-class scheme']),
        ('WorldPop',      ['100 m gridded',
                           '2020 Constrained',
                           'Total 14.67 M']),
        ('OSM Buildings', ['Footprint vector',
                           '151 K (Shenzhen)',
                           'Multiple cities']),
    ]
    box_w_d, box_h_d = 18, 10
    y_data = 77
    x_starts = [16, 37, 58, 79]
    for (title, lines), x in zip(data_sources, x_starts):
        add_box_with_lines(
            ax, x=x, y=y_data, w=box_w_d, h=box_h_d,
            color_key='data',
            title=title, lines=lines,
            title_size=10.5, content_size=8.5,
            title_y_offset=1.7, line_height=2.0, content_y_offset=4.2,
        )

    # L1 → L2: 4 源汇聚到 UTCI synthesis
    data_box_centers = [x + box_w_d / 2 for x in x_starts]
    merge_arrows_to_target(
        ax,
        source_xs=data_box_centers,
        source_y=y_data,
        target_x=56.5,
        target_y=70.7,
        bus_y=74.5,
        color='#0571b0', lw=LW_BUS, alpha=0.75,
    )

    # ============================================================
    # L2: UTCI Synthesis (方法学)
    # ============================================================
    add_stage_label(ax, y_center=66, stage_num=2,
                     stage_name='UTCI\nSynthesis', color_key='stage_2')

    # 数学公式: ⟨ΔT⟩ → \overline{ΔT}  (Arial 不支持 ⟨⟩, 用 mathtext overline)
    formula = (r'UTCI$_{100m}$(i, t) = UTCI$_{25km}$(parent, t) '
                r'+ ΔT$_{LCZ}$(i) − $\overline{\Delta T}_{parent}$')

    add_box_with_lines(
        ax, x=15, y=62, w=83, h=8.5, color_key='method',
        title='DEVIATION-INJECTION SYNTHESIS',
        lines=[
            formula,
            '13,000 grid-hours  ·  3 cities × 4 seasons (2020)  ·  Mass conservation',
        ],
        title_size=10.5, content_size=9.5,
        title_y_offset=1.9, line_height=2.6, content_y_offset=4.6,
    )

    # 假设说明文字 (在 stage 3 boxes 上方)
    ax.text(56.5, 60.0,
            'Pop-weighted Gini decomposition + Pyatt-Yitzhaki  ·  '
            '6 feature families tested  ·  5 pp threshold',
            ha='center', va='center',
            fontsize=8.5, color='#666', style='italic', zorder=3)

    # ============================================================
    # L3: Hypothesis Testing (4 平行假设)
    # ============================================================
    add_stage_label(ax, y_center=43.5, stage_num=3,
                     stage_name='Hypothesis\nTesting', color_key='stage_3')

    test_y, test_h, test_w = 33, 21, 18
    x_test = [16, 37, 58, 79]
    test_centers = [x + test_w / 2 for x in x_test]

    # L2 → L3: UTCI synth 单源分叉到 4 假设
    split_bus_with_arrows(
        ax,
        source_x=56.5, source_y=62.0,
        target_xs=test_centers,
        target_y=test_y + test_h + 0.4,
        bus_y=56.5,
        color='#ce682f', lw=LW_BUS, alpha=0.75,
    )

    hypotheses = [
        {'h_label': 'H1: Morphology',
         'method': ['8 UMPs (OSM)', 'k-means clustering', '39 subcategories'],
         'result': '−1.0 pp', 'verdict': 'FAIL', 'color': 'test_fail'},
        {'h_label': 'H2: Topology',
         'method': ['5 PH-proxy', 'features', '19 subcategories'],
         'result': '−0.2 pp', 'verdict': 'FAIL', 'color': 'test_fail'},
        {'h_label': 'H3: Form + Topo',
         'method': ['13 features', 'hybrid k-means', '32 subcategories'],
         'result': '−0.9 pp', 'verdict': 'FAIL', 'color': 'test_fail'},
        {'h_label': 'H4: Geography',  # 移除 ★ (Arial 不支持)
         'method': ['Coast distance', 'Mountain distance', '+ elevation proxy'],
         'result': '−10.8 pp', 'verdict': 'PASS', 'color': 'test_pass'},
    ]

    for hyp, x in zip(hypotheses, x_test):
        c = C[hyp['color']]
        box = FancyBboxPatch(
            (x, test_y), test_w, test_h,
            boxstyle="round,pad=0.4,rounding_size=1.5",
            facecolor=c['face'], edgecolor=c['edge'],
            linewidth=LW_BOX + 0.2, zorder=2  # H 框稍粗
        )
        ax.add_patch(box)
        cx = x + test_w / 2

        # 假设标题
        ax.text(cx, test_y + test_h - 1.8, hyp['h_label'],
                ha='center', va='center',
                fontsize=10.5, fontweight='bold', color=c['edge'], zorder=3)

        # 方法 (3 行)
        method_top = test_y + test_h - 5.0
        for i, ln in enumerate(hyp['method']):
            ax.text(cx, method_top - i * 2.2, ln,
                    ha='center', va='center',
                    fontsize=8.5, color='#222', zorder=3)

        # 分隔线
        ax.plot([x + 1.5, x + test_w - 1.5],
                [test_y + 8.5, test_y + 8.5],
                color=c['edge'], linewidth=0.8, alpha=0.5, zorder=2.5)

        # 结果数字 (大字)
        ax.text(cx, test_y + 6.0, hyp['result'],
                ha='center', va='center',
                fontsize=18, fontweight='bold', color=c['edge'], zorder=3)

        # 判决 (移除 ✓/✗ 符号, 仅保留 PASS/FAIL 文字)
        ax.text(cx, test_y + 2.0, hyp['verdict'],
                ha='center', va='center',
                fontsize=12, fontweight='bold', color=c['edge'], zorder=3)

    # ============================================================
    # L3 → L4: H4 强绿箭头 + H1-H3 虚红弱化
    # ============================================================
    h4_x = test_centers[3]
    bus_y_3to4 = 29.5
    val_y, val_h = 14, 14
    val_top = val_y + val_h

    # H4 垂直下落 (粗绿)
    ax.plot([h4_x, h4_x], [test_y, bus_y_3to4],
            color='#2ca25f', linewidth=LW_H4, zorder=1.6,
            solid_capstyle='butt')
    # bus 横向: 56.5 → h4_x (粗绿)
    ax.plot([56.5, h4_x], [bus_y_3to4, bus_y_3to4],
            color='#2ca25f', linewidth=LW_H4, zorder=1.6,
            solid_capstyle='butt')
    # 中心向下 (强箭头)
    arr = FancyArrowPatch(
        (56.5, bus_y_3to4), (56.5, val_top + 0.4),
        arrowstyle=ARROW_STRONG,
        mutation_scale=1, color='#2ca25f', linewidth=LW_H4,
        zorder=1.6
    )
    ax.add_patch(arr)

    # H1-H3 虚线弱化 (浅红)
    for x_center in test_centers[:3]:
        ax.plot([x_center, x_center], [test_y, bus_y_3to4],
                color='#b2182b', linewidth=LW_H_DASH, alpha=0.4,
                linestyle='--', zorder=1.4)

    # 注解: only H4 passes
    ax.text(50, bus_y_3to4 + 0.9,
            'only H4 passes  →  validation',
            ha='right', va='bottom',
            fontsize=8.5, color='#2ca25f', style='italic',
            fontweight='bold', zorder=3)

    # ============================================================
    # L4: Mechanism Validation (3 验证)
    # ============================================================
    add_stage_label(ax, y_center=21, stage_num=4,
                     stage_name='Mechanism\nValidation', color_key='stage_4')

    # 移除 ✓/✗ 符号, 用 (pass)/(fail) 文字标注
    validations = [
        {'title': 'Physical Mechanism',
         'lines': ['• Coast → Sea breeze',
                   '• Mountain → Katabatic',
                   '   flow + canopy',
                   '   shading + drainage']},
        {'title': 'Temporal Robustness',
         'lines': ['• Diurnal: H1 day-peak,',
                   '   H2 night-peak',
                   '• Seasonal: 4 months,',
                   '   all > 5 pp']},
        {'title': 'Cross-city Transfer',
         'lines': ['• Shenzhen   100 %',
                   '• Dongguan   75 %',
                   '• Guangzhou   0 %',
                   '• Compactness moderates']},
    ]
    val_w = 26
    x_val = [16, 45, 74]
    val_centers = [x + val_w / 2 for x in x_val]

    # 中心 → 3 validation: 短分叉 (从 H4 主干末端出发)
    for vc in val_centers:
        arr = FancyArrowPatch(
            (vc, val_top + 1.6), (vc, val_top + 0.3),
            arrowstyle=ARROW_SMALL,
            mutation_scale=1, color='#a6611a', linewidth=LW_BUS,
            zorder=1.5
        )
        ax.add_patch(arr)
    # 横向分叉 bus
    ax.plot([min(val_centers), max(val_centers)],
            [val_top + 1.6, val_top + 1.6],
            color='#a6611a', linewidth=LW_BUS, alpha=0.85, zorder=1.5,
            solid_capstyle='butt')

    for v, x in zip(validations, x_val):
        c = C['validate']
        box = FancyBboxPatch(
            (x, val_y), val_w, val_h,
            boxstyle="round,pad=0.4,rounding_size=1.5",
            facecolor=c['face'], edgecolor=c['edge'],
            linewidth=LW_BOX, zorder=2
        )
        ax.add_patch(box)
        cx = x + val_w / 2
        ax.text(cx, val_y + val_h - 1.8, v['title'],
                ha='center', va='center',
                fontsize=10.5, fontweight='bold', color=c['edge'], zorder=3)
        # 内容左对齐 (项目符号开头)
        content_top = val_y + val_h - 5.0
        for i, ln in enumerate(v['lines']):
            ax.text(x + 2.5, content_top - i * 2.2, ln,
                    ha='left', va='center',
                    fontsize=8.5, color='#222', zorder=3)

    # ============================================================
    # L4 → L5: 3 验证汇聚到 conclusion
    # ============================================================
    merge_arrows_to_target(
        ax,
        source_xs=val_centers,
        source_y=val_y,
        target_x=56.5,
        target_y=9.7,
        bus_y=11.5,
        color='#a6611a', lw=LW_BUS, alpha=0.85,
    )

    # ============================================================
    # L5: Conclusion
    # ============================================================
    add_box_with_lines(
        ax, x=15, y=1, w=83, h=8.5, color_key='conclude',
        title='CONCLUSION',
        lines=[
            'Within-class urban thermal exposure inequality is governed by GEOGRAPHIC POSITION',
            '(mountain shading, sea breeze), NOT by building morphology or local topology.',
            'The mechanism is physical, temporally robust, and modulated by city compactness.',
        ],
        title_size=11, content_size=9.5,
        title_y_offset=1.7, line_height=2.0, content_y_offset=3.9,
    )

    # ============================================================
    # 总标题 + 副标题
    # ============================================================
    fig.suptitle('WUDAPT-FUSE Framework — Research Logic Chain',
                  fontsize=15, fontweight='bold', y=0.985)
    fig.text(0.5, 0.964,
              'A 4-stage workstation pipeline for testing whether morphology, '
              'topology, or geography explains intra-LCZ heat inequality',
              ha='center', va='top', fontsize=10, style='italic',
              color='#444')

    # ============================================================
    # 保存 PNG / SVG / PDF
    # ============================================================
    fig_path = FIGURES_DIR / "fig02_framework.png"
    plt.savefig(fig_path, dpi=140, bbox_inches='tight', facecolor='white')

    svg_path = FIGURES_DIR / "fig02_framework.svg"
    plt.savefig(svg_path, bbox_inches='tight', facecolor='white',
                format='svg', metadata={'Creator': 'WUDAPT-FUSE'})

    outputs = [(fig_path, 'PNG'), (svg_path, 'SVG')]
    pdf_path = FIGURES_DIR / "fig02_framework.pdf"
    try:
        plt.savefig(pdf_path, bbox_inches='tight', facecolor='white',
                    format='pdf')
        outputs.append((pdf_path, 'PDF'))
    except PermissionError:
        print(f"  ⚠ PDF 被外部程序占用 (跳过): {pdf_path.name}")

    plt.close()

    print(f"\n✓ 框架图 v4 输出 (整体优化):")
    for p, label in outputs:
        size_kb = p.stat().st_size / 1e3
        print(f"  • {p.name:<35} {size_kb:>8.1f} KB   {label}")

    from PIL import Image
    img = Image.open(fig_path)
    print(f"\n  PNG 尺寸: {img.size[0]} × {img.size[1]} px")

    return fig_path


if __name__ == "__main__":
    main()
