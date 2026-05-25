"""Tests for core.skill_cache module."""
import os
import pytest
from core.skill_cache import (
    SkillCache,
    filter_skills_by_query,
    get_skill_cache_stats,
    _SKILL_KEYWORDS,
)

# Clear stale cache from other test modules to avoid cross-test pollution
_cache_file = os.path.join("data", "cache", "skill_patterns.json")
if os.path.exists(_cache_file):
    os.remove(_cache_file)

# Also clear the in-memory global cache instance
from core.skill_cache import _skill_cache
_skill_cache.clear()


class TestSkillCache:
    """Unit tests for skill caching and pre-filtering."""

    ALL_SKILL_NAMES = [
        "web_search", "deep_search", "web_scrape", "file_read", "file_write",
        "execute_code", "analyze_csv", "create_chart", "create_presentation",
        "create_document", "query_sqlite", "ocr_image", "transcribe_audio",
        "send_email", "generate_image", "git_clone", "browser_navigate",
        "schedule_task", "analyze_image", "send_message", "read_source",
    ]

    def setup_method(self):
        """Clear skill cache file and in-memory cache before each test."""
        import os
        cache_file = os.path.join("data", "cache", "skill_patterns.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
        from core.skill_cache import _skill_cache
        _skill_cache.clear()

    def test_cache_creates_instance(self):
        """SkillCache can be instantiated."""
        c = SkillCache()
        assert c is not None
        assert hasattr(c, '_patterns')

    def test_filter_exact_keyword_match(self):
        """Exact keyword should score highest."""
        skills = ["web_search", "execute_code", "send_email", "create_chart"]
        result = filter_skills_by_query("search the web for news", skills)
        assert "web_search" in result
        assert len(result) >= 1

    def test_filter_partial_match(self):
        """Partial keyword matching works."""
        skills = ["web_search", "deep_search", "ocr_image", "browser_navigate"]
        result = filter_skills_by_query("searching online", skills)
        assert any(s in result for s in ["web_search", "deep_search"])

    def test_filter_returns_minimum_five(self):
        """Always returns at least top 5 skills."""
        skills = list(_SKILL_KEYWORDS.keys())[:20]
        result = filter_skills_by_query("something generic", skills)
        assert len(result) >= 5 or len(result) == len(skills)

    def test_filter_caching(self):
        """Same query should return cached result."""
        skills = ["web_search", "execute_code", "send_email"]
        r1 = filter_skills_by_query("find information", skills)
        r2 = filter_skills_by_query("find information", skills)
        assert r1 == r2

    def test_filter_unknown_skills_get_medium_score(self):
        """Skills not in keyword map get score 0.5."""
        skills = ["unknown_tool_xyz", "web_search"]
        result = filter_skills_by_query("search", skills)
        assert "web_search" in result

    def test_get_stats_returns_dict(self):
        """get_skill_cache_stats returns expected keys."""
        stats = get_skill_cache_stats()
        assert isinstance(stats, dict)
        assert "total_patterns" in stats
        assert "active_patterns" in stats
        assert "ttl_hours" in stats
        assert stats["ttl_hours"] == 1.0

    def test_filter_empty_query(self):
        """Empty query should still return skills."""
        skills = ["web_search", "execute_code"]
        result = filter_skills_by_query("", skills)
        assert len(result) >= 1

    def test_filter_long_query_truncated(self):
        """Very long query is truncated for cache key."""
        long_query = "search " * 100
        skills = ["web_search", "deep_search"]
        result = filter_skills_by_query(long_query, skills)
        assert len(result) >= 1

    def test_filter_reduces_context_size(self):
        """Filtering should significantly reduce skill count with many skills."""
        many_skills = self.ALL_SKILL_NAMES + [f"extra_tool_{i}" for i in range(30)]
        result = filter_skills_by_query("search web", many_skills)
        assert len(result) < len(many_skills)
        # Should return at least some skills (may be < 5 if query is very specific)
        assert len(result) >= 1


class TestSkillCacheIntegration:
    """Integration tests with real skill names."""

    def setup_method(self):
        """Clear skill cache file and in-memory cache before each test."""
        import os
        cache_file = os.path.join("data", "cache", "skill_patterns.json")
        if os.path.exists(cache_file):
            os.remove(cache_file)
        from core.skill_cache import _skill_cache
        _skill_cache.clear()

    ALL_SKILL_NAMES = [
        "web_search", "deep_search", "web_scrape", "file_read", "file_write",
        "execute_code", "analyze_csv", "create_chart", "create_presentation",
        "create_document", "query_sqlite", "ocr_image", "transcribe_audio",
        "send_email", "generate_image", "git_clone", "browser_navigate",
        "schedule_task", "analyze_image", "send_message", "read_source",
    ]

    @pytest.mark.parametrize("query,expected_skill", [
        ("search web for news", "web_search"),
        ("research academic paper", "deep_search"),
        ("scrape website content", "web_scrape"),
        ("read file contents", "file_read"),
        ("run python code", "execute_code"),
        ("analyze csv data", "analyze_csv"),
        ("create chart plot", "create_chart"),
        ("make presentation slides", "create_presentation"),
        ("write document report", "create_document"),
        ("sql query database", "query_sqlite"),
        ("ocr image text", "ocr_image"),
        ("transcribe audio", "transcribe_audio"),
        ("send email letter", "send_email"),
        ("generate image picture", "generate_image"),
        ("git clone repository", "git_clone"),
        ("browser navigate click", "browser_navigate"),
        ("schedule task cron", "schedule_task"),
        ("analyze image vision", "analyze_image"),
        ("send telegram message", "send_message"),
        ("read source code", "read_source"),
    ])
    def test_skill_relevance(self, query, expected_skill):
        """Each query should include the expected skill."""
        result = filter_skills_by_query(query, self.ALL_SKILL_NAMES)
        assert expected_skill in result, f"Expected {expected_skill} in {result} for query '{query}'"

    def test_filter_reduces_context_size(self):
        """Filtering reduces the number of tools passed to LLM."""
        result = filter_skills_by_query("search web", self.ALL_SKILL_NAMES)
        assert len(result) < len(self.ALL_SKILL_NAMES)
        assert len(result) >= 1
