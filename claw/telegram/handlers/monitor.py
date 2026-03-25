from __future__ import annotations

import logging

from aiogram.types import Message

from claw.monitor.watcher import WatchManager

logger = logging.getLogger(__name__)

_watch_mgr: WatchManager | None = None


def setup(watch_mgr: WatchManager) -> None:
    global _watch_mgr
    _watch_mgr = watch_mgr


async def handle_watch_add(message: Message, user_id: int, url: str, interval_hours: int) -> None:
    watch = _watch_mgr.add(url=url, user_id=user_id, interval_hours=interval_hours)
    await message.answer(
        f"Watching: {url}\n"
        f"Check every {interval_hours}h\n"
        f"ID: {watch.id}\n"
        f"I'll alert you when content changes."
    )


async def handle_watch_list(message: Message, user_id: int) -> None:
    watches = _watch_mgr.list_active(user_id)
    if not watches:
        await message.answer("Not watching anything. Send 'watch https://...' to start.")
        return

    lines = [f"Watching {len(watches)} sites:\n"]
    for w in watches:
        interval_h = w.interval_seconds // 3600
        last = w.last_check[:16] if w.last_check else "never"
        lines.append(
            f"  [{w.id}] {w.url[:50]}\n"
            f"    Every {interval_h}h | Checked: {last} | Changes: {w.change_count}"
        )

    await message.answer("\n".join(lines))


async def handle_watch_remove(message: Message, target: str) -> None:
    removed = _watch_mgr.remove(target)
    if removed:
        await message.answer(f"Stopped watching: {removed.url}")
    else:
        await message.answer(f"Watch not found: {target}")
