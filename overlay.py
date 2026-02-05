"""Circular picture-in-picture overlay functionality"""
import tempfile
import os
from utils import download_file, get_media_duration, generate_job_id
from ffmpeg_utils import execute_ffmpeg_pipeline


def overlay_pip(background_url, overlay_url, position="bottom_right", size=200,
                margin=20, border_width=3, border_color="#ffffff"):
    """
    Create a video with circular picture-in-picture overlay

    Args:
        background_url: URL of the background video (B-roll)
        overlay_url: URL of the overlay video (avatar)
        position: Position of PiP - bottom_right, bottom_left, top_right, top_left
        size: Diameter of the circular PiP in pixels
        margin: Margin from edge in pixels
        border_width: Width of the border around the circle
        border_color: Color of the border (hex format)

    Returns:
        bytes: Processed video data
    """
    job_id = generate_job_id()
    print(f"Job {job_id}: Starting overlay_pip process")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Job {job_id}: Created temp directory: {temp_dir}")

            # File paths
            background_path = os.path.join(temp_dir, f"background_{job_id}.mp4")
            overlay_path = os.path.join(temp_dir, f"overlay_{job_id}.mp4")
            output_path = os.path.join(temp_dir, f"output_{job_id}.mp4")

            print(f"Job {job_id}: Background URL: {background_url}")
            print(f"Job {job_id}: Overlay URL: {overlay_url}")

            # Download files
            print(f"Job {job_id}: Downloading background video...")
            if not download_file(background_url, background_path):
                raise Exception("Failed to download background video")

            print(f"Job {job_id}: Downloading overlay video...")
            if not download_file(overlay_url, overlay_path):
                raise Exception("Failed to download overlay video")

            print(f"Job {job_id}: Files downloaded successfully")

            # Verify files
            bg_size = os.path.getsize(background_path)
            ov_size = os.path.getsize(overlay_path)
            print(f"Job {job_id}: Background file size: {bg_size} bytes")
            print(f"Job {job_id}: Overlay file size: {ov_size} bytes")

            # Get durations
            bg_duration = get_media_duration(background_path)
            ov_duration = get_media_duration(overlay_path)
            print(f"Job {job_id}: Background duration: {bg_duration}s")
            print(f"Job {job_id}: Overlay duration: {ov_duration}s")

            # Build FFmpeg command
            ffmpeg_cmd = _build_overlay_command(
                background_path, overlay_path, output_path,
                position, size, margin, border_width, border_color,
                job_id
            )

            # Execute FFmpeg pipeline (longer timeout for complex filter)
            file_data = execute_ffmpeg_pipeline(ffmpeg_cmd, output_path, timeout=300, job_id=job_id)

            print(f"Job {job_id}: Returning {len(file_data)} bytes")
            return file_data

    except Exception as e:
        print(f"Job {job_id}: ERROR - {str(e)}")
        import traceback
        print(f"Job {job_id}: Traceback: {traceback.format_exc()}")
        raise


def _calculate_position(position, size, margin, output_width=1920, output_height=1080):
    """Calculate X, Y coordinates for overlay position"""
    # Account for border in total size
    total_size = size

    positions = {
        "bottom_right": (output_width - total_size - margin, output_height - total_size - margin),
        "bottom_left": (margin, output_height - total_size - margin),
        "top_right": (output_width - total_size - margin, margin),
        "top_left": (margin, margin),
    }

    return positions.get(position, positions["bottom_right"])


def _hex_to_rgb(hex_color):
    """Convert hex color to RGB values"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _build_overlay_command(background_path, overlay_path, output_path,
                           position, size, margin, border_width, border_color,
                           job_id):
    """Build FFmpeg command for circular PiP overlay"""

    x_pos, y_pos = _calculate_position(position, size, margin)
    radius = size // 2
    center = radius

    # Convert border color to RGB
    r, g, b = _hex_to_rgb(border_color)

    print(f"Job {job_id}: PiP position: ({x_pos}, {y_pos}), size: {size}px, radius: {radius}px")

    # Build filter complex for circular mask with optional border
    # 1. Scale overlay to target size
    # 2. Create circular mask using geq filter
    # 3. Overlay on background at calculated position

    if border_width > 0:
        # With border: create a slightly larger circle for border, then overlay the main circle
        border_radius = radius
        inner_radius = radius - border_width

        filter_complex = (
            # Scale overlay video to size
            f"[1:v]scale={size}:{size}[scaled];"
            # Create alpha mask for circle (geq makes pixels outside circle transparent)
            f"[scaled]format=yuva420p,"
            f"geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':"
            f"a='if(lte(pow(X-{center},2)+pow(Y-{center},2),pow({inner_radius},2)),255,0)'[circle];"
            # Create border circle (solid color)
            f"color=c=0x{border_color.lstrip('#')}:s={size}x{size}:d=1[border_color];"
            f"[border_color]format=yuva420p,"
            f"geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':"
            f"a='if(lte(pow(X-{center},2)+pow(Y-{center},2),pow({border_radius},2)),"
            f"if(gt(pow(X-{center},2)+pow(Y-{center},2),pow({inner_radius},2)),255,0),0)'[border_mask];"
            # Overlay border on background
            f"[0:v][border_mask]overlay={x_pos}:{y_pos}:shortest=1[with_border];"
            # Overlay video circle on top
            f"[with_border][circle]overlay={x_pos}:{y_pos}:shortest=1[out]"
        )
    else:
        # Without border: simpler filter
        filter_complex = (
            # Scale overlay video to size
            f"[1:v]scale={size}:{size}[scaled];"
            # Create alpha mask for circle
            f"[scaled]format=yuva420p,"
            f"geq=lum='p(X,Y)':cb='p(X,Y)':cr='p(X,Y)':"
            f"a='if(lte(pow(X-{center},2)+pow(Y-{center},2),pow({radius},2)),255,0)'[circle];"
            # Overlay on background
            f"[0:v][circle]overlay={x_pos}:{y_pos}:shortest=1[out]"
        )

    cmd = [
        'ffmpeg', '-y',
        '-i', background_path,
        '-i', overlay_path,
        '-filter_complex', filter_complex,
        '-map', '[out]',
        '-map', '0:a?',  # Keep background audio if present
        '-c:v', 'h264_nvenc',
        '-preset', 'p4',
        '-cq', '23',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_path
    ]

    return cmd
