import time
from typing import Any, Dict, Optional, Tuple
import asyncio


class SimpleTTLCache:
    """
    A small, memory-bounded TTL cache with simple LRU behaviour.
    - max_size: maximum number of entries to keep
    - ttl_seconds: time-to-live per entry
    Designed to be small and low-overhead.
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300) -> None:
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._data: Dict[str, Tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._data.get(key)
            if not entry:
                return None
            ts, value = entry
            if time.time() - ts > self.ttl:
                # expired
                self._data.pop(key, None)
                return None
            # update LRU position: remove and reinsert
            self._data.pop(key, None)
            self._data[key] = (ts, value)
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            if key in self._data:
                self._data.pop(key)
            elif len(self._data) >= self.max_size:
                # evict oldest (first inserted)
                oldest_key = next(iter(self._data))
                self._data.pop(oldest_key, None)
            self._data[key] = (time.time(), value)

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()

    async def stats(self) -> Dict[str, Any]:
        """
        Return lightweight statistics about the cache suitable for health endpoints.
        This method acquires the lock briefly to read the internal structure safely.
        """
        async with self._lock:
            # Count only non-expired entries
            now = time.time()
            valid_count = 0
            # We avoid creating a new dict to keep memory pressure low; just count.
            for ts, _ in self._data.values():
                if now - ts <= self.ttl:
                    valid_count += 1
            return {"max_size": self.max_size, "ttl_seconds": self.ttl, "entries": valid_count}
