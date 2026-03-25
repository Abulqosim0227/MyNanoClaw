import pytest
from claw.tasks.briefing import generate_briefing
from claw.tasks.manager import TaskManager, Priority
from claw.tasks.reminders import ReminderManager
from claw.scraper.storage import PageStorage


class TestGenerateBriefing:
    def test_empty_briefing(self, tmp_path):
        task_mgr = TaskManager(data_dir=tmp_path / "tasks")
        reminder_mgr = ReminderManager(data_dir=tmp_path / "reminders")
        storage = PageStorage(base_dir=tmp_path / "knowledge")

        text = generate_briefing(user_id=1, task_mgr=task_mgr, reminder_mgr=reminder_mgr, storage=storage)
        assert "clean slate" in text.lower() or "nothing" in text.lower()

    def test_with_tasks(self, tmp_path):
        task_mgr = TaskManager(data_dir=tmp_path / "tasks")
        reminder_mgr = ReminderManager(data_dir=tmp_path / "reminders")
        storage = PageStorage(base_dir=tmp_path / "knowledge")

        task_mgr.add("Fix bug", user_id=1, priority=Priority.HIGH)
        task_mgr.add("Write docs", user_id=1, priority=Priority.LOW)

        text = generate_briefing(user_id=1, task_mgr=task_mgr, reminder_mgr=reminder_mgr, storage=storage)
        assert "Fix bug" in text
        assert "Write docs" in text
        assert "Active tasks: 2" in text

    def test_with_reminders(self, tmp_path):
        task_mgr = TaskManager(data_dir=tmp_path / "tasks")
        reminder_mgr = ReminderManager(data_dir=tmp_path / "reminders")
        storage = PageStorage(base_dir=tmp_path / "knowledge")

        reminder_mgr.add("Deploy", "2026-12-01T15:00:00", user_id=1)

        text = generate_briefing(user_id=1, task_mgr=task_mgr, reminder_mgr=reminder_mgr, storage=storage)
        assert "Deploy" in text
        assert "reminders" in text.lower()

    def test_with_knowledge(self, tmp_path):
        task_mgr = TaskManager(data_dir=tmp_path / "tasks")
        reminder_mgr = ReminderManager(data_dir=tmp_path / "reminders")
        storage = PageStorage(base_dir=tmp_path / "knowledge")

        storage.save("https://a.com", "Page", "content words here", 3, "")

        text = generate_briefing(user_id=1, task_mgr=task_mgr, reminder_mgr=reminder_mgr, storage=storage)
        assert "1 pages" in text or "Knowledge" in text
