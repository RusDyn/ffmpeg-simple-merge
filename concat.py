"""Video concatenation functionality"""
import tempfile
import os
from utils import download_file, generate_job_id
from ffmpeg_utils import execute_ffmpeg_pipeline, run_ffmpeg_command


def concat_videos(segments, width=1920, height=1080):
    """
    Concatenate multiple video segments with optional trimming

    Args:
        segments: List of dicts with 'url', optional 'trim_start', 'trim_end'
                  Example: [{"url": "https://...", "trim_start": 0, "trim_end": 10.5}]
        width: Output video width (default 1920)
        height: Output video height (default 1080)

    Returns:
        bytes: Concatenated video data
    """
    job_id = generate_job_id()
    print(f"Job {job_id}: Starting concat process with {len(segments)} segments")

    if not segments:
        raise Exception("No segments provided for concatenation")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Job {job_id}: Created temp directory: {temp_dir}")

            segment_paths = []
            processed_paths = []

            # Download and process each segment
            for i, segment in enumerate(segments):
                url = segment.get("url")
                if not url:
                    raise Exception(f"Segment {i} missing 'url' field")

                trim_start = segment.get("trim_start", 0)
                trim_end = segment.get("trim_end")

                # Download segment
                input_path = os.path.join(temp_dir, f"segment_{job_id}_{i}_input.mp4")
                processed_path = os.path.join(temp_dir, f"segment_{job_id}_{i}_processed.mp4")

                print(f"Job {job_id}: Downloading segment {i}: {url}")
                if not download_file(url, input_path):
                    raise Exception(f"Failed to download segment {i}")

                segment_paths.append(input_path)

                # Process segment (trim + normalize resolution)
                _process_segment(
                    input_path, processed_path,
                    trim_start, trim_end,
                    width, height,
                    job_id, i
                )

                processed_paths.append(processed_path)

            # Create concat list file
            concat_list_path = os.path.join(temp_dir, f"concat_list_{job_id}.txt")
            with open(concat_list_path, 'w') as f:
                for path in processed_paths:
                    f.write(f"file '{path}'\n")

            print(f"Job {job_id}: Created concat list with {len(processed_paths)} segments")

            # Concatenate all segments
            output_path = os.path.join(temp_dir, f"output_{job_id}.mp4")
            ffmpeg_cmd = _build_concat_command(concat_list_path, output_path)

            # Execute FFmpeg pipeline (longer timeout for multiple segments)
            timeout = max(300, len(segments) * 60)  # At least 5 min, +1 min per segment
            file_data = execute_ffmpeg_pipeline(ffmpeg_cmd, output_path, timeout=timeout, job_id=job_id)

            print(f"Job {job_id}: Returning {len(file_data)} bytes")
            return file_data

    except Exception as e:
        print(f"Job {job_id}: ERROR - {str(e)}")
        import traceback
        print(f"Job {job_id}: Traceback: {traceback.format_exc()}")
        raise


def _process_segment(input_path, output_path, trim_start, trim_end, width, height, job_id, segment_index):
    """Process a single segment: trim and normalize resolution"""
    print(f"Job {job_id}: Processing segment {segment_index}")

    # Build filter for scaling and padding to exact resolution
    # scale to fit within target, then pad to exact size
    scale_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,"
        f"setsar=1"
    )

    cmd = ['ffmpeg', '-y']

    # Add trim parameters if specified
    if trim_start > 0:
        cmd.extend(['-ss', str(trim_start)])

    cmd.extend(['-i', input_path])

    if trim_end is not None:
        duration = trim_end - trim_start
        cmd.extend(['-t', str(duration)])

    # Apply scaling filter and encode
    cmd.extend([
        '-vf', scale_filter,
        '-c:v', 'h264_nvenc',
        '-preset', 'p4',
        '-cq', '23',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-ar', '44100',  # Normalize audio sample rate
        '-ac', '2',      # Stereo audio
        output_path
    ])

    stdout, stderr, returncode = run_ffmpeg_command(cmd, timeout=120, job_id=f"{job_id}-seg{segment_index}")

    if returncode != 0:
        raise Exception(f"Failed to process segment {segment_index}: {stderr}")

    # Verify output
    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise Exception(f"Segment {segment_index} processing produced no output")

    print(f"Job {job_id}: Segment {segment_index} processed successfully")


def _build_concat_command(concat_list_path, output_path):
    """Build FFmpeg command for concatenation using concat demuxer"""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        '-c:v', 'h264_nvenc',
        '-preset', 'p4',
        '-cq', '23',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        output_path
    ]

    return cmd
