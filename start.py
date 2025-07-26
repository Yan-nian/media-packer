#!/usr/bin/env python3
"""
Media Packer 启动脚本
自动选择合适的版本并安装依赖
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """显示横幅"""
    banner = """
╭─────────────────────────────────────────────────╮
│              Media Packer 启动器               │
│          自动依赖安装和版本选择工具             │
╰─────────────────────────────────────────────────╯
"""
    print(banner)

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要 Python 3.8 或更高版本")
        print(f"当前版本: Python {sys.version}")
        return False
    else:
        print(f"✓ Python 版本检查通过: {sys.version}")
        return True

def get_user_choice():
    """获取用户选择"""
    print("\n请选择要使用的版本:")
    print("1. 简化版 (推荐) - 只生成种子文件，依赖最少")
    print("2. 完整版 - 包含元数据获取和NFO生成")
    print("3. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-3): ").strip()
            if choice in ['1', '2', '3']:
                return int(choice)
            else:
                print("请输入有效的选择 (1-3)")
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            return 3
        except:
            print("请输入有效的选择 (1-3)")

def run_script(script_name):
    """运行指定的脚本"""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ 错误: 找不到脚本文件 {script_name}")
        return False
    
    try:
        print(f"\n启动 {script_name}...")
        print("=" * 50)
        
        # 使用当前Python解释器运行脚本
        os.execv(sys.executable, [sys.executable, str(script_path)] + sys.argv[1:])
        
    except Exception as e:
        print(f"❌ 启动脚本失败: {e}")
        return False

def main():
    """主函数"""
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        input("\n按回车键退出...")
        return 1
    
    # 获取用户选择
    choice = get_user_choice()
    
    if choice == 1:
        print("\n选择了简化版 - 专注种子生成")
        run_script("media_packer_simple.py")
    elif choice == 2:
        print("\n选择了完整版 - 包含元数据功能")
        run_script("media_packer_all_in_one.py")
    elif choice == 3:
        print("\n再见！")
        return 0
    
    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序出现异常: {e}")
        input("按回车键退出...")
        sys.exit(1)
