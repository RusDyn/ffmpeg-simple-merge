# FFmpeg Simple Merge - RunPod Serverless Video Processor

A high-performance, GPU-accelerated video processing service that runs on RunPod serverless infrastructure. This service provides two main functionalities:

1. **Video + Audio Merging**: Combine video and audio files with automatic duration matching and independent volume control
2. **Image to Parallax Video**: Convert static images into dynamic video content

## 🚀 Features

- **GPU-accelerated processing** using NVIDIA CUDA and h264_nvenc
- **Automatic duration matching** for video/audio sync
- **Independent volume control** for video and audio tracks during merge
- **Flexible audio mixing** with customizable volume levels (0-2x)
- **Smart audio balancing** to prevent clipping when mixing tracks
- **Flexible resolution support** (480x320 to 4096x4096)
- **Base64 encoded output** for easy integration
- **Optimized for speed** with ultrafast presets and efficient filtering
- **Serverless scalability** with automatic scaling based on demand

## 📁 Project Structure

```
ffmpeg-simple-merge/
├── handler.py          # Main serverless handler
├── merge.py           # Video/audio merging logic
├── parallax.py        # Image to video conversion
├── validators.py      # Input validation
├── utils.py           # Shared utilities
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container configuration
├── README.md          # This documentation
└── CLAUDE.md          # Claude Code guidance
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

Convert a static image into a video with specified duration and resolution:

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
      "height": 1080
    }
  }'
```

#### Python Example

```python
import requests
import base64

def create_parallax_video(image_url, duration=10, width=1920, height=1080, endpoint_id, api_key):
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
            "height": height
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

# Usage
create_parallax_video(
    "https://example.com/landscape.jpg",
    duration=20,
    width=1920,
    height=1080,
    endpoint_id="your-endpoint-id",
    api_key="your-api-key"
)
```

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
    "action": "parallax",
    "duration": 10,
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