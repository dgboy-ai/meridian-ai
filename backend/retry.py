import asyncio
import functools
import random
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

T = TypeVar("T")


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    jitter: bool = True,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    if retryable_exceptions is None:
        retryable_exceptions = (Exception,)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        raise
                    delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    if jitter:
                        delay *= random.uniform(0, 1)
                    await asyncio.sleep(delay)

        return wrapper

    return decorator
