"""Tests for slides tools export path."""
import json
import os
import tempfile

import pytest

from skills.slides.skill import create_slide_deck, save_slide_html
from tools.slides_tools import export_pptx, _load_deck_from_path


def test_save_slide_html_writes_deck_json():
    deck = create_slide_deck(
        "Test Deck",
        [{"type": "title", "title": "Hello", "subtitle": "World"}],
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = save_slide_html(deck, tmpdir)
        deck_json = os.path.join(out_dir, "deck.json")
        assert os.path.isfile(deck_json)
        with open(deck_json, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["title"] == "Test Deck"
        assert len(loaded["slides"]) == 1


def test_load_deck_from_path_missing_returns_error():
    result = _load_deck_from_path("/nonexistent/path/deck.html")
    assert isinstance(result, str)
    assert "not found" in result.lower()


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("pptx"),
    reason="python-pptx not installed",
)
def test_export_pptx_from_saved_deck():
    deck = create_slide_deck(
        "Export Test",
        [
            {"type": "title", "title": "Title", "subtitle": "Sub"},
            {"type": "content", "title": "Slide 2", "bullets": ["A", "B"]},
        ],
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = save_slide_html(deck, tmpdir)
        pptx_path = os.path.join(tmpdir, "out.pptx")
        result = export_pptx(out_dir, pptx_path)
        assert result == pptx_path
        assert os.path.isfile(pptx_path)
