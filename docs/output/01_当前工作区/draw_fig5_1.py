"""
生成第5章图5.1：测试环境网络拓扑图
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

def rect(parent, x, y, w, h, rx=6, fill="#fff", stroke="#ccc", sw=1.2):
    parent.append(el("rect", x=str(x), y=str(y), width=str(w), height=str(h),
                     rx=str(rx), ry=str(rx), fill=fill, stroke=stroke,
                     **{"stroke-width": str(sw)}))

def line_arrow(parent, x1, y1, x2, y2, color="#555", sw=1.2, dash=None,
               label="", label_offset=0):
    attrs = {"stroke": color, "stroke-width": str(sw)}
    if dash:
        attrs["stroke-dasharray"] = dash
    parent.append(el("line", x1=str(x1), y1=str(y1), x2=str(x2), y2=str(y2),
                     **attrs))
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 + label_offset
        add_text(parent, mx, my, label,
                 {"font-size": "9", "fill": color, "font-weight": "bold"})


C_BLUE  = "#2B579A"
C_GREEN = "#4A8B5A"
C_ORANGE = "#C07030"
C_GRAY  = "#888888"
C_LIGHT = "#F2F6FA"

def build_topology() -> ET.Element:
    W, H = 620, 440
    svg = el("svg", xmlns="http://www.w3.org/2000/svg",
             width=str(W), height=str(H), viewBox=f"0 0 {W} {H}")
    svg.append(el("rect", x="0", y="0", width=str(W), height=str(H), fill="#FFFFFF"))

    add_text(svg, W // 2, 26, "图5.1  测试环境网络拓扑图",
             {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"})

    # ====== 路由器（中央上方） ======
    R_X, R_Y, R_W, R_H = 280, 55, 100, 48
    rect(svg, R_X, R_Y, R_W, R_H, rx=8, fill="#EAF0F7", stroke=C_BLUE, sw=1.8)
    add_text(svg, R_X + R_W / 2, R_Y + 20, "千兆无线路由器",
             {"font-size": "11", "fill": C_BLUE, "font-weight": "bold"})
    add_text(svg, R_X + R_W / 2, R_Y + 38, "192.168.1.0/24",
             {"font-size": "9", "fill": "#666"})

    # ====== 网关（中部偏左） ======
    G_X, G_Y, G_W, G_H = 50, 200, 150, 80
    rect(svg, G_X, G_Y, G_W, G_H, rx=8, fill=C_LIGHT, stroke=C_BLUE, sw=2)
    add_text(svg, G_X + G_W / 2, G_Y + 24, "树莓派 4B  (2GB)", {"font-size": "12", "fill": C_BLUE, "font-weight": "bold"})
    add_text(svg, G_X + G_W / 2, G_Y + 44, "网关核心软件", {"font-size": "10", "fill": "#333"})
    add_text(svg, G_X + G_W / 2, G_Y + 62, "EMQX / Node-RED / Python 3.9", {"font-size": "9", "fill": "#666"})

    # 路由器 ←→ 网关（千兆以太网）
    line_arrow(svg, R_X + R_W / 2, R_Y + R_H, G_X + G_W / 2, G_Y,
               C_BLUE, 1.5, None, "千兆以太网", 12)

    # ====== Wi-Fi 终端（右上方） ======
    W_X, W_Y, W_W, W_H = 410, 160, 160, 76
    rect(svg, W_X, W_Y, W_W, W_H, rx=8, fill="#E8F0E8", stroke=C_GREEN, sw=1.5)
    add_text(svg, W_X + W_W / 2, W_Y + 22, "ESP32-S3", {"font-size": "11", "fill": C_GREEN, "font-weight": "bold"})
    add_text(svg, W_X + W_W / 2, W_Y + 42, "SHT30  +  BH1750", {"font-size": "10", "fill": "#333"})
    add_text(svg, W_X + W_W / 2, W_Y + 64, "Wi-Fi  Station 模式", {"font-size": "9", "fill": "#666"})

    # 路由器 ←→ ESP32（2.4GHz Wi-Fi，曲线标注）
    line_arrow(svg, R_X + R_W, R_Y + R_H / 2, W_X, W_Y + W_H / 2,
               C_GREEN, 1.5, "4,3", "2.4 GHz Wi-Fi", 0)

    # ====== BLE 终端（左下方） ======
    B_X, B_Y, B_W, B_H = 50, 340, 150, 76
    rect(svg, B_X, B_Y, B_W, B_H, rx=8, fill="#FFF3E8", stroke=C_ORANGE, sw=1.5)
    add_text(svg, B_X + B_W / 2, B_Y + 22, "STM32F103C8T6", {"font-size": "11", "fill": C_ORANGE, "font-weight": "bold"})
    add_text(svg, B_X + B_W / 2, B_Y + 42, "HM-10 蓝牙模块", {"font-size": "10", "fill": "#333"})
    add_text(svg, B_X + B_W / 2, B_Y + 64, "UART 9600  /  BLE 广播", {"font-size": "9", "fill": "#666"})

    # 网关 ←→ BLE（BLE 直连，曲线避开）
    line_arrow(svg, G_X + 20, G_Y + G_H, B_X + 20, B_Y,
               C_ORANGE, 1.5, None, "BLE 直连", -8)

    # ====== 测试笔记本（右下） ======
    T_X, T_Y, T_W, T_H = 400, 340, 170, 76
    rect(svg, T_X, T_Y, T_W, T_H, rx=8, fill="#F0F0F0", stroke=C_GRAY, sw=1.5)
    add_text(svg, T_X + T_W / 2, T_Y + 22, "Windows 11 笔记本", {"font-size": "11", "fill": C_GRAY, "font-weight": "bold"})
    add_text(svg, T_X + T_W / 2, T_Y + 42, "测试上位机", {"font-size": "10", "fill": "#333"})
    add_text(svg, T_X + T_W / 2, T_Y + 64, "bench /  pytest  /  采集脚本", {"font-size": "9", "fill": "#666"})

    # 路由器 ←→ 笔记本（虚线）
    line_arrow(svg, R_X + R_W / 2, R_Y + R_H, T_X + T_W / 2, T_Y,
               C_GRAY, 1.5, "4,3", "以太网 / Wi-Fi", 12)

    # ====== 局域范围虚线框 ======
    LAN_X, LAN_Y, LAN_W, LAN_H = 22, 36, 576, 394
    svg.append(el("rect", x=str(LAN_X), y=str(LAN_Y), width=str(LAN_W),
                  height=str(LAN_H), rx="14", fill="none", stroke=C_BLUE,
                  **{"stroke-width": "1.8"}, **{"stroke-dasharray": "6,3"}))
    add_text(svg, LAN_X + LAN_W - 60, LAN_Y + 14, "家庭局域网",
             {"font-size": "10", "fill": C_BLUE, "font-weight": "bold"})

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
    s = build_topology()
    save(s, base + r"\图5-1_测试环境网络拓扑图.svg")
    print("saved: 图5-1_测试环境网络拓扑图.svg")


if __name__ == "__main__":
    main()
