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
        zoom_factor = input_data.get("zoomFactor", 1.2)
        pan_direction = input_data.get("panDirection", "right")
        intensity = input_data.get("intensity", 0.5)
        
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
        
        # Validate zoom factor
        try:
            zoom_factor = float(zoom_factor)
            if zoom_factor < 1.1 or zoom_factor > 2.0:
                return False, "Zoom factor must be between 1.1 and 2.0", None
        except (ValueError, TypeError):
            return False, "Invalid zoom factor format", None
        
        # Validate pan direction
        valid_directions = ['left', 'right', 'up', 'down', 'zoom_in', 'zoom_out']
        if pan_direction not in valid_directions:
            return False, f"Pan direction must be one of: {', '.join(valid_directions)}", None
        
        # Validate intensity
        try:
            intensity = float(intensity)
            if intensity < 0.1 or intensity > 1.0:
                return False, "Intensity must be between 0.1 and 1.0", None
        except (ValueError, TypeError):
            return False, "Invalid intensity format", None
        
        return True, None, {
            "image_url": image_url,
            "duration": duration,
            "width": width,
            "height": height,
            "zoom_factor": zoom_factor,
            "pan_direction": pan_direction,
            "intensity": intensity
        }

    @staticmethod
    def validate_overlay_pip_inputs(input_data):
        """Validate inputs for overlay_pip action"""
        background_url = input_data.get("backgroundUrl")
        overlay_url = input_data.get("overlayUrl")
        position = input_data.get("position", "bottom_right")
        size = input_data.get("size", 200)
        margin = input_data.get("margin", 20)
        border_width = input_data.get("borderWidth", 3)
        border_color = input_data.get("borderColor", "#ffffff")

        # Check required fields
        if not background_url:
            return False, "backgroundUrl is required for overlay_pip action", None
        if not overlay_url:
            return False, "overlayUrl is required for overlay_pip action", None

        # Validate URLs
        try:
            urlparse(background_url)
            urlparse(overlay_url)
        except Exception:
            return False, "Invalid URL format", None

        # Validate position
        valid_positions = ['bottom_right', 'bottom_left', 'top_right', 'top_left']
        if position not in valid_positions:
            return False, f"Position must be one of: {', '.join(valid_positions)}", None

        # Validate size
        try:
            size = int(size)
            if size < 50 or size > 800:
                return False, "Size must be between 50 and 800 pixels", None
        except (ValueError, TypeError):
            return False, "Invalid size format", None

        # Validate margin
        try:
            margin = int(margin)
            if margin < 0 or margin > 200:
                return False, "Margin must be between 0 and 200 pixels", None
        except (ValueError, TypeError):
            return False, "Invalid margin format", None

        # Validate border width
        try:
            border_width = int(border_width)
            if border_width < 0 or border_width > 20:
                return False, "Border width must be between 0 and 20 pixels", None
        except (ValueError, TypeError):
            return False, "Invalid border width format", None

        # Validate border color (hex format)
        if not isinstance(border_color, str):
            return False, "Border color must be a string", None
        border_color = border_color.lstrip('#')
        if len(border_color) != 6:
            return False, "Border color must be in hex format (e.g., #ffffff)", None
        try:
            int(border_color, 16)
        except ValueError:
            return False, "Invalid hex color format", None
        border_color = f"#{border_color}"

        return True, None, {
            "background_url": background_url,
            "overlay_url": overlay_url,
            "position": position,
            "size": size,
            "margin": margin,
            "border_width": border_width,
            "border_color": border_color
        }

    @staticmethod
    def validate_concat_inputs(input_data):
        """Validate inputs for concat action"""
        segments = input_data.get("segments")
        width = input_data.get("width", 1920)
        height = input_data.get("height", 1080)

        # Check required fields
        if not segments:
            return False, "segments array is required for concat action", None

        if not isinstance(segments, list):
            return False, "segments must be an array", None

        if len(segments) == 0:
            return False, "segments array cannot be empty", None

        if len(segments) > 50:
            return False, "Maximum 50 segments allowed", None

        # Validate each segment
        validated_segments = []
        for i, segment in enumerate(segments):
            if not isinstance(segment, dict):
                return False, f"Segment {i} must be an object", None

            url = segment.get("url")
            if not url:
                return False, f"Segment {i} missing 'url' field", None

            try:
                urlparse(url)
            except Exception:
                return False, f"Segment {i} has invalid URL format", None

            trim_start = segment.get("trim_start", 0)
            trim_end = segment.get("trim_end")

            # Validate trim_start
            try:
                trim_start = float(trim_start)
                if trim_start < 0:
                    return False, f"Segment {i} trim_start cannot be negative", None
            except (ValueError, TypeError):
                return False, f"Segment {i} has invalid trim_start format", None

            # Validate trim_end if provided
            if trim_end is not None:
                try:
                    trim_end = float(trim_end)
                    if trim_end <= trim_start:
                        return False, f"Segment {i} trim_end must be greater than trim_start", None
                except (ValueError, TypeError):
                    return False, f"Segment {i} has invalid trim_end format", None

            validated_segments.append({
                "url": url,
                "trim_start": trim_start,
                "trim_end": trim_end
            })

        # Validate resolution
        try:
            width = int(width)
            height = int(height)
            if width < 480 or width > 4096 or height < 320 or height > 4096:
                return False, "Resolution must be between 480x320 and 4096x4096", None
        except (ValueError, TypeError):
            return False, "Invalid resolution format", None

        return True, None, {
            "segments": validated_segments,
            "width": width,
            "height": height
        }