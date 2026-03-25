import pytest

from claw.core.history import Turn
from claw.core.session import SessionManager, SessionError, validate_session_name


class TestValidateSessionName:
    def test_valid_names(self):
        assert validate_session_name("default") == "default"
        assert validate_session_name("my-session") == "my-session"
        assert validate_session_name("session_123") == "session_123"

    def test_normalizes_to_lowercase(self):
        assert validate_session_name("MySession") == "mysession"

    def test_strips_whitespace(self):
        assert validate_session_name("  test  ") == "test"

    def test_rejects_path_traversal(self):
        with pytest.raises(SessionError):
            validate_session_name("../etc/passwd")

    def test_rejects_spaces(self):
        with pytest.raises(SessionError):
            validate_session_name("my session")

    def test_rejects_empty(self):
        with pytest.raises(SessionError):
            validate_session_name("")

    def test_rejects_too_long(self):
        with pytest.raises(SessionError):
            validate_session_name("a" * 65)

    def test_rejects_special_chars(self):
        with pytest.raises(SessionError):
            validate_session_name("test;rm -rf /")


class TestSessionManager:
    def test_list_empty(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        assert sm.list_sessions() == []

    def test_save_and_load(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        turns = [Turn.user("hello"), Turn.assistant("hi")]
        sm.save("test", turns)

        loaded = sm.load("test")
        assert len(loaded) == 2

    def test_exists(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        assert sm.exists("test") is False
        sm.save("test", [Turn.user("hi")])
        assert sm.exists("test") is True

    def test_list_sessions(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        sm.save("alpha", [Turn.user("a")])
        sm.save("beta", [Turn.user("b")])
        assert sm.list_sessions() == ["alpha", "beta"]

    def test_append(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        sm.save("test", [])
        sm.append("test", Turn.user("q"), Turn.assistant("a"))
        turns = sm.load("test")
        assert len(turns) == 2

    def test_branch(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        sm.save("source", [Turn.user("data")])
        sm.branch("source", "copy")

        assert sm.exists("copy")
        assert len(sm.load("copy")) == 1

    def test_branch_missing_source(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        with pytest.raises(SessionError, match="does not exist"):
            sm.branch("nope", "copy")

    def test_branch_existing_target(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        sm.save("a", [Turn.user("x")])
        sm.save("b", [Turn.user("y")])
        with pytest.raises(SessionError, match="already exists"):
            sm.branch("a", "b")

    def test_delete(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        sm.save("test", [Turn.user("x")])
        sm.delete("test")
        assert sm.exists("test") is False

    def test_stats(self, tmp_session_dir):
        sm = SessionManager(base_dir=tmp_session_dir)
        sm.save("test", [Turn.user("hello"), Turn.assistant("world")])
        stats = sm.stats("test")
        assert stats["turns"] == 2
        assert stats["user_messages"] == 1
        assert stats["assistant_messages"] == 1
        assert stats["total_chars"] == 10
