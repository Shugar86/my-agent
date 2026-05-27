import os
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
import json
from core.tool_registry import registry

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


def _tavily_search(query, max_results=5):
    """Search using Tavily API (fast, reliable). Returns list of results or None."""
    if not TAVILY_API_KEY:
        return None
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
        return None


def _ddg_search(query, max_results=5):
    """Search using DuckDuckGo. Returns list of results."""
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


def deep_search(query, num_queries=5, results_per_query=5):
    sub_queries = _generate_sub_queries(query, num_queries)
    all_results = []
    seen_urls = set()

    for sub_q in sub_queries:
        try:
            # Try Tavily first
            results = _tavily_search(sub_q, results_per_query)
            if results is None:
                results = _ddg_search(sub_q, results_per_query)
            if isinstance(results, dict) and "error" in results:
                all_results.append({"query": sub_q, "error": results["error"]})
                continue
            for item in results:
                url = item.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append({"query": sub_q, **item})
        except Exception as e:
            all_results.append({"query": sub_q, "error": str(e)})

    return {
        "original_query": query,
        "sub_queries_used": sub_queries,
        "total_results": len(all_results),
        "results": all_results,
    }


def scholar_search(query, max_results=5):
    searches = [
        f"arxiv {query}",
        f"scholar.google.com {query}",
        f"researchgate.net {query}",
    ]
    all_results = []
    seen_urls = set()

    for search_q in searches:
        try:
            # Try Tavily first
            results = _tavily_search(search_q, max_results)
            if results is None:
                # DDGS fallback for academic search
                with DDGS() as ddgs:
                    results = []
                    for r in ddgs.text(search_q, max_results=max_results):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                        })
            if isinstance(results, dict) and "error" in results:
                continue
            for item in results:
                url = item.get("url", "")
                if url not in seen_urls and any(kw in url.lower() for kw in ["arxiv", "scholar", "researchgate", "ieee", "acm", "springer", "nature", "sciencedirect"]):
                    seen_urls.add(url)
                    all_results.append({
                        "title": item.get("title", ""),
                        "url": url,
                        "snippet": item.get("snippet", ""),
                        "type": "academic",
                    })
        except Exception as e:
            all_results.append({"query": search_q, "error": str(e)})

    return {
        "query": query,
        "total_results": len(all_results),
        "results": all_results[:max_results],
    }


def _validate_url(url: str) -> str | None:
    """Prevent SSRF: block file://, internal IPs, private ranges."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return f"URL scheme '{parsed.scheme}' not allowed. Use http:// or https://"
    hostname = parsed.hostname or ""
    # Block internal/private IPs
    import ipaddress
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_reserved:
            return "Internal IP addresses are not allowed"
    except ValueError:
        pass  # Not an IP, ok
    return None


def web_scrape(url):
    err = _validate_url(url)
    if err:
        return {"error": err}
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:3000]
    except Exception as e:
        return {"error": str(e)}


def _generate_sub_queries(query, num):
    base = query
    sub_queries = [base]

    if num > 1:
        sub_queries.append(f"{base} 2025 2026 latest")
    if num > 2:
        sub_queries.append(f"{base} analysis review comparison")
    if num > 3:
        sub_queries.append(f"{base} pros cons benefits drawbacks")
    if num > 4:
        sub_queries.append(f"{base} statistics data trends report")
    if num > 5:
        sub_queries.append(f"{base} expert opinion guide tutorial")

    return sub_queries[:num]


def register_tools():
    registry.register(
        name="deep_search",
        description="Conduct deep research with multiple sub-queries. Returns comprehensive results from different angles.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Main research query"},
                "num_queries": {"type": "integer", "description": "Number of sub-queries (default 5, max 7)"},
                "results_per_query": {"type": "integer", "description": "Results per sub-query (default 5)"},
            },
            "required": ["query"],
        },
        execute_fn=deep_search,
    )

    registry.register(
        name="scholar_search",
        description="Search for academic papers and scholarly sources on arxiv, google scholar, researchgate.",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Academic search query"},
                "max_results": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
        execute_fn=scholar_search,
    )

    registry.register(
        name="web_scrape",
        description="Scrape content from a URL and extract text.",
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
    registry.unregister("deep_search")
    registry.unregister("scholar_search")
    registry.unregister("web_scrape")
