import time
from collections import defaultdict, deque
from threading import Lock


class InMemoryRateLimiter:
    """Small in-memory limiter for single-instance deployments."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def is_allowed(self, key: str) -> tuple[bool, int]:
        now = time.monotonic()

        with self._lock:
            request_times = self._requests[key]

            while request_times and now - request_times[0] >= self.window_seconds:
                request_times.popleft()

            if len(request_times) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - request_times[0])))
                return False, retry_after

            request_times.append(now)
            return True, 0
