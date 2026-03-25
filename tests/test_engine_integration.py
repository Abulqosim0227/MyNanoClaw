import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from claw.core.engine import ClaudeEngine, EngineResult, MAX_PROMPT_TOKENS
from claw.core.history import Turn


class TestEngineWithHistory:
    @pytest.mark.asyncio
    async def test_truncates_large_history(self):
        engine = ClaudeEngine(model="sonnet")
        large_turns = [
            Turn.user("x" * 10000) for _ in range(20)
        ]

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"response", b""))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            with patch("asyncio.wait_for", new_callable=AsyncMock, return_value=(b"response", b"")):
                mock_process.communicate = AsyncMock(return_value=(b"response", b""))
                result = await engine.ask("test", history=large_turns, max_history_turns=20)
                assert result.truncated is True

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        engine = ClaudeEngine(model="sonnet")

        async def fake_exec(*args, **kwargs):
            mock = MagicMock()
            mock.communicate = AsyncMock()
            return mock

        with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
            with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
                result = await engine.ask("test")
                assert "timed out" in result.response.lower()

    @pytest.mark.asyncio
    async def test_cli_error_handling(self):
        engine = ClaudeEngine(model="sonnet")

        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"some error"))

        with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_process):
            with patch("asyncio.wait_for", new_callable=AsyncMock, return_value=(b"", b"some error")):
                mock_process.communicate = AsyncMock(return_value=(b"", b"some error"))
                result = await engine.ask("test")
                assert "wrong" in result.response.lower() or result.response_tokens == 0
