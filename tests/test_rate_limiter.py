import time
from unittest.mock import patch

from claw.security.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=3)
        assert limiter.is_allowed(1) is True
        assert limiter.is_allowed(1) is True
        assert limiter.is_allowed(1) is True

    def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=2)
        assert limiter.is_allowed(1) is True
        assert limiter.is_allowed(1) is True
        assert limiter.is_allowed(1) is False

    def test_separate_users(self):
        limiter = RateLimiter(max_requests=1)
        assert limiter.is_allowed(1) is True
        assert limiter.is_allowed(2) is True
        assert limiter.is_allowed(1) is False
        assert limiter.is_allowed(2) is False

    def test_window_expiry(self):
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.is_allowed(1) is True
        assert limiter.is_allowed(1) is False

        initial = time.monotonic()
        with patch("claw.security.rate_limiter.time") as mock_time:
            mock_time.monotonic.return_value = initial + 2
            assert limiter.is_allowed(1) is True

    def test_remaining(self):
        limiter = RateLimiter(max_requests=5)
        assert limiter.remaining(1) == 5
        limiter.is_allowed(1)
        limiter.is_allowed(1)
        assert limiter.remaining(1) == 3

    def test_reset(self):
        limiter = RateLimiter(max_requests=2)
        limiter.is_allowed(1)
        limiter.is_allowed(1)
        assert limiter.is_allowed(1) is False
        limiter.reset(1)
        assert limiter.is_allowed(1) is True
