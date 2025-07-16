import runpod
import subprocess
import tempfile
import os
import json
import requests
from urllib.parse import urlparse
import uuid

def download_file(url, local_path):
    """Download file from URL to local path"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def get_media_duration(file_path):
    """Get duration of media file using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'csv=p=0', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            raise Exception(f"ffprobe failed: {result.stderr}")
    except Exception as e:
        print(f"Duration check failed: {e}")
        raise

def process_video(video_url, audio_url, video_volume=1.0, audio_volume=1.0):
    """Main video processing function"""
    job_id = str(uuid.uuid4())[:8]
    print(f"Job {job_id}: Starting process_video function")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Job {job_id}: Created temp directory: {temp_dir}")
            
            # File paths
            video_path = os.path.join(temp_dir, f"video_{job_id}.mp4")
            audio_path = os.path.join(temp_dir, f"audio_{job_id}.mp3")
            output_path = os.path.join(temp_dir, f"output_{job_id}.mp4")
            
            print(f"Job {job_id}: Video URL: {video_url}")
            print(f"Job {job_id}: Audio URL: {audio_url}")
            
            # Download files
            print(f"Job {job_id}: Downloading video...")
            if not download_file(video_url, video_path):
                raise Exception("Failed to download video file")
            
            print(f"Job {job_id}: Downloading audio...")
            if not download_file(audio_url, audio_path):
                raise Exception("Failed to download audio file")
            
            print(f"Job {job_id}: Files downloaded successfully")
            
            # Verify files
            video_size = os.path.getsize(video_path)
            audio_size = os.path.getsize(audio_path)
            print(f"Job {job_id}: Video file size: {video_size} bytes")
            print(f"Job {job_id}: Audio file size: {audio_size} bytes")
            
            # Get durations
            video_duration = get_media_duration(video_path)
            audio_duration = get_media_duration(audio_path)
            print(f"Job {job_id}: Video duration: {video_duration}s")
            print(f"Job {job_id}: Audio duration: {audio_duration}s")
            
            # Build FFmpeg command
            if audio_duration >= video_duration:
                speed_factor = video_duration / audio_duration
                print(f"Job {job_id}: Audio is longer, slowing video by factor: {speed_factor}")
                
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-hwaccel', 'cuda',  # GPU acceleration
                    '-hwaccel_output_format', 'cuda',
                    '-i', video_path,
                    '-i', audio_path,
                    '-c:v', 'h264_nvenc',
                    '-preset', 'p1',
                    '-cq', '28',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-filter_complex', 
                    f'[0:v]setpts=PTS*{1/speed_factor}[slowvideo];'
                    f'[0:a]atempo={speed_factor},volume={video_volume}[slowaudio];'
                    f'[1:a]volume={audio_volume}[newaudio];'
                    f'[slowaudio][newaudio]amix=inputs=2:duration=longest:weights=0.5 0.5[mixedaudio]',
                    '-map', '[slowvideo]',
                    '-map', '[mixedaudio]',
                    '-t', str(audio_duration),
                    output_path
                ]
            else:
                print(f"Job {job_id}: Video is longer, mixing audio")
                
                ffmpeg_cmd = [
                    'ffmpeg', '-y',
                    '-hwaccel', 'cuda',
                    '-i', video_path,
                    '-i', audio_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-filter_complex', f'[0:a]volume={video_volume}[originalvol];[1:a]volume={audio_volume}[newvol];[originalvol][newvol]amix=inputs=2:duration=first:weights=0.5 0.5[mixedaudio]',
                    '-map', '0:v:0',
                    '-map', '[mixedaudio]',
                    '-t', str(video_duration),
                    output_path
                ]
            
            print(f"Job {job_id}: Starting FFmpeg...")
            print(f"Command: {' '.join(ffmpeg_cmd)}")
            
            # Run FFmpeg
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                print(f"Job {job_id}: FFmpeg failed: {result.stderr}")
                raise Exception(f"FFmpeg processing failed: {result.stderr}")
            
            print(f"Job {job_id}: FFmpeg completed successfully")
            
            # Check output file
            if not os.path.exists(output_path):
                raise Exception("Output file was not created")
            
            output_size = os.path.getsize(output_path)
            if output_size == 0:
                raise Exception("Output file is empty")
            
            print(f"Job {job_id}: Output file size: {output_size} bytes")
            
            # Read file content
            print(f"Job {job_id}: Reading output file...")
            with open(output_path, 'rb') as f:
                file_data = f.read()
            
            print(f"Job {job_id}: Read {len(file_data)} bytes from file")
            
            if not file_data:
                raise Exception("File data is empty")
            
            print(f"Job {job_id}: Returning {len(file_data)} bytes")
            return file_data
    
    except Exception as e:
        print(f"Job {job_id}: ERROR - {str(e)}")
        import traceback
        print(f"Job {job_id}: Traceback: {traceback.format_exc()}")
        raise

def get_image_dimensions(image_path):
    """Get image width and height using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', image_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            for stream in data['streams']:
                if stream['codec_type'] == 'video':
                    return int(stream['width']), int(stream['height'])
        raise Exception(f"ffprobe failed: {result.stderr}")
    except Exception as e:
        print(f"Image dimension check failed: {e}")
        raise

def create_parallax_video(image_url, duration, output_width=1920, output_height=1080):
    """Create a parallax video from an image with proper scaling"""
    job_id = str(uuid.uuid4())[:8]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # File paths
        image_path = os.path.join(temp_dir, f"image_{job_id}.jpg")
        output_path = os.path.join(temp_dir, f"parallax_{job_id}.mp4")
        
        print(f"Parallax Job {job_id}: Starting image download and processing")
        print(f"Image URL: {image_url}")
        print(f"Duration: {duration}s")
        print(f"Output resolution: {output_width}x{output_height}")
        
        # Download image
        if not download_file(image_url, image_path):
            raise Exception("Failed to download image file")
        
        print(f"Job {job_id}: Image downloaded successfully")
        
        # Get image dimensions
        img_width, img_height = get_image_dimensions(image_path)
        print(f"Image dimensions: {img_width}x{img_height}")
        
        # Simple approach - just scale to exact output size
        print(f"Scaling {img_width}x{img_height} to {output_width}x{output_height}")
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-c:v', 'h264_nvenc',
            '-preset', 'p4', 
            '-cq', '23',
            '-pix_fmt', 'yuv420p',
            '-vf', f'scale={output_width}:{output_height}',  # Simple scale
            '-t', str(duration),
            '-r', '30',
            output_path
        ]
        
        print(f"Job {job_id}: Starting FFmpeg parallax processing...")
        print(f"Command: {' '.join(ffmpeg_cmd)}")
        
        # Run FFmpeg
        result = subprocess.run(
            ffmpeg_cmd, 
            capture_output=True, 
            text=True, 
            timeout=duration * 10 + 30  # Timeout based on duration
        )
        
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            raise Exception(f"FFmpeg parallax processing failed: {result.stderr}")
        
        print(f"Job {job_id}: Parallax processing completed successfully")
        
        # Check output file
        if not os.path.exists(output_path):
            raise Exception("Output parallax video was not created")
        
        output_size = os.path.getsize(output_path)
        if output_size == 0:
            raise Exception("Output parallax video is empty")
        
        print(f"Parallax output file size: {output_size} bytes")
        
        # Read output file
        with open(output_path, 'rb') as f:
            output_data = f.read()
        
        return output_data

def handler(event):
    """RunPod serverless handler with multiple endpoints"""
    try:
        # Parse input
        input_data = event.get("input", {})
        action = input_data.get("action", "merge")  # Default action is merge
        
        if action == "merge":
            # Video + Audio merging functionality
            video_url = input_data.get("videoUrl")
            audio_url = input_data.get("audioUrl")
            video_volume = input_data.get("videoVolume", 1.0)
            audio_volume = input_data.get("audioVolume", 1.0)
            
            if not video_url or not audio_url:
                return {
                    "error": "Both videoUrl and audioUrl are required for merge action"
                }
            
            # Validate URLs
            try:
                urlparse(video_url)
                urlparse(audio_url)
            except Exception:
                return {
                    "error": "Invalid URL format"
                }
            
            # Validate volume parameters
            try:
                video_volume = float(video_volume)
                audio_volume = float(audio_volume)
                if video_volume < 0 or video_volume > 2 or audio_volume < 0 or audio_volume > 2:
                    return {
                        "error": "Volume values must be between 0 and 2"
                    }
            except (ValueError, TypeError):
                return {
                    "error": "Invalid volume format"
                }
            
            # Process video
            print("Calling process_video function...")
            output_data = process_video(video_url, audio_url, video_volume, audio_volume)
            print(f"process_video returned: {type(output_data)}, length: {len(output_data) if output_data else 'None'}")
            
            # Validate output_data before encoding
            if output_data is None:
                return {
                    "error": "Video processing returned no data"
                }
            
            if not isinstance(output_data, bytes):
                return {
                    "error": f"Video processing returned invalid data type: {type(output_data)}"
                }
            
            if len(output_data) == 0:
                return {
                    "error": "Video processing returned empty data"
                }
            
            print(f"Processing successful, got {len(output_data)} bytes of video data")
            
            # Return base64 encoded result
            import base64
            try:
                print("Starting base64 encoding...")
                output_b64 = base64.b64encode(output_data).decode('utf-8')
                print(f"Base64 encoding successful, encoded {len(output_b64)} characters")
            except Exception as e:
                print(f"Base64 encoding error: {str(e)}")
                return {
                    "error": f"Base64 encoding failed: {str(e)}"
                }
            
            return {
                "output": {
                    "video_data": output_b64,
                    "content_type": "video/mp4",
                    "size_bytes": len(output_data),
                    "action": "merge"
                }
            }
            
        elif action == "parallax":
            # Image to parallax video functionality
            image_url = input_data.get("imageUrl")
            duration = input_data.get("duration", 10)  # Default 10 seconds
            width = input_data.get("width", 1920)  # Default 1920x1080
            height = input_data.get("height", 1080)
            
            if not image_url:
                return {
                    "error": "imageUrl is required for parallax action"
                }
            
            # Validate duration
            try:
                duration = float(duration)
                if duration <= 0 or duration > 60:  # Max 60 seconds
                    return {
                        "error": "Duration must be between 0 and 60 seconds"
                    }
            except (ValueError, TypeError):
                return {
                    "error": "Invalid duration format"
                }
            
            # Validate resolution
            try:
                width = int(width)
                height = int(height)
                if width < 480 or width > 4096 or height < 320 or height > 4096:
                    return {
                        "error": "Resolution must be between 480x320 and 4096x4096"
                    }
            except (ValueError, TypeError):
                return {
                    "error": "Invalid resolution format"
                }
            
            # Validate URL
            try:
                urlparse(image_url)
            except Exception:
                return {
                    "error": "Invalid image URL format"
                }
            
            # Create parallax video
            output_data = create_parallax_video(image_url, duration, width, height)
            
            # Return base64 encoded result
            import base64
            output_b64 = base64.b64encode(output_data).decode('utf-8')
            
            return {
                "output": {
                    "video_data": output_b64,
                    "content_type": "video/mp4",
                    "size_bytes": len(output_data),
                    "action": "parallax",
                    "duration": duration,
                    "resolution": f"{width}x{height}"
                }
            }
            
        else:
            return {
                "error": f"Unknown action: {action}. Supported actions: 'merge', 'parallax'"
            }
        
    except Exception as e:
        print(f"Handler error: {str(e)}")
        return {
            "error": str(e)
        }

# Start the serverless handler
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})