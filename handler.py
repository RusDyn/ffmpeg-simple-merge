"""RunPod serverless handler for video processing"""
import runpod
import base64
from merge import merge_video_audio
from parallax import create_parallax_video
from validators import InputValidator


def handler(event):
    """RunPod serverless handler with multiple endpoints"""
    try:
        # Parse input
        input_data = event.get("input", {})
        action = input_data.get("action", "merge")  # Default action is merge
        
        if action == "merge":
            # Video + Audio merging functionality
            is_valid, error_msg, validated_inputs = InputValidator.validate_merge_inputs(input_data)
            
            if not is_valid:
                return {"error": error_msg}
            
            # Process video
            print("Calling merge_video_audio function...")
            output_data = merge_video_audio(
                validated_inputs["video_url"],
                validated_inputs["audio_url"],
                validated_inputs["video_volume"],
                validated_inputs["audio_volume"]
            )
            print(f"merge_video_audio returned: {type(output_data)}, length: {len(output_data) if output_data else 'None'}")
            
            # Validate output_data before encoding
            if output_data is None:
                return {
                    "error": "Video processing returned no data"
                }
            
            if not isinstance(output_data, bytes):
                return {
                    "error": f"Video processing returned invalid data type: {type(output_data)}"
                }
            
            if len(output_data) == 0:
                return {
                    "error": "Video processing returned empty data"
                }
            
            print(f"Processing successful, got {len(output_data)} bytes of video data")
            
            # Return base64 encoded result
            try:
                print("Starting base64 encoding...")
                output_b64 = base64.b64encode(output_data).decode('utf-8')
                print(f"Base64 encoding successful, encoded {len(output_b64)} characters")
            except Exception as e:
                print(f"Base64 encoding error: {str(e)}")
                return {
                    "error": f"Base64 encoding failed: {str(e)}"
                }
            
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
            is_valid, error_msg, validated_inputs = InputValidator.validate_parallax_inputs(input_data)
            
            if not is_valid:
                return {"error": error_msg}
            
            # Create parallax video
            output_data = create_parallax_video(
                validated_inputs["image_url"],
                validated_inputs["duration"],
                validated_inputs["width"],
                validated_inputs["height"],
                validated_inputs["zoom_factor"],
                validated_inputs["pan_direction"],
                validated_inputs["intensity"]
            )
            
            # Return base64 encoded result
            output_b64 = base64.b64encode(output_data).decode('utf-8')
            
            return {
                "output": {
                    "video_data": output_b64,
                    "content_type": "video/mp4",
                    "size_bytes": len(output_data),
                    "action": "parallax",
                    "duration": validated_inputs["duration"],
                    "resolution": f"{validated_inputs['width']}x{validated_inputs['height']}"
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