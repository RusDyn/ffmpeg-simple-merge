# RunPod Serverless Video Merger Setup

## Files Structure
```
video-merger-runpod/
├── handler.py          # Main serverless handler
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
└── README.md          # This file
```

## Setup Steps

### 1. Create RunPod Account
- Go to [RunPod.io](https://runpod.io)
- Sign up and add some credits ($5-10 is plenty to start)

### 2. Build and Push Docker Image

```bash
# Clone/create your project directory
mkdir video-merger-runpod && cd video-merger-runpod

# Create the files (copy from artifacts above)
# handler.py, requirements.txt, Dockerfile

# Build the Docker image
docker build -t your-username/video-merger:latest .

# Push to Docker Hub (or use RunPod's registry)
docker push your-username/video-merger:latest
```

### 3. Create RunPod Serverless Endpoint

1. Go to RunPod Console → Serverless
2. Click "New Endpoint"
3. Configure:
   - **Name**: `video-merger`
   - **Docker Image**: `your-username/video-merger:latest`
   - **GPU Type**: RTX 4090 or A100 (for speed)
   - **Container Disk**: 10GB
   - **Memory**: 16GB
   - **Timeout**: 300 seconds (5 minutes)
   - **Idle Timeout**: 5 seconds (quick scale-down)

### 4. Get Your Endpoint Details
- **Endpoint ID**: Copy from the dashboard
- **API Key**: Get from RunPod settings

## Usage from n8n

### Video + Audio Merge:
**HTTP Request Node Configuration:**
- **Method**: POST
- **URL**: `https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer YOUR_RUNPOD_API_KEY",
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "input": {
      "action": "merge",
      "videoUrl": "https://example.com/video.mp4",
      "audioUrl": "https://example.com/audio.mp3"
    }
  }
  ```

### Image to Parallax Video:
**HTTP Request Node Configuration:**
- **Method**: POST
- **URL**: `https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync`
- **Headers**:
  ```json
  {
    "Authorization": "Bearer YOUR_RUNPOD_API_KEY",
    "Content-Type": "application/json"
  }
  ```
- **Body**:
  ```json
  {
    "input": {
      "action": "parallax",
      "imageUrl": "https://example.com/image.jpg",
      "duration": 10
    }
  }
  ```

### Response Handling:
Both endpoints return the same format:
```json
{
  "status": "COMPLETED",
  "output": {
    "video_data": "UklGRjIAAABXQVZFZm10...",
    "content_type": "video/mp4",
    "size_bytes": 1234567,
    "action": "merge" // or "parallax"
  }
}
```

## Performance Optimizations

The handler uses several speed optimizations:
- **ultrafast preset**: Fastest H.264 encoding
- **copy video stream**: When video doesn't need slowing down
- **lower quality settings**: CRF 28, 128k audio bitrate
- **efficient filtering**: Minimal filter chains
- **local processing**: No intermediate uploads

## Expected Performance
- **Video merge**: 5-15 seconds for 10-second videos
- **Parallax creation**: 8-20 seconds (depends on duration and image size)
- **Cost per video merge**: ~$0.02-0.05 per video
- **Cost per parallax video**: ~$0.03-0.08 per video
- **Cold start**: 10-30 seconds (first request after idle)

## Troubleshooting

### Container logs:
```bash
# Check RunPod logs in the dashboard for errors
```

### Test locally:
```python
# Create test_local.py
if __name__ == "__main__":
    event = {
        "input": {
            "videoUrl": "https://example.com/test.mp4",
            "audioUrl": "https://example.com/test.mp3"
        }
    }
    result = handler(event)
    print(result)
```

### Common issues:
- **Timeout**: Increase timeout in RunPod settings
- **Memory**: Use larger GPU instances if processing fails
- **Network**: Ensure URLs are publicly accessible

## Cost Optimization Tips
1. Use smaller GPU instances for development
2. Set aggressive idle timeouts (5-10 seconds)
3. Monitor usage in RunPod dashboard
4. Consider batch processing multiple videos