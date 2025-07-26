#!/usr/bin/env python3
"""
Media Packer - 单文件完整实现
基于 torf 的影视剧打包制种工具，专为影视内容制作标准化 torrent 文件。
"""

import os
import re
import json
import shutil
import logging
import time
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

# 依赖检查和自动安装
def check_and_install_dependencies():
    """检查并自动安装依赖"""
    required_packages = {
        'torf': 'torf>=4.0.0',
        'pymediainfo': 'pymediainfo>=5.0.0', 
        'tmdbv3api': 'tmdbv3api>=1.8.0',
        'requests': 'requests>=2.28.0',
        'click': 'click>=8.0.0',
        'rich': 'rich>=13.0.0'
    }
    
    missing_packages = []
    
    # 检查依赖
    for package_name, package_spec in required_packages.items():
        try:
            __import__(package_name)
            print(f"✓ {package_name} 已安装")
        except ImportError:
            missing_packages.append(package_spec)
            print(f"✗ {package_name} 未安装")
    
    # 如果有缺失的包，询问是否自动安装
    if missing_packages:
        print(f"\n发现 {len(missing_packages)} 个缺失的依赖包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        
        # 在非交互环境中自动安装
        if not sys.stdin.isatty():
            install_choice = 'y'
        else:
            install_choice = input("\n是否自动安装缺失的依赖? (y/n): ").lower().strip()
        
        if install_choice in ['y', 'yes', '']:
            print("\n正在安装依赖...")
            try:
                for package_spec in missing_packages:
                    print(f"安装 {package_spec}...")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', package_spec
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✓ {package_spec} 安装成功")
                    else:
                        print(f"✗ {package_spec} 安装失败: {result.stderr}")
                        return False
                
                print("\n所有依赖安装完成！正在重新启动程序...")
                # 重新启动脚本
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
            except Exception as e:
                print(f"安装依赖时出错: {e}")
                print("请手动安装依赖: pip install torf pymediainfo tmdbv3api requests click rich")
                return False
        else:
            print("请手动安装依赖后再运行:")
            print("pip install torf pymediainfo tmdbv3api requests click rich")
            return False
    
    return True

# 检查并安装依赖
if not check_and_install_dependencies():
    sys.exit(1)

# 核心依赖
try:
    from torf import Torrent
    from pymediainfo import MediaInfo
    from tmdbv3api import TMDb, TV, Movie, Search
    import requests
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track
    from rich.panel import Panel
    from rich.prompt import Prompt
except ImportError as e:
    print(f"请安装依赖: pip install torf pymediainfo tmdbv3api requests click rich")
    exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
console = Console()

# ================= 数据模型 =================

class MediaType(str, Enum):
    TV_SHOW = "tv"
    MOVIE = "movie"
    DOCUMENTARY = "documentary"

class VideoCodec(str, Enum):
    H264 = "H.264"
    H265 = "H.265"
    XVID = "XviD"
    AV1 = "AV1"
    UNKNOWN = "Unknown"

class AudioCodec(str, Enum):
    AAC = "AAC"
    AC3 = "AC3"
    DTS = "DTS"
    MP3 = "MP3"
    FLAC = "FLAC"
    UNKNOWN = "Unknown"

class Resolution(str, Enum):
    SD_480P = "480p"
    HD_720P = "720p"
    FHD_1080P = "1080p"
    UHD_2160P = "2160p"
    UHD_4K = "4K"
    UNKNOWN = "Unknown"

@dataclass
class MediaInfo:
    file_path: Path
    file_size: int
    duration: Optional[float] = None
    resolution: Resolution = Resolution.UNKNOWN
    video_codec: VideoCodec = VideoCodec.UNKNOWN
    audio_codec: AudioCodec = AudioCodec.UNKNOWN
    bitrate: Optional[int] = None
    frame_rate: Optional[float] = None

@dataclass
class EpisodeInfo:
    season: int
    episode: int
    title: Optional[str] = None
    air_date: Optional[str] = None
    overview: Optional[str] = None

@dataclass
class SeriesInfo:
    title: str
    year: Optional[int] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    overview: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    network: Optional[str] = None
    status: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None

@dataclass
class MovieInfo:
    title: str
    year: Optional[int] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    overview: Optional[str] = None
    genres: List[str] = field(default_factory=list)
    director: Optional[str] = None
    runtime: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None

@dataclass
class MediaFile:
    media_info: MediaInfo
    media_type: MediaType
    series_info: Optional[SeriesInfo] = None
    movie_info: Optional[MovieInfo] = None
    episode_info: Optional[EpisodeInfo] = None
    subtitle_files: List[Path] = field(default_factory=list)

@dataclass
class Config:
    # Torrent 配置
    trackers: List[str] = field(default_factory=list)
    private: bool = True
    piece_size: Optional[int] = None
    comment: str = "Created with Media Packer"
    created_by: str = "Media Packer"
    
    # 命名配置
    tv_format: str = "{title} ({year}) S{season:02d}E{episode:02d} [{resolution}] [{codec}]"
    movie_format: str = "{title} ({year}) [{resolution}] [{codec}]"
    season_folder: str = "Season {season:02d}"
    include_year: bool = True
    include_resolution: bool = True
    include_codec: bool = True
    
    # API 配置
    tmdb_api_key: Optional[str] = None
    output_dir: Path = Path("./output")
    temp_dir: Path = Path("./temp")

# ================= 核心处理器 =================

class MediaProcessor:
    """媒体文件处理器"""
    
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub', '.vtt', '.idx', '.sup'}
    TV_PATTERNS = [
        r'S(\d{1,2})E(\d{1,2})',
        r'(\d{1,2})x(\d{1,2})',
        r'Season\s*(\d{1,2}).*Episode\s*(\d{1,2})',
    ]
    
    @classmethod
    def is_video_file(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in cls.VIDEO_EXTENSIONS
    
    @classmethod
    def is_subtitle_file(cls, file_path: Path) -> bool:
        return file_path.suffix.lower() in cls.SUBTITLE_EXTENSIONS
    
    @classmethod
    def extract_media_info(cls, file_path: Path) -> MediaInfo:
        """提取媒体文件技术信息"""
        if not cls.is_video_file(file_path):
            raise ValueError(f"Not a video file: {file_path}")
        
        media_info = MediaInfo.parse(str(file_path))
        video_track = next((track for track in media_info.tracks if track.track_type == 'Video'), None)
        audio_track = next((track for track in media_info.tracks if track.track_type == 'Audio'), None)
        
        # 判断分辨率
        resolution = Resolution.UNKNOWN
        if video_track and video_track.height:
            height = int(video_track.height)
            if height <= 480:
                resolution = Resolution.SD_480P
            elif height <= 720:
                resolution = Resolution.HD_720P
            elif height <= 1080:
                resolution = Resolution.FHD_1080P
            elif height <= 2160:
                resolution = Resolution.UHD_2160P
        
        # 判断视频编码
        video_codec = VideoCodec.UNKNOWN
        if video_track and video_track.codec:
            codec = video_track.codec.upper()
            if 'H264' in codec or 'AVC' in codec:
                video_codec = VideoCodec.H264
            elif 'H265' in codec or 'HEVC' in codec:
                video_codec = VideoCodec.H265
            elif 'XVID' in codec:
                video_codec = VideoCodec.XVID
            elif 'AV1' in codec:
                video_codec = VideoCodec.AV1
        
        # 判断音频编码
        audio_codec = AudioCodec.UNKNOWN
        if audio_track and audio_track.codec:
            codec = audio_track.codec.upper()
            if 'AAC' in codec:
                audio_codec = AudioCodec.AAC
            elif 'AC3' in codec or 'AC-3' in codec:
                audio_codec = AudioCodec.AC3
            elif 'DTS' in codec:
                audio_codec = AudioCodec.DTS
            elif 'MP3' in codec:
                audio_codec = AudioCodec.MP3
            elif 'FLAC' in codec:
                audio_codec = AudioCodec.FLAC
        
        return MediaInfo(
            file_path=file_path,
            file_size=file_path.stat().st_size,
            duration=float(video_track.duration) / 1000 if video_track and video_track.duration else None,
            resolution=resolution,
            video_codec=video_codec,
            audio_codec=audio_codec,
            bitrate=int(video_track.bit_rate) if video_track and video_track.bit_rate else None,
            frame_rate=float(video_track.frame_rate) if video_track and video_track.frame_rate else None
        )
    
    @classmethod
    def detect_media_type(cls, file_path: Path) -> MediaType:
        """检测媒体类型"""
        filename = file_path.name
        
        for pattern in cls.TV_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return MediaType.TV_SHOW
        
        doc_keywords = ['documentary', 'docuseries', 'docs']
        if any(keyword in filename.lower() for keyword in doc_keywords):
            return MediaType.DOCUMENTARY
        
        return MediaType.MOVIE
    
    @classmethod
    def extract_episode_info(cls, file_path: Path) -> Optional[EpisodeInfo]:
        """提取剧集信息"""
        filename = file_path.name
        
        for pattern in cls.TV_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                season = int(match.group(1))
                episode = int(match.group(2))
                return EpisodeInfo(season=season, episode=episode)
        
        return None
    
    @classmethod
    def find_subtitle_files(cls, video_path: Path) -> List[Path]:
        """查找字幕文件"""
        video_stem = video_path.stem
        video_dir = video_path.parent
        subtitle_files = []
        
        for ext in cls.SUBTITLE_EXTENSIONS:
            subtitle_path = video_dir / f"{video_stem}{ext}"
            if subtitle_path.exists():
                subtitle_files.append(subtitle_path)
        
        for file in video_dir.glob(f"{video_stem}.*"):
            if cls.is_subtitle_file(file):
                subtitle_files.append(file)
        
        return subtitle_files
    
    @classmethod
    def extract_title_and_year(cls, file_path: Path) -> Tuple[str, Optional[int]]:
        """提取标题和年份"""
        filename = file_path.stem
        
        for pattern in cls.TV_PATTERNS:
            filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
        
        year_match = re.search(r'\((\d{4})\)|\b(\d{4})\b', filename)
        year = None
        if year_match:
            year = int(year_match.group(1) or year_match.group(2))
            filename = re.sub(r'\(?\d{4}\)?', '', filename)
        
        title = re.sub(r'[._\-]+', ' ', filename).strip()
        title = re.sub(r'\s+', ' ', title)
        
        return title, year

class MetadataManager:
    """元数据管理器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.tmdb = TMDb()
        if api_key:
            self.tmdb.api_key = api_key
        self.tv = TV()
        self.movie = Movie()
        self.search = Search()
    
    def search_series(self, title: str, year: Optional[int] = None) -> List[SeriesInfo]:
        """搜索电视剧"""
        if not self.tmdb.api_key:
            logger.warning("TMDB API key not set")
            return []
        
        try:
            results = self.search.tv(query=title, first_air_date_year=year)
            series_list = []
            
            for result in results[:5]:
                series_info = SeriesInfo(
                    title=result.name,
                    year=int(result.first_air_date[:4]) if result.first_air_date else None,
                    tmdb_id=result.id,
                    overview=result.overview,
                    poster_path=result.poster_path,
                    backdrop_path=result.backdrop_path
                )
                series_list.append(series_info)
            
            return series_list
        except Exception as e:
            logger.error(f"Error searching for series '{title}': {e}")
            return []
    
    def search_movie(self, title: str, year: Optional[int] = None) -> List[MovieInfo]:
        """搜索电影"""
        if not self.tmdb.api_key:
            logger.warning("TMDB API key not set")
            return []
        
        try:
            results = self.search.movie(query=title, year=year)
            movie_list = []
            
            for result in results[:5]:
                movie_info = MovieInfo(
                    title=result.title,
                    year=int(result.release_date[:4]) if result.release_date else None,
                    tmdb_id=result.id,
                    overview=result.overview,
                    poster_path=result.poster_path,
                    backdrop_path=result.backdrop_path
                )
                movie_list.append(movie_info)
            
            return movie_list
        except Exception as e:
            logger.error(f"Error searching for movie '{title}': {e}")
            return []
    
    def get_series_details(self, tmdb_id: int) -> Optional[SeriesInfo]:
        """获取电视剧详细信息"""
        if not self.tmdb.api_key:
            return None
        
        try:
            details = self.tv.details(tmdb_id)
            
            return SeriesInfo(
                title=details.name,
                year=int(details.first_air_date[:4]) if details.first_air_date else None,
                tmdb_id=details.id,
                overview=details.overview,
                genres=[genre['name'] for genre in details.genres],
                network=details.networks[0]['name'] if details.networks else None,
                status=details.status,
                poster_path=details.poster_path,
                backdrop_path=details.backdrop_path
            )
        except Exception as e:
            logger.error(f"Error getting series details for ID {tmdb_id}: {e}")
            return None
    
    def get_movie_details(self, tmdb_id: int) -> Optional[MovieInfo]:
        """获取电影详细信息"""
        if not self.tmdb.api_key:
            return None
        
        try:
            details = self.movie.details(tmdb_id)
            
            director = None
            if hasattr(details, 'credits') and details.credits:
                crew = details.credits.get('crew', [])
                for person in crew:
                    if person.get('job') == 'Director':
                        director = person.get('name')
                        break
            
            return MovieInfo(
                title=details.title,
                year=int(details.release_date[:4]) if details.release_date else None,
                tmdb_id=details.id,
                imdb_id=details.imdb_id,
                overview=details.overview,
                genres=[genre['name'] for genre in details.genres],
                director=director,
                runtime=details.runtime,
                poster_path=details.poster_path,
                backdrop_path=details.backdrop_path
            )
        except Exception as e:
            logger.error(f"Error getting movie details for ID {tmdb_id}: {e}")
            return None

class FileNamer:
    """文件命名器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def generate_filename(self, media_file: MediaFile) -> str:
        """生成标准化文件名"""
        if media_file.media_type == MediaType.TV_SHOW:
            return self._generate_tv_filename(media_file)
        elif media_file.media_type == MediaType.MOVIE:
            return self._generate_movie_filename(media_file)
        else:
            return self._generate_generic_filename(media_file)
    
    def _generate_tv_filename(self, media_file: MediaFile) -> str:
        """生成电视剧文件名"""
        if not media_file.series_info or not media_file.episode_info:
            raise ValueError("Series and episode info required for TV shows")
        
        format_data = {
            'title': self._clean_title(media_file.series_info.title),
            'year': media_file.series_info.year or '',
            'season': media_file.episode_info.season,
            'episode': media_file.episode_info.episode,
            'resolution': self._format_resolution(media_file.media_info.resolution),
            'codec': self._format_codec(media_file.media_info.video_codec),
        }
        
        if not self.config.include_year or not format_data['year']:
            format_data['year'] = ''
        else:
            format_data['year'] = f" ({format_data['year']})"
        
        filename_template = self.config.tv_format
        if not self.config.include_resolution:
            filename_template = re.sub(r'\s*\[{resolution}\]', '', filename_template)
        if not self.config.include_codec:
            filename_template = re.sub(r'\s*\[{codec}\]', '', filename_template)
        
        filename = filename_template.format(**format_data)
        return self._clean_filename(filename)
    
    def _generate_movie_filename(self, media_file: MediaFile) -> str:
        """生成电影文件名"""
        if not media_file.movie_info:
            raise ValueError("Movie info required for movies")
        
        format_data = {
            'title': self._clean_title(media_file.movie_info.title),
            'year': media_file.movie_info.year or '',
            'resolution': self._format_resolution(media_file.media_info.resolution),
            'codec': self._format_codec(media_file.media_info.video_codec),
        }
        
        if not self.config.include_year or not format_data['year']:
            format_data['year'] = ''
        else:
            format_data['year'] = f" ({format_data['year']})"
        
        filename_template = self.config.movie_format
        if not self.config.include_resolution:
            filename_template = re.sub(r'\s*\[{resolution}\]', '', filename_template)
        if not self.config.include_codec:
            filename_template = re.sub(r'\s*\[{codec}\]', '', filename_template)
        
        filename = filename_template.format(**format_data)
        return self._clean_filename(filename)
    
    def _generate_generic_filename(self, media_file: MediaFile) -> str:
        """生成通用文件名"""
        original_name = media_file.media_info.file_path.stem
        return self._clean_filename(original_name)
    
    def generate_folder_structure(self, media_file: MediaFile) -> Path:
        """生成文件夹结构"""
        if media_file.media_type == MediaType.TV_SHOW:
            return self._generate_tv_folder_structure(media_file)
        elif media_file.media_type == MediaType.MOVIE:
            return self._generate_movie_folder_structure(media_file)
        else:
            return Path("Other")
    
    def _generate_tv_folder_structure(self, media_file: MediaFile) -> Path:
        """生成电视剧文件夹结构"""
        if not media_file.series_info or not media_file.episode_info:
            raise ValueError("Series and episode info required for TV shows")
        
        series_title = self._clean_title(media_file.series_info.title)
        year_part = f" ({media_file.series_info.year})" if media_file.series_info.year else ""
        resolution_part = f" [{self._format_resolution(media_file.media_info.resolution)}]" if self.config.include_resolution else ""
        codec_part = f" [{self._format_codec(media_file.media_info.video_codec)}]" if self.config.include_codec else ""
        
        series_folder = f"{series_title}{year_part}{resolution_part}{codec_part}"
        season_folder = self.config.season_folder.format(season=media_file.episode_info.season)
        
        return Path(series_folder) / season_folder
    
    def _generate_movie_folder_structure(self, media_file: MediaFile) -> Path:
        """生成电影文件夹结构"""
        if not media_file.movie_info:
            raise ValueError("Movie info required for movies")
        
        movie_title = self._clean_title(media_file.movie_info.title)
        year_part = f" ({media_file.movie_info.year})" if media_file.movie_info.year else ""
        resolution_part = f" [{self._format_resolution(media_file.media_info.resolution)}]" if self.config.include_resolution else ""
        codec_part = f" [{self._format_codec(media_file.media_info.video_codec)}]" if self.config.include_codec else ""
        
        movie_folder = f"{movie_title}{year_part}{resolution_part}{codec_part}"
        return Path(movie_folder)
    
    def _clean_title(self, title: str) -> str:
        """清理标题"""
        cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def _clean_filename(self, filename: str) -> str:
        """清理文件名"""
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip(' .')
        return cleaned
    
    def _format_resolution(self, resolution: Resolution) -> str:
        if resolution == Resolution.UNKNOWN:
            return "Unknown"
        return resolution.value
    
    def _format_codec(self, codec: VideoCodec) -> str:
        if codec == VideoCodec.UNKNOWN:
            return "Unknown"
        return codec.value

class TorrentCreator:
    """种子创建器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def create_torrent(self, content_path: Path, output_path: Optional[Path] = None, **kwargs) -> Torrent:
        """创建种子文件"""
        if not content_path.exists():
            raise FileNotFoundError(f"Content path does not exist: {content_path}")
        
        torrent_kwargs = {
            'path': str(content_path),
            'trackers': self.config.trackers,
            'private': self.config.private,
            'comment': self.config.comment,
            'created_by': self.config.created_by,
        }
        
        if self.config.piece_size:
            torrent_kwargs['piece_size'] = self.config.piece_size
        
        torrent_kwargs.update(kwargs)
        
        logger.info(f"Creating torrent for: {content_path}")
        torrent = Torrent(**torrent_kwargs)
        torrent.generate()
        
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torrent.write(str(output_path))
            logger.info(f"Torrent written to: {output_path}")
        
        return torrent
    
    def get_torrent_info(self, torrent_path: Path) -> Dict[str, Any]:
        """获取种子信息"""
        if not torrent_path.exists():
            raise FileNotFoundError(f"Torrent file not found: {torrent_path}")
        
        torrent = Torrent.read(str(torrent_path))
        
        return {
            'name': torrent.name,
            'size': torrent.size,
            'piece_count': torrent.piece_count,
            'piece_size': torrent.piece_size,
            'file_count': len(torrent.files),
            'trackers': torrent.trackers,
            'private': torrent.private,
            'comment': torrent.comment,
            'created_by': torrent.created_by,
            'creation_date': torrent.creation_date,
            'infohash': torrent.infohash,
            'magnet_uri': torrent.magnet()
        }

class FileOrganizer:
    """文件组织器"""
    
    def __init__(self, base_path: Path, namer: FileNamer):
        self.base_path = base_path
        self.namer = namer
    
    def organize_file(self, media_file: MediaFile, copy: bool = False) -> Path:
        """组织文件到标准结构"""
        folder_structure = self.namer.generate_folder_structure(media_file)
        filename = self.namer.generate_filename(media_file)
        
        original_ext = media_file.media_info.file_path.suffix
        full_filename = f"{filename}{original_ext}"
        
        target_path = self.base_path / folder_structure / full_filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if copy:
            shutil.copy2(media_file.media_info.file_path, target_path)
        else:
            media_file.media_info.file_path.rename(target_path)
        
        for subtitle_file in media_file.subtitle_files:
            subtitle_name = f"{filename}{subtitle_file.suffix}"
            subtitle_target = target_path.parent / subtitle_name
            
            if copy:
                shutil.copy2(subtitle_file, subtitle_target)
            else:
                subtitle_file.rename(subtitle_target)
        
        return target_path

class NFOGenerator:
    """NFO文件生成器"""
    
    @staticmethod
    def generate_movie_nfo(movie_info: MovieInfo) -> str:
        """生成电影NFO"""
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{movie_info.title}</title>
    <year>{movie_info.year or ''}</year>
    <plot>{movie_info.overview or ''}</plot>
    <runtime>{movie_info.runtime or ''}</runtime>
    <director>{movie_info.director or ''}</director>
    <tmdbid>{movie_info.tmdb_id or ''}</tmdbid>
    <imdbid>{movie_info.imdb_id or ''}</imdbid>
"""
        
        for genre in movie_info.genres:
            nfo_content += f"    <genre>{genre}</genre>\n"
        
        if movie_info.poster_path:
            nfo_content += f"    <thumb>https://image.tmdb.org/t/p/original{movie_info.poster_path}</thumb>\n"
        
        nfo_content += "</movie>"
        return nfo_content
    
    @staticmethod
    def generate_tvshow_nfo(series_info: SeriesInfo) -> str:
        """生成电视剧NFO"""
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
    <title>{series_info.title}</title>
    <year>{series_info.year or ''}</year>
    <plot>{series_info.overview or ''}</plot>
    <status>{series_info.status or ''}</status>
    <network>{series_info.network or ''}</network>
    <tmdbid>{series_info.tmdb_id or ''}</tmdbid>
"""
        
        for genre in series_info.genres:
            nfo_content += f"    <genre>{genre}</genre>\n"
        
        if series_info.poster_path:
            nfo_content += f"    <thumb>https://image.tmdb.org/t/p/original{series_info.poster_path}</thumb>\n"
        
        nfo_content += "</tvshow>"
        return nfo_content

# ================= 主要功能类 =================

class MediaPacker:
    """媒体打包器主类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.metadata_manager = MetadataManager(config.tmdb_api_key)
        self.file_namer = FileNamer(config)
        self.torrent_creator = TorrentCreator(config)
        self.file_organizer = FileOrganizer(config.output_dir, self.file_namer)
    
    def process_file(self, file_path: Path, organize: bool = True, fetch_metadata: bool = True, create_nfo: bool = False) -> Dict[str, Any]:
        """处理单个文件"""
        console.print(f"[cyan]处理文件: {file_path}[/cyan]")
        
        # 提取媒体信息
        media_info = MediaProcessor.extract_media_info(file_path)
        media_type = MediaProcessor.detect_media_type(file_path)
        
        # 查找字幕文件
        subtitle_files = MediaProcessor.find_subtitle_files(file_path)
        
        # 创建媒体文件对象
        media_file = MediaFile(
            media_info=media_info,
            media_type=media_type,
            subtitle_files=subtitle_files
        )
        
        # 提取标题和年份
        title, year = MediaProcessor.extract_title_and_year(file_path)
        
        # 获取元数据
        if fetch_metadata and self.config.tmdb_api_key:
            if media_type == MediaType.TV_SHOW:
                episode_info = MediaProcessor.extract_episode_info(file_path)
                if episode_info:
                    media_file.episode_info = episode_info
                
                series_results = self.metadata_manager.search_series(title, year)
                if series_results:
                    series_info = self.metadata_manager.get_series_details(series_results[0].tmdb_id)
                    media_file.series_info = series_info
            elif media_type == MediaType.MOVIE:
                movie_results = self.metadata_manager.search_movie(title, year)
                if movie_results:
                    movie_info = self.metadata_manager.get_movie_details(movie_results[0].tmdb_id)
                    media_file.movie_info = movie_info
        
        # 使用提取的信息作为后备
        if not media_file.series_info and media_type == MediaType.TV_SHOW:
            episode_info = MediaProcessor.extract_episode_info(file_path)
            if episode_info:
                media_file.episode_info = episode_info
                media_file.series_info = SeriesInfo(title=title, year=year)
        elif not media_file.movie_info and media_type == MediaType.MOVIE:
            media_file.movie_info = MovieInfo(title=title, year=year)
        
        # 组织文件
        organized_path = None
        if organize:
            try:
                organized_path = self.file_organizer.organize_file(media_file, copy=True)
                console.print(f"[green]文件已组织到: {organized_path}[/green]")
            except Exception as e:
                console.print(f"[red]文件组织失败: {e}[/red]")
                organized_path = file_path
        else:
            organized_path = file_path
        
        # 创建NFO文件
        if create_nfo:
            try:
                nfo_path = organized_path.with_suffix('.nfo')
                if media_type == MediaType.MOVIE and media_file.movie_info:
                    nfo_content = NFOGenerator.generate_movie_nfo(media_file.movie_info)
                    nfo_path.write_text(nfo_content, encoding='utf-8')
                    console.print(f"[green]NFO文件已创建: {nfo_path}[/green]")
                elif media_type == MediaType.TV_SHOW and media_file.series_info:
                    nfo_content = NFOGenerator.generate_tvshow_nfo(media_file.series_info)
                    nfo_path.write_text(nfo_content, encoding='utf-8')
                    console.print(f"[green]NFO文件已创建: {nfo_path}[/green]")
            except Exception as e:
                console.print(f"[red]NFO创建失败: {e}[/red]")
        
        return {
            'media_file': media_file,
            'organized_path': organized_path
        }
    
    def create_torrent_for_file(self, file_path: Path, custom_name: Optional[str] = None, **kwargs) -> Path:
        """为文件创建种子"""
        result = self.process_file(file_path, **kwargs)
        organized_path = result['organized_path']
        
        # 确定种子文件名和路径
        if custom_name:
            # 使用自定义名称（通常是文件夹名称）
            torrent_name = custom_name
            if organized_path.is_file():
                content_path = organized_path.parent
            else:
                content_path = organized_path
        else:
            # 使用默认逻辑
            if organized_path.is_file():
                torrent_name = organized_path.stem
                content_path = organized_path.parent
            else:
                torrent_name = organized_path.name
                content_path = organized_path
        
        torrent_path = self.config.output_dir / f"{torrent_name}.torrent"
        
        # 创建种子
        self.torrent_creator.create_torrent(content_path, torrent_path)
        console.print(f"[green]种子文件已创建: {torrent_path}[/green]")
        
        return torrent_path
    
    def batch_process(self, file_paths: List[Path], torrent_name: str) -> Path:
        """批量处理文件"""
        console.print(f"[cyan]批量处理 {len(file_paths)} 个文件[/cyan]")
        
        processed_paths = []
        for file_path in track(file_paths, description="处理文件..."):
            try:
                result = self.process_file(file_path)
                processed_paths.append(result['organized_path'])
            except Exception as e:
                console.print(f"[red]处理失败 {file_path}: {e}[/red]")
        
        # 创建批量种子
        if processed_paths:
            # 找到共同父目录
            common_parent = self._find_common_parent(processed_paths)
            torrent_path = self.config.output_dir / f"{torrent_name}.torrent"
            
            self.torrent_creator.create_torrent(common_parent, torrent_path)
            console.print(f"[green]批量种子已创建: {torrent_path}[/green]")
            
            return torrent_path
        
        raise ValueError("没有成功处理的文件")
    
    def _find_common_parent(self, paths: List[Path]) -> Path:
        """查找共同父目录"""
        if not paths:
            raise ValueError("路径列表为空")
        
        if len(paths) == 1:
            return paths[0].parent if paths[0].is_file() else paths[0]
        
        common_parts = None
        for path in paths:
            parts = path.parts
            if common_parts is None:
                common_parts = parts
            else:
                common_parts = tuple(
                    part for i, part in enumerate(common_parts)
                    if i < len(parts) and part == parts[i]
                )
        
        if common_parts:
            return Path(*common_parts)
        
        return Path.cwd()

# ================= 配置管理 =================

def load_config(config_path: Optional[Path] = None) -> Config:
    """加载配置"""
    config = Config()
    
    # 从配置文件加载
    if config_path and config_path.exists():
        try:
            with open(config_path) as f:
                data = json.load(f)
            
            # 更新配置
            for key, value in data.items():
                if key == 'torrent':
                    for tk, tv in value.items():
                        setattr(config, tk, tv)
                elif key == 'naming':
                    for nk, nv in value.items():
                        setattr(config, nk, nv)
                elif hasattr(config, key):
                    setattr(config, key, value)
        except Exception as e:
            console.print(f"[red]配置文件加载失败: {e}[/red]")
    
    # 从环境变量覆盖
    if os.getenv('TMDB_API_KEY'):
        config.tmdb_api_key = os.getenv('TMDB_API_KEY')
    
    if os.getenv('MP_OUTPUT_DIR'):
        config.output_dir = Path(os.getenv('MP_OUTPUT_DIR'))
    
    # 确保目录存在
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.temp_dir.mkdir(parents=True, exist_ok=True)
    
    return config

def save_default_config(config_path: Path):
    """保存默认配置"""
    default_config = {
        "torrent": {
            "trackers": [
                "https://tracker1.example.com/announce",
                "https://tracker2.example.com/announce"
            ],
            "private": True,
            "comment": "Created with Media Packer"
        },
        "naming": {
            "tv_format": "{title} ({year}) S{season:02d}E{episode:02d} [{resolution}] [{codec}]",
            "movie_format": "{title} ({year}) [{resolution}] [{codec}]"
        },
        "tmdb_api_key": "your_tmdb_api_key_here",
        "output_dir": "./output"
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    console.print(f"[green]默认配置已保存到: {config_path}[/green]")

# ================= 交互式界面 =================

class InteractiveMediaPacker:
    """终端交互式制种工具"""
    
    def __init__(self):
        self.console = Console()
        self.config: Optional[Config] = None
        self.media_directories: List[str] = []
        self.output_directory: str = ""
        self.trackers: List[str] = []
        self.task_queue: List[Dict] = []
        self.is_processing = False
        
        # 设置文件路径
        self.settings_file = Path.home() / ".media_packer" / "interactive_settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        
        # 内置tracker列表
        self.builtin_trackers = [
            "https://tracker1.example.com/announce",
            "https://tracker2.example.com/announce",
            "https://open.tracker.com/announce"
        ]
        
        self.load_settings()
    
    def run(self):
        """运行交互式界面"""
        try:
            self.show_welcome()
            os.system('clear' if os.name == 'posix' else 'cls')
        except Exception:
            pass  # 清屏失败也继续运行
        
        while True:
            try:
                self.show_main_menu()
                choice = Prompt.ask(
                    "请选择操作",
                    choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                    default="9" if not self.media_directories or not self.output_directory else "1"
                )
                
                if choice == "1":
                    self.manage_media_directories()
                elif choice == "2":
                    self.setup_output_directory()
                elif choice == "3":
                    self.manage_trackers()
                elif choice == "4":
                    self.scan_and_queue_files()
                elif choice == "5":
                    self.manage_queue()
                elif choice == "6":
                    self.start_processing()
                elif choice == "7":
                    self.view_settings()
                elif choice == "8":
                    self.save_settings()
                elif choice == "9":
                    self.quick_setup_wizard()
                elif choice == "0":
                    self.exit_application()
                    break
                
                self.console.print("\n" + "="*60 + "\n")
                
            except KeyboardInterrupt:
                self.console.print("\n")
                if Prompt.ask("确定要退出吗？", choices=["y", "n"], default="n") == "y":
                    self.exit_application()
                    break
                else:
                    self.console.print("[green]继续运行...[/green]")
            except Exception as e:
                self.console.print(f"[red]发生错误: {e}[/red]")
                self.console.print("[yellow]程序将继续运行，请检查错误信息[/yellow]")
                input("按回车键继续...")
    
    def show_welcome(self):
        """显示欢迎界面"""
        welcome_panel = Panel.fit(
            "[bold blue]Media Packer - 终端交互式制种工具[/bold blue]\n"
            "[dim]基于 torf 的专业影视制种解决方案[/dim]\n\n"
            "[green]功能特性:[/green]\n"
            "• 智能媒体文件识别和处理\n"
            "• 标准化文件命名和组织\n"
            "• TMDB 元数据自动获取\n"
            "• 批量处理和制种队列\n"
            "• 交互式操作界面\n\n"
            "[yellow]提示:[/yellow] 可使用 Ctrl+C 随时退出",
            title="欢迎使用 Media Packer",
            border_style="blue"
        )
        self.console.print(welcome_panel)
        self.console.print("\n[dim]按回车键开始配置和使用...[/dim]")
        input()
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_main_menu(self):
        """显示主菜单"""
        menu_table = Table(title="[bold]主菜单[/bold]", show_header=False, box=None)
        menu_table.add_column("选项", style="cyan", width=8)
        menu_table.add_column("功能", style="white")
        menu_table.add_column("状态", style="dim", width=15)
        
        # 检查各功能状态
        media_status = f"[green]{len(self.media_directories)} 个目录[/green]" if self.media_directories else "[red]未设置[/red]"
        output_status = "[green]已设置[/green]" if self.output_directory else "[red]未设置[/red]"
        tracker_status = f"[green]{len(self.trackers)} 个[/green]" if self.trackers else "[red]未设置[/red]"
        queue_status = f"[yellow]{len(self.task_queue)} 个任务[/yellow]" if self.task_queue else "[dim]空[/dim]"
        
        menu_table.add_row("1", "媒体目录管理", media_status)
        menu_table.add_row("2", "设置输出目录", output_status)
        menu_table.add_row("3", "Tracker 配置", tracker_status)
        menu_table.add_row("4", "扫描文件并加入队列", "")
        menu_table.add_row("5", "队列管理", queue_status)
        menu_table.add_row("6", "开始批量处理", "")
        menu_table.add_row("7", "查看当前设置", "")
        menu_table.add_row("8", "保存设置", "")
        menu_table.add_row("9", "快速配置向导", "[cyan]推荐[/cyan]")
        menu_table.add_row("0", "退出程序", "")
        
        self.console.print(menu_table)
    
    def manage_media_directories(self):
        """管理媒体目录"""
        while True:
            self.console.print("\n[bold]媒体目录管理[/bold]")
            
            if self.media_directories:
                dir_table = Table(title="当前媒体目录", show_header=True)
                dir_table.add_column("序号", style="cyan", width=6)
                dir_table.add_column("路径", style="white")
                dir_table.add_column("状态", style="green")
                
                for i, directory in enumerate(self.media_directories, 1):
                    status = "存在" if Path(directory).exists() else "[red]不存在[/red]"
                    dir_table.add_row(str(i), directory, status)
                
                self.console.print(dir_table)
            else:
                self.console.print("[yellow]暂无媒体目录[/yellow]")
            
            self.console.print("\n操作选项:")
            self.console.print("1. 添加目录")
            self.console.print("2. 删除目录")
            self.console.print("3. 返回主菜单")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3"], default="3")
            
            if choice == "1":
                self.add_media_directory()
            elif choice == "2":
                self.remove_media_directory()
            elif choice == "3":
                break
    
    def add_media_directory(self):
        """添加媒体目录"""
        directory = Prompt.ask("请输入媒体目录路径")
        
        if not directory.strip():
            self.console.print("[red]路径不能为空[/red]")
            return
        
        directory_path = Path(directory.strip())
        
        if not directory_path.exists():
            if Prompt.ask(f"目录 {directory} 不存在，是否仍要添加？", choices=["y", "n"], default="n") == "n":
                return
        
        if directory in self.media_directories:
            self.console.print("[yellow]该目录已存在[/yellow]")
            return
        
        self.media_directories.append(directory)
        self.console.print(f"[green]已添加目录: {directory}[/green]")
    
    def remove_media_directory(self):
        """删除媒体目录"""
        if not self.media_directories:
            self.console.print("[yellow]暂无可删除的目录[/yellow]")
            return
        
        try:
            index = int(Prompt.ask("请输入要删除的目录序号")) - 1
            if 0 <= index < len(self.media_directories):
                removed_dir = self.media_directories.pop(index)
                self.console.print(f"[green]已删除目录: {removed_dir}[/green]")
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def setup_output_directory(self):
        """设置输出目录"""
        self.console.print("\n[bold]输出目录设置[/bold]")
        
        if self.output_directory:
            self.console.print(f"当前输出目录: [green]{self.output_directory}[/green]")
        
        directory = Prompt.ask("请输入种子输出目录路径", default=self.output_directory)
        
        if not directory.strip():
            self.console.print("[red]路径不能为空[/red]")
            return
        
        directory_path = Path(directory.strip())
        
        # 尝试创建目录
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            self.output_directory = str(directory_path)
            self.console.print(f"[green]输出目录已设置为: {self.output_directory}[/green]")
        except Exception as e:
            self.console.print(f"[red]无法创建目录: {e}[/red]")
    
    def manage_trackers(self):
        """管理Tracker"""
        while True:
            self.console.print("\n[bold]Tracker 配置[/bold]")
            
            # 显示当前trackers
            if self.trackers:
                tracker_table = Table(title="当前 Tracker 列表", show_header=True)
                tracker_table.add_column("序号", style="cyan", width=6)
                tracker_table.add_column("URL", style="white")
                
                for i, tracker in enumerate(self.trackers, 1):
                    tracker_table.add_row(str(i), tracker)
                
                self.console.print(tracker_table)
            else:
                self.console.print("[yellow]暂无 Tracker[/yellow]")
            
            self.console.print("\n操作选项:")
            self.console.print("1. 添加 Tracker")
            self.console.print("2. 删除 Tracker")
            self.console.print("3. 使用内置 Tracker")
            self.console.print("4. 清空所有 Tracker")
            self.console.print("5. 返回主菜单")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3", "4", "5"], default="5")
            
            if choice == "1":
                self.add_tracker()
            elif choice == "2":
                self.remove_tracker()
            elif choice == "3":
                self.use_builtin_trackers()
            elif choice == "4":
                if Prompt.ask("确定要清空所有 Tracker 吗？", choices=["y", "n"], default="n") == "y":
                    self.trackers.clear()
                    self.console.print("[green]已清空所有 Tracker[/green]")
            elif choice == "5":
                break
    
    def add_tracker(self):
        """添加Tracker"""
        tracker = Prompt.ask("请输入 Tracker URL")
        
        if not tracker.strip():
            self.console.print("[red]URL 不能为空[/red]")
            return
        
        if not tracker.startswith(('http://', 'https://', 'udp://')):
            self.console.print("[red]请输入有效的 URL[/red]")
            return
        
        if tracker in self.trackers:
            self.console.print("[yellow]该 Tracker 已存在[/yellow]")
            return
        
        self.trackers.append(tracker)
        self.console.print(f"[green]已添加 Tracker: {tracker}[/green]")
    
    def remove_tracker(self):
        """删除Tracker"""
        if not self.trackers:
            self.console.print("[yellow]暂无可删除的 Tracker[/yellow]")
            return
        
        try:
            index = int(Prompt.ask("请输入要删除的 Tracker 序号")) - 1
            if 0 <= index < len(self.trackers):
                removed_tracker = self.trackers.pop(index)
                self.console.print(f"[green]已删除 Tracker: {removed_tracker}[/green]")
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def use_builtin_trackers(self):
        """使用内置Tracker"""
        self.console.print("\n[bold]内置 Tracker 列表:[/bold]")
        for i, tracker in enumerate(self.builtin_trackers, 1):
            self.console.print(f"{i}. {tracker}")
        
        if Prompt.ask("是否添加所有内置 Tracker？", choices=["y", "n"], default="y") == "y":
            for tracker in self.builtin_trackers:
                if tracker not in self.trackers:
                    self.trackers.append(tracker)
            self.console.print(f"[green]已添加 {len(self.builtin_trackers)} 个内置 Tracker[/green]")
    
    def scan_and_queue_files(self):
        """扫描文件并加入队列"""
        if not self.media_directories:
            self.console.print("[red]请先设置媒体目录[/red]")
            return
        
        self.console.print("\n[bold]扫描媒体文件...[/bold]")
        
        total_files = 0
        video_files = []
        
        with console.status("[bold green]扫描中...") as status:
            for directory in self.media_directories:
                status.update(f"扫描: {Path(directory).name}")
                dir_path = Path(directory)
                
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and MediaProcessor.is_video_file(file_path):
                            video_files.append(str(file_path.absolute()))
                            total_files += 1
        
        if total_files == 0:
            self.console.print("[yellow]未发现视频文件[/yellow]")
            return
        
        # 显示发现的文件
        self.console.print(f"\n[green]发现 {total_files} 个视频文件[/green]")
        
        if total_files <= 10:
            # 文件数量少时显示列表
            file_table = Table(title="发现的视频文件", show_header=True)
            file_table.add_column("文件名", style="white")
            file_table.add_column("大小", style="cyan")
            
            for file_path in video_files:
                path = Path(file_path)
                size = self.format_file_size(path.stat().st_size)
                file_table.add_row(path.name, size)
            
            self.console.print(file_table)
        
        if Prompt.ask("是否将这些文件加入处理队列？", choices=["y", "n"], default="y") == "y":
            for file_path in video_files:
                task = {
                    'id': f"task_{len(self.task_queue) + 1}",
                    'file_path': file_path,
                    'status': 'pending',
                    'created_at': time.time(),
                    'completed_at': None,
                    'error_message': None
                }
                self.task_queue.append(task)
            
            self.console.print(f"[green]已将 {len(video_files)} 个文件加入队列[/green]")
    
    def manage_queue(self):
        """队列管理"""
        if not self.task_queue:
            self.console.print("[yellow]队列为空，请先扫描文件[/yellow]")
            return
        
        while True:
            self.console.print("\n[bold]制种队列管理[/bold]")
            
            # 显示队列统计
            pending_tasks = [t for t in self.task_queue if t['status'] == 'pending']
            completed_tasks = [t for t in self.task_queue if t['status'] == 'completed']
            error_tasks = [t for t in self.task_queue if t['status'] == 'error']
            
            stats_table = Table(title="队列统计", show_header=True)
            stats_table.add_column("状态", style="cyan")
            stats_table.add_column("数量", style="white")
            
            stats_table.add_row("总数", str(len(self.task_queue)))
            stats_table.add_row("待处理", str(len(pending_tasks)))
            stats_table.add_row("已完成", str(len(completed_tasks)))
            stats_table.add_row("错误", str(len(error_tasks)))
            
            self.console.print(stats_table)
            
            # 显示任务列表
            if self.task_queue:
                task_table = Table(title="任务列表", show_header=True, max_rows=10)
                task_table.add_column("ID", style="dim", width=10)
                task_table.add_column("文件名", style="white", max_width=40)
                task_table.add_column("状态", style="cyan")
                task_table.add_column("创建时间", style="dim")
                
                for task in self.task_queue[:10]:  # 只显示前10个
                    filename = Path(task['file_path']).name
                    if len(filename) > 40:
                        filename = filename[:37] + "..."
                    
                    task_table.add_row(
                        task['id'],
                        filename,
                        task['status'],
                        time.strftime("%H:%M:%S", time.localtime(task['created_at']))
                    )
                
                self.console.print(task_table)
                
                if len(self.task_queue) > 10:
                    self.console.print(f"[dim]... 还有 {len(self.task_queue) - 10} 个任务[/dim]")
            
            self.console.print("\n操作选项:")
            self.console.print("1. 清空队列")
            self.console.print("2. 返回主菜单")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2"], default="2")
            
            if choice == "1":
                if Prompt.ask("确定要清空队列吗？", choices=["y", "n"], default="n") == "y":
                    self.task_queue.clear()
                    self.console.print("[green]队列已清空[/green]")
                    break
            elif choice == "2":
                break
    
    def start_processing(self):
        """开始批量处理"""
        if not self.task_queue:
            self.console.print("[red]队列为空，请先扫描文件[/red]")
            return
        
        if not self.output_directory:
            self.console.print("[red]请先设置输出目录[/red]")
            return
        
        if not self.trackers:
            self.console.print("[red]请先设置 Tracker[/red]")
            return
        
        pending_tasks = [t for t in self.task_queue if t['status'] == 'pending']
        if not pending_tasks:
            self.console.print("[yellow]没有待处理的任务[/yellow]")
            return
        
        self.console.print(f"\n[bold]开始处理 {len(pending_tasks)} 个任务...[/bold]")
        
        # 创建配置
        config = Config(
            trackers=self.trackers,
            output_dir=Path(self.output_directory)
        )
        
        packer = MediaPacker(config)
        
        # 处理任务
        for task in pending_tasks:
            try:
                task['status'] = 'processing'
                self.console.print(f"[cyan]处理: {Path(task['file_path']).name}[/cyan]")
                
                # 处理文件
                result = packer.process_file(
                    Path(task['file_path']),
                    organize=True,
                    fetch_metadata=bool(config.tmdb_api_key),
                    create_nfo=False
                )
                
                # 创建种子 - 使用文件夹名称作为种子名称
                file_path = Path(task['file_path'])
                
                # 获取文件夹名称
                if file_path.is_file():
                    folder_name = file_path.parent.name
                else:
                    folder_name = file_path.name
                
                self.console.print(f"[cyan]种子文件名将使用: {folder_name}[/cyan]")
                
                # 使用更新后的方法创建种子
                torrent_path = packer.create_torrent_for_file(
                    file_path,
                    custom_name=folder_name
                )
                
                task['status'] = 'completed'
                task['completed_at'] = time.time()
                
                self.console.print(f"[green]完成: {torrent_path.name}[/green]")
                
            except Exception as e:
                task['status'] = 'error'
                task['error_message'] = str(e)
                self.console.print(f"[red]错误: {e}[/red]")
        
        completed_count = len([t for t in self.task_queue if t['status'] == 'completed'])
        error_count = len([t for t in self.task_queue if t['status'] == 'error'])
        
        result_panel = Panel(
            f"[green]处理完成![/green]\n\n"
            f"成功: {completed_count} 个\n"
            f"失败: {error_count} 个\n",
            title="处理结果",
            border_style="green"
        )
        self.console.print(result_panel)
        
        input("按回车键继续...")
    
    def quick_setup_wizard(self):
        """快速配置向导"""
        self.console.print("\n[bold blue]快速配置向导[/bold blue]")
        self.console.print("[dim]帮助您快速完成基本设置[/dim]\n")
        
        # 步骤1：设置媒体目录
        if not self.media_directories:
            self.console.print("[yellow]步骤 1/3: 设置媒体目录[/yellow]")
            self.console.print("请输入存放视频文件的目录路径（可输入多个，每次输入一个）")
            
            while True:
                directory = Prompt.ask("媒体目录路径（留空结束）", default="")
                if not directory.strip():
                    break
                
                directory_path = Path(directory.strip())
                if directory_path.exists() or Prompt.ask(f"目录 {directory} 不存在，是否仍要添加？", choices=["y", "n"], default="y") == "y":
                    if directory not in self.media_directories:
                        self.media_directories.append(directory)
                        self.console.print(f"[green]✓ 已添加: {directory}[/green]")
                    else:
                        self.console.print("[yellow]该目录已存在[/yellow]")
                
                if len(self.media_directories) > 0 and Prompt.ask("是否继续添加目录？", choices=["y", "n"], default="n") == "n":
                    break
        else:
            self.console.print("[green]✓ 媒体目录已配置[/green]")
        
        # 步骤2：设置输出目录
        if not self.output_directory:
            self.console.print("\n[yellow]步骤 2/3: 设置输出目录[/yellow]")
            default_output = str(Path.home() / "MediaPacker_Output")
            directory = Prompt.ask("种子文件输出目录", default=default_output)
            
            try:
                directory_path = Path(directory)
                directory_path.mkdir(parents=True, exist_ok=True)
                self.output_directory = str(directory_path)
                self.console.print(f"[green]✓ 输出目录已设置: {self.output_directory}[/green]")
            except Exception as e:
                self.console.print(f"[red]设置输出目录失败: {e}[/red]")
        else:
            self.console.print("[green]✓ 输出目录已配置[/green]")
        
        # 步骤3：设置Tracker
        if not self.trackers:
            self.console.print("\n[yellow]步骤 3/3: 设置 Tracker[/yellow]")
            if Prompt.ask("是否使用内置的示例 Tracker？", choices=["y", "n"], default="y") == "y":
                self.trackers.extend(self.builtin_trackers)
                self.console.print(f"[green]✓ 已添加 {len(self.builtin_trackers)} 个内置 Tracker[/green]")
            else:
                self.console.print("请手动添加 Tracker（至少添加一个）")
                while len(self.trackers) == 0:
                    tracker = Prompt.ask("Tracker URL")
                    if tracker.strip() and tracker.startswith(('http://', 'https://', 'udp://')):
                        self.trackers.append(tracker)
                        self.console.print(f"[green]✓ 已添加 Tracker[/green]")
                    else:
                        self.console.print("[red]请输入有效的 URL[/red]")
        else:
            self.console.print("[green]✓ Tracker 已配置[/green]")
        
        # 完成配置
        self.console.print("\n[bold green]✓ 快速配置完成！[/bold green]")
        self.save_settings()
        
        setup_panel = Panel(
            f"[green]配置摘要:[/green]\n"
            f"媒体目录: {len(self.media_directories)} 个\n"
            f"输出目录: {self.output_directory}\n"
            f"Tracker: {len(self.trackers)} 个\n\n"
            f"[yellow]下一步:[/yellow] 选择选项4扫描文件，然后选择选项6开始处理",
            title="配置完成",
            border_style="green"
        )
        self.console.print(setup_panel)
        input("\n按回车键返回主菜单...")

    def view_settings(self):
        """查看当前设置"""
        settings_panel = Panel(
            f"[bold]媒体目录:[/bold] {len(self.media_directories)} 个\n"
            + "\n".join([f"  • {d}" for d in self.media_directories[:5]]) + 
            (f"\n  ... 还有 {len(self.media_directories) - 5} 个" if len(self.media_directories) > 5 else "") +
            f"\n\n[bold]输出目录:[/bold] {self.output_directory or '未设置'}\n"
            f"\n[bold]Trackers:[/bold] {len(self.trackers)} 个\n"
            + "\n".join([f"  • {t}" for t in self.trackers[:3]]) +
            (f"\n  ... 还有 {len(self.trackers) - 3} 个" if len(self.trackers) > 3 else ""),
            title="当前设置",
            border_style="cyan"
        )
        self.console.print(settings_panel)
        input("\n按回车键返回...")
    
    def save_settings(self):
        """保存设置"""
        settings = {
            "media_directories": self.media_directories,
            "output_directory": self.output_directory,
            "trackers": self.trackers
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.console.print(f"[green]设置已保存到: {self.settings_file}[/green]")
        except Exception as e:
            self.console.print(f"[red]保存设置失败: {e}[/red]")
    
    def load_settings(self):
        """加载设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.media_directories = settings.get("media_directories", [])
                self.output_directory = settings.get("output_directory", "")
                self.trackers = settings.get("trackers", [])
        except Exception:
            pass  # 忽略加载错误，使用默认设置
    
    def exit_application(self):
        """退出应用"""
        self.console.print("\n[bold blue]感谢使用 Media Packer![/bold blue]")
        self.console.print("[dim]提示: 可以使用以下命令行模式:[/dim]")
        self.console.print("[dim]  python media_packer_all_in_one.py pack <文件路径>[/dim]")
        self.console.print("[dim]  python media_packer_all_in_one.py batch <文件1> <文件2> --name <种子名>[/dim]")
        self.console.print("[dim]  python media_packer_all_in_one.py --help[/dim]")
        # 自动保存设置
        self.save_settings()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

# ================= 命令行接口 =================

@click.group()
@click.option('--config', '-c', type=click.Path(), help='配置文件路径')
@click.pass_context
def cli(ctx, config):
    """Media Packer - 影视剧打包制种工具"""
    ctx.ensure_object(dict)
    
    config_path = Path(config) if config else None
    ctx.obj['config'] = load_config(config_path)
    ctx.obj['packer'] = MediaPacker(ctx.obj['config'])

@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--organize', is_flag=True, help='组织文件结构')
@click.option('--fetch-metadata', is_flag=True, help='获取元数据')
@click.option('--create-nfo', is_flag=True, help='创建NFO文件')
@click.option('--name', '-n', help='种子名称（默认使用文件夹名称）')
@click.pass_context
def pack(ctx, input_path, output, organize, fetch_metadata, create_nfo, name):
    """打包文件"""
    packer = ctx.obj['packer']
    
    if output:
        packer.config.output_dir = Path(output)
        packer.file_organizer.base_path = Path(output)
    
    try:
        input_file = Path(input_path)
        
        # 如果没有指定名称，使用文件夹名称
        if not name:
            if input_file.is_file():
                name = input_file.parent.name
            else:
                name = input_file.name
        
        console.print(f"[cyan]种子文件名将使用: {name}[/cyan]")
        
        torrent_path = packer.create_torrent_for_file(
            input_file,
            custom_name=name,
            organize=organize,
            fetch_metadata=fetch_metadata,
            create_nfo=create_nfo
        )
        console.print(f"[bold green]成功创建种子: {torrent_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('input_paths', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--name', '-n', required=True, help='种子名称')
@click.pass_context
def batch(ctx, input_paths, output, name):
    """批量制种"""
    packer = ctx.obj['packer']
    
    if output:
        packer.config.output_dir = Path(output)
        packer.file_organizer.base_path = Path(output)
    
    try:
        file_paths = [Path(p) for p in input_paths]
        torrent_path = packer.batch_process(file_paths, name)
        console.print(f"[bold green]成功创建批量种子: {torrent_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('query')
@click.option('--type', 'media_type', type=click.Choice(['tv', 'movie']), default='tv', help='媒体类型')
@click.option('--year', type=int, help='发布年份')
@click.pass_context
def search(ctx, query, media_type, year):
    """搜索元数据"""
    packer = ctx.obj['packer']
    
    if not packer.config.tmdb_api_key:
        console.print("[red]需要设置TMDB API密钥[/red]")
        return
    
    try:
        if media_type == 'tv':
            results = packer.metadata_manager.search_series(query, year)
            table = Table(title="电视剧搜索结果")
            table.add_column("标题", style="cyan")
            table.add_column("年份", style="green")
            table.add_column("TMDB ID", style="yellow")
            
            for result in results:
                table.add_row(
                    result.title,
                    str(result.year) if result.year else "未知",
                    str(result.tmdb_id)
                )
        else:
            results = packer.metadata_manager.search_movie(query, year)
            table = Table(title="电影搜索结果")
            table.add_column("标题", style="cyan")
            table.add_column("年份", style="green")
            table.add_column("TMDB ID", style="yellow")
            
            for result in results:
                table.add_row(
                    result.title,
                    str(result.year) if result.year else "未知",
                    str(result.tmdb_id)
                )
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]搜索失败: {e}[/red]")

@cli.command()
@click.argument('torrent_path', type=click.Path(exists=True))
def info(torrent_path):
    """显示种子信息"""
    try:
        config = load_config()
        creator = TorrentCreator(config)
        info_data = creator.get_torrent_info(Path(torrent_path))
        
        table = Table(title="种子信息")
        table.add_column("属性", style="cyan")
        table.add_column("值", style="green")
        
        for key, value in info_data.items():
            if key == 'size':
                value = f"{value / (1024**3):.2f} GB"
            elif key == 'trackers':
                value = '\n'.join(value) if isinstance(value, list) else str(value)
            
            table.add_row(key, str(value))
        
        console.print(table)
    except Exception as e:
        console.print(f"[red]读取种子信息失败: {e}[/red]")

@cli.command()
@click.option('--path', type=click.Path(), default='config.json', help='配置文件路径')
def init_config(path):
    """初始化配置文件"""
    config_path = Path(path)
    if config_path.exists():
        if not click.confirm(f"配置文件 {config_path} 已存在，是否覆盖？"):
            return
    
    save_default_config(config_path)

@cli.command()
def interactive():
    """启动交互式界面"""
    try:
        app = InteractiveMediaPacker()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]程序被用户中断[/yellow]")
    except Exception as e:
        console.print(f"[red]启动交互界面失败: {e}[/red]")

if __name__ == '__main__':
    import sys
    
    # 如果没有命令行参数，默认启动交互界面
    if len(sys.argv) == 1:
        try:
            console.print("[green]启动 Media Packer 交互式界面...[/green]")
            console.print("[dim]提示: 使用 'python media_packer_all_in_one.py --help' 查看命令行模式[/dim]\n")
            app = InteractiveMediaPacker()
            app.run()
        except KeyboardInterrupt:
            console.print("\n[yellow]程序被用户中断[/yellow]")
        except ImportError as e:
            console.print(f"[red]缺少依赖: {e}[/red]")
            console.print("[yellow]请运行: pip install torf pymediainfo tmdbv3api requests click rich[/yellow]")
        except Exception as e:
            console.print(f"[red]启动交互界面失败: {e}[/red]")
            console.print("[yellow]尝试使用命令行模式: python media_packer_all_in_one.py --help[/yellow]")
    else:
        # 有命令行参数时运行CLI
        try:
            cli()
        except ImportError as e:
            console.print(f"[red]缺少依赖: {e}[/red]")
            console.print("[yellow]请运行: pip install torf pymediainfo tmdbv3api requests click rich[/yellow]")
        except Exception as e:
            console.print(f"[red]运行失败: {e}[/red]")