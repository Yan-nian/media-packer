"""Batch processing and automation utilities"""
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from queue import Queue, Empty
from dataclasses import dataclass
from enum import Enum
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor, Future

from ..models import MediaFile
from ..core.processor import MediaProcessor
from ..core.torrent import TorrentCreator
from ..core.metadata import MetadataManager
from ..utils.naming import FileNamer, FileOrganizer
from ..config import MediaPackerConfig

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ProcessingTask:
    """Represents a media processing task"""
    id: str
    file_path: Path
    status: TaskStatus = TaskStatus.PENDING
    error_message: Optional[str] = None
    created_at: float = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class BatchProcessor:
    """Handles batch processing of media files"""
    
    def __init__(self, config: MediaPackerConfig, max_workers: int = 4):
        self.config = config
        self.max_workers = max_workers
        self.task_queue = Queue()
        self.tasks: Dict[str, ProcessingTask] = {}
        self.is_running = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures: Dict[str, Future] = {}
        
        # Initialize components
        self.metadata_manager = MetadataManager(config.tmdb_api_key)
        self.torrent_creator = TorrentCreator(config.torrent)
        self.file_namer = FileNamer(config.naming)
        self.file_organizer = FileOrganizer(config.output_dir, self.file_namer)
    
    def add_task(self, file_path: Path) -> str:
        """Add a file to the processing queue"""
        task_id = f"{file_path.name}_{int(time.time())}"
        task = ProcessingTask(id=task_id, file_path=file_path)
        
        self.tasks[task_id] = task
        self.task_queue.put(task_id)
        
        logger.info(f"Added task: {task_id} for file: {file_path}")
        return task_id
    
    def add_batch(self, file_paths: List[Path]) -> List[str]:
        """Add multiple files to the processing queue"""
        task_ids = []
        for file_path in file_paths:
            if MediaProcessor.is_video_file(file_path):
                task_id = self.add_task(file_path)
                task_ids.append(task_id)
        return task_ids
    
    def start_processing(self):
        """Start the batch processing worker"""
        if self.is_running:
            logger.warning("Batch processor is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting batch processor with {self.max_workers} workers")
        
        # Start processing thread
        processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        processing_thread.start()
    
    def stop_processing(self):
        """Stop the batch processing worker"""
        self.is_running = False
        self.executor.shutdown(wait=True)
        logger.info("Batch processor stopped")
    
    def get_task_status(self, task_id: str) -> Optional[ProcessingTask]:
        """Get status of a specific task"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, ProcessingTask]:
        """Get all tasks"""
        return self.tasks.copy()
    
    def get_pending_tasks(self) -> List[ProcessingTask]:
        """Get list of pending tasks"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.PENDING]
    
    def get_completed_tasks(self) -> List[ProcessingTask]:
        """Get list of completed tasks"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]
    
    def get_error_tasks(self) -> List[ProcessingTask]:
        """Get list of failed tasks"""
        return [task for task in self.tasks.values() if task.status == TaskStatus.ERROR]
    
    def _process_queue(self):
        """Main processing loop"""
        while self.is_running:
            try:
                # Get next task (with timeout)
                task_id = self.task_queue.get(timeout=1.0)
                task = self.tasks.get(task_id)
                
                if not task:
                    continue
                
                # Submit task to thread pool
                future = self.executor.submit(self._process_single_task, task)
                self.futures[task_id] = future
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing queue: {e}")
    
    def _process_single_task(self, task: ProcessingTask):
        """Process a single media file"""
        try:
            logger.info(f"Processing task: {task.id}")
            task.status = TaskStatus.PROCESSING
            
            # Extract media information
            media_info = MediaProcessor.extract_media_info(task.file_path)
            media_type = MediaProcessor.detect_media_type(task.file_path)
            episode_info = MediaProcessor.extract_episode_info(task.file_path) if media_type.value == 'tv' else None
            subtitle_files = MediaProcessor.find_subtitle_files(task.file_path)
            
            # Create media file object
            media_file = MediaFile(
                media_info=media_info,
                media_type=media_type,
                episode_info=episode_info,
                subtitle_files=subtitle_files
            )
            
            # Fetch metadata if configured
            if self.config.tmdb_api_key:
                self._fetch_metadata(media_file)
            
            # Organize file
            organized_path = self.file_organizer.organize_file(media_file, copy=True)
            
            # Create NFO files
            self._create_nfo_files(media_file, organized_path.parent if organized_path.is_file() else organized_path)
            
            # Create torrent
            torrent_path = self.torrent_creator.create_media_torrent(
                media_file, organized_path, self.config.output_dir
            )
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            task.result = {
                'organized_path': str(organized_path),
                'torrent_path': str(torrent_path),
                'media_type': media_type.value,
                'title': self._get_media_title(media_file)
            }
            
            logger.info(f"Completed task: {task.id}")
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            task.status = TaskStatus.ERROR
            task.error_message = str(e)
            task.completed_at = time.time()
    
    def _fetch_metadata(self, media_file: MediaFile):
        """Fetch metadata for media file"""
        try:
            title, year = MediaProcessor.extract_title_and_year(media_file.media_info.file_path)
            metadata = self.metadata_manager.auto_match_metadata(title, year, media_file.media_type)
            
            if metadata and metadata['confidence'] > 0.7:
                if metadata['type'] == 'series':
                    media_file.series_info = metadata['info']
                elif metadata['type'] == 'movie':
                    media_file.movie_info = metadata['info']
        except Exception as e:
            logger.warning(f"Failed to fetch metadata: {e}")
    
    def _create_nfo_files(self, media_file: MediaFile, target_dir: Path):
        """Create NFO files for media"""
        try:
            from ..core.metadata import NFOGenerator
            
            if media_file.media_type.value == 'tv' and media_file.series_info:
                # TV show NFO
                nfo_content = NFOGenerator.generate_tvshow_nfo(media_file.series_info)
                nfo_path = target_dir / "tvshow.nfo"
                nfo_path.write_text(nfo_content, encoding='utf-8')
                
                # Episode NFO
                if media_file.episode_info:
                    episode_nfo = NFOGenerator.generate_episode_nfo(media_file.episode_info, media_file.series_info)
                    episode_nfo_path = target_dir / f"{media_file.media_info.file_path.stem}.nfo"
                    episode_nfo_path.write_text(episode_nfo, encoding='utf-8')
            
            elif media_file.media_type.value == 'movie' and media_file.movie_info:
                # Movie NFO
                nfo_content = NFOGenerator.generate_movie_nfo(media_file.movie_info)
                nfo_path = target_dir / f"{media_file.media_info.file_path.stem}.nfo"
                nfo_path.write_text(nfo_content, encoding='utf-8')
        except Exception as e:
            logger.warning(f"Failed to create NFO files: {e}")
    
    def _get_media_title(self, media_file: MediaFile) -> str:
        """Get media title for display"""
        if media_file.series_info:
            return media_file.series_info.title
        elif media_file.movie_info:
            return media_file.movie_info.title
        else:
            return media_file.media_info.file_path.stem


class DirectoryWatcher:
    """Watches directory for new media files and auto-processes them"""
    
    def __init__(self, config: MediaPackerConfig, batch_processor: BatchProcessor):
        self.config = config
        self.batch_processor = batch_processor
        self.observer = Observer()
        self.is_watching = False
    
    def start_watching(self, watch_path: Path):
        """Start watching directory for new files"""
        if self.is_watching:
            logger.warning("Directory watcher is already running")
            return
        
        event_handler = MediaFileHandler(self.batch_processor)
        self.observer.schedule(event_handler, str(watch_path), recursive=True)
        self.observer.start()
        self.is_watching = True
        
        logger.info(f"Started watching directory: {watch_path}")
    
    def stop_watching(self):
        """Stop watching directory"""
        if self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            logger.info("Stopped directory watching")


class MediaFileHandler(FileSystemEventHandler):
    """Handles file system events for media files"""
    
    def __init__(self, batch_processor: BatchProcessor):
        super().__init__()
        self.batch_processor = batch_processor
        self.debounce_time = 5.0  # Wait 5 seconds after file creation
        self.pending_files = {}
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        if MediaProcessor.is_video_file(file_path):
            # Debounce file creation (wait for file to be fully written)
            self._schedule_processing(file_path)
    
    def on_moved(self, event):
        """Handle file move events"""
        if event.is_directory:
            return
        
        file_path = Path(event.dest_path)
        
        if MediaProcessor.is_video_file(file_path):
            self._schedule_processing(file_path)
    
    def _schedule_processing(self, file_path: Path):
        """Schedule file for processing after debounce period"""
        # Cancel any existing timer for this file
        if str(file_path) in self.pending_files:
            self.pending_files[str(file_path)].cancel()
        
        # Schedule new processing
        timer = threading.Timer(
            self.debounce_time,
            self._process_file,
            args=[file_path]
        )
        timer.start()
        self.pending_files[str(file_path)] = timer
        
        logger.info(f"Scheduled processing for: {file_path}")
    
    def _process_file(self, file_path: Path):
        """Process file after debounce period"""
        try:
            if file_path.exists() and file_path.stat().st_size > 0:
                self.batch_processor.add_task(file_path)
                logger.info(f"Added to processing queue: {file_path}")
            
            # Clean up pending files
            if str(file_path) in self.pending_files:
                del self.pending_files[str(file_path)]
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")


class AutomationManager:
    """Manages automated processing workflows"""
    
    def __init__(self, config: MediaPackerConfig):
        self.config = config
        self.batch_processor = BatchProcessor(config)
        self.directory_watcher = DirectoryWatcher(config, self.batch_processor)
        self.is_running = False
    
    def start_automation(self, watch_directories: List[Path]):
        """Start automated processing"""
        if self.is_running:
            logger.warning("Automation is already running")
            return
        
        # Start batch processor
        self.batch_processor.start_processing()
        
        # Start directory watchers
        for watch_dir in watch_directories:
            if watch_dir.exists() and watch_dir.is_dir():
                self.directory_watcher.start_watching(watch_dir)
        
        self.is_running = True
        logger.info("Automation started")
    
    def stop_automation(self):
        """Stop automated processing"""
        if not self.is_running:
            return
        
        self.directory_watcher.stop_watching()
        self.batch_processor.stop_processing()
        self.is_running = False
        logger.info("Automation stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get automation status"""
        return {
            'is_running': self.is_running,
            'pending_tasks': len(self.batch_processor.get_pending_tasks()),
            'completed_tasks': len(self.batch_processor.get_completed_tasks()),
            'error_tasks': len(self.batch_processor.get_error_tasks()),
            'total_tasks': len(self.batch_processor.get_all_tasks())
        }