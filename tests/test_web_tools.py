"""Tests for web_tools Tavily/DuckDuckGo fallback."""

from unittest.mock import MagicMock, patch

from tools import web_tools


def test_web_search_empty_tavily_falls_back_to_ddgs(monkeypatch):
    """M1: empty Tavily results must trigger DuckDuckGo fallback."""
    monkeypatch.setattr(web_tools, "TAVILY_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}

    ddgs_results = [{"title": "DDG", "url": "https://example.com", "snippet": "body"}]

    mock_tavily_mod = MagicMock()
    mock_tavily_mod.TavilyClient.return_value = mock_client

    with patch.dict("sys.modules", {"tavily": mock_tavily_mod}), patch(
        "tools.web_tools.DDGS"
    ) as mock_ddgs_cls:
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__.return_value = mock_ddgs
        mock_ddgs.__exit__.return_value = False
        mock_ddgs.text.return_value = [
            {"title": "DDG", "href": "https://example.com", "body": "body"},
        ]
        mock_ddgs_cls.return_value = mock_ddgs

        result = web_tools.web_search("test query")

    assert result == ddgs_results
    mock_client.search.assert_called_once()
