"""Async-native retry utilities with asyncio.sleep."""
import asyncio
import random
import logging

logger = logging.getLogger(__name__)


def jittered_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.5,
) -> float:
    """Calculate delay with full jitter for exponential backoff (sync version)."""
    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
    jitter = random.uniform(0, delay * jitter_factor)
    return delay + jitter


async def async_jittered_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.5,
) -> None:
    """Async sleep with jittered exponential backoff."""
    delay = jittered_backoff(attempt, base_delay, max_delay, jitter_factor)
    logger.debug("Async backoff: sleeping %.2fs (attempt %d)", delay, attempt)
    await asyncio.sleep(delay)
