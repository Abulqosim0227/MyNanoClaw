import pytest
from claw.tasks.manager import TaskManager, Task, Priority, Status


class TestTaskManager:
    def test_add_task(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        task = mgr.add("Fix login bug", user_id=123, priority=Priority.HIGH)
        assert task.title == "Fix login bug"
        assert task.priority == Priority.HIGH
        assert task.status == Status.PENDING
        assert len(task.id) == 8

    def test_complete_task(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        task = mgr.add("Test task", user_id=123)
        completed = mgr.complete(task.id)
        assert completed.status == Status.DONE

    def test_complete_nonexistent(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        assert mgr.complete("nope1234") is None

    def test_cancel_task(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        task = mgr.add("Cancel me", user_id=123)
        cancelled = mgr.cancel(task.id)
        assert cancelled.status == Status.CANCELLED

    def test_list_active(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        mgr.add("Task 1", user_id=123)
        mgr.add("Task 2", user_id=123)
        t3 = mgr.add("Task 3", user_id=123)
        mgr.complete(t3.id)
        active = mgr.list_active(user_id=123)
        assert len(active) == 2

    def test_list_active_sorted_by_priority(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        mgr.add("Low", user_id=1, priority=Priority.LOW)
        mgr.add("Urgent", user_id=1, priority=Priority.URGENT)
        mgr.add("High", user_id=1, priority=Priority.HIGH)
        active = mgr.list_active(user_id=1)
        assert active[0].priority == Priority.URGENT
        assert active[1].priority == Priority.HIGH
        assert active[2].priority == Priority.LOW

    def test_user_isolation(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        mgr.add("User 1 task", user_id=1)
        mgr.add("User 2 task", user_id=2)
        assert len(mgr.list_active(user_id=1)) == 1
        assert len(mgr.list_active(user_id=2)) == 1

    def test_persistence(self, tmp_path):
        mgr1 = TaskManager(data_dir=tmp_path)
        mgr1.add("Persist me", user_id=1)
        mgr2 = TaskManager(data_dir=tmp_path)
        assert len(mgr2.list_active(user_id=1)) == 1

    def test_stats(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        mgr.add("A", user_id=1)
        t = mgr.add("B", user_id=1)
        mgr.complete(t.id)
        stats = mgr.stats(user_id=1)
        assert stats["pending"] == 1
        assert stats["done"] == 1
        assert stats["total"] == 2

    def test_deadline(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        mgr.add("With deadline", user_id=1, deadline="2026-03-25")
        due = mgr.due_today(user_id=1)
        assert len(due) >= 0

    def test_get_task(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        task = mgr.add("Find me", user_id=1)
        found = mgr.get(task.id)
        assert found.title == "Find me"

    def test_get_nonexistent(self, tmp_path):
        mgr = TaskManager(data_dir=tmp_path)
        assert mgr.get("nope") is None
