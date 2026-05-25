"""Input validation utilities for agent tools.

Provides fast-fail validation for common inputs like file paths,
SQL queries, email addresses, and API credentials.
"""
import os
import re
from typing import Optional


def validate_not_empty(value: str, name: str = "value") -> bool:
    return bool(value and str(value).strip())


def validate_file_exists(path: str, name: str = "file") -> bool:
    if not validate_not_empty(path, name):
        return False
    return os.path.exists(path) and os.path.isfile(path)


def validate_safe_path(path: str, name: str = "path") -> bool:
    """Ensure path doesn't traverse outside working directory."""
    if not validate_not_empty(path, name):
        return False
    abs_path = os.path.abspath(path)
    cwd = os.path.abspath(os.getcwd())
    output_dir = os.path.abspath("output")
    # Allow paths within cwd or output directory
    if not abs_path.startswith(cwd) and not abs_path.startswith(output_dir):
        return False
    # Block parent directory traversal
    if ".." in path or "~" in path:
        return False
    # Block null bytes and dangerous chars
    if "\x00" in path or ";" in path or "|" in path:
        return False
    return True


EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_RE.match(email))


def validate_sql(query: str) -> bool:
    """Basic SQL safety check — blocks obvious stacked queries and dangerous commands."""
    if not query or not query.strip():
        return False
    # Remove string literals to avoid false positives
    cleaned = re.sub(r"'[^']*'", "''", query)
    # Block dangerous DDL commands anywhere
    dangerous_ddl = re.search(r"\b(drop|alter|grant|revoke|exec|copy)\b", cleaned, re.I)
    if dangerous_ddl:
        return False
    # Block DELETE without WHERE
    if re.search(r"\bdelete\b(?!.*\bwhere\b)", cleaned, re.I):
        return False
    # Block stacked queries after semicolon
    dangerous = re.search(r";\s*(drop|delete|insert|update|create|alter|grant|revoke|exec|copy)\s", cleaned, re.I)
    if dangerous:
        return False
    # Block UNION-based injection patterns
    if re.search(r"\bunion\b.*\bselect\b", cleaned, re.I):
        return False
    # Block INTO OUTFILE
    if re.search(r"\binto\s+outfile\b", cleaned, re.I):
        return False
    # Block SLEEP and time-based injection
    if re.search(r"\bsleep\b", cleaned, re.I):
        return False
    # Block OR 1=1 style injection in WHERE clauses
    if re.search(r"\bwhere\b.*1\s*=\s*1\b", cleaned, re.I):
        return False
    # Block comment-based injection
    if "--" in cleaned or "/*" in cleaned or "*/" in cleaned:
        return False
    return True


def validate_twitter_text(text: str) -> bool:
    if not text:
        return False
    return len(text) <= 280


def validate_all(*checks) -> bool:
    """Run multiple validations, return True if all pass."""
    for check in checks:
        if isinstance(check, str):
            return False
        result = check() if callable(check) else check
        if not result:
            return False
    return True


# String-returning validators for tool error messages
# Returns None on success, error string on failure

def validate_not_empty_or_error(value: str, name: str = "value") -> Optional[str]:
    if not (value and str(value).strip()):
        return f"{name} cannot be empty"
    return None


def validate_file_exists_or_error(path: str, name: str = "file") -> Optional[str]:
    if not (path and str(path).strip()):
        return f"{name} path cannot be empty"
    if not os.path.exists(path):
        return f"{name} does not exist: {path}"
    if not os.path.isfile(path):
        return f"{name} is not a file: {path}"
    return None


def validate_safe_path_or_error(path: str, name: str = "path") -> Optional[str]:
    if not (path and str(path).strip()):
        return f"{name} path cannot be empty"
    abs_path = os.path.abspath(path)
    cwd = os.path.abspath(os.getcwd())
    output_dir = os.path.abspath("output")
    if not abs_path.startswith(cwd) and not abs_path.startswith(output_dir):
        return f"{name} must be within project directory"
    if ".." in path or "~" in path:
        return f"{name} contains invalid traversal characters"
    if "\x00" in path or ";" in path or "|" in path:
        return f"{name} contains invalid characters"
    return None


def validate_email_or_error(email: str) -> Optional[str]:
    if not email or not isinstance(email, str):
        return "Email must be a non-empty string"
    if not EMAIL_RE.match(email):
        return f"Invalid email format: {email}"
    return None


def validate_twitter_text_or_error(text: str) -> Optional[str]:
    if not text:
        return "Tweet text cannot be empty"
    if len(text) > 280:
        return f"Tweet exceeds 280 characters ({len(text)})"
    return None
