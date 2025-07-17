"""Image to parallax video conversion functionality"""
import subprocess
import tempfile
import os
from utils import download_file, get_image_dimensions, generate_job_id


def create_parallax_video(image_url, duration, output_width=1920, output_height=1080):
    """
    Create a video from a static image with specified duration and resolution
    
    Args:
        image_url: URL of the image file
        duration: Duration of the output video in seconds
        output_width: Width of the output video (default 1920)
        output_height: Height of the output video (default 1080)
    
    Returns:
        bytes: Generated video data
    """
    job_id = generate_job_id()
    
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