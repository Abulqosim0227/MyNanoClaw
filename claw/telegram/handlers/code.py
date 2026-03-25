from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

from aiogram.types import Message

logger = logging.getLogger(__name__)

EXEC_TIMEOUT = 30
MAX_OUTPUT = 3000


async def handle_run_code(message: Message, code: str, language: str = "python") -> None:
    if language != "python":
        await message.answer(f"Only Python execution supported. Got: {language}")
        return

    processing = await message.answer("Running...")

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(code)
        script_path = f.name

    try:
        process = await asyncio.create_subprocess_exec(
            "python3", script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=EXEC_TIMEOUT)

        output = stdout.decode("utf-8", errors="replace")
        errors = stderr.decode("utf-8", errors="replace")

        parts: list[str] = []
        if output.strip():
            parts.append(f"Output:\n{output[:MAX_OUTPUT]}")
        if errors.strip():
            parts.append(f"Errors:\n{errors[:MAX_OUTPUT]}")
        if not parts:
            parts.append("No output.")
        if process.returncode != 0:
            parts.append(f"Exit code: {process.returncode}")

        await processing.edit_text("\n\n".join(parts))

    except asyncio.TimeoutError:
        await processing.edit_text(f"Execution timed out ({EXEC_TIMEOUT}s limit).")
    except Exception as e:
        await processing.edit_text(f"Execution failed: {e}")
    finally:
        Path(script_path).unlink(missing_ok=True)
