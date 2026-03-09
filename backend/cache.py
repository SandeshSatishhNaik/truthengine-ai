"""In-memory TTL cache for API responses.

Provides a simple thread-safe cache with per-key expiration.
Suitable for single-process deployments (PythonAnywhere).
"""

import time
import threading
from typing import Any

from loguru import logger


class TTLCache:
    """Thread-safe in-memory cache with per-key time-to-live expiration."""

    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Args:
            default_ttl: Default time-to-live in seconds.
            max_size: Maximum number of entries before eviction.
        """
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        """Return cached value or None if missing/expired."""
        from backend.metrics import metrics

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                metrics.cache_misses.inc()
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                metrics.cache_misses.inc()
                return None
            metrics.cache_hits.inc()
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value with optional custom TTL (seconds)."""
        ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            # Evict expired entries if at capacity
            if len(self._store) >= self._max_size:
                self._evict_expired()
            # If still at capacity, evict oldest
            if len(self._store) >= self._max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][1])
                del self._store[oldest_key]
            self._store[key] = (value, time.monotonic() + ttl)

    def invalidate(self, key: str) -> None:
        """Remove a specific key."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._store.clear()

    def _evict_expired(self) -> None:
        """Remove all expired entries (must hold lock)."""
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)


# Shared singleton caches
tools_cache = TTLCache(default_ttl=120, max_size=500)       # 2 min for tool listings
search_cache = TTLCache(default_ttl=300, max_size=200)      # 5 min for search results
embedding_cache = TTLCache(default_ttl=600, max_size=300)   # 10 min for embeddings
