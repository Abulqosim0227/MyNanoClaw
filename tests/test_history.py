from pathlib import Path

from claw.core.history import Turn, save_turns, load_turns, turns_to_prompt, estimate_tokens


class TestTurn:
    def test_user_turn(self):
        turn = Turn.user("hello")
        assert turn.role == "user"
        assert turn.content == "hello"
        assert turn.timestamp

    def test_assistant_turn(self):
        turn = Turn.assistant("hi there")
        assert turn.role == "assistant"
        assert turn.content == "hi there"

    def test_turn_is_immutable(self):
        turn = Turn.user("test")
        try:
            turn.content = "changed"
            assert False, "Should not allow mutation"
        except AttributeError:
            pass


class TestSaveLoad:
    def test_round_trip(self, tmp_path):
        path = tmp_path / "test.md"
        turns = [Turn.user("hello"), Turn.assistant("hi")]
        save_turns(path, turns)

        loaded = load_turns(path)
        assert len(loaded) == 2
        assert loaded[0].role == "user"
        assert loaded[0].content == "hello"
        assert loaded[1].role == "assistant"
        assert loaded[1].content == "hi"

    def test_load_nonexistent(self, tmp_path):
        path = tmp_path / "nope.md"
        assert load_turns(path) == []

    def test_empty_turns(self, tmp_path):
        path = tmp_path / "empty.md"
        save_turns(path, [])
        assert load_turns(path) == []

    def test_multiline_content(self, tmp_path):
        path = tmp_path / "multi.md"
        turns = [Turn.user("line1\nline2\nline3")]
        save_turns(path, turns)

        loaded = load_turns(path)
        assert loaded[0].content == "line1\nline2\nline3"

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "test.md"
        save_turns(path, [Turn.user("test")])
        assert path.exists()


class TestTurnsToPrompt:
    def test_basic_prompt(self):
        turns = [Turn.user("q1"), Turn.assistant("a1")]
        result = turns_to_prompt(turns, max_turns=10)
        assert "Human: q1" in result
        assert "Assistant: a1" in result

    def test_truncation(self):
        turns = [Turn.user(f"msg{i}") for i in range(10)]
        result = turns_to_prompt(turns, max_turns=4)
        assert "msg5" not in result
        assert "msg6" in result
        assert "msg9" in result

    def test_empty_history(self):
        assert turns_to_prompt([], max_turns=10) == ""


class TestEstimateTokens:
    def test_estimate(self):
        assert estimate_tokens("a" * 400) == 100

    def test_empty(self):
        assert estimate_tokens("") == 0
