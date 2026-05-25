"""Security fuzzing and input validation tests."""
import pytest
from core.validation import (
    validate_safe_path,
    validate_sql,
    validate_email,
    validate_file_exists,
    validate_twitter_text,
)


class TestPathValidation:
    def test_valid_relative_path(self):
        assert validate_safe_path("data/output/file.txt")

    def test_valid_simple_name(self):
        assert validate_safe_path("report.pdf")

    def test_rejects_absolute_path(self):
        assert not validate_safe_path("/etc/passwd")

    def test_rejects_parent_directory(self):
        assert not validate_safe_path("../../../etc/passwd")

    def test_rejects_null_byte(self):
        assert not validate_safe_path("file\x00.txt")

    def test_rejects_empty(self):
        assert not validate_safe_path("")

    def test_rejects_tilde(self):
        assert not validate_safe_path("~/.ssh/id_rsa")

    def test_allows_subdir(self):
        assert validate_safe_path("output/subdir/file.txt")

    def test_rejects_double_dots(self):
        assert not validate_safe_path("foo/bar/../baz")

    def test_rejects_special_chars(self):
        assert not validate_safe_path("file;rm -rf /")


class TestSQLValidation:
    def test_valid_select(self):
        assert validate_sql("SELECT * FROM users WHERE id = 1")

    def test_valid_insert(self):
        assert validate_sql("INSERT INTO users (name) VALUES ('alice')")

    def test_blocks_union(self):
        assert not validate_sql("SELECT * FROM users UNION SELECT * FROM secrets")

    def test_blocks_drop(self):
        assert not validate_sql("DROP TABLE users")

    def test_blocks_delete_without_where(self):
        assert not validate_sql("DELETE FROM users")

    def test_allows_delete_with_where(self):
        assert validate_sql("DELETE FROM users WHERE id = 1")

    def test_blocks_stacked_queries(self):
        assert not validate_sql("SELECT 1; DROP TABLE users")

    def test_blocks_comment_injection(self):
        assert not validate_sql("SELECT * FROM users --")

    def test_blocks_or_true(self):
        assert not validate_sql("SELECT * FROM users WHERE 1=1 OR 'a'='a'")

    def test_blocks_sleep(self):
        assert not validate_sql("SELECT * FROM users WHERE SLEEP(5)")

    def test_allows_complex_select(self):
        assert validate_sql("SELECT u.name, p.title FROM users u JOIN posts p ON u.id = p.user_id WHERE p.status = 'published'")

    def test_blocks_alter(self):
        assert not validate_sql("ALTER TABLE users ADD COLUMN hack TEXT")

    def test_blocks_exec(self):
        assert not validate_sql("EXEC xp_cmdshell 'dir'")


class TestEmailValidation:
    def test_valid_email(self):
        assert validate_email("user@example.com")

    def test_valid_email_with_plus(self):
        assert validate_email("user+tag@example.com")

    def test_rejects_missing_at(self):
        assert not validate_email("userexample.com")

    def test_rejects_missing_domain(self):
        assert not validate_email("user@")

    def test_rejects_multiple_at(self):
        assert not validate_email("user@@example.com")

    def test_rejects_empty(self):
        assert not validate_email("")

    def test_rejects_no_user(self):
        assert not validate_email("@example.com")


class TestTwitterValidation:
    def test_valid_short_text(self):
        assert validate_twitter_text("Hello world")

    def test_exactly_280_chars(self):
        assert validate_twitter_text("x" * 280)

    def test_over_280_rejected(self):
        assert not validate_twitter_text("x" * 281)

    def test_empty_rejected(self):
        assert not validate_twitter_text("")

    def test_emoji_count(self):
        assert validate_twitter_text("Hello 🚀")


class TestFileExists:
    def test_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        assert validate_file_exists(str(f))

    def test_missing_file(self, tmp_path):
        assert not validate_file_exists(str(tmp_path / "missing.txt"))

    def test_directory_not_file(self, tmp_path):
        assert not validate_file_exists(str(tmp_path))

    def test_empty_path(self):
        assert not validate_file_exists("")
