"""
Redis cache helpers.

Provides simple get/set/delete wrappers around the Redis client.
When Redis is unavailable (redis_client is None), all operations
gracefully return None / no-op so the application keeps working
without cache.
"""

import json
import logging

logger = logging.getLogger(__name__)


def _get_client():
    """Lazy import to avoid circular dependency at module load time."""
    from app.extensiones import redis_client
    return redis_client


def cache_get(key):
    """Retrieve a JSON-serialised value from Redis.

    Returns the deserialised Python object, or ``None`` if the key
    does not exist or Redis is unavailable.
    """
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("cache_get(%s) failed: %s", key, exc)
        return None


def cache_set(key, data, ttl=300):
    """Serialise *data* to JSON and store in Redis with a TTL (seconds)."""
    client = _get_client()
    if client is None:
        return
    try:
        client.set(key, json.dumps(data), ex=ttl)
    except Exception as exc:
        logger.warning("cache_set(%s) failed: %s", key, exc)


def cache_delete(key):
    """Remove a single key from Redis."""
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception as exc:
        logger.warning("cache_delete(%s) failed: %s", key, exc)
