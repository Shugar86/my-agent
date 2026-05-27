"""Tests for Browser Automation skill."""
import pytest
from unittest.mock import MagicMock, patch
from skills.browser.skill import navigate, click, fill_form, extract_text, screenshot, close_browser


class FakePage:
    def __init__(self):
        self.url = "https://example.com"
        self.title_val = "Example"
        self.closed = False

    def goto(self, url, wait_until=None, timeout=None):
        self.url = url

    def title(self):
        return self.title_val

    def close(self):
        self.closed = True

    def click(self, selector, timeout=None):
        pass

    def fill(self, selector, text, timeout=None):
        pass

    def inner_text(self, selector):
        return "Hello world"

    def query_selector(self, selector):
        return self

    def screenshot(self, full_page=False):
        return b"fake_png"


class FakeContext:
    def __init__(self):
        self._pages = [FakePage()]

    def new_page(self):
        p = FakePage()
        self._pages.append(p)
        return p

    @property
    def pages(self):
        return self._pages


@pytest.fixture(autouse=True)
def reset_browser():
    import skills.browser.skill as skill_mod
    skill_mod._browser_context = None
    skill_mod._browser = None
    skill_mod._playwright = None
    skill_mod._active_page = None
    yield
    skill_mod._browser_context = None
    skill_mod._browser = None
    skill_mod._playwright = None
    skill_mod._active_page = None


def test_navigate():
    with patch("skills.browser.skill.sync_playwright") as mock_pw:
        mock_ctx = FakeContext()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_ctx
        pw_instance = MagicMock()
        pw_instance.chromium.launch.return_value = mock_browser
        pw_instance.start.return_value = pw_instance
        mock_pw.return_value = pw_instance

        result = navigate("https://example.com")
        assert result["success"] is True
        assert result["title"] == "Example"


def test_click():
    with patch("skills.browser.skill.sync_playwright") as mock_pw:
        mock_ctx = FakeContext()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_ctx
        pw_instance = MagicMock()
        pw_instance.chromium.launch.return_value = mock_browser
        pw_instance.start.return_value = pw_instance
        mock_pw.return_value = pw_instance

        navigate("https://example.com")
        result = click("button#submit")
        assert result["success"] is True


def test_extract_text():
    with patch("skills.browser.skill.sync_playwright") as mock_pw:
        mock_ctx = FakeContext()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_ctx
        pw_instance = MagicMock()
        pw_instance.chromium.launch.return_value = mock_browser
        pw_instance.start.return_value = pw_instance
        mock_pw.return_value = pw_instance

        navigate("https://example.com")
        result = extract_text()
        assert result["success"] is True
        assert "Hello world" in result["text"]


def test_screenshot():
    with patch("skills.browser.skill.sync_playwright") as mock_pw:
        mock_ctx = FakeContext()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_ctx
        pw_instance = MagicMock()
        pw_instance.chromium.launch.return_value = mock_browser
        pw_instance.start.return_value = pw_instance
        mock_pw.return_value = pw_instance

        navigate("https://example.com")
        result = screenshot()
        assert result["success"] is True
        assert "image_base64" in result


def test_close_browser():
    result = close_browser()
    assert result["success"] is True


def test_navigate_closes_previous_page():
    import skills.browser.skill as skill_mod

    with patch("skills.browser.skill.sync_playwright") as mock_pw:
        mock_ctx = FakeContext()
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_ctx
        pw_instance = MagicMock()
        pw_instance.chromium.launch.return_value = mock_browser
        pw_instance.start.return_value = pw_instance
        mock_pw.return_value = pw_instance

        navigate("https://example.com")
        first_page = skill_mod._active_page
        navigate("https://example.org")
        assert first_page.closed is True
        assert skill_mod._active_page is not first_page
        assert skill_mod._active_page.closed is False
