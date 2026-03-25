from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RateLimiter:
    max_requests: int
    window_seconds: int = 60
    _timestamps: dict[int, list[float]] = field(default_factory=lambda: defaultdict(list))
    _lock: Lock = field(default_factory=Lock)

    def is_allowed(self, user_id: int) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            self._timestamps[user_id] = [
                ts for ts in self._timestamps[user_id] if ts > cutoff
            ]

            if len(self._timestamps[user_id]) >= self.max_requests:
                return False

            self._timestamps[user_id].append(now)
            return True

    def remaining(self, user_id: int) -> int:
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            self._timestamps[user_id] = [
                ts for ts in self._timestamps[user_id] if ts > cutoff
            ]
            return max(0, self.max_requests - len(self._timestamps[user_id]))

    def reset(self, user_id: int) -> None:
        with self._lock:
            self._timestamps.pop(user_id, None)
