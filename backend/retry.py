"""Retry decorator with exponential backoff for external API calls."""

import time
import functools
from typing import TypeVar, Callable, Any

from loguru import logger

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    """
    Decorator that retries a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including the first call).
        base_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay between retries (caps exponential growth).
        backoff_factor: Multiplier applied to delay after each retry.
        retryable_exceptions: Tuple of exception types that trigger a retry.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__qualname__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"{func.__qualname__} attempt {attempt}/{max_attempts} failed: {e} "
                        f"— retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
            raise last_exception  # type: ignore[misc]

        return sync_wrapper

    return decorator


def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    """Async version of retry decorator with exponential backoff."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            import asyncio

            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__qualname__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"{func.__qualname__} attempt {attempt}/{max_attempts} failed: {e} "
                        f"— retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
            raise last_exception  # type: ignore[misc]

        return async_wrapper

    return decorator
