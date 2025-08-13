"""Redis cache management for the RAG pipeline."""

import json
import pickle
from typing import Any, Optional

import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.infrastructure.logging import LoggerMixin, get_logger

logger = get_logger(__name__)


class CacheManager(LoggerMixin):
    """Manages Redis cache operations."""

    def __init__(self) -> None:
        """Initialize cache manager."""
        self.settings = get_settings()
        self.client: Optional[redis.Redis] = None
        self.connected = False

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.client = redis.from_url(
                str(self.settings.redis_url),
                encoding="utf-8",
                decode_responses=False,
                max_connections=50,
            )
            # Test connection
            await self.client.ping()
            self.connected = True
            self.logger.info("Redis cache initialized")
        except Exception as e:
            self.logger.error("Failed to initialize Redis cache", error=str(e))
            self.connected = False
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.connected = False
            self.logger.info("Redis cache connection closed")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not self.connected:
            return default

        try:
            value = await self.client.get(key)
            if value is None:
                return default

            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value)
        except Exception as e:
            self.logger.warning("Cache get failed", key=key, error=str(e))
            return default

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache."""
        if not self.connected:
            return False

        try:
            # Try to serialize as JSON first, fallback to pickle
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)

            ttl = ttl or self.settings.cache_ttl_seconds
            await self.client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            self.logger.warning("Cache set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.connected:
            return False

        try:
            result = await self.client.delete(key)
            return bool(result)
        except Exception as e:
            self.logger.warning("Cache delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.connected:
            return False

        try:
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            self.logger.warning("Cache exists check failed", key=key, error=str(e))
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache."""
        if not self.connected:
            return None

        try:
            result = await self.client.incrby(key, amount)
            return result
        except Exception as e:
            self.logger.warning("Cache increment failed", key=key, error=str(e))
            return None

    async def get_pattern(self, pattern: str) -> dict:
        """Get all keys matching pattern."""
        if not self.connected:
            return {}

        try:
            keys = await self.client.keys(pattern)
            if not keys:
                return {}

            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key.decode("utf-8")] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key.decode("utf-8")] = pickle.loads(value)
            return result
        except Exception as e:
            self.logger.warning("Cache pattern get failed", pattern=pattern, error=str(e))
            return {}

    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.connected:
            return 0

        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            self.logger.warning("Cache pattern flush failed", pattern=pattern, error=str(e))
            return 0

    def make_key(self, *parts: str) -> str:
        """Create cache key from parts."""
        return ":".join([self.settings.app_name] + list(parts))


# Global cache manager instance
cache_manager = CacheManager()


class CacheDecorator:
    """Decorator for caching function results."""

    def __init__(
        self,
        key_prefix: str,
        ttl: Optional[int] = None,
    ):
        """Initialize cache decorator."""
        self.key_prefix = key_prefix
        self.ttl = ttl

    def __call__(self, func):
        """Wrap function with caching."""

        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.make_key(
                self.key_prefix,
                str(hash((str(args), str(sorted(kwargs.items()))))),
            )

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug("Cache hit", key=cache_key)
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, ttl=self.ttl)
            logger.debug("Cache miss, stored result", key=cache_key)

            return result

        return wrapper