import json
import logging
from typing import Any, Optional
import redis

from app.core.config import settings

logger = logging.getLogger("intelliops.cache")


class RedisCacheClient:
    """
    Resilient Redis client wrapper implementing graceful failover.
    If Redis is unavailable or throws errors, all operations return None/False
    and log warnings without raising exceptions to API routes.
    """

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Redis client: {str(e)}")
                self._client = None
        return self._client

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves and deserializes JSON cached value for given key.
        Returns None on cache miss, invalid JSON, or Redis error.
        """
        try:
            r = self.client
            if not r:
                return None
            data = r.get(key)
            if data is not None:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Redis GET failed for key '{key}': {str(e)}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Serializes and sets a JSON cache entry with TTL seconds.
        Returns True on success, False on failure.
        """
        try:
            r = self.client
            if not r:
                return False
            ex = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
            serialized = json.dumps(value, default=str)
            r.set(name=key, value=serialized, ex=ex)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key '{key}': {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Deletes a single cache key.
        """
        try:
            r = self.client
            if not r:
                return False
            r.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE failed for key '{key}': {str(e)}")
            return False

    def delete_pattern(self, pattern: str) -> bool:
        """
        Invalidates all keys matching the given pattern (e.g. 'issues:list:*').
        """
        try:
            r = self.client
            if not r:
                return False
            keys = r.keys(pattern)
            if keys:
                r.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE PATTERN failed for '{pattern}': {str(e)}")
            return False


# Singleton Redis client instance
redis_client = RedisCacheClient()
