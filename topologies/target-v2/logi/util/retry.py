"""Retry helper for flaky carrier APIs."""
import time
from functools import wraps


def retry(attempts: int = 3, delay_s: float = 0.0, exceptions=(Exception,)):
    """Call the wrapped function up to `attempts` times in total.

    Re-raises the last exception if every attempt fails.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            last = None
            for attempt in range(1, attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last = exc
                    if delay_s:
                        time.sleep(delay_s * attempt)
            raise last
        return wrapper
    return decorator
