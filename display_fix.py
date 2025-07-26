#!/usr/bin/env python3
"""
进度条显示修复补丁
解决进度条与文本重叠的问题
"""

import os
import sys
from pathlib import Path

def fix_progress_display():
    """修复进度条显示重叠问题"""
    
    script_path = Path("media_packer_simple.py")
    if not script_path.exists():
        print("错误：找不到 media_packer_simple.py 文件")
        return False
    
    print("正在修复进度条显示重叠问题...")
    
    # 备份原文件
    backup_path = Path("media_packer_simple.py.backup2")
    if not backup_path.exists():
        import shutil
        shutil.copy2(script_path, backup_path)
        print(f"已备份原文件到: {backup_path}")
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复1: 移除重复的console.print调用
        old_code1 = '''        self.console.print(f"[cyan]处理文件夹: {folder_name}[/cyan]")
                        
                        # 直接为文件夹创建种子
                        torrent_path = packer.create_torrent_for_file('''
        
        new_code1 = '''        # 为文件夹创建种子（不重复打印）
                        torrent_path = packer.create_torrent_for_file('''
        
        if old_code1 in content:
            content = content.replace(old_code1, new_code1)
            print("✓ 已移除重复的文件夹处理提示")
        
        # 修复2: 移除文件处理中的重复打印
        old_code2 = '''        self.console.print(f"[cyan]处理文件: {file_name}[/cyan]")
                        
                        # 获取文件夹名称'''
        
        new_code2 = '''        # 获取文件夹名称（不重复打印）'''
        
        if old_code2 in content:
            content = content.replace(old_code2, new_code2)
            print("✓ 已移除重复的文件处理提示")
        
        # 修复3: 在进度条开始前添加换行，确保不重叠
        old_progress_start = '''            # 生成种子
            console.print(f"[cyan]正在生成种子文件...[/cyan]")
            
            # 尝试设置多线程（如果torf支持）'''
        
        new_progress_start = '''            # 生成种子（为进度条预留空间）
            console.print(f"[cyan]正在生成种子文件...[/cyan]")
            console.print("")  # 空行，避免与进度条重叠
            
            # 尝试设置多线程（如果torf支持）'''
        
        if old_progress_start in content:
            content = content.replace(old_progress_start, new_progress_start)
            print("✓ 已在进度条前添加空行")
        
        # 修复4: 确保进度条使用独立的控制台区域
        old_progress_config = '''            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=2  # 限制刷新频率
            ) as progress:'''
        
        new_progress_config = '''            # 使用独立的进度条显示，避免与其他输出重叠
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=2,  # 限制刷新频率
                transient=False  # 进度条完成后保留显示
            ) as progress:'''
        
        if old_progress_config in content:
            content = content.replace(old_progress_config, new_progress_config)
            print("✓ 已优化进度条配置")
        
        # 修复5: 在进度条完成后添加换行
        old_end_code = '''            console.print(f"\\n[green]哈希计算完成 - 用时: {duration:.1f}s, 吞吐量: {throughput:.1f} MB/s[/green]")
            
            # 保存种子文件'''
        
        new_end_code = '''            # 确保进度条完成后有清晰的分隔
            console.print("")
            console.print(f"[green]✅ 哈希计算完成 - 用时: {duration:.1f}s, 吞吐量: {throughput:.1f} MB/s[/green]")
            
            # 保存种子文件'''
        
        if old_end_code in content:
            content = content.replace(old_end_code, new_end_code)
            print("✓ 已优化完成提示显示")
        
        # 修复6: 简化任务描述，避免在Progress外部打印任务信息
        old_task_desc = '''                task_progress = progress.add_task(
                            f"处理文件夹: {folder_name} ({task.get('episode_count', 0)} 集)",
                            total=None
                        )'''
        
        new_task_desc = '''                # 直接在进度条中显示任务信息，避免重复
                task_progress = progress.add_task(
                            f"[cyan]制种: {folder_name} ({task.get('episode_count', 0)} 集)[/cyan]",
                            total=None
                        )'''
        
        if old_task_desc in content:
            content = content.replace(old_task_desc, new_task_desc)
            print("✓ 已简化任务描述显示")
        
        # 写入修复后的文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("\n✅ 进度条显示修复完成！")
        print("\n修复内容:")
        print("• 移除重复的处理提示信息")
        print("• 在进度条前后添加适当空行")
        print("• 设置进度条为非临时显示")
        print("• 优化任务描述，集中在进度条中显示")
        print("• 确保文本和进度条不重叠")
        
        return True
        
    except Exception as e:
        print(f"修复失败: {e}")
        return False

def main():
    print("Media Packer 进度条显示修复工具")
    print("=" * 45)
    
    if not fix_progress_display():
        print("修复失败！")
        return 1
    
    print("\n现在进度条应该不会与文本重叠了！")
    print("\n如果还有问题，可以恢复备份:")
    print("cp media_packer_simple.py.backup2 media_packer_simple.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())