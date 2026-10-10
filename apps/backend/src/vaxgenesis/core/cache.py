"""Redis-backed query cache (audit 5.4).

Provides:
  - `cached(ttl=...)` decorator for FastAPI route handlers and service
    functions that return JSON-serializable results.
  - Cache key is derived from function name + sorted kwargs.
  - Cache invalidation via `invalidate(prefix)` for tagged invalidation.
  - Fallback to no-op cache when Redis is unavailable.

Usage:
    from vaxgenesis.core.cache import cached

    @cached(ttl=300, key_prefix="candidates")
    async def list_candidates(project_id: str, ...): ...
"""
from __future__ import annotations

import functools
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import Any

from vaxgenesis.config_audit_v11 import audit_v11_settings
from vaxgenesis.core.logging import get_logger

logger = get_logger(__name__)


class QueryCache:
    """Redis-backed query cache with graceful degradation."""

    def __init__(self) -> None:
        self._redis: Any | None = None
        self._local_fallback: dict[str, tuple[float, Any]] = {}
        self._enabled = audit_v11_settings.query_cache_enabled

    def _get_redis(self) -> Any | None:
        if not self._enabled:
            return None
        if self._redis is None:
            try:
                import redis
                from vaxgenesis.config import settings as v1_settings
                self._redis = redis.from_url(
                    str(v1_settings.redis_url),
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                )
                self._redis.ping()
            except Exception as exc:
                # Use plain stdlib logging since structlog may not be configured
                import logging
                logging.getLogger("vaxgenesis.cache").warning(
                    "cache.redis_unavailable error=%s", str(exc)
                )
                self._redis = None
                self._enabled = False
        return self._redis

    async def get(self, key: str) -> Any | None:
        redis = self._get_redis()
        if redis is not None:
            try:
                raw = redis.get(f"vcx:{key}")
                if raw:
                    return json.loads(raw)
            except Exception as exc:
                import logging
                logging.getLogger("vaxgenesis.cache").warning(
                    "cache.get_failed key=%s error=%s", key, str(exc)
                )
        else:
            entry = self._local_fallback.get(key)
            if entry and entry[0] > 0:
                import time
                if time.time() < entry[0]:
                    return entry[1]
                del self._local_fallback[key]
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or audit_v11_settings.query_cache_default_ttl_seconds
        redis = self._get_redis()
        if redis is not None:
            try:
                redis.setex(f"vcx:{key}", ttl, json.dumps(value, default=str))
            except Exception as exc:
                import logging
                logging.getLogger("vaxgenesis.cache").warning(
                    "cache.set_failed key=%s error=%s", key, str(exc)
                )
                # Fall through to local fallback
        # Always also store in local fallback (works without redis)
        import time
        self._local_fallback[key] = (time.time() + ttl, value)
        if len(self._local_fallback) > audit_v11_settings.query_cache_max_size:
            oldest = sorted(self._local_fallback.items(), key=lambda x: x[1][0])
            for k, _ in oldest[:100]:
                self._local_fallback.pop(k, None)

    async def invalidate(self, prefix: str) -> int:
        """Invalidate all keys matching the given prefix."""
        redis = self._get_redis()
        if redis is not None:
            try:
                keys = redis.keys(f"vcx:{prefix}*")
                if keys:
                    redis.delete(*keys)
                return len(keys)
            except Exception:
                return 0
        else:
            to_remove = [k for k in self._local_fallback if k.startswith(prefix)]
            for k in to_remove:
                self._local_fallback.pop(k, None)
            return len(to_remove)


# Singleton
query_cache = QueryCache()


def cached(ttl: int = 300, key_prefix: str = "") -> Callable:
    """Decorator: cache the result of an async function.

    Cache key = sha256(key_prefix + function_name + sorted kwargs).
    """
    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [key_prefix or fn.__name__]
            # Skip 'self' / 'cls' for methods
            arg_str = str(args[1:]) if args and hasattr(args[0], "__dict__") else str(args)
            key_parts.append(arg_str)
            key_parts.append(json.dumps(kwargs, sort_keys=True, default=str))
            cache_key = hashlib.sha256("|".join(key_parts).encode()).hexdigest()

            cached_val = await query_cache.get(cache_key)
            if cached_val is not None:
                return cached_val

            result = await fn(*args, **kwargs)
            await query_cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
