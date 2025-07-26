#!/usr/bin/env python3
"""
VPS 部署验证脚本
用于检查 Media Packer 的实际部署状态和性能配置
"""

import sys
import os
import subprocess
from pathlib import Path

def check_version():
    """检查版本信息"""
    print("=== 版本信息检查 ===")
    
    # 检查 version.py 文件
    version_file = Path("version.py")
    if version_file.exists():
        try:
            with open(version_file, 'r') as f:
                content = f.read()
                print(f"✓ version.py 存在: {content.strip()}")
        except Exception as e:
            print(f"✗ 读取 version.py 失败: {e}")
    else:
        print("✗ version.py 文件不存在")
    
    # 检查代码中的版本导入
    try:
        from version import __version__
        print(f"✓ 版本导入成功: {__version__}")
    except ImportError as e:
        print(f"✗ 版本导入失败: {e}")

def check_performance_code():
    """检查性能优化代码"""
    print("\n=== 性能优化代码检查 ===")
    
    script_file = Path("media_packer_simple.py")
    if not script_file.exists():
        print("✗ media_packer_simple.py 不存在")
        return False
    
    try:
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键性能优化代码
        checks = [
            ("physical_cores >= 32", "超高性能CPU检测"),
            ("physical_cores >= 16", "高性能CPU检测"),  
            ("min(12, physical_cores // 2)", "16核CPU优化算法"),
            ("rich.progress import Progress", "进度条功能"),
            ("psutil>=5.8.0", "性能监控依赖"),
            ("SpinnerColumn", "Rich进度条组件"),
            ("TimeRemainingColumn", "剩余时间显示")
        ]
        
        for code_snippet, description in checks:
            if code_snippet in content:
                print(f"✓ {description}: 已包含")
            else:
                print(f"✗ {description}: 缺失")
                
        return True
        
    except Exception as e:
        print(f"✗ 读取文件失败: {e}")
        return False

def check_cpu_detection():
    """测试CPU检测功能"""
    print("\n=== CPU检测测试 ===")
    
    try:
        import multiprocessing
        logical_cores = multiprocessing.cpu_count()
        print(f"✓ 逻辑核心数: {logical_cores}")
        
        try:
            import psutil
            physical_cores = psutil.cpu_count(logical=False)
            print(f"✓ 物理核心数: {physical_cores}")
            
            # 模拟线程数计算
            if physical_cores >= 16:
                optimal_workers = min(12, physical_cores // 2)
                print(f"✓ 16核+CPU优化: 应使用 {optimal_workers} 线程")
            else:
                print(f"! CPU核心数 {physical_cores} < 16，使用标准算法")
                
        except ImportError:
            print("✗ psutil 未安装，无法获取物理核心数")
            
    except Exception as e:
        print(f"✗ CPU检测失败: {e}")

def check_files():
    """检查必要文件"""
    print("\n=== 文件完整性检查 ===")
    
    required_files = [
        "media_packer_simple.py",
        "version.py", 
        "requirements.txt",
        "install_deps.py"
    ]
    
    for file_name in required_files:
        file_path = Path(file_name)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✓ {file_name}: {size} 字节")
        else:
            print(f"✗ {file_name}: 不存在")

def check_symlink():
    """检查系统命令链接"""
    print("\n=== 系统命令检查 ===")
    
    # 检查本地命令
    local_script = Path("media-packer")
    if local_script.exists():
        print("✓ 本地 media-packer 脚本存在")
    else:
        print("✗ 本地 media-packer 脚本不存在")
    
    # 检查系统命令
    try:
        result = subprocess.run(['which', 'media-packer'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ 系统命令: {result.stdout.strip()}")
        else:
            print("✗ 系统命令未安装")
    except Exception as e:
        print(f"! 无法检查系统命令: {e}")

def run_quick_test():
    """运行快速功能测试"""
    print("\n=== 快速功能测试 ===")
    
    try:
        # 测试帮助命令
        result = subprocess.run([sys.executable, 'media_packer_simple.py', '--help'],
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ 脚本可正常运行")
            # 检查输出中的版本信息
            if "Media Packer" in result.stdout:
                print("✓ 程序标识正常")
            if "v2.1" in result.stdout or "2.1" in result.stdout:
                print("✓ 版本信息正常")
        else:
            print(f"✗ 脚本运行失败: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("✗ 脚本运行超时")
    except Exception as e:
        print(f"✗ 脚本测试失败: {e}")

def main():
    print("Media Packer VPS 部署验证工具")
    print("=" * 50)
    print(f"当前目录: {os.getcwd()}")
    print(f"Python版本: {sys.version}")
    print()
    
    # 运行各项检查
    check_version()
    check_files()
    check_performance_code()
    check_cpu_detection()
    check_symlink()
    run_quick_test()
    
    print("\n" + "=" * 50)
    print("验证完成！")
    print("\n如果发现问题，请运行以下命令重新安装:")
    print("curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --force")

if __name__ == "__main__":
    main()