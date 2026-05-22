"""
图3-4 硬件系统连接框图
======================
依据：
  - 论文 §3.2 硬件平台设计 (树莓派 4B / ESP32-S3 / STM32F103)
  - 项目实际外设：
      ESP32-S3 节点：DHT 温湿度（单总线 GPIO）+ 蜂鸣器（PWM GPIO）
      STM32F103 节点：HM-10 透传（UART 9600）+ GY-302/BH1750（I²C）+ LED（GPIO）
  - 网络拓扑：家用 Wi-Fi 路由器 ←(2.4GHz Wi-Fi)→ ESP32
              家用 Wi-Fi 路由器 ←(RJ45 千兆 / 802.11ac)→ 树莓派
              树莓派内置 BT5 ←(BLE GATT FFE0/FFE1)→ HM-10 → STM32

视觉表达：
  - 实线（青蓝）：有线数字总线（I²C / UART / GPIO / RJ45）
  - 虚线（橙红）：2.4GHz 无线链路（Wi-Fi / BLE）
  - 粗实线（暖橙）：供电链路（USB-C 5V/3A、3.3V LDO）
  - 点线（灰）：存储链路（microSD SD bus）

画幅：约 13×13 in，方正，便于插入论文。
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


COL_ROUTER = "#5A7A9F"
COL_WIFI_NODE = "#7AA66A"
COL_PI = "#C04A4A"
COL_BLE_NODE = "#C28A4A"
COL_PERIPHERAL = "#5BA199"

COL_LINE_WIRE = "#2E5A8C"
COL_LINE_WIRELESS = "#D44A4A"
COL_LINE_BLE = "#A055B0"
COL_LINE_POWER = "#D08020"
COL_LINE_STORAGE = "#7A8896"

COL_BG_BOX = "#FFFFFF"
COL_TITLE_TEXT = "#FFFFFF"
COL_BODY_TEXT = "#1F3550"
COL_LABEL_BG = "#FFFFFF"
COL_LABEL_EDGE = "#C0D0E0"


def draw_main_block(
    ax,
    cx,
    cy,
    w,
    h,
    title,
    spec_lines,
    title_color,
    icon=None,
):
    """大块：MCU 主块（含 title bar + spec lines）。返回内部内容区的 (bottom_y, available_w)。"""
    x = cx - w / 2
    y = cy - h / 2
    outer = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=1.8,
        edgecolor=title_color,
        facecolor=COL_BG_BOX,
        zorder=3,
    )
    ax.add_patch(outer)

    title_h = 0.55
    bar = FancyBboxPatch(
        (x + 0.06, y + h - title_h - 0.06),
        w - 0.12,
        title_h,
        boxstyle="round,pad=0.0,rounding_size=0.10",
        linewidth=0,
        edgecolor="none",
        facecolor=title_color,
        zorder=4,
    )
    ax.add_patch(bar)

    if icon:
        ax.text(
            x + 0.34,
            y + h - title_h / 2 - 0.06,
            icon,
            fontsize=13,
            color=COL_TITLE_TEXT,
            ha="center",
            va="center",
            weight="bold",
            zorder=5,
        )
        title_x = x + 0.62
        title_ha = "left"
    else:
        title_x = cx
        title_ha = "center"

    ax.text(
        title_x,
        y + h - title_h / 2 - 0.06,
        title,
        fontsize=12,
        color=COL_TITLE_TEXT,
        ha=title_ha,
        va="center",
        weight="bold",
        zorder=5,
    )

    spec_top = y + h - title_h - 0.20
    spec_count = len(spec_lines)
    spec_band_h = 0.35 * spec_count
    step = 0.35
    for i, line in enumerate(spec_lines):
        yy = spec_top - step * (i + 0.5)
        ax.text(
            cx,
            yy,
            line,
            fontsize=9,
            color=COL_BODY_TEXT,
            ha="center",
            va="center",
            zorder=5,
        )

    content_top = spec_top - spec_band_h - 0.10
    content_bot = y + 0.20
    return content_top, content_bot, x + 0.20, x + w - 0.20


def draw_sub_block(ax, cx, cy, w, h, title, sub_desc, color):
    """小块：传感器/执行器/外设。"""
    x = cx - w / 2
    y = cy - h / 2
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.0,
        edgecolor=color,
        facecolor="#EAF4EE" if color == COL_PERIPHERAL else "#F4ECDD",
        zorder=4,
    )
    ax.add_patch(box)
    ax.text(
        cx,
        cy + h * 0.18,
        title,
        fontsize=9.5,
        color=COL_BODY_TEXT,
        ha="center",
        va="center",
        weight="bold",
        zorder=5,
    )
    if sub_desc:
        ax.text(
            cx,
            cy - h * 0.22,
            sub_desc,
            fontsize=8.5,
            color="#445566",
            ha="center",
            va="center",
            zorder=5,
        )


def draw_link(
    ax,
    x1,
    y1,
    x2,
    y2,
    kind="wire",
    label=None,
    label_pos=None,
    rad=0.0,
    bidir=True,
    label_fontsize=9,
    zorder=2,
):
    """绘制连接线。kind ∈ {'wire','wireless','ble','power','storage'}"""
    if kind == "wire":
        color = COL_LINE_WIRE
        ls = "-"
        lw = 1.7
    elif kind == "wireless":
        color = COL_LINE_WIRELESS
        ls = (0, (6, 4))
        lw = 2.0
    elif kind == "ble":
        color = COL_LINE_BLE
        ls = (0, (6, 4))
        lw = 2.0
    elif kind == "power":
        color = COL_LINE_POWER
        ls = "-"
        lw = 2.4
    else:
        color = COL_LINE_STORAGE
        ls = (0, (1.5, 2))
        lw = 1.4

    arrowstyle = "<|-|>" if bidir else "-|>"
    arrow = FancyArrowPatch(
        (x1, y1),
        (x2, y2),
        arrowstyle=arrowstyle,
        mutation_scale=14,
        linewidth=lw,
        color=color,
        linestyle=ls,
        connectionstyle=f"arc3,rad={rad}",
        zorder=zorder,
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
            color=COL_BODY_TEXT,
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


def main():
    fig, ax = plt.subplots(figsize=(13, 13.2), dpi=180)
    ax.set_xlim(-0.3, 14.0)
    ax.set_ylim(-1.55, 14.0)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ROUTER_CX = 6.85
    ROUTER_CY = 12.55
    ROUTER_W = 9.0
    ROUTER_H = 1.65

    ESP_CX = 2.10
    PI_CX = 6.85
    STM_CX = 11.60
    BLOCK_CY = 6.10
    BLOCK_W = 3.85
    BLOCK_H = 8.10

    draw_main_block(
        ax,
        ROUTER_CX,
        ROUTER_CY,
        ROUTER_W,
        ROUTER_H,
        "家庭 Wi-Fi 路由器（家庭局域网核心）",
        [
            "802.11ac 双频 (2.4GHz + 5GHz)   ·   千兆 RJ45 LAN×4",
            "提供 DHCP / NAT / 互联网上行（可选云端转发出口）",
        ],
        COL_ROUTER,
        icon="R",
    )

    esp_content_top, esp_content_bot, esp_xl, esp_xr = draw_main_block(
        ax,
        ESP_CX,
        BLOCK_CY,
        BLOCK_W,
        BLOCK_H,
        "Wi-Fi 终端节点",
        [
            "MCU：ESP32-S3",
            "Xtensa LX7 双核 240MHz",
            "Flash 8MB / SRAM 512KB",
            "无线：Wi-Fi b/g/n + BT5",
        ],
        COL_WIFI_NODE,
        icon="W",
    )

    draw_sub_block(ax, ESP_CX, 5.55, BLOCK_W - 0.55, 1.05,
                   "DHT 温湿度传感器",
                   "GPIO 单总线（One-Wire）", COL_PERIPHERAL)

    draw_sub_block(ax, ESP_CX, 4.05, BLOCK_W - 0.55, 1.05,
                   "板载蜂鸣器",
                   "GPIO PWM（声音报警）", COL_PERIPHERAL)

    draw_sub_block(ax, ESP_CX, 2.55, BLOCK_W - 0.55, 1.05,
                   "USB-C 接口",
                   "供电 5V / 编程下载", COL_BLE_NODE)

    pi_content_top, pi_content_bot, pi_xl, pi_xr = draw_main_block(
        ax,
        PI_CX,
        BLOCK_CY,
        BLOCK_W,
        BLOCK_H,
        "网关主控：树莓派 4B",
        [
            "SoC：BCM2711 四核 Cortex-A72",
            "主频 1.5GHz · 4GB LPDDR4",
            "网络：千兆以太网 + 802.11ac",
            "无线：Bluetooth 5.0 内置",
            "GPIO 40-pin · USB 2.0 / 3.0",
        ],
        COL_PI,
        icon="Pi",
    )

    draw_sub_block(ax, PI_CX, 5.20, BLOCK_W - 0.55, 1.00,
                   "microSD（32GB）",
                   "系统盘：Raspberry Pi OS", COL_PERIPHERAL)

    draw_sub_block(ax, PI_CX, 3.85, BLOCK_W - 0.55, 1.00,
                   "USB-C 5V/3A 电源",
                   "适配器或 PoE HAT 供电", COL_BLE_NODE)

    draw_sub_block(ax, PI_CX, 2.50, BLOCK_W - 0.55, 1.00,
                   "GPIO 40-pin 排针",
                   "（备用扩展 / 调试接口）", COL_PERIPHERAL)

    stm_content_top, stm_content_bot, stm_xl, stm_xr = draw_main_block(
        ax,
        STM_CX,
        BLOCK_CY,
        BLOCK_W,
        BLOCK_H,
        "BLE 终端节点",
        [
            "MCU：STM32F103",
            "Cortex-M3 72MHz",
            "Flash 64KB / SRAM 20KB",
            "供电：5V → 3.3V LDO",
        ],
        COL_BLE_NODE,
        icon="B",
    )

    draw_sub_block(ax, STM_CX, 5.55, BLOCK_W - 0.55, 1.05,
                   "HM-10 蓝牙透传模块",
                   "UART TX/RX · 9600 bps", COL_PERIPHERAL)

    draw_sub_block(ax, STM_CX, 4.05, BLOCK_W - 0.55, 1.05,
                   "GY-302（BH1750）光照",
                   "I²C 总线（SDA/SCL）", COL_PERIPHERAL)

    draw_sub_block(ax, STM_CX, 2.55, BLOCK_W - 0.55, 1.05,
                   "LED 指示灯",
                   "GPIO 数字输出 / PWM", COL_PERIPHERAL)

    ROUTER_BOT = ROUTER_CY - ROUTER_H / 2
    ESP_TOP = BLOCK_CY + BLOCK_H / 2
    PI_TOP = BLOCK_CY + BLOCK_H / 2
    STM_TOP = BLOCK_CY + BLOCK_H / 2

    draw_link(
        ax,
        ROUTER_CX - 2.4,
        ROUTER_BOT,
        ESP_CX + 0.4,
        ESP_TOP,
        kind="wireless",
        label="Wi-Fi 2.4GHz (802.11n)\nESP32 与 路由器 上行",
        label_pos=(3.55, 11.32),
        bidir=True,
        label_fontsize=8.8,
    )
    draw_link(
        ax,
        ROUTER_CX,
        ROUTER_BOT,
        PI_CX,
        PI_TOP,
        kind="wire",
        label="千兆以太网 RJ45\n（或 802.11ac Wi-Fi 备用）",
        label_pos=(PI_CX + 1.40, 11.00),
        bidir=True,
        label_fontsize=8.8,
    )

    ble_y = 7.05
    draw_link(
        ax,
        PI_CX + BLOCK_W / 2 - 0.05,
        ble_y,
        STM_CX - BLOCK_W / 2 + 0.05,
        ble_y,
        kind="ble",
        label="BLE GATT · 2.4GHz\nFFE0 / FFE1 · 9600 bps",
        label_pos=((PI_CX + STM_CX) / 2, ble_y - 0.40),
        bidir=True,
        label_fontsize=8.8,
    )

    def vlink(ax_, x, y_top, y_bot, kind, bidir=False):
        draw_link(ax_, x, y_top, x, y_bot, kind=kind, bidir=bidir,
                  label=None, zorder=3.5)

    def vlabel(ax_, x, y, txt, accent=False, ha="left"):
        ax_.text(
            x, y, txt,
            fontsize=8.5,
            color="#A2641A" if accent else "#324A66",
            ha=ha, va="center", zorder=7,
            bbox=dict(
                boxstyle="round,pad=0.22",
                facecolor="white",
                edgecolor="#E4B879" if accent else COL_LABEL_EDGE,
                linewidth=0.8,
            ),
        )

    esp_top_subs = [(5.55, 1.05), (4.05, 1.05), (2.55, 1.05)]
    pi_top_subs = [(5.20, 1.00), (3.85, 1.00), (2.50, 1.00)]
    stm_top_subs = [(5.55, 1.05), (4.05, 1.05), (2.55, 1.05)]

    e1y_top = esp_top_subs[0][0] + esp_top_subs[0][1] / 2
    e1y_bot = esp_top_subs[0][0] - esp_top_subs[0][1] / 2
    e2y_top = esp_top_subs[1][0] + esp_top_subs[1][1] / 2
    e2y_bot = esp_top_subs[1][0] - esp_top_subs[1][1] / 2
    e3y_top = esp_top_subs[2][0] + esp_top_subs[2][1] / 2

    vlink(ax, ESP_CX + 0.18, esp_content_top - 0.08, e1y_top, kind="wire", bidir=False)
    vlink(ax, ESP_CX + 0.18, e1y_bot, e2y_top, kind="wire", bidir=False)
    vlink(ax, ESP_CX + 0.18, e2y_bot, e3y_top, kind="power", bidir=False)

    vlabel(ax, ESP_CX + 1.05, (esp_content_top + e1y_top) / 2, "单总线 GPIO")
    vlabel(ax, ESP_CX + 1.05, (e1y_bot + e2y_top) / 2, "GPIO PWM")
    vlabel(ax, ESP_CX + 1.05, (e2y_bot + e3y_top) / 2, "USB-C 5V", accent=True)

    p1y_top = pi_top_subs[0][0] + pi_top_subs[0][1] / 2
    p1y_bot = pi_top_subs[0][0] - pi_top_subs[0][1] / 2
    p2y_top = pi_top_subs[1][0] + pi_top_subs[1][1] / 2
    p2y_bot = pi_top_subs[1][0] - pi_top_subs[1][1] / 2
    p3y_top = pi_top_subs[2][0] + pi_top_subs[2][1] / 2

    vlink(ax, PI_CX - 0.18, pi_content_top - 0.08, p1y_top, kind="storage", bidir=False)
    vlink(ax, PI_CX - 0.18, p1y_bot, p2y_top, kind="power", bidir=False)
    vlink(ax, PI_CX - 0.18, p2y_bot, p3y_top, kind="wire", bidir=False)

    vlabel(ax, PI_CX - 1.05, (pi_content_top + p1y_top) / 2, "SD bus", ha="right")
    vlabel(ax, PI_CX - 1.05, (p1y_bot + p2y_top) / 2, "5V/3A DC", accent=True, ha="right")
    vlabel(ax, PI_CX - 1.05, (p2y_bot + p3y_top) / 2, "40-pin GPIO", ha="right")

    s1y_top = stm_top_subs[0][0] + stm_top_subs[0][1] / 2
    s1y_bot = stm_top_subs[0][0] - stm_top_subs[0][1] / 2
    s2y_top = stm_top_subs[1][0] + stm_top_subs[1][1] / 2
    s2y_bot = stm_top_subs[1][0] - stm_top_subs[1][1] / 2
    s3y_top = stm_top_subs[2][0] + stm_top_subs[2][1] / 2

    vlink(ax, STM_CX - 0.18, stm_content_top - 0.08, s1y_top, kind="wire", bidir=True)
    vlink(ax, STM_CX - 0.18, s1y_bot, s2y_top, kind="wire", bidir=True)
    vlink(ax, STM_CX - 0.18, s2y_bot, s3y_top, kind="wire", bidir=False)

    vlabel(ax, STM_CX + 0.30, (stm_content_top + s1y_top) / 2, "UART TX/RX")
    vlabel(ax, STM_CX + 0.30, (s1y_bot + s2y_top) / 2, "I²C SDA/SCL")
    vlabel(ax, STM_CX + 0.30, (s2y_bot + s3y_top) / 2, "GPIO 数字")

    ax.text(
        ROUTER_CX, 13.65,
        "硬件系统连接框图：家用 Wi-Fi 路由器 + ESP32 节点 + 树莓派 4B 网关 + STM32+HM-10 节点",
        fontsize=12.8, color="#1F3550",
        ha="center", va="center", weight="bold",
    )

    legend_items = [
        ("实线 (青蓝)：有线数字总线  I²C / UART / GPIO / RJ45", COL_LINE_WIRE, "-", 1.8),
        ("虚线 (橙红)：Wi-Fi 2.4GHz 无线链路 (802.11 b/g/n)", COL_LINE_WIRELESS, (0, (6, 4)), 1.8),
        ("虚线 (紫红)：BLE GATT 蓝牙低功耗链路 (2.4GHz)", COL_LINE_BLE, (0, (6, 4)), 1.8),
        ("粗实线 (暖橙)：直流供电  5V / 3.3V  (USB-C / LDO)", COL_LINE_POWER, "-", 2.4),
        ("点线 (灰色)：存储链路  SD bus  (microSD)", COL_LINE_STORAGE, (0, (1.5, 2)), 1.4),
    ]
    row0_y = -0.45
    row1_y = -1.05
    col_xs = [0.4, 4.8, 9.2]
    positions = [
        (col_xs[0], row0_y),
        (col_xs[1], row0_y),
        (col_xs[2], row0_y),
        (col_xs[0], row1_y),
        (col_xs[1], row1_y),
    ]
    for (lbl, c, ls, lw), (xx, yy) in zip(legend_items, positions):
        ax.plot([xx, xx + 0.55], [yy, yy], color=c, linewidth=lw, linestyle=ls)
        ax.annotate(
            "",
            xy=(xx + 0.65, yy),
            xytext=(xx + 0.50, yy),
            arrowprops=dict(arrowstyle="-|>", color=c, lw=lw),
        )
        ax.text(xx + 0.82, yy, lbl, fontsize=8.6,
                color="#324A66", ha="left", va="center")

    plt.tight_layout(pad=0.4)
    out = "图3-4_硬件系统连接框图.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
