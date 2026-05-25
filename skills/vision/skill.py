"""Vision / Multimodal skill.

Analyze images using cloud vision models (GPT-4o, Gemini) via litellm,
or local LLaVA via Ollama.
"""
import base64
import os
from typing import Optional

from core.tool_registry import registry
from core.llm_gateway import LLMGateway


def _image_to_base64(image_path_or_url: str) -> tuple[str, str]:
    """Return (data_uri, media_type) for an image path or URL."""
    if image_path_or_url.startswith("http"):
        # Remote URL
        import httpx
        resp = httpx.get(image_path_or_url, timeout=30)
        resp.raise_for_status()
        media_type = resp.headers.get("content-type", "image/png")
        b64 = base64.b64encode(resp.content).decode("utf-8")
        return f"data:{media_type};base64,{b64}", media_type
    else:
        # Local file
        path = os.path.expanduser(image_path_or_url)
        with open(path, "rb") as f:
            data = f.read()
        ext = os.path.splitext(path)[1].lower()
        media_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(ext, "image/png")
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{media_type};base64,{b64}", media_type


def analyze_image(image_path_or_url: str, question: str = "Describe this image in detail.",
                  model: Optional[str] = None) -> dict:
    """Analyze an image using a multimodal LLM.

    Defaults to the configured primary model if it supports vision,
    otherwise falls back to openrouter/gpt-4o-mini.
    """
    try:
        data_uri, _ = _image_to_base64(image_path_or_url)
    except Exception as e:
        return {"success": False, "error": f"Failed to load image: {e}"}

    vision_model = model or os.environ.get("VISION_MODEL", "")
    if not vision_model:
        # Try to use primary model if it looks like a vision-capable model
        primary = os.environ.get("LLM_MODEL_PRIMARY", "openrouter/openai/gpt-4o-mini")
        if any(x in primary for x in ("gpt-4o", "gemini", "claude-3", "llava", "vision")):
            vision_model = primary
        else:
            vision_model = "openrouter/openai/gpt-4o-mini"

    # Use litellm for cloud models
    if vision_model.startswith("openrouter/") or vision_model.startswith("openai/") or vision_model.startswith("anthropic/"):
        actual_model = vision_model
        if actual_model.startswith("openrouter/"):
            actual_model = actual_model[len("openrouter/"):]
        try:
            import litellm
            api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
            response = litellm.completion(
                model=actual_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    }
                ],
                api_key=api_key,
                max_tokens=1024,
            )
            content = response.choices[0].message.content
            return {"success": True, "description": content, "model": vision_model}
        except Exception as e:
            return {"success": False, "error": f"LLM vision failed: {e}"}

    # Local Ollama fallback
    if "://" not in vision_model:
        try:
            import httpx
            ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
            resp = httpx.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": vision_model,
                    "messages": [
                        {"role": "user", "content": question, "images": [data_uri.split(",")[1]]}
                    ],
                    "stream": False,
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            return {"success": True, "description": content, "model": vision_model}
        except Exception as e:
            return {"success": False, "error": f"Ollama vision failed: {e}"}

    return {"success": False, "error": "No suitable vision model configured."}


def describe_screenshot() -> dict:
    """Placeholder: in full implementation this would integrate with browser_screenshot."""
    return {"success": False, "error": "Use browser_screenshot first, then analyze_image with the returned base64."}


def register_tools():
    registry.register(
        name="analyze_image",
        description="Analyze an image using a multimodal LLM (GPT-4o, Gemini, or local LLaVA).",
        parameters={
            "type": "object",
            "properties": {
                "image_path_or_url": {"type": "string", "description": "Local path or URL to image"},
                "question": {"type": "string", "description": "Question to ask about the image"},
                "model": {"type": "string", "description": "Optional vision model override"},
            },
            "required": ["image_path_or_url"],
        },
        execute_fn=analyze_image,
    )
    registry.register(
        name="describe_screenshot",
        description="Placeholder: describe a previously captured screenshot.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        execute_fn=describe_screenshot,
    )


def unregister_tools():
    registry.unregister("analyze_image")
    registry.unregister("describe_screenshot")
