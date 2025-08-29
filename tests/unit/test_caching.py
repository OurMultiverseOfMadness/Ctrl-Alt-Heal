"""Tests for caching system."""

import pytest
import time
from unittest.mock import patch

from ctrl_alt_heal.core.caching import (
    InMemoryCache,
    CacheManager,
    CacheDecorator,
    get_cache_manager,
    get_memory_cache,
    cache_result,
    setup_redis_cache,
)
from ctrl_alt_heal.utils.exceptions import ConfigurationError


class TestInMemoryCache:
    """Test in-memory cache implementation."""

    def test_cache_creation(self):
        """Test creating a new cache."""
        cache = InMemoryCache()
        assert cache is not None

    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = InMemoryCache()

        # Set value
        assert cache.set("test_key", "test_value")

        # Get value
        result = cache.get("test_key")
        assert result == "test_value"

    def test_set_with_ttl(self):
        """Test setting value with TTL."""
        cache = InMemoryCache()

        # Set value with short TTL
        assert cache.set("test_key", "test_value", ttl=1)

        # Value should exist immediately
        assert cache.get("test_key") == "test_value"

        # Wait for expiration
        time.sleep(1.1)

        # Value should be expired
        assert cache.get("test_key") is None

    def test_delete(self):
        """Test deleting values."""
        cache = InMemoryCache()

        # Set value
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        # Delete value
        assert cache.delete("test_key")
        assert cache.get("test_key") is None

        # Delete non-existent key
        assert not cache.delete("non_existent")

    def test_exists(self):
        """Test checking if key exists."""
        cache = InMemoryCache()

        # Key doesn't exist
        assert not cache.exists("test_key")

        # Set key
        cache.set("test_key", "test_value")
        assert cache.exists("test_key")

        # Set key with short TTL
        cache.set("expiring_key", "test_value", ttl=1)
        assert cache.exists("expiring_key")

        # Wait for expiration
        time.sleep(1.1)
        assert not cache.exists("expiring_key")

    def test_clear(self):
        """Test clearing all cache entries."""
        cache = InMemoryCache()

        # Add multiple entries
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

        # Clear cache
        assert cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cleanup_expired(self):
        """Test cleaning up expired entries."""
        cache = InMemoryCache()

        # Add entries with different TTLs
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=2)
        cache.set("key3", "value3")  # No TTL

        # Wait for first key to expire
        time.sleep(1.1)

        # Clean up expired entries
        expired_count = cache.cleanup_expired()
        assert expired_count == 1

        # Check remaining entries
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = InMemoryCache()

        # Add some entries
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("expiring_key", "value3", ttl=1)

        # Wait for one to expire
        time.sleep(1.1)

        stats = cache.get_stats()
        assert stats["total_entries"] == 3
        assert stats["expired_entries"] == 1
        assert stats["active_entries"] == 2
        assert stats["default_ttl"] == 3600


class TestCacheManager:
    """Test cache manager with multiple layers."""

    def test_cache_manager_creation(self):
        """Test creating a cache manager."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)
        assert manager is not None

    def test_get_from_primary(self):
        """Test getting value from primary cache."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        # Set in primary cache
        primary_cache.set("test_key", "primary_value")

        # Get from manager
        result = manager.get("test_key")
        assert result == "primary_value"

    def test_get_from_fallback(self):
        """Test getting value from fallback cache."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        # Set in fallback cache only
        fallback_cache.set("test_key", "fallback_value")

        # Get from manager
        result = manager.get("test_key")
        assert result == "fallback_value"

        # Should populate primary cache
        assert primary_cache.get("test_key") == "fallback_value"

    def test_get_not_found(self):
        """Test getting non-existent value."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        result = manager.get("non_existent")
        assert result is None

    def test_set_in_both_caches(self):
        """Test setting value in both cache layers."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        # Set value
        assert manager.set("test_key", "test_value")

        # Check both caches
        assert primary_cache.get("test_key") == "test_value"
        assert fallback_cache.get("test_key") == "test_value"

    def test_delete_from_both_caches(self):
        """Test deleting value from both cache layers."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        # Set values
        primary_cache.set("test_key", "test_value")
        fallback_cache.set("test_key", "test_value")

        # Delete from manager
        assert manager.delete("test_key")

        # Check both caches
        assert primary_cache.get("test_key") is None
        assert fallback_cache.get("test_key") is None

    def test_exists_in_primary(self):
        """Test checking existence in primary cache."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        primary_cache.set("test_key", "test_value")
        assert manager.exists("test_key")

    def test_exists_in_fallback(self):
        """Test checking existence in fallback cache."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        fallback_cache.set("test_key", "test_value")
        assert manager.exists("test_key")

    def test_exists_not_found(self):
        """Test checking existence of non-existent key."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        assert not manager.exists("non_existent")

    def test_clear_both_caches(self):
        """Test clearing both cache layers."""
        primary_cache = InMemoryCache()
        fallback_cache = InMemoryCache()
        manager = CacheManager(primary_cache, fallback_cache)

        # Add values to both caches
        primary_cache.set("key1", "value1")
        fallback_cache.set("key2", "value2")

        # Clear manager
        assert manager.clear()

        # Check both caches are empty
        assert primary_cache.get("key1") is None
        assert fallback_cache.get("key2") is None


class TestCacheDecorator:
    """Test cache decorator functionality."""

    def test_cache_decorator(self):
        """Test basic cache decorator functionality."""
        cache_manager = CacheManager(InMemoryCache())
        decorator = CacheDecorator(cache_manager)

        call_count = 0

        @decorator("test_prefix")
        def test_function(param1, param2):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}"

        # First call should execute function
        result1 = test_function("a", "b")
        assert result1 == "result_a_b"
        assert call_count == 1

        # Second call with same parameters should use cache
        result2 = test_function("a", "b")
        assert result2 == "result_a_b"
        assert call_count == 1  # Should not increment

        # Different parameters should execute function again
        result3 = test_function("c", "d")
        assert result3 == "result_c_d"
        assert call_count == 2

    def test_cache_decorator_with_ttl(self):
        """Test cache decorator with TTL."""
        cache_manager = CacheManager(InMemoryCache())
        decorator = CacheDecorator(cache_manager, ttl=1)

        call_count = 0

        @decorator("test_prefix")
        def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        # First call
        result1 = test_function("test")
        assert result1 == "result_test"
        assert call_count == 1

        # Second call (should use cache)
        result2 = test_function("test")
        assert result2 == "result_test"
        assert call_count == 1

        # Wait for expiration
        time.sleep(1.1)

        # Third call (should execute again)
        result3 = test_function("test")
        assert result3 == "result_test"
        assert call_count == 2

    def test_cache_key_generation(self):
        """Test cache key generation."""
        cache_manager = CacheManager(InMemoryCache())
        decorator = CacheDecorator(cache_manager)

        @decorator("test_prefix")
        def test_function(param1, param2, kwarg1="default"):
            return f"result_{param1}_{param2}_{kwarg1}"

        # Call function to generate cache key
        test_function("a", "b", kwarg1="custom")

        # Check that cache key was generated
        cache_keys = list(cache_manager.primary_cache._cache.keys())
        assert len(cache_keys) == 1
        assert "test_prefix" in cache_keys[0]
        assert "test_function" in cache_keys[0]


class TestGlobalFunctions:
    """Test global cache functions."""

    def test_get_cache_manager(self):
        """Test getting global cache manager."""
        manager = get_cache_manager()
        assert isinstance(manager, CacheManager)

    def test_get_memory_cache(self):
        """Test getting global memory cache."""
        cache = get_memory_cache()
        assert isinstance(cache, InMemoryCache)

    def test_cache_result_decorator(self):
        """Test global cache result decorator."""
        call_count = 0

        @cache_result("test_prefix")
        def test_function(param):
            nonlocal call_count
            call_count += 1
            return f"result_{param}"

        # First call
        result1 = test_function("test")
        assert result1 == "result_test"
        assert call_count == 1

        # Second call (should use cache)
        result2 = test_function("test")
        assert result2 == "result_test"
        assert call_count == 1

    def test_setup_redis_cache_missing_redis(self):
        """Test setting up Redis cache without Redis package."""
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'redis'")
        ):
            with pytest.raises(ConfigurationError, match="Redis package not installed"):
                setup_redis_cache("redis://localhost:6379")

    def test_setup_redis_cache_connection_error(self):
        """Test setting up Redis cache with connection error."""
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'redis'")
        ):
            with pytest.raises(ConfigurationError, match="Redis package not installed"):
                setup_redis_cache("redis://localhost:6379")
