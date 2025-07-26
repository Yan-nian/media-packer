"""Example usage of Media Packer"""

# 基本使用示例
example_usage = '''
# 1. 安装依赖
pip install torf requests click pydantic tmdbv3api pymediainfo colorama rich watchdog

# 2. 基本打包命令
media-packer pack /path/to/video.mkv

# 3. 完整功能打包
media-packer pack /path/to/show/Season1 \\
  --organize \\
  --fetch-metadata \\
  --create-nfo \\
  --output /path/to/output

# 4. 批量制种
media-packer batch \\
  /path/to/season1 \\
  /path/to/season2 \\
  --name "Complete Series" \\
  --output /path/to/torrents

# 5. 搜索元数据
media-packer search "Breaking Bad" --type tv --year 2008

# 6. 查看种子信息
media-packer info /path/to/torrent.torrent
'''

# 配置文件示例
config_example = '''{
  "torrent": {
    "trackers": [
      "https://tracker1.example.com/announce",
      "https://tracker2.example.com/announce"
    ],
    "private": true,
    "comment": "Created with Media Packer",
    "piece_size": null
  },
  "naming": {
    "tv_format": "{title} ({year}) S{season:02d}E{episode:02d} [{resolution}] [{codec}]",
    "movie_format": "{title} ({year}) [{resolution}] [{codec}]",
    "season_folder": "Season {season:02d}",
    "include_year": true,
    "include_resolution": true,
    "include_codec": true
  },
  "tmdb_api_key": "your_tmdb_api_key_here",
  "output_dir": "./output",
  "temp_dir": "./temp"
}'''

# Python API 示例
python_api_example = '''
from pathlib import Path
from media_packer.config import load_config
from media_packer.core.processor import MediaProcessor
from media_packer.core.torrent import TorrentCreator
from media_packer.core.metadata import MetadataManager
from media_packer.utils.naming import FileNamer, FileOrganizer
from media_packer.models import MediaFile

# 加载配置
config = load_config()

# 处理媒体文件
video_path = Path("episode.mkv")
media_info = MediaProcessor.extract_media_info(video_path)
media_type = MediaProcessor.detect_media_type(video_path)
episode_info = MediaProcessor.extract_episode_info(video_path)
subtitle_files = MediaProcessor.find_subtitle_files(video_path)

# 创建媒体文件对象
media_file = MediaFile(
    media_info=media_info,
    media_type=media_type,
    episode_info=episode_info,
    subtitle_files=subtitle_files
)

# 获取元数据
if config.tmdb_api_key:
    metadata_manager = MetadataManager(config.tmdb_api_key)
    title, year = MediaProcessor.extract_title_and_year(video_path)
    metadata = metadata_manager.auto_match_metadata(title, year, media_type)
    
    if metadata and metadata['confidence'] > 0.7:
        if metadata['type'] == 'series':
            media_file.series_info = metadata['info']

# 组织文件
namer = FileNamer(config.naming)
organizer = FileOrganizer(config.output_dir, namer)
organized_path = organizer.organize_file(media_file, copy=True)

# 创建种子
torrent_creator = TorrentCreator(config.torrent)
torrent_path = torrent_creator.create_media_torrent(
    media_file, organized_path, config.output_dir
)

print(f"Torrent created: {torrent_path}")
'''

# 自动化处理示例
automation_example = '''
from pathlib import Path
from media_packer.config import load_config
from media_packer.core.automation import AutomationManager

# 加载配置
config = load_config()

# 创建自动化管理器
automation = AutomationManager(config)

# 设置监控目录
watch_directories = [
    Path("/downloads/tv"),
    Path("/downloads/movies"),
    Path("/incoming")
]

# 启动自动处理
automation.start_automation(watch_directories)

try:
    # 保持运行
    while True:
        import time
        time.sleep(10)
        
        # 检查状态
        status = automation.get_status()
        print(f"处理状态: 待处理={status['pending_tasks']}, "
              f"已完成={status['completed_tasks']}, "
              f"错误={status['error_tasks']}")
        
except KeyboardInterrupt:
    print("停止自动处理...")
    automation.stop_automation()
'''

print("Media Packer 使用示例")
print("="*50)
print("\\n1. 命令行使用:")
print(example_usage)

print("\\n2. 配置文件 (config.json):")
print(config_example)

print("\\n3. Python API 使用:")
print(python_api_example)

print("\\n4. 自动化处理:")
print(automation_example)