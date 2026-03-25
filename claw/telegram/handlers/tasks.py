from __future__ import annotations

import logging

from aiogram.types import Message

from claw.rag.index import VectorIndex
from claw.scraper.storage import PageStorage
from claw.tasks.briefing import generate_briefing
from claw.tasks.manager import TaskManager, Priority
from claw.tasks.reminders import ReminderManager

logger = logging.getLogger(__name__)

_task_mgr: TaskManager | None = None
_reminder_mgr: ReminderManager | None = None
_storage: PageStorage | None = None
_index: VectorIndex | None = None


def setup(
    task_mgr: TaskManager,
    reminder_mgr: ReminderManager,
    storage: PageStorage,
    index: VectorIndex | None = None,
) -> None:
    global _task_mgr, _reminder_mgr, _storage, _index
    _task_mgr = task_mgr
    _reminder_mgr = reminder_mgr
    _storage = storage
    _index = index


async def handle_task_add(message: Message, user_id: int, title: str, priority: str, deadline: str) -> None:
    if not title:
        await message.answer("What's the task? Example: add task fix login bug high priority")
        return

    p = Priority(priority) if priority in [e.value for e in Priority] else Priority.MEDIUM
    task = _task_mgr.add(title=title, user_id=user_id, priority=p, deadline=deadline)

    lines = [f"Task added: {task.title}", f"ID: {task.id} | Priority: {task.priority.value}"]
    if deadline:
        lines.append(f"Due: {deadline}")

    await message.answer("\n".join(lines))


async def handle_task_list(message: Message, user_id: int) -> None:
    tasks = _task_mgr.list_active(user_id)
    if not tasks:
        await message.answer("No active tasks.")
        return

    lines = [f"Active tasks ({len(tasks)}):\n"]
    for t in tasks:
        marker = {"urgent": "!!", "high": "!", "medium": "-", "low": "."}[t.priority.value]
        deadline = f" (due {t.deadline[:10]})" if t.deadline else ""
        lines.append(f"  {marker} [{t.id}] {t.title}{deadline}")

    await message.answer("\n".join(lines))


async def handle_task_done(message: Message, task_id: str) -> None:
    task = _task_mgr.complete(task_id)
    if task:
        await message.answer(f"Completed: {task.title}")
    else:
        await message.answer(f"Task not found: {task_id}")


async def handle_reminder_add(message: Message, user_id: int, text: str, remind_at: str) -> None:
    if not remind_at:
        await message.answer("When? Example: remind me to deploy at 2026-03-26 15:00")
        return
    if not text:
        text = "Reminder"

    reminder = _reminder_mgr.add(text=text, remind_at=remind_at, user_id=user_id)
    await message.answer(f"Reminder set: {reminder.text}\nAt: {reminder.remind_at}\nID: {reminder.id}")


async def handle_reminder_list(message: Message, user_id: int) -> None:
    reminders = _reminder_mgr.list_pending(user_id)
    if not reminders:
        await message.answer("No pending reminders.")
        return

    lines = [f"Pending reminders ({len(reminders)}):\n"]
    for r in reminders:
        lines.append(f"  {r.remind_at[:16]} — {r.text} [{r.id}]")

    await message.answer("\n".join(lines))


async def handle_briefing(message: Message, user_id: int) -> None:
    text = generate_briefing(
        user_id=user_id,
        task_mgr=_task_mgr,
        reminder_mgr=_reminder_mgr,
        storage=_storage,
        index=_index,
    )
    await message.answer(text)
