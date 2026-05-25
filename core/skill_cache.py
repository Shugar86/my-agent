"""Skill relevance cache for token economy.

Uses keyword-based pre-filtering and pattern caching to reduce
LLM context size by only sending relevant skill schemas.
"""
import json
import time
from pathlib import Path
from typing import List, Dict, Optional

# Keyword → skill mappings (heuristic pre-filtering)
_SKILL_KEYWORDS = {
    "web_search": {"search", "find", "google", "web", "internet", "lookup", "query", "information"},
    "deep_search": {"research", "deep", "academic", "scholar", "paper", "arxiv", "study"},
    "web_scrape": {"scrape", "extract", "parse", "html", "page", "content", "crawl"},
    "file_read": {"read", "file", "open", "content", "document", "text", "load"},
    "file_write": {"write", "save", "create", "file", "output", "export", "generate"},
    "execute_code": {"code", "python", "run", "execute", "script", "program", "function"},
    "analyze_csv": {"csv", "data", "table", "pandas", "dataframe", "analysis", "stats"},
    "create_chart": {"chart", "plot", "graph", "visualize", "matplotlib", "diagram"},
    "create_presentation": {"presentation", "slide", "ppt", "powerpoint", "deck", "talk"},
    "create_document": {"document", "docx", "pdf", "report", "word", "paper"},
    "query_sqlite": {"sql", "database", "sqlite", "query", "table", "select"},
    "ocr_image": {"ocr", "image", "text", "scan", "photo", "picture", "recognize"},
    "transcribe_audio": {"audio", "transcribe", "speech", "whisper", "voice", "record"},
    "send_email": {"email", "mail", "send", "smtp", "letter", "message"},
    "generate_image": {"image", "generate", "dalle", "picture", "photo", "create image"},
    "git_clone": {"git", "clone", "repository", "repo", "github", "download"},
    "browser_navigate": {"browser", "navigate", "website", "click", "fill", "form", "login", "page"},
    "schedule_task": {"schedule", "cron", "timer", "periodic", "job", "automate", "recurring"},
    "analyze_image": {"image", "analyze", "vision", "describe", "multimodal", "screenshot"},
    "send_message": {"telegram", "discord", "slack", "message", "chat", "notify"},
    "read_source": {"code", "source", "read file", "inspect", "review"},
}

# Cache file
_CACHE_DIR = Path("data/cache")
_CACHE_FILE = _CACHE_DIR / "skill_patterns.json"
_CACHE_TTL_SECONDS = 3600  # 1 hour


class SkillCache:
    """Caches skill→query relevance patterns to reduce LLM token usage."""

    def __init__(self):
        self._patterns: Dict[str, Dict] = {}
        self._load()

    def _load(self):
        if _CACHE_FILE.exists():
            try:
                with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                    self._patterns = json.load(f)
            except Exception:
                self._patterns = {}

    def _save(self):
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self._patterns, f, indent=2, ensure_ascii=False)

    def filter_skills(self, query: str, all_skill_names: List[str]) -> List[str]:
        """Return only skills likely relevant to the query."""
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Check cache first
        # Include skill set hash in cache key to avoid cross-test pollution
        import hashlib
        skills_hash = hashlib.md5(",".join(sorted(all_skill_names)).encode()).hexdigest()[:8]
        cache_key = f"{query_lower[:100]}:{skills_hash}"
        cached = self._patterns.get(cache_key)
        if cached and (time.time() - cached.get("ts", 0)) < _CACHE_TTL_SECONDS:
            cached_skills = cached.get("skills", [])
            # Only return cached skills that still exist
            return [s for s in cached_skills if s in all_skill_names]

        # Heuristic matching
        scores = {}
        for skill in all_skill_names:
            keywords = _SKILL_KEYWORDS.get(skill, set())
            if not keywords:
                scores[skill] = 0.5  # unknown skills get medium score
                continue
            matches = query_words & keywords
            # Also check for partial matches (e.g., "searching" matches "search")
            partial_matches = sum(1 for kw in keywords if any(kw in w or w in kw for w in query_words))
            scores[skill] = len(matches) * 2 + partial_matches * 0.5

        # Sort by score, take top 75% or minimum 5 skills
        sorted_skills = sorted(scores.keys(), key=lambda s: scores[s], reverse=True)
        # Keep top 75% by count (not by score threshold)
        keep_count = max(5, int(len(sorted_skills) * 0.75))
        filtered = sorted_skills[:keep_count]

        # Cache result
        self._patterns[cache_key] = {"skills": filtered, "ts": time.time()}
        self._save()

        return filtered

    def get_stats(self) -> Dict:
        """Return cache statistics."""
        total = len(self._patterns)
        recent = sum(1 for v in self._patterns.values() if (time.time() - v.get("ts", 0)) < _CACHE_TTL_SECONDS)
        return {"total_patterns": total, "active_patterns": recent, "ttl_hours": _CACHE_TTL_SECONDS / 3600}

    def clear(self):
        """Clear all cached patterns."""
        self._patterns = {}
        if _CACHE_FILE.exists():
            _CACHE_FILE.unlink()


# Global instance
_skill_cache = SkillCache()


def filter_skills_by_query(query: str, all_skill_names: List[str]) -> List[str]:
    """Convenience function to filter skills by query."""
    return _skill_cache.filter_skills(query, all_skill_names)


def get_skill_cache_stats() -> Dict:
    """Get cache statistics."""
    return _skill_cache.get_stats()
