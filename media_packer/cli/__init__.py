"""Command line interface for Media Packer"""
import click
import logging
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import print as rprint

from ..config import load_config, MediaPackerConfig
from ..core.processor import MediaProcessor
from ..core.torrent import TorrentCreator
from ..core.metadata import MetadataManager, NFOGenerator
from ..utils.naming import FileNamer, FileOrganizer
from ..models import MediaFile, MediaType

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx, config, verbose):
    """Media Packer - Create torrents for TV shows and movies"""
    
    # Setup logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    config_path = Path(config) if config else None
    ctx.obj = load_config(config_path)


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--organize', is_flag=True, help='Organize files before creating torrent')
@click.option('--fetch-metadata', is_flag=True, help='Fetch metadata from TMDB')
@click.option('--create-nfo', is_flag=True, help='Create NFO files')
@click.pass_obj
def pack(config: MediaPackerConfig, input_path, output, organize, fetch_metadata, create_nfo):
    """Pack a media file or directory into a torrent"""
    
    input_path = Path(input_path)
    output_dir = Path(output) if output else config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Process media files
        task = progress.add_task("Scanning media files...", total=None)
        media_files = _scan_media_files(input_path)
        progress.update(task, description=f"Found {len(media_files)} media files")
        
        if not media_files:
            rprint("[red]No media files found![/red]")
            return
        
        # Process each media file
        for i, media_file in enumerate(media_files):
            progress.update(task, description=f"Processing {media_file.media_info.file_path.name}")
            
            # Fetch metadata if requested
            if fetch_metadata and config.tmdb_api_key:
                _fetch_and_apply_metadata(media_file, config)
            
            # Organize files if requested
            if organize:
                organized_path = _organize_media_file(media_file, output_dir, config)
            else:
                organized_path = media_file.media_info.file_path
            
            # Create NFO files if requested
            if create_nfo:
                _create_nfo_files(media_file, organized_path.parent if organized_path.is_file() else organized_path)
            
            # Create torrent
            torrent_path = _create_torrent(media_file, organized_path, output_dir, config)
            
            rprint(f"[green]✓[/green] Created: {torrent_path.name}")
        
        progress.update(task, description="Completed!")


@main.command()
@click.argument('input_paths', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--name', '-n', required=True, help='Torrent name')
@click.pass_obj
def batch(config: MediaPackerConfig, input_paths, output, name):
    """Create a single torrent from multiple files/directories"""
    
    if not input_paths:
        rprint("[red]No input paths provided![/red]")
        return
    
    paths = [Path(p) for p in input_paths]
    output_dir = Path(output) if output else config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Creating batch torrent...", total=None)
        
        # Create torrent creator
        torrent_creator = TorrentCreator(config.torrent)
        
        # Create batch torrent
        torrent_path = torrent_creator.create_batch_torrent(paths, output_dir, name)
        
        progress.update(task, description="Completed!")
        rprint(f"[green]✓[/green] Created batch torrent: {torrent_path.name}")


@main.command()
@click.argument('torrent_path', type=click.Path(exists=True))
def info(torrent_path):
    """Display information about a torrent file"""
    
    torrent_path = Path(torrent_path)
    
    try:
        from ..core.torrent import TorrentCreator
        torrent_creator = TorrentCreator(None)  # Config not needed for info
        info_dict = torrent_creator.get_torrent_info(torrent_path)
        
        # Create info table
        table = Table(title=f"Torrent Info: {torrent_path.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Name", info_dict['name'])
        table.add_row("Size", _format_size(info_dict['size']))
        table.add_row("Files", str(info_dict['file_count']))
        table.add_row("Pieces", str(info_dict['piece_count']))
        table.add_row("Piece Size", _format_size(info_dict['piece_size']))
        table.add_row("Private", "Yes" if info_dict['private'] else "No")
        table.add_row("Comment", info_dict['comment'] or "")
        table.add_row("Created By", info_dict['created_by'] or "")
        table.add_row("InfoHash", info_dict['infohash'])
        
        console.print(table)
        
        # Show trackers
        if info_dict['trackers']:
            rprint("\n[bold]Trackers:[/bold]")
            for i, tracker in enumerate(info_dict['trackers'], 1):
                rprint(f"  {i}. {tracker}")
        
        # Show magnet link
        rprint(f"\n[bold]Magnet URI:[/bold]\n{info_dict['magnet_uri']}")
        
    except Exception as e:
        rprint(f"[red]Error reading torrent: {e}[/red]")


@main.command()
@click.argument('query')
@click.option('--type', 'media_type', type=click.Choice(['tv', 'movie']), default='tv')
@click.option('--year', type=int, help='Release year')
@click.pass_obj
def search(config: MediaPackerConfig, query, media_type, year):
    """Search for media metadata"""
    
    if not config.tmdb_api_key:
        rprint("[red]TMDB API key not configured![/red]")
        return
    
    metadata_manager = MetadataManager(config.tmdb_api_key)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task(f"Searching for '{query}'...", total=None)
        
        if media_type == 'tv':
            results = metadata_manager.search_series(query, year)
        else:
            results = metadata_manager.search_movie(query, year)
        
        progress.update(task, description="Search completed!")
    
    if not results:
        rprint("[yellow]No results found[/yellow]")
        return
    
    # Display results
    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Year", style="yellow")
    table.add_column("Overview", style="dim", max_width=50)
    
    for result in results:
        table.add_row(
            str(result.tmdb_id),
            result.title,
            str(result.year) if result.year else "N/A",
            (result.overview[:100] + "...") if result.overview and len(result.overview) > 100 else (result.overview or "")
        )
    
    console.print(table)


def _scan_media_files(path: Path) -> List[MediaFile]:
    """Scan directory for media files"""
    media_files = []
    
    if path.is_file() and MediaProcessor.is_video_file(path):
        # Single file
        media_info = MediaProcessor.extract_media_info(path)
        media_type = MediaProcessor.detect_media_type(path)
        episode_info = MediaProcessor.extract_episode_info(path) if media_type == MediaType.TV_SHOW else None
        subtitle_files = MediaProcessor.find_subtitle_files(path)
        
        media_file = MediaFile(
            media_info=media_info,
            media_type=media_type,
            episode_info=episode_info,
            subtitle_files=subtitle_files
        )
        media_files.append(media_file)
    
    elif path.is_dir():
        # Directory - scan for video files
        for video_file in path.rglob("*"):
            if video_file.is_file() and MediaProcessor.is_video_file(video_file):
                media_info = MediaProcessor.extract_media_info(video_file)
                media_type = MediaProcessor.detect_media_type(video_file)
                episode_info = MediaProcessor.extract_episode_info(video_file) if media_type == MediaType.TV_SHOW else None
                subtitle_files = MediaProcessor.find_subtitle_files(video_file)
                
                media_file = MediaFile(
                    media_info=media_info,
                    media_type=media_type,
                    episode_info=episode_info,
                    subtitle_files=subtitle_files
                )
                media_files.append(media_file)
    
    return media_files


def _fetch_and_apply_metadata(media_file: MediaFile, config: MediaPackerConfig):
    """Fetch and apply metadata to media file"""
    metadata_manager = MetadataManager(config.tmdb_api_key)
    
    # Extract title and year from filename
    title, year = MediaProcessor.extract_title_and_year(media_file.media_info.file_path)
    
    # Auto-match metadata
    metadata = metadata_manager.auto_match_metadata(title, year, media_file.media_type)
    
    if metadata and metadata['confidence'] > 0.7:  # High confidence match
        if metadata['type'] == 'series':
            media_file.series_info = metadata['info']
        elif metadata['type'] == 'movie':
            media_file.movie_info = metadata['info']


def _organize_media_file(media_file: MediaFile, output_dir: Path, config: MediaPackerConfig) -> Path:
    """Organize media file using naming conventions"""
    namer = FileNamer(config.naming)
    organizer = FileOrganizer(output_dir, namer)
    
    return organizer.organize_file(media_file, copy=True)  # Copy to preserve originals


def _create_nfo_files(media_file: MediaFile, target_dir: Path):
    """Create NFO files for media"""
    if media_file.media_type == MediaType.TV_SHOW and media_file.series_info:
        # TV show NFO
        nfo_content = NFOGenerator.generate_tvshow_nfo(media_file.series_info)
        nfo_path = target_dir / "tvshow.nfo"
        nfo_path.write_text(nfo_content, encoding='utf-8')
        
        # Episode NFO
        if media_file.episode_info:
            episode_nfo = NFOGenerator.generate_episode_nfo(media_file.episode_info, media_file.series_info)
            episode_nfo_path = target_dir / f"{media_file.media_info.file_path.stem}.nfo"
            episode_nfo_path.write_text(episode_nfo, encoding='utf-8')
    
    elif media_file.media_type == MediaType.MOVIE and media_file.movie_info:
        # Movie NFO
        nfo_content = NFOGenerator.generate_movie_nfo(media_file.movie_info)
        nfo_path = target_dir / f"{media_file.media_info.file_path.stem}.nfo"
        nfo_path.write_text(nfo_content, encoding='utf-8')


def _create_torrent(media_file: MediaFile, content_path: Path, output_dir: Path, config: MediaPackerConfig) -> Path:
    """Create torrent for media file"""
    torrent_creator = TorrentCreator(config.torrent)
    return torrent_creator.create_media_torrent(media_file, content_path, output_dir)


def _format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


if __name__ == '__main__':
    main()