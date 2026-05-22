"""
批量生成所有图表的SVG格式版本
=============================
将所有PNG图表转换为矢量SVG格式，可在Visio中自由编辑。
"""

import os
import sys
import subprocess
from pathlib import Path

# ==================== 配置 ====================
WORK_DIR = Path(r"e:\100_study\120_Project\CapstoneProject\SmartHome_MultiProtocol_EdgeIntelligent_Gateway\SH-MP-EG\docs\output\01_当前工作区")

# 所有绘图脚本列表（按论文顺序排列）
SCRIPTS = [
    "draw_architecture_diagram.py",      # 图2-1 系统整体架构图
    "draw_sequence_diagram.py",          # 图2-2 跨协议联动时序图
    "draw_dataflow_diagram.py",          # 图3-1 系统数据流架构图
    "draw_hardware_diagram.py",          # 图3-3 硬件系统连接框图
    "draw_software_diagram.py",          # 图3-5 软件系统架构图
    "draw_module_call_diagram.py",       # 图4-1 软件系统模块调用关系图
    "draw_wifi_flow_diagram.py",         # 图4-2 Wi-Fi终端接入模块流程图
    "draw_ble_flow_diagram.py",          # 图4-4 BLE终端接入模块流程图
    "draw_message_routing_diagram.py",   # 图4-4 消息路由处理流程图
    "draw_cache_diagram.py",             # 图4-6 离线缓存与补传机制流程图
    "draw_test_topology_diagram.py",     # 图5-1 测试环境网络拓扑图
]

def create_svg_converter(script_name):
    """为单个脚本创建带SVG输出的修改版"""
    script_path = WORK_DIR / script_name

    if not script_path.exists():
        print(f"[WARN] 脚本不存在: {script_name}")
        return None

    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否已经包含SVG输出（更严格的检查）
    if "svg_path" in content and 'plt.savefig(svg_path' in content:
        print(f"[OK] {script_name} 已包含SVG输出")
        return None

    # 找到保存PNG的部分并添加SVG保存
    if 'savefig(' in content:
        # 创建修改后的内容：在PNG保存后添加SVG保存
        modified_content = content.replace(
            '''print(f"Saved -> {output_path}")''',
            '''print(f"Saved -> {output_path}")

# 保存SVG格式（可在Visio中编辑）
svg_path = output_path.replace('.png', '.svg')
if 'fig' in dir():
    fig.savefig(svg_path, format='svg', bbox_inches="tight",
                facecolor="white", edgecolor="none")
else:
    plt.savefig(svg_path, format='svg', bbox_inches="tight",
                facecolor="white", edgecolor="none")
print(f"Saved -> {svg_path}")'''
        )

        # 写入临时文件
        temp_script = WORK_DIR / f"temp_{script_name}"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        return temp_script

    return None

def main():
    print("=" * 70)
    print("[INFO] 批量生成SVG格式图表（Visio可编辑）")
    print("=" * 70)

    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, script in enumerate(SCRIPTS, 1):
        print(f"\n[{i}/{len(SCRIPTS)}] 处理: {script}")
        print("-" * 50)

        try:
            # 创建修改版脚本
            temp_script = create_svg_converter(script)

            if temp_script is None:
                skip_count += 1
                continue

            # 运行修改版脚本
            result = subprocess.run(
                [sys.executable, str(temp_script)],
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                success_count += 1
                print(f"[OK] 成功生成: {script}")
            else:
                fail_count += 1
                print(f"[FAIL] 执行失败: {script}")
                print(f"   错误: {result.stderr}")

            # 清理临时文件
            if temp_script.exists():
                temp_script.unlink()

        except Exception as e:
            fail_count += 1
            print(f"[ERROR] 异常: {script}")
            print(f"   错误: {str(e)}")

    # 统计结果
    print("\n" + "=" * 70)
    print("[STAT] 生成完成统计")
    print("=" * 70)
    print(f"[OK]   成功: {success_count} 个")
    print(f"[SKIP] 跳过: {skip_count} 个 (已包含SVG)")
    print(f"[FAIL] 失败: {fail_count} 个")

    # 列出生成的SVG文件
    print("\n[LIST] 生成的SVG文件列表:")
    svg_files = list(WORK_DIR.glob("*.svg"))
    for i, svg_file in enumerate(sorted(svg_files), 1):
        size_kb = svg_file.stat().st_size / 1024
        print(f"  {i}. {svg_file.name} ({size_kb:.1f} KB)")

    print("\n[TIPS] 使用说明:")
    print("   - SVG为矢量格式，可无限缩放不失真")
    print("   - 可使用Adobe Illustrator、Inkscape、Visio等软件编辑")
    print("   - Visio导入方法: 插入 -> 图片 -> 选择SVG文件")

if __name__ == "__main__":
    main()
