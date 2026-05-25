import hashlib
try:
    import langdetect
except ImportError:
    langdetect = None


LANG_MAP = {
    "ru": "Russian", "en": "English", "de": "German", "fr": "French",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "tr": "Turkish",
    "nl": "Dutch", "pl": "Polish", "uk": "Ukrainian", "he": "Hebrew",
    "hi": "Hindi", "th": "Thai", "vi": "Vietnamese",
}


def detect_language(text: str) -> dict:
    if langdetect is None:
        return {"error": "langdetect not installed"}
    try:
        lang = langdetect.detect(text)
        return {"language": lang, "name": LANG_MAP.get(lang, lang), "text_length": len(text)}
    except Exception as e:
        return {"error": str(e)}


def translate_text(text: str, target_lang: str = "en", source_lang: str = None) -> dict:
    """Translate text using LLM. Returns a prompt for the agent to translate."""
    if not text or not text.strip():
        return {"error": "Text is empty"}
    src = source_lang or "detected"
    return {
        "translation_prompt": f"Translate the following text from {src} to {target_lang}:\n\n{text}",
        "source_lang": src,
        "target_lang": target_lang,
        "note": "Pass this prompt to the LLM to get the translated text.",
    }


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="detect_language",
        description="Detect the language of a text string (e.g. 'ru', 'en', 'fr').",
        parameters={"type": "object", "properties": {
            "text": {"type": "string"},
        }},
        execute_fn=lambda text="": detect_language(text),
    )


def unregister_tools():
    from core.tool_registry import registry
    registry.unregister("detect_language")
