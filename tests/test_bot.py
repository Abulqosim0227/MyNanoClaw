from pathlib import Path

from claw.config import Config
from claw.telegram.bot import create_bot


class TestCreateBot:
    def test_creates_bot_and_dispatcher(self, tmp_path):
        config = Config(
            telegram_token="1234567890:ABCDEFtest",
            allowed_chat_ids=frozenset({123}),
            claude_model="sonnet",
            max_history_turns=20,
            rate_limit_per_minute=15,
            session_dir=tmp_path / "sessions",
        )
        bot, dp = create_bot(config)
        assert bot is not None
        assert dp is not None
        assert bot.token == "1234567890:ABCDEFtest"
