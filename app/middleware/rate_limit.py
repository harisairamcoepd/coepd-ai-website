import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimiter:
    """Simple in-memory IP rate limiter for chat/lead APIs."""

    def __init__(self, limit_per_minute: int = 90):
        self.limit_per_minute = limit_per_minute
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, request: Request, call_next):
        if request.url.path not in {"/chat", "/lead"}:
            return await call_next(request)

        key = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60
        bucket = self._buckets[key]

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self.limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry in a minute."},
            )

        bucket.append(now)
        return await call_next(request)
