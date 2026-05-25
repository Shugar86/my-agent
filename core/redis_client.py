"""Redis client wrapper for My Agent.

Provides async Redis connection with auto-reconnect fallback.
Used for:
- Revoked JWT token blacklist
- Session metadata cache
- Rate-limiting counters (optional)
"""
import os
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


class RedisClient:
    """Async Redis client with lazy initialization."""

    def __init__(self, url: Optional[str] = None):
        self.url = url or REDIS_URL
        self._client = None
        self._available = False

    async def connect(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(self.url, decode_responses=True)
            await self._client.ping()
            self._available = True
            logger.info("Redis connected: %s", self.url)
        except Exception as e:
            self._available = False
            logger.warning("Redis not available (%s). Some features disabled.", e)

    async def close(self):
        if self._client:
            await self._client.close()
            self._available = False

    async def ping(self) -> bool:
        if not self._available or not self._client:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False

    # Token blacklist
    async def revoke_token(self, jti: str, expire_seconds: int = 86400) -> bool:
        if not self._available or not self._client:
            return False
        try:
            await self._client.setex(f"revoked_token:{jti}", expire_seconds, "1")
            return True
        except Exception as e:
            logger.warning("Redis revoke_token failed: %s", e)
            return False

    async def is_token_revoked(self, jti: str) -> bool:
        if not self._available or not self._client:
            return False
        try:
            return await self._client.exists(f"revoked_token:{jti}") > 0
        except Exception:
            return False

    # Generic cache
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        if not self._available or not self._client:
            return False
        try:
            if expire:
                await self._client.setex(key, expire, value)
            else:
                await self._client.set(key, value)
            return True
        except Exception as e:
            logger.warning("Redis set failed: %s", e)
            return False

    async def get(self, key: str) -> Optional[str]:
        if not self._available or not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception:
            return None

    async def delete(self, key: str) -> bool:
        if not self._available or not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception:
            return False

    # Session cache
    async def cache_session(self, session_id: str, data: dict, expire: int = 3600) -> bool:
        """Cache session data with TTL (default 1 hour)."""
        if not self._available or not self._client:
            return False
        try:
            import json
            await self._client.setex(f"session:{session_id}", expire, json.dumps(data))
            return True
        except Exception as e:
            logger.warning("Redis cache_session failed: %s", e)
            return False

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get cached session data."""
        if not self._available or not self._client:
            return None
        try:
            import json
            data = await self._client.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except Exception:
            return None

    async def extend_session_ttl(self, session_id: str, expire: int = 3600) -> bool:
        """Extend session TTL."""
        if not self._available or not self._client:
            return False
        try:
            await self._client.expire(f"session:{session_id}", expire)
            return True
        except Exception:
            return False

    # Response cache for LLM
    async def cache_response(self, key: str, response: str, expire: int = 300) -> bool:
        """Cache LLM response with TTL (default 5 min)."""
        if not self._available or not self._client:
            return False
        try:
            await self._client.setex(f"cache:{key}", expire, response)
            return True
        except Exception as e:
            logger.warning("Redis cache_response failed: %s", e)
            return False

    async def get_cached_response(self, key: str) -> Optional[str]:
        """Get cached LLM response."""
        if not self._available or not self._client:
            return None
        try:
            return await self._client.get(f"cache:{key}")
        except Exception:
            return None

    # Rate limiting helpers
    async def check_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Check if request is within rate limit. Returns (allowed, remaining)."""
        if not self._available or not self._client:
            return True, limit  # Allow if Redis unavailable
        try:
            pipe = self._client.pipeline()
            now = time.time()
            window_key = f"ratelimit:{key}:{int(now // window) * window}"
            pipe.incr(window_key)
            pipe.expire(window_key, window)
            results = await pipe.execute()
            current = results[0]
            allowed = current <= limit
            remaining = max(0, limit - current)
            return allowed, remaining
        except Exception as e:
            logger.warning("Redis rate limit check failed: %s", e)
            return True, limit


# Singleton
redis_client = RedisClient()
