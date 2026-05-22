"""
图4-2 Wi-Fi终端接入模块流程图（优化版）
=====================================

纵向布局流程图，展示Wi-Fi终端接入的完整流程：
  Socket监听 → 设备连接 → 身份验证 → 数据接收 → 协议解析 → JSON封装

优化内容：
  - 使用规范流程图形状（椭圆、菱形、矩形、平行四边形）
  - 添加错误处理分支（身份验证失败、数据解析失败）
  - 优化布局与间距，无重叠遮挡
  - 清晰的箭头标注
  - 配色与系统架构图保持一致
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Wedge
import platform


def setup_chinese_font():
    system = platform.system()
    if system == "Windows":
        candidates = ["Microsoft YaHei", "SimHei", "SimSun"]
    elif system == "Darwin":
        candidates = ["PingFang SC", "Hiragino Sans GB", "Heiti SC"]
    else:
        candidates = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for n in candidates:
        if n in available:
            plt.rcParams["font.family"] = n
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 9


setup_chinese_font()

# 配色方案 - 与系统架构图保持一致
COL_PRIMARY = "#2C5AA0"    # 深蓝色 - 主色调
COL_SECONDARY = "#1A8C5A"  # 绿色 - 成功/完成
COL_TERTIARY = "#A24A88"   # 紫色 - 处理中
COL_ACCENT = "#C28A4A"     # 橙色 - 核心/重点
COL_ERROR = "#C53030"      # 红色 - 错误/失败
COL_BG_LIGHT = "#F5F7FA"   # 浅灰背景
COL_TEXT = "#2D3748"       # 深灰文字
COL_TEXT_LIGHT = "#718096" # 浅灰文字
COL_BORDER = "#4A5568"     # 边框色

# 字体大小
FONT_SIZE_TITLE = 14
FONT_SIZE_NODE = 10.5
FONT_SIZE_DESC = 8.5
FONT_SIZE_FOOTNOTE = 8.0


def draw_ellipse(ax, cx, cy, w, h, text, color):
    """绘制椭圆 - 开始/结束节点"""
    # 使用两个Wedge和一个矩形模拟椭圆
    from matplotlib.patches import Ellipse
    ellipse = Ellipse((cx, cy), w, h,
                     facecolor="#F0FFF4", edgecolor=color, linewidth=1.5, zorder=5)
    ax.add_patch(ellipse)
    ax.text(cx, cy, text, fontsize=FONT_SIZE_NODE, color=color, weight="bold",
            ha="center", va="center", zorder=6)


def draw_diamond(ax, cx, cy, w, h, text, color):
    """绘制菱形 - 判断/决策节点"""
    diamond = plt.Polygon([
        [cx, cy + h / 2],
        [cx + w / 2, cy],
        [cx, cy - h / 2],
        [cx - w / 2, cy],
    ], facecolor="#FFF5F5", edgecolor=color, linewidth=1.5, zorder=5)
    ax.add_patch(diamond)
    ax.text(cx, cy, text, fontsize=FONT_SIZE_NODE, color=color, weight="bold",
            ha="center", va="center", zorder=6)


def draw_parallelogram(ax, cx, cy, w, h, text, color):
    """绘制平行四边形 - 输入/输出节点"""
    # 平行四边形顶点
    skew = 0.3
    para = plt.Polygon([
        [cx - w / 2 + skew, cy + h / 2],
        [cx + w / 2 + skew, cy + h / 2],
        [cx + w / 2 - skew, cy - h / 2],
        [cx - w / 2 - skew, cy - h / 2],
    ], facecolor="#EBF8FF", edgecolor=color, linewidth=1.5, zorder=5)
    ax.add_patch(para)
    ax.text(cx, cy, text, fontsize=FONT_SIZE_NODE, color=color, weight="bold",
            ha="center", va="center", zorder=6)


def draw_rounded_box(ax, cx, cy, w, h, text, color, desc=None):
    """绘制圆角矩形 - 处理节点"""
    x = cx - w / 2
    y = cy - h / 2
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.15",
        linewidth=1.5,
        edgecolor=color,
        facecolor="white",
        zorder=5,
    )
    ax.add_patch(box)
    ax.text(cx, cy, text, fontsize=FONT_SIZE_NODE, color=COL_TEXT, weight="bold",
            ha="center", va="center", zorder=6)
    if desc:
        desc_lines = desc.split("\n")
        for i, line in enumerate(desc_lines):
            offset_y = (len(desc_lines) / 2 - i - 0.5) * 0.3
            ax.text(cx + w / 2 + 0.45, cy + offset_y, line,
                   fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
                   ha="left", va="center", zorder=6)


def draw_arrow(ax, x1, y1, x2, y2, label=None, color=COL_PRIMARY, style="-|>", label_pos="right"):
    """绘制带标签的箭头"""
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        color=color,
        linewidth=2.0,
        mutation_scale=15,
        zorder=4,
    )
    ax.add_patch(arrow)

    if label:
        # 根据label_pos确定标签位置
        if label_pos == "right":
            mid_x = (x1 + x2) / 2 + 0.4
            mid_y = (y1 + y2) / 2
            ha = "left"
        elif label_pos == "left":
            mid_x = (x1 + x2) / 2 - 0.4
            mid_y = (y1 + y2) / 2
            ha = "right"
        elif label_pos == "bottom":
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2 - 0.25
            ha = "center"
        else:
            mid_x = (x1 + x2) / 2 + 0.4
            mid_y = (y1 + y2) / 2
            ha = "left"
        ax.text(mid_x, mid_y, label, fontsize=FONT_SIZE_DESC - 0.5, color=color,
                ha=ha, va="center", zorder=7, style="italic")


def draw_loop_arrow(ax, start_x, start_y, end_x, end_y, label=None, color=COL_SECONDARY):
    """绘制循环箭头（带圆弧）"""
    # 先画圆弧路径
    path_x = [start_x, start_x + 1.5, start_x + 1.5, end_x]
    path_y = [start_y, start_y, end_y, end_y]
    ax.plot(path_x, path_y, color=color, linewidth=1.5, linestyle="--", zorder=3)
    # 最后一段箭头
    arrow = FancyArrowPatch(
        (start_x + 1.5, end_y), (end_x, end_y),
        arrowstyle="-|>", color=color, linewidth=1.5,
        mutation_scale=12, zorder=4,
    )
    ax.add_patch(arrow)
    if label:
        ax.text(start_x + 1.5 + 0.1, (start_y + end_y) / 2, label,
                fontsize=FONT_SIZE_DESC - 0.5, color=color,
                ha="left", va="center", zorder=7, style="italic")


def draw_error_branch(ax, from_x, from_y, to_x, to_y, label, text):
    """绘制错误处理分支"""
    # 先水平向左
    x_mid = to_x - 1.2
    ax.plot([from_x, x_mid], [from_y, from_y], color=COL_ERROR, linewidth=1.5, zorder=3)
    # 再垂直向下
    ax.plot([x_mid, x_mid], [from_y, to_y], color=COL_ERROR, linewidth=1.5, zorder=3)
    # 最后水平向右
    arrow = FancyArrowPatch(
        (x_mid, to_y), (to_x, to_y),
        arrowstyle="-|>", color=COL_ERROR, linewidth=1.5,
        mutation_scale=12, zorder=4,
    )
    ax.add_patch(arrow)
    # 标签
    ax.text((from_x + x_mid) / 2, from_y + 0.15, label,
            fontsize=FONT_SIZE_DESC - 0.5, color=COL_ERROR,
            ha="center", va="bottom", zorder=7)
    # 错误处理节点
    draw_ellipse(ax, to_x + 1.2, to_y, 2.2, 0.8, text, COL_ERROR)


def main():
    # 画布设置 - 纵向布局，比例协调，增加宽度给错误分支
    fig, ax = plt.subplots(figsize=(9.5, 13.5), dpi=200)
    ax.set_xlim(-2.0, 10.0)
    ax.set_ylim(-1.0, 15.0)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # 标题
    ax.text(4.25, 14.3, "Wi-Fi终端接入模块流程图",
            fontsize=FONT_SIZE_TITLE, color=COL_TEXT, weight="bold",
            ha="center", va="center")
    ax.text(4.25, 13.8, "(展示TCP长连接接入与数据处理的完整流程)",
            fontsize=9.0, color=COL_TEXT_LIGHT,
            ha="center", va="center")

    # 主流程节点
    # 1. 开始 - 椭圆
    draw_ellipse(ax, 4.25, 12.7, 2.0, 0.8, "开始", COL_SECONDARY)
    ax.text(4.25 + 1.6, 12.7, "WifiReceiver.start()",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 2. Socket监听 - 矩形
    draw_rounded_box(ax, 4.25, 11.3, 3.0, 1.0, "Socket监听", COL_PRIMARY,
                    desc="asyncio.start_server()\n监听 :9000 端口")

    # 3. 等待设备连接 - 矩形
    draw_rounded_box(ax, 4.25, 9.9, 3.0, 1.0, "等待设备连接", COL_PRIMARY,
                    desc="阻塞等待TCP连接")

    # 4. 设备连接建立 - 矩形（橙色重点）
    draw_rounded_box(ax, 4.25, 8.5, 3.2, 1.0, "设备连接建立", COL_ACCENT,
                    desc="_handle_tcp_client()\n创建独立处理协程")

    # 5. 身份验证 - 菱形判断
    draw_diamond(ax, 4.25, 6.9, 2.6, 1.3, "身份验证", COL_TERTIARY)
    ax.text(4.25 + 1.9, 6.9, "验证device_id合法性\nregister_writer登记",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 6. 数据接收 - 矩形
    draw_rounded_box(ax, 4.25, 5.3, 3.0, 1.0, "数据接收", COL_PRIMARY,
                    desc="reader.readline()\n按行读取JSON报文")

    # 7. 协议解析 - 菱形判断
    draw_diamond(ax, 4.25, 3.7, 2.4, 1.2, "协议解析", COL_TERTIARY)
    ax.text(4.25 + 1.8, 3.7, "json.loads()解码\n字段映射与提取",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 8. JSON封装 - 平行四边形（输出）
    draw_parallelogram(ax, 4.25, 2.1, 3.0, 1.0, "JSON封装", COL_SECONDARY)
    ax.text(4.25 + 1.9, 2.1, "normalize_wifi()转换\n统一JSON Schema校验",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 9. 上报消息队列 - 矩形
    draw_rounded_box(ax, 4.25, 0.7, 3.0, 1.0, "上报消息队列", COL_SECONDARY,
                    desc="on_message()回调\n交由上层路由分发")

    # 绘制主流程箭头
    arrows = [
        (4.25, 12.7 - 0.4, 4.25, 11.3 + 0.5, "", COL_PRIMARY),
        (4.25, 11.3 - 0.5, 4.25, 9.9 + 0.5, "", COL_PRIMARY),
        (4.25, 9.9 - 0.5, 4.25, 8.5 + 0.5, "", COL_PRIMARY),
        (4.25, 8.5 - 0.5, 4.25, 6.9 + 0.65, "连接成功", COL_SECONDARY, "right"),
        (4.25, 6.9 - 0.65, 4.25, 5.3 + 0.5, "验证通过", COL_SECONDARY, "right"),
        (4.25, 5.3 - 0.5, 4.25, 3.7 + 0.6, "", COL_PRIMARY),
        (4.25, 3.7 - 0.6, 4.25, 2.1 + 0.5, "解析成功", COL_SECONDARY, "right"),
        (4.25, 2.1 - 0.5, 4.25, 0.7 + 0.5, "", COL_PRIMARY),
    ]
    for a in arrows:
        if len(a) == 7:
            draw_arrow(ax, a[0], a[1], a[2], a[3], a[4], a[5], label_pos=a[6])
        else:
            draw_arrow(ax, a[0], a[1], a[2], a[3], a[4], a[5])

    # 错误处理分支1：身份验证失败
    draw_error_branch(
        ax=ax,
        from_x=4.25 - 1.3, from_y=6.9,
        to_x=-0.2, to_y=4.4,
        label="验证失败",
        text="关闭连接"
    )

    # 错误处理分支2：协议解析失败
    draw_error_branch(
        ax=ax,
        from_x=4.25 - 1.2, from_y=3.7,
        to_x=-0.2, to_y=1.8,
        label="解析失败",
        text="跳过此条数据"
    )

    # 数据接收循环箭头（从"上报消息队列"后回到"数据接收"）
    draw_loop_arrow(
        ax=ax,
        start_x=4.25 + 1.5, start_y=0.7,
        end_x=4.25 + 1.5, end_y=5.3,
        label="持续监听\n下一条数据",
        color=COL_SECONDARY
    )
    # 最后接上数据接收
    arrow = FancyArrowPatch(
        (4.25 + 1.5, 5.3), (4.25 + 1.5, 5.3 + 0.3),
        arrowstyle="-|>", color=COL_SECONDARY, linewidth=1.5,
        mutation_scale=12, zorder=4,
    )
    ax.add_patch(arrow)

    # 图例说明 - 只保留箭头图例，放在右上角
    legend_y = 12.8
    legend_x = 8.0
    ax.text(legend_x, legend_y, "图例", fontsize=9.5, color=COL_TEXT, weight="bold",
            ha="left", va="center")
    # 成功箭头
    arrow_green = FancyArrowPatch((legend_x, legend_y - 0.6), (legend_x + 0.7, legend_y - 0.6),
                                   arrowstyle="-|>", color=COL_SECONDARY, linewidth=1.5, mutation_scale=10, zorder=5)
    ax.add_patch(arrow_green)
    ax.text(legend_x + 0.9, legend_y - 0.6, "成功路径", fontsize=8.0, color=COL_SECONDARY,
            ha="left", va="center")
    # 错误箭头
    arrow_red = FancyArrowPatch((legend_x, legend_y - 1.3), (legend_x + 0.7, legend_y - 1.3),
                                 arrowstyle="-|>", color=COL_ERROR, linewidth=1.5, mutation_scale=10, zorder=5)
    ax.add_patch(arrow_red)
    ax.text(legend_x + 0.9, legend_y - 1.3, "错误路径", fontsize=8.0, color=COL_ERROR,
            ha="left", va="center")
    # 循环箭头
    ax.plot([legend_x, legend_x + 0.7], [legend_y - 2.0, legend_y - 2.0],
            color=COL_SECONDARY, linewidth=1.5, linestyle="--", zorder=3)
    ax.text(legend_x + 0.9, legend_y - 2.0, "数据循环", fontsize=8.0, color=COL_SECONDARY,
            ha="left", va="center")

    # 底部说明
    ax.text(4.25, -0.5,
            "注：主流程从顶部开始向下，左侧为错误处理分支，右侧为数据接收循环",
            fontsize=7.5, color=COL_TEXT_LIGHT, ha="center", va="center", style="italic")

    plt.tight_layout(pad=0.3)
    output_path = "图4-2_Wi-Fi终端接入模块流程图.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {output_path}")

    # 保存SVG格式（可在Visio中编辑）
    svg_path = output_path.replace('.png', '.svg')
    fig.savefig(svg_path, format='svg', bbox_inches="tight", facecolor="white")
    print(f"Saved -> {svg_path}")


if __name__ == "__main__":
    main()
