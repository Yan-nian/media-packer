#!/usr/bin/env python3
"""
Media Packer 依赖安装脚本
自动检查和安装所需的依赖包
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path

# 版本信息
try:
    from version import __version__
except ImportError:
    __version__ = "unknown"

def install_package(package, mode='user'):
    """安装单个包，处理现代Python环境限制"""
    print(f"安装 {package}...")
    
    # 尝试多种安装方式
    install_methods = [
        # 方式1: 用户安装
        [sys.executable, '-m', 'pip', 'install', '--user', package],
        # 方式2: 用户安装 + break-system-packages
        [sys.executable, '-m', 'pip', 'install', '--user', '--break-system-packages', package],
        # 方式3: 标准安装（旧系统）
        [sys.executable, '-m', 'pip', 'install', package],
        # 方式4: 在虚拟环境中安装
        [sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'],
        [sys.executable, '-m', 'venv', 'venv'],
        ['./venv/bin/pip' if os.name != 'nt' else 'venv\\Scripts\\pip.exe', 'install', package],
    ]
    
    # 在当前目录创建虚拟环境
    venv_path = Path.cwd() / 'venv'
    
    for i, method in enumerate(install_methods):
        try:
            # 特殊处理虚拟环境的创建和使用
            if i == 3:  # 升级pip
                subprocess.run(method, capture_output=True, text=True, timeout=300)
                continue
            elif i == 4:  # 创建虚拟环境
                if not venv_path.exists():
                    subprocess.run(method, capture_output=True, text=True, timeout=300)
                continue
            elif i == 5:  # 在虚拟环境中安装
                venv_pip = str(venv_path / ('Scripts/pip.exe' if os.name == 'nt' else 'bin/pip'))
                method[0] = venv_pip
                if not os.path.exists(venv_pip):
                    continue
                    
            result = subprocess.run(method, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✓ {package} 安装成功")
                # 如果是在虚拟环境中安装，记录虚拟环境信息
                if i == 5:
                    with open('venv_info.txt', 'w') as f:
                        f.write("使用虚拟环境安装依赖\n")
                        f.write("运行前请激活虚拟环境: source venv/bin/activate (Linux/Mac) 或 venv\\Scripts\\activate (Windows)\n")
                return True
            else:
                # 如果是externally-managed-environment错误，尝试下一个方法
                if "externally-managed-environment" in result.stderr:
                    continue
                # 其他错误，显示错误信息
                print(f"✗ {package} 安装失败: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print(f"✗ {package} 安装超时")
        except Exception as e:
            print(f"✗ {package} 安装异常: {str(e)}")
    
    # 所有方法都失败了
    print(f"✗ {package} 所有安装方法都失败")
    return False

def check_package(package_name):
    """检查包是否已安装"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        # 检查虚拟环境中的包
        venv_path = Path.cwd() / 'venv'
        if venv_path.exists():
            try:
                # 构建虚拟环境中的Python路径
                venv_python = str(venv_path / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python'))
                result = subprocess.run([venv_python, '-c', f'import {package_name}'], 
                                        capture_output=True, text=True)
                return result.returncode == 0
            except:
                pass
        return False

def check_pip():
    """检查pip是否可用"""
    try:
        subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                       capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def install_pip():
    """安装pip"""
    try:
        # 尝试使用ensurepip安装pip
        subprocess.run([sys.executable, '-m', 'ensurepip', '--upgrade'], 
                       capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        print("✗ 无法自动安装pip，请手动安装pip")
        return False

def main():
    parser = argparse.ArgumentParser(description=f'Media Packer 依赖安装工具 v{__version__}')
    parser.add_argument('--mode', choices=['simple', 'full'], default='simple',
                       help='安装模式: simple(简化版) 或 full(完整版)')
    parser.add_argument('--force', action='store_true',
                       help='强制重新安装所有依赖')
    parser.add_argument('--use-venv', action='store_true',
                       help='强制使用虚拟环境安装')
    parser.add_argument('--version', action='version', version=f'Media Packer 依赖安装工具 v{__version__}')
    
    args = parser.parse_args()
    
    print(f"Media Packer 依赖安装 - {args.mode}模式 (v{__version__})")
    print("=" * 50)
    
    # 检查pip
    if not check_pip():
        print("✗ 未找到pip，尝试安装...")
        if not install_pip():
            print("✗ pip安装失败，无法继续")
            return 1
    
    # 定义依赖包
    simple_packages = {
        'torf': 'torf>=4.0.0',
        'click': 'click>=8.0.0', 
        'rich': 'rich>=13.0.0',
        'psutil': 'psutil>=5.8.0'
    }
    
    full_packages = {
        **simple_packages,
        'pymediainfo': 'pymediainfo>=5.0.0',
        'tmdbv3api': 'tmdbv3api>=1.8.0',
        'requests': 'requests>=2.28.0'
    }
    
    packages = full_packages if args.mode == 'full' else simple_packages
    
    # 检查已安装的包
    if not args.force:
        print("检查已安装的依赖...")
        installed_packages = []
        missing_packages = []
        
        for package_name, package_spec in packages.items():
            if check_package(package_name):
                print(f"✓ {package_name} 已安装")
                installed_packages.append(package_name)
            else:
                print(f"✗ {package_name} 未安装")
                missing_packages.append((package_name, package_spec))
        
        if not missing_packages:
            print("\n🎉 所有依赖都已安装！")
            return 0
        
        packages_to_install = missing_packages
    else:
        print("强制重新安装所有依赖...")
        packages_to_install = list(packages.items())
    
    # 安装依赖
    print(f"\n开始安装 {len(packages_to_install)} 个依赖包...")
    
    success_count = 0
    for package_name, package_spec in packages_to_install:
        if install_package(package_spec):
            success_count += 1
    
    # 结果统计
    print("\n" + "=" * 50)
    print(f"安装完成: {success_count}/{len(packages_to_install)} 个包安装成功")
    
    if success_count == len(packages_to_install):
        print("🎉 所有依赖安装成功！")
        print(f"\n现在可以运行:")
        if args.mode == 'simple':
            print("  python3 media_packer_simple.py")
        else:
            print("  python3 media_packer_all_in_one.py")
            
        # 提示虚拟环境信息
        if os.path.exists('venv_info.txt'):
            with open('venv_info.txt', 'r') as f:
                print(f.read())
        return 0
    else:
        print("❌ 部分依赖安装失败")
        print("\n请检查网络连接或手动安装失败的依赖")
        if os.path.exists('venv_info.txt'):
            with open('venv_info.txt', 'r') as f:
                print(f.read())
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)