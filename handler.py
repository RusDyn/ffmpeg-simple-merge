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

def process_video(video_url, audio_url):
    """Main video processing function"""
    job_id = str(uuid.uuid4())[:8]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # File paths
        video_path = os.path.join(temp_dir, f"video_{job_id}.mp4")
        audio_path = os.path.join(temp_dir, f"audio_{job_id}.mp3")
        output_path = os.path.join(temp_dir, f"output_{job_id}.mp4")
        
        print(f"Job {job_id}: Starting download and processing")
        print(f"Video URL: {video_url}")
        print(f"Audio URL: {audio_url}")
        
        # Download files
        if not download_file(video_url, video_path):
            raise Exception("Failed to download video file")
        
        if not download_file(audio_url, audio_path):
            raise Exception("Failed to download audio file")
        
        print(f"Job {job_id}: Files downloaded successfully")
        
        # Get durations
        video_duration = get_media_duration(video_path)
        audio_duration = get_media_duration(audio_path)
        
        print(f"Video duration: {video_duration}s")
        print(f"Audio duration: {audio_duration}s")
        
        final_duration = max(video_duration, audio_duration)
        print(f"Final output duration: {final_duration}s")
        
        # Build FFmpeg command with GPU acceleration
        if audio_duration >= video_duration:
            # Audio is longer - slow down video and mix audio
            speed_factor = video_duration / audio_duration
            print(f"Audio is longer. Slowing down video with factor: {speed_factor}")
            
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-hwaccel', 'cuda',  # GPU acceleration
                '-hwaccel_output_format', 'cuda',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'h264_nvenc',  # NVIDIA GPU encoder
                '-preset', 'p1',  # Fastest GPU preset
                '-cq', '28',  # Quality for NVENC
                '-c:a', 'aac',
                '-b:a', '128k',
                '-filter_complex', 
                f'[0:v]setpts=PTS*{1/speed_factor}[slowvideo];'
                f'[0:a]atempo={speed_factor}[slowaudio];'
                f'[slowaudio][1:a]amix=inputs=2:duration=longest[mixedaudio]',
                '-map', '[slowvideo]',
                '-map', '[mixedaudio]',
                '-t', str(audio_duration),
                output_path
            ]
        else:
            # Video is longer - keep video speed, mix audio
            print("Video is longer. Keeping video speed, mixing audio tracks")
            
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-hwaccel', 'cuda',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',  # Copy video stream (fastest)
                '-c:a', 'aac',
                '-b:a', '128k',
                '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first[mixedaudio]',
                '-map', '0:v:0',
                '-map', '[mixedaudio]',
                '-t', str(video_duration),
                output_path
            ]
        
        print(f"Job {job_id}: Starting FFmpeg processing...")
        print(f"Command: {' '.join(ffmpeg_cmd)}")
        
        # Run FFmpeg
        result = subprocess.run(
            ffmpeg_cmd, 
            capture_output=True, 
            text=True, 
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            raise Exception(f"FFmpeg processing failed: {result.stderr}")
        
        print(f"Job {job_id}: Processing completed successfully")
        
        # Check output file
        if not os.path.exists(output_path):
            raise Exception("Output file was not created")
        
        output_size = os.path.getsize(output_path)
        if output_size == 0:
            raise Exception("Output file is empty")
        
        print(f"Output file size: {output_size} bytes")
        
        # Read output file
        with open(output_path, 'rb') as f:
            output_data = f.read()
        
def create_parallax_video(image_url, duration):
    """Create a parallax video from an image"""
    job_id = str(uuid.uuid4())[:8]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # File paths
        image_path = os.path.join(temp_dir, f"image_{job_id}.jpg")
        output_path = os.path.join(temp_dir, f"parallax_{job_id}.mp4")
        
        print(f"Parallax Job {job_id}: Starting image download and processing")
        print(f"Image URL: {image_url}")
        print(f"Duration: {duration}s")
        
        # Download image
        if not download_file(image_url, image_path):
            raise Exception("Failed to download image file")
        
        print(f"Job {job_id}: Image downloaded successfully")
        
        # Create parallax video with slow zoom and pan effect
        # Enhanced parallax with multiple movement options
        
        # Calculate total frames
        fps = 30
        total_frames = int(duration * fps)
        
        # Create complex parallax effect:
        # 1. Slow zoom from 100% to 120%
        # 2. Gentle pan from left to right
        # 3. Slight vertical drift
        
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-loop', '1',  # Loop the image
            '-i', image_path,
            '-c:v', 'h264_nvenc',  # GPU encoding
            '-preset', 'p4',  # Good quality preset for NVENC
            '-cq', '23',  # High quality
            '-pix_fmt', 'yuv420p',  # Compatibility
            '-vf', 
            # Scale image larger than output for panning room
            f'scale=2304:1296:force_original_aspect_ratio=increase,'  # 20% larger than 1920x1080
            f'crop=2304:1296,'  # Crop to exact size
            # Zoompan filter for parallax effect
            f'zoompan='
            f'z=\'1+0.2*sin(2*PI*t/{duration})\':'  # Subtle breathing zoom
            f'x=\'iw/2-(iw/zoom/2)+50*sin(2*PI*t/{duration})\':'  # Horizontal pan
            f'y=\'ih/2-(ih/zoom/2)+20*sin(PI*t/{duration})\':'  # Gentle vertical drift
            f's=1920x1080:'  # Output size
            f'fps=30:'
            f'd={total_frames}',
            '-t', str(duration),
            '-r', '30',  # 30 fps
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
            
            # Process video
            output_data = process_video(video_url, audio_url)
            
            # Return base64 encoded result
            import base64
            output_b64 = base64.b64encode(output_data).decode('utf-8')
            
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
            
            # Validate URL
            try:
                urlparse(image_url)
            except Exception:
                return {
                    "error": "Invalid image URL format"
                }
            
            # Create parallax video
            output_data = create_parallax_video(image_url, duration)
            
            # Return base64 encoded result
            import base64
            output_b64 = base64.b64encode(output_data).decode('utf-8')
            
            return {
                "output": {
                    "video_data": output_b64,
                    "content_type": "video/mp4",
                    "size_bytes": len(output_data),
                    "action": "parallax",
                    "duration": duration
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