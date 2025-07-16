"""Utility functions for file operations and media processing"""
import subprocess
import requests
import uuid
import json


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


def get_image_dimensions(image_path):
    """Get image width and height using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', image_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            for stream in data['streams']:
                if stream['codec_type'] == 'video':
                    return int(stream['width']), int(stream['height'])
        raise Exception(f"ffprobe failed: {result.stderr}")
    except Exception as e:
        print(f"Image dimension check failed: {e}")
        raise


def generate_job_id():
    """Generate a unique job ID"""
    return str(uuid.uuid4())[:8]