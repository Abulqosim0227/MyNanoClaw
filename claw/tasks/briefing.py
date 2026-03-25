from __future__ import annotations

from claw.rag.index import VectorIndex
from claw.scraper.storage import PageStorage
from claw.tasks.manager import TaskManager
from claw.tasks.reminders import ReminderManager


def generate_briefing(
    user_id: int,
    task_mgr: TaskManager,
    reminder_mgr: ReminderManager,
    storage: PageStorage,
    index: VectorIndex | None = None,
) -> str:
    lines: list[str] = ["Daily Briefing\n"]

    active = task_mgr.list_active(user_id)
    due = task_mgr.due_today(user_id)
    task_stats = task_mgr.stats(user_id)

    if due:
        lines.append(f"Due today: {len(due)} tasks")
        for t in due:
            lines.append(f"  [{t.priority.value.upper()}] {t.title}")
        lines.append("")

    if active:
        lines.append(f"Active tasks: {len(active)}")
        for t in active[:10]:
            marker = "!" if t.priority.value in ("urgent", "high") else "-"
            deadline = f" (due {t.deadline[:10]})" if t.deadline else ""
            lines.append(f"  {marker} {t.title}{deadline}")
        lines.append("")

    pending_reminders = reminder_mgr.list_pending(user_id)
    if pending_reminders:
        lines.append(f"Upcoming reminders: {len(pending_reminders)}")
        for r in pending_reminders[:5]:
            lines.append(f"  {r.remind_at[:16]} — {r.text}")
        lines.append("")

    kb_stats = storage.stats()
    if kb_stats["total_pages"] > 0:
        lines.append(f"Knowledge base: {kb_stats['total_pages']} pages, {kb_stats['total_words']:,} words")
        if index:
            lines.append(f"Search index: {index.total_vectors} chunks")
        lines.append("")

    if task_stats["done"] > 0:
        lines.append(f"Completed: {task_stats['done']} tasks total")

    if len(lines) <= 1:
        lines.append("Nothing pending. Clean slate.")

    return "\n".join(lines)
