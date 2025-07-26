# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Media Packer**, a Chinese torrent creation tool designed for PT (Private Tracker) users. The project provides simplified torrent generation functionality with automatic dependency management and cross-platform support.

## Key Architecture

### Two Main Versions
- **Simple Version** (`media_packer_simple.py`): Minimal dependencies (torf, click, rich), focused on core torrent creation
- **Full Version** (`media_packer_all_in_one.py`): Complete feature set including metadata fetching and NFO generation

### Core Components
- `start.py`: Intelligent launcher that handles version selection and dependency installation
- `install_deps.py`: Dedicated dependency management tool
- `universal-install.sh`: Cross-platform installation script for production deployment
- Performance testing tools (`test_performance_default.py`, `torf_performance_analyzer.py`)

### Project Structure
- `/output/`: Default directory for generated torrent files
- `/performance_test_output/`: Contains various torrent test files for performance analysis
- Multiple documentation files in Chinese for deployment and usage guides

## Common Development Commands

### Running the Application
```bash
# Smart launcher (recommended)
python3 start.py

# Direct execution - Simple version
python3 media_packer_simple.py

# Direct execution - Full version  
python3 media_packer_all_in_one.py

# Interactive mode
python3 media_packer_simple.py interactive

# Command line usage
python3 media_packer_simple.py pack /path/to/video.mkv --name "MyTorrent"
python3 media_packer_simple.py batch /path/to/videos/* --organize
```

### Dependency Management
```bash
# Check and install dependencies automatically
python3 install_deps.py --mode simple    # For simple version
python3 install_deps.py --mode full      # For full version
python3 install_deps.py --force          # Force reinstall

# Manual dependency installation
pip install torf click rich              # Simple version deps
pip install torf pymediainfo tmdbv3api requests click rich  # Full version deps
```

### Testing
```bash
# Basic functionality test
python3 media_packer_simple.py --help
python3 start.py
```

## Core Dependencies

### Required for Simple Version
- `torf>=4.0.0`: Torrent file creation library
- `click>=8.0.0`: Command line interface framework  
- `rich>=13.0.0`: Terminal formatting and progress display

### Additional for Full Version
- `requests>=2.25.0`: HTTP requests for metadata
- `tmdbv3api>=1.7.0`: TMDB API for movie/TV metadata
- `pymediainfo>=5.0.0`: Media file analysis

## Key Features

### Automatic Dependency Management
The project includes sophisticated dependency checking and installation:
- Automatic detection of missing packages
- Smart installer that works across platforms
- Virtual environment support for modern Python restrictions
- Fallback options for restricted environments

### Torrent Creation Workflow
1. Input validation and file/folder selection
2. Intelligent naming (defaults to folder name)
3. Torrent generation with configurable parameters
4. Output organization and file management

### Cross-Platform Deployment
- Universal installer script handles different OS environments
- VPS-optimized deployment with minimal dependencies
- Support for both traditional and modern Python package management

## Important Notes

- This project is specifically designed for Chinese PT users
- File names and documentation are primarily in Chinese  
- The tool prioritizes simplicity and automatic operation
- Optimized for production use with minimal file footprint

## Development Environment

- **Python Version**: Requires Python 3.8+
- **Primary Language**: Python with minimal dependencies
- **Package Management**: Uses both requirements.txt and pyproject.toml
- **Testing**: Use `python3 start.py` or direct script execution for verification