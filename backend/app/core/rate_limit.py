import time
import threading
from collections import defaultdict
from typing import Callable, Dict, List
from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self):
        self._records: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        if not getattr(settings, "AUTH_RATE_LIMIT_ENABLED", True):
            return True

        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Filter timestamps within current window
            valid_timestamps = [t for t in self._records[key] if t > cutoff]
            if len(valid_timestamps) >= max_requests:
                self._records[key] = valid_timestamps
                return False

            valid_timestamps.append(now)
            self._records[key] = valid_timestamps
            return True

    def reset(self):
        """Clears all records, useful for test suites."""
        with self._lock:
            self._records.clear()


limiter_instance = InMemoryRateLimiter()


def rate_limit(limit_getter: Callable[[], int], window_seconds: int = 60):
    """FastAPI dependency for rate limiting endpoints based on client IP."""
    def dependency(request: Request):
        if not getattr(settings, "AUTH_RATE_LIMIT_ENABLED", True):
            return

        client_ip = "127.0.0.1"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif request.client:
            client_ip = request.client.host

        route_path = request.url.path
        key = f"{client_ip}:{route_path}"
        max_requests = limit_getter()

        if not limiter_instance.is_allowed(key, max_requests=max_requests, window_seconds=window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak permintaan. Silakan coba lagi nanti.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
