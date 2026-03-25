import pytest
from claw.config import Config, ConfigError


class TestConfigLoad:
    def test_loads_valid_config(self, valid_env):
        config = Config.load()
        assert config.claude_model == "sonnet"
        assert 123456 in config.allowed_chat_ids
        assert config.max_history_turns == 20
        assert config.rate_limit_per_minute == 15

    def test_missing_token_raises(self, monkeypatch, tmp_path):
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "123")
        fake_env = tmp_path / ".env"
        fake_env.write_text("")
        with pytest.raises(ConfigError, match="TELEGRAM_BOT_TOKEN"):
            Config.load(env_path=fake_env)

    def test_missing_chat_ids_raises(self, monkeypatch, tmp_path):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake:token")
        fake_env = tmp_path / ".env"
        fake_env.write_text("")
        with pytest.raises(ConfigError, match="ALLOWED_CHAT_IDS"):
            Config.load(env_path=fake_env)

    def test_invalid_chat_ids_raises(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake:token")
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "abc,def")
        with pytest.raises(ConfigError, match="integers"):
            Config.load()

    def test_invalid_model_raises(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake:token")
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "123")
        monkeypatch.setenv("CLAUDE_MODEL", "gpt4")
        with pytest.raises(ConfigError, match="sonnet, opus, or haiku"):
            Config.load()

    def test_multiple_chat_ids(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake:token")
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "111,222,333")
        config = Config.load()
        assert config.allowed_chat_ids == frozenset({111, 222, 333})

    def test_config_is_immutable(self, valid_env):
        config = Config.load()
        with pytest.raises(AttributeError):
            config.claude_model = "opus"


class TestMaskedToken:
    def test_masks_normal_token(self, valid_env):
        config = Config.load()
        masked = config.masked_token()
        assert "test_token_fake" not in masked
        assert masked.startswith("1234")
        assert masked.endswith("fake")
        assert "***" in masked

    def test_masks_short_token(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "short")
        monkeypatch.setenv("ALLOWED_CHAT_IDS", "123")
        config = Config.load()
        assert config.masked_token() == "***"
