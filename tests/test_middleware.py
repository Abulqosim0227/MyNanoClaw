import pytest
from unittest.mock import AsyncMock, MagicMock

from claw.telegram.middleware import AuthMiddleware, RateLimitMiddleware
from claw.security.rate_limiter import RateLimiter


def _make_message(user_id: int) -> MagicMock:
    msg = MagicMock()
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.answer = AsyncMock()
    return msg


class TestAuthMiddleware:
    @pytest.mark.asyncio
    async def test_allows_authorized(self):
        mw = AuthMiddleware(frozenset({123}))
        handler = AsyncMock(return_value="ok")
        msg = _make_message(123)

        result = await mw(handler, msg, {})
        handler.assert_awaited_once()
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_blocks_unauthorized(self):
        mw = AuthMiddleware(frozenset({123}))
        handler = AsyncMock()
        msg = _make_message(999)

        result = await mw(handler, msg, {})
        handler.assert_not_awaited()
        assert result is None

    @pytest.mark.asyncio
    async def test_blocks_no_user(self):
        mw = AuthMiddleware(frozenset({123}))
        handler = AsyncMock()
        msg = MagicMock()
        msg.from_user = None

        result = await mw(handler, msg, {})
        handler.assert_not_awaited()


class TestRateLimitMiddleware:
    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        limiter = RateLimiter(max_requests=5)
        mw = RateLimitMiddleware(limiter)
        handler = AsyncMock(return_value="ok")
        msg = _make_message(1)

        result = await mw(handler, msg, {})
        handler.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        limiter = RateLimiter(max_requests=1)
        mw = RateLimitMiddleware(limiter)
        handler = AsyncMock()

        msg1 = _make_message(1)
        await mw(handler, msg1, {})

        msg2 = _make_message(1)
        await mw(handler, msg2, {})
        msg2.answer.assert_awaited_once()
        assert handler.await_count == 1
