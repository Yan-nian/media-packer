"""Data models for Media Packer"""
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator
import re


class MediaType(str, Enum):
    """Media type enumeration"""
    TV_SHOW = "tv"
    MOVIE = "movie"
    DOCUMENTARY = "documentary"


class VideoCodec(str, Enum):
    """Video codec enumeration"""
    H264 = "H.264"
    H265 = "H.265"
    XVID = "XviD"
    AV1 = "AV1"
    UNKNOWN = "Unknown"


class AudioCodec(str, Enum):
    """Audio codec enumeration"""
    AAC = "AAC"
    AC3 = "AC3"
    DTS = "DTS"
    MP3 = "MP3"
    FLAC = "FLAC"
    UNKNOWN = "Unknown"


class Resolution(str, Enum):
    """Resolution enumeration"""
    SD_480P = "480p"
    HD_720P = "720p"
    FHD_1080P = "1080p"
    UHD_2160P = "2160p"
    UHD_4K = "4K"
    UNKNOWN = "Unknown"


class MediaInfo(BaseModel):
    """Media file information"""
    file_path: Path
    file_size: int
    duration: Optional[float] = None
    resolution: Resolution = Resolution.UNKNOWN
    video_codec: VideoCodec = VideoCodec.UNKNOWN
    audio_codec: AudioCodec = AudioCodec.UNKNOWN
    bitrate: Optional[int] = None
    frame_rate: Optional[float] = None
    
    @validator('file_path')
    def path_must_exist(cls, v):
        if not v.exists():
            raise ValueError(f"File does not exist: {v}")
        return v


class EpisodeInfo(BaseModel):
    """TV episode information"""
    season: int
    episode: int
    title: Optional[str] = None
    air_date: Optional[str] = None
    overview: Optional[str] = None
    
    @validator('season', 'episode')
    def positive_numbers(cls, v):
        if v <= 0:
            raise ValueError("Season and episode numbers must be positive")
        return v


class SeriesInfo(BaseModel):
    """TV series information"""
    title: str
    year: Optional[int] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    overview: Optional[str] = None
    genres: List[str] = []
    network: Optional[str] = None
    status: Optional[str] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None


class MovieInfo(BaseModel):
    """Movie information"""
    title: str
    year: Optional[int] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    overview: Optional[str] = None
    genres: List[str] = []
    director: Optional[str] = None
    runtime: Optional[int] = None
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None


class MediaFile(BaseModel):
    """Complete media file representation"""
    media_info: MediaInfo
    media_type: MediaType
    series_info: Optional[SeriesInfo] = None
    movie_info: Optional[MovieInfo] = None
    episode_info: Optional[EpisodeInfo] = None
    subtitle_files: List[Path] = []
    
    @validator('series_info')
    def series_info_for_tv(cls, v, values):
        if values.get('media_type') == MediaType.TV_SHOW and not v:
            raise ValueError("Series info required for TV shows")
        return v
    
    @validator('movie_info')
    def movie_info_for_movies(cls, v, values):
        if values.get('media_type') == MediaType.MOVIE and not v:
            raise ValueError("Movie info required for movies")
        return v
    
    @validator('episode_info')
    def episode_info_for_tv(cls, v, values):
        if values.get('media_type') == MediaType.TV_SHOW and not v:
            raise ValueError("Episode info required for TV shows")
        return v