# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Docker Commands
```bash
# Build the Docker image
docker build -t video-merger:latest .

# Run the container locally for testing
docker run --rm -it video-merger:latest

# Push to Docker Hub
docker push your-username/video-merger:latest
```

### Local Testing
```bash
# Install dependencies
pip3 install -r requirements.txt

# Test the handler locally
python3 -c "
from handler import handler
event = {
    'input': {
        'action': 'merge',
        'videoUrl': 'https://example.com/test.mp4',
        'audioUrl': 'https://example.com/test.mp3'
    }
}
result = handler(event)
print(result)
"
```

## Project Architecture

This is a **RunPod serverless handler** for video processing that provides two main functions:

1. **Video + Audio Merging** (`action: "merge"`)
   - Downloads video and audio files from URLs
   - Merges them using FFmpeg with CUDA acceleration
   - Handles duration mismatches by adjusting video speed or audio mixing
   - Returns base64-encoded MP4 video

2. **Image to Parallax Video** (`action: "parallax"`)
   - Downloads an image from URL
   - Creates a video by scaling the image to specified dimensions
   - Configurable duration, width, and height
   - Returns base64-encoded MP4 video

### Key Components

- **`handler.py`**: Main serverless handler with action routing
  - Routes requests to appropriate processing modules
  - Handles base64 encoding and response formatting
  - RunPod entry point

- **`merge.py`**: Video and audio merging functionality
  - `merge_video_audio()`: Handles video+audio merging with speed adjustment
  - Independent volume control for both tracks
  - Automatic duration matching

- **`parallax.py`**: Image to video conversion
  - `create_parallax_video()`: Creates static video from image
  - Configurable resolution and duration

- **`validators.py`**: Input validation for all actions
- **`utils.py`**: Shared utility functions

- **FFmpeg Processing**: Uses CUDA acceleration with optimized presets
  - Hardware acceleration: `h264_nvenc` codec with CUDA
  - Speed optimizations: `ultrafast` preset, CRF 28, 128k audio bitrate
  - Complex audio filtering for duration matching

- **File Management**: Uses temporary directories for processing
  - Downloads files locally before processing
  - Cleans up automatically after each job
  - Includes file validation and error handling

### Dependencies
- `runpod`: Serverless framework integration
- `requests`: File downloads from URLs
- `ffmpeg`: Video/audio processing (installed via system packages)

## RunPod Deployment

This application is designed to run on RunPod's serverless platform with:
- NVIDIA CUDA base image (Ubuntu 22.04)
- GPU acceleration (RTX 4090/A100 recommended)
- 10GB container disk, 16GB memory
- 300-second timeout for processing

The handler expects RunPod event format with `input` containing action-specific parameters.