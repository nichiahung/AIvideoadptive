# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AdaptVideo is a DOOH (Digital Out-of-Home) video adaptation tool that intelligently converts videos to different aspect ratios using AI-powered content analysis. It's built with Flask and integrates OpenAI's vision API for smart cropping and face detection.

## Development Commands

### Setup and Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads outputs
```

### Running the Application
```bash
# Development server (runs on port 5001)
python app.py

# Production server (using gunicorn)
gunicorn app:app

# Platform-specific launchers
./start_unix.sh     # macOS/Linux
start_windows.bat   # Windows
```

### Testing
```bash
# Run individual test files
python test_analyzer.py
python test_api.py
python test_video_comparison.py
```

## Architecture Overview

### Core Components

1. **Flask Application** (`app.py`): Factory pattern setup with blueprints
   - Main blueprint registered from `routes.py`
   - Extended routes from `routes_extended.py`

2. **Video Processing Pipeline** (`video_processing.py`):
   - OpenAI Vision API integration for content analysis
   - Face detection using OpenCV
   - Smart cropping based on detected subjects
   - MoviePy for video manipulation

3. **Data Persistence** (`database.py`):
   - Shelve-based local storage for video metadata
   - Stores analysis results and processing status

4. **Frontend** (modular JavaScript):
   - `/static/js/app.js`: Main application logic
   - `/static/js/api.js`: API client
   - `/static/js/ui.js`: UI interactions

### Key API Endpoints

- `POST /upload` - Upload video file
- `POST /analyze_video` - Trigger AI analysis
- `POST /generate_crop_suggestions` - Get crop recommendations
- `POST /convert_with_custom_area` - Convert with specific crop area
- `GET /get_video_status/<video_id>` - Check processing status
- `GET /download/<video_id>` - Download converted video

### DOOH Templates

Pre-configured sizes in `config.py`:
- 高雄版位: 3840×1526
- 忠孝商圈: 1440×960
- Standard 16:9, 4K, 9:16 portrait, 1:1 square, ultrawide

### Environment Variables

Required in `.env`:
- `OPENAI_API_KEY` - For AI vision analysis

### File Structure

- `/uploads/` - Original uploaded videos
- `/outputs/` - Converted video files
- `/static/` - Frontend assets
- `/templates/` - Flask HTML templates
- Video metadata stored in `video_data.db` (Shelve database)

## Important Considerations

1. **Port Configuration**: Default port is 5001 (see `config.py`)
2. **File Size Limit**: 500MB max upload
3. **Supported Formats**: .mp4, .avi, .mov, .mkv, .webm
4. **AI Analysis**: Limited to 90 frames for performance
5. **No formal testing framework** - Tests use basic Python assertions
6. **No linting tools** configured in requirements.txt