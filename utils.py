"""Utility functions for the trading application"""

import threading
import time
from datetime import datetime


def run_in_thread(func, *args, **kwargs):
    """Run a function in a background thread"""
    thread = threading.Thread(target=func, args=args,
                              kwargs=kwargs, daemon=True)
    thread.start()
    return thread


def format_currency(value, with_prefix=True):
    """Format a value as currency with $ prefix"""
    if value is None:
        return "$0.00" if with_prefix else "0.00"

    prefix = "$" if with_prefix else ""
    return f"{prefix}{value:,.2f}"


def format_percent(value, with_sign=True):
    """Format a value as a percentage with sign"""
    if value is None:
        return "0.00%"

    sign = "+" if value > 0 and with_sign else ""
    return f"{sign}{value:.2f}%"


def format_datetime(dt=None, format_str="%Y-%m-%d %H:%M:%S"):
    """Format a datetime object to string"""
    if dt is None:
        dt = datetime.now()
    elif isinstance(dt, str):
        return dt  # Already a string

    return dt.strftime(format_str)


def get_current_timestamp(format_str="%H:%M:%S"):
    """Get current time as formatted string"""
    return time.strftime(format_str, time.localtime())


def throttle(seconds=0.5):
    """
    Decorator to throttle function calls by adding a delay
    Useful for functions that make API calls to prevent rate limiting
    """
    def decorator(func):
        last_called = [0.0]  # Use list for mutable state

        def throttled_function(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            remaining = seconds - elapsed

            if remaining > 0:
                time.sleep(remaining)

            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return throttled_function

    return decorator


def retry(max_attempts=3, delay=1.0, backoff=2, exceptions=(Exception,)):
    """
    Decorator to retry a function call on exception

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            attempts = 0

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise

                    print(
                        f"Retry: {func.__name__} attempt {attempts}/{max_attempts} failed: {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff

        return wrapper

    return decorator
