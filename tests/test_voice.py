import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from claw.processors.voice import VoiceResult, MAX_DURATION


class TestVoiceResult:
    def test_immutable(self):
        r = VoiceResult(text="hi", duration_seconds=1.0, success=True, error="")
        with pytest.raises(AttributeError):
            r.text = "changed"

    def test_structure(self):
        r = VoiceResult(text="hello", duration_seconds=5.0, success=True, error="")
        assert r.text == "hello"
        assert r.duration_seconds == 5.0
        assert r.success is True


class TestTranscribeVoice:
    def test_file_not_found(self, tmp_path):
        from claw.processors.voice import transcribe_voice
        result = transcribe_voice(tmp_path / "nope.ogg")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_max_duration_constant(self):
        assert MAX_DURATION == 300
