from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from claw.core.history import Turn, load_turns, save_turns

_SAFE_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class SessionError(Exception):
    pass


def validate_session_name(name: str) -> str:
    name = name.strip().lower()
    if not _SAFE_NAME.match(name):
        raise SessionError(
            f"Invalid session name: '{name}'. Use only letters, numbers, hyphens, underscores (max 64 chars)."
        )
    return name


@dataclass
class SessionManager:
    base_dir: Path

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.base_dir / f"{name}.md"

    def exists(self, name: str) -> bool:
        return self._path(validate_session_name(name)).exists()

    def list_sessions(self) -> list[str]:
        return sorted(p.stem for p in self.base_dir.glob("*.md"))

    def load(self, name: str) -> list[Turn]:
        name = validate_session_name(name)
        return load_turns(self._path(name))

    def save(self, name: str, turns: list[Turn]) -> None:
        name = validate_session_name(name)
        save_turns(self._path(name), turns)

    def append(self, name: str, user_turn: Turn, assistant_turn: Turn) -> list[Turn]:
        name = validate_session_name(name)
        turns = self.load(name)
        turns.append(user_turn)
        turns.append(assistant_turn)
        self.save(name, turns)
        return turns

    def branch(self, source: str, target: str) -> None:
        source = validate_session_name(source)
        target = validate_session_name(target)

        if not self.exists(source):
            raise SessionError(f"Source session '{source}' does not exist")
        if self.exists(target):
            raise SessionError(f"Target session '{target}' already exists")

        shutil.copy2(self._path(source), self._path(target))

    def delete(self, name: str) -> None:
        name = validate_session_name(name)
        path = self._path(name)
        if path.exists():
            path.unlink()

    def stats(self, name: str) -> dict[str, int]:
        turns = self.load(name)
        total_chars = sum(len(t.content) for t in turns)
        return {
            "turns": len(turns),
            "user_messages": sum(1 for t in turns if t.role == "user"),
            "assistant_messages": sum(1 for t in turns if t.role == "assistant"),
            "total_chars": total_chars,
            "estimated_tokens": total_chars // 4,
        }
