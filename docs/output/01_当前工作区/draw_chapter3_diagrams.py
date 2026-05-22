"""
生成第3章两幅图：
  图3-1 系统整体分层架构图
  图3-2 系统数据流架构图

A4 论文大小，文字小四，Visio 可编辑。
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

# ============================================================
# 工具
# ============================================================
def el(tag: str, **attrs) -> ET.Element:
    e = ET.Element(tag)
    for k, v in attrs.items():
        e.set(k, str(v))
    return e


def add_text(parent, x, y, text, attrs=None):
    a = {"font-size": "12", "fill": "#333", "text-anchor": "middle",
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


def arrow_down(parent, x, y1, y2, color="#2B579A", sw=1.5):
    parent.append(el("line", x1=str(x), y1=str(y1), x2=str(x), y2=str(y2 - 7),
                     stroke=color, **{"stroke-width": str(sw)}))
    parent.append(el("polygon",
                     points=f"{x-5},{y2-8} {x+5},{y2-8} {x},{y2}",
                     fill=color))


def arrow_right(parent, x1, y, x2, color="#8BAAC4", sw=1.2, dash="4,3"):
    parent.append(el("line", x1=str(x1), y1=str(y), x2=str(x2 - 7), y2=str(y),
                     stroke=color, **{"stroke-width": str(sw)},
                     **{"stroke-dasharray": dash}))
    parent.append(el("polygon",
                     points=f"{x2-8},{y-4} {x2-8},{y+4} {x2},{y}",
                     fill=color))


C1 = "#2B579A"   # 深蓝主题
C2 = "#D6E4F0"   # 浅蓝底
C3 = "#555555"   #灰文字
C4 = "#E8EEF7"   # 更浅蓝

# ============================================================
# 图 3-1  系统整体分层架构图
# ============================================================
def build_layer_arch() -> ET.Element:
    W, H = 640, 700
    svg = el("svg", xmlns="http://www.w3.org/2000/svg",
             width=str(W), height=str(H), viewBox=f"0 0 {W} {H}")

    # 背景
    svg.append(el("rect", x="0", y="0", width=str(W), height=str(H),
                  fill="#FFFFFF"))

    # 标题
    add_text(svg, W // 2, 32, "图3-1  系统整体分层架构图",
             {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"})

    # ---------- 四层主体 ----------
    layers = [
        {"name": "应用与联动管理层", "y": 60, "blocks": [
            {"text": "Web管理后台\n(Flask + MQTT/WS)", "x": 80},
            {"text": "Node-RED\n联动规则引擎", "x": 270},
            {"text": "云端桥接\n(可选)", "x": 460},
        ]},
        {"name": "消息路由与处理层", "y": 210, "blocks": [
            {"text": "EMQX\n消息代理", "x": 120, "w": 140},
            {"text": "MQTT 适配器\n主题路由 / QoS", "x": 310, "w": 140},
            {"text": "SQLite\n离线缓存", "x": 500, "w": 100},
        ]},
        {"name": "协议适配层", "y": 360, "blocks": [
            {"text": "Wi-Fi 适配器\nTCP/HTTP解析", "x": 80, "w": 130},
            {"text": "BLE 适配器\nBleak GATT", "x": 230, "w": 130},
            {"text": "协议转换器\nJSON映射/标准化", "x": 380, "w": 140},
        ]},
        {"name": "设备接入层", "y": 510, "blocks": [
            {"text": "ESP32-S3\nWi-Fi 终端", "x": 70, "w": 180},
            {"text": "STM32+HM-10\nBLE 终端", "x": 310, "w": 180},
            {"text": "扩展接口\n(Zigbee/Thread)", "x": 530, "w": 90},
        ]},
    ]

    LAYER_H = 136

    for i, layer in enumerate(layers):
        ly = layer["y"]
        # 层底色框
        svg.append(el("rect", x="40", y=str(ly), width="560", height=str(LAYER_H),
                      rx="8", ry="8", fill="#F2F6FA", stroke="#CCD9E8", **{"stroke-width": "1"}))

        # 左侧层名标签
        lw = 18
        svg.append(el("rect", x="42", y=str(ly + 2), width=str(lw),
                      height=str(LAYER_H - 4), rx="6", fill=C1))
        # 竖排文字
        label_chars = list(layer["name"])
        for ci, ch in enumerate(label_chars):
            add_text(svg, 51, ly + 22 + ci * 16, ch,
                     {"font-size": "12", "fill": "#FFFFFF", "font-weight": "bold"})

        # 层内模块
        for blk in layer["blocks"]:
            bw = blk.get("w", 150)
            bh = 72
            bx = blk["x"]
            by = ly + 34
            rect(svg, bx, by, bw, bh, rx=6, fill="#FFFFFF",
                 stroke=C1, sw=1.2)
            lines = blk["text"].split("\n")
            start = by + bh / 2 - (len(lines) - 1) * 9
            for li, line in enumerate(lines):
                add_text(svg, bx + bw / 2, start + li * 18 + 4, line,
                         {"font-size": "11", "fill": "#333", "font-weight": "bold"
                          if li == 0 else "normal"})

        # 层间下箭头（最后一层不加）
        if i < len(layers) - 1:
            arrow_down(svg, W // 2, ly + LAYER_H, layers[i + 1]["y"])

    # ========== 底部：图例 ==========
    legend_y = 660
    add_text(svg, W // 2, legend_y, "数据流向：下层采集 → 上层处理  /  上层指令 → 下层执行",
             {"font-size": "11", "fill": C3})

    return svg


# ============================================================
# 图 3-2  系统数据流架构图
# ============================================================
def build_dataflow() -> ET.Element:
    W, H = 700, 560
    svg = el("svg", xmlns="http://www.w3.org/2000/svg",
             width=str(W), height=str(H), viewBox=f"0 0 {W} {H}")
    svg.append(el("rect", x="0", y="0", width=str(W), height=str(H),
                  fill="#FFFFFF"))

    add_text(svg, W // 2, 30, "图3-2  系统数据流架构图",
             {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"})

    # ========== 上行区域（上半） ==========
    # 左侧：终端
    add_text(svg, 75, 72, "Wi-Fi 终端",
             {"font-size": "11", "fill": C1, "font-weight": "bold"})
    rect(svg, 15, 82, 120, 48, rx=6, fill=C2, stroke=C1, sw=1.2)
    add_text(svg, 75, 100, "ESP32-S3", {"font-size": "11", "fill": "#333", "font-weight": "bold"})
    add_text(svg, 75, 118, "SHT30 / BH1750", {"font-size": "10", "fill": "#666"})

    add_text(svg, 75, 168, "BLE 终端",
             {"font-size": "11", "fill": C1, "font-weight": "bold"})
    rect(svg, 15, 178, 120, 48, rx=6, fill=C2, stroke=C1, sw=1.2)
    add_text(svg, 75, 196, "STM32 + HM-10", {"font-size": "11", "fill": "#333", "font-weight": "bold"})
    add_text(svg, 75, 214, "BLE 广播 / GATT", {"font-size": "10", "fill": "#666"})

    # 左侧到网关的箭头（上行）
    arrow_right(svg, 135, 106, 190, C1, 1.5, None)
    arrow_right(svg, 135, 202, 190, C1, 1.5, None)

    # 网关核心大框
    rect(svg, 195, 62, 300, 340, rx=10, fill="#F7F9FC", stroke=C1, sw=2)
    add_text(svg, 345, 82, "多协议边缘智能网关",
             {"font-size": "12", "fill": C1, "font-weight": "bold"})

    # 网关内部模块
    def gw_block(x, y, w, h, lines, color_stroke="#7FA3C7", color_fill="#EAF0F7"):
        rect(svg, x, y, w, h, rx=5, fill=color_fill, stroke=color_stroke, sw=1)
        start = y + h / 2 - (len(lines) - 1) * 8
        for li, line in enumerate(lines):
            add_text(svg, x + w / 2, start + li * 16 + 4, line,
                     {"font-size": "10", "fill": "#333",
                      "font-weight": "bold" if li == 0 else "normal"})

    gw_block(213, 100, 130, 40, ["Wi-Fi 适配器", "TCP/HTTP 解析"])
    gw_block(355, 100, 130, 40, ["BLE 适配器", "Bleak 扫描/连接"])

    # 网关内部箭头
    arrow_down(svg, 278, 136, 155, "#7FA3C7")
    arrow_down(svg, 420, 136, 155, "#7FA3C7")

    gw_block(213, 158, 264, 34, ["协议转换器  ─  JSON映射 / 单位标准化"])

    arrow_down(svg, 345, 190, 210, "#7FA3C7")

    gw_block(255, 213, 180, 70, [
        "EMQX 消息代理",
        "主题路由 / QoS1",
        "发布/订阅分发",
    ], "#5A8BB5", "#DCE8F2")

    # 网关内部 → WebSocket / Node-RED
    arrow_right(svg, 435, 235, 495, "#7FA3C7", 1.2, "4,3")
    arrow_right(svg, 435, 258, 495, "#7FA3C7", 1.2, "4,3")

    # 右侧：Node-RED
    rect(svg, 520, 155, 155, 58, rx=6, fill=C2, stroke=C1, sw=1.2)
    add_text(svg, 597, 177, "Node-RED", {"font-size": "12", "fill": "#333", "font-weight": "bold"})
    add_text(svg, 597, 196, "联动规则引擎", {"font-size": "10", "fill": "#555"})
    add_text(svg, 597, 210, "跨协议自动化编排", {"font-size": "9", "fill": "#888"})

    # 右侧：Web 管理台
    rect(svg, 520, 232, 155, 50, rx=6, fill=C2, stroke=C1, sw=1.2)
    add_text(svg, 597, 252, "Web 管理后台", {"font-size": "12", "fill": "#333", "font-weight": "bold"})
    add_text(svg, 597, 270, "Flask + MQTT/WS", {"font-size": "10", "fill": "#555"})

    # SQLite 缓存
    gw_block(213, 298, 80, 46, [
        "SQLite",
        "离线缓存",
        "状态存储",
    ], "#888888", "#F0F0F0")

    # EMQX → SQLite 虚线
    svg.append(el("line", x1="278", y1="280", x2="278", y2="293",
                  stroke="#888888", **{"stroke-width": "1"}, **{"stroke-dasharray": "3,3"}))
    svg.append(el("polygon", points="273,292 283,292 278,300", fill="#888888"))

    # ---------- 上行标注 ----------
    add_text(svg, 530, 102, "上行数据流",
             {"font-size": "10", "fill": C1, "font-weight": "bold", "text-anchor": "start"})

    # ========== 下行标注 ==========
    add_text(svg, 530, 330, "下行控制流",
             {"font-size": "10", "fill": "#C44", "font-weight": "bold", "text-anchor": "start"})

    # Node-RED → EMQX（下行）
    arrow_right(svg, 495, 192, 435, "#C44", 1.2, "4,3")
    # Web → EMQX
    arrow_right(svg, 495, 257, 435, "#C44", 1.2, "4,3")

    # 网关内 EMQX → 适配器（下行）
    arrow_down(svg, 278, 280, 260, "#C44", 1.2)
    arrow_down(svg, 420, 280, 260, "#C44", 1.2)

    # 网关 → 终端（下行）
    arrow_right(svg, 188, 120, 135, "#C44", 1, "4,3")
    arrow_right(svg, 188, 202, 135, "#C44", 1, "4,3")

    # ========== 底部：图例 ==========
    legend_y = 440
    # 上行图例
    svg.append(el("line", x1="60", y1=str(legend_y), x2="110", y2=str(legend_y),
                  stroke=C1, **{"stroke-width": "2"}))
    svg.append(el("polygon", points=f"110,{legend_y - 4} 110,{legend_y + 4} 120,{legend_y}",
                  fill=C1))
    add_text(svg, 160, legend_y + 5, "上行数据流（传感器 → 网关 → 上层）",
             {"font-size": "10", "fill": "#555", "font-weight": "bold", "text-anchor": "start"})

    # 下行图例
    ly2 = legend_y + 22
    svg.append(el("line", x1="60", y1=str(ly2), x2="110", y2=str(ly2),
                  stroke="#C44", **{"stroke-width": "2"}))
    svg.append(el("polygon", points=f"110,{ly2 - 4} 110,{ly2 + 4} 120,{ly2}",
                  fill="#C44"))
    add_text(svg, 160, ly2 + 5, "下行控制流（用户/规则 → 网关 → 终端）",
             {"font-size": "10", "fill": "#555", "font-weight": "bold", "text-anchor": "start"})

    # 局域网标识
    add_text(svg, 345, 490, "全链路在家庭局域网内闭环，断网不影响上行采集与下行控制",
             {"font-size": "11", "fill": C1, "font-weight": "bold"})

    return svg


# ============================================================
def save(svg: ET.Element, path: str):
    ET.indent(svg, space="  ", level=0)
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(ET.tostring(svg, encoding="unicode"))


def main():
    base = (
        r"e:\100_study\120_Project\CapstoneProject"
        r"\SmartHome_MultiProtocol_EdgeIntelligent_Gateway"
        r"\SH-MP-EG\docs\output\01_当前工作区"
    )
    s1 = build_layer_arch()
    save(s1, base + r"\图3-1_系统整体分层架构图.svg")
    print("saved: 图3-1_系统整体分层架构图.svg")

    s2 = build_dataflow()
    save(s2, base + r"\图3-2_系统数据流架构图.svg")
    print("saved: 图3-2_系统数据流架构图.svg")


if __name__ == "__main__":
    main()
