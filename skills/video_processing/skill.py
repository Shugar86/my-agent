"""Video Processing Skill — FFmpeg-based video analysis and editing."""
import os
import json
import re
import subprocess
from fractions import Fraction
from typing import Dict, List, Optional
from pathlib import Path


def _parse_frame_rate(rate: Optional[str]) -> float:
    """Parse ffprobe r_frame_rate (e.g. '30/1') without eval."""
    if not rate or not isinstance(rate, str):
        return 0.0
    if not re.fullmatch(r"\d+/\d+", rate):
        return 0.0
    try:
        return float(Fraction(rate))
    except (ValueError, ZeroDivisionError):
        return 0.0


def extract_frames(video_path: str, output_dir: str = None, fps: float = 1.0, max_frames: int = 100) -> Dict:
    """Extract frames from video using FFmpeg.
    
    Requires ffmpeg installed and in PATH.
    """
    if not os.path.exists(video_path):
        return {"error": f"Video file not found: {video_path}"}
    
    try:
        # Check ffmpeg availability
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return {"error": "ffmpeg not found. Install ffmpeg and add to PATH."}
    except FileNotFoundError:
        return {"error": "ffmpeg not installed. Download from https://ffmpeg.org/download.html"}
    
    if not output_dir:
        output_dir = f"output/frames_{Path(video_path).stem}"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Extract frames at specified FPS
        pattern = os.path.join(output_dir, "frame_%04d.jpg")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vf", f"fps={fps},scale=640:-1",
            "-frames:v", str(max_frames),
            "-q:v", "2",
            pattern,
            "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return {"error": f"FFmpeg error: {result.stderr[:200]}"}
        
        frames = sorted([f for f in os.listdir(output_dir) if f.endswith('.jpg')])
        
        return {
            "output_dir": output_dir,
            "frames_count": len(frames),
            "frames": frames[:10],  # Preview first 10
            "fps": fps,
            "video_path": video_path,
        }
    except Exception as e:
        return {"error": f"Frame extraction failed: {str(e)}"}


def get_video_info(video_path: str) -> Dict:
    """Get video metadata using ffprobe."""
    if not os.path.exists(video_path):
        return {"error": f"Video file not found: {video_path}"}
    
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-show_streams", 
             "-print_format", "json", video_path],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode != 0:
            return {"error": f"ffprobe error: {result.stderr[:200]}"}
        
        info = json.loads(result.stdout)
        format_info = info.get("format", {})
        streams = info.get("streams", [])
        
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
        
        return {
            "filename": format_info.get("filename"),
            "duration": float(format_info.get("duration", 0)),
            "size_bytes": int(format_info.get("size", 0)),
            "format": format_info.get("format_name"),
            "video": {
                "codec": video_stream.get("codec_name"),
                "width": video_stream.get("width"),
                "height": video_stream.get("height"),
                "fps": _parse_frame_rate(video_stream.get("r_frame_rate", "0/1")),
            },
            "audio": {
                "codec": audio_stream.get("codec_name"),
                "sample_rate": audio_stream.get("sample_rate"),
                "channels": audio_stream.get("channels"),
            } if audio_stream else None,
        }
    except FileNotFoundError:
        return {"error": "ffprobe not installed. Install ffmpeg."}
    except Exception as e:
        return {"error": f"Failed to get video info: {str(e)}"}


def extract_audio(video_path: str, output_path: str = None) -> Dict:
    """Extract audio track from video as MP3."""
    if not os.path.exists(video_path):
        return {"error": f"Video file not found: {video_path}"}
    
    if not output_path:
        output_path = f"output/{Path(video_path).stem}.mp3"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    try:
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn",  # no video
            "-acodec", "libmp3lame",
            "-q:a", "2",
            output_path,
            "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return {"error": f"FFmpeg error: {result.stderr[:200]}"}
        
        return {
            "audio_path": output_path,
            "video_path": video_path,
        }
    except FileNotFoundError:
        return {"error": "ffmpeg not installed"}
    except Exception as e:
        return {"error": f"Audio extraction failed: {str(e)}"}


def trim_video(video_path: str, start: float, end: float, output_path: str = None) -> Dict:
    """Trim video to specified time range."""
    if not os.path.exists(video_path):
        return {"error": f"Video file not found: {video_path}"}
    
    if not output_path:
        output_path = f"output/{Path(video_path).stem}_trimmed.mp4"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    try:
        duration = end - start
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",  # copy without re-encoding (fast)
            output_path,
            "-y"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return {"error": f"FFmpeg error: {result.stderr[:200]}"}
        
        return {
            "output_path": output_path,
            "start": start,
            "end": end,
            "duration": duration,
        }
    except FileNotFoundError:
        return {"error": "ffmpeg not installed"}
    except Exception as e:
        return {"error": f"Trim failed: {str(e)}"}


def register_tools():
    from core.tool_registry import registry
    
    registry.register(
        name="extract_frames",
        description="Extract frames from video using FFmpeg. Requires ffmpeg.",
        parameters={
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "output_dir": {"type": "string"},
                "fps": {"type": "number", "default": 1.0},
                "max_frames": {"type": "integer", "default": 100},
            },
            "required": ["video_path"],
        },
        execute_fn=lambda video_path="", output_dir=None, fps=1.0, max_frames=100: extract_frames(video_path, output_dir, fps, max_frames),
    )
    
    registry.register(
        name="get_video_info",
        description="Get video metadata (duration, resolution, codec). Requires ffprobe.",
        parameters={
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
            },
            "required": ["video_path"],
        },
        execute_fn=lambda video_path="": get_video_info(video_path),
    )
    
    registry.register(
        name="extract_audio",
        description="Extract audio track from video as MP3. Requires ffmpeg.",
        parameters={
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "output_path": {"type": "string"},
            },
            "required": ["video_path"],
        },
        execute_fn=lambda video_path="", output_path=None: extract_audio(video_path, output_path),
    )
    
    registry.register(
        name="trim_video",
        description="Trim video to time range. Requires ffmpeg.",
        parameters={
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "start": {"type": "number", "description": "Start time in seconds"},
                "end": {"type": "number", "description": "End time in seconds"},
                "output_path": {"type": "string"},
            },
            "required": ["video_path", "start", "end"],
        },
        execute_fn=lambda video_path="", start=0, end=0, output_path=None: trim_video(video_path, start, end, output_path),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["extract_frames", "get_video_info", "extract_audio", "trim_video"]:
        registry.unregister(name)
