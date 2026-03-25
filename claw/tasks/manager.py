from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    title: str
    priority: Priority
    status: Status
    created_at: str
    deadline: str
    notes: str
    user_id: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "notes": self.notes,
            "user_id": self.user_id,
        }

    @staticmethod
    def from_dict(d: dict) -> Task:
        return Task(
            id=d["id"],
            title=d["title"],
            priority=Priority(d["priority"]),
            status=Status(d["status"]),
            created_at=d["created_at"],
            deadline=d.get("deadline", ""),
            notes=d.get("notes", ""),
            user_id=d.get("user_id", 0),
        )


@dataclass
class TaskManager:
    data_dir: Path
    _tasks: dict[str, Task] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _path(self) -> Path:
        return self.data_dir / "tasks.json"

    def _load(self) -> None:
        path = self._path()
        if not path.exists():
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._tasks = {t["id"]: Task.from_dict(t) for t in raw}

    def _save(self) -> None:
        data = [t.to_dict() for t in self._tasks.values()]
        self._path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add(self, title: str, user_id: int, priority: Priority = Priority.MEDIUM, deadline: str = "", notes: str = "") -> Task:
        task = Task(
            id=uuid.uuid4().hex[:8],
            title=title,
            priority=priority,
            status=Status.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
            deadline=deadline,
            notes=notes,
            user_id=user_id,
        )
        self._tasks[task.id] = task
        self._save()
        return task

    def complete(self, task_id: str) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = Status.DONE
        self._save()
        return task

    def cancel(self, task_id: str) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = Status.CANCELLED
        self._save()
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_active(self, user_id: int) -> list[Task]:
        return sorted(
            [t for t in self._tasks.values() if t.user_id == user_id and t.status in (Status.PENDING, Status.IN_PROGRESS)],
            key=lambda t: ({"urgent": 0, "high": 1, "medium": 2, "low": 3}[t.priority.value], t.created_at),
        )

    def list_all(self, user_id: int) -> list[Task]:
        return sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)

    def stats(self, user_id: int) -> dict[str, int]:
        user_tasks = [t for t in self._tasks.values() if t.user_id == user_id]
        return {
            "total": len(user_tasks),
            "pending": sum(1 for t in user_tasks if t.status == Status.PENDING),
            "in_progress": sum(1 for t in user_tasks if t.status == Status.IN_PROGRESS),
            "done": sum(1 for t in user_tasks if t.status == Status.DONE),
            "cancelled": sum(1 for t in user_tasks if t.status == Status.CANCELLED),
        }

    def due_today(self, user_id: int) -> list[Task]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return [
            t for t in self.list_active(user_id)
            if t.deadline and t.deadline.startswith(today)
        ]
