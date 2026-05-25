"""Centralized logging setup for My Agent.

Provides a single ``setup_logging()`` entry point called early in startup.
All log files live under ``logs/`` (project-relative).

Log files produced:
    agent.log   — INFO+, all agent/tool/session activity (main log)
    errors.log  — WARNING+, errors and warnings only (quick triage)
    web.log     — INFO+, web/gateway events (when mode="web")

All files use ``RotatingFileHandler`` with ``RedactingFormatter`` so secrets
are never written to disk.

Component separation:
    web.log only receives records from ``web.*`` loggers.
    agent.log remains the catch-all.

Session context:
    Call ``set_session_context(session_id)`` at start of conversation
    and ``clear_session_context()`` when done. All log lines on that
    thread include ``[session_id]`` for filtering/correlation.
"""

import logging
import os
import re
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Sequence


# Sentinel to track whether setup_logging() has already run.
_logging_initialized = False

# Thread-local storage for per-conversation session context.
_session_context = threading.local()

# Default log format
_LOG_FORMAT = "%(asctime)s %(levelname)s%(session_tag)s %(name)s: %(message)s"
_LOG_FORMAT_VERBOSE = "%(asctime)s - %(name)s - %(levelname)s%(session_tag)s - %(message)s"

# Third-party loggers that are noisy at DEBUG/INFO level.
_NOISY_LOGGERS = (
    "openai",
    "openai._base_client",
    "httpx",
    "httpcore",
    "asyncio",
    "urllib3",
    "urllib3.connectionpool",
    "websockets",
    "charset_normalizer",
    "markdown_it",
    "litellm",
    "litellm.utils",
)


# ---------------------------------------------------------------------------
# Public session context API
# ---------------------------------------------------------------------------

def set_session_context(session_id: str) -> None:
    """Set session ID for the current thread."""
    _session_context.session_id = session_id


def clear_session_context() -> None:
    """Clear session ID for the current thread."""
    _session_context.session_id = None


# ---------------------------------------------------------------------------
# Record factory — injects session_tag into every LogRecord
# ---------------------------------------------------------------------------

def _install_session_record_factory() -> None:
    """Replace global LogRecord factory to add ``session_tag``."""
    current_factory = logging.getLogRecordFactory()
    if getattr(current_factory, "_my_agent_session_injector", False):
        return

    def _session_record_factory(*args, **kwargs):
        record = current_factory(*args, **kwargs)
        sid = getattr(_session_context, "session_id", None)
        record.session_tag = f" [{sid}]" if sid else ""
        return record

    _session_record_factory._my_agent_session_injector = True
    logging.setLogRecordFactory(_session_record_factory)


_install_session_record_factory()


# ---------------------------------------------------------------------------
# Redacting Formatter — masks secrets in log output
# ---------------------------------------------------------------------------

class RedactingFormatter(logging.Formatter):
    """Formatter that redacts API keys and bearer tokens from log messages."""

    _SECRET_PATTERNS = (
        # OpenRouter / OpenAI keys
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
        # Bearer tokens
        re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b", re.IGNORECASE),
        # Generic API keys in URLs
        re.compile(r"([?&]api_key=)[^&\s]+", re.IGNORECASE),
        re.compile(r"([?&]apikey=)[^&\s]+", re.IGNORECASE),
    )

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in self._SECRET_PATTERNS:
            msg = pattern.sub(lambda m: m.group(1) + "[REDACTED]" if m.lastindex else "[REDACTED]", msg)
        return msg


# ---------------------------------------------------------------------------
# Component filter
# ---------------------------------------------------------------------------

class _ComponentFilter(logging.Filter):
    """Only pass records whose logger name starts with one of *prefixes*."""

    def __init__(self, prefixes: Sequence[str]) -> None:
        super().__init__()
        self._prefixes = tuple(prefixes)

    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(self._prefixes)


COMPONENT_PREFIXES = {
    "web": ("web", "uvicorn", "fastapi"),
    "agent": ("agent", "core", "tools", "skills"),
}


# ---------------------------------------------------------------------------
# Main setup
# ---------------------------------------------------------------------------


def setup_logging(
    *,
    log_dir: Optional[Path] = None,
    log_level: Optional[str] = None,
    max_size_mb: int = 5,
    backup_count: int = 3,
    mode: Optional[str] = None,
    force: bool = False,
) -> Path:
    """Configure the My Agent logging subsystem.

    Safe to call multiple times. Second call is a no-op unless ``force=True``.

    Parameters
    ----------
    log_dir
        Directory for log files. Defaults to ``logs/`` next to this file.
    log_level
        Minimum level (DEBUG, INFO, WARNING). Defaults to INFO.
    max_size_mb
        Max size per log file before rotation.
    backup_count
        Number of rotated backups to keep.
    mode
        Caller context: ``"agent"``, ``"web"``, ``"cli"``.
        When ``"web"``, additional ``web.log`` is created.
    force
        Re-run setup even if already initialized.
    """
    global _logging_initialized

    if log_dir is None:
        # logs/ next to this file (i.e. project_root/logs/)
        log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    level_name = (log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    max_bytes = max_size_mb * 1024 * 1024

    root = logging.getLogger()

    # --- agent.log (INFO+) — main activity log -------------------------
    _add_rotating_handler(
        root,
        log_dir / "agent.log",
        level=level,
        max_bytes=max_bytes,
        backup_count=backup_count,
        formatter=RedactingFormatter(_LOG_FORMAT),
    )

    # --- errors.log (WARNING+) — quick triage --------------------------
    _add_rotating_handler(
        root,
        log_dir / "errors.log",
        level=logging.WARNING,
        max_bytes=2 * 1024 * 1024,
        backup_count=2,
        formatter=RedactingFormatter(_LOG_FORMAT),
    )

    # --- web.log (INFO+, web component only) ----------------------------
    if mode == "web":
        _add_rotating_handler(
            root,
            log_dir / "web.log",
            level=logging.INFO,
            max_bytes=max_bytes,
            backup_count=backup_count,
            formatter=RedactingFormatter(_LOG_FORMAT),
            log_filter=_ComponentFilter(COMPONENT_PREFIXES["web"]),
        )

    if _logging_initialized and not force:
        return log_dir

    if root.level == logging.NOTSET or root.level > level:
        root.setLevel(level)

    # Suppress noisy third-party loggers
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    _logging_initialized = True
    return log_dir


def setup_verbose_logging() -> None:
    """Enable DEBUG-level console logging for verbose mode."""
    root = logging.getLogger()

    # Avoid duplicates
    for h in root.handlers:
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler):
            if getattr(h, "_my_agent_verbose", False):
                return

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(RedactingFormatter(_LOG_FORMAT_VERBOSE, datefmt="%H:%M:%S"))
    handler._my_agent_verbose = True
    root.addHandler(handler)

    if root.level > logging.DEBUG:
        root.setLevel(logging.DEBUG)

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _add_rotating_handler(
    logger: logging.Logger,
    path: Path,
    *,
    level: int,
    max_bytes: int,
    backup_count: int,
    formatter: logging.Formatter,
    log_filter: Optional[logging.Filter] = None,
) -> None:
    """Add a RotatingFileHandler, skipping if one already exists for the path."""
    resolved = path.resolve()
    for existing in logger.handlers:
        if (
            isinstance(existing, RotatingFileHandler)
            and Path(getattr(existing, "baseFilename", "")).resolve() == resolved
        ):
            return

    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        str(path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    if log_filter is not None:
        handler.addFilter(log_filter)
    logger.addHandler(handler)
