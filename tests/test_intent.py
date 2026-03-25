import pytest

from claw.core.intent import Intent, ClassifiedIntent, classify


class TestModelSwitch:
    @pytest.mark.parametrize("text,expected_model", [
        ("switch to opus", "opus"),
        ("use haiku", "haiku"),
        ("change to sonnet", "sonnet"),
        ("Switch to Opus", "opus"),
        ("USE HAIKU", "haiku"),
        ("set model to opus", "opus"),
        ("change model to haiku", "haiku"),
    ])
    def test_detects_model_switch(self, text, expected_model):
        result = classify(text)
        assert result.intent == Intent.MODEL_SWITCH
        assert result.params["model"] == expected_model

    def test_ignores_model_in_conversation(self):
        result = classify("tell me about the opus model architecture")
        assert result.intent == Intent.CHAT


class TestSessionList:
    @pytest.mark.parametrize("text", [
        "show sessions",
        "list sessions",
        "my sessions",
        "show my sessions",
        "what sessions do I have",
    ])
    def test_detects_session_list(self, text):
        result = classify(text)
        assert result.intent == Intent.SESSION_LIST


class TestSessionBranch:
    @pytest.mark.parametrize("text,expected_target", [
        ("branch this as research", "research"),
        ("fork as backup", "backup"),
        ("copy to my-notes", "my-notes"),
        ("save this as important", "important"),
        ("branch as test_123", "test_123"),
    ])
    def test_detects_branch(self, text, expected_target):
        result = classify(text)
        assert result.intent == Intent.SESSION_BRANCH
        assert result.params["target"] == expected_target


class TestSessionClear:
    @pytest.mark.parametrize("text", [
        "clear history",
        "reset session",
        "start over",
        "start fresh",
        "new session",
        "new chat",
        "wipe conversation",
    ])
    def test_detects_clear(self, text):
        result = classify(text)
        assert result.intent == Intent.SESSION_CLEAR


class TestSessionStats:
    @pytest.mark.parametrize("text", [
        "stats",
        "statistics",
        "show stats",
        "how many messages",
        "how much tokens",
        "usage",
    ])
    def test_detects_stats(self, text):
        result = classify(text)
        assert result.intent == Intent.SESSION_STATS


class TestHelp:
    @pytest.mark.parametrize("text", [
        "help",
        "what can you do",
        "commands",
    ])
    def test_detects_help(self, text):
        result = classify(text)
        assert result.intent == Intent.HELP


class TestScrape:
    @pytest.mark.parametrize("text", [
        "save this https://example.com/article",
        "scrape https://example.com",
        "grab https://docs.python.org",
        "fetch this page https://blog.com/post",
        "get https://news.com/article",
        "read https://wiki.com/page",
    ])
    def test_detects_scrape(self, text):
        result = classify(text)
        assert result.intent == Intent.SCRAPE
        assert "url" in result.params

    def test_bare_url_defaults_to_scrape(self):
        result = classify("https://example.com/some-page")
        assert result.intent == Intent.SCRAPE
        assert result.params["url"] == "https://example.com/some-page"

    def test_extracts_url_correctly(self):
        result = classify("save this https://docs.python.org/3/tutorial/")
        assert result.params["url"] == "https://docs.python.org/3/tutorial/"


class TestCrawl:
    @pytest.mark.parametrize("text", [
        "crawl https://example.com",
        "grab everything from https://example.com",
        "scrape everything from https://docs.python.org",
        "deep crawl https://wiki.com",
        "full scrape https://site.com",
    ])
    def test_detects_crawl(self, text):
        result = classify(text)
        assert result.intent == Intent.CRAWL
        assert "url" in result.params
        assert "depth" in result.params

    def test_extracts_depth(self):
        result = classify("crawl https://example.com go 3 levels deep")
        assert result.intent == Intent.CRAWL
        assert result.params["depth"] == 3

    def test_default_depth_is_2(self):
        result = classify("crawl https://example.com")
        assert result.params["depth"] == 2

    def test_caps_depth_at_5(self):
        result = classify("crawl https://example.com depth 99")
        assert result.params["depth"] == 5


class TestKnowledge:
    @pytest.mark.parametrize("text", [
        "my sources",
        "show sources",
        "what sites have I saved",
        "list my knowledge",
        "what do I know",
    ])
    def test_detects_sources(self, text):
        result = classify(text)
        assert result.intent == Intent.KNOWLEDGE_SOURCES

    @pytest.mark.parametrize("text", [
        "how much do I know",
        "knowledge stats",
        "brain size",
    ])
    def test_detects_knowledge_stats(self, text):
        result = classify(text)
        assert result.intent == Intent.KNOWLEDGE_STATS

    def test_detects_delete(self):
        result = classify("delete https://old.com/page")
        assert result.intent == Intent.KNOWLEDGE_DELETE
        assert result.params["url"] == "https://old.com/page"

    def test_forget_as_delete(self):
        result = classify("forget https://old.com")
        assert result.intent == Intent.KNOWLEDGE_DELETE


class TestTaskIntents:
    @pytest.mark.parametrize("text", [
        "add task fix the login bug",
        "create task deploy new version",
        "new task review PR",
        "task: write unit tests",
        "todo: update docs",
    ])
    def test_detects_task_add(self, text):
        result = classify(text)
        assert result.intent == Intent.TASK_ADD
        assert "title" in result.params

    def test_extracts_priority(self):
        result = classify("add task fix crash urgent priority")
        assert result.intent == Intent.TASK_ADD
        assert result.params["priority"] == "urgent"

    def test_extracts_deadline(self):
        result = classify("add task deploy by 2026-03-30")
        assert result.intent == Intent.TASK_ADD
        assert result.params["deadline"] == "2026-03-30"

    @pytest.mark.parametrize("text", [
        "my tasks",
        "show tasks",
        "list tasks",
        "what do I need to do",
        "pending tasks",
    ])
    def test_detects_task_list(self, text):
        result = classify(text)
        assert result.intent == Intent.TASK_LIST

    def test_detects_task_done(self):
        result = classify("done abc12345")
        assert result.intent == Intent.TASK_DONE
        assert result.params["task_id"] == "abc12345"

    def test_complete_task(self):
        result = classify("complete task a1b2c3d4")
        assert result.intent == Intent.TASK_DONE


class TestReminderIntents:
    @pytest.mark.parametrize("text", [
        "remind me to deploy at 2026-03-26 15:00",
        "set a reminder to check server at 2026-04-01 09:00",
    ])
    def test_detects_reminder_add(self, text):
        result = classify(text)
        assert result.intent == Intent.REMINDER_ADD
        assert result.params["remind_at"]

    @pytest.mark.parametrize("text", [
        "my reminders",
        "show reminders",
        "list reminders",
    ])
    def test_detects_reminder_list(self, text):
        result = classify(text)
        assert result.intent == Intent.REMINDER_LIST


class TestBriefingIntent:
    @pytest.mark.parametrize("text", [
        "briefing",
        "daily briefing",
        "good morning",
        "what do I have today",
        "morning report",
    ])
    def test_detects_briefing(self, text):
        result = classify(text)
        assert result.intent == Intent.BRIEFING


class TestChat:
    @pytest.mark.parametrize("text", [
        "what is python",
        "explain decorators",
        "how does FAISS work",
        "tell me about machine learning",
        "",
        "   ",
    ])
    def test_falls_back_to_chat(self, text):
        result = classify(text)
        assert result.intent == Intent.CHAT


class TestClassifiedIntent:
    def test_chat_factory(self):
        ci = ClassifiedIntent.chat()
        assert ci.intent == Intent.CHAT
        assert ci.confidence == 1.0
        assert ci.params == {}

    def test_immutable(self):
        ci = ClassifiedIntent.chat()
        with pytest.raises(AttributeError):
            ci.intent = Intent.HELP
