import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from claw.monitor.watcher import WatchManager, Watch, ChangeAlert
from claw.scraper.fetcher import FetchResult


class TestWatchManager:
    def test_add_watch(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        w = mgr.add("https://example.com", user_id=1, interval_hours=12)
        assert w.url == "https://example.com"
        assert w.interval_seconds == 12 * 3600
        assert w.active is True

    def test_remove_watch(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        w = mgr.add("https://a.com", user_id=1)
        removed = mgr.remove(w.id)
        assert removed is not None
        assert len(mgr.list_active(user_id=1)) == 0

    def test_remove_nonexistent(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        assert mgr.remove("nope") is None

    def test_list_active(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        mgr.add("https://a.com", user_id=1)
        mgr.add("https://b.com", user_id=1)
        mgr.add("https://c.com", user_id=2)
        assert len(mgr.list_active(user_id=1)) == 2
        assert len(mgr.list_active(user_id=2)) == 1

    def test_persistence(self, tmp_path):
        mgr1 = WatchManager(data_dir=tmp_path)
        mgr1.add("https://a.com", user_id=1)
        mgr2 = WatchManager(data_dir=tmp_path)
        assert len(mgr2.list_active(user_id=1)) == 1

    @pytest.mark.asyncio
    async def test_check_one_first_time(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        w = mgr.add("https://a.com", user_id=1)

        html = "<html><body><p>Content here with enough words for extraction.</p></body></html>"
        fetch_result = FetchResult(
            url="https://a.com", status_code=200, content=html,
            content_type="text/html", final_url="https://a.com",
            size_bytes=len(html), success=True, error="",
        )

        with patch("claw.monitor.watcher.fetch", new_callable=AsyncMock, return_value=fetch_result):
            alert = await mgr.check_one(w)
            assert alert is None
            assert w.last_hash != ""
            assert w.check_count == 1

    @pytest.mark.asyncio
    async def test_check_one_no_change(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        w = mgr.add("https://a.com", user_id=1)

        html = "<html><body><p>Same content stays the same.</p></body></html>"
        fetch_result = FetchResult(
            url="https://a.com", status_code=200, content=html,
            content_type="text/html", final_url="https://a.com",
            size_bytes=len(html), success=True, error="",
        )

        with patch("claw.monitor.watcher.fetch", new_callable=AsyncMock, return_value=fetch_result):
            await mgr.check_one(w)
            alert = await mgr.check_one(w)
            assert alert is None

    @pytest.mark.asyncio
    async def test_check_one_detects_change(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        w = mgr.add("https://a.com", user_id=1)

        html1 = "<html><body><p>Original content here for testing.</p></body></html>"
        html2 = "<html><body><p>Updated new content that is different.</p></body></html>"
        fr1 = FetchResult(url="https://a.com", status_code=200, content=html1,
                          content_type="text/html", final_url="https://a.com",
                          size_bytes=len(html1), success=True, error="")
        fr2 = FetchResult(url="https://a.com", status_code=200, content=html2,
                          content_type="text/html", final_url="https://a.com",
                          size_bytes=len(html2), success=True, error="")

        with patch("claw.monitor.watcher.fetch", new_callable=AsyncMock, return_value=fr1):
            await mgr.check_one(w)

        with patch("claw.monitor.watcher.fetch", new_callable=AsyncMock, return_value=fr2):
            alert = await mgr.check_one(w)

        if alert:
            assert isinstance(alert, ChangeAlert)
            assert w.change_count >= 1

    @pytest.mark.asyncio
    async def test_check_one_fetch_failure(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        w = mgr.add("https://a.com", user_id=1)

        with patch("claw.monitor.watcher.fetch", new_callable=AsyncMock, return_value=FetchResult.failure("https://a.com", "timeout")):
            alert = await mgr.check_one(w)
            assert alert is None
            assert w.check_count == 1

    def test_stop(self, tmp_path):
        mgr = WatchManager(data_dir=tmp_path)
        mgr.stop()
        assert mgr._running is False


class TestWatchIntents:
    def test_detects_watch_add(self):
        from claw.core.intent import classify, Intent
        result = classify("watch https://example.com")
        assert result.intent == Intent.WATCH_ADD
        assert result.params["url"] == "https://example.com"

    def test_watch_with_interval(self):
        from claw.core.intent import classify, Intent
        result = classify("watch https://example.com every 6h")
        assert result.intent == Intent.WATCH_ADD
        assert result.params["interval_hours"] == 6

    def test_monitor_keyword(self):
        from claw.core.intent import classify, Intent
        result = classify("monitor https://news.com/api")
        assert result.intent == Intent.WATCH_ADD

    def test_watch_list(self):
        from claw.core.intent import classify, Intent
        result = classify("my watches")
        assert result.intent == Intent.WATCH_LIST

    def test_stop_watching(self):
        from claw.core.intent import classify, Intent
        result = classify("stop watching id abc12345")
        assert result.intent == Intent.WATCH_REMOVE
