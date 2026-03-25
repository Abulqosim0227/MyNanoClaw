import asyncio
import pytest

from claw.core.engine import ClaudeEngine, EngineResult
from claw.core.history import Turn


class TestEngineResult:
    def test_structure(self):
        result = EngineResult(
            response="test",
            prompt_tokens=10,
            response_tokens=5,
            model="sonnet",
            truncated=False,
        )
        assert result.response == "test"
        assert result.model == "sonnet"


class TestClaudeEngine:
    @pytest.mark.asyncio
    async def test_empty_message(self):
        engine = ClaudeEngine(model="sonnet")
        result = await engine.ask("")
        assert result.response == "Empty message."
        assert result.prompt_tokens == 0

    @pytest.mark.asyncio
    async def test_whitespace_message(self):
        engine = ClaudeEngine(model="sonnet")
        result = await engine.ask("   ")
        assert result.response == "Empty message."

    @pytest.mark.asyncio
    async def test_model_assignment(self):
        engine = ClaudeEngine(model="opus")
        assert engine.model == "opus"

    @pytest.mark.asyncio
    async def test_handles_missing_cli(self, monkeypatch):
        engine = ClaudeEngine(model="sonnet")

        async def fake_exec(*args, **kwargs):
            raise FileNotFoundError()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
        result = await engine.ask("test")
        assert "not installed" in result.response or "not found" in result.response.lower()
