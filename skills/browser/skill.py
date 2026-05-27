"""Browser automation skill using Playwright.

Provides full browser control: navigation, clicking, form filling,
screenshots, and semantic element search.
"""
import base64
import os
from typing import Optional

from core.tool_registry import registry

try:
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover
    sync_playwright = None

_playwright = None
_browser = None
_browser_context = None
_active_page = None


def _get_browser():
    """Lazy-initialize Playwright browser (Chromium)."""
    global _playwright, _browser, _browser_context
    if _browser_context is None:
        if sync_playwright is None:
            raise RuntimeError("Playwright not installed. Install with: pip install playwright && playwright install chromium")
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=True)
        _browser_context = _browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        )
    return _browser_context


def _get_active_page():
    """Return the current active page, if any."""
    global _active_page
    if _active_page is not None:
        return _active_page
    ctx = _browser_context
    if ctx and ctx.pages:
        return ctx.pages[0]
    return None


def _close_browser():
    global _playwright, _browser, _browser_context, _active_page
    if _active_page is not None:
        try:
            _active_page.close()
        except Exception:
            pass
        _active_page = None
    if _browser_context:
        _browser_context.close()
        _browser_context = None
    if _browser:
        _browser.close()
        _browser = None
    if _playwright:
        _playwright.stop()
        _playwright = None


def navigate(url: str, wait_until: str = "networkidle") -> dict:
    """Navigate to a URL and wait for page load."""
    global _active_page
    try:
        ctx = _get_browser()
        if _active_page is not None:
            try:
                _active_page.close()
            except Exception:
                pass
            _active_page = None
        page = ctx.new_page()
        _active_page = page
        page.goto(url, wait_until=wait_until, timeout=30000)
        title = page.title()
        return {"success": True, "title": title, "url": page.url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def click(selector: str) -> dict:
    """Click an element by CSS selector."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        page.click(selector, timeout=10000)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fill_form(selector: str, text: str) -> dict:
    """Fill a form field by CSS selector."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        page.fill(selector, text, timeout=10000)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def press_key(key: str) -> dict:
    """Press a keyboard key (Enter, ArrowDown, etc.)."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        page.keyboard.press(key)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_text(selector: Optional[str] = None) -> dict:
    """Extract text from the page or a specific element."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        if selector:
            element = page.query_selector(selector)
            text = element.inner_text() if element else ""
        else:
            text = page.inner_text("body")
        return {"success": True, "text": text[:5000]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_links() -> dict:
    """Extract all links from the current page."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        links = page.eval_on_selector_all("a", "elements => elements.map(e => ({text: e.innerText, href: e.href}))")
        return {"success": True, "links": links[:100]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def screenshot(full_page: bool = False, selector: Optional[str] = None) -> dict:
    """Take a screenshot. Returns base64 PNG."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        if selector:
            element = page.query_selector(selector)
            if not element:
                return {"success": False, "error": f"Element not found: {selector}"}
            png_bytes = element.screenshot()
        else:
            png_bytes = page.screenshot(full_page=full_page)
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return {"success": True, "image_base64": b64, "format": "png"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def scroll(direction: str = "down", amount: int = 300) -> dict:
    """Scroll the page."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        if direction == "down":
            page.mouse.wheel(0, amount)
        elif direction == "up":
            page.mouse.wheel(0, -amount)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def find_element(description: str) -> dict:
    """Semantic element search (simple heuristic: find by text content)."""
    try:
        page = _get_active_page()
        if not page:
            return {"success": False, "error": "No open page"}
        # Heuristic: query all buttons/links/inputs and filter by inner text
        escaped_description = description.replace("'", "\\'")
        elements = page.eval_on_selector_all(
            "button, a, input, textarea, select, label, [role='button']",
            f"""elements => {{
                const query = '{escaped_description}';
                return elements
                    .map(e => ({{tag: e.tagName.toLowerCase(), text: (e.innerText || e.value || e.placeholder || '').toLowerCase(), selector: e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className ? '.' + e.className.split(' ').join('.') : '')}}))
                    .filter(e => e.text.includes(query));
            }}"""
        )
        return {"success": True, "matches": elements[:10]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def close_browser() -> dict:
    """Close the browser and free resources."""
    try:
        _close_browser()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def register_tools():
    registry.register(
        name="browser_navigate",
        description="Navigate to a URL using headless browser (Playwright).",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to navigate to"},
                "wait_until": {"type": "string", "enum": ["load", "domcontentloaded", "networkidle", "commit"], "description": "When to consider navigation done"},
            },
            "required": ["url"],
        },
        execute_fn=navigate,
    )
    registry.register(
        name="browser_click",
        description="Click an element on the current page by CSS selector.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of element to click"},
            },
            "required": ["selector"],
        },
        execute_fn=click,
    )
    registry.register(
        name="browser_fill",
        description="Fill a form field by CSS selector.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of input/textarea"},
                "text": {"type": "string", "description": "Text to type"},
            },
            "required": ["selector", "text"],
        },
        execute_fn=fill_form,
    )
    registry.register(
        name="browser_press_key",
        description="Press a keyboard key (Enter, Tab, ArrowDown, etc.).",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key name"},
            },
            "required": ["key"],
        },
        execute_fn=press_key,
    )
    registry.register(
        name="browser_extract_text",
        description="Extract text from current page or specific element.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "Optional CSS selector. If omitted, extracts whole page body text."},
            },
            "required": [],
        },
        execute_fn=extract_text,
    )
    registry.register(
        name="browser_extract_links",
        description="Extract all links from the current page.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        execute_fn=extract_links,
    )
    registry.register(
        name="browser_screenshot",
        description="Take a screenshot of current page or element. Returns base64 PNG.",
        parameters={
            "type": "object",
            "properties": {
                "full_page": {"type": "boolean", "description": "Capture full scrollable page"},
                "selector": {"type": "string", "description": "Optional CSS selector to capture specific element"},
            },
            "required": [],
        },
        execute_fn=screenshot,
    )
    registry.register(
        name="browser_scroll",
        description="Scroll the current page up or down.",
        parameters={
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["down", "up"], "description": "Scroll direction"},
                "amount": {"type": "integer", "description": "Pixels to scroll (default 300)"},
            },
            "required": [],
        },
        execute_fn=scroll,
    )
    registry.register(
        name="browser_find",
        description="Find elements by text description (semantic search heuristic).",
        parameters={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Text to search for in elements"},
            },
            "required": ["description"],
        },
        execute_fn=find_element,
    )
    registry.register(
        name="browser_close",
        description="Close the browser and release resources.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        execute_fn=close_browser,
    )


def unregister_tools():
    for name in [
        "browser_navigate", "browser_click", "browser_fill", "browser_press_key",
        "browser_extract_text", "browser_extract_links", "browser_screenshot",
        "browser_scroll", "browser_find", "browser_close",
    ]:
        registry.unregister(name)
