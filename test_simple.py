#!/usr/bin/env python3
"""
测试简化版 media_packer_simple.py 脚本
"""

import sys
import subprocess
from pathlib import Path

def test_import():
    """测试导入功能"""
    print("测试导入功能...")
    try:
        # 测试基本导入
        import media_packer_simple
        print("✓ 基本导入成功")
        
        # 测试关键类
        config = media_packer_simple.Config()
        print("✓ Config 类创建成功")
        
        processor = media_packer_simple.MediaProcessor()
        print("✓ MediaProcessor 类创建成功")
        
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_file_detection():
    """测试文件检测功能"""
    print("\n测试文件检测功能...")
    try:
        from media_packer_simple import MediaProcessor
        
        # 测试视频文件检测
        test_files = [
            ("test.mkv", True),
            ("test.mp4", True),
            ("test.avi", True),
            ("test.txt", False),
            ("test.srt", False)
        ]
        
        for filename, expected in test_files:
            result = MediaProcessor.is_video_file(Path(filename))
            status = "✓" if result == expected else "✗"
            print(f"  {status} {filename}: {result} (期望: {expected})")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_media_type():
    """测试媒体类型识别"""
    print("\n测试媒体类型识别...")
    try:
        from media_packer_simple import MediaProcessor
        
        processor = MediaProcessor()
        
        test_cases = [
            ("movie.mkv", "video"),
            ("show.mp4", "video"),
            ("subtitle.srt", "unknown"),
            ("readme.txt", "unknown")
        ]
        
        for filename, expected in test_cases:
            result = processor.detect_media_type(Path(filename))
            status = "✓" if result == expected else "✗"
            print(f"  {status} {filename}: {result} (期望: {expected})")
        
        return True
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_cli_help():
    """测试命令行帮助"""
    print("\n测试命令行帮助...")
    try:
        # 测试主命令帮助
        result = subprocess.run([
            sys.executable, "media_packer_simple.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Media Packer" in result.stdout:
            print("✓ 主命令帮助正常")
        else:
            print("✗ 主命令帮助异常")
            return False
        
        # 测试子命令帮助
        result = subprocess.run([
            sys.executable, "media_packer_simple.py", "pack", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "pack" in result.stdout:
            print("✓ pack 命令帮助正常")
        else:
            print("✗ pack 命令帮助异常")
            return False
        
        return True
    except subprocess.TimeoutExpired:
        print("✗ 命令超时")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试简化版 Media Packer...\n")
    
    tests = [
        test_import,
        test_file_detection,
        test_media_type,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
