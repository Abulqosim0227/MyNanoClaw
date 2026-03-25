from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Sequence

from claw.core.history import Turn, turns_to_prompt, estimate_tokens
from claw.security.sanitizer import sanitize_message, sanitize_for_shell

logger = logging.getLogger(__name__)

MAX_PROMPT_TOKENS = 30000
SUBPROCESS_TIMEOUT = 120


@dataclass
class EngineResult:
    response: str
    prompt_tokens: int
    response_tokens: int
    model: str
    truncated: bool


@dataclass
class ClaudeEngine:
    model: str = "sonnet"

    async def ask(
        self,
        message: str,
        history: Sequence[Turn] | None = None,
        max_history_turns: int = 20,
    ) -> EngineResult:
        message = sanitize_message(message)
        if not message:
            return EngineResult(
                response="Empty message.",
                prompt_tokens=0,
                response_tokens=0,
                model=self.model,
                truncated=False,
            )

        prompt_parts: list[str] = []
        truncated = False

        if history:
            context = turns_to_prompt(history, max_history_turns)
            context_tokens = estimate_tokens(context)

            if context_tokens > MAX_PROMPT_TOKENS:
                while context_tokens > MAX_PROMPT_TOKENS and max_history_turns > 2:
                    max_history_turns -= 2
                    context = turns_to_prompt(history, max_history_turns)
                    context_tokens = estimate_tokens(context)
                truncated = True

            prompt_parts.append(
                f"Previous conversation:\n{context}\n\nNow respond to the latest message."
            )

        prompt_parts.append(message)
        full_prompt = "\n\n".join(prompt_parts)
        prompt_tokens = estimate_tokens(full_prompt)

        safe_prompt = sanitize_for_shell(full_prompt)

        try:
            process = await asyncio.create_subprocess_exec(
                "claude",
                "-p", safe_prompt,
                "--model", self.model,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=SUBPROCESS_TIMEOUT,
            )

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                logger.error("Claude CLI error: %s", error_msg)
                return EngineResult(
                    response="Something went wrong. Try again.",
                    prompt_tokens=prompt_tokens,
                    response_tokens=0,
                    model=self.model,
                    truncated=truncated,
                )

            response = stdout.decode("utf-8", errors="replace").strip()
            response_tokens = estimate_tokens(response)

            return EngineResult(
                response=response,
                prompt_tokens=prompt_tokens,
                response_tokens=response_tokens,
                model=self.model,
                truncated=truncated,
            )

        except asyncio.TimeoutError:
            logger.error("Claude CLI timed out after %ds", SUBPROCESS_TIMEOUT)
            return EngineResult(
                response="Request timed out. Try a shorter message.",
                prompt_tokens=prompt_tokens,
                response_tokens=0,
                model=self.model,
                truncated=truncated,
            )
        except FileNotFoundError:
            logger.error("Claude CLI not found in PATH")
            return EngineResult(
                response="Claude CLI not installed or not in PATH.",
                prompt_tokens=0,
                response_tokens=0,
                model=self.model,
                truncated=False,
            )
