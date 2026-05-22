"""
图2-1 系统整体架构图 - 基于实际落地的分层架构图
=====================================================
内容依据：
  - README.md（项目实际架构图）
  - software/gateway/python/config.py（实际端口/Topic/数据库路径）
  - software/gateway/python/main.py（Wi-Fi/BLE 双协议适配 + 下行命令分发）
  - software/gateway/python/admin_routes.py（Web 管理台 /admin/ + 用户/节点 CRUD）
  - software/esp32-s3/src/main.cpp 与 sensors.cpp（DHT 温湿度 + 蜂鸣器）
  - software/stm32f103/src/main.cpp 与 ldr/buzzer/ble_uart（GY-302 + LED + HM-10）

布局：自顶向下 4 层 + 底部并列 2 个感知节点，方形画幅，便于插入论文正文。
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import platform


def setup_chinese_font():
    """Windows 下优先使用微软雅黑/SimHei，确保中文不出方框。"""
    system = platform.system()
    if system == "Windows":
        candidates = ["Microsoft YaHei", "SimHei", "SimSun"]
    elif system == "Darwin":
        candidates = ["PingFang SC", "Hiragino Sans GB", "Heiti SC"]
    else:
        candidates = ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


setup_chinese_font()


COLOR_BG = "#FFFFFF"
COLOR_TITLE_BAR = {
    "app": "#3A6FB0",
    "net": "#4A90B8",
    "edge": "#5BA199",
    "node1": "#7AA66A",
    "node2": "#C28A4A",
}
COLOR_BOX_FILL = "#F4F8FC"
COLOR_BOX_EDGE = "#7B9EC2"
COLOR_TEXT_TITLE = "#FFFFFF"
COLOR_TEXT_BODY = "#1F3550"
COLOR_ARROW = "#4A6B8A"
COLOR_HIGHLIGHT = "#A8E6CF"


def draw_layer_box(
    ax,
    x,
    y,
    width,
    height,
    title,
    lines,
    title_color,
    icon_char=None,
    highlight_indices=None,
):
    """绘制一个分层盒子：上方为标题条（含图标），下方为多行内容。"""
    if highlight_indices is None:
        highlight_indices = set()
    outer = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=1.6,
        edgecolor=COLOR_BOX_EDGE,
        facecolor=COLOR_BOX_FILL,
        zorder=2,
    )
    ax.add_patch(outer)

    title_h = 0.55
    title_bar = FancyBboxPatch(
        (x + 0.05, y + height - title_h - 0.05),
        width - 0.10,
        title_h,
        boxstyle="round,pad=0.0,rounding_size=0.10",
        linewidth=0,
        edgecolor="none",
        facecolor=title_color,
        zorder=3,
    )
    ax.add_patch(title_bar)

    if icon_char is not None:
        ax.text(
            x + 0.32,
            y + height - title_h / 2 - 0.05,
            icon_char,
            fontsize=14,
            color=COLOR_TEXT_TITLE,
            ha="center",
            va="center",
            weight="bold",
            zorder=4,
        )
        title_x = x + 0.58
        title_ha = "left"
    else:
        title_x = x + width / 2
        title_ha = "center"

    ax.text(
        title_x,
        y + height - title_h / 2 - 0.05,
        title,
        fontsize=12.5,
        color=COLOR_TEXT_TITLE,
        ha=title_ha,
        va="center",
        weight="bold",
        zorder=4,
    )

    content_top = y + height - title_h - 0.18
    content_bottom = y + 0.15
    line_count = len(lines)
    if line_count == 0:
        return
    line_h = (content_top - content_bottom) / line_count

    for i, line in enumerate(lines):
        cy = content_top - line_h * (i + 0.5)
        is_highlighted = i in highlight_indices
        inner = FancyBboxPatch(
            (x + 0.18, cy - line_h * 0.40),
            width - 0.36,
            line_h * 0.78,
            boxstyle="round,pad=0.0,rounding_size=0.08",
            linewidth=0.8,
            edgecolor="#7CC9A8" if is_highlighted else COLOR_BOX_EDGE,
            facecolor=COLOR_HIGHLIGHT if is_highlighted else "#EAF2FA",
            zorder=3,
        )
        ax.add_patch(inner)
        ax.text(
            x + width / 2,
            cy,
            line,
            fontsize=10,
            color=COLOR_TEXT_BODY,
            ha="center",
            va="center",
            zorder=4,
        )


def draw_arrow(ax, x1, y1, x2, y2, label=None, label_pos=None):
    """绘制连接线 + 可选标签。"""
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="-|>",
        mutation_scale=20,
        linewidth=2.0,
        color=COLOR_ARROW,
        zorder=1,
    )
    ax.add_patch(arrow)
    if label:
        if label_pos is None:
            mx, my = (x1 + x2) / 2 + 0.18, (y1 + y2) / 2
        else:
            mx, my = label_pos
        ax.text(
            mx,
            my,
            label,
            fontsize=9.5,
            color="#324A66",
            ha="center",
            va="center",
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="#FFFFFF",
                edgecolor="#B8CCE0",
                linewidth=0.7,
            ),
            zorder=5,
        )


def build_figure():
    fig, ax = plt.subplots(figsize=(11, 12.5), dpi=180)
    ax.set_xlim(-0.2, 10.2)
    ax.set_ylim(-2.2, 11.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(COLOR_BG)

    draw_layer_box(
        ax,
        x=1.0,
        y=9.0,
        width=8.0,
        height=2.0,
        title="应用层（Application）",
        lines=[
            "Web 管理台（Flask + Session 登录）：/admin/ 用户与节点 CRUD、在线状态",
            "Node-RED 规则引擎与 Dashboard（端口 1880）：跨协议联动可视化编排",
            "EMQX Dashboard（端口 18083） · 外部 MQTT 客户端（mosquitto_sub 等）",
        ],
        title_color=COLOR_TITLE_BAR["app"],
        icon_char="App",
    )

    draw_arrow(
        ax,
        5.0,
        9.0,
        5.0,
        7.65,
        label="HTTP(8080) / MQTT(1883) / WebSocket",
        label_pos=(5.0, 8.32),
    )

    draw_layer_box(
        ax,
        x=1.0,
        y=6.0,
        width=8.0,
        height=1.65,
        title="网络层（Network · MQTT Broker）",
        lines=[
            "EMQX（Docker 容器化部署） · Topic 前缀 smarthome/v1/...",
            "三类主题：telemetry（上行） · status（状态） · command（下行）",
        ],
        title_color=COLOR_TITLE_BAR["net"],
        icon_char="Net",
    )

    draw_arrow(
        ax,
        5.0,
        6.0,
        5.0,
        4.85,
        label="统一 JSON（QoS 1） · paho-mqtt",
        label_pos=(5.0, 5.42),
    )

    draw_layer_box(
        ax,
        x=0.4,
        y=1.40,
        width=9.2,
        height=3.45,
        title="边缘层（Edge Gateway · 树莓派 4B）",
        lines=[
            "Wi-Fi 适配器（Flask + asyncio）：HTTP POST :8080 + TCP :9000 双通道",
            "BLE 适配器（bleak）：GATT 扫描 / 通知订阅，兼容 HM-10（FFE0/FFE1）",
            "数据融合与协议转换：字段映射 / 时间戳归一 / 统一 JSON Schema 校验",
            "SQLite 双库：cache.db（断网离线缓存与补传） + admin.db（用户/节点台账）",
            "下行命令路由：订阅 command/+/+ → BLE(JSON行/raw_hex) · Wi-Fi(TCP透传)",
            "Node-RED 本地联动 + Python 日志中心（logs/gateway.log）",
        ],
        title_color=COLOR_TITLE_BAR["edge"],
        icon_char="Pi",
        highlight_indices={5},
    )

    draw_arrow(
        ax,
        2.8,
        1.40,
        2.0,
        0.55,
        label="Wi-Fi（HTTP POST / TCP）",
        label_pos=(0.95, 0.95),
    )
    draw_arrow(
        ax,
        7.2,
        1.40,
        8.0,
        0.55,
        label="蓝牙 BLE（GATT · HM-10）",
        label_pos=(8.95, 0.95),
    )

    draw_layer_box(
        ax,
        x=-0.20,
        y=-2.15,
        width=4.4,
        height=2.65,
        title="感知层节点①（Wi-Fi）",
        lines=[
            "主控：ESP32-S3 DevKitC-1",
            "无线接入：Wi-Fi（IEEE 802.11 b/g/n）",
            "传感器：DHT 温湿度（I²C）",
            "执行器：板载蜂鸣器（PWM 报警）",
        ],
        title_color=COLOR_TITLE_BAR["node1"],
        icon_char="W",
    )

    draw_layer_box(
        ax,
        x=5.80,
        y=-2.15,
        width=4.4,
        height=2.65,
        title="感知层节点②（BLE）",
        lines=[
            "主控：STM32F103 + HM-10 透传模块",
            "无线接入：蓝牙 BLE（UART over GATT）",
            "传感器：GY-302（BH1750）光照 / LDR",
            "执行器：LED 指示灯（GPIO PWM）",
        ],
        title_color=COLOR_TITLE_BAR["node2"],
        icon_char="B",
    )

    plt.tight_layout(pad=0.5)
    return fig


if __name__ == "__main__":
    fig = build_figure()
    out_path = "图2-1_系统整体架构图.png"
    fig.savefig(out_path, dpi=220, bbox_inches="tight", facecolor=COLOR_BG)
    print(f"Saved -> {out_path}")
