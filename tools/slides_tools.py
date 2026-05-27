import json
import os
from typing import Dict, Any, List

def _load_deck_from_path(html_path: str) -> Dict[str, Any] | str:
    """Load deck metadata from deck.json adjacent to HTML output."""
    if os.path.isdir(html_path):
        deck_dir = html_path
    elif os.path.isfile(html_path):
        deck_dir = os.path.dirname(html_path) or "."
    else:
        return f"Error: html_path not found: {html_path}"

    deck_json_path = os.path.join(deck_dir, "deck.json")
    if not os.path.isfile(deck_json_path):
        return "Error: deck.json not found. Run create_presentation first."

    with open(deck_json_path, encoding="utf-8") as f:
        return json.load(f)


def create_presentation(title: str, slides: list, theme: dict = None) -> Dict[str, Any]:
    """Create HTML presentation and return paths."""
    try:
        from skills.slides.skill import create_slide_deck, save_slide_html, export_to_pptx
        
        deck = create_slide_deck(title, slides, theme)
        html_dir = save_slide_html(deck)
        
        # Try to export to PPTX
        try:
            pptx_path = export_to_pptx(deck, f"output/{title.replace(' ', '_')}.pptx")
        except ImportError:
            pptx_path = None
        
        return {
            "html_dir": html_dir,
            "pptx_path": pptx_path,
            "slide_count": len(slides),
            "success": True
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def export_pptx(html_path: str, output_path: str) -> str:
    """Export HTML slides to PPTX."""
    deck_or_error = _load_deck_from_path(html_path)
    if isinstance(deck_or_error, str):
        return deck_or_error
    try:
        from skills.slides.skill import export_to_pptx
        result = export_to_pptx(deck_or_error, output_path)
        return result
    except ImportError as e:
        return f"Error: python-pptx not installed. {e}"
    except Exception as e:
        return f"Error: {str(e)}"


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="create_presentation",
        description="Create an HTML slide deck presentation from structured slide data. Returns paths to HTML and PPTX.",
        parameters={"type": "object", "properties": {
            "title": {"type": "string"},
            "slides": {"type": "array", "items": {"type": "object"}},
            "theme": {"type": "object"},
        }},
        execute_fn=create_presentation,
    )
    registry.register(
        name="export_pptx",
        description="Export HTML slides to PPTX format",
        parameters={"type": "object", "properties": {
            "html_path": {"type": "string"},
            "output_path": {"type": "string"},
        }},
        execute_fn=export_pptx,
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["create_presentation", "export_pptx"]:
        registry.unregister(name)
