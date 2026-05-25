import os
from openai import OpenAI


def transcribe_audio(audio_path: str, language: str = "ru", model: str = "whisper-1") -> dict:
    try:
        client = OpenAI()
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=f,
                language=language,
                response_format="verbose_json",
            )
        return {
            "text": transcript.text,
            "duration": getattr(transcript, "duration", None),
            "language": language,
            "segments": getattr(transcript, "segments", []),
        }
    except Exception as e:
        return {"error": str(e)}


def translate_audio(audio_path: str, model: str = "whisper-1") -> dict:
    try:
        client = OpenAI()
        with open(audio_path, "rb") as f:
            transcript = client.audio.translations.create(
                model=model,
                file=f,
                response_format="verbose_json",
            )
        return {
            "text": transcript.text,
            "duration": getattr(transcript, "duration", None),
        }
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="transcribe_audio",
        description="Transcribe audio file to text using OpenAI Whisper. Supports Russian and many other languages.",
        parameters={"type": "object", "properties": {
            "audio_path": {"type": "string"},
            "language": {"type": "string"},
        }},
        execute_fn=lambda audio_path="", language="ru": transcribe_audio(audio_path, language),
    )
    registry.register(
        name="translate_audio",
        description="Translate audio file to English text using OpenAI Whisper.",
        parameters={"type": "object", "properties": {
            "audio_path": {"type": "string"},
        }},
        execute_fn=lambda audio_path="": translate_audio(audio_path),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["transcribe_audio", "translate_audio"]:
        registry.unregister(name)
