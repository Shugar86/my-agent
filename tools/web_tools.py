import os
import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from core.tool_registry import registry

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

def web_search(query, max_results=5):
    # Try Tavily first (faster and more reliable)
    if TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=TAVILY_API_KEY)
            r = client.search(query=query, max_results=min(max_results, 5))
            results = []
            for item in r.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                })
            return results if results else None
        except Exception:
            pass  # Fallback to DuckDuckGo

    # Fallback: DuckDuckGo
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        return {"error": str(e)}
    return results


def web_scrape(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:3000]
    except Exception as e:
        return {"error": str(e)}


def register_tools():
    registry.register(
        name="web_search",
        description="Search the web for information",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
        execute_fn=web_search,
    )

    registry.register(
        name="web_scrape",
        description="Scrape content from a URL",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to scrape"},
            },
            "required": ["url"],
        },
        execute_fn=web_scrape,
    )


def unregister_tools():
    registry.unregister("web_search")
    registry.unregister("web_scrape")
