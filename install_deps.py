#!/usr/bin/env python3
"""
Media Packer 依赖安装脚本
自动检查和安装所需的依赖包
"""

import sys
import subprocess
import argparse

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
    ]
    
    for method in install_methods:
        try:
            result = subprocess.run(method, capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✓ {package} 安装成功")
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
        return False

def main():
    parser = argparse.ArgumentParser(description='Media Packer 依赖安装工具')
    parser.add_argument('--mode', choices=['simple', 'full'], default='simple',
                       help='安装模式: simple(简化版) 或 full(完整版)')
    parser.add_argument('--force', action='store_true',
                       help='强制重新安装所有依赖')
    
    args = parser.parse_args()
    
    # 定义依赖包
    simple_packages = {
        'torf': 'torf>=4.0.0',
        'click': 'click>=8.0.0', 
        'rich': 'rich>=13.0.0'
    }
    
    full_packages = {
        **simple_packages,
        'pymediainfo': 'pymediainfo>=5.0.0',
        'tmdbv3api': 'tmdbv3api>=1.8.0',
        'requests': 'requests>=2.28.0'
    }
    
    packages = full_packages if args.mode == 'full' else simple_packages
    
    print(f"Media Packer 依赖安装 - {args.mode}模式")
    print("=" * 50)
    
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
        return 0
    else:
        print("❌ 部分依赖安装失败")
        print("\n请检查网络连接或手动安装失败的依赖")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
