import pytest
from unittest.mock import AsyncMock, MagicMock

from claw.core.intent import classify, Intent
from claw.telegram.handlers.terminal import TerminalManager, handle_shell


class TestTerminalIntents:
    def test_shell_command(self):
        result = classify("$ git status")
        assert result.intent == Intent.SHELL
        assert result.params["command"] == "git status"
        assert result.params["session"] == ""

    def test_shell_with_session(self):
        result = classify("myproject$ ls -la")
        assert result.intent == Intent.SHELL
        assert result.params["command"] == "ls -la"
        assert result.params["session"] == "myproject"

    def test_terminal_create(self):
        result = classify("terminal new myproject /home/user/project")
        assert result.intent == Intent.TERMINAL_CREATE
        assert result.params["name"] == "myproject"
        assert result.params["cwd"] == "/home/user/project"

    def test_terminal_list(self):
        result = classify("my terminals")
        assert result.intent == Intent.TERMINAL_LIST

    def test_normal_text_not_shell(self):
        result = classify("what is python")
        assert result.intent == Intent.CHAT


class TestTerminalManager:
    def test_create_session(self):
        mgr = TerminalManager()
        s = mgr.create("test", "/tmp")
        assert s.name == "test"
        assert s.cwd == "/tmp"

    def test_list_sessions(self):
        mgr = TerminalManager()
        mgr.create("a", "/tmp")
        mgr.create("b", "/home")
        assert len(mgr.list_all()) == 2

    def test_remove_session(self):
        mgr = TerminalManager()
        mgr.create("x", "/tmp")
        assert mgr.remove("x") is True
        assert mgr.get("x") is None

    def test_remove_nonexistent(self):
        mgr = TerminalManager()
        assert mgr.remove("nope") is False


class TestHandleShell:
    @pytest.mark.asyncio
    async def test_runs_simple_command(self):
        msg = MagicMock()
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        await handle_shell(msg, "echo hello_claw")
        response = processing.edit_text.call_args[0][0]
        assert "hello_claw" in response
        assert "[OK]" in response

    @pytest.mark.asyncio
    async def test_runs_failing_command(self):
        msg = MagicMock()
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        await handle_shell(msg, "false")
        response = processing.edit_text.call_args[0][0]
        assert "Exit" in response
