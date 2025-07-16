"""Video and audio processing functions"""
import subprocess
import tempfile
import os
import base64
from utils import download_file, get_media_duration, get_image_dimensions, generate_job_id


class VideoProcessor:
    """Handles video and audio merging operations"""
    
    @staticmethod
    def process_video(video_url, audio_url, video_volume=1.0, audio_volume=1.0):
        """Main video processing function"""
        job_id = generate_job_id()
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
                ffmpeg_cmd = VideoProcessor._build_merge_command(
                    video_path, audio_path, output_path,
                    video_duration, audio_duration,
                    video_volume, audio_volume, job_id
                )
                
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
    
    @staticmethod
    def _build_merge_command(video_path, audio_path, output_path, video_duration, 
                           audio_duration, video_volume, audio_volume, job_id):
        """Build FFmpeg command for merging video and audio"""
        if audio_duration >= video_duration:
            speed_factor = video_duration / audio_duration
            print(f"Job {job_id}: Audio is longer, slowing video by factor: {speed_factor}")
            
            return [
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
            
            return [
                'ffmpeg', '-y',
                '-hwaccel', 'cuda',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-filter_complex', 
                f'[0:a]volume={video_volume}[originalvol];'
                f'[1:a]volume={audio_volume}[newvol];'
                f'[originalvol][newvol]amix=inputs=2:duration=first:weights=0.5 0.5[mixedaudio]',
                '-map', '0:v:0',
                '-map', '[mixedaudio]',
                '-t', str(video_duration),
                output_path
            ]


class ParallaxProcessor:
    """Handles image to parallax video conversion"""
    
    @staticmethod
    def create_parallax_video(image_url, duration, output_width=1920, output_height=1080):
        """Create a parallax video from an image with proper scaling"""
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