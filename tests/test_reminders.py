import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from claw.tasks.reminders import ReminderManager, Reminder


class TestReminderManager:
    def test_add_reminder(self, tmp_path):
        mgr = ReminderManager(data_dir=tmp_path)
        r = mgr.add("Deploy server", "2026-03-26T15:00:00", user_id=1)
        assert r.text == "Deploy server"
        assert r.fired is False

    def test_cancel_reminder(self, tmp_path):
        mgr = ReminderManager(data_dir=tmp_path)
        r = mgr.add("Cancel me", "2026-12-01T00:00:00", user_id=1)
        cancelled = mgr.cancel(r.id)
        assert cancelled is not None
        assert len(mgr.list_pending(user_id=1)) == 0

    def test_cancel_nonexistent(self, tmp_path):
        mgr = ReminderManager(data_dir=tmp_path)
        assert mgr.cancel("nope") is None

    def test_list_pending(self, tmp_path):
        mgr = ReminderManager(data_dir=tmp_path)
        mgr.add("R1", "2026-12-01T00:00:00", user_id=1)
        mgr.add("R2", "2026-12-02T00:00:00", user_id=1)
        mgr.add("R3", "2026-12-03T00:00:00", user_id=2)
        assert len(mgr.list_pending(user_id=1)) == 2
        assert len(mgr.list_pending(user_id=2)) == 1

    @pytest.mark.asyncio
    async def test_check_and_fire_past(self, tmp_path):
        callback = AsyncMock()
        mgr = ReminderManager(data_dir=tmp_path, on_fire=callback)
        mgr.add("Past reminder", "2020-01-01T00:00:00", user_id=1)

        fired = await mgr.check_and_fire()
        assert len(fired) == 1
        assert fired[0].text == "Past reminder"
        callback.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_check_and_fire_future(self, tmp_path):
        callback = AsyncMock()
        mgr = ReminderManager(data_dir=tmp_path, on_fire=callback)
        mgr.add("Future reminder", "2099-01-01T00:00:00", user_id=1)

        fired = await mgr.check_and_fire()
        assert len(fired) == 0
        callback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fired_not_refired(self, tmp_path):
        callback = AsyncMock()
        mgr = ReminderManager(data_dir=tmp_path, on_fire=callback)
        mgr.add("Once", "2020-01-01T00:00:00", user_id=1)

        await mgr.check_and_fire()
        await mgr.check_and_fire()
        assert callback.await_count == 1

    def test_persistence(self, tmp_path):
        mgr1 = ReminderManager(data_dir=tmp_path)
        mgr1.add("Persist", "2026-12-01T00:00:00", user_id=1)
        mgr2 = ReminderManager(data_dir=tmp_path)
        assert len(mgr2.list_pending(user_id=1)) == 1

    def test_stop(self, tmp_path):
        mgr = ReminderManager(data_dir=tmp_path)
        mgr.stop()
        assert mgr._running is False
