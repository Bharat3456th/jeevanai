import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request

_hits = defaultdict(deque)


def rate_limit(limit: int, window: int = 60):
    """In-memory sliding window limiter per client IP + path."""
    def dep(request: Request):
        key = (request.client.host if request.client else "unknown", request.url.path)
        now = time.time()
        q = _hits[key]
        while q and q[0] < now - window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")
        q.append(now)
    return dep
# ---- added for v1.1 (login/register rate limit) ----
import time as _time
import threading as _threading
from collections import defaultdict as _defaultdict, deque as _deque
from fastapi import HTTPException as _HTTPException


class RateLimiter:
    """Ek key (jaise IP) ko `window` seconds me sirf `limit` baar allow karta hai."""

    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._hits = _defaultdict(_deque)
        self._lock = _threading.Lock()

    def check(self, key: str):
        now = _time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                raise _HTTPException(status_code=429,
                                     detail="Too many attempts. Please wait a minute and try again.")
            q.append(now)


def client_ip(request) -> str:
    return request.client.host if request.client else "unknown"