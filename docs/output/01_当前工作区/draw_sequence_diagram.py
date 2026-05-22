"""
图2-2 跨协议联动时序图
=====================
依据：
  - 论文 §2.3"上层协同调度可行性分析"中"光照自动控灯"场景
  - 论文表 5-4 跨节点联动时延分解 (BLE 78.6 ms + 规则 12.4 ms + Wi-Fi 45.2 ms = 136.2 ms)
  - 实际项目硬件分布：
      BLE 节点 (STM32F103 + HM-10 + GY-302/LDR) ── 光照传感
      Wi-Fi 节点 (ESP32-S3 + 蜂鸣器) ───────────── 报警执行器
  - 实际项目 Topic：smarthome/v1/{telemetry|command}/<type>/<id>

布局：6 条 lifeline，中间 4 条用虚线框圈出"网关 · 树莓派 4B 边缘流水线"，
       右侧 4 个关键时间点 (t0/t1/t2/t3) 与论文表 5-4 数据呼应。
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
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


setup_chinese_font()


COL_SENSOR = "#7AA66A"
COL_BLE_ADAPTER = "#5BA199"
COL_BROKER = "#4A90B8"
COL_NODERED = "#3A6FB0"
COL_WIFI_ADAPTER = "#5BA199"
COL_ACTUATOR = "#C28A4A"

LIFELINE_COLOR = "#A8B8CC"
ACTIVATION_FILL = "#EAF2FA"
ACTIVATION_EDGE = "#7B9EC2"
ARROW_COLOR = "#1F3550"
RETURN_ARROW = "#6E869F"
GATEWAY_BG = "#F8F9FB"
GATEWAY_BORDER = "#B0BFD2"
TIME_FILL = "#FFF6D9"
TIME_EDGE = "#D4BA66"
LABEL_BG = "#FFFFFF"
LABEL_EDGE = "#C8D5E3"

PARTICIPANTS = [
    ("BLE 传感器节点", "STM32F103 + HM-10\nGY-302 / LDR 光照", COL_SENSOR),
    ("BLE 适配器", "bleak (GATT)\nFFE0 / FFE1", COL_BLE_ADAPTER),
    ("MQTT Broker", "EMQX (Docker)\nsmarthome/v1/...", COL_BROKER),
    ("Node-RED", "规则引擎\n阈值判断", COL_NODERED),
    ("Wi-Fi 适配器", "Flask + asyncio\nTCP:9000 / HTTP:8080", COL_WIFI_ADAPTER),
    ("Wi-Fi 执行器节点", "ESP32-S3\n蜂鸣器报警", COL_ACTUATOR),
]

LIFELINE_X = [1.6, 4.0, 6.4, 8.8, 11.2, 13.6]
HEADER_TOP = 0.0
HEADER_H = 1.45
HEADER_W = 2.10

LIFELINE_BOTTOM = -14.0
TIME_X = 14.95

X_MIN = -0.2
X_MAX = 17.5
Y_MIN = LIFELINE_BOTTOM - 0.5
Y_MAX = HEADER_TOP + 2.2


def draw_participant_header(ax, x, title, subtitle, color):
    box = FancyBboxPatch(
        (x - HEADER_W / 2, HEADER_TOP - HEADER_H),
        HEADER_W,
        HEADER_H,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=1.4,
        edgecolor=color,
        facecolor="white",
        zorder=4,
    )
    ax.add_patch(box)

    title_h = 0.48
    bar = FancyBboxPatch(
        (x - HEADER_W / 2 + 0.04, HEADER_TOP - title_h - 0.04),
        HEADER_W - 0.08,
        title_h,
        boxstyle="round,pad=0.0,rounding_size=0.08",
        linewidth=0,
        edgecolor="none",
        facecolor=color,
        zorder=5,
    )
    ax.add_patch(bar)
    ax.text(
        x,
        HEADER_TOP - title_h / 2 - 0.04,
        title,
        fontsize=11,
        color="white",
        ha="center",
        va="center",
        weight="bold",
        zorder=6,
    )
    ax.text(
        x,
        HEADER_TOP - title_h - 0.46,
        subtitle,
        fontsize=8.8,
        color="#1F3550",
        ha="center",
        va="center",
        zorder=6,
    )


def draw_lifeline(ax, x):
    ax.plot(
        [x, x],
        [HEADER_TOP - HEADER_H - 0.02, LIFELINE_BOTTOM],
        linestyle=(0, (4, 3)),
        color=LIFELINE_COLOR,
        linewidth=1.0,
        zorder=1,
    )


def draw_message(ax, y, src_x, dst_x, label, kind="msg"):
    is_return = kind == "return"
    color = RETURN_ARROW if is_return else ARROW_COLOR
    ls = "--" if is_return else "-"
    arrow = FancyArrowPatch(
        (src_x, y),
        (dst_x, y),
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.7,
        color=color,
        linestyle=ls,
        zorder=3,
    )
    ax.add_patch(arrow)
    mx = (src_x + dst_x) / 2
    ax.text(
        mx,
        y + 0.13,
        label,
        fontsize=8.8,
        color="#1F3550",
        ha="center",
        va="bottom",
        zorder=5,
        bbox=dict(
            boxstyle="round,pad=0.22",
            facecolor=LABEL_BG,
            edgecolor=LABEL_EDGE,
            linewidth=0.7,
        ),
    )


def draw_self_message(ax, y, x, label, side="right", loop_w=0.65, loop_h=0.5):
    if side == "right":
        pts = [(x, y), (x + loop_w, y), (x + loop_w, y - loop_h), (x, y - loop_h)]
        label_x = x + loop_w + 0.18
        label_ha = "left"
    else:
        pts = [(x, y), (x - loop_w, y), (x - loop_w, y - loop_h), (x, y - loop_h)]
        label_x = x - loop_w - 0.18
        label_ha = "right"
    for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
        if i < len(pts) - 2:
            ax.plot(
                [a[0], b[0]],
                [a[1], b[1]],
                color=ARROW_COLOR,
                linewidth=1.6,
                zorder=3,
            )
        else:
            arrow = FancyArrowPatch(
                a,
                b,
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.6,
                color=ARROW_COLOR,
                zorder=3,
            )
            ax.add_patch(arrow)
    ax.text(
        label_x,
        y - loop_h / 2,
        label,
        fontsize=8.8,
        color="#1F3550",
        ha=label_ha,
        va="center",
        zorder=5,
        bbox=dict(
            boxstyle="round,pad=0.22",
            facecolor=LABEL_BG,
            edgecolor=LABEL_EDGE,
            linewidth=0.7,
        ),
    )


def draw_activation(ax, x, y_top, y_bottom, width=0.20):
    rect = Rectangle(
        (x - width / 2, y_bottom),
        width,
        y_top - y_bottom,
        linewidth=0.8,
        edgecolor=ACTIVATION_EDGE,
        facecolor=ACTIVATION_FILL,
        zorder=2,
    )
    ax.add_patch(rect)


def draw_gateway_grouping(ax):
    x1 = LIFELINE_X[1] - 1.35
    x2 = LIFELINE_X[4] + 1.35
    y1 = HEADER_TOP + 0.95
    y2 = LIFELINE_BOTTOM - 0.25
    rect = FancyBboxPatch(
        (x1, y2),
        x2 - x1,
        y1 - y2,
        boxstyle="round,pad=0.0,rounding_size=0.18",
        linewidth=1.5,
        edgecolor=GATEWAY_BORDER,
        facecolor=GATEWAY_BG,
        linestyle=(0, (6, 4)),
        zorder=0,
    )
    ax.add_patch(rect)
    label = FancyBboxPatch(
        ((x1 + x2) / 2 - 3.0, y1 - 0.55),
        6.0,
        0.50,
        boxstyle="round,pad=0.0,rounding_size=0.10",
        linewidth=1.0,
        edgecolor=GATEWAY_BORDER,
        facecolor="#E9EFF7",
        zorder=10,
    )
    ax.add_patch(label)
    ax.text(
        (x1 + x2) / 2,
        y1 - 0.30,
        "网关 · 树莓派 4B 边缘处理流水线 (Edge Pipeline)",
        fontsize=11.5,
        color="#2E4A6A",
        ha="center",
        va="center",
        weight="bold",
        zorder=11,
    )


def draw_time_marker(ax, y, label):
    ax.plot([TIME_X - 0.15, TIME_X + 0.05], [y, y], color="#B0934F", linewidth=1.2, zorder=4)
    ax.text(
        TIME_X + 0.15,
        y,
        label,
        fontsize=9,
        color="#5A4720",
        ha="left",
        va="center",
        zorder=6,
        bbox=dict(
            boxstyle="round,pad=0.30",
            facecolor=TIME_FILL,
            edgecolor=TIME_EDGE,
            linewidth=0.9,
        ),
    )


def main():
    fig, ax = plt.subplots(figsize=(13.5, 13), dpi=180)
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    draw_gateway_grouping(ax)

    for x, (title, subtitle, color) in zip(LIFELINE_X, PARTICIPANTS):
        draw_participant_header(ax, x, title, subtitle, color)
        draw_lifeline(ax, x)

    LX = LIFELINE_X

    draw_activation(ax, LX[0], -1.7, -3.0)
    draw_activation(ax, LX[1], -3.4, -5.7)
    draw_activation(ax, LX[2], -5.7, -9.1)
    draw_activation(ax, LX[3], -6.7, -8.5)
    draw_activation(ax, LX[4], -9.6, -10.7)
    draw_activation(ax, LX[5], -10.7, -13.0)

    draw_self_message(ax, -1.9, LX[0], "① 周期采样 (I²C)\nilluminance = 35 lux")

    draw_message(ax, -3.4, LX[0], LX[1],
                 "② BLE GATT notify (FFE1)\nUART JSON: {\"lux\":35,\"ts\":t0}")

    draw_self_message(ax, -4.2, LX[1],
                      "③ 协议解析 + 字段映射\nJSON Schema 校验",
                      loop_w=0.70, loop_h=0.55)

    draw_message(ax, -5.8, LX[1], LX[2],
                 "④ publish 统一 JSON (QoS 1)\ntopic: smarthome/v1/telemetry/ble/light_01")

    draw_message(ax, -6.8, LX[2], LX[3], "⑤ MQTT 推送至订阅者")

    draw_self_message(ax, -7.5, LX[3],
                      "⑥ if lux < 50 →\n action: beep_on, duration: 2 s",
                      loop_w=0.70, loop_h=0.55)

    draw_message(ax, -8.7, LX[3], LX[2],
                 "⑦ publish 控制命令 (QoS 1)\ntopic: smarthome/v1/command/wifi/buzzer_01",
                 kind="return")

    draw_message(ax, -9.7, LX[2], LX[4],
                 "⑧ 网关订阅 command/+/+\n命令路由 → wifi 适配器")

    draw_message(ax, -10.8, LX[4], LX[5],
                 "⑨ TCP:9000 透传\n{\"action\":\"beep_on\",\"duration\":2}")

    draw_self_message(ax, -11.6, LX[5],
                      "⑩ 蜂鸣器 GPIO PWM\n报警执行",
                      loop_w=0.70, loop_h=0.55)

    draw_message(ax, -12.9, LX[5], LX[4],
                 "(11) ACK 状态回传 (status: ok)",
                 kind="return")

    time_markers = [
        (-1.9, "t0 = 0 ms\nBLE 采样起点"),
        (-5.8, "t1 ≈ 78.6 ms\n数据到达 Broker"),
        (-8.7, "t2 ≈ 91.0 ms\n规则触发完毕"),
        (-10.8, "t3 ≈ 110 ms\n命令路由完成"),
        (-12.9, "t4 ≈ 136.2 ms\n执行 + ACK 闭环"),
    ]
    for y, lbl in time_markers:
        draw_time_marker(ax, y, lbl)

    ax.text(
        (X_MIN + X_MAX) / 2 + 0.2,
        Y_MAX - 0.45,
        "跨协议联动时序：BLE 光照传感 → 网关边缘处理 → Wi-Fi 蜂鸣器报警",
        fontsize=13.5,
        color="#1F3550",
        ha="center",
        va="center",
        weight="bold",
    )

    legend_items = [
        ("实线箭头：异步消息 / 命令", ARROW_COLOR, "-"),
        ("虚线箭头：响应 / 回传 ACK", RETURN_ARROW, "--"),
        ("浅色矩形：执行激活段 (Activation)", ACTIVATION_EDGE, None),
    ]
    lx, ly = X_MIN + 0.4, Y_MIN + 0.55
    for i, (lbl, c, ls) in enumerate(legend_items):
        yy = ly - i * 0.45
        if ls is not None:
            ax.plot([lx, lx + 0.6], [yy, yy], color=c, linewidth=1.6, linestyle=ls)
            ax.annotate("", xy=(lx + 0.65, yy), xytext=(lx + 0.55, yy),
                        arrowprops=dict(arrowstyle="-|>", color=c, lw=1.6))
        else:
            rect = Rectangle((lx + 0.05, yy - 0.15), 0.5, 0.30,
                             linewidth=0.8, edgecolor=ACTIVATION_EDGE,
                             facecolor=ACTIVATION_FILL)
            ax.add_patch(rect)
        ax.text(lx + 0.85, yy, lbl, fontsize=9, color="#324A66",
                ha="left", va="center")

    plt.tight_layout(pad=0.5)
    out = "图2-2_跨协议联动时序图.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
