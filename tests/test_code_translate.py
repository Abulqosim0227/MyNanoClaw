import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from claw.core.intent import classify, Intent


class TestRunCodeIntent:
    def test_detects_code_block(self):
        text = 'run this code:\n```python\nprint("hello")\n```'
        result = classify(text)
        assert result.intent == Intent.RUN_CODE
        assert 'print("hello")' in result.params["code"]

    def test_detects_code_no_lang(self):
        text = 'execute:\n```\nx = 1+1\nprint(x)\n```'
        result = classify(text)
        assert result.intent == Intent.RUN_CODE


class TestTranslateIntent:
    def test_translate_to_language(self):
        result = classify("translate to Russian: hello world")
        assert result.intent == Intent.TRANSLATE
        assert result.params["target_lang"].lower() == "russian"
        assert "hello world" in result.params["text"]

    def test_translate_uzbek(self):
        result = classify("translate Uzbek: how are you")
        assert result.intent == Intent.TRANSLATE
        assert result.params["target_lang"].lower() == "uzbek"

    def test_normal_text_not_translate(self):
        result = classify("what is machine learning")
        assert result.intent == Intent.CHAT


class TestRunCode:
    @pytest.mark.asyncio
    async def test_run_simple_code(self):
        from claw.telegram.handlers.code import handle_run_code

        msg = MagicMock()
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        await handle_run_code(msg, 'print("hello from claw")', "python")
        processing.edit_text.assert_awaited_once()
        assert "hello from claw" in processing.edit_text.call_args[0][0]

    @pytest.mark.asyncio
    async def test_run_error_code(self):
        from claw.telegram.handlers.code import handle_run_code

        msg = MagicMock()
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        await handle_run_code(msg, "raise ValueError('test')", "python")
        response = processing.edit_text.call_args[0][0]
        assert "ValueError" in response or "Error" in response

    @pytest.mark.asyncio
    async def test_unsupported_language(self):
        from claw.telegram.handlers.code import handle_run_code

        msg = MagicMock()
        msg.answer = AsyncMock()
        await handle_run_code(msg, "console.log('hi')", "javascript")
        assert "only python" in msg.answer.call_args[0][0].lower()
