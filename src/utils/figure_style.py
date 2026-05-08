"""
统一图表样式配置（Nature / Science 系标准）。

调用方式（在所有出图脚本顶部）:
    from src.utils.figure_style import apply_paper_style
    apply_paper_style()
"""
import matplotlib
import matplotlib.pyplot as plt


# Nature / Science / Cell 标准字体
PAPER_FONT = {
    'family': 'sans-serif',
    'sans-serif': [
        'Arial',
        'Helvetica',
        'Liberation Sans',
        'DejaVu Sans',     # 兜底（系统总有）
    ],
}

# 标准字号（pt）
PAPER_SIZE = {
    'small':       7,    # 内部小字
    'tick':        8,    # 坐标刻度
    'label':       9,    # 轴标签 / 普通注释
    'panel_letter': 12,  # (a)(b)(c) 字母
    'title':       10,   # panel 标题
    'figure_title': 12,  # 整图标题
    'legend':      8,    # 图例
}

# 颜色规范（Nature 兼容）
PAPER_COLOR = {
    # 主分类配色（10 类，对色盲友好）
    'cat10': [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ],
    # 二元对比（暖/冷）
    'warm': '#fc8d59',
    'cool': '#1a9850',
    # 强调
    'highlight': '#d73027',
    'subtle':    '#999999',
    # 中性灰
    'gray':      '#666666',
    'gray_light': '#cccccc',
    'gray_dark':  '#333333',
}


def apply_paper_style(font_size_base=9):
    """
    应用 Nature / Science 风格字体与样式到全局 matplotlib rcParams。

    Parameters
    ----------
    font_size_base : int
        基础字号（pt），影响 axes.labelsize 等
    """
    rc = matplotlib.rcParams

    # 字体设置
    rc['font.family'] = PAPER_FONT['family']
    rc['font.sans-serif'] = PAPER_FONT['sans-serif']

    # 字号
    rc['font.size'] = font_size_base
    rc['axes.titlesize'] = PAPER_SIZE['title']
    rc['axes.labelsize'] = PAPER_SIZE['label']
    rc['xtick.labelsize'] = PAPER_SIZE['tick']
    rc['ytick.labelsize'] = PAPER_SIZE['tick']
    rc['legend.fontsize'] = PAPER_SIZE['legend']
    rc['figure.titlesize'] = PAPER_SIZE['figure_title']

    # 线宽 / 标记
    rc['axes.linewidth'] = 0.8
    rc['lines.linewidth'] = 1.4
    rc['lines.markersize'] = 5
    rc['xtick.major.width'] = 0.7
    rc['ytick.major.width'] = 0.7
    rc['xtick.minor.width'] = 0.4
    rc['ytick.minor.width'] = 0.4
    rc['xtick.major.size'] = 3
    rc['ytick.major.size'] = 3

    # 颜色与背景
    rc['axes.edgecolor'] = '#333333'
    rc['axes.labelcolor'] = '#222222'
    rc['xtick.color'] = '#222222'
    rc['ytick.color'] = '#222222'
    rc['axes.facecolor'] = 'white'
    rc['figure.facecolor'] = 'white'
    rc['savefig.facecolor'] = 'white'

    # PDF / EPS 兼容
    rc['pdf.fonttype'] = 42   # TrueType（嵌入字体）
    rc['ps.fonttype'] = 42

    # SVG: 保持文字为可编辑文本（而非转为路径）
    # → AI / Figma / Inkscape 中可直接编辑文字
    rc['svg.fonttype'] = 'none'

    # 高分辨率默认
    rc['savefig.dpi'] = 150
    rc['figure.dpi'] = 110

    # 数学字体（与 Arial 协调）
    rc['mathtext.fontset'] = 'custom'
    rc['mathtext.rm'] = 'Arial'
    rc['mathtext.it'] = 'Arial:italic'
    rc['mathtext.bf'] = 'Arial:bold'


def check_font_available(name='Arial'):
    """检查特定字体是否在系统上可用"""
    from matplotlib import font_manager
    fonts = [f.name for f in font_manager.fontManager.ttflist]
    return name in fonts


def save_paper_fig(fig_path, dpi=140, formats=('png', 'svg', 'pdf'),
                   verbose=True, **kwargs):
    """
    将当前 matplotlib 图同时保存为多种格式 (PNG / SVG / PDF)。

    用途: 投稿要求矢量图（SVG/PDF），同时保留 PNG 用于 Markdown 嵌入。

    Parameters
    ----------
    fig_path : str | Path
        基础路径（建议以 .png 结尾）。SVG/PDF 自动使用同一 stem。
    dpi : int
        仅 PNG 使用（矢量格式忽略）。
    formats : tuple of str
        要输出的格式扩展名。默认 ('png', 'svg', 'pdf')。
    verbose : bool
        是否打印保存信息。
    **kwargs
        传给 plt.savefig（例如 bbox_inches='tight', facecolor='white'）。

    Returns
    -------
    list of Path
        实际成功保存的文件路径列表。

    Notes
    -----
    - SVG 中文字保留为 <text>（svg.fonttype='none' 全局已设）。
    - 若某种格式因文件被外部程序占用而失败，会跳过并继续。
    """
    import matplotlib.pyplot as plt
    from pathlib import Path

    fig_path = Path(fig_path)
    base = fig_path.with_suffix('')
    saved = []

    for fmt in formats:
        out_path = base.with_suffix(f'.{fmt}')
        try:
            if fmt == 'png':
                plt.savefig(out_path, dpi=dpi, **kwargs)
            else:
                # 矢量格式（SVG/PDF）— dpi 不影响矢量
                plt.savefig(out_path, format=fmt, **kwargs)
            saved.append(out_path)
            if verbose:
                size_kb = out_path.stat().st_size / 1e3
                print(f"  ✓ {out_path.name:<42} {size_kb:>7.1f} KB ({fmt.upper()})")
        except PermissionError:
            if verbose:
                print(f"  ⚠ {out_path.name} 被外部程序占用，跳过")
        except Exception as e:
            if verbose:
                print(f"  ✗ {out_path.name} 保存失败: {e}")

    return saved


if __name__ == "__main__":
    # 验证脚本
    apply_paper_style()
    print(f"font.family: {matplotlib.rcParams['font.family']}")
    print(f"font.sans-serif: {matplotlib.rcParams['font.sans-serif']}")
    for f in ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans']:
        avail = check_font_available(f)
        print(f"  {f}: {'✓' if avail else '✗'}")
