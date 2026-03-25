from claw.security.sanitizer import (
    sanitize_message,
    is_safe_for_shell,
    sanitize_for_shell,
    MAX_MESSAGE_LENGTH,
)


class TestSanitizeMessage:
    def test_strips_whitespace(self):
        assert sanitize_message("  hello  ") == "hello"

    def test_empty_string(self):
        assert sanitize_message("") == ""

    def test_none_returns_empty(self):
        assert sanitize_message(None) == ""

    def test_truncates_long_message(self):
        long_msg = "a" * (MAX_MESSAGE_LENGTH + 100)
        result = sanitize_message(long_msg)
        assert len(result) == MAX_MESSAGE_LENGTH

    def test_strips_null_bytes(self):
        assert sanitize_message("hello\x00world") == "helloworld"

    def test_whitespace_only(self):
        assert sanitize_message("   \n\t  ") == ""


class TestShellSafety:
    def test_safe_text(self):
        assert is_safe_for_shell("hello world") is True

    def test_detects_command_substitution(self):
        assert is_safe_for_shell("$(rm -rf /)") is False

    def test_detects_backtick_substitution(self):
        assert is_safe_for_shell("`rm -rf /`") is False

    def test_detects_brace_expansion(self):
        assert is_safe_for_shell("${HOME}") is False

    def test_sanitize_quotes(self):
        assert sanitize_for_shell("it's a test") == "it'\\''s a test"

    def test_normal_text_unchanged(self):
        assert sanitize_for_shell("hello world") == "hello world"
