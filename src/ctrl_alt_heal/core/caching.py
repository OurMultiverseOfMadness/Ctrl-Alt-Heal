"""Caching system for Ctrl-Alt-Heal application."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional, Callable
import threading

from ctrl_alt_heal.utils.exceptions import ConfigurationError


class CacheInterface:
    """Interface for cache implementations."""

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError

    def clear(self) -> bool:
        """Clear all cache entries."""
        raise NotImplementedError


class InMemoryCache(CacheInterface):
    """In-memory cache implementation."""

    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None

            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            ttl = ttl or self._default_ttl
            expiry = datetime.now() + timedelta(seconds=ttl)

            self._cache[key] = {
                "value": value,
                "expiry": expiry,
                "created_at": datetime.now(),
            }
            return True

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            if key not in self._cache:
                return False

            if self._is_expired(self._cache[key]):
                del self._cache[key]
                return False

            return True

    def clear(self) -> bool:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            return True

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        return datetime.now() > entry["expiry"]

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if self._is_expired(entry)
            ]

            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(
                1 for entry in self._cache.values() if self._is_expired(entry)
            )

            return {
                "total_entries": total_entries,
                "expired_entries": expired_count,
                "active_entries": total_entries - expired_count,
                "default_ttl": self._default_ttl,
            }


class RedisCache(CacheInterface):
    """Redis cache implementation."""

    def __init__(self, redis_client, default_ttl: int = 3600):
        self._redis = redis_client
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self._redis.get(key)
            if value is None:
                return None

            return json.loads(value)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self._default_ttl
            serialized_value = json.dumps(value)
            return self._redis.setex(key, ttl, serialized_value)
        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            return bool(self._redis.delete(key))
        except Exception:
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(self._redis.exists(key))
        except Exception:
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            self._redis.flushdb()
            return True
        except Exception:
            return False


class CacheManager:
    """Cache manager for handling multiple cache layers."""

    def __init__(
        self,
        primary_cache: CacheInterface,
        fallback_cache: Optional[CacheInterface] = None,
    ):
        self.primary_cache = primary_cache
        self.fallback_cache = fallback_cache

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback."""
        # Try primary cache first
        value = self.primary_cache.get(key)
        if value is not None:
            return value

        # Try fallback cache if available
        if self.fallback_cache:
            value = self.fallback_cache.get(key)
            if value is not None:
                # Populate primary cache with fallback value
                self.primary_cache.set(key, value)
                return value

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache layers."""
        success = True

        # Set in primary cache
        if not self.primary_cache.set(key, value, ttl):
            success = False

        # Set in fallback cache if available
        if self.fallback_cache and not self.fallback_cache.set(key, value, ttl):
            success = False

        return success

    def delete(self, key: str) -> bool:
        """Delete value from all cache layers."""
        success = True

        # Delete from primary cache
        if not self.primary_cache.delete(key):
            success = False

        # Delete from fallback cache if available
        if self.fallback_cache and not self.fallback_cache.delete(key):
            success = False

        return success

    def exists(self, key: str) -> bool:
        """Check if key exists in any cache layer."""
        if self.primary_cache.exists(key):
            return True

        if self.fallback_cache and self.fallback_cache.exists(key):
            return True

        return False

    def clear(self) -> bool:
        """Clear all cache layers."""
        success = True

        if not self.primary_cache.clear():
            success = False

        if self.fallback_cache and not self.fallback_cache.clear():
            success = False

        return success


class CacheDecorator:
    """Decorator for caching function results."""

    def __init__(self, cache_manager: CacheManager, ttl: Optional[int] = None):
        self.cache_manager = cache_manager
        self.ttl = ttl

    def __call__(self, key_prefix: str = ""):
        """Create cache decorator with key prefix."""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(key_prefix, func.__name__, args, kwargs)

                # Try to get from cache
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result

                # Execute function and cache result
                result = func(*args, **kwargs)
                self.cache_manager.set(cache_key, result, self.ttl)

                return result

            return wrapper

        return decorator

    def _generate_key(
        self, prefix: str, func_name: str, args: tuple, kwargs: dict
    ) -> str:
        """Generate cache key from function call."""
        # Create a hash of the function call
        key_parts = [prefix, func_name]

        # Add args (skip self for methods)
        if args and hasattr(args[0], "__class__"):
            key_parts.extend([str(arg) for arg in args[1:]])
        else:
            key_parts.extend([str(arg) for arg in args])

        # Add kwargs
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")

        return ":".join(key_parts)


# Global cache instances
_memory_cache = InMemoryCache()
_cache_manager = CacheManager(_memory_cache)


def get_cache_manager() -> CacheManager:
    """Get the global cache manager."""
    return _cache_manager


def get_memory_cache() -> InMemoryCache:
    """Get the global in-memory cache."""
    return _memory_cache


def setup_redis_cache(redis_url: str, default_ttl: int = 3600) -> None:
    """Setup Redis cache as primary cache."""
    try:
        import redis

        redis_client = redis.from_url(redis_url)
        redis_cache = RedisCache(redis_client, default_ttl)

        # Set Redis as primary, memory as fallback
        global _cache_manager
        _cache_manager = CacheManager(redis_cache, _memory_cache)

    except ImportError:
        raise ConfigurationError(
            "Redis package not installed. Install with: pip install redis"
        )
    except Exception as e:
        raise ConfigurationError(f"Failed to setup Redis cache: {str(e)}")


def cache_result(key_prefix: str = "", ttl: Optional[int] = None):
    """Decorator to cache function results."""
    return CacheDecorator(_cache_manager, ttl)(key_prefix)


def invalidate_cache(pattern: str) -> int:
    """Invalidate cache entries matching pattern."""
    # This is a simplified implementation
    # In a real Redis setup, you'd use SCAN and pattern matching
    return 0
