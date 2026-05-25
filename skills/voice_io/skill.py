"""Voice I/O Skill — STT via Whisper + TTS via Edge TTS."""
import os
import tempfile
import asyncio
from typing import Dict, Optional


def transcribe_audio(audio_path: str, language: str = "auto", model: str = "whisper-1") -> Dict:
    """Transcribe audio to text using OpenAI Whisper API.
    
    Requires OPENAI_API_KEY environment variable.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                language=None if language == "auto" else language,
            )
        
        return {
            "text": transcript.text,
            "language": language,
            "model": model,
        }
    except Exception as e:
        return {"error": f"Transcription failed: {str(e)}"}


async def speak_text(text: str, voice: str = "en-US-AriaNeural", output_path: str = None) -> Dict:
    """Convert text to speech using Edge TTS (free Microsoft voices).
    
    Available voices: en-US-AriaNeural, ru-RU-SvetlanaNeural, etc.
    See: edge-tts --list-voices
    """
    try:
        import edge_tts
    except ImportError:
        return {"error": "edge_tts not installed. Run: pip install edge-tts"}
    
    if not output_path:
        output_path = f"output/tts_{hash(text) % 10000}.mp3"
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        
        return {
            "audio_path": output_path,
            "text": text,
            "voice": voice,
            "duration_estimate": len(text) * 0.08,  # rough estimate
        }
    except Exception as e:
        return {"error": f"TTS failed: {str(e)}"}


def list_voices(language: str = None) -> Dict:
    """List available Edge TTS voices."""
    try:
        import edge_tts
        import asyncio
        
        async def _fetch():
            voices = await edge_tts.list_voices()
            if language:
                voices = [v for v in voices if language.lower() in v["Locale"].lower()]
            return voices[:20]  # Limit for brevity
        
        voices = asyncio.get_event_loop().run_until_complete(_fetch())
        
        return {
            "voices": [
                {"name": v["ShortName"], "locale": v["Locale"], "gender": v["Gender"]}
                for v in voices
            ],
            "count": len(voices),
        }
    except Exception as e:
        return {"error": f"Failed to list voices: {str(e)}"}


def register_tools():
    from core.tool_registry import registry
    
    registry.register(
        name="transcribe_audio",
        description="Transcribe audio file to text using Whisper API. Requires OPENAI_API_KEY.",
        parameters={
            "type": "object",
            "properties": {
                "audio_path": {"type": "string", "description": "Path to audio file (mp3, wav, m4a)"},
                "language": {"type": "string", "description": "Language code (e.g. 'ru', 'en') or 'auto'"},
                "model": {"type": "string", "default": "whisper-1"},
            },
            "required": ["audio_path"],
        },
        execute_fn=lambda audio_path="", language="auto", model="whisper-1": transcribe_audio(audio_path, language, model),
    )
    
    registry.register(
        name="speak_text",
        description="Convert text to speech using free Microsoft Edge voices. Output is MP3.",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "default": "en-US-AriaNeural"},
                "output_path": {"type": "string", "description": "Output MP3 path"},
            },
            "required": ["text"],
        },
        execute_fn=lambda text="", voice="en-US-AriaNeural", output_path=None: asyncio.get_event_loop().run_until_complete(
            speak_text(text, voice, output_path)
        ),
    )
    
    registry.register(
        name="list_tts_voices",
        description="List available text-to-speech voices.",
        parameters={
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Filter by language (e.g. 'ru', 'en')"},
            },
        },
        execute_fn=lambda language="": list_voices(language),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["transcribe_audio", "speak_text", "list_tts_voices"]:
        registry.unregister(name)
