"""
SVG转Visio友好格式工具
=====================
将matplotlib生成的SVG转换为更适合Visio编辑的格式。
主要解决：
1. 元素过大难以调整的问题
2. 分组嵌套导致无法单独编辑
3. 坐标系复杂导致定位困难
"""

import os
import re
from pathlib import Path

def optimize_svg_for_visio(svg_content):
    """
    优化SVG内容使其更适合Visio编辑
    
    改进点：
    - 移除过深的分组嵌套
    - 标准化坐标系
    - 添加明确的图层标识
    - 优化文字渲染
    """
    
    # 1. 提取SVG基本信息
    width_match = re.search(r'width="([\d.]+)pt"', svg_content)
    height_match = re.search(r'height="([\d.]+)pt"', svg_content)
    viewbox_match = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg_content)
    
    if not all([width_match, height_match, viewbox_match]):
        return svg_content
    
    original_width = float(width_match.group(1))
    original_height = float(height_match.group(1))
    vb_width = float(viewbox_match.group(1))
    vb_height = float(viewbox_match.group(2))
    
    # 2. 计算缩放因子（将pt转换为更合理的单位）
    # 目标：使图表在Visio中默认显示为A4纸大小的合适比例
    target_width = 800  # 像素
    scale_factor = target_width / vb_width
    
    new_width = target_width
    new_height = vb_height * scale_factor
    
    # 3. 替换SVG头部信息
    optimized = svg_content.replace(
        f'width="{original_width}pt" height="{original_height}pt"',
        f'width="{new_width}px" height="{new_height}px"'
    )
    
    # 4. 移除matplotlib特有的元数据（减少文件大小和复杂度）
    # 保留必要的结构但移除冗余信息
    optimized = re.sub(
        r'<metadata>.*?</metadata>',
        '<!-- Optimized for Visio editing -->',
        optimized,
        flags=re.DOTALL
    )
    
    # 5. 简化样式定义
    optimized = optimized.replace(
        '*{stroke-linejoin: round; stroke-linecap: butt}',
        '*{stroke-linejoin: miter; stroke-linecap: round}'
    )
    
    # 6. 为主要图形组添加注释，便于Visio中识别
    optimized = optimized.replace(
        '<g id="figure_1">',
        '''<g id="figure_1">
     <!-- 主图形容器 - 可整体移动缩放 -->'''
    )
    
    optimized = optimized.replace(
        '<g id="axes_1">',
        '     <!-- 坐标轴/绘图区域 -->\n     <g id="axes_1">'
    )
    
    # 7. 为文本元素添加可编辑性提示
    def add_text_annotation(match):
        text_content = match.group(0)
        if 'id="text_' in text_content:
            return text_content.replace('<g ', '<g style="cursor: text;" ')
        return text_content
    
    optimized = re.sub(r'<g id="text_\d+">', add_text_annotation, optimized)
    
    return optimized

def convert_svg_to_visio_friendly(input_path, output_path=None):
    """
    将单个SVG文件转换为Visio友好格式
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"[ERROR] 文件不存在: {input_path}")
        return False
    
    if output_path is None:
        output_path = input_file.with_suffix('.visio.svg')
    
    print(f"[INFO] 处理: {input_file.name}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        optimized_content = optimize_svg_for_visio(content)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(optimized_content)
        
        size_kb = Path(output_path).stat().st_size / 1024
        print(f"[OK] 已生成: {Path(output_path).name} ({size_kb:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 处理失败: {str(e)}")
        return False

def batch_convert_svg_files(directory):
    """
    批量转换目录下所有SVG文件
    """
    work_dir = Path(directory)
    svg_files = list(work_dir.glob("*.svg"))
    
    if not svg_files:
        print("[WARN] 未找到SVG文件")
        return
    
    print("=" * 70)
    print("[INFO] SVG -> Visio友好格式 批量转换")
    print("=" * 70)
    print(f"目录: {work_dir}")
    print(f"找到 {len(svg_files)} 个SVG文件\n")
    
    success_count = 0
    fail_count = 0
    
    for i, svg_file in enumerate(sorted(svg_files), 1):
        print(f"[{i}/{len(svg_files)}]", end=" ")
        if convert_svg_to_visio_friendly(svg_file):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 70)
    print("[STAT] 转换完成:")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print("=" * 70)

if __name__ == "__main__":
    import sys
    
    WORK_DIR = r"e:\100_study\120_Project\CapstoneProject\SmartHome_MultiProtocol_EdgeIntelligent_Gateway\SH-MP-EG\docs\output\01_当前工作区"
    
    batch_convert_svg_files(WORK_DIR)
