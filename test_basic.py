"""Test the media processor functionality"""
import tempfile
from pathlib import Path
from media_packer.core.processor import MediaProcessor
from media_packer.models import MediaType

def test_basic_functionality():
    """Test basic functionality without actual media files"""
    
    # Test video file detection
    test_files = [
        "movie.mkv",
        "episode.mp4", 
        "show.avi",
        "subtitle.srt",
        "document.txt"
    ]
    
    for filename in test_files:
        path = Path(filename)
        is_video = MediaProcessor.is_video_file(path)
        is_subtitle = MediaProcessor.is_subtitle_file(path)
        
        print(f"{filename}: video={is_video}, subtitle={is_subtitle}")
    
    # Test media type detection
    tv_files = [
        "Show.S01E01.mkv",
        "Series.1x05.mp4",
        "Drama.Season.1.Episode.3.avi"
    ]
    
    movie_files = [
        "Movie.2023.1080p.mkv",
        "Film.BluRay.mp4"
    ]
    
    print("\\nTV Show Detection:")
    for filename in tv_files:
        path = Path(filename)
        media_type = MediaProcessor.detect_media_type(path)
        episode_info = MediaProcessor.extract_episode_info(path)
        print(f"{filename}: type={media_type}, episode={episode_info}")
    
    print("\\nMovie Detection:")
    for filename in movie_files:
        path = Path(filename)
        media_type = MediaProcessor.detect_media_type(path)
        print(f"{filename}: type={media_type}")
    
    # Test title extraction
    print("\\nTitle Extraction:")
    test_titles = [
        "Breaking.Bad.S01E01.2008.1080p.mkv",
        "The.Matrix.1999.BluRay.1080p.mp4",
        "Game.of.Thrones.S08E06.2019.4K.mkv"
    ]
    
    for filename in test_titles:
        path = Path(filename)
        title, year = MediaProcessor.extract_title_and_year(path)
        print(f"{filename}: title='{title}', year={year}")

if __name__ == "__main__":
    test_basic_functionality()