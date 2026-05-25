from datetime import datetime
try:
    import feedparser
except ImportError:
    feedparser = None
from bs4 import BeautifulSoup
import requests


def parse_rss(feed_url: str, max_items: int = 10) -> dict:
    if feedparser is None:
        return {"error": "feedparser not installed. Run: pip install feedparser"}
    try:
        feed = feedparser.parse(feed_url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:500],
            })
        return {
            "feed_title": feed.feed.get("title", ""),
            "items": items,
            "total": len(items),
            "fetched_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_article(url: str) -> dict:
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; MyAgent/1.0)"
        })
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title = soup.title.string if soup.title else ""
        text = soup.get_text(separator="\n", strip=True)
        text = "\n".join(line for line in text.splitlines() if len(line) > 40)
        return {
            "title": title,
            "text": text[:10000],
            "length": min(len(text), 10000),
            "source": url,
        }
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    from core.tool_registry import registry
    registry.register(
        name="parse_rss",
        description="Parse an RSS/Atom feed and return recent articles. Use for news monitoring.",
        parameters={"type": "object", "properties": {
            "feed_url": {"type": "string"},
            "max_items": {"type": "integer"},
        }},
        execute_fn=lambda feed_url="", max_items=10: parse_rss(feed_url, max_items),
    )
    registry.register(
        name="fetch_article",
        description="Fetch and extract readable text content from a news article URL.",
        parameters={"type": "object", "properties": {
            "url": {"type": "string"},
        }},
        execute_fn=lambda url="": fetch_article(url),
    )


def unregister_tools():
    from core.tool_registry import registry
    for name in ["parse_rss", "fetch_article"]:
        registry.unregister(name)
