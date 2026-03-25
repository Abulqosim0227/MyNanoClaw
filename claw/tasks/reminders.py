from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class Reminder:
    id: str
    text: str
    remind_at: str
    user_id: int
    fired: bool = False

    def to_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "remind_at": self.remind_at, "user_id": self.user_id, "fired": self.fired}

    @staticmethod
    def from_dict(d: dict) -> Reminder:
        return Reminder(id=d["id"], text=d["text"], remind_at=d["remind_at"], user_id=d["user_id"], fired=d.get("fired", False))


@dataclass
class ReminderManager:
    data_dir: Path
    on_fire: Optional[Callable[[Reminder], Awaitable[None]]] = None
    _reminders: dict[str, Reminder] = field(default_factory=dict, repr=False)
    _running: bool = False

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _path(self) -> Path:
        return self.data_dir / "reminders.json"

    def _load(self) -> None:
        path = self._path()
        if not path.exists():
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._reminders = {r["id"]: Reminder.from_dict(r) for r in raw}

    def _save(self) -> None:
        data = [r.to_dict() for r in self._reminders.values()]
        self._path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add(self, text: str, remind_at: str, user_id: int) -> Reminder:
        reminder = Reminder(
            id=uuid.uuid4().hex[:8],
            text=text,
            remind_at=remind_at,
            user_id=user_id,
        )
        self._reminders[reminder.id] = reminder
        self._save()
        return reminder

    def cancel(self, reminder_id: str) -> Optional[Reminder]:
        r = self._reminders.pop(reminder_id, None)
        if r:
            self._save()
        return r

    def list_pending(self, user_id: int) -> list[Reminder]:
        return [r for r in self._reminders.values() if r.user_id == user_id and not r.fired]

    async def check_and_fire(self) -> list[Reminder]:
        now = datetime.now(timezone.utc).isoformat()
        fired: list[Reminder] = []

        for r in list(self._reminders.values()):
            if r.fired:
                continue
            if r.remind_at <= now:
                r.fired = True
                fired.append(r)
                if self.on_fire:
                    try:
                        await self.on_fire(r)
                    except Exception as e:
                        logger.error("Reminder fire failed: %s", e)

        if fired:
            self._save()

        return fired

    async def start_loop(self, interval: int = 60) -> None:
        self._running = True
        while self._running:
            await self.check_and_fire()
            await asyncio.sleep(interval)

    def stop(self) -> None:
        self._running = False
