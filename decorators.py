# Custom decorators used across the app.
import functools
from datetime import datetime


def log_action(func):
    """logs every call to a function with timestamp"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # write to log file using context manager (with statement)
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat(timespec='seconds')}] {func.__name__}\n"
            )
        return func(*args, **kwargs)

    return wrapper
