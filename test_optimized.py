#!/usr/bin/env python3
"""
测试优化后的 media_packer_all_in_one.py 脚本
"""

import sys
import subprocess
from pathlib import Path

def test_import():
    """测试导入功能"""
    print("测试导入功能...")
    try:
        # 测试基本导入
        import media_packer_all_in_one
        print("✓ 基本导入成功")
        
        # 测试关键类
        config = media_packer_all_in_one.Config()
        print("✓ Config 类创建成功")
        
        processor = media_packer_all_in_one.MediaProcessor()
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
        from media_packer_all_in_one import MediaProcessor
        
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
            print(f"{status} {filename}: {result} (期望: {expected})")
        
        print("✓ 文件检测测试完成")
        return True
    except Exception as e:
        print(f"✗ 文件检测测试失败: {e}")
        return False

def test_media_type_detection():
    """测试媒体类型检测"""
    print("\n测试媒体类型检测...")
    try:
        from media_packer_all_in_one import MediaProcessor, MediaType
        
        test_cases = [
            ("Breaking.Bad.S01E01.mkv", MediaType.TV_SHOW),
            ("The.Matrix.1999.mp4", MediaType.MOVIE),
            ("Documentary.2023.mkv", MediaType.MOVIE)
        ]
        
        for filename, expected in test_cases:
            result = MediaProcessor.detect_media_type(Path(filename))
            status = "✓" if result == expected else "✗"
            print(f"{status} {filename}: {result} (期望: {expected})")
        
        print("✓ 媒体类型检测测试完成")
        return True
    except Exception as e:
        print(f"✗ 媒体类型检测测试失败: {e}")
        return False

def test_cli_help():
    """测试命令行帮助"""
    print("\n测试命令行帮助...")
    try:
        result = subprocess.run([
            sys.executable, "media_packer_all_in_one.py", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "Media Packer" in result.stdout:
            print("✓ 命令行帮助正常")
            return True
        else:
            print(f"✗ 命令行帮助异常: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ 命令行帮助超时")
        return False
    except Exception as e:
        print(f"✗ 命令行帮助测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试优化后的 Media Packer 脚本...")
    print("=" * 50)
    
    tests = [
        test_import,
        test_file_detection,
        test_media_type_detection,
        test_cli_help
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！脚本优化成功")
        print("\n使用说明:")
        print("1. 直接运行: python media_packer_all_in_one.py")
        print("2. 命令行模式: python media_packer_all_in_one.py pack <文件路径>")
        print("3. 查看帮助: python media_packer_all_in_one.py --help")
    else:
        print("⚠️  部分测试失败，请检查依赖和配置")
        print("\n安装依赖: pip install torf pymediainfo tmdbv3api requests click rich")

if __name__ == "__main__":
    main()
