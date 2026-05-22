"""
图4-6 离线缓存与补传机制流程图
============================
基于SQLite的离线缓存机制：网络断开时写入缓存，网络恢复后自动补发。
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Ellipse, Polygon
import numpy as np

# ==================== 中文字体配置 ====================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 配色方案 ====================
COL_PRIMARY = "#1783FF"      # 主色调-蓝色
COL_SECONDARY = "#00C9C9"   # 辅助色-青色
COL_ACCENT = "#F0884D"      # 强调色-橙色
COL_TERTIARY = "#D580FF"    # 判断节点-紫色
COL_SUCCESS = "#60C42D"     # 成功/开始-绿色
COL_ERROR = "#FF4D4F"       # 错误/异常-红色
COL_TEXT_DARK = "#1F2937"   # 深色文字
COL_TEXT_LIGHT = "#6B7280"  # 浅色文字/描述
COL_BG_LIGHT = "#EBF8FF"    # 浅蓝背景
COL_BG_GREEN = "#F0FDF4"    # 浅绿背景
COL_BG_ORANGE = "#FFF7ED"   # 浅橙背景

FONT_SIZE_TITLE = 16        # 标题字号
FONT_SIZE_NODE = 11         # 节点主标题字号
FONT_SIZE_DESC = 9          # 描述字号
FONT_WEIGHT_BOLD = "bold"

# ==================== 绘图函数 ====================
def draw_ellipse(ax, x, y, w, h, text, color):
    """绘制椭圆形（开始/结束）"""
    ellipse = Ellipse((x, y), width=w, height=h,
                      facecolor=color, edgecolor=color,
                      linewidth=2.5, alpha=0.15)
    ax.add_patch(ellipse)
    ellipse_border = Ellipse((x, y), width=w, height=h,
                             facecolor="none", edgecolor=color,
                             linewidth=2.5)
    ax.add_patch(ellipse_border)
    ax.text(x, y, text, fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
            ha="center", va="center", weight=FONT_WEIGHT_BOLD)

def draw_rounded_box(ax, x, y, w, h, text, color, desc=None):
    """绘制圆角矩形（处理步骤）"""
    box = FancyBboxPatch((x - w/2, y - h/2), width=w, height=h,
                         boxstyle="round,pad=0.05,rounding_size=0.15",
                         facecolor=color, edgecolor=color,
                         linewidth=2, alpha=0.12)
    ax.add_patch(box)
    box_border = FancyBboxPatch((x - w/2, y - h/2), width=w, height=h,
                                boxstyle="round,pad=0.05,rounding_size=0.15",
                                facecolor="none", edgecolor=color,
                                linewidth=2)
    ax.add_patch(box_border)

    if desc:
        ax.text(x, y + h*0.12, text, fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
                ha="center", va="center", weight=FONT_WEIGHT_BOLD)
        ax.text(x, y - h*0.12, desc, fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
                ha="center", va="center", linespacing=1.3)
    else:
        ax.text(x, y, text, fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
                ha="center", va="center", weight=FONT_WEIGHT_BOLD)

def draw_diamond(ax, x, y, w, h, text, color):
    """绘制菱形（判断节点）"""
    diamond = Polygon([(x, y + h/2), (x + w/2, y),
                       (x, y - h/2), (x - w/2, y)],
                      closed=True, facecolor=color, edgecolor=color,
                      linewidth=2, alpha=0.15)
    ax.add_patch(diamond)
    diamond_border = Polygon([(x, y + h/2), (x + w/2, y),
                              (x, y - h/2), (x - w/2, y)],
                             closed=True, facecolor="none", edgecolor=color,
                             linewidth=2)
    ax.add_patch(diamond_border)
    ax.text(x, y, text, fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
            ha="center", va="center", weight=FONT_WEIGHT_BOLD)

def draw_parallelogram(ax, x, y, w, h, text, color):
    """绘制平行四边形（数据输入/输出）"""
    offset = 0.25
    para = Polygon([(x - w/2 + offset, y + h/2), (x + w/2 + offset, y + h/2),
                    (x + w/2 - offset, y - h/2), (x - w/2 - offset, y - h/2)],
                   closed=True, facecolor=color, edgecolor=color,
                   linewidth=2, alpha=0.12)
    ax.add_patch(para)
    para_border = Polygon([(x - w/2 + offset, y + h/2), (x + w/2 + offset, y + h/2),
                           (x + w/2 - offset, y - h/2), (x - w/2 - offset, y - h/2)],
                          closed=True, facecolor="none", edgecolor=color,
                          linewidth=2)
    ax.add_patch(para_border)
    ax.text(x, y, text, fontsize=FONT_SIZE_NODE, color=COL_TEXT_DARK,
            ha="center", va="center", weight=FONT_WEIGHT_BOLD)

def draw_arrow(ax, start_x, start_y, end_x, end_y, color=COL_PRIMARY,
               label=None, label_pos=None, style="-"):
    """绘制箭头"""
    arrow = FancyArrowPatch((start_x, start_y), (end_x, end_y),
                            arrowstyle="-|>", mutation_scale=18,
                            color=color, linewidth=2,
                            linestyle=style)
    ax.add_patch(arrow)

    if label and label_pos:
        mid_x = (start_x + end_x) / 2 + label_pos[0]
        mid_y = (start_y + end_y) / 2 + label_pos[1]
        ax.text(mid_x, mid_y, label, fontsize=9, color=color,
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                         edgecolor="none", alpha=0.9))

def draw_error_branch_left(ax, from_x, from_y, to_x, to_y, label, text):
    """绘制左侧错误分支"""
    draw_arrow(ax, from_x, from_y, to_x + 1.2, to_y, color=COL_ERROR,
               label=label, label_pos=(0.35, 0.25))
    draw_ellipse(ax, to_x, to_y, 2.4, 0.85, text, COL_ERROR)

def draw_loop_arrow_right(ax, start_x, start_y, end_x, end_y, label, color, use_curve=False):
    """绘制右侧循环箭头，支持直虚线和拐弯箭头"""
    if use_curve:
        # 使用拐弯箭头：向右→向上→向左
        mid_x = start_x + 1.2
        # 第一段：水平向右
        arrow1 = FancyArrowPatch((start_x, start_y), (mid_x, start_y),
                                arrowstyle="-|>", mutation_scale=18,
                                color=color, linewidth=2, linestyle="--")
        ax.add_patch(arrow1)
        # 第二段：垂直向上
        arrow2 = FancyArrowPatch((mid_x, start_y), (mid_x, end_y),
                                arrowstyle="-|>", mutation_scale=18,
                                color=color, linewidth=2, linestyle="--")
        ax.add_patch(arrow2)
        # 第三段：水平向左
        arrow3 = FancyArrowPatch((mid_x, end_y), (end_x, end_y),
                                arrowstyle="-|>", mutation_scale=18,
                                color=color, linewidth=2, linestyle="--")
        ax.add_patch(arrow3)
        # 标签放在垂直段右侧
        mid_y = (start_y + end_y) / 2
        ax.text(mid_x + 0.35, mid_y, label, fontsize=9, color=color,
                ha="left", va="center", rotation=90,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                         edgecolor="none", alpha=0.9))
    else:
        # 直虚线箭头
        arrow = FancyArrowPatch((start_x, start_y), (end_x, end_y),
                                arrowstyle="-|>", mutation_scale=18,
                                color=color, linewidth=2, linestyle="--")
        ax.add_patch(arrow)
        mid_y = (start_y + end_y) / 2
        ax.text(start_x + 0.45, mid_y, label, fontsize=9, color=color,
                ha="left", va="center", rotation=90,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                         edgecolor="none", alpha=0.9))

# ==================== 主绘图逻辑 ====================
fig, ax = plt.subplots(figsize=(11, 16))
ax.set_xlim(-2, 10)
ax.set_ylim(-1, 18)
ax.set_aspect("equal")
ax.axis("off")

# 标题
ax.text(4.25, 17.2, "离线缓存与补传机制流程图",
        fontsize=FONT_SIZE_TITLE, color=COL_TEXT_DARK,
        ha="center", va="center", weight=FONT_WEIGHT_BOLD)
ax.text(4.25, 16.65, "（展示网络断开时缓存消息、网络恢复后补发的完整流程）",
        fontsize=10, color=COL_TEXT_LIGHT, ha="center", va="center")

# ==================== 流程节点 ====================

# 1. 开始 - 椭圆形
draw_ellipse(ax, 4.25, 15.6, 2.6, 0.95, "开始", COL_SUCCESS)

# 2. 接收待发送消息 - 平行四边形
draw_parallelogram(ax, 4.25, 14.2, 3.2, 0.95, "接收待发送消息", COL_PRIMARY)
ax.text(6.8, 14.2, "publish()调用\ntopic+payload+qos",
        fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
        ha="left", va="center")

# 3. 检测MQTT连接状态 - 菱形判断
draw_diamond(ax, 4.25, 12.7, 2.6, 1.2, "在线检测", COL_TERTIARY)
ax.text(6.75, 12.7, "_connected.is_set()\n检查MQTT连接状态",
        fontsize=FONT_SIZE_DESC, color=COL_TEXT_LIGHT,
        ha="left", va="center")

# 4a. 在线分支：发布消息到MQTT (右侧偏移)
draw_rounded_box(ax, 7.8, 10.8, 3.0, 0.95, "发布到MQTT Broker", COL_SUCCESS,
                desc="mqtt_client.publish()\nQoS=1保证送达")

# 5. 结束 - 椭圆形 (右侧)
draw_ellipse(ax, 7.8, 9.3, 2.6, 0.95, "结束", COL_SUCCESS)

# 4b. 离线分支：写入SQLite缓存 (主流程继续)
draw_rounded_box(ax, 4.25, 10.8, 3.0, 0.95, "写入本地缓存", COL_ACCENT,
                desc="cache.push()\nSQLite持久化存储")

# 6. 等待网络恢复
draw_rounded_box(ax, 4.25, 9.35, 3.0, 0.95, "等待网络恢复", COL_SECONDARY,
                desc="后台线程监听\n连接状态变化")

# 7. 读取缓存记录
draw_rounded_box(ax, 4.25, 7.9, 3.0, 0.95, "读取缓存队列", COL_PRIMARY,
                desc="cache.peek(100)\n按ID升序(FIFO)")

# 8. 判断是否有缓存数据
draw_diamond(ax, 4.25, 6.4, 2.4, 1.15, "有数据?", COL_TERTIARY)

# 9a. 补发消息到MQTT
draw_rounded_box(ax, 4.25, 4.6, 3.0, 0.95, "补发消息", COL_SUCCESS,
                desc="逐条重发至Broker\n确认成功返回")

# 10. 删除已发送记录
draw_rounded_box(ax, 4.25, 3.2, 3.0, 0.95, "删除已发记录", COL_PRIMARY,
                desc="cache.delete(ids)\n清理成功记录")

# 9b. 无数据：结束 (左侧)
draw_ellipse(ax, 1.3, 5.5, 2.2, 0.85, "补发完成", COL_SUCCESS)

# ==================== 连接箭头 ====================

# 主流程箭头
draw_arrow(ax, 4.25, 15.12, 4.25, 14.72)  # 开始→接收消息
draw_arrow(ax, 4.25, 13.67, 4.25, 13.35)  # 接收消息→在线检测

# 在线分支（右侧）
draw_arrow(ax, 4.25 + 1.3, 12.7, 7.8, 11.32, color=COL_SUCCESS,
           label="在线", label_pos=(0.8, 0.2))  # 在线检测→发布MQTT
draw_arrow(ax, 7.8, 10.27, 7.8, 9.82)  # 发布MQTT→结束

# 离线分支（主流程继续）
draw_arrow(ax, 4.25 - 1.3, 12.7, 4.25 - 1.3, 11.32, color=COL_ERROR,
           label="离线", label_pos=(-0.5, 0.2))  # 在线检测→写入缓存
draw_arrow(ax, 4.25, 10.27, 4.25, 9.87)  # 写入缓存→等待恢复
draw_arrow(ax, 4.25, 8.87, 4.25, 8.42)  # 等待恢复→读取缓存
draw_arrow(ax, 4.25, 7.42, 4.25, 7.02)  # 读取缓存→有数据?

# 有数据判断分支
draw_arrow(ax, 4.25, 5.8, 4.25, 5.12, color=COL_SUCCESS,
           label="是", label_pos=(0.28, 0.1))  # 有数据→补发消息
draw_arrow(ax, 4.25 - 1.2, 6.4, 1.3 + 1.1, 5.85, color=COL_SECONDARY,
           label="否", label_pos=(-0.28, 0.15))  # 无数据→补发完成

# 补发流程
draw_arrow(ax, 4.25, 4.07, 4.25, 3.72)  # 补发消息→删除记录

# 循环箭头：删除记录后回到读取缓存（使用拐弯箭头+绿色）
draw_loop_arrow_right(ax, 4.25 + 1.5, 3.2, 4.25 + 1.5, 7.9,
                       label="继续补发\n下一条数据", color=COL_SUCCESS, use_curve=True)

# ==================== 图例 ====================
legend_x = -1.0
legend_y_start = 17.0

ax.text(legend_x, legend_y_start + 0.5, "图例", fontsize=10,
        color=COL_TEXT_DARK, weight="bold", ha="center")

# 图例项
legend_items = [
    ("正常流程", COL_PRIMARY, "-"),
    ("成功路径", COL_SUCCESS, "-"),
    ("错误/离线路径", COL_ERROR, "-"),
    ("数据循环", COL_SUCCESS, "--"),
]

for i, (label, color, style) in enumerate(legend_items):
    y_pos = legend_y_start - 0.65 - i * 0.75
    ax.plot([legend_x - 0.8, legend_x - 0.2], [y_pos, y_pos],
            color=color, linewidth=2, linestyle=style)
    if style == "-":
        ax.annotate("", xy=(legend_x - 0.2, y_pos),
                   xytext=(legend_x - 0.5, y_pos),
                   arrowprops=dict(arrowstyle="-|>", color=color, lw=2))
    ax.text(legend_x, y_pos, label, fontsize=9, color=COL_TEXT_DARK,
            ha="left", va="center")

# 底部注释
ax.text(4.25, 1.8, "注：基于SQLite实现WAL模式持久化存储，支持FIFO顺序补发，容量上限100000条",
        fontsize=8.5, color=COL_TEXT_LIGHT, ha="center", va="center",
        style="italic")

plt.tight_layout()
output_path = r"图4-6_离线缓存与补传机制流程图.png"
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
