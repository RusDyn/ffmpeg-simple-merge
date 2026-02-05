# FFmpeg Simple Merge - RunPod Serverless Video Processor

A high-performance, GPU-accelerated video processing service that runs on RunPod serverless infrastructure. This service provides four main functionalities:

1. **Video + Audio Merging**: Combine video and audio files with automatic duration matching and independent volume control
2. **Image to Parallax Video**: Convert static images into dynamic video content with pseudo-3D parallax effects
3. **Circular PiP Overlay**: Create picture-in-picture videos with circular avatar overlays on B-roll footage
4. **Video Concatenation**: Concatenate multiple video segments with optional trimming and resolution normalization

## 🚀 Features

- **GPU-accelerated processing** using NVIDIA CUDA and h264_nvenc
- **Automatic duration matching** for video/audio sync
- **Independent volume control** for video and audio tracks during merge
- **Flexible audio mixing** with customizable volume levels (0-2x)
- **Smart audio balancing** to prevent clipping when mixing tracks
- **Flexible resolution support** (480x320 to 4096x4096)
- **Parallax effects** with configurable pan directions, zoom, and intensity
- **Circular PiP overlays** with customizable position, size, and border styling
- **Video concatenation** with per-segment trimming and resolution normalization
- **Base64 encoded output** for easy integration
- **Optimized for speed** with ultrafast presets and efficient filtering
- **Serverless scalability** with automatic scaling based on demand

## 📁 Project Structure

```
ffmpeg-simple-merge/
├── handler.py          # Main serverless handler (routes all actions)
├── merge.py            # Video/audio merging logic
├── parallax.py         # Image to video conversion
├── overlay.py          # Circular PiP overlay logic
├── concat.py           # Video concatenation logic
├── validators.py       # Input validation for all actions
├── utils.py            # Shared utilities (download, duration, etc.)
├── ffmpeg_utils.py     # FFmpeg command utilities
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container configuration
├── README.md           # This documentation
└── CLAUDE.md           # Claude Code guidance
```

## 🛠️ Installation & Setup

### Prerequisites

- Docker installed on your system
- RunPod account with credits
- Docker Hub account (or access to RunPod registry)

### 1. Create RunPod Account

1. Go to [RunPod.io](https://runpod.io)
2. Sign up and add credits ($5-10 is sufficient to start)
3. Navigate to your dashboard

### 2. Build and Push Docker Image

```bash
# Clone the repository
git clone <repository-url>
cd ffmpeg-simple-merge

# Build the Docker image
docker build -t your-username/ffmpeg-simple-merge:latest .

# Push to Docker Hub
docker push your-username/ffmpeg-simple-merge:latest
```

### 3. Create RunPod Serverless Endpoint

1. Go to RunPod Console → Serverless
2. Click "New Endpoint"
3. Configure the endpoint:
   - **Name**: `ffmpeg-simple-merge`
   - **Docker Image**: `your-username/ffmpeg-simple-merge:latest`
   - **GPU Type**: RTX 4090 or A100 (recommended for speed)
   - **Container Disk**: 10GB
   - **Memory**: 16GB
   - **Timeout**: 300 seconds (5 minutes)
   - **Idle Timeout**: 5 seconds (for quick scale-down)

### 4. Get Your Endpoint Details

- **Endpoint ID**: Copy from the RunPod dashboard
- **API Key**: Get from RunPod Settings → API Keys

## 🎯 Usage Examples

### Video + Audio Merge

Merge a video file with an audio file, automatically handling duration mismatches and providing independent volume control for both tracks:

#### cURL Example

```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "merge",
      "videoUrl": "https://example.com/video.mp4",
      "audioUrl": "https://example.com/audio.mp3",
      "videoVolume": 0.8,
      "audioVolume": 1.2
    }
  }'
```

#### Python Example

```python
import requests
import base64

def merge_video_audio(video_url, audio_url, endpoint_id, api_key, video_volume=1.0, audio_volume=1.0):
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "action": "merge",
            "videoUrl": video_url,
            "audioUrl": audio_url,
            "videoVolume": video_volume,
            "audioVolume": audio_volume
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("status") == "COMPLETED":
        # Decode base64 video data
        video_data = base64.b64decode(result["output"]["video_data"])
        
        # Save to file
        with open("merged_video.mp4", "wb") as f:
            f.write(video_data)
            
        print(f"Video saved! Size: {len(video_data)} bytes")
        return video_data
    else:
        print(f"Error: {result}")
        return None

# Usage
merge_video_audio(
    "https://example.com/video.mp4",
    "https://example.com/audio.mp3",
    "your-endpoint-id",
    "your-api-key",
    video_volume=0.8,  # Reduce original video audio
    audio_volume=1.2   # Boost additional audio
)
```

#### JavaScript Example

```javascript
async function mergeVideoAudio(videoUrl, audioUrl, endpointId, apiKey, videoVolume = 1.0, audioVolume = 1.0) {
    const response = await fetch(`https://api.runpod.ai/v2/${endpointId}/runsync`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            input: {
                action: 'merge',
                videoUrl: videoUrl,
                audioUrl: audioUrl,
                videoVolume: videoVolume,
                audioVolume: audioVolume
            }
        })
    });
    
    const result = await response.json();
    
    if (result.status === 'COMPLETED') {
        // Convert base64 to blob
        const videoData = atob(result.output.video_data);
        const videoBlob = new Blob([videoData], { type: 'video/mp4' });
        
        // Create download link
        const url = URL.createObjectURL(videoBlob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'merged_video.mp4';
        a.click();
        
        return videoBlob;
    } else {
        console.error('Error:', result);
        return null;
    }
}
```

#### Volume Control Features

The merge action provides sophisticated volume control for professional audio mixing:

- **videoVolume**: Controls the original video's audio track volume (default: 1.0)
- **audioVolume**: Controls the additional audio file volume (default: 1.0)
- **Range**: 0.0 to 2.0 (0 = muted, 1.0 = original, 2.0 = double volume)
- **Smart Mixing**: Automatically balances audio levels to prevent clipping
- **Use Cases**:
  - Background music: Set `videoVolume: 1.0, audioVolume: 0.3`
  - Voice-over: Set `videoVolume: 0.2, audioVolume: 1.0`
  - Equal mix: Set both to `1.0` (auto-balanced to 0.5 each)
  - Replace audio: Set `videoVolume: 0.0, audioVolume: 1.0`

**Example - Adding background music:**
```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "merge",
      "videoUrl": "https://example.com/video.mp4",
      "audioUrl": "https://example.com/background-music.mp3",
      "videoVolume": 1.0,
      "audioVolume": 0.3
    }
  }'
```

**Example - Voice-over narration:**
```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "merge",
      "videoUrl": "https://example.com/video.mp4",
      "audioUrl": "https://example.com/narration.mp3",
      "videoVolume": 0.2,
      "audioVolume": 1.0
    }
  }'
```

### Image to Parallax Video

Convert a static image into a dynamic video with pseudo-3D parallax effects, configurable pan directions, zoom, and intensity:

#### cURL Example

```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "parallax",
      "imageUrl": "https://example.com/image.jpg",
      "duration": 15,
      "width": 1920,
      "height": 1080,
      "zoomFactor": 1.3,
      "panDirection": "zoom_in",
      "intensity": 0.7
    }
  }'
```

#### Python Example

```python
import requests
import base64

def create_parallax_video(image_url, duration=10, width=1920, height=1080, 
                         zoom_factor=1.2, pan_direction='right', intensity=0.5, 
                         endpoint_id, api_key):
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "action": "parallax",
            "imageUrl": image_url,
            "duration": duration,
            "width": width,
            "height": height,
            "zoomFactor": zoom_factor,
            "panDirection": pan_direction,
            "intensity": intensity
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("status") == "COMPLETED":
        # Decode base64 video data
        video_data = base64.b64decode(result["output"]["video_data"])
        
        # Save to file
        filename = f"parallax_video_{width}x{height}_{duration}s.mp4"
        with open(filename, "wb") as f:
            f.write(video_data)
            
        print(f"Parallax video saved as {filename}! Size: {len(video_data)} bytes")
        return video_data
    else:
        print(f"Error: {result}")
        return None

# Usage examples
create_parallax_video(
    "https://example.com/landscape.jpg",
    duration=20,
    width=1920,
    height=1080,
    zoom_factor=1.5,
    pan_direction="zoom_in",
    intensity=0.8,
    endpoint_id="your-endpoint-id",
    api_key="your-api-key"
)
```

#### Parallax Effect Parameters

The parallax action supports various parameters to create different pseudo-3D effects:

- **zoomFactor**: Controls the zoom level (1.1-2.0, default: 1.2)
  - Higher values create more pronounced zoom effects
  - Used for zoom_in and zoom_out directions
- **panDirection**: Direction of the parallax effect
  - `'right'`: Pan from left to right (default)
  - `'left'`: Pan from right to left
  - `'up'`: Pan from bottom to top
  - `'down'`: Pan from top to bottom
  - `'zoom_in'`: Gradual zoom into the image
  - `'zoom_out'`: Gradual zoom out from the image
- **intensity**: Controls the strength of the parallax effect (0.1-1.0, default: 0.5)
  - Lower values create subtle movement
  - Higher values create more dramatic effects

**Example combinations:**
```json
{
  "panDirection": "right",
  "intensity": 0.3,
  "zoomFactor": 1.2
}  // Subtle right pan

{
  "panDirection": "zoom_in",
  "intensity": 0.8,
  "zoomFactor": 1.5
}  // Dramatic zoom in effect

{
  "panDirection": "up",
  "intensity": 0.6,
  "zoomFactor": 1.3
}  // Upward pan with medium intensity
```

### Circular PiP Overlay

Create picture-in-picture videos with a circular avatar overlay on B-roll footage. Perfect for talking-head videos with dynamic backgrounds:

#### cURL Example

```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "overlay_pip",
      "backgroundUrl": "https://example.com/broll.mp4",
      "overlayUrl": "https://example.com/avatar.mp4",
      "position": "bottom_right",
      "size": 200,
      "margin": 20,
      "borderWidth": 3,
      "borderColor": "#ffffff"
    }
  }'
```

#### Python Example

```python
import requests
import base64

def create_pip_video(background_url, overlay_url, endpoint_id, api_key,
                     position='bottom_right', size=200, margin=20,
                     border_width=3, border_color='#ffffff'):
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "action": "overlay_pip",
            "backgroundUrl": background_url,
            "overlayUrl": overlay_url,
            "position": position,
            "size": size,
            "margin": margin,
            "borderWidth": border_width,
            "borderColor": border_color
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    if result.get("status") == "COMPLETED":
        video_data = base64.b64decode(result["output"]["video_data"])
        with open("pip_video.mp4", "wb") as f:
            f.write(video_data)
        print(f"PiP video saved! Size: {len(video_data)} bytes")
        return video_data
    else:
        print(f"Error: {result}")
        return None

# Usage - Avatar in bottom-right corner
create_pip_video(
    "https://example.com/nature-broll.mp4",
    "https://example.com/talking-avatar.mp4",
    "your-endpoint-id",
    "your-api-key",
    position="bottom_right",
    size=180,
    border_width=3,
    border_color="#ffffff"
)
```

#### PiP Overlay Parameters

- **position**: Corner placement of the circular overlay
  - `'bottom_right'`: Bottom-right corner (default)
  - `'bottom_left'`: Bottom-left corner
  - `'top_right'`: Top-right corner
  - `'top_left'`: Top-left corner
- **size**: Diameter of the circular overlay in pixels (50-800, default: 200)
- **margin**: Distance from edge in pixels (0-200, default: 20)
- **borderWidth**: Width of the white border around circle (0-20, default: 3)
- **borderColor**: Hex color of the border (default: #ffffff)

**Use Cases:**
- Talking-head videos with B-roll backgrounds
- Tutorial videos with presenter in corner
- News-style presentations
- Gaming streams with facecam

### Video Concatenation

Concatenate multiple video segments into a single video with optional trimming and automatic resolution normalization:

#### cURL Example

```bash
curl -X POST https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "action": "concat",
      "segments": [
        {"url": "https://example.com/intro.mp4", "trim_start": 0, "trim_end": 5},
        {"url": "https://example.com/main.mp4", "trim_start": 2, "trim_end": 30},
        {"url": "https://example.com/outro.mp4"}
      ],
      "width": 1920,
      "height": 1080
    }
  }'
```

#### Python Example

```python
import requests
import base64

def concat_videos(segments, endpoint_id, api_key, width=1920, height=1080):
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "input": {
            "action": "concat",
            "segments": segments,
            "width": width,
            "height": height
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    if result.get("status") == "COMPLETED":
        video_data = base64.b64decode(result["output"]["video_data"])
        with open("concatenated.mp4", "wb") as f:
            f.write(video_data)
        print(f"Concatenated video saved! Size: {len(video_data)} bytes")
        return video_data
    else:
        print(f"Error: {result}")
        return None

# Usage - Combine intro, main content, and outro
segments = [
    {"url": "https://example.com/intro.mp4", "trim_start": 0, "trim_end": 5},
    {"url": "https://example.com/talking-head.mp4", "trim_start": 10, "trim_end": 25},
    {"url": "https://example.com/broll.mp4"},  # Full video, no trimming
    {"url": "https://example.com/outro.mp4", "trim_start": 0, "trim_end": 3}
]

concat_videos(segments, "your-endpoint-id", "your-api-key")
```

#### Concatenation Parameters

- **segments**: Array of segment objects (required, max 50 segments)
  - `url`: URL of the video segment (required)
  - `trim_start`: Start time in seconds (optional, default: 0)
  - `trim_end`: End time in seconds (optional, uses full video if not specified)
- **width**: Output video width (480-4096, default: 1920)
- **height**: Output video height (320-4096, default: 1080)

**Features:**
- Automatic resolution normalization (all segments scaled/padded to target resolution)
- Audio sample rate normalization (44100 Hz stereo)
- Preserves aspect ratio with letterboxing/pillarboxing when needed
- GPU-accelerated encoding

### n8n Integration

For n8n workflow automation:

#### HTTP Request Node Configuration

**For Video Merge:**
- **Method**: POST
- **URL**: `https://api.runpod.ai/v2/{{$json.endpointId}}/runsync`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer {{$json.apiKey}}",
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "input": {
      "action": "merge",
      "videoUrl": "{{$json.videoUrl}}",
      "audioUrl": "{{$json.audioUrl}}",
      "videoVolume": "{{$json.videoVolume}}",
      "audioVolume": "{{$json.audioVolume}}"
    }
  }
  ```

**For Parallax Video:**
- **Method**: POST
- **URL**: `https://api.runpod.ai/v2/{{$json.endpointId}}/runsync`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer {{$json.apiKey}}",
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "input": {
      "action": "parallax",
      "imageUrl": "{{$json.imageUrl}}",
      "duration": {{$json.duration}},
      "width": {{$json.width}},
      "height": {{$json.height}}
    }
  }
  ```

**For Overlay PiP:**
- **Method**: POST
- **URL**: `https://api.runpod.ai/v2/{{$json.endpointId}}/runsync`
- **Body**:
  ```json
  {
    "input": {
      "action": "overlay_pip",
      "backgroundUrl": "{{$json.backgroundUrl}}",
      "overlayUrl": "{{$json.overlayUrl}}",
      "position": "bottom_right",
      "size": 180,
      "margin": 20,
      "borderWidth": 3,
      "borderColor": "#ffffff"
    }
  }
  ```

**For Video Concatenation:**
- **Method**: POST
- **URL**: `https://api.runpod.ai/v2/{{$json.endpointId}}/runsync`
- **Body**:
  ```json
  {
    "input": {
      "action": "concat",
      "segments": {{JSON.stringify($json.segments)}},
      "width": 1920,
      "height": 1080
    }
  }
  ```

## 📊 API Documentation

### Merge Action

**Endpoint**: `POST /v2/{endpoint_id}/runsync`

**Request Body**:
```json
{
  "input": {
    "action": "merge",
    "videoUrl": "string (required)",
    "audioUrl": "string (required)",
    "videoVolume": "number (optional, default: 1.0, range: 0-2)",
    "audioVolume": "number (optional, default: 1.0, range: 0-2)"
  }
}
```

**Response**:
```json
{
  "status": "COMPLETED",
  "output": {
    "video_data": "base64_encoded_video_data",
    "content_type": "video/mp4",
    "size_bytes": 1234567,
    "action": "merge"
  }
}
```

### Parallax Action

**Endpoint**: `POST /v2/{endpoint_id}/runsync`

**Request Body**:
```json
{
  "input": {
    "action": "parallax",
    "imageUrl": "string (required)",
    "duration": "number (default: 10, max: 60)",
    "width": "number (default: 1920, range: 480-4096)",
    "height": "number (default: 1080, range: 320-4096)",
    "zoomFactor": "number (default: 1.2, range: 1.1-2.0)",
    "panDirection": "string (default: 'right', options: 'left', 'right', 'up', 'down', 'zoom_in', 'zoom_out')",
    "intensity": "number (default: 0.5, range: 0.1-1.0)"
  }
}
```

**Response**:
```json
{
  "status": "COMPLETED",
  "output": {
    "video_data": "base64_encoded_video_data",
    "content_type": "video/mp4",
    "size_bytes": 1234567,
    "action": "parallax",
    "duration": 10,
    "resolution": "1920x1080",
    "zoom_factor": 1.2,
    "pan_direction": "right",
    "intensity": 0.5
  }
}
```

### Overlay PiP Action

**Endpoint**: `POST /v2/{endpoint_id}/runsync`

**Request Body**:
```json
{
  "input": {
    "action": "overlay_pip",
    "backgroundUrl": "string (required) - B-roll or background video URL",
    "overlayUrl": "string (required) - Avatar or overlay video URL",
    "position": "string (default: 'bottom_right', options: 'bottom_right', 'bottom_left', 'top_right', 'top_left')",
    "size": "number (default: 200, range: 50-800) - Circle diameter in pixels",
    "margin": "number (default: 20, range: 0-200) - Distance from edge in pixels",
    "borderWidth": "number (default: 3, range: 0-20) - Border thickness in pixels",
    "borderColor": "string (default: '#ffffff') - Hex color for border"
  }
}
```

**Response**:
```json
{
  "status": "COMPLETED",
  "output": {
    "video_data": "base64_encoded_video_data",
    "content_type": "video/mp4",
    "size_bytes": 1234567,
    "action": "overlay_pip"
  }
}
```

### Concat Action

**Endpoint**: `POST /v2/{endpoint_id}/runsync`

**Request Body**:
```json
{
  "input": {
    "action": "concat",
    "segments": [
      {
        "url": "string (required) - Video segment URL",
        "trim_start": "number (default: 0) - Start time in seconds",
        "trim_end": "number (optional) - End time in seconds"
      }
    ],
    "width": "number (default: 1920, range: 480-4096)",
    "height": "number (default: 1080, range: 320-4096)"
  }
}
```

**Response**:
```json
{
  "status": "COMPLETED",
  "output": {
    "video_data": "base64_encoded_video_data",
    "content_type": "video/mp4",
    "size_bytes": 1234567,
    "action": "concat",
    "segment_count": 3,
    "resolution": "1920x1080"
  }
}
```

### Error Response

```json
{
  "status": "FAILED",
  "error": "Error description"
}
```

## 🔧 Local Development

### Prerequisites

- Python 3.8+
- FFmpeg installed
- NVIDIA GPU with CUDA support (optional but recommended)

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Test the handler locally
python3 -c "
from handler import handler
event = {
    'input': {
        'action': 'merge',
        'videoUrl': 'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4',
        'audioUrl': 'https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3'
    }
}
result = handler(event)
print(result)
"
```

### Testing Different Actions

```python
# Test video merge
merge_test = {
    'input': {
        'action': 'merge',
        'videoUrl': 'https://example.com/video.mp4',
        'audioUrl': 'https://example.com/audio.mp3'
    }
}

# Test parallax video
parallax_test = {
    'input': {
        'action': 'parallax',
        'imageUrl': 'https://example.com/image.jpg',
        'duration': 15,
        'width': 1280,
        'height': 720
    }
}
```

## ⚡ Performance Optimizations

The service includes several performance optimizations:

- **GPU Acceleration**: Uses NVIDIA CUDA with h264_nvenc codec
- **Efficient Presets**: Utilizes p1/p4 presets for optimal speed/quality balance
- **Smart Processing**: Copies video streams when possible to avoid re-encoding
- **Memory Management**: Uses temporary directories with automatic cleanup
- **Optimized Settings**: CRF 23-28, 128k audio bitrate for balanced output

## 📈 Expected Performance

| Operation | Processing Time | Cost Estimate | Notes |
|-----------|----------------|---------------|-------|
| Video Merge (10s) | 5-15 seconds | $0.02-0.05 | Depends on duration mismatch |
| Parallax Video (10s) | 8-20 seconds | $0.03-0.08 | Depends on image size |
| Overlay PiP (10s) | 10-25 seconds | $0.04-0.10 | Complex filter chain |
| Concat (5 segments) | 20-60 seconds | $0.08-0.20 | Depends on segment count/length |
| Cold Start | 10-30 seconds | Included | First request after idle |

## 🐛 Troubleshooting

### Common Issues

1. **Timeout Errors**
   - Increase timeout in RunPod endpoint settings
   - Use smaller input files for testing
   - Check if URLs are accessible

2. **Memory Issues**
   - Upgrade to larger GPU instances (A100 recommended)
   - Reduce output resolution for parallax videos
   - Process shorter duration videos

3. **Network Issues**
   - Ensure input URLs are publicly accessible
   - Check for CORS restrictions
   - Verify URL formats are correct

4. **Processing Errors**
   - Check RunPod logs in dashboard
   - Verify input file formats (MP4, MP3, JPG, PNG supported)
   - Ensure adequate container disk space

### Debugging

```bash
# Check container logs in RunPod dashboard
# Or run locally with verbose output:
python3 handler.py
```

### Testing Locally

```python
# Create test_local.py
from handler import handler

# Test merge functionality
merge_event = {
    "input": {
        "action": "merge",
        "videoUrl": "https://example.com/test.mp4",
        "audioUrl": "https://example.com/test.mp3",
        "videoVolume": 0.8,
        "audioVolume": 1.2
    }
}

# Test parallax functionality
parallax_event = {
    "input": {
        "action": "parallax",
        "imageUrl": "https://example.com/test.jpg",
        "duration": 10,
        "width": 1920,
        "height": 1080
    }
}

# Run tests
merge_result = handler(merge_event)
parallax_result = handler(parallax_event)

print("Merge result:", merge_result)
print("Parallax result:", parallax_result)
```

## 💰 Cost Optimization Tips

1. **Choose Appropriate GPU**: Use RTX 4090 for development, A100 for production
2. **Set Idle Timeouts**: Use 5-10 second idle timeouts for quick scale-down
3. **Monitor Usage**: Track usage in RunPod dashboard
4. **Batch Processing**: Process multiple videos in sequence when possible
5. **Optimize Settings**: Use lower quality settings for draft/preview videos

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section above
- Review RunPod documentation
- Check container logs in RunPod dashboard
- Ensure all URLs are publicly accessible

---

**Note**: This service is optimized for RunPod's serverless infrastructure. For other deployment platforms, you may need to modify the Docker configuration and handler setup.