"""Redis-backed session cache with SQLite fallback.

Stores chat session history in Redis with TTL. Falls back to
state_db (SQLite) if Redis is unavailable.
"""
import json
import logging
import hashlib
from typing import Optional, List, Dict

from core.redis_client import redis_client
from core.state_db import StateDB

logger = logging.getLogger(__name__)

_state_db: StateDB | None = None


def _get_state_db() -> StateDB:
    """Lazy StateDB singleton — avoids import-time failure if data/ is missing."""
    global _state_db
    if _state_db is None:
        _state_db = StateDB()
    return _state_db


class SessionCache:
    """Two-tier session cache: Redis (hot) -> SQLite (warm)."""

    DEFAULT_TTL = 3600  # 1 hour

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"session:{session_id}"

    @staticmethod
    def _messages_key(session_id: str) -> str:
        return f"session:{session_id}:messages"

    @staticmethod
    async def get_messages(session_id: str) -> List[Dict]:
        """Get message history for session."""
        # Try Redis first
        try:
            data = await redis_client.get(SessionCache._messages_key(session_id))
            if data:
                messages = json.loads(data)
                # Extend TTL on access
                await redis_client.set(
                    SessionCache._messages_key(session_id),
                    data,
                    expire=SessionCache.DEFAULT_TTL
                )
                return messages
        except Exception as e:
            logger.debug("Redis session miss: %s", e)

        # Fallback to SQLite (read-only — populate Redis cache without rewriting DB)
        try:
            messages = _get_state_db().get_messages(session_id)
            if messages:
                try:
                    data = json.dumps(messages, ensure_ascii=False, default=str)
                    await redis_client.set(
                        SessionCache._messages_key(session_id),
                        data,
                        expire=SessionCache.DEFAULT_TTL,
                    )
                except Exception as cache_exc:
                    logger.debug("Redis session cache populate failed: %s", cache_exc)
            return messages
        except Exception as e:
            logger.warning("SQLite session fallback failed: %s", e)
            return []

    @staticmethod
    async def set_messages(session_id: str, messages: List[Dict]) -> bool:
        """Store message history. Returns True if stored in Redis."""
        try:
            data = json.dumps(messages, ensure_ascii=False, default=str)
            return await redis_client.set(
                SessionCache._messages_key(session_id),
                data,
                expire=SessionCache.DEFAULT_TTL
            )
        except Exception as e:
            logger.debug("Redis session store failed: %s", e)
            # Fallback to SQLite
            try:
                _get_state_db().save_messages(session_id, messages)
                return False
            except Exception as e2:
                logger.warning("SQLite session store failed: %s", e2)
                return False

    @staticmethod
    async def append_message(session_id: str, message: Dict) -> bool:
        """Append single message to session history."""
        messages = await SessionCache.get_messages(session_id)
        messages.append(message)
        return await SessionCache.set_messages(session_id, messages)

    @staticmethod
    async def clear(session_id: str) -> bool:
        """Clear session from both Redis and SQLite."""
        try:
            await redis_client.delete(SessionCache._messages_key(session_id))
        except Exception:
            pass
        try:
            _get_state_db().clear_session(session_id)
        except Exception:
            pass
        return True

    @staticmethod
    async def get_metadata(session_id: str) -> Optional[Dict]:
        """Get session metadata (agent_id, model, created_at, etc)."""
        try:
            data = await redis_client.get(SessionCache._session_key(session_id))
            if data:
                return json.loads(data)
        except Exception:
            pass
        return None

    @staticmethod
    async def set_metadata(session_id: str, metadata: Dict) -> bool:
        """Store session metadata."""
        try:
            return await redis_client.set(
                SessionCache._session_key(session_id),
                json.dumps(metadata, default=str),
                expire=SessionCache.DEFAULT_TTL
            )
        except Exception:
            return False


class ResponseCache:
    """LLM response cache to avoid repeated identical queries.

    Keys are hashed from (model, prompt, tools_hash) for uniqueness.
    TTL is short (5 min) to balance speed vs freshness.
    """

    DEFAULT_TTL = 300  # 5 minutes

    @staticmethod
    def _make_key(model: str, prompt: str, tools: Optional[List] = None) -> str:
        """Create deterministic cache key."""
        tools_str = json.dumps(tools, sort_keys=True) if tools else ""
        raw = f"{model}:{prompt}:{tools_str}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    @staticmethod
    async def get(model: str, prompt: str, tools: Optional[List] = None) -> Optional[str]:
        """Get cached response if available."""
        key = ResponseCache._make_key(model, prompt, tools)
        try:
            return await redis_client.get_cached_response(key)
        except Exception:
            return None

    @staticmethod
    async def set(model: str, prompt: str, response: str, tools: Optional[List] = None) -> bool:
        """Cache a response."""
        key = ResponseCache._make_key(model, prompt, tools)
        try:
            return await redis_client.cache_response(key, response, expire=ResponseCache.DEFAULT_TTL)
        except Exception:
            return False

    @staticmethod
    async def invalidate(model: str, prompt: str, tools: Optional[List] = None) -> bool:
        """Remove a cached response."""
        key = ResponseCache._make_key(model, prompt, tools)
        try:
            return await redis_client.delete(f"cache:{key}")
        except Exception:
            return False


class RateLimiter:
    """Distributed rate limiter using Redis sliding window.

    More accurate than slowapi's fixed window for burst handling.
    """

    @staticmethod
    async def check(
        identifier: str,
        action: str,
        limit: int = 60,
        window: int = 60
    ) -> tuple[bool, int, int]:
        """Check rate limit.

        Returns: (allowed, remaining, reset_after)
        """
        key = f"ratelimit:{action}:{identifier}"
        allowed, remaining = await redis_client.check_rate_limit(key, limit, window)
        reset_after = window if not allowed else 0
        return allowed, remaining, reset_after
