"""Workflow expression engine.

Provides n8n-style template interpolation with safe, sandboxed evaluation.

Supported syntax inside ``{{ ... }}``:
    - Path access: ``trigger.payload.email``, ``a1.output.items[0].name``.
    - Bracket access: ``state["counter"]``.
    - String / number literals: ``"hello"``, ``42``, ``true``, ``false``, ``null``.
    - Function calls (whitelisted): ``now()``, ``today()``, ``upper(x)``,
      ``lower(x)``, ``len(x)``, ``default(x, "fallback")``, ``json(x)``,
      ``str(x)``, ``int(x)``, ``float(x)``, ``bool(x)``, ``trim(x)``,
      ``slice(x, 0, 10)``, ``join(list, ",")``, ``uuid()``, ``env("KEY")``.

Design trade-offs:
    - No ``eval``/``exec``: AST is built from a hand-rolled parser to keep
      execution sandboxed (security > flexibility).
    - Simple grammar: only path + call, no operators. This covers ~95% of
      real-world templating cases (n8n's ``$json.foo``) without exposing a
      full JS sandbox.
    - Backward compatible with previous resolver: ``{{node.output}}`` and
      ``{{trigger.field}}`` keep working.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

_EXPR_RE = re.compile(r"{{\s*(.*?)\s*}}", re.DOTALL)


def _safe_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _safe_default(value: Any, fallback: Any) -> Any:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return value


def _safe_join(value: Any, sep: str = ",") -> str:
    if isinstance(value, (list, tuple)):
        return sep.join(str(v) for v in value)
    return str(value or "")


def _safe_slice(value: Any, start: int = 0, end: int | None = None) -> Any:
    try:
        if isinstance(value, str):
            return value[start:end] if end is not None else value[start:]
        if isinstance(value, (list, tuple)):
            return list(value)[start:end] if end is not None else list(value)[start:]
    except (TypeError, ValueError):
        return value
    return value


def _safe_env(name: str, default: str = "") -> str:
    if not isinstance(name, str):
        return default
    return os.environ.get(name, default)


def _safe_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(value)


_HELPERS: dict[str, Callable[..., Any]] = {
    "now": _safe_now,
    "today": _safe_today,
    "upper": lambda v: str(v or "").upper(),
    "lower": lambda v: str(v or "").lower(),
    "len": lambda v: len(v) if hasattr(v, "__len__") else 0,
    "default": _safe_default,
    "json": _safe_json,
    "str": lambda v: str(v) if v is not None else "",
    "int": lambda v: int(float(v)) if v not in (None, "") else 0,
    "float": lambda v: float(v) if v not in (None, "") else 0.0,
    "bool": lambda v: bool(v) and str(v).lower() not in {"false", "0", "no", ""},
    "trim": lambda v: str(v or "").strip(),
    "slice": _safe_slice,
    "join": _safe_join,
    "uuid": lambda: uuid.uuid4().hex,
    "env": _safe_env,
}


@dataclass
class _Token:
    """Lexer token."""

    kind: str
    value: Any


def _tokenize(source: str) -> list[_Token]:
    """Split expression into tokens. Raises ``ValueError`` on bad input."""
    tokens: list[_Token] = []
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        if ch.isspace():
            i += 1
            continue
        if ch in "().,[]":
            tokens.append(_Token(ch, ch))
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            j = i + 1
            buf = []
            while j < n and source[j] != quote:
                if source[j] == "\\" and j + 1 < n:
                    buf.append(source[j + 1])
                    j += 2
                    continue
                buf.append(source[j])
                j += 1
            if j >= n:
                raise ValueError(f"Unterminated string in expression: {source!r}")
            tokens.append(_Token("str", "".join(buf)))
            i = j + 1
            continue
        if ch.isdigit() or (ch == "-" and i + 1 < n and source[i + 1].isdigit()):
            j = i + 1
            has_dot = False
            while j < n and (source[j].isdigit() or source[j] == "."):
                if source[j] == ".":
                    has_dot = True
                j += 1
            num_str = source[i:j]
            try:
                value: Any = float(num_str) if has_dot else int(num_str)
            except ValueError as exc:
                raise ValueError(f"Bad number: {num_str}") from exc
            tokens.append(_Token("num", value))
            i = j
            continue
        if ch.isalpha() or ch == "_" or ch == "$":
            j = i + 1
            while j < n and (source[j].isalnum() or source[j] in "_$"):
                j += 1
            word = source[i:j]
            tokens.append(_Token("ident", word))
            i = j
            continue
        if ch == ".":
            tokens.append(_Token(".", "."))
            i += 1
            continue
        raise ValueError(f"Unexpected character {ch!r} in expression: {source!r}")
    return tokens


class _Parser:
    """Recursive descent parser for the expression grammar."""

    def __init__(self, tokens: list[_Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> _Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> _Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> _Token:
        tok = self.peek()
        if tok is None or tok.kind != kind:
            raise ValueError(f"Expected {kind}, got {tok}")
        return self.advance()

    def parse(self, ctx_lookup: Callable[[str], Any]) -> Any:
        """Evaluate expression against runtime context lookup."""
        result = self._primary(ctx_lookup)
        if self.peek() is not None:
            extra = self.peek()
            raise ValueError(f"Unexpected token after expression: {extra}")
        return result

    def _primary(self, ctx_lookup: Callable[[str], Any]) -> Any:
        tok = self.peek()
        if tok is None:
            return ""
        if tok.kind in {"str", "num"}:
            self.advance()
            return self._postfix(tok.value)
        if tok.kind == "ident":
            self.advance()
            nxt = self.peek()
            if nxt is not None and nxt.kind == "(":
                return self._call(tok.value, ctx_lookup)
            base = ctx_lookup(tok.value)
            if tok.value in {"true", "false"} and base is None:
                base = tok.value == "true"
            elif tok.value == "null" and base is None:
                base = None
            return self._postfix(base, ctx_lookup)
        raise ValueError(f"Unexpected token: {tok}")

    def _call(self, name: str, ctx_lookup: Callable[[str], Any]) -> Any:
        helper = _HELPERS.get(name)
        if helper is None:
            raise ValueError(f"Unknown helper: {name}()")
        self.expect("(")
        args: list[Any] = []
        if self.peek() and self.peek().kind != ")":
            args.append(self._primary(ctx_lookup))
            while self.peek() and self.peek().kind == ",":
                self.advance()
                args.append(self._primary(ctx_lookup))
        self.expect(")")
        try:
            return helper(*args)
        except Exception as exc:
            logger.warning("Helper %s failed: %s", name, exc)
            return ""

    def _postfix(self, base: Any, ctx_lookup: Callable[[str], Any] | None = None) -> Any:
        value = base
        while True:
            tok = self.peek()
            if tok is None:
                return value
            if tok.kind == ".":
                self.advance()
                ident = self.expect("ident")
                value = _resolve_attr(value, ident.value)
            elif tok.kind == "[":
                self.advance()
                idx_tok = self.peek()
                if idx_tok is None:
                    raise ValueError("Empty index")
                if idx_tok.kind == "num":
                    self.advance()
                    value = _resolve_index(value, idx_tok.value)
                elif idx_tok.kind == "str":
                    self.advance()
                    value = _resolve_attr(value, str(idx_tok.value))
                else:
                    raise ValueError(f"Unsupported index: {idx_tok}")
                self.expect("]")
            else:
                return value


def _resolve_attr(value: Any, key: str) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(key)
    if hasattr(value, key):
        return getattr(value, key)
    return None


def _resolve_index(value: Any, idx: int) -> Any:
    if isinstance(value, (list, tuple)):
        return value[idx] if -len(value) <= idx < len(value) else None
    if isinstance(value, str):
        return value[idx] if -len(value) <= idx < len(value) else ""
    return None


def evaluate(expression: str, scope: dict[str, Any]) -> Any:
    """Evaluate single ``{{ ... }}`` expression body against scope.

    Args:
        expression: Expression body without the surrounding braces.
        scope: Top-level identifiers (e.g. ``trigger``, ``state``, node ids).

    Returns:
        Evaluated value (any JSON-serializable type).
    """
    tokens = _tokenize(expression)
    if not tokens:
        return ""

    def lookup(name: str) -> Any:
        if name in scope:
            return scope[name]
        if name == "true":
            return True
        if name == "false":
            return False
        if name == "null":
            return None
        return None

    parser = _Parser(tokens)
    return parser.parse(lookup)


def render_template(value: Any, scope: dict[str, Any]) -> Any:
    """Render template-with-expressions inside a string or recursively in dict/list.

    If the input string is a single ``{{ ... }}`` expression, returns the
    evaluated value with its native type (dict, list, etc.). Otherwise, all
    expressions are converted to strings and substituted.

    Args:
        value: Input string, dict, list, or scalar.
        scope: Variables available to expressions.

    Returns:
        Rendered value.
    """
    if isinstance(value, str):
        return _render_string(value, scope)
    if isinstance(value, dict):
        return {k: render_template(v, scope) for k, v in value.items()}
    if isinstance(value, list):
        return [render_template(v, scope) for v in value]
    return value


def _render_string(text: str, scope: dict[str, Any]) -> Any:
    if "{{" not in text:
        return text

    matches = list(_EXPR_RE.finditer(text))
    if not matches:
        return text

    if len(matches) == 1 and matches[0].group(0) == text.strip():
        try:
            return evaluate(matches[0].group(1), scope)
        except ValueError as exc:
            logger.warning("Expression eval failed (%s) in %r", exc, text)
            return text

    def _replace(match: re.Match[str]) -> str:
        try:
            result = evaluate(match.group(1), scope)
        except ValueError as exc:
            logger.warning("Expression eval failed (%s) in %r", exc, match.group(0))
            return match.group(0)
        if result is None:
            return ""
        if isinstance(result, (dict, list)):
            return _safe_json(result)
        return str(result)

    return _EXPR_RE.sub(_replace, text)
