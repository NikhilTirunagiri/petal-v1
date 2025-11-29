"""Redis cache service for session data and embeddings."""

import redis
import json
import logging
from typing import Optional, List, Dict, Any
import hashlib

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis cache service with graceful degradation."""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """Initialize Redis connection with fallback."""
        self.client: Optional[redis.Redis] = None
        self.enabled = False

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=False,  # We handle JSON ourselves
                socket_timeout=1,  # Don't hang if Redis is down
                socket_connect_timeout=1,
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info("Redis cache enabled")
        except Exception as e:
            logger.warning(f"Redis unavailable, caching disabled: {e}")
            self.client = None
            self.enabled = False

    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return value.decode('utf-8')
            logger.debug(f"Cache miss: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache read error for {key}: {e}")
            return None

    def set(self, key: str, value: str, ttl_seconds: int = 3600):
        """Set value in cache with TTL."""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.setex(key, ttl_seconds, value)
            logger.debug(f"Cached: {key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
            return False

    def delete(self, key: str):
        """Delete key from cache."""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.delete(key)
            logger.debug(f"Deleted cache: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        if not self.enabled or not self.client:
            return False

        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
                logger.info(f"Deleted {len(keys)} keys matching: {pattern}")
            return True
        except Exception as e:
            logger.warning(f"Cache pattern delete error for {pattern}: {e}")
            return False


class SessionCache:
    """Cache for session-specific data."""

    def __init__(self, redis_cache: RedisCache):
        """Initialize with Redis cache."""
        self.cache = redis_cache

    def _session_key(self, session_id: str) -> str:
        """Generate cache key for session metadata."""
        return f"session:{session_id}"

    def _session_memories_key(self, session_id: str) -> str:
        """Generate cache key for session memories."""
        return f"session:{session_id}:memories"

    def _session_description_key(self, session_id: str) -> str:
        """Generate cache key for session description."""
        return f"session:{session_id}:description"

    async def warm_session_cache(self, session_id: str, session_data: Dict[str, Any], memories: List[Dict[str, Any]]):
        """Pre-load session data into cache."""
        try:
            # Cache session metadata (1 hour TTL)
            self.cache.set(
                self._session_key(session_id),
                json.dumps(session_data),
                ttl_seconds=3600
            )

            # Cache recent memories (10 min TTL - they change often)
            self.cache.set(
                self._session_memories_key(session_id),
                json.dumps(memories),
                ttl_seconds=600
            )

            logger.info(f"Warmed cache for session {session_id}: {len(memories)} memories")
        except Exception as e:
            logger.error(f"Failed to warm session cache: {e}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata from cache."""
        try:
            cached = self.cache.get(self._session_key(session_id))
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Error reading session from cache: {e}")
            return None

    def get_session_memories(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get session memories from cache."""
        try:
            cached = self.cache.get(self._session_memories_key(session_id))
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Error reading memories from cache: {e}")
            return None

    def invalidate_session_memories(self, session_id: str):
        """Invalidate cached memories for a session."""
        self.cache.delete(self._session_memories_key(session_id))
        logger.debug(f"Invalidated memories cache for session {session_id}")

    def invalidate_session(self, session_id: str):
        """Invalidate all cache for a session."""
        self.cache.delete_pattern(f"session:{session_id}:*")
        self.cache.delete(self._session_key(session_id))
        logger.info(f"Invalidated all cache for session {session_id}")

    def get_session_description(self, session_id: str) -> Optional[str]:
        """Get cached session description."""
        try:
            cached = self.cache.get(self._session_description_key(session_id))
            if cached:
                return cached
            return None
        except Exception as e:
            logger.error(f"Error reading description from cache: {e}")
            return None

    def set_session_description(self, session_id: str, description: str):
        """Cache session description (no TTL - permanent until invalidated)."""
        try:
            self.cache.set(self._session_description_key(session_id), description)
            logger.debug(f"Cached description for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to cache description: {e}")

    def invalidate_session_description(self, session_id: str):
        """Invalidate cached description for a session."""
        self.cache.delete(self._session_description_key(session_id))
        logger.debug(f"Invalidated description cache for session {session_id}")


class EmbeddingCache:
    """Cache for embedding vectors."""

    def __init__(self, redis_cache: RedisCache):
        """Initialize with Redis cache."""
        self.cache = redis_cache

    def _embedding_key(self, text: str) -> str:
        """Generate cache key for embedding."""
        # Hash the text to create a fixed-length key
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"embed:v1:{text_hash}"

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        try:
            cache_key = self._embedding_key(text)
            cached = self.cache.get(cache_key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error(f"Error reading embedding from cache: {e}")
            return None

    def save_embedding(self, text: str, embedding: List[float], ttl_seconds: int = 86400):
        """Save embedding to cache (24 hour TTL by default)."""
        try:
            cache_key = self._embedding_key(text)
            self.cache.set(
                cache_key,
                json.dumps(embedding),
                ttl_seconds=ttl_seconds
            )
            logger.debug(f"Cached embedding for {len(text)} chars")
        except Exception as e:
            logger.error(f"Error saving embedding to cache: {e}")


# Global cache instances
redis_cache = RedisCache()
session_cache = SessionCache(redis_cache)
embedding_cache = EmbeddingCache(redis_cache)
