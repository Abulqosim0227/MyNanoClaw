import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from claw.config import Config
from claw.core.engine import ClaudeEngine, EngineResult
from claw.core.session import SessionManager
from claw.telegram.handlers import chat


@pytest.fixture
def setup_handler(tmp_path):
    config = Config(
        telegram_token="fake:token",
        allowed_chat_ids=frozenset({123}),
        claude_model="sonnet",
        max_history_turns=20,
        rate_limit_per_minute=15,
        session_dir=tmp_path / "sessions",
    )
    engine = ClaudeEngine(model="sonnet")
    sessions = SessionManager(base_dir=tmp_path / "sessions")
    chat.setup(config, engine, sessions)
    return config, engine, sessions


def _make_message(user_id: int, text: str) -> MagicMock:
    msg = MagicMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.answer = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    return msg


class TestChatIntent:
    @pytest.mark.asyncio
    async def test_ignores_empty_text(self, setup_handler):
        msg = _make_message(123, "")
        await chat.handle_message(msg)
        msg.answer.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ignores_no_user(self, setup_handler):
        msg = MagicMock()
        msg.text = "hello"
        msg.from_user = None
        await chat.handle_message(msg)

    @pytest.mark.asyncio
    async def test_processes_chat_message(self, setup_handler):
        _, engine, _ = setup_handler
        fake_result = EngineResult(
            response="test reply", prompt_tokens=10, response_tokens=5,
            model="sonnet", truncated=False,
        )
        with patch.object(engine, "ask", new_callable=AsyncMock, return_value=fake_result):
            msg = _make_message(123, "hello")
            processing_msg = MagicMock(edit_text=AsyncMock())
            msg.answer = AsyncMock(return_value=processing_msg)
            await chat.handle_message(msg)
            msg.answer.assert_awaited_once_with("Thinking...")
            processing_msg.edit_text.assert_awaited()

    @pytest.mark.asyncio
    async def test_saves_to_session(self, setup_handler):
        _, engine, sessions = setup_handler
        fake_result = EngineResult(
            response="saved reply", prompt_tokens=10, response_tokens=5,
            model="sonnet", truncated=False,
        )
        with patch.object(engine, "ask", new_callable=AsyncMock, return_value=fake_result):
            msg = _make_message(123, "test message")
            processing_msg = MagicMock(edit_text=AsyncMock())
            msg.answer = AsyncMock(return_value=processing_msg)
            await chat.handle_message(msg)
            turns = sessions.load("user-123")
            assert len(turns) == 2
            assert turns[0].content == "test message"
            assert turns[1].content == "saved reply"


class TestModelSwitchIntent:
    @pytest.mark.asyncio
    async def test_switches_model(self, setup_handler):
        _, engine, _ = setup_handler
        assert engine.model == "sonnet"
        msg = _make_message(123, "switch to opus")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        assert engine.model == "opus"
        msg.answer.assert_awaited_once()
        assert "opus" in msg.answer.call_args[0][0].lower()


class TestSessionListIntent:
    @pytest.mark.asyncio
    async def test_lists_empty(self, setup_handler):
        msg = _make_message(123, "show sessions")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        msg.answer.assert_awaited_once()
        assert "no sessions" in msg.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_lists_existing(self, setup_handler):
        _, engine, sessions = setup_handler
        from claw.core.history import Turn
        sessions.save("test-session", [Turn.user("hi"), Turn.assistant("hello")])
        msg = _make_message(123, "show sessions")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        assert "test-session" in msg.answer.call_args[0][0]


class TestSessionClearIntent:
    @pytest.mark.asyncio
    async def test_clears_session(self, setup_handler):
        _, _, sessions = setup_handler
        from claw.core.history import Turn
        sessions.save("user-123", [Turn.user("old")])
        msg = _make_message(123, "clear history")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        assert not sessions.exists("user-123")
        assert "cleared" in msg.answer.call_args[0][0].lower()


class TestSessionBranchIntent:
    @pytest.mark.asyncio
    async def test_branches_session(self, setup_handler):
        _, _, sessions = setup_handler
        from claw.core.history import Turn
        sessions.save("user-123", [Turn.user("data")])
        msg = _make_message(123, "branch this as research")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        assert sessions.exists("research")
        assert "branched" in msg.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_branch_no_source(self, setup_handler):
        msg = _make_message(123, "branch this as test")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        assert "does not exist" in msg.answer.call_args[0][0].lower()


class TestSessionStatsIntent:
    @pytest.mark.asyncio
    async def test_shows_stats(self, setup_handler):
        _, _, sessions = setup_handler
        from claw.core.history import Turn
        sessions.save("user-123", [Turn.user("hello"), Turn.assistant("hi")])
        msg = _make_message(123, "stats")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        response = msg.answer.call_args[0][0]
        assert "Turns: 2" in response
        assert "sonnet" in response.lower()

    @pytest.mark.asyncio
    async def test_stats_no_session(self, setup_handler):
        msg = _make_message(123, "stats")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        assert "no session" in msg.answer.call_args[0][0].lower()


class TestHelpIntent:
    @pytest.mark.asyncio
    async def test_shows_help(self, setup_handler):
        msg = _make_message(123, "help")
        msg.answer = AsyncMock()
        await chat.handle_message(msg)
        response = msg.answer.call_args[0][0]
        assert "need" in response.lower() or "knowledge" in response.lower()
