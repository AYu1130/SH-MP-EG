"""
技术路线图 SVG 生成脚本
适合 A4 论文页面插入，文字大小为小四（12pt ≈ 16px）
可在 Visio 中打开编辑
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def _sub(tag: str, **attrs) -> ET.Element:
    el = ET.Element(tag)
    for k, v in attrs.items():
        el.set(k, str(v))
    return el


def _svg(w: int = 680, h: int = 1020) -> ET.Element:
    return ET.Element("svg", {
        "xmlns": "http://www.w3.org/2000/svg",
        "width": str(w), "height": str(h),
        "viewBox": f"0 0 {w} {h}",
        "font-family": "宋体, SimSun, serif",
    })


FONT12 = {"font-size": "12", "fill": "#333333"}
FONT13 = {"font-size": "13", "fill": "#222222", "font-weight": "bold"}
FONT11 = {"font-size": "11", "fill": "#555555"}
FONT10 = {"font-size": "10", "fill": "#666666"}
FONT14 = {"font-size": "14", "fill": "#1a1a1a", "font-weight": "bold"}

# 配色
C_STAGE = "#2B579A"      # 阶段主色 深蓝
C_STAGE_BG = "#E8EEF7"   # 阶段浅底
C_OUTPUT_BG = "#F5F5F5"  # 产出框底
C_OUTPUT_STROKE = "#999999"
C_ARROW = "#2B579A"
C_ARROW_LIGHT = "#8BAAC4"
C_TITLE = "#1a1a1a"


def add_text(parent, x, y, text, attrs=None):
    """在指定位置添加文字，x 为水平中心点。"""
    a = dict(FONT12)
    if attrs:
        a.update(attrs)
    e = _sub("text", **{k: v for k, v in a.items() if k != "text-anchor"})
    e.set("x", str(x))
    e.set("y", str(y))
    e.set("text-anchor", a.get("text-anchor", "middle"))
    e.text = text
    parent.append(e)


def add_rect(parent, x, y, w, h, rx=6, fill="#fff", stroke="#ccc", sw=1.2):
    parent.append(_sub("rect", x=x, y=y, width=w, height=h,
                        rx=str(rx), ry=str(rx),
                        fill=fill, stroke=stroke, **{"stroke-width": str(sw)}))


def add_line(parent, x1, y1, x2, y2, stroke=C_ARROW, sw=1.5, dash=None):
    attrs = {"x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2),
             "stroke": stroke, **{"stroke-width": str(sw)}}
    if dash:
        attrs["stroke-dasharray"] = dash
    parent.append(_sub("line", **attrs))


def add_arrow_down(parent, x, y1, y2):
    """垂直向下的箭头（含三角箭头）。"""
    add_line(parent, x, y1, x, y2 - 8)
    pts = f"{x-5},{y2-8} {x+5},{y2-8} {x},{y2}"
    parent.append(_sub("polygon", points=pts, fill=C_ARROW))


def add_arrow_right(parent, x1, y, x2):
    add_line(parent, x1, y, x2 - 8, y, stroke=C_ARROW_LIGHT, sw=1.2, dash="4,3")
    pts = f"{x2-8},{y-4} {x2-8},{y+4} {x2},{y}"
    parent.append(_sub("polygon", points=pts, fill=C_ARROW_LIGHT))


def build() -> ET.Element:
    svg = _svg(680, 1020)

    # 背景
    svg.append(_sub("rect", x="0", y="0", width="680", height="1020",
                    fill="#FFFFFF", stroke="none"))

    # ============================================================
    # 标题
    # ============================================================
    add_text(svg, 340, 38, "技术路线图", FONT14)

    # 中央竖线
    cx = 340  # 阶段框水平中心
    sx = 150  # 阶段框左边界
    sw_ = 380  # 阶段框宽

    # ============================================================
    # 六个阶段
    # ============================================================
    stages = [
        {
            "label": "第一阶段：文献调研与需求分析",
            "items": [
                "梳理国内外多协议网关与边缘计算研究成果",
                "识别协议异构、云端依赖、时延偏高等痛点",
                "明确网关功能边界与性能设计指标",
            ],
            "output": "文献综述报告\n需求规格文档",
            "y": 72,
        },
        {
            "label": "第二阶段：总体方案设计",
            "items": [
                '设计\u201c感知层-边缘层-网络层-应用层\u201d四层架构',
                "确定统一JSON数据模型与MQTT主题规范",
                "定义模块接口与数据流路径",
            ],
            "output": "系统架构图\n模块接口定义",
            "y": 212,
        },
        {
            "label": "第三阶段：硬件选型与平台搭建",
            "items": [
                "树莓派4B（2GB）作为网关核心主控",
                "ESP32-S3 + SHT30/BH1750 作为 Wi-Fi 终端",
                "STM32F103 + HM-10 作为 BLE 终端",
            ],
            "output": "硬件平台搭建\n运行环境配置",
            "y": 352,
        },
        {
            "label": "第四阶段：软件模块开发与单元测试",
            "items": [
                "协议适配器：Wi-Fi(HTTP/TCP)+BLE(Bleak)双模接收",
                "数据转换器：异构数据→统一JSON Schema校验",
                "消息路由：paho-mqtt发布订阅 + SQLite离线缓存",
                "联动引擎：Node-RED流程编排 + Flask Web管理台",
            ],
            "output": "协议适配器\n消息路由器\n联动规则引擎",
            "y": 492,
        },
        {
            "label": "第五阶段：系统集成与测试验证",
            "items": [
                "功能测试：7项用例覆盖设备接入至断网自治全流程",
                "性能测试：端到端时延、跨节点联动、并发与丢包率",
                "稳定性测试：168h长时运行 + 多断网时长恢复",
            ],
            "output": "功能测试报告\n性能测试报告\n稳定性测试报告",
            "y": 652,
        },
        {
            "label": "第六阶段：结果分析与总结展望",
            "items": [
                "设计指标达标分析：五项指标全部达标且优于阈值",
                "与商业网关方案的定性对比分析",
                "总结方法优势与不足，提出后续改进方向",
            ],
            "output": "论文撰写\n答辩准备",
            "y": 812,
        },
    ]

    H_STAGE = 112   # 每阶段高度
    OUT_X = 545     # 产出框 x
    OUT_W = 120     # 产出框宽

    for s in stages:
        y0 = s["y"]
        x0 = sx

        # 阶段主框
        add_rect(svg, x0, y0, sw_, H_STAGE, rx=8,
                 fill=C_STAGE_BG, stroke=C_STAGE, sw=1.5)

        # 左侧阶段标签竖条
        svg.append(_sub("rect", x=str(x0), y=str(y0),
                        width="42", height=str(H_STAGE),
                        rx="8", ry="8", fill=C_STAGE))
        # 覆盖右下圆角使其变直角
        svg.append(_sub("rect", x=str(x0 + 34), y=str(y0 + H_STAGE - 8),
                        width="8", height="8", fill=C_STAGE))
        # 覆盖右上圆角
        svg.append(_sub("rect", x=str(x0 + 34), y=str(y0),
                        width="8", height="8", fill=C_STAGE))

        # 阶段编号
        num = stages.index(s) + 1
        add_text(svg, x0 + 21, y0 + 58, f"0{num}",
                 {"font-size": "20", "fill": "#FFFFFF", "font-weight": "bold",
                  "text-anchor": "middle"})

        # 阶段标题
        add_text(svg, x0 + 50 + (sw_ - 50) / 2, y0 + 22, s["label"],
                 {"font-size": "13", "fill": "#222222", "font-weight": "bold",
                  "text-anchor": "middle"})

        # 阶段内容项
        item_y = y0 + 42
        for item in s["items"]:
            # 圆点
            svg.append(_sub("circle", cx=str(x0 + 52), cy=str(item_y + 3),
                            r="2.5", fill=C_STAGE))
            add_text(svg, x0 + 60, item_y + 7, item,
                     {"font-size": "11", "fill": "#444444",
                      "text-anchor": "start"})
            item_y += 18

        # 产出框
        out_h = 40
        out_y = y0 + (H_STAGE - out_h) / 2
        add_rect(svg, OUT_X, out_y, OUT_W, out_h, rx=5,
                 fill=C_OUTPUT_BG, stroke=C_OUTPUT_STROKE, sw=1)

        # 产出文字居中
        lines = s["output"].split("\n")
        lh = 13 if len(lines) <= 2 else 11
        start = out_y + out_h / 2 - (len(lines) - 1) * lh / 2
        for i, line in enumerate(lines):
            add_text(svg, OUT_X + OUT_W / 2, start + i * lh + 5, line,
                     {"font-size": "10", "fill": "#555555",
                      "text-anchor": "middle"})

        # 阶段框到产出框的虚线
        add_arrow_right(svg, x0 + sw_, y0 + H_STAGE / 2, OUT_X)

    # ============================================================
    # 阶段间向下箭头（从上一阶段底部到下一阶段顶部）
    # ============================================================
    for i in range(len(stages) - 1):
        y_from = stages[i]["y"] + H_STAGE
        y_to = stages[i + 1]["y"]
        add_arrow_down(svg, cx, y_from + 6, y_to - 6)

    # ============================================================
    # 底部总结
    # ============================================================
    add_text(svg, 340, 968,
             "六阶段前后衔接、逐层递进，构成从理论分析到工程验证的完整研究闭环",
             {"font-size": "12", "fill": C_STAGE, "font-weight": "bold",
              "text-anchor": "middle"})

    return svg


def main():
    svg = build()

    # 缩进美化输出
    ET.indent(svg, space="  ", level=0)

    out_path = (
        r"e:\100_study\120_Project\CapstoneProject"
        r"\SmartHome_MultiProtocol_EdgeIntelligent_Gateway"
        r"\SH-MP-EG\docs\output\01_当前工作区"
        r"\图_技术路线图.svg"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(ET.tostring(svg, encoding="unicode"))
    print(f"SVG saved: {out_path}")


if __name__ == "__main__":
    main()
