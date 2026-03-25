from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field

from aiogram.types import Message

logger = logging.getLogger(__name__)

SSH_TIMEOUT = 60
MAX_OUTPUT = 3500


@dataclass(frozen=True)
class RemoteServer:
    name: str
    host: str
    port: int
    user: str
    password: str


def load_servers() -> dict[str, RemoteServer]:
    raw = os.getenv("REMOTE_SERVERS", "").strip()
    if not raw:
        return {}

    servers: dict[str, RemoteServer] = {}
    for entry in raw.split(","):
        parts = entry.strip().split(":")
        if len(parts) < 5:
            continue
        name = parts[0].strip()
        host = parts[1].strip()
        port = int(parts[2].strip())
        user = parts[3].strip()
        password = ":".join(parts[4:]).strip()
        servers[name] = RemoteServer(name=name, host=host, port=port, user=user, password=password)

    return servers


_servers: dict[str, RemoteServer] = {}


def setup() -> None:
    global _servers
    _servers = load_servers()
    if _servers:
        logger.info("Loaded %d remote servers: %s", len(_servers), ", ".join(_servers.keys()))


async def _ssh_exec(server: RemoteServer, command: str) -> tuple[str, int]:
    try:
        import asyncssh

        async with asyncssh.connect(
            server.host,
            port=server.port,
            username=server.user,
            password=server.password,
            known_hosts=None,
            connect_timeout=10,
        ) as conn:
            result = await asyncio.wait_for(conn.run(command), timeout=SSH_TIMEOUT)

            output = ""
            if result.stdout and result.stdout.strip():
                output += result.stdout
            if result.stderr and result.stderr.strip():
                if output:
                    output += "\n"
                output += result.stderr

            if not output.strip():
                output = "(no output)"

            return output[:MAX_OUTPUT], result.exit_status or 0

    except asyncio.TimeoutError:
        return f"Timed out after {SSH_TIMEOUT}s", 1
    except Exception as e:
        return f"SSH error: {type(e).__name__}: {e}", 1


async def handle_remote(message: Message, server_name: str, command: str) -> None:
    server = _servers.get(server_name)
    if not server:
        available = ", ".join(_servers.keys()) if _servers else "none"
        await message.answer(f"Server '{server_name}' not found.\nAvailable: {available}")
        return

    processing = await message.answer(f"[{server_name}] Running...")

    output, code = await _ssh_exec(server, command)

    status = "OK" if code == 0 else f"Exit {code}"
    response = f"[{server_name}] [{status}]\n{output}"

    if len(response) > 4096:
        chunks = [response[i:i + 4096] for i in range(0, len(response), 4096)]
        await processing.edit_text(chunks[0])
        for chunk in chunks[1:]:
            await message.answer(chunk)
    else:
        await processing.edit_text(response)

    logger.info("ssh server=%s command=%s exit=%d", server_name, command[:50], code)


async def handle_server_list(message: Message) -> None:
    if not _servers:
        await message.answer(
            "No remote servers configured.\n"
            "Add to .env:\nREMOTE_SERVERS=name:host:port:user:password"
        )
        return

    lines = [f"Remote servers ({len(_servers)}):\n"]
    for s in _servers.values():
        lines.append(f"  {s.name} -> {s.user}@{s.host}:{s.port}")
    lines.append("")
    lines.append('Run: "vps> ls -la"')
    lines.append('Or: "vps> claude -p \'your prompt\'"')

    await message.answer("\n".join(lines))
