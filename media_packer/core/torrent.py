"""Torrent creation using torf library"""
from pathlib import Path
from typing import List, Optional, Dict, Any
from torf import Torrent
from ..models import MediaFile
from ..config import TorrentConfig
import logging

logger = logging.getLogger(__name__)


class TorrentCreator:
    """Creates torrent files using torf library"""
    
    def __init__(self, config: TorrentConfig):
        self.config = config
    
    def create_torrent(
        self, 
        content_path: Path, 
        output_path: Optional[Path] = None,
        **kwargs
    ) -> Torrent:
        """Create a torrent file for the given content"""
        
        if not content_path.exists():
            raise FileNotFoundError(f"Content path does not exist: {content_path}")
        
        # Merge config with kwargs
        torrent_kwargs = {
            'path': str(content_path),
            'trackers': self.config.trackers,
            'private': self.config.private,
            'comment': self.config.comment,
            'created_by': self.config.created_by,
        }
        
        # Add piece size if specified
        if self.config.piece_size:
            torrent_kwargs['piece_size'] = self.config.piece_size
        
        # Override with any provided kwargs
        torrent_kwargs.update(kwargs)
        
        logger.info(f"Creating torrent for: {content_path}")
        torrent = Torrent(**torrent_kwargs)
        
        # Generate torrent data
        torrent.generate()
        
        # Write torrent file if output path specified
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torrent.write(str(output_path))
            logger.info(f"Torrent written to: {output_path}")
        
        return torrent
    
    def create_media_torrent(
        self, 
        media_file: MediaFile, 
        organized_path: Path,
        output_dir: Path
    ) -> Path:
        """Create torrent specifically for a media file"""
        
        # Generate torrent filename
        torrent_name = self._generate_torrent_name(media_file, organized_path)
        torrent_path = output_dir / f"{torrent_name}.torrent"
        
        # Create custom comment for media
        comment = self._generate_media_comment(media_file)
        
        # Create torrent
        torrent = self.create_torrent(
            content_path=organized_path,
            output_path=torrent_path,
            comment=comment
        )
        
        return torrent_path
    
    def create_batch_torrent(
        self, 
        content_paths: List[Path], 
        output_dir: Path,
        torrent_name: str
    ) -> Path:
        """Create a single torrent for multiple content paths"""
        
        # For multiple paths, we need a common parent directory
        if len(content_paths) == 1:
            content_path = content_paths[0]
        else:
            # Find common parent or create temp structure
            common_parent = self._find_common_parent(content_paths)
            if not common_parent:
                raise ValueError("Cannot find common parent for batch torrent")
            content_path = common_parent
        
        torrent_path = output_dir / f"{torrent_name}.torrent"
        
        self.create_torrent(
            content_path=content_path,
            output_path=torrent_path
        )
        
        return torrent_path
    
    def _generate_torrent_name(self, media_file: MediaFile, organized_path: Path) -> str:
        """Generate torrent filename based on media info"""
        if organized_path.is_file():
            # Single file torrent
            return organized_path.stem
        else:
            # Directory torrent
            return organized_path.name
    
    def _generate_media_comment(self, media_file: MediaFile) -> str:
        """Generate descriptive comment for media torrent"""
        base_comment = self.config.comment
        
        # Add media-specific info
        media_info = []
        
        if media_file.media_info.resolution.value != "Unknown":
            media_info.append(media_file.media_info.resolution.value)
        
        if media_file.media_info.video_codec.value != "Unknown":
            media_info.append(media_file.media_info.video_codec.value)
        
        if media_file.media_info.audio_codec.value != "Unknown":
            media_info.append(media_file.media_info.audio_codec.value)
        
        if media_info:
            return f"{base_comment} | {' | '.join(media_info)}"
        
        return base_comment
    
    def _find_common_parent(self, paths: List[Path]) -> Optional[Path]:
        """Find common parent directory for multiple paths"""
        if not paths:
            return None
        
        if len(paths) == 1:
            return paths[0].parent if paths[0].is_file() else paths[0]
        
        # Find common parts
        common_parts = None
        for path in paths:
            parts = path.parts
            if common_parts is None:
                common_parts = parts
            else:
                # Find common prefix
                common_parts = tuple(
                    part for i, part in enumerate(common_parts)
                    if i < len(parts) and part == parts[i]
                )
        
        if common_parts:
            return Path(*common_parts)
        
        return None
    
    def get_torrent_info(self, torrent_path: Path) -> Dict[str, Any]:
        """Get information about an existing torrent file"""
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


class TorrentValidator:
    """Validates torrent files and content"""
    
    @staticmethod
    def validate_torrent(torrent_path: Path) -> bool:
        """Validate that torrent file is valid"""
        try:
            torrent = Torrent.read(str(torrent_path))
            return torrent.is_ready
        except Exception as e:
            logger.error(f"Torrent validation failed: {e}")
            return False
    
    @staticmethod
    def verify_content(torrent_path: Path, content_path: Path) -> bool:
        """Verify that content matches torrent"""
        try:
            torrent = Torrent.read(str(torrent_path))
            
            # Create new torrent from content and compare
            verification_torrent = Torrent(
                path=str(content_path),
                piece_size=torrent.piece_size
            )
            verification_torrent.generate()
            
            return torrent.infohash == verification_torrent.infohash
        except Exception as e:
            logger.error(f"Content verification failed: {e}")
            return False