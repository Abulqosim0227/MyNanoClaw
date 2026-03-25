from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet

from dotenv import load_dotenv


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    telegram_token: str
    allowed_chat_ids: FrozenSet[int]
    claude_model: str
    max_history_turns: int
    rate_limit_per_minute: int
    session_dir: Path

    @staticmethod
    def load(env_path: Path | None = None) -> Config:
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            raise ConfigError("TELEGRAM_BOT_TOKEN is required")

        raw_ids = os.getenv("ALLOWED_CHAT_IDS", "").strip()
        if not raw_ids:
            raise ConfigError("ALLOWED_CHAT_IDS is required")

        try:
            chat_ids = frozenset(int(x.strip()) for x in raw_ids.split(",") if x.strip())
        except ValueError as e:
            raise ConfigError(f"ALLOWED_CHAT_IDS must be comma-separated integers: {e}")

        if not chat_ids:
            raise ConfigError("ALLOWED_CHAT_IDS must contain at least one ID")

        model = os.getenv("CLAUDE_MODEL", "sonnet").strip()
        if model not in ("sonnet", "opus", "haiku"):
            raise ConfigError(f"CLAUDE_MODEL must be sonnet, opus, or haiku, got: {model}")

        max_turns = int(os.getenv("MAX_HISTORY_TURNS", "20"))
        rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "15"))
        session_dir = Path(os.getenv("SESSION_DIR", "sessions"))

        return Config(
            telegram_token=token,
            allowed_chat_ids=chat_ids,
            claude_model=model,
            max_history_turns=max_turns,
            rate_limit_per_minute=rate_limit,
            session_dir=session_dir,
        )

    def masked_token(self) -> str:
        if len(self.telegram_token) < 10:
            return "***"
        return self.telegram_token[:4] + "***" + self.telegram_token[-4:]
