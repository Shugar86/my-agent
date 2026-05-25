"""Tests for Vision / Multimodal skill."""
import pytest
from unittest.mock import patch, MagicMock
from skills.vision.skill import analyze_image


def test_analyze_image_load_failure():
    result = analyze_image("/nonexistent/path.png")
    assert result["success"] is False
    assert "Failed to load image" in result["error"]


def test_analyze_image_with_mock_litellm():
    with patch("litellm.completion") as mock_litellm:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "A cat sitting on a mat."
        mock_litellm.return_value = mock_response

        # Create a dummy image file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png_data")
            path = f.name

        result = analyze_image(path, question="What is in this image?")
        assert result["success"] is True
        assert "cat" in result["description"].lower()
        mock_litellm.assert_called_once()


def test_analyze_image_ollama_fallback():
    with patch("httpx.post") as mock_post:
        mock_post.return_value.json.return_value = {"message": {"content": "It is a dog."}}
        mock_post.return_value.raise_for_status = MagicMock()

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"fake_png_data")
            path = f.name

        with patch.dict("os.environ", {"VISION_MODEL": "llava"}):
            result = analyze_image(path)
        assert result["success"] is True
        assert "dog" in result["description"].lower()
