import os
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("ALLOWED_CHAT_IDS", raising=False)
    monkeypatch.delenv("CLAUDE_MODEL", raising=False)
    monkeypatch.delenv("MAX_HISTORY_TURNS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_PER_MINUTE", raising=False)
    monkeypatch.delenv("SESSION_DIR", raising=False)
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def tmp_session_dir(tmp_path):
    d = tmp_path / "sessions"
    d.mkdir()
    return d


@pytest.fixture
def valid_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1234567890:ABCDEFtest_token_fake")
    monkeypatch.setenv("ALLOWED_CHAT_IDS", "123456")
    monkeypatch.setenv("CLAUDE_MODEL", "sonnet")
    monkeypatch.setenv("MAX_HISTORY_TURNS", "20")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "15")
    monkeypatch.setenv("SESSION_DIR", "sessions")
