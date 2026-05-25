import os
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None
try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None


def ocr_image(image_path: str, lang: str = "rus+eng") -> dict:
    from core.validation import validate_file_exists_or_error
    if pytesseract is None:
        return {"error": "pytesseract not installed. Run: pip install pytesseract"}
    if Image is None:
        return {"error": "Pillow not installed"}
    err = validate_file_exists_or_error(image_path, "image_path")
    if err:
        return {"error": err}
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        return {"text": text, "length": len(text), "language": lang}
    except Exception as e:
        return {"error": str(e)}


def ocr_pdf(pdf_path: str, lang: str = "rus+eng", dpi: int = 200) -> dict:
    from core.validation import validate_file_exists_or_error
    if convert_from_path is None:
        return {"error": "pdf2image not installed. Run: pip install pdf2image"}
    if pytesseract is None:
        return {"error": "pytesseract not installed"}
    err = validate_file_exists_or_error(pdf_path, "pdf_path")
    if err:
        return {"error": err}
    try:
        images = convert_from_path(pdf_path, dpi=dpi)
        all_text = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img, lang=lang)
            all_text.append({"page": i + 1, "text": text})
        return {"pages": all_text, "total_pages": len(all_text),
                "total_chars": sum(len(p["text"]) for p in all_text)}
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="ocr_image",
        description="Extract text from an image file using OCR. Supports Russian and English.",
        parameters={"type": "object", "properties": {
            "image_path": {"type": "string"},
            "lang": {"type": "string"},
        }},
        execute_fn=lambda image_path="", lang="rus+eng": ocr_image(image_path, lang),
    )
    registry.register(
        name="ocr_pdf",
        description="Extract text from all pages of a PDF file using OCR.",
        parameters={"type": "object", "properties": {
            "pdf_path": {"type": "string"},
            "lang": {"type": "string"},
            "dpi": {"type": "integer"},
        }},
        execute_fn=lambda pdf_path="", lang="rus+eng", dpi=200: ocr_pdf(pdf_path, lang, dpi),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["ocr_image", "ocr_pdf"]:
        registry.unregister(name)
