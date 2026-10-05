"""Async Redis caching utilities with graceful fallback.

If Redis is not running, all cache operations silently return None/do nothing
so the API continues to work without cache — it just hits the DB every time.
"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """Returns a shared async Redis client, or None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await client.ping()
            _redis_client = client
            logger.info("Redis connection established: %s", settings.REDIS_URL)
        except Exception as exc:
            logger.warning("Redis unavailable (%s). All requests will hit the DB.", exc)
            _redis_client = None
    return _redis_client


async def cache_get(key: str) -> Optional[Any]:
    """Retrieves and deserializes a cached value. Returns None on miss or error."""
    client = await get_redis()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:
        logger.warning("Redis GET error for '%s': %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Serializes and stores value in Redis with a TTL (seconds). Silently fails."""
    client = await get_redis()
    if client is None:
        return
    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.warning("Redis SET error for '%s': %s", key, exc)


async def cache_delete(*keys: str) -> None:
    """Deletes one or more cache keys. Silently fails."""
    client = await get_redis()
    if client is None:
        return
    try:
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.warning("Redis DEL error for %s: %s", keys, exc)
