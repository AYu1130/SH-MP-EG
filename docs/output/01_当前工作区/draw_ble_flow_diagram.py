"""
图4-4 BLE终端接入模块流程图（优化版）
=====================================

纵向布局流程图，展示BLE终端接入的完整流程：
  设备扫描 → 设备匹配 → GATT连接 → 身份验证 → 订阅通知 → 参数配置 → 数据接收 → 协议解析 → JSON封装

基于实际项目 ble_receiver.py 实现，展示Bleak库的异步扫描、GATT连接、Notification订阅等关键环节。

优化内容：
  - 使用规范流程图形状（椭圆、菱形、矩形、平行四边形）
  - 添加错误处理分支（扫描失败、连接失败、数据异常）
  - 优化布局与间距，无重叠遮挡
  - 清晰的箭头标注
  - 配色与Wi-Fi流程图保持一致
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Arc
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

# 配色方案 - 与Wi-Fi流程图保持一致
COL_PRIMARY = "#2C5AA0"    # 深蓝色 - 主色调
COL_SECONDARY = "#1A8C5A"  # 绿色 - 成功/完成
COL_TERTIARY = "#A24A88"   # 紫色 - 处理中/判断
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


def draw_loop_arrow_right(ax, start_x, start_y, end_x, end_y, label=None, color=COL_SECONDARY):
    """绘制右侧循环箭头（带圆弧）"""
    path_x = [start_x, start_x + 1.5, start_x + 1.5, end_x]
    path_y = [start_y, start_y, end_y, end_y]
    ax.plot(path_x, path_y, color=color, linewidth=1.5, linestyle="--", zorder=3)
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


def draw_error_branch_left(ax, from_x, from_y, to_x, to_y, label, text):
    """绘制左侧错误处理分支"""
    x_mid = to_x - 1.0
    ax.plot([from_x, x_mid], [from_y, from_y], color=COL_ERROR, linewidth=1.5, zorder=3)
    ax.plot([x_mid, x_mid], [from_y, to_y], color=COL_ERROR, linewidth=1.5, zorder=3)
    arrow = FancyArrowPatch(
        (x_mid, to_y), (to_x, to_y),
        arrowstyle="-|>", color=COL_ERROR, linewidth=1.5,
        mutation_scale=12, zorder=4,
    )
    ax.add_patch(arrow)
    ax.text((from_x + x_mid) / 2, from_y + 0.15, label,
            fontsize=FONT_SIZE_DESC - 0.5, color=COL_ERROR,
            ha="center", va="bottom", zorder=7)
    draw_ellipse(ax, to_x + 1.1, to_y, 2.2, 0.8, text, COL_ERROR)


def main():
    fig, ax = plt.subplots(figsize=(9.5, 16.0), dpi=200)
    ax.set_xlim(-2.5, 10.0)
    ax.set_ylim(-1.0, 17.0)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # 标题
    ax.text(4.25, 16.3, "BLE终端接入模块流程图",
            fontsize=FONT_SIZE_TITLE, color=COL_TEXT, weight="bold",
            ha="center", va="center")
    ax.text(4.25, 15.85, "(展示Bleak异步扫描与GATT连接的完整流程)",
            fontsize=9.0, color=COL_TEXT_LIGHT,
            ha="center", va="center")

    # ==================== 主流程节点 ====================

    # 1. 开始 - 椭圆
    draw_ellipse(ax, 4.25, 14.8, 2.0, 0.8, "开始", COL_SECONDARY)
    ax.text(4.25 + 1.6, 14.8, "BleReceiver.start()",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 2. 设备扫描 - 矩形
    draw_rounded_box(ax, 4.25, 13.4, 3.0, 1.0, "设备扫描", COL_PRIMARY,
                    desc="BleakScanner.discover()\n周期性广播扫描")

    # 3. 设备匹配 - 菱形判断
    draw_diamond(ax, 4.25, 11.8, 2.6, 1.2, "设备匹配", COL_TERTIARY)
    ax.text(4.25 + 1.9, 11.8, "_match()按名称前缀过滤\n避免重复连接",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 4. GATT连接 - 矩形（橙色重点）
    draw_rounded_box(ax, 4.25, 10.2, 3.0, 1.0, "GATT连接", COL_ACCENT,
                    desc="client.connect(timeout=10s)\n建立BLE链路层连接")

    # 5. 连接验证 - 菱形判断
    draw_diamond(ax, 4.25, 8.6, 2.4, 1.2, "连接验证", COL_TERTIARY)
    ax.text(4.25 + 1.8, 8.6, "检查is_connected状态\n确认GATT会话有效",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 6. 订阅通知 - 矩形
    draw_rounded_box(ax, 4.25, 7.0, 3.0, 1.0, "订阅通知", COL_PRIMARY,
                    desc="start_notify(char_uuid)\n注册Notification回调")

    # 7. 参数配置 - 矩形
    draw_rounded_box(ax, 4.25, 5.6, 3.0, 1.0, "参数配置", COL_PRIMARY,
                    desc="发送sync_ns同步命令\n初始化时间基准")

    # 8. 数据接收 - 矩形
    draw_rounded_box(ax, 4.25, 4.2, 3.0, 1.0, "数据接收", COL_PRIMARY,
                    desc="_on_notify()回调\n接收原始字节流")

    # 9. 数据缓冲 - 菱形判断
    draw_diamond(ax, 4.25, 2.8, 2.4, 1.1, "数据缓冲", COL_TERTIARY)
    ax.text(4.25 + 1.8, 2.8, "按\\n切分完整帧\nHM-10 20B分片重组",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 10. JSON封装 - 平行四边形（输出）
    draw_parallelogram(ax, 4.25, 1.4, 3.0, 0.95, "JSON封装", COL_SECONDARY)
    ax.text(4.25 + 1.9, 1.4, "normalize_ble()转换\n统一JSON Schema校验",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 11. 消息分发 - 矩形
    draw_rounded_box(ax, 4.25, 0.05, 3.0, 1.0, "消息分发", COL_SECONDARY,
                    desc="on_message()回调\n交由上层路由分发")

    # ==================== 绘制主流程箭头 ====================
    arrows = [
        (4.25, 14.8 - 0.4, 4.25, 13.4 + 0.5, "", COL_PRIMARY),
        (4.25, 13.4 - 0.5, 4.25, 11.8 + 0.6, "", COL_PRIMARY),
        (4.25, 11.8 - 0.6, 4.25, 10.2 + 0.5, "匹配成功", COL_SECONDARY, "right"),
        (4.25, 10.2 - 0.5, 4.25, 8.6 + 0.6, "", COL_PRIMARY),
        (4.25, 8.6 - 0.6, 4.25, 7.0 + 0.5, "连接成功", COL_SECONDARY, "right"),
        (4.25, 7.0 - 0.5, 4.25, 5.6 + 0.5, "", COL_PRIMARY),
        (4.25, 5.6 - 0.5, 4.25, 4.2 + 0.5, "", COL_PRIMARY),
        (4.25, 4.2 - 0.5, 4.25, 2.8 + 0.55, "", COL_PRIMARY),
        (4.25, 2.8 - 0.55, 4.25, 1.4 + 0.475, "帧完整", COL_SECONDARY, "right"),
        (4.25, 1.4 - 0.475, 4.25, 0.05 + 0.5, "", COL_PRIMARY),
    ]
    for a in arrows:
        if len(a) == 7:
            draw_arrow(ax, a[0], a[1], a[2], a[3], a[4], a[5], label_pos=a[6])
        else:
            draw_arrow(ax, a[0], a[1], a[2], a[3], a[4], a[5])

    # ==================== 错误处理分支 ====================

    # 错误分支1：设备匹配失败 → 跳过此设备（向左下）
    draw_error_branch_left(
        ax=ax,
        from_x=4.25 - 1.3, from_y=11.8,
        to_x=-0.5, to_y=10.2,
        label="不匹配",
        text="跳过此设备"
    )

    # 错误分支2：连接验证失败 → 断开重连（向左下）
    draw_error_branch_left(
        ax=ax,
        from_x=4.25 - 1.2, from_y=8.6,
        to_x=-0.5, to_y=6.5,
        label="连接失败",
        text="断开重连"
    )

    # 错误分支3：数据缓冲异常 → 等待续传（向左下）
    draw_error_branch_left(
        ax=ax,
        from_x=4.25 - 1.2, from_y=2.8,
        to_x=-0.5, to_y=1.4,
        label="帧不完整",
        text="等待续传"
    )

    # ==================== 循环箭头 ====================

    # 数据接收循环（持续监听Notification）- 右侧
    draw_loop_arrow_right(
        ax=ax,
        start_x=4.25 + 1.5, start_y=0.05,
        end_x=4.25 + 1.5, end_y=4.2,
        label="持续监听\n下一条通知",
        color=COL_SECONDARY
    )
    arrow = FancyArrowPatch(
        (4.25 + 1.5, 4.2), (4.25 + 1.5, 4.2 + 0.3),
        arrowstyle="-|>", color=COL_SECONDARY, linewidth=1.5,
        mutation_scale=12, zorder=4,
    )
    ax.add_patch(arrow)

    # ==================== 图例说明 ====================
    legend_y = 15.0
    legend_x = 8.0
    ax.text(legend_x, legend_y, "图例", fontsize=9.5, color=COL_TEXT, weight="bold",
            ha="left", va="center")

    # 成功箭头
    arrow_green = FancyArrowPatch((legend_x, legend_y - 0.65), (legend_x + 0.7, legend_y - 0.65),
                                   arrowstyle="-|>", color=COL_SECONDARY, linewidth=1.5, mutation_scale=10, zorder=5)
    ax.add_patch(arrow_green)
    ax.text(legend_x + 0.9, legend_y - 0.65, "成功路径", fontsize=8.0, color=COL_SECONDARY,
            ha="left", va="center")

    # 错误箭头
    arrow_red = FancyArrowPatch((legend_x, legend_y - 1.35), (legend_x + 0.7, legend_y - 1.35),
                                 arrowstyle="-|>", color=COL_ERROR, linewidth=1.5, mutation_scale=10, zorder=5)
    ax.add_patch(arrow_red)
    ax.text(legend_x + 0.9, legend_y - 1.35, "错误路径", fontsize=8.0, color=COL_ERROR,
            ha="left", va="center")

    # 循环箭头
    ax.plot([legend_x, legend_x + 0.7], [legend_y - 2.05, legend_y - 2.05],
            color=COL_SECONDARY, linewidth=1.5, linestyle="--", zorder=3)
    ax.text(legend_x + 0.9, legend_y - 2.05, "数据循环", fontsize=8.0, color=COL_SECONDARY,
            ha="left", va="center")

    # 底部说明
    ax.text(4.25, -0.6,
            "注：主流程从顶部开始向下，左侧为错误处理分支，右侧为数据接收循环，展示Bleak异步BLE通信的完整生命周期",
            fontsize=7.5, color=COL_TEXT_LIGHT, ha="center", va="center", style="italic")

    plt.tight_layout(pad=0.3)
    output_path = "图4-4_BLE终端接入模块流程图.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {output_path}")

    # 保存SVG格式（可在Visio中编辑）
    svg_path = output_path.replace('.png', '.svg')
    fig.savefig(svg_path, format='svg', bbox_inches="tight", facecolor="white")
    print(f"Saved -> {svg_path}")


if __name__ == "__main__":
    main()
