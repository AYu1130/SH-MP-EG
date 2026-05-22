"""
图4-1 软件系统模块调用关系图
============================

根据用户需求，展示五大核心模块间的数据流向和调用关系：
  1. 协议适配与数据收发模块 (Protocol Adapter & Data I/O)
  2. 统一数据传输模型模块 (Unified Data Model)
  3. 协议转换与消息路由模块 (Protocol Conversion & Message Routing)
  4. 本地自治联动模块 (Local Autonomous Linkage)
  5. 设备管理与状态管理模块 (Device & State Management)

设计要点：
  - 中心辐射式布局，核心模块居中，其他模块环绕
  - 使用箭头清晰展示数据流向和调用关系
  - 配色方案参考用户提供的参考图片风格
  - 画幅方正 (~12×12 in)，适合论文排版
  - 优化文字排版，避免重叠遮挡
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
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
    plt.rcParams["font.size"] = 9  # 全局基础字号


setup_chinese_font()

# 配色方案 - 参考用户提供的架构图风格
COL_PRIMARY = "#2C5AA0"    # 深蓝色 - 主色调
COL_SECONDARY = "#1A8C5A"  # 绿色 - 上行数据
COL_TERTIARY = "#A24A88"   # 紫色 - 下行控制
COL_ACCENT = "#C28A4A"     # 橙色 - 核心模块
COL_BG_LIGHT = "#F5F7FA"   # 浅灰背景
COL_TEXT = "#1F3550"       # 深色文字
COL_TEXT_LIGHT = "#5A6D80" # 浅色文字

# 字体大小配置 - 层次分明
FONT_SIZE_TITLE = 14       # 图表标题
FONT_SIZE_MODULE = 10.5    # 模块标题
FONT_SIZE_MODULE_CORE = 11.5  # 核心模块标题
FONT_SIZE_DESC = 8.2       # 模块说明文字
FONT_SIZE_ICON = 11        # 模块图标
FONT_SIZE_ARROW_LABEL = 7.2 # 箭头标签
FONT_SIZE_LEGEND = 8.5     # 图例文字
FONT_SIZE_FOOTNOTE = 8.0   # 底部说明文字


def draw_module_box(ax, cx, cy, w, h, title, desc_lines, color, icon=None, is_core=False):
    """绘制模块盒：圆角矩形 + 标题 + 说明文字"""
    x = cx - w / 2
    y = cy - h / 2

    # 核心模块使用不同样式
    if is_core:
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.03,rounding_size=0.12",
            linewidth=2.0,
            edgecolor=color,
            facecolor="#FEFBF5",
            zorder=5,
        )
    else:
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.10",
            linewidth=1.5,
            edgecolor=color,
            facecolor="white",
            zorder=4,
        )
    ax.add_patch(box)

    # 顶部图标和标题区域
    title_h = 0.58  # 标题栏高度增加
    if icon:
        icon_size = 0.38
        icon_box = FancyBboxPatch(
            (x + 0.18, y + h - title_h / 2 - icon_size / 2 - 0.06),
            icon_size, icon_size,
            boxstyle="round,pad=0.0,rounding_size=0.08",
            linewidth=0,
            facecolor=color,
            zorder=6,
        )
        ax.add_patch(icon_box)
        ax.text(
            x + 0.18 + icon_size / 2,
            y + h - title_h / 2 - 0.06,
            icon,
            fontsize=FONT_SIZE_ICON, color="white", weight="bold",
            ha="center", va="center", zorder=7,
        )

    title_x = x + 0.72 if icon else cx
    title_ha = "left" if icon else "center"
    title_font_size = FONT_SIZE_MODULE_CORE if is_core else FONT_SIZE_MODULE
    ax.text(
        title_x, y + h - title_h / 2 - 0.06, title,
        fontsize=title_font_size, color=color, weight="bold",
        ha=title_ha, va="center", zorder=7,
    )

    # 分隔线
    sep_y = y + h - title_h - 0.10  # 增加与标题的间距
    ax.plot(
        [x + 0.18, x + w - 0.18], [sep_y, sep_y],
        color=color, linewidth=0.8, alpha=0.4, zorder=5,
    )

    # 说明文字区域 - 垂直居中摆放
    n = len(desc_lines)
    desc_top = sep_y - 0.10  # 与分隔线的间距
    desc_bot = y + 0.10      # 底部边距

    if n > 0:
        # 合适的行间距
        line_spacing = 0.28
        available_height = desc_top - desc_bot

        # 计算内容区域中心位置
        desc_center_y = (desc_top + desc_bot) / 2

        # 计算起始位置，使三行内容垂直居中
        if n > 1:
            total_content_height = (n - 1) * line_spacing
            start_y = desc_center_y + total_content_height / 2
        else:
            start_y = desc_center_y

        ys = [start_y - line_spacing * i for i in range(n)]

        for yy, line in zip(ys, desc_lines):
            ax.text(
                cx, yy, line,
                fontsize=FONT_SIZE_DESC, color=COL_TEXT,
                ha="center", va="center", zorder=6,
                linespacing=1.0,
            )


def draw_data_flow(ax, x1, y1, x2, y2, label, color, style="->", linewidth=2.0):
    """绘制数据流箭头 - 优化标签位置，避免重叠"""
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style,
        mutation_scale=14,  # 减小箭头尺寸
        linewidth=linewidth,
        color=color,
        zorder=3,
    )
    ax.add_patch(arrow)

    # 标签位置 - 根据箭头方向动态调整
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    # 计算箭头方向，确定偏移量
    dx = x2 - x1
    dy = y2 - y1
    dist = (dx**2 + dy**2)**0.5

    if dist > 0:
        nx = dx / dist
        ny = dy / dist
    else:
        nx, ny = 0, 0

    # 垂直于箭头方向偏移标签，避免与箭头重叠
    offset_perp_x = -ny * 0.35  # 垂直偏移
    offset_perp_y = nx * 0.35

    label_x = mid_x + offset_perp_x
    label_y = mid_y + offset_perp_y

    ax.text(
        label_x, label_y, label,
        fontsize=FONT_SIZE_ARROW_LABEL, color=color, weight="bold",
        ha="center", va="center", zorder=4,
        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor=color, linewidth=0.5),
    )


def main():
    # 紧凑画布尺寸，减少留白
    fig, ax = plt.subplots(figsize=(11, 11), dpi=180)
    ax.set_xlim(0.0, 13.8)
    ax.set_ylim(0.0, 13.8)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # 标题 - 移除"图4-1"标号，紧凑布局
    ax.text(
        6.9, 13.0,
        "软件系统模块调用关系图",
        fontsize=FONT_SIZE_TITLE, color=COL_TEXT, weight="bold",
        ha="center", va="center",
    )

    # 副标题说明 - 紧跟标题下方
    ax.text(
        6.9, 12.5,
        "(展示各模块间的数据流向和调用关系)",
        fontsize=9.0, color=COL_TEXT_LIGHT,
        ha="center", va="center",
    )

    # 五大核心模块位置布局（紧凑中心辐射式）
    MODULES = {
        # 中心核心模块
        "core": {
            "name": "协议转换与消息路由",
            "icon": "R",
            "color": COL_ACCENT,
            "cx": 6.9,
            "cy": 7.2,
            "w": 3.8,
            "h": 2.9,
            "desc": ["protocol_converter.py", "MQTT Topic 路由", "统一JSON格式转换"],
            "is_core": True,
        },
        # 左上 - 协议适配与数据收发
        "adapter": {
            "name": "协议适配与数据收发",
            "icon": "A",
            "color": COL_PRIMARY,
            "cx": 2.8,
            "cy": 10.5,
            "w": 3.0,
            "h": 2.1,
            "desc": ["wifi_receiver.py", "ble_receiver.py", "原始数据收发"],
        },
        # 右上 - 统一数据传输模型
        "unified": {
            "name": "统一数据传输模型",
            "icon": "U",
            "color": COL_SECONDARY,
            "cx": 11.0,
            "cy": 10.5,
            "w": 3.0,
            "h": 2.1,
            "desc": ["data_converter.py", "JSON Schema校验", "标准化字段映射"],
        },
        # 右下 - 本地自治联动
        "local": {
            "name": "本地自治联动",
            "icon": "L",
            "color": COL_TERTIARY,
            "cx": 11.0,
            "cy": 4.0,
            "w": 3.0,
            "h": 2.1,
            "desc": ["Node-RED规则引擎", "SQLite离线缓存", "断网续传机制"],
        },
        # 左下 - 设备管理与状态管理
        "device": {
            "name": "设备管理与状态管理",
            "icon": "D",
            "color": COL_PRIMARY,
            "cx": 2.8,
            "cy": 4.0,
            "w": 3.0,
            "h": 2.1,
            "desc": ["admin_routes.py", "Web管理界面", "设备状态监控"],
        },
    }

    # 绘制所有模块
    for key, mod in MODULES.items():
        draw_module_box(
            ax,
            mod["cx"], mod["cy"],
            mod["w"], mod["h"],
            mod["name"],
            mod["desc"],
            mod["color"],
            mod.get("icon"),
            mod.get("is_core", False),
        )

    # 绘制数据流（调用关系）
    # 1. 协议适配 -> 协议转换（原始数据）
    draw_data_flow(
        ax,
        MODULES["adapter"]["cx"] + MODULES["adapter"]["w"]/2 - 0.15,
        MODULES["adapter"]["cy"] - MODULES["adapter"]["h"]/2 + 0.4,
        MODULES["core"]["cx"] - MODULES["core"]["w"]/2 + 0.4,
        MODULES["core"]["cy"] + MODULES["core"]["h"]/2 - 0.4,
        "原始数据",
        COL_SECONDARY,
        "->",
    )

    # 2. 协议转换 -> 统一数据模型（格式校验）
    draw_data_flow(
        ax,
        MODULES["core"]["cx"] + MODULES["core"]["w"]/2 - 0.15,
        MODULES["core"]["cy"] + MODULES["core"]["h"]/2 - 0.4,
        MODULES["unified"]["cx"] - MODULES["unified"]["w"]/2 + 0.15,
        MODULES["unified"]["cy"] - MODULES["unified"]["h"]/2 + 0.4,
        "统一JSON",
        COL_SECONDARY,
        "->",
    )

    # 3. 统一数据模型 -> 协议转换（校验结果）
    draw_data_flow(
        ax,
        MODULES["unified"]["cx"] - MODULES["unified"]["w"]/2 + 0.15,
        MODULES["unified"]["cy"] + MODULES["unified"]["h"]/2 - 0.4,
        MODULES["core"]["cx"] + MODULES["core"]["w"]/2 - 0.4,
        MODULES["core"]["cy"] + MODULES["core"]["h"]/2 - 0.4,
        "校验反馈",
        COL_TEXT_LIGHT,
        "<-",
    )

    # 4. 协议转换 -> 本地自治联动（数据下发）
    draw_data_flow(
        ax,
        MODULES["core"]["cx"] + MODULES["core"]["w"]/2 - 0.15,
        MODULES["core"]["cy"] - MODULES["core"]["h"]/2 + 0.4,
        MODULES["local"]["cx"] - MODULES["local"]["w"]/2 + 0.15,
        MODULES["local"]["cy"] + MODULES["local"]["h"]/2 - 0.4,
        "传感数据",
        COL_SECONDARY,
        "->",
    )

    # 5. 本地自治联动 -> 协议转换（联动指令）
    draw_data_flow(
        ax,
        MODULES["local"]["cx"] - MODULES["local"]["w"]/2 + 0.15,
        MODULES["local"]["cy"] - MODULES["local"]["h"]/2 + 0.4,
        MODULES["core"]["cx"] + MODULES["core"]["w"]/2 - 0.4,
        MODULES["core"]["cy"] - MODULES["core"]["h"]/2 + 0.4,
        "联动指令",
        COL_TERTIARY,
        "<-",
    )

    # 6. 设备管理 -> 协议转换（配置更新）
    draw_data_flow(
        ax,
        MODULES["device"]["cx"] + MODULES["device"]["w"]/2 - 0.15,
        MODULES["device"]["cy"] + MODULES["device"]["h"]/2 - 0.4,
        MODULES["core"]["cx"] - MODULES["core"]["w"]/2 + 0.4,
        MODULES["core"]["cy"] - MODULES["core"]["h"]/2 + 0.4,
        "配置更新",
        COL_TERTIARY,
        "->",
    )

    # 7. 协议转换 -> 协议适配（控制指令）
    draw_data_flow(
        ax,
        MODULES["core"]["cx"] - MODULES["core"]["w"]/2 + 0.15,
        MODULES["core"]["cy"] + MODULES["core"]["h"]/2 - 0.4,
        MODULES["adapter"]["cx"] + MODULES["adapter"]["w"]/2 - 0.15,
        MODULES["adapter"]["cy"] + MODULES["adapter"]["h"]/2 - 0.4,
        "控制指令",
        COL_TERTIARY,
        "<-",
    )

    # 8. 协议转换 -> 设备管理（状态上报）
    draw_data_flow(
        ax,
        MODULES["core"]["cx"] - MODULES["core"]["w"]/2 + 0.15,
        MODULES["core"]["cy"] - MODULES["core"]["h"]/2 + 0.4,
        MODULES["device"]["cx"] + MODULES["device"]["w"]/2 - 0.15,
        MODULES["device"]["cy"] + MODULES["device"]["h"]/2 - 0.4,
        "状态上报",
        COL_SECONDARY,
        "->",
    )

    # 图例区域 - 箭头图例放在左侧，避免与设备管理模块重叠
    legend_start_y = 1.8
    legend_x = 0.8

    # 上行数据图例
    ax.plot([legend_x, legend_x + 0.6], [legend_start_y, legend_start_y],
            color=COL_SECONDARY, linewidth=3)
    ax.annotate("", xy=(legend_x + 0.75, legend_start_y), xytext=(legend_x + 0.6, legend_start_y),
                arrowprops=dict(arrowstyle="-|>", color=COL_SECONDARY, lw=3))
    ax.text(legend_x + 0.95, legend_start_y, "上行数据 (传感数据上报)",
            fontsize=FONT_SIZE_LEGEND, color=COL_SECONDARY, ha="left", va="center", weight="bold")

    # 下行控制图例
    legend_y = legend_start_y - 0.48
    ax.plot([legend_x, legend_x + 0.6], [legend_y, legend_y],
            color=COL_TERTIARY, linewidth=3)
    ax.annotate("", xy=(legend_x + 0.75, legend_y), xytext=(legend_x + 0.6, legend_y),
                arrowprops=dict(arrowstyle="-|>", color=COL_TERTIARY, lw=3))
    ax.text(legend_x + 0.95, legend_y, "下行控制 (命令下发)",
            fontsize=FONT_SIZE_LEGEND, color=COL_TERTIARY, ha="left", va="center", weight="bold")

    # 箭头注释放在箭头图例下方
    footer_y = legend_y - 0.52
    ax.text(
        legend_x, footer_y,
        "注：箭头方向表示数据流向，绿色为上行数据，紫色为下行控制指令",
        fontsize=7.2, color=COL_TEXT_LIGHT, ha="left", va="center",
        style="italic",
    )

    # 模块功能说明 - 移至右侧，与图例垂直分离
    desc_start_y = legend_start_y
    desc_x = 6.4

    ax.text(desc_x, desc_start_y, "模块功能说明：",
            fontsize=FONT_SIZE_LEGEND, color=COL_TEXT, weight="bold", ha="left", va="center")

    desc_items = [
        ("A", "协议适配与数据收发：Wi-Fi/BLE原始数据接收与发送"),
        ("U", "统一数据传输模型：JSON Schema标准化与字段校验"),
        ("R", "协议转换与消息路由：核心模块，协议转换与MQTT路由"),
        ("L", "本地自治联动：Node-RED规则编排与离线缓存"),
        ("D", "设备管理与状态管理：Web管理界面与设备监控"),
    ]

    # 紧凑行间距
    line_spacing = 0.40
    for i, (icon, desc) in enumerate(desc_items):
        ax.text(desc_x, desc_start_y - line_spacing * (i + 1), f"{icon} - {desc}",
                fontsize=FONT_SIZE_FOOTNOTE, color=COL_TEXT_LIGHT, ha="left", va="center")

    plt.tight_layout(pad=0.2)
    output_path = "图4-1_软件系统模块调用关系图.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {output_path}")

    # 保存SVG格式（可在Visio中编辑）
    svg_path = output_path.replace('.png', '.svg')
    fig.savefig(svg_path, format='svg', bbox_inches="tight", facecolor="white")
    print(f"Saved -> {svg_path}")


if __name__ == "__main__":
    main()
