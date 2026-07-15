import asyncio
import functools
import time
from collections import OrderedDict
from typing import Any, Callable, Optional, TypeVar

T = TypeVar("T")


class CacheManager:
    """A TTL-based in-memory async cache with LRU eviction."""

    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    async def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._cache.move_to_end(key)
                self._stats["hits"] += 1
                return value
            else:
                del self._cache[key]
        self._stats["misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: float = 300) -> None:
        if key in self._cache:
            del self._cache[key]
        elif len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1
        self._cache[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def clear(self) -> None:
        self._cache.clear()

    async def stats(self) -> dict:
        return self._stats.copy()


_cache_manager = CacheManager()


def cached(ttl: float = 300) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_value = await _cache_manager.get(key)
            if cached_value is not None:
                return cached_value
            result = await func(*args, **kwargs)
            await _cache_manager.set(key, result, ttl)
            return result

        return wrapper

    return decorator
