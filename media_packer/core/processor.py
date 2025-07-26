"""Media file processing utilities"""
import re
from pathlib import Path
from typing import Optional, Tuple, List
from pymediainfo import MediaInfo
from ..models import (
    MediaInfo as MediaInfoModel, 
    VideoCodec, 
    AudioCodec, 
    Resolution,
    MediaType,
    EpisodeInfo
)


class MediaProcessor:
    """Processes media files and extracts information"""
    
    # Video file extensions
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    # Subtitle file extensions  
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub', '.vtt', '.idx', '.sup'}
    
    # Common TV show patterns
    TV_PATTERNS = [
        r'S(\d{1,2})E(\d{1,2})',  # S01E01
        r'(\d{1,2})x(\d{1,2})',   # 1x01
        r'Season\s*(\d{1,2}).*Episode\s*(\d{1,2})', # Season 1 Episode 1
    ]
    
    @classmethod
    def is_video_file(cls, file_path: Path) -> bool:
        """Check if file is a video file"""
        return file_path.suffix.lower() in cls.VIDEO_EXTENSIONS
    
    @classmethod
    def is_subtitle_file(cls, file_path: Path) -> bool:
        """Check if file is a subtitle file"""
        return file_path.suffix.lower() in cls.SUBTITLE_EXTENSIONS
    
    @classmethod
    def extract_media_info(cls, file_path: Path) -> MediaInfoModel:
        """Extract technical information from media file"""
        if not cls.is_video_file(file_path):
            raise ValueError(f"Not a video file: {file_path}")
        
        media_info = MediaInfo.parse(str(file_path))
        
        # Extract video track info
        video_track = next((track for track in media_info.tracks if track.track_type == 'Video'), None)
        audio_track = next((track for track in media_info.tracks if track.track_type == 'Audio'), None)
        
        # Determine resolution
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
        
        # Determine video codec
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
        
        # Determine audio codec
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
        
        return MediaInfoModel(
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
        """Detect if file is TV show or movie based on filename patterns"""
        filename = file_path.name
        
        # Check for TV show patterns
        for pattern in cls.TV_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return MediaType.TV_SHOW
        
        # Check for documentary keywords
        doc_keywords = ['documentary', 'docuseries', 'docs']
        if any(keyword in filename.lower() for keyword in doc_keywords):
            return MediaType.DOCUMENTARY
        
        # Default to movie
        return MediaType.MOVIE
    
    @classmethod
    def extract_episode_info(cls, file_path: Path) -> Optional[EpisodeInfo]:
        """Extract season and episode information from filename"""
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
        """Find subtitle files for a video file"""
        video_stem = video_path.stem
        video_dir = video_path.parent
        subtitle_files = []
        
        # Look for subtitles with same base name
        for ext in cls.SUBTITLE_EXTENSIONS:
            subtitle_path = video_dir / f"{video_stem}{ext}"
            if subtitle_path.exists():
                subtitle_files.append(subtitle_path)
        
        # Look for subtitles with language codes
        for file in video_dir.glob(f"{video_stem}.*"):
            if cls.is_subtitle_file(file):
                subtitle_files.append(file)
        
        return subtitle_files
    
    @classmethod
    def extract_title_and_year(cls, file_path: Path) -> Tuple[str, Optional[int]]:
        """Extract title and year from filename"""
        filename = file_path.stem
        
        # Remove episode information for TV shows
        for pattern in cls.TV_PATTERNS:
            filename = re.sub(pattern, '', filename, flags=re.IGNORECASE)
        
        # Extract year
        year_match = re.search(r'\((\d{4})\)|\b(\d{4})\b', filename)
        year = None
        if year_match:
            year = int(year_match.group(1) or year_match.group(2))
            # Remove year from title
            filename = re.sub(r'\(?\d{4}\)?', '', filename)
        
        # Clean up title
        title = re.sub(r'[._\-]+', ' ', filename).strip()
        title = re.sub(r'\s+', ' ', title)  # Normalize spaces
        
        return title, year