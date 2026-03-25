from __future__ import annotations

import re

MAX_MESSAGE_LENGTH = 4000

_SHELL_INJECTION_PATTERN = re.compile(r"`|(\$(?:\(|{))")


def sanitize_message(text: str) -> str:
    if not text or not text.strip():
        return ""

    cleaned = text.strip()

    if len(cleaned) > MAX_MESSAGE_LENGTH:
        cleaned = cleaned[:MAX_MESSAGE_LENGTH]

    cleaned = cleaned.replace("\x00", "")

    return cleaned


def is_safe_for_shell(text: str) -> bool:
    return not bool(_SHELL_INJECTION_PATTERN.search(text))


def sanitize_for_shell(text: str) -> str:
    return text.replace("'", "'\\''")
