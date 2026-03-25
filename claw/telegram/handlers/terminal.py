from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from aiogram.types import Message

logger = logging.getLogger(__name__)

EXEC_TIMEOUT = 60
MAX_OUTPUT = 3500


@dataclass
class Session:
    name: str
    cwd: str

    def to_str(self) -> str:
        return f"{self.name} ({self.cwd})"


@dataclass
class TerminalManager:
    default_cwd: str = str(Path.home())
    _sessions: dict[str, Session] = field(default_factory=dict)

    def create(self, name: str, cwd: str) -> Session:
        session = Session(name=name, cwd=cwd)
        self._sessions[name] = session
        return session

    def get(self, name: str) -> Session | None:
        return self._sessions.get(name)

    def list_all(self) -> list[Session]:
        return list(self._sessions.values())

    def remove(self, name: str) -> bool:
        return self._sessions.pop(name, None) is not None


_manager = TerminalManager()


async def _run_command(command: str, cwd: str) -> tuple[str, int]:
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env={**os.environ, "TERM": "dumb"},
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=EXEC_TIMEOUT)

        output = stdout.decode("utf-8", errors="replace")
        errors = stderr.decode("utf-8", errors="replace")

        combined = ""
        if output.strip():
            combined += output
        if errors.strip():
            if combined:
                combined += "\n"
            combined += errors

        if not combined.strip():
            combined = "(no output)"

        return combined[:MAX_OUTPUT], process.returncode or 0

    except asyncio.TimeoutError:
        return f"Timed out after {EXEC_TIMEOUT}s", 1
    except Exception as e:
        return f"Failed: {e}", 1


async def handle_shell(message: Message, command: str, session_name: str = "") -> None:
    session = _manager.get(session_name) if session_name else None
    cwd = session.cwd if session else _manager.default_cwd

    processing = await message.answer(f"Running in {cwd}...")

    output, code = await _run_command(command, cwd)

    status = "OK" if code == 0 else f"Exit {code}"
    response = f"[{status}]\n{output}"

    if len(response) > 4096:
        chunks = [response[i:i + 4096] for i in range(0, len(response), 4096)]
        await processing.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.answer(chunk)
    else:
        await processing.edit_text(response)


async def handle_session_create(message: Message, name: str, cwd: str) -> None:
    if not Path(cwd).is_dir():
        await message.answer(f"Directory not found: {cwd}")
        return

    session = _manager.create(name, cwd)
    await message.answer(f"Terminal session created: {session.to_str()}")


async def handle_session_list(message: Message) -> None:
    sessions = _manager.list_all()
    if not sessions:
        lines = [
            "No terminal sessions.",
            "",
            "Create one:",
            '  "terminal new myproject /path/to/project"',
            "",
            "Or run commands directly:",
            '  "$ git status"',
            '  "$ ls -la"',
        ]
    else:
        lines = [f"Terminal sessions ({len(sessions)}):\n"]
        for s in sessions:
            lines.append(f"  {s.name} -> {s.cwd}")
        lines.append("")
        lines.append('Run: "myproject$ git status"')

    await message.answer("\n".join(lines))
