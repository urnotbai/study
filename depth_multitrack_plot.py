# -*- coding: utf-8 -*-
"""
高度定制化地质深度多跨度线型图（测井解释剖面风格）
- 支持中英文混排独立渲染（中文：微软雅黑；英文/数字/符号：Times New Roman）
- 顶部X轴、共享反转深度Y轴、底部统一图例
"""

import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.offsetbox import AnnotationBbox, HPacker, TextArea


# =========================
# 第一部分：全局参数控制区（可直接微调）
# =========================

# 1) 字体控制参数（严格要求）
font_zh = 'Microsoft YaHei'           # 中文字体（微软雅黑）
font_en = 'Times New Roman'           # 英文字体
base_font_size_zh = 10                # 中文基础字号
base_font_size_en = base_font_size_zh + 0.5  # 英文基础字号（比中文大0.5）
font_weight = 'bold'                  # 全局文字加粗

# 2) 深度控制参数
depth_tick_interval = 2               # Y轴深度标签显示间隔（m）
data_sample_interval = 4              # 数据抽稀间隔（m）

# 3) 宽度与间距控制参数（inch）
track_widths = [1.5, 0.5, 1.5, 2.0, 2.0, 2.0, 1.5, 2.0]  # 8列子图宽度
left_offset = 0.2                     # 曲线距离本列左边缘空白距离（本地x坐标）
group_spacing = 0.5                   # 同列两组曲线X轴之间相对间距

# 4) 标题与图例控制参数
title_spacing = 0.5                   # 总图名与组合图顶部距离（inch）
legend_spacing = 0.5                  # 底部图例与组合图底部距离（inch）
fig_height = 10                       # 画布整体高度（inch）

# 其他可选参数
excel_path = r"E:\urnotbai\博士\资料\筇竹寺\基础资料图\深度线型图\深度线型图.xlsx"
output_png = "depth_multitrack_plot.png"


# =========================
# 第二部分：中英文混排独立渲染函数（核心）
# =========================

def is_chinese_char(ch: str) -> bool:
    """判断字符是否属于常见中文Unicode区间。"""
    code = ord(ch)
    return (
        0x4E00 <= code <= 0x9FFF or      # CJK Unified Ideographs
        0x3400 <= code <= 0x4DBF or      # CJK Extension A
        0x20000 <= code <= 0x2A6DF or    # CJK Extension B
        0x2A700 <= code <= 0x2B73F or    # CJK Extension C
        0x2B740 <= code <= 0x2B81F or    # CJK Extension D
        0x2B820 <= code <= 0x2CEAF       # CJK Extension E/F
    )


def split_text_by_language(text: str):
    """
    将文本按“中文片段 / 非中文片段”分段。
    目的：为每段指定不同字体与字号。
    """
    if text is None:
        return []

    text = str(text)
    if text == "":
        return []

    parts = []
    current = text[0]
    current_is_zh = is_chinese_char(text[0])

    for ch in text[1:]:
        ch_is_zh = is_chinese_char(ch)
        if ch_is_zh == current_is_zh:
            current += ch
        else:
            parts.append((current, current_is_zh))
            current = ch
            current_is_zh = ch_is_zh
    parts.append((current, current_is_zh))
    return parts


def draw_mixed_text(
    container,
    x,
    y,
    text,
    coord='axes',
    ha='center',
    va='center',
    zorder=10,
):
    """
    在 Figure 或 Axes 上绘制“中英文混排独立渲染”文本。

    参数说明：
    - container: matplotlib.figure.Figure 或 matplotlib.axes.Axes
    - x, y: 文本锚点坐标
    - text: 目标字符串（可中英文混排）
    - coord:
        * 'axes'  : 以 ax.transAxes 为坐标系（0~1）
        * 'data'  : 以 ax.transData 为坐标系
        * 'figure': 以 fig.transFigure 为坐标系（0~1）
    - ha, va: 对齐方式（left/center/right, bottom/center/top）

    实现细节：
    1) 先按中文/非中文切片。
    2) 每个切片用 TextArea 创建一个小文本块，分别设置：
       - 中文 -> Microsoft YaHei, base_font_size_zh
       - 非中文(字母/数字/符号) -> Times New Roman, base_font_size_en
       且统一 font_weight=bold。
    3) 用 HPacker 沿水平方向拼接多个文本块，形成“视觉上一行完整字符串”。
    4) 用 AnnotationBbox 放到目标坐标系中。

    这样可以绕过 matplotlib 单个 Text 对象无法对同一字符串内部多字体样式的限制。
    """
    parts = split_text_by_language(text)
    if not parts:
        return None

    boxes = []
    for seg, is_zh in parts:
        props = {
            'fontname': font_zh if is_zh else font_en,
            'fontsize': base_font_size_zh if is_zh else base_font_size_en,
            'fontweight': font_weight,
            'color': 'black',
        }
        boxes.append(TextArea(seg, textprops=props))

    packed = HPacker(children=boxes, align='center', pad=0, sep=0)

    if hasattr(container, 'transAxes'):
        ax = container
        if coord == 'axes':
            xycoords = ax.transAxes
        elif coord == 'data':
            xycoords = ax.transData
        elif coord == 'figure':
            xycoords = ax.figure.transFigure
        else:
            raise ValueError("coord 必须是 'axes'/'data'/'figure'")
        draw_obj = ax
    else:
        fig = container
        if coord != 'figure':
            raise ValueError("当 container 为 Figure 时，coord 只能为 'figure'")
        xycoords = fig.transFigure
        draw_obj = fig

    ab = AnnotationBbox(
        packed,
        (x, y),
        xycoords=xycoords,
        frameon=False,
        box_alignment={
            ('left', 'bottom'): (0, 0), ('left', 'center'): (0, 0.5), ('left', 'top'): (0, 1),
            ('center', 'bottom'): (0.5, 0), ('center', 'center'): (0.5, 0.5), ('center', 'top'): (0.5, 1),
            ('right', 'bottom'): (1, 0), ('right', 'center'): (1, 0.5), ('right', 'top'): (1, 1),
        }[(ha, va)],
        pad=0.0,
        zorder=zorder,
    )

    if hasattr(draw_obj, 'add_artist'):
        draw_obj.add_artist(ab)
    return ab


# =========================
# 第三部分：数据读取与预处理
# =========================

def clean_columns(cols):
    """清理列名中的换行、连续空白、首尾空格。"""
    cleaned = []
    for c in cols:
        c = str(c).replace('\n', ' ')
        c = re.sub(r'\s+', ' ', c).strip()
        cleaned.append(c)
    return cleaned


def find_depth_column(df):
    """自动识别深度列，优先包含“深度”或depth关键字。"""
    priorities = ['深度', 'Depth', 'depth', 'DEPTH']
    for p in priorities:
        for c in df.columns:
            if p in c:
                return c
    return df.columns[0]


def sample_by_depth_interval(df, depth_col, interval):
    """
    按深度等距抽样：
    - 先排序
    - 再生成目标深度序列
    - 使用 merge_asof 找最近深度点
    """
    work = df.copy()
    work[depth_col] = pd.to_numeric(work[depth_col], errors='coerce')
    work = work.dropna(subset=[depth_col]).sort_values(depth_col).reset_index(drop=True)

    dmin, dmax = work[depth_col].min(), work[depth_col].max()
    target_depths = pd.DataFrame({depth_col: np.arange(dmin, dmax + 1e-9, interval)})

    sampled = pd.merge_asof(
        target_depths,
        work,
        on=depth_col,
        direction='nearest'
    )
    sampled = sampled.drop_duplicates(subset=[depth_col]).reset_index(drop=True)
    return sampled


# =========================
# 第四部分：绘图辅助函数
# =========================

def normalize_series(s):
    """将序列归一化到[0,1]，常数列时返回0.5。"""
    s = pd.to_numeric(s, errors='coerce')
    smin, smax = np.nanmin(s), np.nanmax(s)
    if np.isclose(smax, smin, equal_nan=False):
        return np.full_like(s, 0.5, dtype=float)
    return (s - smin) / (smax - smin)


def set_depth_axis(ax, depth_values, show_labels=False):
    """统一设置共享深度轴（反转），并用自定义混排绘制刻度数字。"""
    dmin, dmax = float(np.nanmin(depth_values)), float(np.nanmax(depth_values))
    ax.set_ylim(dmax, dmin)

    ticks = np.arange(np.floor(dmin / depth_tick_interval) * depth_tick_interval,
                      np.ceil(dmax / depth_tick_interval) * depth_tick_interval + depth_tick_interval / 2,
                      depth_tick_interval)
    ax.set_yticks(ticks)
    ax.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.6)

    # 隐藏默认刻度文本，改为手工绘制（保证英文数字字体规则）
    ax.set_yticklabels([])

    if show_labels:
        for t in ticks:
            # x=-0.02 让数字略在坐标轴左外侧
            draw_mixed_text(ax, -0.04, t, f"{t:g}", coord='data', ha='right', va='center')


def style_top_x_axis(ax):
    """顶部X轴、隐藏底部X轴。"""
    ax.xaxis.set_ticks_position('top')
    ax.xaxis.set_label_position('top')
    ax.tick_params(axis='x', top=True, bottom=False, labeltop=False, labelbottom=False)


def plot_single_curve(ax, depth, values, color, marker='o', lw=1.2, ms=3.5):
    """单组散点折线图。"""
    x_local = left_offset + normalize_series(values) * (1 - left_offset - 0.08)
    ax.plot(x_local, depth, color=color, marker=marker, linestyle='-', linewidth=lw, markersize=ms)
    ax.set_xlim(0, 1)
    return x_local


def plot_dual_curve(ax, depth, v1, v2, c1, c2, marker1='o', marker2='s', lw=1.2, ms=3.5):
    """
    同一列双组散点折线图：
    - 利用 group_spacing 将两组曲线放在同列内不同X子区域，避免重叠。
    """
    available = 1 - left_offset - 0.08
    gap = min(max(group_spacing, 0.0), available * 0.6)
    w = (available - gap) / 2
    start1 = left_offset
    start2 = left_offset + w + gap

    x1 = start1 + normalize_series(v1) * w
    x2 = start2 + normalize_series(v2) * w

    ax.plot(x1, depth, color=c1, marker=marker1, linestyle='-', linewidth=lw, markersize=ms)
    ax.plot(x2, depth, color=c2, marker=marker2, linestyle='-', linewidth=lw, markersize=ms)
    ax.set_xlim(0, 1)
    return x1, x2, (start1 + w / 2), (start2 + w / 2)


# =========================
# 第五部分：主绘图流程
# =========================

def main():
    # 1) 读取数据
    df = pd.read_excel(excel_path)
    df.columns = clean_columns(df.columns)

    depth_col = find_depth_column(df)
    sampled = sample_by_depth_interval(df, depth_col, data_sample_interval)

    depth = pd.to_numeric(sampled[depth_col], errors='coerce').values

    # 2) 建立画布：按 inch 计算总宽
    fig_width = sum(track_widths) + 0.8
    fig = plt.figure(figsize=(fig_width, fig_height), dpi=150)

    # 计算上下留白（将 inch 换成 figure 相对比例）
    top_margin = 1 - (title_spacing / fig_height)
    bottom_margin = (legend_spacing + 0.8) / fig_height

    gs = GridSpec(
        nrows=1,
        ncols=8,
        width_ratios=track_widths,
        left=0.04,
        right=0.99,
        top=top_margin,
        bottom=bottom_margin,
        wspace=0.08,
        figure=fig,
    )

    axes = []
    for i in range(8):
        ax = fig.add_subplot(gs[0, i], sharey=axes[0] if axes else None)
        style_top_x_axis(ax)
        axes.append(ax)

    # 3) 每列绘制
    # Track1 地层
    ax1 = axes[0]
    set_depth_axis(ax1, depth, show_labels=False)
    ax1.set_xlim(0, 1)

    # 这里以深度中位数人为划分“分层1/分层2”，可替换为实际分层顶底深度
    mid = np.nanmedian(depth)
    ax1.axhspan(np.nanmin(depth), mid, color='#f7d9c4', alpha=0.7)
    ax1.axhspan(mid, np.nanmax(depth), color='#d9e6f2', alpha=0.7)
    draw_mixed_text(ax1, 0.5, (np.nanmin(depth) + mid) / 2, '分层1', coord='data')
    draw_mixed_text(ax1, 0.5, (mid + np.nanmax(depth)) / 2, '分层2', coord='data')
    draw_mixed_text(ax1, 0.5, 1.06, '地层', coord='axes', ha='center', va='bottom')

    # Track2 深度（仅显示Y轴标签）
    ax2 = axes[1]
    set_depth_axis(ax2, depth, show_labels=True)
    ax2.set_xlim(0, 1)
    ax2.set_xticks([])
    draw_mixed_text(ax2, 0.5, 1.06, '深度(m)', coord='axes', ha='center', va='bottom')

    # Track3 TOC
    ax3 = axes[2]
    set_depth_axis(ax3, depth, show_labels=False)
    x_toc = plot_single_curve(ax3, depth, sampled['TOC（%）'], color='#1f77b4')
    draw_mixed_text(ax3, 0.5, 1.06, 'TOC(%)', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax3, 0.5, 1.01, 'TOC（%）', coord='axes', ha='center', va='bottom')

    # Track4 石英与长石
    ax4 = axes[3]
    set_depth_axis(ax4, depth, show_labels=False)
    _, _, c41, c42 = plot_dual_curve(ax4, depth, sampled['石英'], sampled['长石'], c1='#ff7f0e', c2='#2ca02c')
    draw_mixed_text(ax4, c41, 1.01, '石英', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax4, c42, 1.01, '长石', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax4, 0.5, 1.08, '石英与长石', coord='axes', ha='center', va='bottom')

    # Track5 碳酸盐和黏土矿物
    ax5 = axes[4]
    set_depth_axis(ax5, depth, show_labels=False)
    _, _, c51, c52 = plot_dual_curve(ax5, depth, sampled['碳酸盐矿物'], sampled['黏土矿物'], c1='#9467bd', c2='#8c564b')
    draw_mixed_text(ax5, c51, 1.01, '碳酸盐矿物', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax5, c52, 1.01, '黏土矿物', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax5, 0.5, 1.08, '碳酸盐和黏土矿物', coord='axes', ha='center', va='bottom')

    # Track6 密度
    ax6 = axes[5]
    set_depth_axis(ax6, depth, show_labels=False)
    _, _, c61, c62 = plot_dual_curve(ax6, depth, sampled['岩石密度g/cm^3'], sampled['颗粒密度g/cm^3'], c1='#d62728', c2='#17becf')
    draw_mixed_text(ax6, c61, 1.01, '岩石密度g/cm^3', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax6, c62, 1.01, '颗粒密度g/cm^3', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax6, 0.5, 1.08, '密度', coord='axes', ha='center', va='bottom')

    # Track7 孔隙度
    ax7 = axes[6]
    set_depth_axis(ax7, depth, show_labels=False)
    plot_single_curve(ax7, depth, sampled['孔隙度 %'], color='#bcbd22')
    draw_mixed_text(ax7, 0.5, 1.06, '孔隙度(%)', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax7, 0.5, 1.01, '孔隙度 %', coord='axes', ha='center', va='bottom')

    # Track8 饱和度
    ax8 = axes[7]
    set_depth_axis(ax8, depth, show_labels=False)
    _, _, c81, c82 = plot_dual_curve(ax8, depth, sampled['含水饱和度 %'], sampled['含气饱和度 %'], c1='#7f7f7f', c2='#e377c2')
    draw_mixed_text(ax8, c81, 1.01, '含水饱和度 %', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax8, c82, 1.01, '含气饱和度 %', coord='axes', ha='center', va='bottom')
    draw_mixed_text(ax8, 0.5, 1.08, '饱和度', coord='axes', ha='center', va='bottom')

    # 4) 统一边框与网格风格
    for ax in axes:
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
        ax.tick_params(axis='y', labelleft=False)

    # Track2显示深度刻度数字，其他隐藏
    ax2.tick_params(axis='y', length=3)

    # 5) 总图名（混排）
    draw_mixed_text(fig, 0.5, 1 - (title_spacing / fig_height) + 0.02,
                    '地质深度多跨度线型图 Geological Multi-track Depth Profile',
                    coord='figure', ha='center', va='bottom')

    # 6) 底部统一图例（手工绘制，支持混排）
    legend_ax = fig.add_axes([0.08, 0.02, 0.84, 0.08])
    legend_ax.axis('off')

    legend_items = [
        ('#1f77b4', 'o', 'TOC（%）'),
        ('#ff7f0e', 'o', '石英'),
        ('#2ca02c', 's', '长石'),
        ('#9467bd', 'o', '碳酸盐矿物'),
        ('#8c564b', 's', '黏土矿物'),
        ('#d62728', 'o', '岩石密度g/cm^3'),
        ('#17becf', 's', '颗粒密度g/cm^3'),
        ('#bcbd22', 'o', '孔隙度 %'),
        ('#7f7f7f', 'o', '含水饱和度 %'),
        ('#e377c2', 's', '含气饱和度 %'),
    ]

    n = len(legend_items)
    xs = np.linspace(0.02, 0.98, n)
    for x, (c, m, label) in zip(xs, legend_items):
        legend_ax.plot([x - 0.012, x + 0.012], [0.5, 0.5], color=c, linewidth=1.4, transform=legend_ax.transAxes)
        legend_ax.plot([x], [0.5], color=c, marker=m, markersize=4, transform=legend_ax.transAxes)
        draw_mixed_text(legend_ax, x + 0.017, 0.5, label, coord='axes', ha='left', va='center')

    # 7) 输出
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    plt.show()


if __name__ == '__main__':
    main()
