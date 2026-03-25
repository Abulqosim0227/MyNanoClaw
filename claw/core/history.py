from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class Turn:
    role: str
    content: str
    timestamp: str

    @staticmethod
    def user(content: str) -> Turn:
        return Turn(
            role="user",
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def assistant(content: str) -> Turn:
        return Turn(
            role="assistant",
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def save_turns(path: Path, turns: Sequence[Turn]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [f"# Session: {path.stem}", f"<!-- turns: {len(turns)} -->", ""]

    for turn in turns:
        role_label = "You" if turn.role == "user" else "Claw"
        lines.append(f"### {role_label} [{turn.timestamp}]")
        lines.append("")
        lines.append(turn.content)
        lines.append("")
        lines.append("---")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def load_turns(path: Path) -> list[Turn]:
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    turns: list[Turn] = []
    current_role = ""
    current_timestamp = ""
    content_lines: list[str] = []

    for line in text.split("\n"):
        if line.startswith("### You ["):
            if current_role and content_lines:
                turns.append(Turn(role=current_role, content="\n".join(content_lines).strip(), timestamp=current_timestamp))
            current_role = "user"
            current_timestamp = line.split("[")[1].rstrip("]")
            content_lines = []
        elif line.startswith("### Claw ["):
            if current_role and content_lines:
                turns.append(Turn(role=current_role, content="\n".join(content_lines).strip(), timestamp=current_timestamp))
            current_role = "assistant"
            current_timestamp = line.split("[")[1].rstrip("]")
            content_lines = []
        elif line.strip() == "---":
            continue
        elif current_role:
            content_lines.append(line)

    if current_role and content_lines:
        turns.append(Turn(role=current_role, content="\n".join(content_lines).strip(), timestamp=current_timestamp))

    return turns


def turns_to_prompt(turns: Sequence[Turn], max_turns: int) -> str:
    recent = turns[-max_turns:] if len(turns) > max_turns else turns

    parts: list[str] = []
    for turn in recent:
        prefix = "Human" if turn.role == "user" else "Assistant"
        parts.append(f"{prefix}: {turn.content}")

    return "\n\n".join(parts)


def estimate_tokens(text: str) -> int:
    return len(text) // 4
