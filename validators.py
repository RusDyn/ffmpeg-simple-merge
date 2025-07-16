"""Input validation functions"""
from urllib.parse import urlparse


class InputValidator:
    """Handles input validation for different actions"""
    
    @staticmethod
    def validate_merge_inputs(input_data):
        """Validate inputs for merge action"""
        video_url = input_data.get("videoUrl")
        audio_url = input_data.get("audioUrl")
        video_volume = input_data.get("videoVolume", 1.0)
        audio_volume = input_data.get("audioVolume", 1.0)
        
        # Check required fields
        if not video_url or not audio_url:
            return False, "Both videoUrl and audioUrl are required for merge action", None
        
        # Validate URLs
        try:
            urlparse(video_url)
            urlparse(audio_url)
        except Exception:
            return False, "Invalid URL format", None
        
        # Validate volume parameters
        try:
            video_volume = float(video_volume)
            audio_volume = float(audio_volume)
            if video_volume < 0 or video_volume > 2 or audio_volume < 0 or audio_volume > 2:
                return False, "Volume values must be between 0 and 2", None
        except (ValueError, TypeError):
            return False, "Invalid volume format", None
        
        return True, None, {
            "video_url": video_url,
            "audio_url": audio_url,
            "video_volume": video_volume,
            "audio_volume": audio_volume
        }
    
    @staticmethod
    def validate_parallax_inputs(input_data):
        """Validate inputs for parallax action"""
        image_url = input_data.get("imageUrl")
        duration = input_data.get("duration", 10)
        width = input_data.get("width", 1920)
        height = input_data.get("height", 1080)
        
        # Check required fields
        if not image_url:
            return False, "imageUrl is required for parallax action", None
        
        # Validate URL
        try:
            urlparse(image_url)
        except Exception:
            return False, "Invalid image URL format", None
        
        # Validate duration
        try:
            duration = float(duration)
            if duration <= 0 or duration > 60:  # Max 60 seconds
                return False, "Duration must be between 0 and 60 seconds", None
        except (ValueError, TypeError):
            return False, "Invalid duration format", None
        
        # Validate resolution
        try:
            width = int(width)
            height = int(height)
            if width < 480 or width > 4096 or height < 320 or height > 4096:
                return False, "Resolution must be between 480x320 and 4096x4096", None
        except (ValueError, TypeError):
            return False, "Invalid resolution format", None
        
        return True, None, {
            "image_url": image_url,
            "duration": duration,
            "width": width,
            "height": height
        }