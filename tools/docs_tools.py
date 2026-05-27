import os
from typing import Dict, Any


def create_document(title: str, content: str, format_type: str = "html",
                    metadata: dict = None) -> Dict[str, Any]:
    """Create document and return paths."""
    try:
        from skills.docs.skill import create_document as create_doc, convert_document

        doc = create_doc(title, content, format_type, metadata)

        results = {
            "html": None,
            "docx": None,
            "pdf": None,
            "txt": None,
            "success": True
        }

        html_path = f"output/{title.replace(' ', '_')}.html"
        results["html"] = convert_document(doc, html_path, "html")

        try:
            docx_path = f"output/{title.replace(' ', '_')}.docx"
            results["docx"] = convert_document(doc, docx_path, "docx")
        except Exception:
            pass

        try:
            pdf_path = f"output/{title.replace(' ', '_')}.pdf"
            results["pdf"] = convert_document(doc, pdf_path, "pdf")
        except Exception:
            pass

        return results
    except Exception as e:
        return {"error": str(e), "success": False}


def convert_to_format(input_path: str, output_format: str) -> str:
    """Convert document to specified format."""
    try:
        from skills.docs.skill import convert_document, create_document

        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()

        title = os.path.splitext(os.path.basename(input_path))[0]
        doc = create_document(title, content, "html")

        output_path = f"output/{title}.{output_format}"
        return convert_document(doc, output_path, output_format)
    except Exception as e:
        return f"Error: {str(e)}"


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="create_document",
        description="Create a document (HTML, DOCX, PDF, TXT) from content. Returns paths to all generated formats.",
        parameters={"type": "object", "properties": {
            "title": {"type": "string"},
            "content": {"type": "string"},
            "format_type": {"type": "string"},
            "metadata": {"type": "object"},
        }},
        execute_fn=create_document,
    )
    registry.register(
        name="convert_to_format",
        description="Convert a document file to another format (html, docx, pdf, txt)",
        parameters={"type": "object", "properties": {
            "input_path": {"type": "string"},
            "output_format": {"type": "string"},
        }},
        execute_fn=convert_to_format,
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["create_document", "convert_to_format"]:
        registry.unregister(name)
