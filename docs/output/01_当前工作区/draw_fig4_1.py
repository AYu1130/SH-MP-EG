"""
生成第4章图4-1：软件系统总程序流程图
A4 论文插入，文字小四，Visio 可编辑，简洁紧凑。
"""

from __future__ import annotations
import xml.etree.ElementTree as ET

def el(tag: str, **attrs) -> ET.Element:
    e = ET.Element(tag)
    for k, v in attrs.items():
        e.set(k, str(v))
    return e


def add_text(parent, x, y, text, attrs=None):
    a = {"font-size": "11", "fill": "#333", "text-anchor": "middle",
         "font-family": "宋体, SimSun, sans-serif"}
    if attrs:
        a.update(attrs)
    e = el("text", x=str(x), y=str(y), **{k: str(v) for k, v in a.items()
         if k not in ("text-anchor",)})
    e.set("text-anchor", a.get("text-anchor", "middle"))
    e.text = text
    parent.append(e)


def rect(parent, x, y, w, h, rx=5, fill="#fff", stroke="#ccc", sw=1):
    parent.append(el("rect", x=str(x), y=str(y), width=str(w), height=str(h),
                     rx=str(rx), ry=str(rx), fill=fill, stroke=stroke,
                     **{"stroke-width": str(sw)}))


def diamond(parent, cx, cy, w, h, fill="#fff", stroke="#999", sw=1):
    hw, hh = w / 2, h / 2
    pts = f"{cx},{cy - hh} {cx + hw},{cy} {cx},{cy + hh} {cx - hw},{cy}"
    parent.append(el("polygon", points=pts, fill=fill, stroke=stroke,
                     **{"stroke-width": str(sw)}))


def arrow_v(parent, x, y1, y2, color="#2B579A", sw=1.2, dash=None):
    attrs = {"stroke": color, "stroke-width": str(sw)}
    if dash:
        attrs["stroke-dasharray"] = dash
    parent.append(el("line", x1=str(x), y1=str(y1), x2=str(x), y2=str(y2 - 6),
                     **attrs))
    parent.append(el("polygon",
                     points=f"{x - 5},{y2 - 7} {x + 5},{y2 - 7} {x},{y2}",
                     fill=color))


def arrow_h(parent, x1, y, x2, color="#2B579A", sw=1.2, dash=None):
    attrs = {"stroke": color, "stroke-width": str(sw)}
    if dash:
        attrs["stroke-dasharray"] = dash
    parent.append(el("line", x1=str(x1), y1=str(y), x2=str(x2 - 6), y2=str(y),
                     **attrs))
    parent.append(el("polygon",
                     points=f"{x2 - 7},{y - 4} {x2 - 7},{y + 4} {x2},{y}",
                     fill=color))


C_BLUE = "#2B579A"
C_GREEN = "#4A8B5A"
C_ORANGE = "#C07030"
C_GRAY = "#888888"
C_LIGHT = "#F2F6FA"
C_RED = "#C44A4A"


def build_flow() -> ET.Element:
    W, H = 660, 720
    svg = el("svg", xmlns="http://www.w3.org/2000/svg",
             width=str(W), height=str(H), viewBox=f"0 0 {W} {H}")
    svg.append(el("rect", x="0", y="0", width=str(W), height=str(H), fill="#FFFFFF"))

    add_text(svg, W // 2, 26, "图4-1  软件系统总程序流程图",
             {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"})

    # ====== 左侧：启动初始化列 ======
    L_X = 80
    L_W = 150
    L_BH = 36

    def start_box(y, text, color=C_BLUE):
        rect(svg, L_X, y, L_W, L_BH, rx=6, fill=C_LIGHT, stroke=color, sw=1.2)
        add_text(svg, L_X + L_W / 2, y + L_BH / 2 + 5, text,
                 {"font-size": "11", "fill": "#333", "font-weight": "bold"})

    sy = 48
    boxes = [
        "解析命令行参数",
        "装配全局配置",
        "初始化日志 / SQLite",
        "连接 EMQX Broker",
        "并发拉起适配器",
    ]
    for i, b in enumerate(boxes):
        y = sy + i * 52
        start_box(y, b)
        if i < len(boxes) - 1:
            arrow_v(svg, L_X + L_W / 2, y + L_BH, y + 50, C_BLUE)

    # ====== 中间：双适配器并行区 ======
    MX = 310
    # Wi-Fi 适配器
    WIFI_X = MX - 110
    BLE_X = MX + 110
    AD_W = 140
    AD_H = 50

    # "并发拉起" → Wi-Fi
    arrow_h(svg, L_X + L_W, sy + 4 * 52 + 18, WIFI_X - 8, C_BLUE)
    # "并发拉起" → BLE
    arrow_h(svg, L_X + L_W, sy + 4 * 52 + 18 + 8, BLE_X - 8, C_BLUE)

    # Wi-Fi 适配器块
    ay = sy + 4 * 52 + 44
    rect(svg, WIFI_X - AD_W / 2, ay, AD_W, AD_H, rx=6, fill="#FFFFFF", stroke=C_GREEN, sw=1.5)
    add_text(svg, WIFI_X, ay + 18, "Wi-Fi 适配器", {"font-size": "11", "fill": C_GREEN, "font-weight": "bold"})
    add_text(svg, WIFI_X, ay + 38, "TCP Socket / HTTP 接收", {"font-size": "9", "fill": "#666"})

    # BLE 适配器块
    rect(svg, BLE_X - AD_W / 2, ay, AD_W, AD_H, rx=6, fill="#FFFFFF", stroke=C_ORANGE, sw=1.5)
    add_text(svg, BLE_X, ay + 18, "BLE 适配器", {"font-size": "11", "fill": C_ORANGE, "font-weight": "bold"})
    add_text(svg, BLE_X, ay + 38, "Bleak GATT 扫描/接收", {"font-size": "9", "fill": "#666"})

    # ====== 汇聚：协议转换 ======
    CONV_X = MX
    CONV_Y = ay + AD_H + 26
    CONV_W = 240
    CONV_H = 42

    arrow_v(svg, WIFI_X, ay + AD_H, CONV_Y, C_GREEN)
    arrow_v(svg, BLE_X, ay + AD_H, CONV_Y, C_ORANGE)

    # 汇聚标签
    add_text(svg, WIFI_X, CONV_Y - 6, "原始数据帧",
             {"font-size": "9", "fill": C_GREEN, "text-anchor": "middle"})
    add_text(svg, BLE_X, CONV_Y - 6, "原始数据帧",
             {"font-size": "9", "fill": C_ORANGE, "text-anchor": "middle"})

    rect(svg, CONV_X - CONV_W / 2, CONV_Y, CONV_W, CONV_H, rx=6,
         fill="#EAF0F7", stroke=C_BLUE, sw=1.5)
    add_text(svg, CONV_X, CONV_Y + 18, "数据转换与校验", {"font-size": "11", "fill": C_BLUE, "font-weight": "bold"})
    add_text(svg, CONV_X, CONV_Y + 36, "JSON映射 / 单位标准化 / jsonschema校验",
             {"font-size": "9", "fill": "#555"})

    # ====== MQTT 发布 ======
    MQTT_Y = CONV_Y + CONV_H + 24
    MQTT_W = 200
    arrow_v(svg, CONV_X, CONV_Y + CONV_H, MQTT_Y, C_BLUE)

    rect(svg, CONV_X - MQTT_W / 2, MQTT_Y, MQTT_W, 44, rx=6,
         fill="#FFFFFF", stroke=C_BLUE, sw=1.5)
    add_text(svg, CONV_X, MQTT_Y + 18, "MQTT 发布器 (上行回调)",
             {"font-size": "11", "fill": C_BLUE, "font-weight": "bold"})
    add_text(svg, CONV_X, MQTT_Y + 36, "paho-mqtt → EMQX Broker",
             {"font-size": "9", "fill": "#666"})

    # ====== 右侧：EMQX + 消费端 ======
    EMQX_X = 570
    EMQX_Y = CONV_Y
    EMQX_W = 72

    rect(svg, EMQX_X - EMQX_W / 2, EMQX_Y, EMQX_W, 130, rx=8,
         fill=C_LIGHT, stroke=C_BLUE, sw=2)
    add_text(svg, EMQX_X, EMQX_Y + 22, "EMQX", {"font-size": "11", "fill": C_BLUE, "font-weight": "bold"})
    add_text(svg, EMQX_X, EMQX_Y + 42, "消息", {"font-size": "10", "fill": "#555"})
    add_text(svg, EMQX_X, EMQX_Y + 58, "代理", {"font-size": "10", "fill": "#555"})

    # 发布器 → EMQX
    arrow_h(svg, CONV_X + MQTT_W / 2, MQTT_Y + 22, EMQX_X - EMQX_W / 2, C_BLUE)
    add_text(svg, CONV_X + MQTT_W / 2 + (EMQX_X - EMQX_W / 2 - CONV_X - MQTT_W / 2) / 2,
             MQTT_Y + 10, "publish", {"font-size": "8", "fill": C_BLUE})

    # EMQX 订阅者
    SUB_Y1 = EMQX_Y + 6
    SUB_Y2 = EMQX_Y + 55
    SUB_Y3 = EMQX_Y + 104
    SUB_X = EMQX_X + EMQX_W / 2 + 8
    SUB_W = 60

    # Node-RED
    rect(svg, SUB_X, SUB_Y1, SUB_W, 30, rx=4, fill="#FFFFFF", stroke=C_GREEN, sw=1)
    add_text(svg, SUB_X + SUB_W / 2, SUB_Y1 + 20, "Node-RED",
             {"font-size": "9", "fill": C_GREEN, "font-weight": "bold"})
    arrow_h(svg, EMQX_X + EMQX_W / 2, SUB_Y1 + 15, SUB_X, C_GREEN, 1, "3,3")

    # Web 后台
    rect(svg, SUB_X, SUB_Y2, SUB_W, 30, rx=4, fill="#FFFFFF", stroke=C_ORANGE, sw=1)
    add_text(svg, SUB_X + SUB_W / 2, SUB_Y2 + 20, "Web 后台",
             {"font-size": "9", "fill": C_ORANGE, "font-weight": "bold"})
    arrow_h(svg, EMQX_X + EMQX_W / 2, SUB_Y2 + 15, SUB_X, C_ORANGE, 1, "3,3")

    # SQLite
    rect(svg, SUB_X, SUB_Y3, SUB_W, 30, rx=4, fill="#FFFFFF", stroke=C_GRAY, sw=1)
    add_text(svg, SUB_X + SUB_W / 2, SUB_Y3 + 20, "SQLite",
             {"font-size": "9", "fill": C_GRAY, "font-weight": "bold"})
    arrow_h(svg, EMQX_X + EMQX_W / 2, SUB_Y3 + 15, SUB_X, C_GRAY, 1, "3,3")

    # ====== 下行控制流（返回） ======
    # EMQX → MQTT 发布器 (command subscribe)
    CMD_Y = MQTT_Y + 60
    arrow_h(svg, EMQX_X - EMQX_W / 2, CMD_Y, CONV_X + MQTT_W / 2, C_RED, 1.2, "4,3")
    add_text(svg, CONV_X, CMD_Y - 6, "command 主题 (下行)",
             {"font-size": "9", "fill": C_RED})

    # 分发判断菱形
    DISP_Y = CMD_Y + 24
    DISP_X = CONV_X
    DISP_W = 120
    DISP_H = 50
    diamond(svg, DISP_X, DISP_Y + DISP_H / 2, DISP_W, DISP_H,
            fill="#FFF5F5", stroke=C_RED, sw=1.2)
    add_text(svg, DISP_X, DISP_Y + DISP_H / 2, "指令分发",
             {"font-size": "10", "fill": C_RED, "font-weight": "bold"})

    arrow_v(svg, CONV_X, CMD_Y, DISP_Y, C_RED, 1.2, "3,3")

    # 下行回到两个适配器
    WIFI_DOWN_Y = DISP_Y + DISP_H / 2 - 10
    BLE_DOWN_Y = DISP_Y + DISP_H / 2 + 10

    arrow_h(svg, DISP_X - DISP_W / 2, WIFI_DOWN_Y, WIFI_X - AD_W / 2, C_RED, 1.2, "4,3")
    add_text(svg, (DISP_X - DISP_W / 2 + WIFI_X - AD_W / 2) / 2, WIFI_DOWN_Y - 8,
             "Wi-Fi 指令", {"font-size": "8", "fill": C_RED})

    arrow_h(svg, DISP_X - DISP_W / 2, BLE_DOWN_Y, BLE_X - AD_W / 2, C_RED, 1.2, "4,3")
    add_text(svg, (DISP_X - DISP_W / 2 + BLE_X - AD_W / 2) / 2, BLE_DOWN_Y - 8,
             "BLE 指令", {"font-size": "8", "fill": C_RED})

    # 下行到终端的标注
    DOWN_LABEL_Y = WIFI_DOWN_Y - 6
    add_text(svg, WIFI_X, ay - 10, "⬆ 传感器数据上报",
             {"font-size": "9", "fill": C_GREEN})
    add_text(svg, WIFI_X, ay + AD_H + 6 - 28, "⬇ 控制指令下发",
             {"font-size": "9", "fill": C_RED})

    # ====== 图例 ======
    legend_y = 620
    # 上行
    svg.append(el("line", x1="120", y1=str(legend_y), x2="170", y2=str(legend_y),
                  stroke=C_BLUE, **{"stroke-width": "1.5"}))
    svg.append(el("polygon", points=f"170,{legend_y - 4} 170,{legend_y + 4} 180,{legend_y}",
                  fill=C_BLUE))
    add_text(svg, 240, legend_y + 5, "上行数据流",
             {"font-size": "10", "fill": "#555", "font-weight": "bold", "text-anchor": "start"})

    # 下行
    ly2 = legend_y + 22
    svg.append(el("line", x1="120", y1=str(ly2), x2="170", y2=str(ly2),
                  stroke=C_RED, **{"stroke-width": "1.5"}, **{"stroke-dasharray": "4,3"}))
    svg.append(el("polygon", points=f"170,{ly2 - 4} 170,{ly2 + 4} 180,{ly2}",
                  fill=C_RED))
    add_text(svg, 240, ly2 + 5, "下行控制流",
             {"font-size": "10", "fill": "#555", "font-weight": "bold", "text-anchor": "start"})

    # 并行
    ly3 = legend_y + 44
    svg.append(el("line", x1="370", y1=str(ly3), x2="420", y2=str(ly3),
                  stroke=C_GREEN, **{"stroke-width": "1.5"}))
    add_text(svg, 430, ly3 + 5, "Wi-Fi 路径",
             {"font-size": "10", "fill": C_GREEN, "font-weight": "bold", "text-anchor": "start"})
    svg.append(el("line", x1="500", y1=str(ly3), x2="550", y2=str(ly3),
                  stroke=C_ORANGE, **{"stroke-width": "1.5"}))
    add_text(svg, 560, ly3 + 5, "BLE 路径",
             {"font-size": "10", "fill": C_ORANGE, "font-weight": "bold", "text-anchor": "start"})

    # 底部说明
    add_text(svg, W // 2, legend_y + 80, "运行模型：MainThread 主控 + Wi-Fi 适配 asyncio + BLE 适配 asyncio + MQTT 发布线程",
             {"font-size": "10", "fill": C_GRAY})

    return svg


def save(svg_e: ET.Element, path: str):
    ET.indent(svg_e, space="  ", level=0)
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(ET.tostring(svg_e, encoding="unicode"))


def main():
    base = (
        r"e:\100_study\120_Project\CapstoneProject"
        r"\SmartHome_MultiProtocol_EdgeIntelligent_Gateway"
        r"\SH-MP-EG\docs\output\01_当前工作区"
    )
    s = build_flow()
    save(s, base + r"\图4-1_软件系统总程序流程图.svg")
    print("saved: 图4-1_软件系统总程序流程图.svg")


if __name__ == "__main__":
    main()
