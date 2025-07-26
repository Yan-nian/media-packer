#!/usr/bin/env python3
"""
测试种子命名功能
"""

import tempfile
import shutil
from pathlib import Path
from media_packer_all_in_one import Config, MediaPacker

def test_folder_based_naming():
    """测试基于文件夹名称的种子命名功能"""
    print("测试基于文件夹名称的种子命名功能...")
    
    # 创建临时目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试文件夹和文件
        test_folder = temp_path / "Test_Movie_2024"
        test_folder.mkdir()
        
        test_file = test_folder / "movie.mkv"
        test_file.write_text("fake video content")
        
        # 创建输出目录
        output_dir = temp_path / "output"
        output_dir.mkdir()
        
        # 配置
        config = Config(
            trackers=["http://test.tracker:8080/announce"],
            output_dir=output_dir
        )
        
        # 创建 MediaPacker 实例
        packer = MediaPacker(config)
        
        try:
            # 测试自定义名称功能
            print(f"处理文件: {test_file}")
            print(f"文件夹名称: {test_folder.name}")
            
            # 使用自定义名称创建种子
            torrent_path = packer.create_torrent_for_file(
                test_file,
                custom_name="Test_Movie_2024",
                organize=False,
                fetch_metadata=False,
                create_nfo=False
            )
            
            print(f"生成的种子文件: {torrent_path}")
            
            # 验证种子文件名
            expected_name = "Test_Movie_2024.torrent"
            if torrent_path.name == expected_name:
                print("✓ 种子命名测试通过")
                return True
            else:
                print(f"✗ 种子命名测试失败，期望: {expected_name}，实际: {torrent_path.name}")
                return False
                
        except Exception as e:
            print(f"✗ 测试过程中出错: {e}")
            return False

def test_default_naming():
    """测试默认命名（不指定自定义名称时）"""
    print("\n测试默认命名功能...")
    
    # 创建临时目录结构
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 创建测试文件夹和文件
        test_folder = temp_path / "Default_Test_Folder"
        test_folder.mkdir()
        
        test_file = test_folder / "video.mp4"
        test_file.write_text("fake video content")
        
        # 创建输出目录
        output_dir = temp_path / "output"
        output_dir.mkdir()
        
        # 配置
        config = Config(
            trackers=["http://test.tracker:8080/announce"],
            output_dir=output_dir
        )
        
        # 创建 MediaPacker 实例
        packer = MediaPacker(config)
        
        try:
            # 测试默认命名（不指定 custom_name）
            print(f"处理文件: {test_file}")
            
            torrent_path = packer.create_torrent_for_file(
                test_file,
                organize=False,
                fetch_metadata=False,
                create_nfo=False
            )
            
            print(f"生成的种子文件: {torrent_path}")
            
            # 验证种子文件名（应该基于文件名或组织后的路径）
            if torrent_path.exists():
                print("✓ 默认命名测试通过 - 种子文件已创建")
                return True
            else:
                print("✗ 默认命名测试失败 - 种子文件未创建")
                return False
                
        except Exception as e:
            print(f"✗ 测试过程中出错: {e}")
            return False

if __name__ == '__main__':
    print("开始测试种子命名功能...\n")
    
    success_count = 0
    total_tests = 2
    
    # 运行测试
    if test_folder_based_naming():
        success_count += 1
    
    if test_default_naming():
        success_count += 1
    
    print(f"\n测试完成: {success_count}/{total_tests} 个测试通过")
    
    if success_count == total_tests:
        print("✓ 所有种子命名功能测试通过")
    else:
        print("✗ 部分测试失败")
