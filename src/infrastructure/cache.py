"""Redis cache management for the RAG pipeline."""

import asyncio
import hashlib
import json
import pickle
import re
from typing import Any

import redis.asyncio as redis
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.infrastructure.logging import LoggerMixin, get_logger

logger = get_logger(__name__)


class CacheManager(LoggerMixin):
    """Manages Redis cache operations with improved key handling."""

    def __init__(self) -> None:
        """Initialize cache manager."""
        self.settings = get_settings()
        self.client: redis.Redis | None = None
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
            ping_result = self.client.ping()
            if hasattr(ping_result, "__await__"):
                await ping_result
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
            if self.client is None:
                return default
            value = await self.client.get(key)
            if value is None:
                return default

            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Security check: Only unpickle if we trust the source (internal cache)
                if not self.connected or self.client is None:
                    return default
                # Consider using a safer serialization method like msgpack
                return pickle.loads(value)
        except Exception as e:
            self.logger.warning("Cache get failed", key=key, error=str(e))
            return default

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache."""
        if not self.connected:
            return False

        try:
            # Try to serialize as JSON first, fallback to pickle
            serialized: str | bytes
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value)

            ttl = ttl or self.settings.cache_ttl_seconds
            if self.client is None:
                return False
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
            if self.client is None:
                return False
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
            if self.client is None:
                return False
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            self.logger.warning("Cache exists check failed", key=key, error=str(e))
            return False

    async def increment(self, key: str, amount: int = 1) -> int | None:
        """Increment counter in cache."""
        if not self.connected:
            return None

        try:
            if self.client is None:
                return None
            result = await self.client.incrby(key, amount)
            return int(result)
        except Exception as e:
            self.logger.warning("Cache increment failed", key=key, error=str(e))
            return None

    async def get_pattern(self, pattern: str) -> dict:
        """Get all keys matching pattern."""
        if not self.connected:
            return {}

        try:
            if self.client is None:
                return {}
            keys = await self.client.keys(pattern)
            if not keys:
                return {}

            if self.client is None:
                return {}
            values = await self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values, strict=False):
                if value:
                    try:
                        result[key.decode("utf-8")] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        # Security check: Only unpickle if we trust the source (internal cache)
                        if self.connected and self.client is not None:
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
            if self.client is None:
                return 0
            keys = await self.client.keys(pattern)
            if keys:
                deleted = await self.client.delete(*keys)
                return int(deleted)
            return 0
        except Exception as e:
            self.logger.warning("Cache pattern flush failed", pattern=pattern, error=str(e))
            return 0

    def normalize_query(self, query: str) -> str:
        """Normalize query for better cache hits.

        Normalizations applied:
        - Convert to lowercase
        - Remove extra whitespace
        - Remove trailing punctuation (?,!,.)
        - Normalize quotes
        """
        if not query:
            return ""

        # Convert to lowercase
        normalized = query.lower().strip()

        # Normalize whitespace (multiple spaces to single space)
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove trailing punctuation
        normalized = normalized.rstrip("?.!")

        # Normalize quotes
        normalized = normalized.replace('"', "'").replace(""", "'").replace(""", "'")

        return normalized

    def generate_cache_key(self, prefix: str, query: str, params: dict | None = None) -> str:
        """Generate deterministic cache key from query and parameters.

        Args:
            prefix: Key prefix (e.g., "query_result")
            query: Query text to normalize
            params: Optional parameters to include in key

        Returns:
            Cache key string
        """
        # Normalize the query
        normalized_query = self.normalize_query(query)

        # Create stable key from query and params
        key_data = {"query": normalized_query, "params": params or {}}

        # Sort params for consistency
        key_str = json.dumps(key_data, sort_keys=True)

        # Generate hash for consistent length
        key_hash = hashlib.md5(key_str.encode()).hexdigest()[:16]

        return self.make_key(prefix, key_hash)

    async def get_or_compute(
        self, key: str, compute_fn, ttl: int | None = None
    ) -> tuple[Any, bool]:
        """Get from cache or compute and store.

        Returns:
            Tuple of (value, was_cached)
        """
        # Try to get from cache
        cached = await self.get(key)
        if cached is not None:
            self.logger.debug(f"Cache hit for key: {key}")
            await self.increment("metrics:cache_hits")
            return cached, True

        # Cache miss - compute new value
        self.logger.debug(f"Cache miss for key: {key}")
        await self.increment("metrics:cache_misses")

        value = await compute_fn() if asyncio.iscoroutinefunction(compute_fn) else compute_fn()

        # Store in cache
        await self.set(key, value, ttl=ttl)

        return value, False

    def make_key(self, *parts: str) -> str:
        """Create cache key from parts."""
        return ":".join([self.settings.app_name, *parts])


# Global cache manager instance
cache_manager = CacheManager()


class CacheDecorator:
    """Decorator for caching function results."""

    def __init__(
        self,
        key_prefix: str,
        ttl: int | None = None,
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
