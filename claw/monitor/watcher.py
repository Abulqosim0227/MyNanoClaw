from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Optional

from claw.scraper.fetcher import fetch
from claw.scraper.parser import parse_html

logger = logging.getLogger(__name__)


@dataclass
class Watch:
    id: str
    url: str
    interval_seconds: int
    user_id: int
    last_hash: str
    last_check: str
    created_at: str
    active: bool = True
    check_count: int = 0
    change_count: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "url": self.url, "interval_seconds": self.interval_seconds,
            "user_id": self.user_id, "last_hash": self.last_hash, "last_check": self.last_check,
            "created_at": self.created_at, "active": self.active,
            "check_count": self.check_count, "change_count": self.change_count,
        }

    @staticmethod
    def from_dict(d: dict) -> Watch:
        return Watch(**d)


@dataclass(frozen=True)
class ChangeAlert:
    watch: Watch
    old_hash: str
    new_hash: str
    summary: str


@dataclass
class WatchManager:
    data_dir: Path
    on_change: Optional[Callable[[ChangeAlert], Awaitable[None]]] = None
    _watches: dict[str, Watch] = field(default_factory=dict, repr=False)
    _running: bool = False

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _path(self) -> Path:
        return self.data_dir / "watches.json"

    def _load(self) -> None:
        path = self._path()
        if not path.exists():
            return
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._watches = {w["id"]: Watch.from_dict(w) for w in raw}

    def _save(self) -> None:
        data = [w.to_dict() for w in self._watches.values()]
        self._path().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add(self, url: str, user_id: int, interval_hours: int = 24) -> Watch:
        watch = Watch(
            id=uuid.uuid4().hex[:8],
            url=url,
            interval_seconds=interval_hours * 3600,
            user_id=user_id,
            last_hash="",
            last_check="",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._watches[watch.id] = watch
        self._save()
        return watch

    def remove(self, watch_id: str) -> Optional[Watch]:
        w = self._watches.pop(watch_id, None)
        if w:
            self._save()
        return w

    def list_active(self, user_id: int) -> list[Watch]:
        return [w for w in self._watches.values() if w.user_id == user_id and w.active]

    def list_all(self) -> list[Watch]:
        return list(self._watches.values())

    async def check_one(self, watch: Watch) -> Optional[ChangeAlert]:
        result = await fetch(watch.url)
        watch.check_count += 1
        watch.last_check = datetime.now(timezone.utc).isoformat()

        if not result.success:
            self._save()
            return None

        parsed = parse_html(result.content, base_url=result.final_url)
        content_hash = hashlib.sha256(parsed.text.encode()).hexdigest()[:32]

        if not watch.last_hash:
            watch.last_hash = content_hash
            self._save()
            return None

        if content_hash != watch.last_hash:
            old_hash = watch.last_hash
            watch.last_hash = content_hash
            watch.change_count += 1
            self._save()

            return ChangeAlert(
                watch=watch,
                old_hash=old_hash,
                new_hash=content_hash,
                summary=f"Content changed on {watch.url}",
            )

        self._save()
        return None

    async def check_all_due(self) -> list[ChangeAlert]:
        now = datetime.now(timezone.utc)
        alerts: list[ChangeAlert] = []

        for watch in list(self._watches.values()):
            if not watch.active:
                continue

            if watch.last_check:
                last = datetime.fromisoformat(watch.last_check)
                elapsed = (now - last).total_seconds()
                if elapsed < watch.interval_seconds:
                    continue

            alert = await self.check_one(watch)
            if alert:
                alerts.append(alert)
                if self.on_change:
                    try:
                        await self.on_change(alert)
                    except Exception as e:
                        logger.error("Watch alert failed: %s", e)

        return alerts

    async def start_loop(self, interval: int = 300) -> None:
        self._running = True
        while self._running:
            await self.check_all_due()
            await asyncio.sleep(interval)

    def stop(self) -> None:
        self._running = False
