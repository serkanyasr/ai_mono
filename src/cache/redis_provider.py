"""
Redis connection manager and cache provider.

This module provides Redis integration for caching, rate limiting,
and distributed state management.
"""

import json
from typing import Any, Optional, TypeVar
from datetime import timedelta

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from src.config.settings import settings
from src.utils import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RedisConnectionManager:
    """Redis connection manager with async support.

    Handles connection pooling and provides singleton access to Redis client.
    """

    _pool: Optional[ConnectionPool] = None
    _client: Optional[aioredis.Redis] = None

    @classmethod
    async def get_client(cls) -> aioredis.Redis:
        """Get Redis client instance (singleton).

        Creates connection pool on first call and reuses for subsequent calls.

        Returns:
            Redis client instance

        Raises:
            Exception: If Redis connection fails
        """
        if cls._client is None:
            await cls.initialize()
        return cls._client  # type: ignore

    @classmethod
    async def initialize(cls):
        """Initialize Redis connection pool.

        Should be called during application startup.
        """
        if cls._pool is not None:
            return  # Already initialized

        try:
            # Create connection pool
            cls._pool = ConnectionPool.from_url(
                settings.redis_url,
                decode_responses=True,  # Auto-decode bytes to strings
                max_connections=50,  # Maximum connections in pool
                retry_on_timeout=True,
            )

            # Create Redis client
            cls._client = aioredis.Redis(connection_pool=cls._pool)

            # Test connection
            await cls._client.ping()

            logger.info(
                "Redis connection established",
                redis_url=settings.redis_url,
            )

        except Exception as e:
            logger.error(
                "Redis connection failed",
                error=str(e),
                redis_url=settings.redis_url,
            )
            # Create a mock client for graceful degradation
            cls._client = None
            raise

    @classmethod
    async def close(cls):
        """Close Redis connection pool.

        Should be called during application shutdown.
        """
        if cls._client:
            await cls._client.close()
            logger.info("Redis connection closed")

        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None

        cls._client = None

    @classmethod
    def is_connected(cls) -> bool:
        """Check if Redis client is connected.

        Returns:
            True if connected, False otherwise
        """
        return cls._client is not None


class RedisCache:
    """Redis-based cache provider.

    Provides async caching operations with TTL support.

    Example:
        >>> cache = RedisCache()
        >>> await cache.set("key", "value", ttl=3600)
        >>> value = await cache.get("key")
        >>> await cache.delete("key")
    """

    def __init__(self, prefix: str = "cache"):
        """Initialize Redis cache.

        Args:
            prefix: Key prefix for all cache entries
        """
        self._prefix = prefix
        self._default_ttl = settings.redis_cache_ttl

    def _make_key(self, key: str) -> str:
        """Create full key with prefix.

        Args:
            key: Original key

        Returns:
            Key with prefix
        """
        return f"{self._prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key (without prefix)

        Returns:
            Cached value or None if not found
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            value = await client.get(full_key)
            if value is None:
                return None

            # Deserialize JSON
            return json.loads(value)

        except Exception as e:
            logger.warning(
                "Cache get failed",
                key=key,
                error=str(e),
            )
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key (without prefix)
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (uses default if not specified)

        Returns:
            True if successful, False otherwise
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            # Serialize to JSON
            serialized = json.dumps(value)

            # Set with TTL
            ttl_seconds = ttl if ttl is not None else self._default_ttl
            await client.setex(full_key, ttl_seconds, serialized)

            return True

        except Exception as e:
            logger.warning(
                "Cache set failed",
                key=key,
                error=str(e),
            )
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key (without prefix)

        Returns:
            True if key was deleted, False otherwise
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            result = await client.delete(full_key)
            return result > 0

        except Exception as e:
            logger.warning(
                "Cache delete failed",
                key=key,
                error=str(e),
            )
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache.

        Args:
            key: Cache key (without prefix)

        Returns:
            True if key exists, False otherwise
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            result = await client.exists(full_key)
            return result > 0

        except Exception as e:
            logger.warning(
                "Cache exists check failed",
                key=key,
                error=str(e),
            )
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Update TTL for existing key.

        Args:
            key: Cache key (without prefix)
            ttl: New TTL in seconds

        Returns:
            True if successful, False otherwise
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            result = await client.expire(full_key, ttl)
            return result > 0

        except Exception as e:
            logger.warning(
                "Cache expire failed",
                key=key,
                error=str(e),
            )
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key.

        Args:
            key: Cache key (without prefix)

        Returns:
            Remaining TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            return await client.ttl(full_key)

        except Exception as e:
            logger.warning(
                "Cache TTL check failed",
                key=key,
                error=str(e),
            )
            return -2

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "session:*", "user:123:*")

        Returns:
            Number of keys deleted
        """
        client = await RedisConnectionManager.get_client()
        full_pattern = self._make_key(pattern)

        try:
            # Find matching keys
            keys = []
            async for key in client.scan_iter(match=full_pattern):
                keys.append(key)

            # Delete in batch
            if keys:
                return await client.delete(*keys)

            return 0

        except Exception as e:
            logger.warning(
                "Cache clear pattern failed",
                pattern=pattern,
                error=str(e),
            )
            return 0

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter value.

        Args:
            key: Cache key (without prefix)
            amount: Amount to increment by

        Returns:
            New value or None if failed
        """
        client = await RedisConnectionManager.get_client()
        full_key = self._make_key(key)

        try:
            return await client.incrby(full_key, amount)

        except Exception as e:
            logger.warning(
                "Cache increment failed",
                key=key,
                error=str(e),
            )
            return None

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values from cache.

        Args:
            keys: List of cache keys (without prefix)

        Returns:
            Dictionary of key-value pairs for found keys
        """
        if not keys:
            return {}

        client = await RedisConnectionManager.get_client()
        full_keys = [self._make_key(k) for k in keys]

        try:
            values = await client.mget(full_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value

            return result

        except Exception as e:
            logger.warning(
                "Cache get_many failed",
                keys=keys,
                error=str(e),
            )
            return {}

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Set multiple values in cache.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds

        Returns:
            True if all successful, False otherwise
        """
        ttl_seconds = ttl if ttl is not None else self._default_ttl

        try:
            # Set each key with TTL
            for key, value in mapping.items():
                await self.set(key, value, ttl=ttl_seconds)

            return True

        except Exception as e:
            logger.warning(
                "Cache set_many failed",
                error=str(e),
            )
            return False


# Specialized cache instances for different use cases
class SessionCache(RedisCache):
    """Cache for session data."""

    def __init__(self):
        super().__init__(prefix="session")


class UserCache(RedisCache):
    """Cache for user data."""

    def __init__(self):
        super().__init__(prefix="user")


class RateLimitCache(RedisCache):
    """Cache for rate limiting counters."""

    def __init__(self):
        super().__init__(prefix="rate_limit")


# Convenience function to get Redis client
async def get_redis_client() -> aioredis.Redis:
    """Get Redis client instance.

    Convenience function for accessing Redis client.

    Returns:
        Redis client instance
    """
    return await RedisConnectionManager.get_client()


# Singleton instances
_session_cache: Optional[SessionCache] = None
_user_cache: Optional[UserCache] = None
_rate_limit_cache: Optional[RateLimitCache] = None


def get_session_cache() -> SessionCache:
    """Get session cache instance (singleton)."""
    global _session_cache
    if _session_cache is None:
        _session_cache = SessionCache()
    return _session_cache


def get_user_cache() -> UserCache:
    """Get user cache instance (singleton)."""
    global _user_cache
    if _user_cache is None:
        _user_cache = UserCache()
    return _user_cache


def get_rate_limit_cache() -> RateLimitCache:
    """Get rate limit cache instance (singleton)."""
    global _rate_limit_cache
    if _rate_limit_cache is None:
        _rate_limit_cache = RateLimitCache()
    return _rate_limit_cache
