"""Image to parallax video conversion functionality"""
import tempfile
import os
from utils import download_file, get_image_dimensions, generate_job_id
from ffmpeg_utils import get_nvenc_params, execute_ffmpeg_pipeline


def create_parallax_video(image_url, duration, output_width=1920, output_height=1080, 
                         zoom_factor=1.2, pan_direction='right', intensity=0.5):
    """
    Create a parallax video with pseudo-3D effect from a static image
    
    Args:
        image_url: URL of the image file
        duration: Duration of the output video in seconds
        output_width: Width of the output video (default 1920)
        output_height: Height of the output video (default 1080)
        zoom_factor: Zoom level for parallax effect (default 1.2, range 1.1-2.0)
        pan_direction: Direction of panning ('left', 'right', 'up', 'down', 'zoom_in', 'zoom_out')
        intensity: Intensity of the parallax effect (default 0.5, range 0.1-1.0)
    
    Returns:
        bytes: Generated video data with parallax effect
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
        
        # Generate parallax effect filter
        parallax_filter = _generate_parallax_filter(
            img_width, img_height, output_width, output_height,
            duration, zoom_factor, pan_direction, intensity, job_id
        )
        
        # Build FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path
        ]
        
        # Add NVENC encoding parameters
        ffmpeg_cmd.extend(get_nvenc_params(preset='p4', cq=23))
        
        # Add video processing parameters with parallax effect
        ffmpeg_cmd.extend([
            '-vf', parallax_filter,
            '-t', str(duration),
            '-r', '30',
            output_path
        ])
        
        # Execute FFmpeg pipeline with dynamic timeout
        timeout = duration * 10 + 30  # Timeout based on duration
        output_data = execute_ffmpeg_pipeline(ffmpeg_cmd, output_path, timeout=timeout, job_id=job_id)
        
        return output_data


def _generate_parallax_filter(img_width, img_height, output_width, output_height, 
                            duration, zoom_factor, pan_direction, intensity, job_id):
    """
    Generate FFmpeg filter for parallax effect
    
    Args:
        img_width, img_height: Input image dimensions
        output_width, output_height: Output video dimensions
        duration: Video duration in seconds
        zoom_factor: Zoom level for parallax effect
        pan_direction: Direction of panning
        intensity: Intensity of the parallax effect
        job_id: Job ID for logging
    
    Returns:
        str: FFmpeg filter string for parallax effect
    """
    print(f"Job {job_id}: Creating parallax effect - {pan_direction} with intensity {intensity}")
    
    # Calculate the scaled dimensions to allow for movement
    # We need extra space around the image to create the parallax effect
    scale_factor = max(zoom_factor, 1.5)  # Ensure enough space for movement
    scaled_width = int(img_width * scale_factor)
    scaled_height = int(img_height * scale_factor)
    
    # Calculate movement range based on intensity
    max_movement_x = int((scaled_width - output_width) * intensity)
    max_movement_y = int((scaled_height - output_height) * intensity)
    
    # Generate movement expressions based on direction
    if pan_direction == 'right':
        x_expr = f"t/{duration}*{max_movement_x}"
        y_expr = f"({scaled_height}-{output_height})/2"
    elif pan_direction == 'left':
        x_expr = f"{max_movement_x}-t/{duration}*{max_movement_x}"
        y_expr = f"({scaled_height}-{output_height})/2"
    elif pan_direction == 'down':
        x_expr = f"({scaled_width}-{output_width})/2"
        y_expr = f"t/{duration}*{max_movement_y}"
    elif pan_direction == 'up':
        x_expr = f"({scaled_width}-{output_width})/2"
        y_expr = f"{max_movement_y}-t/{duration}*{max_movement_y}"
    elif pan_direction == 'zoom_in':
        # Zoom in effect - start from scaled size and crop to center
        zoom_start = 1.0
        zoom_end = zoom_factor
        zoom_expr = f"{zoom_start}+({zoom_end}-{zoom_start})*t/{duration}"
        x_expr = f"({scaled_width}-{output_width}*{zoom_expr})/2"
        y_expr = f"({scaled_height}-{output_height}*{zoom_expr})/2"
        return f"scale={scaled_width}:{scaled_height},crop={output_width}:{output_height}:({x_expr}):({y_expr})"
    elif pan_direction == 'zoom_out':
        # Zoom out effect
        zoom_start = zoom_factor
        zoom_end = 1.0
        zoom_expr = f"{zoom_start}+({zoom_end}-{zoom_start})*t/{duration}"
        x_expr = f"({scaled_width}-{output_width}*{zoom_expr})/2"
        y_expr = f"({scaled_height}-{output_height}*{zoom_expr})/2"
        return f"scale={scaled_width}:{scaled_height},crop={output_width}:{output_height}:({x_expr}):({y_expr})"
    else:
        # Default to right panning
        x_expr = f"t/{duration}*{max_movement_x}"
        y_expr = f"({scaled_height}-{output_height})/2"
    
    # Build the filter chain
    filter_chain = f"scale={scaled_width}:{scaled_height},crop={output_width}:{output_height}:({x_expr}):({y_expr})"
    
    print(f"Job {job_id}: Parallax filter: {filter_chain}")
    return filter_chain