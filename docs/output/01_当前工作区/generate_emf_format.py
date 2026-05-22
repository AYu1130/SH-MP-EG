"""
生成Visio完美兼容的EMF格式图表
================================
EMF（Enhanced Metafile）是Windows原生的矢量图形格式，
在Visio中可以完美编辑每个元素。

特点：
- Visio 100%原生支持
- 每个元素可独立编辑、移动、缩放
- 文字可直接修改
- 矢量无损
"""

import os
import sys
from pathlib import Path

WORK_DIR = Path(r"e:\100_study\120_Project\CapstoneProject\SmartHome_MultiProtocol_EdgeIntelligent_Gateway\SH-MP-EG\docs\output\01_当前工作区")

# 所有绘图脚本列表
SCRIPTS = [
    "draw_architecture_diagram.py",
    "draw_sequence_diagram.py",
    "draw_dataflow_diagram.py",
    "draw_hardware_diagram.py",
    "draw_software_diagram.py",
    "draw_module_call_diagram.py",
    "draw_wifi_flow_diagram.py",
    "draw_ble_flow_diagram.py",
    "draw_message_routing_diagram.py",
    "draw_cache_diagram.py",
    "draw_test_topology_diagram.py",
]

def add_emf_output_to_script(script_path):
    """
    为脚本添加EMF输出功能
    EMF是Windows增强型元文件格式，Visio完美支持
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经包含EMF输出
    if '.emf"' in content and 'emf_path' in content:
        return False, None
    
    # 找到保存PNG的位置并添加EMF保存
    if 'print(f"Saved -> {output_path}")' in content or "print(f'Saved -> {output_path}')" in content:
        # 创建修改后的内容
        modified_content = content.replace(
            '''print(f"Saved -> {output_path}")''',
            '''print(f"Saved -> {output_path}")

    # 保存EMF格式（Visio完美支持，可自由编辑每个元素）
    emf_path = output_path.replace('.png', '.emf')
    try:
        import matplotlib.backends.backend_agg as backend_agg
        if 'fig' in dir():
            fig.savefig(emf_path, format='emf', bbox_inches="tight", facecolor="white")
            print(f"Saved -> {emf_path}")
        else:
            plt.savefig(emf_path, format='emf', bbox_inches="tight", facecolor="white")
            print(f"Saved -> {emf_path}")
    except Exception as emf_error:
        print(f"[WARN] EMF生成失败: {str(emf_error)}")'''
        )
        
        # 写入临时文件
        temp_script = script_path.parent / f"temp_emf_{script_path.name}"
        with open(temp_script, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        return True, temp_script
    
    return False, None

def main():
    print("=" * 70)
    print("[INFO] 生成EMF格式图表（Visio完美兼容）")
    print("=" * 70)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, script_name in enumerate(SCRIPTS, 1):
        script_path = WORK_DIR / script_name
        
        print(f"\n[{i}/{len(SCRIPTS)}] 处理: {script_name}", end=" ")
        
        if not script_path.exists():
            print("[SKIP] 脚本不存在")
            skip_count += 1
            continue
        
        # 添加EMF输出
        has_changes, temp_script = add_emf_output_to_script(script_path)
        
        if not has_changes and temp_script is None:
            print("[SKIP] 已包含EMF")
            skip_count += 1
            continue
        
        if temp_script is None:
            skip_count += 1
            continue
        
        # 运行脚本
        try:
            result = subprocess.run(
                [sys.executable, str(temp_script)],
                cwd=WORK_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                success_count += 1
                print("[OK]")
            else:
                fail_count += 1
                print(f"[FAIL]\n{result.stderr[:200]}")
            
            # 清理临时文件
            if temp_script.exists():
                temp_script.unlink()
                
        except Exception as e:
            fail_count += 1
            print(f"[ERROR] {str(e)}")
    
    # 统计结果
    print("\n" + "=" * 70)
    print("[STAT] 生成完成:")
    print(f"  成功: {success_count}")
    print(f"  跳过: {skip_count}")
    print(f"  失败: {fail_count}")
    
    # 列出生成的EMF文件
    emf_files = list(WORK_DIR.glob("*.emf"))
    if emf_files:
        print("\n[LIST] 生成的EMF文件:")
        for i, emf_file in enumerate(sorted(emf_files), 1):
            size_kb = emf_file.stat().st_size / 1024
            print(f"  {i}. {emf_file.name} ({size_kb:.1f} KB)")
    
    print("\n[TIPS] 使用方法:")
    print("  1. 在Visio中: 插入 -> 图片 -> 此设备 -> 选择.emf文件")
    print("  2. 右键图片 -> 取消组合 (Ctrl+Shift+G)")
    print("  3. 现在每个元素都可以独立编辑！")
    print("     - 移动/调整大小")
    print("     - 修改文字")
    print("     - 更改颜色")
    print("     - 删除不需要的元素")

if __name__ == "__main__":
    import subprocess
    main()
