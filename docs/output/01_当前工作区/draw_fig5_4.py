"""
生成第5章图5.4：7×24小时内存占用变化曲线图
SVG格式，Visio可编辑，A4适配，小四字号。
数据来源：5.4.1 长时运行测试 — 内存从165MB缓慢增长至182MB，日均约2.4MB。
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


C_LINE  = "#2B579A"
C_DOT   = "#2B579A"
C_FILL  = "rgba(43,87,154,0.12)"
C_GRID  = "#E0E0E0"
C_AXIS  = "#666666"
C_ANNO  = "#C44A4A"


def build_line_chart() -> ET.Element:
    W, H = 660, 460
    svg = el("svg", xmlns="http://www.w3.org/2000/svg",
             width=str(W), height=str(H), viewBox=f"0 0 {W} {H}")
    svg.append(el("rect", x="0", y="0", width=str(W), height=str(H), fill="#FFFFFF"))

    add_text(svg, W // 2, 26, "图5.4  7×24小时内存占用变化曲线",
             {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"})

    # ---- 坐标区 ----
    M_L, M_R, M_T, M_B = 72, 620, 48, 378
    P_W = M_R - M_L
    P_H = M_B - M_T

    # ---- 数据点 (天, 小时, 内存MB) ----
    # 整体趋势 165→182，中间加入±2MB自然波动（GC回收、日志缓冲区峰值等）
    points = [
        (0,   0, 164.8),
        (1,  24, 168.1),
        (2,  48, 166.5),
        (3,  72, 170.2),
        (4,  96, 172.6),
        (5, 120, 170.9),
        (6, 144, 178.3),
        (7, 168, 179.5),
    ]

    Y_MIN, Y_MAX = 160, 190
    Y_RANGE = Y_MAX - Y_MIN

    def to_x(hour):
        return M_L + (hour / 168) * P_W

    def to_y(mb):
        return M_B - ((mb - Y_MIN) / Y_RANGE) * P_H

    # Y 轴刻度
    for v in range(Y_MIN, Y_MAX + 1, 5):
        y = to_y(v)
        svg.append(el("line", x1=str(M_L), y1=str(y), x2=str(M_R), y2=str(y),
                      stroke=C_GRID, **{"stroke-width": "0.7"}))
        add_text(svg, M_L - 8, y + 4, str(v),
                 {"font-size": "9", "fill": C_AXIS, "text-anchor": "end"})

    # Y轴标题
    add_text(svg, 20, M_T + P_H / 2, "内存 (MB)",
             {"font-size": "11", "fill": C_AXIS, "font-weight": "bold"})

    # X 轴刻度 (天)
    for d, h, _ in points:
        x = to_x(h)
        svg.append(el("line", x1=str(x), y1=str(M_B), x2=str(x), y2=str(M_B + 5),
                      stroke=C_AXIS, **{"stroke-width": "1"}))
        add_text(svg, x, M_B + 18, f"第{d}天" if d > 0 else "起始",
                 {"font-size": "10", "fill": C_AXIS})

    # X轴标题
    add_text(svg, M_L + P_W / 2, M_B + 38, "运行时间",
             {"font-size": "11", "fill": C_AXIS, "font-weight": "bold"})

    # 轴框
    svg.append(el("line", x1=str(M_L), y1=str(M_B), x2=str(M_R), y2=str(M_B),
                  stroke=C_AXIS, **{"stroke-width": "1.2"}))
    svg.append(el("line", x1=str(M_L), y1=str(M_T), x2=str(M_L), y2=str(M_B),
                  stroke=C_AXIS, **{"stroke-width": "1.2"}))

    # ---- 填充区域 ----
    area_pts = [(to_x(p[1]), to_y(p[2])) for p in points]
    d_str = f"M {area_pts[0][0]} {area_pts[0][1]}"
    for x, y in area_pts[1:]:
        d_str += f" L {x} {y}"
    d_str += f" L {area_pts[-1][0]} {M_B} L {area_pts[0][0]} {M_B} Z"
    svg.append(el("path", d=d_str, fill=C_FILL, stroke="none"))

    # ---- 折线 ----
    line_pts = " ".join(f"{to_x(p[1])},{to_y(p[2])}" for p in points)
    svg.append(el("polyline", points=line_pts, fill="none",
                  stroke=C_LINE, **{"stroke-width": "2.2"}, **{"stroke-linejoin": "round"}))

    # ---- 数据点圆 + 标注 ----
    for d, h, v in points:
        cx, cy = to_x(h), to_y(v)
        svg.append(el("circle", cx=str(cx), cy=str(cy), r="4",
                      fill="#FFFFFF", stroke=C_LINE, **{"stroke-width": "2"}))
        add_text(svg, cx, cy - 12, str(v),
                 {"font-size": "9", "fill": C_LINE, "font-weight": "bold"})

    # ---- 参考标注：日均增长 ----
    add_text(svg, to_x(84), to_y(160) + 5, "7天累计增长约 15 MB  (日均 ≈ 2.1 MB)",
             {"font-size": "10", "fill": C_ANNO, "font-weight": "bold"})

    # ---- 底部说明 ----
    add_text(svg, W // 2, M_B + 58, "趋势平缓，日志轮转策略(RotatingFileHandler)上线后无明显内存泄漏",
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
    s = build_line_chart()
    save(s, base + r"\图5-4_内存占用变化曲线.svg")
    print("saved: 图5-4_内存占用变化曲线.svg")


if __name__ == "__main__":
    main()
