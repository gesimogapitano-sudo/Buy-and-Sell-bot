"""Shared Redis client used for cross-process coordination."""

from __future__ import annotations

from typing import Any, Optional

from app.config import get_settings

_client: Optional[object] = None


def get_redis() -> Optional[Any]:
    """Return the shared Redis client, or None when Redis is disabled."""
    global _client
    settings = get_settings()
    if not settings.redis_url:
        return None
    if _client is None:
        from redis.asyncio import Redis

        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_redis() -> None:
    """Close the shared Redis connection pool."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
