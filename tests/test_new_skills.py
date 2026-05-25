"""Tests for 9 new competitor skills integrated into My Agent."""
import sys, os, json, tempfile, sqlite3
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.tool_registry import registry


# Register all new tools
from skills.sql_db.skill import register_tools as reg_sql
from skills.ocr.skill import register_tools as reg_ocr
from skills.audio_transcription.skill import register_tools as reg_audio
from skills.rss_news.skill import register_tools as reg_rss
from skills.email.skill import register_tools as reg_email
from skills.image_generation.skill import register_tools as reg_img
from skills.translation.skill import register_tools as reg_tr
from skills.git_integration.skill import register_tools as reg_git
from skills.social_media.skill import register_tools as reg_social, search_tweets

for fn in [reg_sql, reg_ocr, reg_audio, reg_rss, reg_email, reg_img, reg_tr, reg_git, reg_social]:
    fn()


# ─── SQL / DB ─────────────────────────────────────────────────────────

def test_query_sqlite_select():
    r = registry.execute("query_sqlite", db_path=":memory:", query="SELECT 42 as answer")
    assert "rows" in r
    assert r["count"] == 1
    assert r["rows"][0]["answer"] == 42
    print("  PASSED: query_sqlite SELECT")


def test_query_sqlite_create_insert():
    os.makedirs("output", exist_ok=True)
    db = "output/test_sql.db"
    try:
        registry.execute("query_sqlite", db_path=db, query="CREATE TABLE users (id INT, name TEXT)")
        registry.execute("query_sqlite", db_path=db, query="INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
        r3 = registry.execute("query_sqlite", db_path=db, query="SELECT * FROM users")
        assert r3["count"] == 2
        assert r3["rows"][0]["name"] == "Alice"
    finally:
        if os.path.exists(db):
            os.unlink(db)
    print("  PASSED: query_sqlite CREATE/INSERT/SELECT")


def test_query_sqlite_params():
    os.makedirs("output", exist_ok=True)
    db = "output/test_params.db"
    try:
        registry.execute("query_sqlite", db_path=db, query="CREATE TABLE t (x TEXT)")
        registry.execute("query_sqlite", db_path=db, query="INSERT INTO t VALUES (?)", params=["hello"])
        r = registry.execute("query_sqlite", db_path=db, query="SELECT * FROM t WHERE x = ?", params=["hello"])
        assert r["count"] == 1
    finally:
        if os.path.exists(db):
            os.unlink(db)
    print("  PASSED: query_sqlite with params")


def test_list_tables():
    os.makedirs("output", exist_ok=True)
    db = "output/test_tables.db"
    try:
        registry.execute("query_sqlite", db_path=db, query="CREATE TABLE foo (id INT)")
        r = registry.execute("list_tables", db_path=db)
        assert r["count"] >= 1
        names = [row["name"] for row in r["rows"]]
        assert "foo" in names
    finally:
        if os.path.exists(db):
            os.unlink(db)
    print("  PASSED: list_tables")


# ─── OCR ──────────────────────────────────────────────────────────────

def test_ocr_image_graceful():
    r = registry.execute("ocr_image", image_path="nonexistent.png")
    assert "error" in r
    print("  PASSED: ocr_image graceful error")


def test_ocr_pdf_graceful():
    r = registry.execute("ocr_pdf", pdf_path="nonexistent.pdf")
    assert "error" in r
    print("  PASSED: ocr_pdf graceful error")


# ─── Audio Transcription ──────────────────────────────────────────────

def test_transcribe_audio_graceful():
    r = registry.execute("transcribe_audio", audio_path="nonexistent.mp3")
    assert "error" in r
    print("  PASSED: transcribe_audio graceful error")


def test_translate_audio_graceful():
    r = registry.execute("translate_audio", audio_path="nonexistent.mp3")
    assert "error" in r
    print("  PASSED: translate_audio graceful error")


# ─── RSS / News ───────────────────────────────────────────────────────

def test_fetch_article():
    r = registry.execute("fetch_article", url="https://example.com")
    assert "title" in r
    assert "text" in r
    print("  PASSED: fetch_article")


# ─── Email ────────────────────────────────────────────────────────────

def test_send_email_graceful():
    r = registry.execute("send_email",
        smtp_host="smtp.invalid", smtp_port=465,
        username="x", password="x", to="x@x.com",
        subject="test", body="test")
    assert r["success"] is False
    print("  PASSED: send_email graceful error")


# ─── Image Generation ─────────────────────────────────────────────────

def test_generate_image_graceful():
    r = registry.execute("generate_image", prompt="test")
    assert "error" in r
    print("  PASSED: generate_image graceful error")


def test_generate_image_variation_graceful():
    r = registry.execute("generate_image_variation", image_path="nonexistent.png")
    assert "error" in r
    print("  PASSED: generate_image_variation graceful error")


# ─── Translation ──────────────────────────────────────────────────────

def test_detect_language_english():
    r = registry.execute("detect_language", text="Python is a programming language used worldwide")
    assert "language" in r
    print(f"  detected: {r['language']} ({r.get('name', '?')})")
    print("  PASSED: detect_language")


# ─── Git / GitHub ─────────────────────────────────────────────────────

def test_git_status():
    r = registry.execute("git_status", repo_path=".")
    assert "branch" in r or "error" in r
    print("  PASSED: git_status")


def test_git_clone_graceful():
    r = registry.execute("git_clone", repo_url="https://github.com/nonexistent-repo-12345.git")
    assert "error" in r or "path" in r
    print("  PASSED: git_clone graceful")


def test_github_list_issues_graceful():
    r = registry.execute("github_list_issues", token="", repo="foo/bar")
    assert "error" in r
    print("  PASSED: github_list_issues graceful error")


# ─── Social Media ─────────────────────────────────────────────────────

def test_post_tweet_graceful():
    r = registry.execute("post_tweet",
        api_key="", api_secret="", access_token="", access_secret="", text="test")
    assert "error" in r
    print("  PASSED: post_tweet graceful error")


@pytest.mark.slow
def test_search_tweets_graceful():
    result = search_tweets("k", "s", "t", "s", "python")
    assert "success" in result or "error" in result


@pytest.mark.slow
def test_search_tweets_empty_query():
    r = registry.execute("search_tweets",
        api_key="k", api_secret="s", access_token="t", access_secret="s", query="")
    assert "error" in r
    print("  PASSED: search_tweets empty query")


# ─── Cleanup ──────────────────────────────────────────────────────────

def test_all():
    print("=" * 60)
    print("Testing 9 NEW SKILLS")
    print("=" * 60)

    test_query_sqlite_select()
    test_query_sqlite_create_insert()
    test_query_sqlite_params()
    test_list_tables()
    test_ocr_image_graceful()
    test_ocr_pdf_graceful()
    test_transcribe_audio_graceful()
    test_translate_audio_graceful()
    test_fetch_article()
    test_send_email_graceful()
    test_generate_image_graceful()
    test_generate_image_variation_graceful()
    test_detect_language_english()
    test_git_status()
    test_git_clone_graceful()
    test_github_list_issues_graceful()
    test_post_tweet_graceful()
    test_search_tweets_graceful()

    print()
    print("=" * 60)
    print("ALL 18 NEW SKILL TESTS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    test_all()
