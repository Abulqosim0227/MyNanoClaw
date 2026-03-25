import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os

from claw.core.intent import classify, Intent
from claw.telegram.handlers.remote import load_servers, RemoteServer


class TestRemoteIntents:
    def test_remote_command(self):
        result = classify("vps> ls -la")
        assert result.intent == Intent.REMOTE
        assert result.params["server"] == "vps"
        assert result.params["command"] == "ls -la"

    def test_remote_claude(self):
        result = classify("vps> claude -p 'check status'")
        assert result.intent == Intent.REMOTE
        assert result.params["server"] == "vps"

    def test_server_list(self):
        result = classify("my servers")
        assert result.intent == Intent.SERVER_LIST

    def test_show_servers(self):
        result = classify("list servers")
        assert result.intent == Intent.SERVER_LIST

    def test_normal_text_not_remote(self):
        result = classify("what is python")
        assert result.intent == Intent.CHAT


class TestLoadServers:
    def test_loads_from_env(self, monkeypatch):
        monkeypatch.setenv("REMOTE_SERVERS", "test:1.2.3.4:22:root:pass123")
        servers = load_servers()
        assert "test" in servers
        assert servers["test"].host == "1.2.3.4"
        assert servers["test"].port == 22
        assert servers["test"].user == "root"
        assert servers["test"].password == "pass123"

    def test_multiple_servers(self, monkeypatch):
        monkeypatch.setenv("REMOTE_SERVERS", "a:1.1.1.1:22:root:p1,b:2.2.2.2:22:admin:p2")
        servers = load_servers()
        assert len(servers) == 2

    def test_empty_env(self, monkeypatch):
        monkeypatch.setenv("REMOTE_SERVERS", "")
        servers = load_servers()
        assert servers == {}

    def test_password_with_colons(self, monkeypatch):
        monkeypatch.setenv("REMOTE_SERVERS", "srv:1.1.1.1:22:root:pass:with:colons")
        servers = load_servers()
        assert servers["srv"].password == "pass:with:colons"

    def test_server_immutable(self, monkeypatch):
        monkeypatch.setenv("REMOTE_SERVERS", "x:1.1.1.1:22:root:pass")
        servers = load_servers()
        with pytest.raises(AttributeError):
            servers["x"].host = "changed"
