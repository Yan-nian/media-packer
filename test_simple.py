"""Simplified test without external dependencies"""
from pathlib import Path
import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_patterns():
    """Test basic pattern matching without external dependencies"""
    import re
    
    # Test video file detection
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    SUBTITLE_EXTENSIONS = {'.srt', '.ass', '.ssa', '.sub', '.vtt', '.idx', '.sup'}
    
    test_files = [
        "movie.mkv",
        "episode.mp4", 
        "show.avi",
        "subtitle.srt",
        "document.txt"
    ]
    
    print("File Type Detection:")
    for filename in test_files:
        path = Path(filename)
        is_video = path.suffix.lower() in VIDEO_EXTENSIONS
        is_subtitle = path.suffix.lower() in SUBTITLE_EXTENSIONS
        print(f"{filename}: video={is_video}, subtitle={is_subtitle}")
    
    # Test TV show patterns
    TV_PATTERNS = [
        r'S(\d{1,2})E(\d{1,2})',  # S01E01
        r'(\d{1,2})x(\d{1,2})',   # 1x01
        r'Season\s*(\d{1,2}).*Episode\s*(\d{1,2})', # Season 1 Episode 1
    ]
    
    tv_files = [
        "Show.S01E01.mkv",
        "Series.1x05.mp4",
        "Drama.Season.1.Episode.3.avi",
        "Regular.Movie.2023.mkv"
    ]
    
    print("\\nTV Show Pattern Detection:")
    for filename in tv_files:
        is_tv = False
        season = episode = None
        
        for pattern in TV_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                is_tv = True
                season = int(match.group(1))
                episode = int(match.group(2))
                break
        
        print(f"{filename}: TV={is_tv}, S{season}E{episode}" if is_tv else f"{filename}: TV={is_tv}")
    
    # Test title and year extraction
    print("\\nTitle and Year Extraction:")
    test_titles = [
        "Breaking.Bad.S01E01.2008.1080p.mkv",
        "The.Matrix.1999.BluRay.1080p.mp4",
        "Game.of.Thrones.S08E06.2019.4K.mkv",
        "Inception.2010.mkv"
    ]
    
    for filename in test_titles:
        # Remove episode info
        cleaned = filename
        for pattern in TV_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Extract year
        year_match = re.search(r'\((\d{4})\)|\b(\d{4})\b', cleaned)
        year = None
        if year_match:
            year = int(year_match.group(1) or year_match.group(2))
            cleaned = re.sub(r'\(?\d{4}\)?', '', cleaned)
        
        # Clean title
        title = re.sub(r'[._\-]+', ' ', Path(cleaned).stem).strip()
        title = re.sub(r'\s+', ' ', title)
        
        print(f"{filename}: title='{title}', year={year}")

def test_config_loading():
    """Test configuration system"""
    print("\\nTesting Configuration:")
    
    # Test default config creation
    try:
        from media_packer.config import MediaPackerConfig
        config = MediaPackerConfig()
        print(f"Default config created successfully")
        print(f"Output dir: {config.output_dir}")
        print(f"Torrent private: {config.torrent.private}")
        print(f"TV format: {config.naming.tv_format}")
    except Exception as e:
        print(f"Config creation failed: {e}")

def test_models():
    """Test data models"""
    print("\\nTesting Data Models:")
    
    try:
        from media_packer.models import Resolution, VideoCodec, MediaType
        print(f"Resolution enum: {list(Resolution)}")
        print(f"Video codec enum: {list(VideoCodec)}")
        print(f"Media type enum: {list(MediaType)}")
    except Exception as e:
        print(f"Models test failed: {e}")

if __name__ == "__main__":
    print("=== Media Packer Basic Tests ===\\n")
    test_basic_patterns()
    test_config_loading()
    test_models()
    print("\\n=== Tests Completed ===")