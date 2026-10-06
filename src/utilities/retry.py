from typing import Any, Callable

from tenacity import retry, stop_after_attempt, wait_exponential

from .logger import logger

def log_retry_attempt(retry_state: Any) -> None:
    """Logs information about the retry attempt."""
    logger.warning(
        "Retrying execution",
        attempt_number=retry_state.attempt_number,
        wait_time=retry_state.idle_for,
        exception=str(retry_state.outcome.exception()),
    )

def with_retry(
    max_attempts: int = 3,
    min_wait_seconds: int = 1,
    max_wait_seconds: int = 10,
) -> Callable[[Any], Any]:
    """Decorator to automatically retry a function upon failure.

    Uses exponential backoff for wait times between attempts.

    Args:
        max_attempts: The maximum number of times to try the function.
        min_wait_seconds: The minimum time to wait before the first retry.
        max_wait_seconds: The maximum time to wait between retries.

    Returns:
        A decorated function with retry logic.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=min_wait_seconds, max=max_wait_seconds),
        before_sleep=log_retry_attempt,
        reraise=True,
    )
