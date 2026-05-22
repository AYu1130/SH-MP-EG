"""
图4-4 消息路由处理流程图（优化版）
=====================================

纵向布局流程图，展示协议转换与消息路由模块的完整流程：
  设备标识 → 主题生成 → 消息发布

基于实际项目 mqtt_publisher.py、data_converter.py、config.py 实现，
展示"接收统一JSON → 主题路径生成 → MQTT发布"的三段式核心流程。

优化内容：
  - 使用规范流程图形状（椭圆、菱形、矩形、平行四边形）
  - 完整展示三段式流程：设备标识、主题生成、消息发布
  - 添加错误处理分支（格式错误、离线缓存等）
  - 优化布局与间距，无重叠遮挡
  - 清晰的箭头标注
  - 配色与Wi-Fi/BLE流程图保持一致
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse
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

# 配色方案 - 与Wi-Fi/BLE流程图保持一致
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
    fig, ax = plt.subplots(figsize=(9.5, 18.5), dpi=200)
    ax.set_xlim(-2.5, 10.0)
    ax.set_ylim(-1.0, 19.0)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # 标题
    ax.text(4.25, 18.3, "消息路由处理流程图",
            fontsize=FONT_SIZE_TITLE, color=COL_TEXT, weight="bold",
            ha="center", va="center")
    ax.text(4.25, 17.85, "(展示从接收原始数据到发布MQTT消息的完整处理流程)",
            fontsize=9.0, color=COL_TEXT_LIGHT,
            ha="center", va="center")

    # 三段式流程标注
    ax.text(4.25, 17.35, "【三段式核心流程】设备标识 → 主题生成 → 消息发布",
            fontsize=9.5, color=COL_ACCENT, weight="bold",
            ha="center", va="center", style="italic")

    # ==================== 第一段：设备标识 ====================
    # 阶段标题
    ax.text(2.5, 16.65, "第一阶段：设备标识", fontsize=10.0, color=COL_PRIMARY, weight="bold",
            ha="center", va="center", bbox=dict(boxstyle="round,pad=0.3", facecolor="#EBF8FF", edgecolor=COL_PRIMARY, alpha=0.8))

    # 1. 开始 - 椭圆
    draw_ellipse(ax, 4.25, 15.85, 2.0, 0.75, "开始", COL_SECONDARY)
    ax.text(4.25 + 1.6, 15.85, "on_message()回调",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 2. 接收统一JSON消息 - 平行四边形（输入）
    draw_parallelogram(ax, 4.25, 14.55, 3.2, 0.95, "接收统一JSON消息", COL_PRIMARY)

    # 3. 解析消息内容 - 矩形
    draw_rounded_box(ax, 4.25, 13.35, 3.0, 0.95, "解析消息内容", COL_PRIMARY,
                    desc="json.loads()解码\n提取各字段值")

    # 4. 消息格式验证 - 菱形判断
    draw_diamond(ax, 4.25, 11.95, 2.6, 1.15, "格式验证", COL_TERTIARY)
    ax.text(4.25 + 1.9, 11.95, "validate()校验\nSchema字段完整性",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 5. 提取device_id - 矩形
    draw_rounded_box(ax, 4.25, 10.55, 3.0, 0.95, "提取设备标识", COL_PRIMARY,
                    desc="message['device_id']\nmessage['device_type']")

    # 6. 查询设备注册表 - 矩形（橙色重点）
    draw_rounded_box(ax, 4.25, 9.25, 3.0, 0.95, "查询设备信息", COL_ACCENT,
                    desc="获取位置/类型\n确认设备合法性")

    # ==================== 第二段：主题生成 ====================
    # 阶段标题
    ax.text(2.5, 8.45, "第二阶段：主题生成", fontsize=10.0, color=COL_PRIMARY, weight="bold",
            ha="center", va="center", bbox=dict(boxstyle="round,pad=0.3", facecolor="#EBF8FF", edgecolor=COL_PRIMARY, alpha=0.8))

    # 7. 加载主题映射表 - 矩形
    draw_rounded_box(ax, 4.25, 7.55, 3.0, 0.95, "加载主题模板", COL_PRIMARY,
                    desc="cfg.topic_prefix\nsmarthome/v1")

    # 8. 生成MQTT主题路径 - 矩形（核心步骤）
    draw_rounded_box(ax, 4.25, 6.25, 3.2, 0.95, "生成主题路径", COL_ACCENT,
                    desc="telemetry_topic()\n{prefix}/telemetry/{type}/{id}")

    # 9. 序列化消息体 - 矩形
    draw_rounded_box(ax, 4.25, 4.95, 3.0, 0.95, "序列化消息体", COL_PRIMARY,
                    desc="to_json()转换\n紧凑JSON字符串")

    # ==================== 第三段：消息发布 ====================
    # 阶段标题
    ax.text(2.5, 4.15, "第三阶段：消息发布", fontsize=10.0, color=COL_PRIMARY, weight="bold",
            ha="center", va="center", bbox=dict(boxstyle="round,pad=0.3", facecolor="#EBF8FF", edgecolor=COL_PRIMARY, alpha=0.8))

    # 10. 检查连接状态 - 菱形判断
    draw_diamond(ax, 4.25, 3.05, 2.4, 1.05, "连接状态", COL_TERTIARY)
    ax.text(4.25 + 1.8, 3.05, "检查MQTT是否在线\n_connected.is_set()",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 11. 调用MQTT客户端 - 矩形
    draw_rounded_box(ax, 4.25, 1.75, 3.0, 0.95, "调用MQTT客户端", COL_PRIMARY,
                    desc="paho-mqtt.publish()\nQoS=1保证送达")

    # 12. 发布到MQTT主题 - 平行四边形（输出）
    draw_parallelogram(ax, 4.25, 0.6, 3.0, 0.9, "发布MQTT消息", COL_SECONDARY)
    ax.text(4.25 + 1.9, 0.6, "消息成功发送至\ntelemetry主题",
            fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
            ha="left", va="center")

    # 13. 结束 - 椭圆
    draw_ellipse(ax, 4.25, -0.55, 2.0, 0.7, "结束", COL_SECONDARY)

    # ==================== 绘制主流程箭头 ====================
    arrows = [
        (4.25, 15.85 - 0.375, 4.25, 14.55 + 0.475, "", COL_PRIMARY),
        (4.25, 14.55 - 0.475, 4.25, 13.35 + 0.475, "", COL_PRIMARY),
        (4.25, 13.35 - 0.475, 4.25, 11.95 + 0.575, "", COL_PRIMARY),
        (4.25, 11.95 - 0.575, 4.25, 10.55 + 0.475, "验证通过", COL_SECONDARY, "right"),
        (4.25, 10.55 - 0.475, 4.25, 9.25 + 0.475, "", COL_PRIMARY),
        (4.25, 9.25 - 0.475, 4.25, 7.55 + 0.475, "", COL_PRIMARY),
        (4.25, 7.55 - 0.475, 4.25, 6.25 + 0.475, "", COL_PRIMARY),
        (4.25, 6.25 - 0.475, 4.25, 4.95 + 0.475, "", COL_PRIMARY),
        (4.25, 4.95 - 0.475, 4.25, 3.05 + 0.525, "", COL_PRIMARY),
        (4.25, 3.05 - 0.525, 4.25, 1.75 + 0.475, "已连接", COL_SECONDARY, "right"),
        (4.25, 1.75 - 0.475, 4.25, 0.6 + 0.45, "", COL_PRIMARY),
        (4.25, 0.6 - 0.45, 4.25, -0.55 + 0.35, "发布成功", COL_SECONDARY, "right"),
    ]
    for a in arrows:
        if len(a) == 7:
            draw_arrow(ax, a[0], a[1], a[2], a[3], a[4], a[5], label_pos=a[6])
        else:
            draw_arrow(ax, a[0], a[1], a[2], a[3], a[4], a[5])

    # ==================== 错误处理分支 ====================

    # 错误分支1：格式验证失败 → 丢弃消息
    draw_error_branch_left(
        ax=ax,
        from_x=4.25 - 1.3, from_y=11.95,
        to_x=-0.5, to_y=10.55,
        label="格式错误",
        text="丢弃消息"
    )

    # 错误分支2：MQTT未连接 → 写入本地缓存
    draw_error_branch_left(
        ax=ax,
        from_x=4.25 - 1.2, from_y=3.05,
        to_x=-0.5, to_y=1.75,
        label="离线状态",
        text="写入缓存"
    )

    # ==================== 循环箭头 ====================

    # 数据接收循环（持续监听下一条消息）- 右侧
    draw_loop_arrow_right(
        ax=ax,
        start_x=4.25 + 1.5, start_y=-0.55,
        end_x=4.25 + 1.5, end_y=14.55,
        label="持续监听\n下一条消息",
        color=COL_SECONDARY
    )
    arrow = FancyArrowPatch(
        (4.25 + 1.5, 14.55), (4.25 + 1.5, 14.55 + 0.3),
        arrowstyle="-|>", color=COL_SECONDARY, linewidth=1.5,
        mutation_scale=12, zorder=4,
    )
    ax.add_patch(arrow)

    # 缓存重发循环（从写入缓存后回到连接状态检查）- 左侧小循环
    cache_loop_start_x = -0.5 + 1.1
    cache_loop_start_y = 1.75
    cache_loop_end_x = -0.5 + 1.1
    cache_loop_end_y = 3.05
    ax.plot([cache_loop_start_x, cache_loop_start_x + 0.8],
            [cache_loop_start_y, cache_loop_start_y],
            color=COL_ERROR, linewidth=1.5, linestyle="--", zorder=3)
    ax.plot([cache_loop_start_x + 0.8, cache_loop_start_x + 0.8],
            [cache_loop_start_y, cache_loop_end_y],
            color=COL_ERROR, linewidth=1.5, linestyle="--", zorder=3)
    arrow_cache = FancyArrowPatch(
        (cache_loop_start_x + 0.8, cache_loop_end_y - 0.01),
        (cache_loop_start_x + 0.81, cache_loop_end_y - 0.3),
        arrowstyle="-|>", color=COL_ERROR, linewidth=1.5,
        mutation_scale=10, zorder=4,
    )
    ax.add_patch(arrow_cache)
    ax.text(cache_loop_start_x + 0.9, (cache_loop_start_y + cache_loop_end_y) / 2, "重试重发",
            fontsize=FONT_SIZE_DESC - 0.8, color=COL_ERROR,
            ha="left", va="center", zorder=7, style="italic")

    # ==================== 图例说明 ====================
    legend_y = 17.0
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
    ax.text(4.25, -1.2,
            "注：主流程从顶部开始向下，展示'设备标识→主题生成→消息发布'三段式核心流程，左侧为错误处理分支，右侧为数据接收循环",
            fontsize=7.5, color=COL_TEXT_LIGHT, ha="center", va="center", style="italic")

    plt.tight_layout(pad=0.3)
    output_path = "图4-4_消息路由处理流程图.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {output_path}")

    # 保存SVG格式（可在Visio中编辑）
    svg_path = output_path.replace('.png', '.svg')
    fig.savefig(svg_path, format='svg', bbox_inches="tight", facecolor="white")
    print(f"Saved -> {svg_path}")


if __name__ == "__main__":
    main()
