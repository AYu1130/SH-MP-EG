"""
图5-1 测试环境网络拓扑图
========================
展示树莓派网关、ESP32 Wi-Fi节点、STM32 BLE节点、测试上位机的连接关系。
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

# ==================== 中文字体配置 ====================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 配色方案 ====================
COL_GATEWAY = "#1783FF"      # 网关-蓝色
COL_WIFI = "#F0884D"         # Wi-Fi节点-橙色
COL_BLE = "#D580FF"          # BLE节点-紫色
COL_PC = "#00C9C9"           # 上位机-青色
COL_ROUTER = "#60C42D"       # 路由器-绿色
COL_MQTT = "#FF4D4F"         # MQTT Broker-红色
COL_TEXT_DARK = "#1F2937"    # 深色文字
COL_TEXT_LIGHT = "#6B7280"   # 浅色文字
COL_BG = "#F8FAFC"           # 背景色

FONT_SIZE_TITLE = 16
FONT_SIZE_NODE = 11
FONT_SIZE_DESC = 9
FONT_SIZE_SMALL = 8

# ==================== 绘图函数 ====================
def draw_device_box(ax, x, y, w, h, title, color, symbol_text, details=None):
    """绘制设备节点框"""
    # 背景框
    box = FancyBboxPatch((x - w/2, y - h/2), width=w, height=h,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=color, edgecolor=color,
                         linewidth=2, alpha=0.12)
    ax.add_patch(box)
    box_border = FancyBboxPatch((x - w/2, y - h/2), width=w, height=h,
                                boxstyle="round,pad=0.05,rounding_size=0.2",
                                facecolor="none", edgecolor=color,
                                linewidth=2)
    ax.add_patch(box_border)

    # 图标区域（纯矢量圆形 + 文字缩写，不使用 emoji）
    icon_size = 0.52
    icon_y = y + h * 0.16
    icon = Circle((x, icon_y), icon_size / 2, facecolor=color, edgecolor=color,
                  linewidth=2, alpha=0.25)
    ax.add_patch(icon)
    ax.text(x, icon_y, symbol_text, fontsize=10, color=color,
            ha="center", va="center", weight="bold")

    # 标题
    ax.text(x, y - h*0.15, title, fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
            ha="center", va="center", weight="bold")

    # 详细信息
    if details:
        ax.text(x, y - h*0.35, details, fontsize=FONT_SIZE_SMALL, color=COL_TEXT_LIGHT,
                ha="center", va="center", linespacing=1.2)

def draw_router(ax, x, y, w, h):
    """绘制路由器图标"""
    # 路由器主体
    box = FancyBboxPatch((x - w/2, y - h/2), width=w, height=h,
                         boxstyle="round,pad=0.05,rounding_size=0.15",
                         facecolor=COL_ROUTER, edgecolor=COL_ROUTER,
                         linewidth=2, alpha=0.15)
    ax.add_patch(box)
    box_border = FancyBboxPatch((x - w/2, y - h/2), width=w, height=h,
                                boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor="none", edgecolor=COL_ROUTER,
                                linewidth=2)
    ax.add_patch(box_border)

    # 路由器标识（纯文字）
    ax.text(x, y + h * 0.1, "RT", fontsize=11, color=COL_ROUTER,
            ha="center", va="center")

    ax.text(x, y - h*0.2, "无线路由器", fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
            ha="center", va="center", weight="bold")
    ax.text(x, y - h*0.4, "2.4GHz AP", fontsize=FONT_SIZE_SMALL, color=COL_TEXT_LIGHT,
            ha="center", va="center")

def draw_arrow(ax, start_x, start_y, end_x, end_y, color, label=None, style="-", lw=2):
    """绘制连接箭头"""
    arrow = FancyArrowPatch((start_x, start_y), (end_x, end_y),
                            arrowstyle="-|>", mutation_scale=16,
                            color=color, linewidth=lw, linestyle=style)
    ax.add_patch(arrow)

    if label:
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        ax.text(mid_x, mid_y + 0.25, label, fontsize=FONT_SIZE_SMALL,
                color=color, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                         edgecolor="none", alpha=0.9))

def draw_double_arrow(ax, start_x, start_y, end_x, end_y, color, label=None):
    """绘制双向箭头"""
    # 正向箭头
    arrow1 = FancyArrowPatch((start_x, start_y), (end_x, end_y),
                             arrowstyle="-|>", mutation_scale=14,
                             color=color, linewidth=2)
    ax.add_patch(arrow1)
    # 反向箭头
    arrow2 = FancyArrowPatch((end_x, end_y), (start_x, start_y),
                             arrowstyle="-|>", mutation_scale=14,
                             color=color, linewidth=2)
    ax.add_patch(arrow2)

    if label:
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        ax.text(mid_x, mid_y + 0.25, label, fontsize=FONT_SIZE_SMALL,
                color=color, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                         edgecolor="none", alpha=0.9))

def draw_double_dashed_arrow(ax, start_x, start_y, end_x, end_y, color, label=None):
    """绘制双向虚线箭头"""
    arrow1 = FancyArrowPatch((start_x, start_y), (end_x, end_y),
                             arrowstyle="-|>", mutation_scale=14,
                             color=color, linewidth=2, linestyle="--")
    ax.add_patch(arrow1)
    arrow2 = FancyArrowPatch((end_x, end_y), (start_x, start_y),
                             arrowstyle="-|>", mutation_scale=14,
                             color=color, linewidth=2, linestyle="--")
    ax.add_patch(arrow2)

    if label:
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        ax.text(mid_x, mid_y + 0.2, label, fontsize=FONT_SIZE_SMALL,
                color=color, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                         edgecolor="none", alpha=0.9))

def draw_dashed_line(ax, start_x, start_y, end_x, end_y, color, label=None):
    """绘制虚线连接"""
    ax.plot([start_x, end_x], [start_y, end_y], color=color,
            linewidth=2, linestyle="--", alpha=0.7)

    if label:
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        ax.text(mid_x, mid_y + 0.2, label, fontsize=FONT_SIZE_SMALL,
                color=color, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white",
                         edgecolor="none", alpha=0.9))

# ==================== 主绘图逻辑 ====================
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(-1, 15)
ax.set_ylim(-1, 11)
ax.set_aspect("equal")
ax.axis("off")

# 背景
bg = FancyBboxPatch((-0.5, -0.5), width=15, height=11,
                    boxstyle="round,pad=0.1,rounding_size=0.3",
                    facecolor=COL_BG, edgecolor="#E2E8F0",
                    linewidth=1, alpha=0.5)
ax.add_patch(bg)

# 标题
ax.text(7, 10.5, "测试环境网络拓扑图",
        fontsize=FONT_SIZE_TITLE, color=COL_TEXT_DARK,
        ha="center", va="center", weight="bold")
ax.text(7, 10.0, "（展示树莓派网关、ESP32节点、STM32节点、测试上位机的连接关系）",
        fontsize=10, color=COL_TEXT_LIGHT, ha="center", va="center")

# ==================== 设备节点 ====================

# 中心：无线路由器
draw_router(ax, 7.0, 7.3, 2.4, 1.5)

# 左上：测试上位机（笔记本电脑）
draw_device_box(ax, 2.5, 7.3, 3.0, 1.7, "测试上位机", COL_PC, "PC",
                "笔记本电脑\n运行测试脚本和数据分析")

# 右上：MQTT Broker / EMQX
draw_device_box(ax, 11.5, 7.3, 3.0, 1.7, "MQTT Broker", COL_MQTT, "MQ",
                "EMQX 5.0.8\nDocker容器化部署")

# 左下：树莓派网关（中心设备）
draw_device_box(ax, 5.3, 3.2, 3.4, 2.0, "树莓派网关", COL_GATEWAY, "GW",
                "Raspberry Pi 4B 4GB\nRaspberry Pi OS 64bit\n运行网关核心软件")

# 中下：ESP32-S3 Wi-Fi节点（下移，避免与网关视觉重叠）
draw_device_box(ax, 7.4, 0.95, 2.8, 1.6, "Wi-Fi节点", COL_WIFI, "WF",
                "ESP32-S3 DevKitC-1\nDHT11温湿度传感器\n模拟Wi-Fi传感器")

# 右下：STM32F103 + HM-10 BLE节点
draw_device_box(ax, 10.8, 3.2, 3.2, 2.0, "BLE节点", COL_BLE, "BT",
                "STM32F103 + HM-10\nBH1750光照传感器\n模拟BLE传感器")

# ==================== 连接线 ====================

# 1. 路由器 ↔ 测试上位机（有线/无线）
draw_double_arrow(ax, 4.1, 7.3, 5.8, 7.3, COL_PC,
                  label="Wi-Fi/LAN")

# 2. 路由器 ↔ MQTT Broker（有线）
draw_double_arrow(ax, 8.2, 7.3, 9.9, 7.3, COL_MQTT,
                  label="LAN 1883端口")

# 3. 路由器 ↔ 树莓派网关（有线）
draw_double_arrow(ax, 6.3, 6.4, 5.8, 4.4, COL_GATEWAY,
                  label="以太网")

# 4. ESP32 → 树莓派网关（Wi-Fi 2.4GHz）
draw_double_dashed_arrow(ax, 7.3, 1.75, 6.95, 2.45, COL_WIFI,
                         label="Wi-Fi 2.4GHz")

# 5. 树莓派网关 ↔ BLE节点（蓝牙）
draw_double_dashed_arrow(ax, 7.1, 3.2, 9.1, 3.2, COL_BLE,
                         label="BLE")

# 6. 测试上位机 → 树莓派（SSH调试）
draw_arrow(ax, 2.6, 6.3, 4.0, 4.2, COL_PC,
           label="SSH调试", style="--")

# ==================== 图例 ====================
legend_x = 0.5
legend_y = 2.4

ax.text(legend_x, legend_y + 0.3, "连接类型", fontsize=10,
        color=COL_TEXT_DARK, weight="bold", ha="left")

legend_items = [
    ("以太网/有线", COL_GATEWAY, "-"),
    ("Wi-Fi无线", COL_WIFI, "--"),
    ("蓝牙BLE", COL_BLE, "--"),
    ("双向通信", COL_PC, "-"),
]

for i, (label, color, style) in enumerate(legend_items):
    y_pos = legend_y - 0.5 - i * 0.5
    ax.plot([legend_x, legend_x + 0.6], [y_pos, y_pos],
            color=color, linewidth=2, linestyle=style)
    if style == "-":
        ax.annotate("", xy=(legend_x + 0.6, y_pos),
                   xytext=(legend_x + 0.3, y_pos),
                   arrowprops=dict(arrowstyle="-|>", color=color, lw=2))
        # 双向箭头第二个
        ax.annotate("", xy=(legend_x, y_pos),
                   xytext=(legend_x + 0.3, y_pos),
                   arrowprops=dict(arrowstyle="-|>", color=color, lw=2))
    ax.text(legend_x + 0.9, y_pos, label, fontsize=8, color=COL_TEXT_DARK,
            ha="left", va="center")

# ==================== 环境信息框 ====================
info_box = FancyBboxPatch((11.0, 9.0), width=3.5, height=1.2,
                          boxstyle="round,pad=0.1,rounding_size=0.15",
                          facecolor="white", edgecolor=COL_TEXT_LIGHT,
                          linewidth=1, alpha=0.8)
ax.add_patch(info_box)

ax.text(12.75, 9.7, "测试环境配置", fontsize=10, color=COL_TEXT_DARK,
        ha="center", va="center", weight="bold")
ax.text(12.75, 9.3, "Python 3.9 | SQLite 3 | Locust\nmatplotlib | EMQX 5.0.8 | Node-RED 3.0",
        fontsize=FONT_SIZE_SMALL, color=COL_TEXT_LIGHT,
        ha="center", va="center", linespacing=1.3)

# 底部注释
ax.text(7, -0.35, "注：树莓派4B作为核心网关，通过多协议适配实现Wi-Fi和BLE设备的统一接入与管理",
        fontsize=8.5, color=COL_TEXT_LIGHT, ha="center", va="center",
        style="italic")

plt.tight_layout()
output_path = r"图5-1_测试环境网络拓扑图.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight",
            facecolor="white", edgecolor="none")
print(f"Saved -> {output_path}")

emf_path = output_path.replace('.png', '.emf')
try:
    plt.savefig(emf_path, format='emf', bbox_inches="tight", facecolor="white")
    print(f"Saved -> {emf_path}")
except Exception as emf_error:
    print(f"[WARN] EMF生成失败: {str(emf_error)}")

svg_path = output_path.replace('.png', '.svg')
try:
    plt.savefig(svg_path, format='svg', bbox_inches="tight",
                facecolor="white", edgecolor="none")
    print(f"Saved -> {svg_path}")
except Exception as svg_error:
    print(f"[WARN] SVG生成失败: {str(svg_error)}")

plt.close()
