"""
图3-5 软件系统架构图
========================
分层模型 (自顶向下)：
  1. 应用服务层 (Application Service Layer)
  2. 业务逻辑层 (Business Logic Layer)
  3. 协议适配层 (Protocol Adaptation Layer)
  4. 硬件抽象层 (Hardware Abstraction Layer)

模块对应项目实际代码与服务：
  - Flask Admin Web UI (admin_routes.py / templates) - 5000
  - Node-RED 可视化编辑器 - 1880
  - EMQX Dashboard - 18083
  - REST API 接口集合 (Bootstrap UI / JSON)
  - data_converter.py / rules_engine.py / command_router.py / cache_manager.py
  - wifi_receiver.py / ble_receiver.py / paho-mqtt / EMQX Broker
  - Raspberry Pi OS / Linux Net Stack / BlueZ / Python+Node.js+Docker+SQLite

设计要点：
  - 4 层水平色带，每层 4 个模块盒（共 16 模块）
  - 左右两条侧栏分别表达 北向(上行) 与 南向(下行) 数据/控制流
  - 横切关注点 (安全 + 可观测性) 以底部注脚形式呈现
  - 画幅 ~13×13.2 in (方正)，dpi 220
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


COL_APP = "#4A6FB0"
COL_BIZ = "#C04A4A"
COL_PROTO = "#C28A4A"
COL_HAL = "#5A6D80"

COL_APP_BG = "#EAF1FA"
COL_BIZ_BG = "#FCEBEB"
COL_PROTO_BG = "#FBF3E1"
COL_HAL_BG = "#ECF0F4"

COL_UP_ARROW = "#3A8A56"
COL_DOWN_ARROW = "#A24A88"

COL_BODY_TEXT = "#1F3550"
COL_LIGHT_TEXT = "#445566"


def draw_layer_band(ax, x0, x1, y_top, y_bot, color_dark, color_bg, label_zh, label_en):
    """绘制一层水平色带：浅色背景 + 顶部深色标题条。返回内部内容区 (cx, cy, w, h)。"""
    band = FancyBboxPatch(
        (x0, y_bot),
        x1 - x0,
        y_top - y_bot,
        boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=1.2,
        edgecolor=color_dark,
        facecolor=color_bg,
        zorder=2,
    )
    ax.add_patch(band)

    title_h = 0.55
    title_bar = FancyBboxPatch(
        (x0 + 0.05, y_top - title_h - 0.05),
        x1 - x0 - 0.10,
        title_h,
        boxstyle="round,pad=0.0,rounding_size=0.08",
        linewidth=0,
        edgecolor="none",
        facecolor=color_dark,
        zorder=3,
    )
    ax.add_patch(title_bar)

    title_y = y_top - title_h / 2 - 0.05
    ax.text(
        x0 + 0.25, title_y, label_zh,
        fontsize=12.5, color="white", weight="bold",
        ha="left", va="center", zorder=5,
    )
    ax.text(
        x1 - 0.25, title_y, label_en,
        fontsize=10, color="white", weight="bold",
        ha="right", va="center", zorder=5, style="italic",
    )

    inner_top = y_top - title_h - 0.18
    inner_bot = y_bot + 0.18
    inner_left = x0 + 0.18
    inner_right = x1 - 0.18
    return inner_left, inner_right, inner_top, inner_bot


def draw_module(ax, cx, cy, w, h, title, desc_lines, color_dark, icon=None):
    """绘制单个模块盒：白底 + 彩色描边 + 顶部小色块 icon + 标题 + 说明文字。"""
    x = cx - w / 2
    y = cy - h / 2
    box = FancyBboxPatch(
        (x, y),
        w, h,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=1.5,
        edgecolor=color_dark,
        facecolor="white",
        zorder=4,
    )
    ax.add_patch(box)

    title_band_h = 0.42
    if icon:
        icon_size = 0.34
        icon_box = FancyBboxPatch(
            (x + 0.12, y + h - title_band_h / 2 - icon_size / 2 - 0.04),
            icon_size, icon_size,
            boxstyle="round,pad=0.0,rounding_size=0.06",
            linewidth=0,
            facecolor=color_dark,
            zorder=5,
        )
        ax.add_patch(icon_box)
        ax.text(
            x + 0.12 + icon_size / 2,
            y + h - title_band_h / 2 - 0.04,
            icon,
            fontsize=10, color="white", weight="bold",
            ha="center", va="center", zorder=6,
        )

    title_x = x + 0.55 if icon else cx
    title_ha = "left" if icon else "center"
    ax.text(
        title_x, y + h - title_band_h / 2 - 0.04, title,
        fontsize=10.3, color=color_dark, weight="bold",
        ha=title_ha, va="center", zorder=6,
    )

    sep_y = y + h - title_band_h - 0.06
    ax.plot(
        [x + 0.15, x + w - 0.15], [sep_y, sep_y],
        color=color_dark, linewidth=0.7, alpha=0.4, zorder=5,
    )

    n = len(desc_lines)
    desc_top = sep_y - 0.08
    desc_bot = y + 0.12
    if n > 1:
        step = (desc_top - desc_bot) / (n - 1) if n > 1 else 0
        ys = [desc_top - step * i for i in range(n)]
    else:
        ys = [(desc_top + desc_bot) / 2]
    for yy, line in zip(ys, desc_lines):
        ax.text(
            cx, yy,
            line,
            fontsize=8.7, color=COL_BODY_TEXT,
            ha="center", va="center", zorder=6,
        )


def draw_side_arrow(ax, x, y_top, y_bot, color, label_main, label_sub, side="left"):
    """侧边大箭头：贯穿四层，标明北向上行 / 南向下行。"""
    if side == "left":
        arrow = FancyArrowPatch(
            (x, y_bot), (x, y_top),
            arrowstyle="-|>",
            mutation_scale=28,
            linewidth=5.5,
            color=color,
            zorder=8,
        )
    else:
        arrow = FancyArrowPatch(
            (x, y_top), (x, y_bot),
            arrowstyle="-|>",
            mutation_scale=28,
            linewidth=5.5,
            color=color,
            zorder=8,
        )
    ax.add_patch(arrow)

    mid_y = (y_top + y_bot) / 2
    rot = 90 if side == "left" else -90
    ax.text(
        x, mid_y + 1.20, label_main,
        fontsize=11, color=color, weight="bold",
        ha="center", va="center", zorder=9, rotation=rot,
        bbox=dict(boxstyle="round,pad=0.30", facecolor="white",
                  edgecolor=color, linewidth=1.0),
    )
    ax.text(
        x, mid_y - 1.60, label_sub,
        fontsize=8.4, color=color,
        ha="center", va="center", zorder=9, rotation=rot,
        bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                  edgecolor=color, linewidth=0.7),
    )


def draw_interlayer_arrows(ax, x_left, x_right, y_above_bot, y_below_top, n=5):
    """两层之间的细灰色双向小箭头，表示层间接口。"""
    span = x_right - x_left
    for i in range(n):
        xx = x_left + span * (i + 0.5) / n
        arr = FancyArrowPatch(
            (xx, y_above_bot), (xx, y_below_top),
            arrowstyle="<|-|>",
            mutation_scale=10,
            linewidth=1.2,
            color="#9AAAB8",
            alpha=0.75,
            zorder=3,
        )
        ax.add_patch(arr)


def main():
    fig, ax = plt.subplots(figsize=(13, 13.2), dpi=180)
    ax.set_xlim(-0.2, 14.0)
    ax.set_ylim(-1.10, 14.20)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    X_LEFT_ARROW = 0.65
    X_RIGHT_ARROW = 13.20
    BAND_X0 = 1.40
    BAND_X1 = 12.60

    LAYER_HEIGHTS = {
        "app":  (13.15, 10.55),
        "biz":  (10.30,  7.70),
        "proto":(7.45,  4.85),
        "hal":  (4.60,  2.00),
    }

    ax.text(
        (BAND_X0 + BAND_X1) / 2, 13.70,
        "软件系统架构图：四层结构 (应用 / 业务 / 协议 / HAL) + 数据流方向",
        fontsize=13, color=COL_BODY_TEXT, weight="bold",
        ha="center", va="center",
    )

    y_top, y_bot = LAYER_HEIGHTS["app"]
    il, ir, it, ib = draw_layer_band(
        ax, BAND_X0, BAND_X1, y_top, y_bot,
        COL_APP, COL_APP_BG,
        "① 应用服务层",
        "Application Service Layer",
    )
    box_w = (ir - il - 3 * 0.10) / 4
    box_h = it - ib
    cy = (it + ib) / 2
    cxs = [il + box_w / 2 + (box_w + 0.10) * i for i in range(4)]
    draw_module(ax, cxs[0], cy, box_w, box_h,
                "Flask Admin Web",
                ["端口 5000 · Python WSGI",
                 "用户登录 / 节点 CRUD",
                 "规则配置 · 状态实时刷新"],
                COL_APP, icon="W")
    draw_module(ax, cxs[1], cy, box_w, box_h,
                "Node-RED 编辑器",
                ["端口 1880 · Node.js 16+",
                 "可视化 Flow 拖拽 / 部署",
                 "调试面板 · 节点市场"],
                COL_APP, icon="N")
    draw_module(ax, cxs[2], cy, box_w, box_h,
                "EMQX Dashboard",
                ["端口 18083 · Web 控制台",
                 "客户端 / 主题 / 会话监控",
                 "ACL / 认证 / 指标"],
                COL_APP, icon="E")
    draw_module(ax, cxs[3], cy, box_w, box_h,
                "RESTful API + 模板",
                ["admin_routes.py",
                 "GET/POST/PUT/DELETE",
                 "JSON 响应 · Jinja2 模板"],
                COL_APP, icon="A")

    y_top, y_bot = LAYER_HEIGHTS["biz"]
    il, ir, it, ib = draw_layer_band(
        ax, BAND_X0, BAND_X1, y_top, y_bot,
        COL_BIZ, COL_BIZ_BG,
        "② 业务逻辑层",
        "Business Logic Layer",
    )
    cy = (it + ib) / 2
    cxs = [il + box_w / 2 + (box_w + 0.10) * i for i in range(4)]
    draw_module(ax, cxs[0], cy, box_w, box_h,
                "数据融合 / 校验",
                ["data_converter.py",
                 "JSON Schema 字段校验",
                 "字段映射 / 时间戳归一"],
                COL_BIZ, icon="D")
    draw_module(ax, cxs[1], cy, box_w, box_h,
                "规则联动引擎",
                ["rules_engine.py + Node-RED",
                 "IF-THEN 触发条件",
                 "跨协议事件路由"],
                COL_BIZ, icon="R")
    draw_module(ax, cxs[2], cy, box_w, box_h,
                "命令路由 / 下发",
                ["command_router.py",
                 "topic → 协议适配器",
                 "Wi-Fi TCP / BLE GATT 分流"],
                COL_BIZ, icon="C")
    draw_module(ax, cxs[3], cy, box_w, box_h,
                "缓存与用户管理",
                ["cache_manager.py + SQLite",
                 "cache.db (离线消息重传)",
                 "admin.db (用户 / 节点注册)"],
                COL_BIZ, icon="S")

    y_top, y_bot = LAYER_HEIGHTS["proto"]
    il, ir, it, ib = draw_layer_band(
        ax, BAND_X0, BAND_X1, y_top, y_bot,
        COL_PROTO, COL_PROTO_BG,
        "③ 协议适配层",
        "Protocol Adaptation Layer",
    )
    cy = (it + ib) / 2
    cxs = [il + box_w / 2 + (box_w + 0.10) * i for i in range(4)]
    draw_module(ax, cxs[0], cy, box_w, box_h,
                "Wi-Fi 适配器",
                ["wifi_receiver.py",
                 "TCP 长连接 :9000 · HTTP :8080",
                 "asyncio + socket"],
                COL_PROTO, icon="W")
    draw_module(ax, cxs[1], cy, box_w, box_h,
                "BLE GATT 适配器",
                ["ble_receiver.py + bleak",
                 "HM-10 FFE0 / FFE1 特征",
                 "Notify 订阅 + Write 下发"],
                COL_PROTO, icon="B")
    draw_module(ax, cxs[2], cy, box_w, box_h,
                "MQTT 客户端",
                ["paho-mqtt (Python)",
                 "publish + subscribe",
                 "smarthome/v1/* · QoS 1"],
                COL_PROTO, icon="M")
    draw_module(ax, cxs[3], cy, box_w, box_h,
                "EMQX MQTT Broker",
                ["EMQX 5.x · Docker 容器化",
                 "TCP :1883 · WS :8083",
                 "topic ACL · 持久会话"],
                COL_PROTO, icon="X")

    y_top, y_bot = LAYER_HEIGHTS["hal"]
    il, ir, it, ib = draw_layer_band(
        ax, BAND_X0, BAND_X1, y_top, y_bot,
        COL_HAL, COL_HAL_BG,
        "④ 硬件抽象层",
        "Hardware Abstraction Layer (HAL)",
    )
    cy = (it + ib) / 2
    cxs = [il + box_w / 2 + (box_w + 0.10) * i for i in range(4)]
    draw_module(ax, cxs[0], cy, box_w, box_h,
                "Raspberry Pi OS",
                ["Debian 11 Bullseye",
                 "Linux Kernel 6.x · systemd",
                 "SSH 远程 · 静态 IP · Cron"],
                COL_HAL, icon="O")
    draw_module(ax, cxs[1], cy, box_w, box_h,
                "Linux 网络协议栈",
                ["TCP/UDP/IP · BSD socket",
                 "wlan0 · 802.11ac Wi-Fi",
                 "eth0 · 千兆以太网"],
                COL_HAL, icon="N")
    draw_module(ax, cxs[2], cy, box_w, box_h,
                "蓝牙栈 BlueZ",
                ["hci0 · BT 5.0 控制器",
                 "GAP + GATT 客户端",
                 "L2CAP / SMP / bluetoothd"],
                COL_HAL, icon="B")
    draw_module(ax, cxs[3], cy, box_w, box_h,
                "运行时 + 存储",
                ["Python 3.9+ · Node.js 16+",
                 "Docker Engine 容器化",
                 "SQLite 3 · ext4 microSD"],
                COL_HAL, icon="R")

    layers_order = ["app", "biz", "proto", "hal"]
    for i in range(len(layers_order) - 1):
        y_above_bot = LAYER_HEIGHTS[layers_order[i]][1]
        y_below_top = LAYER_HEIGHTS[layers_order[i + 1]][0]
        draw_interlayer_arrows(ax, BAND_X0 + 0.20, BAND_X1 - 0.20,
                                y_above_bot, y_below_top, n=5)

    arrow_top = LAYER_HEIGHTS["app"][0] + 0.05
    arrow_bot = LAYER_HEIGHTS["hal"][1] - 0.05

    draw_side_arrow(
        ax, X_LEFT_ARROW, arrow_top, arrow_bot,
        COL_UP_ARROW,
        "↑  北向上行  Northbound",
        "传感数据：设备 → 网关 → 应用",
        side="left",
    )
    draw_side_arrow(
        ax, X_RIGHT_ARROW, arrow_top, arrow_bot,
        COL_DOWN_ARROW,
        "↓  南向下行  Southbound",
        "控制指令：应用 → 网关 → 设备",
        side="right",
    )

    cross_y = 1.10
    cross_box = FancyBboxPatch(
        (BAND_X0, cross_y - 0.55),
        BAND_X1 - BAND_X0, 1.10,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=1.0,
        edgecolor="#7A8896",
        facecolor="#F4F6F9",
        zorder=2,
    )
    ax.add_patch(cross_box)
    ax.text(
        (BAND_X0 + BAND_X1) / 2, cross_y + 0.32,
        "⑤ 横切关注点 (Cross-Cutting Concerns)",
        fontsize=11, color="#324A66", weight="bold",
        ha="center", va="center",
    )

    cross_items = [
        ("安全", "session 登录 · bcrypt · MQTT ACL"),
        ("可观测性", "logging · EMQX 指标 · 心跳"),
        ("配置管理", "config.py · 环境变量 · systemd"),
    ]
    n_cross = len(cross_items)
    cross_w = (BAND_X1 - BAND_X0 - 0.4) / n_cross
    for i, (title, desc) in enumerate(cross_items):
        col_left = BAND_X0 + 0.20 + cross_w * i
        ax.text(
            col_left + 0.10, cross_y - 0.10, title + "：",
            fontsize=9.8, color="#1F3550", weight="bold",
            ha="left", va="center",
        )
        ax.text(
            col_left + 1.05, cross_y - 0.10, desc,
            fontsize=8.6, color=COL_LIGHT_TEXT,
            ha="left", va="center",
        )

    legend_y = -0.70
    ax.plot([1.6, 2.0], [legend_y, legend_y], color=COL_UP_ARROW, linewidth=4)
    ax.annotate("", xy=(2.10, legend_y), xytext=(1.95, legend_y),
                arrowprops=dict(arrowstyle="-|>", color=COL_UP_ARROW, lw=4))
    ax.text(2.25, legend_y, "↑ 北向/上行：传感数据 (Wi-Fi/BLE → 网关 → MQTT → Web/Node-RED)",
            fontsize=9, color=COL_UP_ARROW, ha="left", va="center", weight="bold")

    ax.plot([8.0, 8.4], [legend_y, legend_y], color=COL_DOWN_ARROW, linewidth=4)
    ax.annotate("", xy=(8.50, legend_y), xytext=(8.35, legend_y),
                arrowprops=dict(arrowstyle="-|>", color=COL_DOWN_ARROW, lw=4))
    ax.text(8.65, legend_y, "↓ 南向/下行：控制指令 (Web/规则 → MQTT → 适配器 → 设备)",
            fontsize=9, color=COL_DOWN_ARROW, ha="left", va="center", weight="bold")

    plt.tight_layout(pad=0.4)
    out = "图3-5_软件系统架构图.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
