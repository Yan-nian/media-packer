"""File naming and organization utilities"""
import re
from pathlib import Path
from typing import Dict, Any, Optional
from ..models import MediaFile, MediaType, Resolution, VideoCodec
from ..config import NamingConfig


class FileNamer:
    """Handles file naming and organization according to standards"""
    
    def __init__(self, config: NamingConfig):
        self.config = config
    
    def generate_filename(self, media_file: MediaFile) -> str:
        """Generate standardized filename for media file"""
        if media_file.media_type == MediaType.TV_SHOW:
            return self._generate_tv_filename(media_file)
        elif media_file.media_type == MediaType.MOVIE:
            return self._generate_movie_filename(media_file)
        else:
            return self._generate_generic_filename(media_file)
    
    def _generate_tv_filename(self, media_file: MediaFile) -> str:
        """Generate TV show filename"""
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
        
        # Handle optional year
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
        """Generate movie filename"""
        if not media_file.movie_info:
            raise ValueError("Movie info required for movies")
        
        format_data = {
            'title': self._clean_title(media_file.movie_info.title),
            'year': media_file.movie_info.year or '',
            'resolution': self._format_resolution(media_file.media_info.resolution),
            'codec': self._format_codec(media_file.media_info.video_codec),
        }
        
        # Handle optional year
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
        """Generate generic filename for other media types"""
        original_name = media_file.media_info.file_path.stem
        return self._clean_filename(original_name)
    
    def generate_folder_structure(self, media_file: MediaFile) -> Path:
        """Generate folder structure for media file"""
        if media_file.media_type == MediaType.TV_SHOW:
            return self._generate_tv_folder_structure(media_file)
        elif media_file.media_type == MediaType.MOVIE:
            return self._generate_movie_folder_structure(media_file)
        else:
            return Path("Other")
    
    def _generate_tv_folder_structure(self, media_file: MediaFile) -> Path:
        """Generate TV show folder structure"""
        if not media_file.series_info or not media_file.episode_info:
            raise ValueError("Series and episode info required for TV shows")
        
        # Main series folder
        series_title = self._clean_title(media_file.series_info.title)
        year_part = f" ({media_file.series_info.year})" if media_file.series_info.year else ""
        resolution_part = f" [{self._format_resolution(media_file.media_info.resolution)}]" if self.config.include_resolution else ""
        codec_part = f" [{self._format_codec(media_file.media_info.video_codec)}]" if self.config.include_codec else ""
        
        series_folder = f"{series_title}{year_part}{resolution_part}{codec_part}"
        
        # Season folder
        season_folder = self.config.season_folder.format(season=media_file.episode_info.season)
        
        return Path(series_folder) / season_folder
    
    def _generate_movie_folder_structure(self, media_file: MediaFile) -> Path:
        """Generate movie folder structure"""
        if not media_file.movie_info:
            raise ValueError("Movie info required for movies")
        
        movie_title = self._clean_title(media_file.movie_info.title)
        year_part = f" ({media_file.movie_info.year})" if media_file.movie_info.year else ""
        resolution_part = f" [{self._format_resolution(media_file.media_info.resolution)}]" if self.config.include_resolution else ""
        codec_part = f" [{self._format_codec(media_file.media_info.video_codec)}]" if self.config.include_codec else ""
        
        movie_folder = f"{movie_title}{year_part}{resolution_part}{codec_part}"
        return Path(movie_folder)
    
    def _clean_title(self, title: str) -> str:
        """Clean title for use in filenames"""
        # Remove problematic characters
        cleaned = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename to be filesystem safe"""
        # Remove or replace problematic characters
        cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Remove leading/trailing spaces and dots
        cleaned = cleaned.strip(' .')
        return cleaned
    
    def _format_resolution(self, resolution: Resolution) -> str:
        """Format resolution for filename"""
        if resolution == Resolution.UNKNOWN:
            return "Unknown"
        return resolution.value
    
    def _format_codec(self, codec: VideoCodec) -> str:
        """Format codec for filename"""
        if codec == VideoCodec.UNKNOWN:
            return "Unknown"
        return codec.value


class FileOrganizer:
    """Organizes files into proper directory structure"""
    
    def __init__(self, base_path: Path, namer: FileNamer):
        self.base_path = base_path
        self.namer = namer
    
    def organize_file(self, media_file: MediaFile, copy: bool = False) -> Path:
        """Organize media file into proper structure"""
        # Generate target structure
        folder_structure = self.namer.generate_folder_structure(media_file)
        filename = self.namer.generate_filename(media_file)
        
        # Add original extension
        original_ext = media_file.media_info.file_path.suffix
        full_filename = f"{filename}{original_ext}"
        
        target_path = self.base_path / folder_structure / full_filename
        
        # Create directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move or copy file
        if copy:
            import shutil
            shutil.copy2(media_file.media_info.file_path, target_path)
        else:
            media_file.media_info.file_path.rename(target_path)
        
        # Handle subtitle files
        for subtitle_file in media_file.subtitle_files:
            subtitle_name = f"{filename}{subtitle_file.suffix}"
            subtitle_target = target_path.parent / subtitle_name
            
            if copy:
                import shutil
                shutil.copy2(subtitle_file, subtitle_target)
            else:
                subtitle_file.rename(subtitle_target)
        
        return target_path