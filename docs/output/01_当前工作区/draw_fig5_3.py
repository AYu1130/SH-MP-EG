"""
生成第5章图5-3：不同场景传输时延对比柱状图
SVG格式，Visio可编辑，A4适配，小四字号。
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
    e = el("text", x=str(x), y=str(y),
           **{k: str(v) for k, v in a.items() if k not in ("text-anchor",)})
    e.set("text-anchor", a.get("text-anchor", "middle"))
    e.text = text
    parent.append(e)


def rect(parent, x, y, w, h, fill, rx=0):
    parent.append(el("rect", x=str(x), y=str(y), width=str(w), height=str(h),
                     fill=fill, rx=str(rx), ry=str(rx)))


# ============================================================
# 配色 (学术风格，色盲友好)
# ============================================================
C_MIN  = "#6BAED6"   # 浅蓝
C_AVG  = "#2B579A"   # 深蓝
C_P95  = "#E68A2E"   # 橙色
C_MAX  = "#C44A4A"   # 红色
C_TOTAL = "#4A8B5A"   # 绿色(联动总时延)
C_GRID = "#DDDDDD"
C_AXIS = "#666666"


def build_bar_chart() -> ET.Element:
    W, H = 660, 500
    svg = el("svg", xmlns="http://www.w3.org/2000/svg",
             width=str(W), height=str(H), viewBox=f"0 0 {W} {H}")
    svg.append(el("rect", x="0", y="0", width=str(W), height=str(H), fill="#FFFFFF"))

    # 标题
    add_text(svg, W // 2, 28, "图5-3  不同场景传输时延对比",
             {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"})

    # 坐标区
    M_L, M_R, M_T, M_B = 80, 620, 48, 400
    P_W = M_R - M_L  # 绘图区宽
    P_H = M_B - M_T  # 绘图区高

    # Y轴刻度 (0 ~ 200 ms)
    Y_MAX = 200
    y_ticks = [0, 40, 80, 120, 160, 200]
    for v in y_ticks:
        y = M_B - (v / Y_MAX) * P_H
        svg.append(el("line", x1=str(M_L), y1=str(y), x2=str(M_R), y2=str(y),
                      stroke=C_GRID, **{"stroke-width": "0.8"}))
        add_text(svg, M_L - 10, y + 4, str(v),
                 {"font-size": "10", "fill": C_AXIS, "text-anchor": "end"})

    # Y轴标题
    add_text(svg, 24, M_T + P_H / 2, "时延 (ms)",
             {"font-size": "11", "fill": C_AXIS, "font-weight": "bold"})

    # 轴框
    svg.append(el("line", x1=str(M_L), y1=str(M_B), x2=str(M_R), y2=str(M_B),
                  stroke=C_AXIS, **{"stroke-width": "1.2"}))
    svg.append(el("line", x1=str(M_L), y1=str(M_T), x2=str(M_L), y2=str(M_B),
                  stroke=C_AXIS, **{"stroke-width": "1.2"}))

    # ========== 数据 ==========
    scenarios = [
        {
            "label": "Wi-Fi 端到端",
            "bars": [
                ("最小值", 18,  C_MIN),
                ("平均值", 43.5, C_AVG),
                ("P95",   68.7, C_P95),
                ("最大值", 102,  C_MAX),
            ]
        },
        {
            "label": "BLE 端到端",
            "bars": [
                ("最小值", 41,   C_MIN),
                ("平均值", 76.8, C_AVG),
                ("P95",   128.3, C_P95),
                ("最大值", 178,  C_MAX),
            ]
        },
        {
            "label": "跨节点联动",
            "bars": [
                ("总时延", 134.5, C_TOTAL),
            ]
        },
    ]

    N = len(scenarios)
    GROUP_W = P_W / N
    BAR_GAP_RATIO = 0.32  # 组间距占组宽的比例

    for gi, sc in enumerate(scenarios):
        cx = M_L + GROUP_W * (gi + 0.5)  # 组中心 X
        bars = sc["bars"]
        K = len(bars)
        bar_w = GROUP_W * (1 - BAR_GAP_RATIO) / K
        gap_w = GROUP_W * BAR_GAP_RATIO / (K + 1)

        for bi, (bname, bval, bcolor) in enumerate(bars):
            bar_h = (bval / Y_MAX) * P_H
            bar_x = cx - (K * bar_w + (K - 1) * gap_w) / 2 + bi * (bar_w + gap_w)
            bar_y = M_B - bar_h

            rect(svg, bar_x, bar_y, bar_w, bar_h, bcolor, rx=2)

            # 柱顶数值标注
            add_text(svg, bar_x + bar_w / 2, bar_y - 6, str(bval),
                     {"font-size": "9", "fill": bcolor, "font-weight": "bold"})

        # X轴类别标签
        add_text(svg, cx, M_B + 20, sc["label"],
                 {"font-size": "11", "fill": "#333", "font-weight": "bold"})

    # ========== 图例 ==========
    legend_items = [
        ("最小值", C_MIN), ("平均值", C_AVG), ("P95", C_P95),
        ("最大值", C_MAX), ("总时延", C_TOTAL),
    ]
    lx = M_L + 20
    ly = M_B + 52
    for i, (lbl, lc) in enumerate(legend_items):
        ix = lx + i * 106
        rect(svg, ix, ly, 16, 12, lc, rx=2)
        add_text(svg, ix + 22, ly + 10, lbl,
                 {"font-size": "10", "fill": "#333", "text-anchor": "start"})

    # 底部统计口径
    add_text(svg, W // 2, ly + 32, "Wi-Fi/BLE 各200样本；跨节点联动50次测试",
             {"font-size": "9", "fill": C_AXIS})

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
    s = build_bar_chart()
    save(s, base + r"\图5-3_传输时延对比柱状图.svg")
    print("saved: 图5-3_传输时延对比柱状图.svg")


if __name__ == "__main__":
    main()
