"""Configuration management for Media Packer"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, validator


class TorrentConfig(BaseModel):
    """Torrent creation configuration"""
    trackers: List[str] = []
    private: bool = True
    piece_size: Optional[int] = None
    comment: str = "Created with Media Packer"
    created_by: str = "Media Packer"
    
    @validator('trackers')
    def validate_trackers(cls, v):
        if not v:
            raise ValueError("At least one tracker is required")
        return v


class NamingConfig(BaseModel):
    """File naming configuration"""
    tv_format: str = "{title} ({year}) S{season:02d}E{episode:02d} [{resolution}] [{codec}]"
    movie_format: str = "{title} ({year}) [{resolution}] [{codec}]"
    season_folder: str = "Season {season:02d}"
    include_year: bool = True
    include_resolution: bool = True
    include_codec: bool = True


class MediaPackerConfig(BaseModel):
    """Main configuration class"""
    torrent: TorrentConfig = TorrentConfig()
    naming: NamingConfig = NamingConfig()
    tmdb_api_key: Optional[str] = None
    output_dir: Path = Path("./output")
    temp_dir: Path = Path("./temp")
    
    @validator('output_dir', 'temp_dir')
    def ensure_path_exists(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v


def load_config(config_path: Optional[Path] = None) -> MediaPackerConfig:
    """Load configuration from file or environment"""
    if config_path and config_path.exists():
        import json
        with open(config_path) as f:
            data = json.load(f)
        return MediaPackerConfig(**data)
    
    # Load from environment variables
    config = MediaPackerConfig()
    
    # Override with environment variables if present
    if os.getenv('TMDB_API_KEY'):
        config.tmdb_api_key = os.getenv('TMDB_API_KEY')
    
    if os.getenv('MP_OUTPUT_DIR'):
        config.output_dir = Path(os.getenv('MP_OUTPUT_DIR'))
    
    return config