from __future__ import annotations

import logging

from aiogram.types import Message

from claw.core.engine import ClaudeEngine

logger = logging.getLogger(__name__)

_engine: ClaudeEngine | None = None


def setup(engine: ClaudeEngine) -> None:
    global _engine
    _engine = engine


async def handle_translate(message: Message, text: str, target_lang: str) -> None:
    processing = await message.answer("Translating...")

    prompt = (
        f"Translate the following text to {target_lang}. "
        f"Return only the translation, no explanation.\n\n{text}"
    )

    result = await _engine.ask(prompt)
    await processing.edit_text(result.response)
