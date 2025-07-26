#!/usr/bin/env python3
"""
Media Packer 启动脚本
自动选择合适的版本并安装依赖
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 版本信息
try:
    from version import __version__
except ImportError:
    __version__ = "unknown"

def print_banner():
    """显示横幅"""
    banner = f"""
╭─────────────────────────────────────────────────╮
│              Media Packer 启动器               │
│          自动依赖安装和版本选择工具             │
│              版本: v{__version__}                       │
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

def install_dependencies(mode='simple'):
    """安装依赖"""
    print(f"\n安装 {mode} 模式依赖...")
    
    # 检查是否存在安装脚本
    install_script = Path(__file__).parent / 'install_deps.py'
    if install_script.exists():
        try:
            cmd = [sys.executable, str(install_script), '--mode', mode]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ 依赖安装成功")
                return True
            else:
                print(f"✗ 依赖安装失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"✗ 依赖安装异常: {e}")
            return False
    else:
        print("✗ 未找到依赖安装脚本")
        return False

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

def check_dependencies(mode='simple'):
    """检查依赖是否已安装"""
    # 简化版依赖
    simple_deps = ['torf', 'click', 'rich', 'psutil']
    
    # 完整版额外依赖
    full_deps = simple_deps + ['pymediainfo', 'tmdbv3api', 'requests']
    
    deps = full_deps if mode == 'full' else simple_deps
    
    missing_deps = []
    for dep in deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    return missing_deps

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
    parser = argparse.ArgumentParser(description=f'Media Packer 启动器 v{__version__}')
    parser.add_argument('--mode', choices=['simple', 'full'], help='直接指定模式，跳过选择')
    parser.add_argument('--install-deps', action='store_true', help='只安装依赖')
    parser.add_argument('--check-deps', action='store_true', help='只检查依赖')
    parser.add_argument('--version', action='version', version=f'Media Packer 启动器 v{__version__}')
    
    args, unknown_args = parser.parse_known_args()
    
    # 传递额外参数到子脚本
    sys.argv = [sys.argv[0]] + unknown_args
    
    print_banner()
    
    # 检查Python版本
    if not check_python_version():
        input("\n按回车键退出...")
        return 1
    
    # 只检查依赖
    if args.check_deps:
        mode = args.mode or 'simple'
        missing_deps = check_dependencies(mode)
        if missing_deps:
            print(f"✗ 缺少以下依赖: {', '.join(missing_deps)}")
            return 1
        else:
            print(f"✓ 所有 {mode} 模式依赖已安装")
            return 0
    
    # 只安装依赖
    if args.install_deps:
        mode = args.mode or 'simple'
        if install_dependencies(mode):
            print(f"✓ {mode} 模式依赖安装完成")
            return 0
        else:
            print(f"✗ {mode} 模式依赖安装失败")
            return 1
    
    # 获取用户选择的模式
    if args.mode:
        choice = 1 if args.mode == 'simple' else 2
    else:
        choice = get_user_choice()
    
    if choice == 1:
        mode = 'simple'
        script_name = "media_packer_simple.py"
        print("\n选择了简化版 - 专注种子生成")
    elif choice == 2:
        mode = 'full'
        script_name = "media_packer_all_in_one.py"
        print("\n选择了完整版 - 包含元数据功能")
    elif choice == 3:
        print("\n再见！")
        return 0
    
    # 检查依赖
    missing_deps = check_dependencies(mode)
    if missing_deps:
        print(f"\n检测到缺少依赖: {', '.join(missing_deps)}")
        install_choice = input("是否现在安装依赖？(Y/n): ").strip().lower()
        if install_choice in ['', 'y', 'yes']:
            if not install_dependencies(mode):
                print("依赖安装失败，请手动安装后重试")
                return 1
    
    # 运行脚本
    run_script(script_name)
    
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