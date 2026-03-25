from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

MAX_DURATION = 300


@dataclass(frozen=True)
class VoiceResult:
    text: str
    duration_seconds: float
    success: bool
    error: str


def transcribe_voice(file_path: Path, language: str = "en-US") -> VoiceResult:
    if not file_path.exists():
        return VoiceResult(text="", duration_seconds=0, success=False, error="File not found")

    try:
        from pydub import AudioSegment
        import speech_recognition as sr
    except ImportError as e:
        return VoiceResult(text="", duration_seconds=0, success=False, error=f"Missing dependency: {e}")

    try:
        audio = AudioSegment.from_file(str(file_path))
        duration = len(audio) / 1000.0

        if duration > MAX_DURATION:
            return VoiceResult(text="", duration_seconds=duration, success=False, error=f"Audio too long ({duration:.0f}s, max {MAX_DURATION}s)")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
            audio.export(tmp.name, format="wav")

            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp.name) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data, language=language)

        return VoiceResult(
            text=text,
            duration_seconds=duration,
            success=True,
            error="",
        )

    except sr.UnknownValueError:
        return VoiceResult(text="", duration_seconds=0, success=False, error="Could not understand audio")
    except sr.RequestError as e:
        return VoiceResult(text="", duration_seconds=0, success=False, error=f"Speech service error: {e}")
    except Exception as e:
        return VoiceResult(text="", duration_seconds=0, success=False, error=f"Audio processing failed: {e}")
