"""
图3-1 系统数据流架构图
=====================
依据：
  - 论文 §3.1"系统数据流架构"段落（终端 → 网关 → 协议转换 → Broker → 各应用层）
  - 实际项目模块：
      软件层：wifi_receiver / ble_receiver / data_converter / mqtt_publisher /
              cache.py / admin_routes.py / Node-RED flows.json / EMQX (Docker)
      Topic 规范：smarthome/v1/{telemetry|command|status}/<type>/<id>

视觉表达：
  - 上行数据流（solid 深蓝箭头）：感知层 → 适配器 → 协议转换 → Broker → 应用层
  - 下行命令流（dashed 橙色箭头）：应用层 → Broker → 命令路由 → 适配器 → 终端
  - MQTT Broker 居中，作为消息总线枢纽 (Hub) 向 4 个应用消费者扇出。

布局：方形画幅 (~12×13 in)，便于插入论文正文。
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


setup_chinese_font()


COL_TERMINAL = "#7AA66A"
COL_ADAPTER = "#5BA199"
COL_CONVERT = "#D4A862"
COL_BROKER = "#3A6FB0"
COL_NODERED = "#7B6AAA"
COL_SQLITE = "#A57B5C"
COL_WEB = "#5694C8"
COL_EXT = "#8B98A5"
COL_USER = "#4A5566"

COL_BOX_FILL = "#FFFFFF"
COL_TEXT_TITLE = "#FFFFFF"
COL_TEXT_BODY = "#1F3550"

COL_UP_ARROW = "#1F3550"
COL_DOWN_ARROW = "#C28A4A"
COL_STORE_ARROW = "#7A8896"
COL_LABEL_BG = "#FFFFFF"
COL_LABEL_EDGE = "#C0D0E0"


def draw_box(
    ax,
    cx,
    cy,
    w,
    h,
    title,
    lines,
    title_color,
    icon_char=None,
    emphasize=False,
):
    """绘制带标题条的圆角盒子（cx,cy 为盒子中心点）。"""
    x = cx - w / 2
    y = cy - h / 2
    edge_width = 2.0 if emphasize else 1.4
    outer = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.14",
        linewidth=edge_width,
        edgecolor=title_color if emphasize else "#7B9EC2",
        facecolor=COL_BOX_FILL,
        zorder=3,
    )
    ax.add_patch(outer)

    title_h = 0.46 if not emphasize else 0.56
    title_bar = FancyBboxPatch(
        (x + 0.04, y + h - title_h - 0.04),
        w - 0.08,
        title_h,
        boxstyle="round,pad=0.0,rounding_size=0.08",
        linewidth=0,
        edgecolor="none",
        facecolor=title_color,
        zorder=4,
    )
    ax.add_patch(title_bar)

    if icon_char:
        ax.text(
            x + 0.30,
            y + h - title_h / 2 - 0.04,
            icon_char,
            fontsize=12 if not emphasize else 13,
            color=COL_TEXT_TITLE,
            ha="center",
            va="center",
            weight="bold",
            zorder=5,
        )
        title_x = x + 0.55
        title_ha = "left"
    else:
        title_x = cx
        title_ha = "center"

    ax.text(
        title_x,
        y + h - title_h / 2 - 0.04,
        title,
        fontsize=11.5 if not emphasize else 13,
        color=COL_TEXT_TITLE,
        ha=title_ha,
        va="center",
        weight="bold",
        zorder=5,
    )

    if lines:
        content_top = y + h - title_h - 0.14
        content_bot = y + 0.10
        line_count = len(lines)
        step = (content_top - content_bot) / line_count
        for i, line in enumerate(lines):
            yy = content_top - step * (i + 0.5)
            ax.text(
                cx,
                yy,
                line,
                fontsize=9.5,
                color=COL_TEXT_BODY,
                ha="center",
                va="center",
                zorder=5,
            )


def draw_arrow(
    ax,
    x1,
    y1,
    x2,
    y2,
    label=None,
    label_pos=None,
    kind="up",
    rad=0.0,
    label_fontsize=9,
):
    """绘制带方向的箭头，kind ∈ {'up','down','store'}。"""
    if kind == "up":
        color = COL_UP_ARROW
        ls = "-"
        lw = 1.9
    elif kind == "down":
        color = COL_DOWN_ARROW
        ls = (0, (6, 3))
        lw = 1.8
    else:
        color = COL_STORE_ARROW
        ls = (0, (1.5, 2))
        lw = 1.5

    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle="-|>",
        mutation_scale=16,
        linewidth=lw,
        color=color,
        linestyle=ls,
        connectionstyle=f"arc3,rad={rad}",
        zorder=2,
    )
    ax.add_patch(arrow)

    if label:
        if label_pos is None:
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
        else:
            mx, my = label_pos
        ax.text(
            mx,
            my,
            label,
            fontsize=label_fontsize,
            color=COL_TEXT_BODY,
            ha="center",
            va="center",
            zorder=6,
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor=COL_LABEL_BG,
                edgecolor=COL_LABEL_EDGE,
                linewidth=0.7,
            ),
        )


def draw_section_band(ax, y_top, y_bot, x_left, x_right, label, color):
    """绘制左侧的小色条注释当前所处层级（视觉锚点）。"""
    rect = FancyBboxPatch(
        (x_left, y_bot),
        x_right - x_left,
        y_top - y_bot,
        boxstyle="round,pad=0.0,rounding_size=0.08",
        linewidth=1.0,
        edgecolor=color,
        facecolor=color + "20",
        zorder=0,
    )
    ax.add_patch(rect)
    ax.text(
        x_left + 0.18,
        (y_top + y_bot) / 2,
        label,
        fontsize=11,
        color=color,
        ha="left",
        va="center",
        rotation=90,
        weight="bold",
        zorder=1,
    )


def main():
    fig, ax = plt.subplots(figsize=(12.5, 14.5), dpi=180)
    ax.set_xlim(-0.3, 13.0)
    ax.set_ylim(-1.4, 16.4)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    LEFT_X = 3.4
    RIGHT_X = 9.2
    CENTER_X = 6.3

    Y_TERMINAL = 14.1
    Y_LABEL_UP = 13.05
    Y_LABEL_DN = 12.50
    Y_ADAPTER = 11.6
    Y_CONVERT = 9.6
    Y_BROKER = 7.0
    Y_APPS = 3.6
    Y_USER = 0.6

    BOX_W_SMALL = 3.4
    BOX_H_SMALL = 1.30
    BOX_W_WIDE = 10.4
    BOX_H_CONVERT = 1.65
    BOX_H_BROKER = 1.95
    BOX_W_APP = 2.55
    BOX_H_APP = 1.55

    draw_section_band(ax, 14.90, 13.45, -0.20, 0.45, "感知层", "#5E8B3E")
    draw_section_band(ax, 13.40, 8.65, -0.20, 0.45, "边缘层（树莓派 4B 网关）", "#3D7A78")
    draw_section_band(ax, 8.60, 5.85, -0.20, 0.45, "网络层（MQTT Broker）", "#2E5A91")
    draw_section_band(ax, 5.80, 2.65, -0.20, 0.45, "应用层", "#5A4880")
    draw_section_band(ax, 2.60, -0.30, -0.20, 0.45, "用户层", "#3E4C5C")

    draw_box(
        ax,
        LEFT_X,
        Y_TERMINAL,
        BOX_W_SMALL,
        BOX_H_SMALL,
        "Wi-Fi 终端节点",
        ["ESP32-S3 · DHT 温湿度 + 蜂鸣器", "Wi-Fi 802.11 b/g/n"],
        COL_TERMINAL,
        icon_char="W",
    )
    draw_box(
        ax,
        RIGHT_X,
        Y_TERMINAL,
        BOX_W_SMALL,
        BOX_H_SMALL,
        "BLE 终端节点",
        ["STM32F103 + HM-10 · GY-302 + LED", "Bluetooth LE GATT"],
        COL_TERMINAL,
        icon_char="B",
    )

    draw_box(
        ax,
        LEFT_X,
        Y_ADAPTER,
        BOX_W_SMALL,
        BOX_H_SMALL,
        "Wi-Fi 适配器",
        ["Flask + asyncio", "HTTP:8080 · TCP:9000"],
        COL_ADAPTER,
        icon_char="A",
    )
    draw_box(
        ax,
        RIGHT_X,
        Y_ADAPTER,
        BOX_W_SMALL,
        BOX_H_SMALL,
        "BLE 适配器",
        ["bleak 库 · GATT 通知订阅", "FFE0 / FFE1 特征值"],
        COL_ADAPTER,
        icon_char="A",
    )

    draw_box(
        ax,
        CENTER_X,
        Y_CONVERT,
        BOX_W_WIDE,
        BOX_H_CONVERT,
        "协议转换 + 数据融合（data_converter）",
        [
            "字段映射 · 时间戳归一 · 单位标准化 · JSON Schema 校验",
            "上行：publish 统一 JSON   |   下行：on_command → BLE/Wi-Fi 路由",
            "SQLite cache.db 离线缓存（断网期暂存，恢复后按时间戳补传）",
        ],
        COL_CONVERT,
        icon_char="C",
    )

    draw_box(
        ax,
        CENTER_X,
        Y_BROKER,
        BOX_W_WIDE,
        BOX_H_BROKER,
        "EMQX MQTT Broker（Docker 容器化部署）",
        [
            "Topic 前缀  smarthome/v1/...",
            "telemetry/<type>/<id>（↑ 上行遥测）   ·   command/<type>/<id>（↓ 下行命令）",
            "status/<type>/<id>（设备在线/离线事件） · QoS 1 / WebSocket 8083",
        ],
        COL_BROKER,
        icon_char="M",
        emphasize=True,
    )

    APP_XS = [1.7, 4.7, 7.9, 11.1]
    draw_box(
        ax,
        APP_XS[0],
        Y_APPS,
        BOX_W_APP,
        BOX_H_APP,
        "Node-RED 规则引擎",
        [
            "订阅 telemetry/+/+",
            "本地联动规则",
            "publish command/+/+",
            "端口 1880",
        ],
        COL_NODERED,
        icon_char="N",
    )
    draw_box(
        ax,
        APP_XS[1],
        Y_APPS,
        BOX_W_APP,
        BOX_H_APP,
        "SQLite 本地存储",
        [
            "admin.db 用户/节点",
            "cache.db 离线补传",
            "历史数据持久化",
            "断网自治备份",
        ],
        COL_SQLITE,
        icon_char="S",
    )
    draw_box(
        ax,
        APP_XS[2],
        Y_APPS,
        BOX_W_APP,
        BOX_H_APP,
        "Web 管理台（Flask）",
        [
            "/admin/ Session 登录",
            "节点 CRUD + 在线状态",
            "数据可视化",
            "规则配置 API",
        ],
        COL_WEB,
        icon_char="W",
    )
    draw_box(
        ax,
        APP_XS[3],
        Y_APPS,
        BOX_W_APP,
        BOX_H_APP,
        "外部 MQTT 客户端",
        [
            "mosquitto_sub / pub",
            "EMQX Dashboard",
            "端口 18083",
            "（可选云端桥接）",
        ],
        COL_EXT,
        icon_char="E",
    )

    draw_box(
        ax,
        CENTER_X,
        Y_USER,
        4.6,
        1.30,
        "用户 · 浏览器 / 移动端",
        ["HTTPS 访问 /admin/ Web 管理台 · 配置规则 · 触发控制指令"],
        COL_USER,
        icon_char="U",
    )

    draw_arrow(
        ax, LEFT_X + 0.25, Y_TERMINAL - BOX_H_SMALL / 2,
        LEFT_X + 0.25, Y_ADAPTER + BOX_H_SMALL / 2,
        kind="up",
        label="↑ 上行 HTTP POST / TCP",
        label_pos=(LEFT_X - 1.40, Y_LABEL_UP),
        label_fontsize=8.8,
    )
    draw_arrow(
        ax, LEFT_X - 0.25, Y_ADAPTER + BOX_H_SMALL / 2,
        LEFT_X - 0.25, Y_TERMINAL - BOX_H_SMALL / 2,
        kind="down",
        label="↓ 下行 TCP 透传",
        label_pos=(LEFT_X - 1.40, Y_LABEL_DN),
        label_fontsize=8.8,
    )

    draw_arrow(
        ax, RIGHT_X + 0.25, Y_TERMINAL - BOX_H_SMALL / 2,
        RIGHT_X + 0.25, Y_ADAPTER + BOX_H_SMALL / 2,
        kind="up",
        label="↑ BLE notify (GATT)",
        label_pos=(RIGHT_X + 1.55, Y_LABEL_UP),
        label_fontsize=8.8,
    )
    draw_arrow(
        ax, RIGHT_X - 0.25, Y_ADAPTER + BOX_H_SMALL / 2,
        RIGHT_X - 0.25, Y_TERMINAL - BOX_H_SMALL / 2,
        kind="down",
        label="↓ HM-10 UART 写",
        label_pos=(RIGHT_X + 1.55, Y_LABEL_DN),
        label_fontsize=8.8,
    )

    draw_arrow(
        ax, LEFT_X + 0.25, Y_ADAPTER - BOX_H_SMALL / 2,
        LEFT_X + 0.25, Y_CONVERT + BOX_H_CONVERT / 2,
        kind="up",
        label="原始数据帧",
        label_pos=(LEFT_X - 1.10, 10.55),
        label_fontsize=8.8,
    )
    draw_arrow(
        ax, LEFT_X - 0.25, Y_CONVERT + BOX_H_CONVERT / 2,
        LEFT_X - 0.25, Y_ADAPTER - BOX_H_SMALL / 2,
        kind="down",
    )

    draw_arrow(
        ax, RIGHT_X + 0.25, Y_ADAPTER - BOX_H_SMALL / 2,
        RIGHT_X + 0.25, Y_CONVERT + BOX_H_CONVERT / 2,
        kind="up",
        label="原始数据帧",
        label_pos=(RIGHT_X + 1.40, 10.55),
        label_fontsize=8.8,
    )
    draw_arrow(
        ax, RIGHT_X - 0.25, Y_CONVERT + BOX_H_CONVERT / 2,
        RIGHT_X - 0.25, Y_ADAPTER - BOX_H_SMALL / 2,
        kind="down",
    )

    draw_arrow(
        ax, CENTER_X + 0.30, Y_CONVERT - BOX_H_CONVERT / 2,
        CENTER_X + 0.30, Y_BROKER + BOX_H_BROKER / 2,
        kind="up",
        label="publish 统一 JSON (QoS 1)",
        label_pos=(CENTER_X + 2.45, (Y_CONVERT + Y_BROKER) / 2 + 0.20),
        label_fontsize=9,
    )
    draw_arrow(
        ax, CENTER_X - 0.30, Y_BROKER + BOX_H_BROKER / 2,
        CENTER_X - 0.30, Y_CONVERT - BOX_H_CONVERT / 2,
        kind="down",
        label="subscribe command/+/+",
        label_pos=(CENTER_X - 2.40, (Y_CONVERT + Y_BROKER) / 2 + 0.20),
        label_fontsize=9,
    )

    BROKER_BOT = Y_BROKER - BOX_H_BROKER / 2
    APPS_TOP = Y_APPS + BOX_H_APP / 2

    for i, ax_x in enumerate(APP_XS):
        if i in (0, 3):
            draw_arrow(ax, ax_x - 0.25, BROKER_BOT, ax_x - 0.25, APPS_TOP, kind="up")
            draw_arrow(ax, ax_x + 0.25, APPS_TOP, ax_x + 0.25, BROKER_BOT, kind="down")
        elif i == 1:
            draw_arrow(ax, ax_x, BROKER_BOT, ax_x, APPS_TOP, kind="store")
        else:
            draw_arrow(ax, ax_x - 0.25, BROKER_BOT, ax_x - 0.25, APPS_TOP, kind="up")
            draw_arrow(ax, ax_x + 0.25, APPS_TOP, ax_x + 0.25, BROKER_BOT, kind="down")

    ax.text(
        APP_XS[0],
        BROKER_BOT - 0.30,
        "telemetry ↑↓ command",
        fontsize=8.5,
        color=COL_TEXT_BODY,
        ha="center",
        va="top",
        bbox=dict(
            boxstyle="round,pad=0.20",
            facecolor=COL_LABEL_BG,
            edgecolor=COL_LABEL_EDGE,
            linewidth=0.6,
        ),
        zorder=6,
    )
    ax.text(
        APP_XS[1],
        BROKER_BOT - 0.30,
        "读写持久化",
        fontsize=8.5,
        color=COL_TEXT_BODY,
        ha="center",
        va="top",
        bbox=dict(
            boxstyle="round,pad=0.20",
            facecolor=COL_LABEL_BG,
            edgecolor=COL_LABEL_EDGE,
            linewidth=0.6,
        ),
        zorder=6,
    )
    ax.text(
        APP_XS[2],
        BROKER_BOT - 0.30,
        "telemetry ↑↓ command",
        fontsize=8.5,
        color=COL_TEXT_BODY,
        ha="center",
        va="top",
        bbox=dict(
            boxstyle="round,pad=0.20",
            facecolor=COL_LABEL_BG,
            edgecolor=COL_LABEL_EDGE,
            linewidth=0.6,
        ),
        zorder=6,
    )
    ax.text(
        APP_XS[3],
        BROKER_BOT - 0.30,
        "外部订阅 / 转发",
        fontsize=8.5,
        color=COL_TEXT_BODY,
        ha="center",
        va="top",
        bbox=dict(
            boxstyle="round,pad=0.20",
            facecolor=COL_LABEL_BG,
            edgecolor=COL_LABEL_EDGE,
            linewidth=0.6,
        ),
        zorder=6,
    )

    USER_TOP = Y_USER + 0.65
    draw_arrow(
        ax, APP_XS[2] - 0.20, Y_APPS - BOX_H_APP / 2,
        CENTER_X - 0.20, USER_TOP,
        kind="up",
        rad=-0.10,
    )
    draw_arrow(
        ax, CENTER_X + 0.20, USER_TOP,
        APP_XS[2] + 0.20, Y_APPS - BOX_H_APP / 2,
        kind="down",
        rad=0.10,
        label="HTTPS 控制指令",
        label_pos=(CENTER_X + 1.80, (USER_TOP + Y_APPS - BOX_H_APP / 2) / 2),
        label_fontsize=8.8,
    )

    ax.text(
        6.35,
        15.85,
        "系统数据流架构：终端 → 网关 → 协议转换 → MQTT Broker → 应用层",
        fontsize=13.5,
        color="#1F3550",
        ha="center",
        va="center",
        weight="bold",
    )

    legend_x0 = 0.6
    legend_y0 = -1.10
    items = [
        ("实线 (深蓝)：上行数据流 (telemetry)", COL_UP_ARROW, "-"),
        ("虚线 (橙色)：下行命令流 (command)", COL_DOWN_ARROW, (0, (6, 3))),
        ("点线 (灰色)：本地持久化 (SQLite 双向读写)", COL_STORE_ARROW, (0, (1.5, 2))),
    ]
    for i, (lbl, c, ls) in enumerate(items):
        yy = legend_y0 - i * 0.0
        xx = legend_x0 + i * 4.1
        ax.plot([xx, xx + 0.55], [yy, yy], color=c, linewidth=1.8, linestyle=ls)
        ax.annotate(
            "",
            xy=(xx + 0.62, yy),
            xytext=(xx + 0.50, yy),
            arrowprops=dict(arrowstyle="-|>", color=c, lw=1.8),
        )
        ax.text(xx + 0.78, yy, lbl, fontsize=9, color="#324A66", ha="left", va="center")

    plt.tight_layout(pad=0.4)
    out = "图3-1_系统数据流架构图.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
