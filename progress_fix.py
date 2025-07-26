#!/usr/bin/env python3
"""
进度条修复补丁
解决进度条闪烁问题，降低刷新频率并优化显示逻辑
"""

import os
import sys
from pathlib import Path

def fix_progress_bar():
    """修复进度条闪烁问题"""
    
    script_path = Path("media_packer_simple.py")
    if not script_path.exists():
        print("错误：找不到 media_packer_simple.py 文件")
        return False
    
    print("正在修复进度条闪烁问题...")
    
    # 备份原文件
    backup_path = Path("media_packer_simple.py.backup")
    if not backup_path.exists():
        import shutil
        shutil.copy2(script_path, backup_path)
        print(f"已备份原文件到: {backup_path}")
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复进度条刷新逻辑
        old_progress_code = '''                # 添加进度回调函数
                def progress_callback(torrent, filepath, pieces_done, pieces_total):
                    if pieces_total > 0:
                        percent = (pieces_done / pieces_total) * 100
                        progress.update(task, completed=percent)
                        if pieces_done > 0:
                            elapsed = time.time() - start_time
                            speed = (pieces_done / elapsed) if elapsed > 0 else 0
                            progress.update(task, description=f"[cyan]制种进度 ({optimal_workers} 线程) - {speed:.1f} pieces/s")
                
                # 尝试设置进度回调
                try:
                    torrent.generate(callback=progress_callback, interval=1)'''

        new_progress_code = '''                # 添加进度回调函数 - 优化版本
                last_update_time = 0
                def progress_callback(torrent, filepath, pieces_done, pieces_total):
                    nonlocal last_update_time
                    current_time = time.time()
                    
                    # 限制刷新频率，避免闪烁（每0.5秒更新一次）
                    if current_time - last_update_time < 0.5 and pieces_done < pieces_total:
                        return
                    
                    last_update_time = current_time
                    
                    if pieces_total > 0:
                        percent = (pieces_done / pieces_total) * 100
                        progress.update(task, completed=percent)
                        
                        if pieces_done > 0:
                            elapsed = current_time - start_time
                            speed = (pieces_done / elapsed) if elapsed > 0 else 0
                            eta_seconds = ((pieces_total - pieces_done) / speed) if speed > 0 else 0
                            
                            # 更新描述信息，但不要太频繁
                            if pieces_done % 10 == 0 or pieces_done == pieces_total:
                                progress.update(task, description=f"[cyan]制种进度 ({optimal_workers} 线程) - {speed:.1f} pieces/s")
                
                # 尝试设置进度回调
                try:
                    torrent.generate(callback=progress_callback, interval=2)'''

        if old_progress_code in content:
            content = content.replace(old_progress_code, new_progress_code)
            print("✓ 已修复进度回调刷新频率")
        else:
            print("! 未找到需要修复的进度回调代码")
        
        # 修复 Rich Progress 配置
        old_config = '''            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:'''
            
        new_config = '''            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=console,
                refresh_per_second=2  # 限制刷新频率
            ) as progress:'''
        
        if old_config in content:
            content = content.replace(old_config, new_config)
            print("✓ 已修复 Progress 刷新频率")
        else:
            print("! 未找到需要修复的 Progress 配置")
        
        # 写入修复后的文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 进度条修复完成！")
        print("\n修复内容:")
        print("• 限制进度条刷新频率为每0.5秒一次")
        print("• 设置Rich Progress整体刷新频率为2Hz")
        print("• 优化描述信息更新逻辑")
        print("• 避免过度频繁的屏幕刷新")
        
        return True
        
    except Exception as e:
        print(f"修复失败: {e}")
        return False

def main():
    print("Media Packer 进度条修复工具")
    print("=" * 40)
    
    if not fix_progress_bar():
        print("修复失败！")
        return 1
    
    print("\n现在可以测试修复效果:")
    print("python3 media_packer_simple.py pack /path/to/your/file")
    print("\n如果还有问题，可以恢复备份:")
    print("cp media_packer_simple.py.backup media_packer_simple.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())