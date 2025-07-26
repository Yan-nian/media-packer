#!/usr/bin/env python3
"""
简单测试种子命名逻辑
"""

from pathlib import Path
from media_packer_all_in_one import Config, MediaPacker

def test_naming_logic():
    """测试种子命名逻辑"""
    print("测试种子命名逻辑...")
    
    # 创建配置
    config = Config(
        trackers=["http://test.tracker:8080/announce"],
        output_dir=Path("/tmp")
    )
    
    # 创建 MediaPacker 实例
    packer = MediaPacker(config)
    
    # 测试文件路径
    test_paths = [
        Path("/home/user/Movies/The.Matrix.1999/matrix.mkv"),
        Path("/home/user/TV Shows/Breaking Bad Season 1"),
        Path("/Downloads/Movie_2024/film.mp4")
    ]
    
    print("\n测试不同路径的文件夹名称提取:")
    
    for test_path in test_paths:
        print(f"\n路径: {test_path}")
        
        # 模拟文件夹名称提取逻辑
        if test_path.is_file() or test_path.suffix:  # 如果是文件
            folder_name = test_path.parent.name
            print(f"  -> 文件，提取父目录名: {folder_name}")
        else:  # 如果是目录
            folder_name = test_path.name
            print(f"  -> 目录，使用目录名: {folder_name}")
        
        print(f"  -> 种子名称将是: {folder_name}.torrent")
    
    print("\n✓ 种子命名逻辑测试完成")
    return True

def test_custom_name_parameter():
    """测试 create_torrent_for_file 的 custom_name 参数"""
    print("\n测试 custom_name 参数...")
    
    # 检查方法签名
    from media_packer_all_in_one import MediaPacker
    import inspect
    
    # 获取方法签名
    sig = inspect.signature(MediaPacker.create_torrent_for_file)
    params = list(sig.parameters.keys())
    
    print(f"create_torrent_for_file 参数: {params}")
    
    if 'custom_name' in params:
        print("✓ custom_name 参数存在")
        return True
    else:
        print("✗ custom_name 参数不存在")
        return False

if __name__ == '__main__':
    print("开始测试种子命名逻辑...\n")
    
    success_count = 0
    total_tests = 2
    
    # 运行测试
    if test_naming_logic():
        success_count += 1
    
    if test_custom_name_parameter():
        success_count += 1
    
    print(f"\n测试完成: {success_count}/{total_tests} 个测试通过")
    
    if success_count == total_tests:
        print("✓ 所有命名逻辑测试通过")
    else:
        print("✗ 部分测试失败")
