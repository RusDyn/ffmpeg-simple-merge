"""Shared FFmpeg utilities for video processing"""
import subprocess
import os


def run_ffmpeg_command(cmd, timeout=120, job_id=None):
    """
    Execute FFmpeg command with standard error handling
    
    Args:
        cmd: List of command arguments
        timeout: Command timeout in seconds
        job_id: Optional job ID for logging
    
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    job_prefix = f"Job {job_id}: " if job_id else ""
    
    print(f"{job_prefix}Starting FFmpeg...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            print(f"{job_prefix}FFmpeg failed: {result.stderr}")
        else:
            print(f"{job_prefix}FFmpeg completed successfully")
            
        return result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired:
        error_msg = f"FFmpeg command timed out after {timeout} seconds"
        print(f"{job_prefix}ERROR - {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        print(f"{job_prefix}ERROR - FFmpeg execution failed: {str(e)}")
        raise


def validate_output_file(file_path, job_id=None):
    """
    Validate that output file exists and is not empty
    
    Args:
        file_path: Path to the output file
        job_id: Optional job ID for logging
    
    Returns:
        int: File size in bytes
    
    Raises:
        Exception: If file doesn't exist or is empty
    """
    job_prefix = f"Job {job_id}: " if job_id else ""
    
    if not os.path.exists(file_path):
        raise Exception("Output file was not created")
    
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise Exception("Output file is empty")
    
    print(f"{job_prefix}Output file size: {file_size} bytes")
    return file_size


def read_video_file(file_path, job_id=None):
    """
    Read video file and return its contents
    
    Args:
        file_path: Path to the video file
        job_id: Optional job ID for logging
    
    Returns:
        bytes: File contents
    """
    job_prefix = f"Job {job_id}: " if job_id else ""
    
    print(f"{job_prefix}Reading output file...")
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    print(f"{job_prefix}Read {len(file_data)} bytes from file")
    
    if not file_data:
        raise Exception("File data is empty")
    
    return file_data


def get_nvenc_params(preset='p4', cq=23):
    """
    Get NVIDIA encoder parameters
    
    Args:
        preset: NVENC preset (p1-p7, where p1 is fastest)
        cq: Constant quality value (0-51, lower is better)
    
    Returns:
        list: FFmpeg parameters for NVENC
    """
    return [
        '-c:v', 'h264_nvenc',
        '-preset', preset,
        '-cq', str(cq),
        '-pix_fmt', 'yuv420p'
    ]


def get_cuda_params():
    """
    Get CUDA hardware acceleration parameters
    
    Returns:
        list: FFmpeg parameters for CUDA acceleration
    """
    return [
        '-hwaccel', 'cuda',
        '-hwaccel_output_format', 'cuda'
    ]


def build_base_command(inputs=None, output=None, use_cuda=True, overwrite=True):
    """
    Build base FFmpeg command structure
    
    Args:
        inputs: List of input file paths or None
        output: Output file path or None
        use_cuda: Whether to use CUDA acceleration
        overwrite: Whether to overwrite existing files
    
    Returns:
        list: Base FFmpeg command
    """
    cmd = ['ffmpeg']
    
    if overwrite:
        cmd.append('-y')
    
    if use_cuda and inputs:
        cmd.extend(get_cuda_params())
    
    if inputs:
        for input_file in inputs:
            cmd.extend(['-i', input_file])
    
    return cmd


def execute_ffmpeg_pipeline(cmd, output_path, timeout=120, job_id=None):
    """
    Execute FFmpeg command and validate output
    
    Args:
        cmd: FFmpeg command list
        output_path: Expected output file path
        timeout: Command timeout in seconds
        job_id: Optional job ID for logging
    
    Returns:
        bytes: Output video data
    
    Raises:
        Exception: If processing fails
    """
    # Run FFmpeg
    stdout, stderr, returncode = run_ffmpeg_command(cmd, timeout, job_id)
    
    if returncode != 0:
        raise Exception(f"FFmpeg processing failed: {stderr}")
    
    # Validate output
    validate_output_file(output_path, job_id)
    
    # Read and return file data
    return read_video_file(output_path, job_id)