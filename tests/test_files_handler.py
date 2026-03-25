import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from claw.scraper.storage import PageStorage
from claw.telegram.handlers import files


@pytest.fixture
def setup_files(tmp_path):
    storage = PageStorage(base_dir=tmp_path / "knowledge")
    files.setup(storage)
    return storage


def _make_doc_message(file_name: str, file_id: str = "abc123") -> MagicMock:
    msg = MagicMock()
    msg.document = MagicMock()
    msg.document.file_name = file_name
    msg.document.file_id = file_id
    msg.bot = MagicMock()
    msg.answer = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    msg.voice = None
    return msg


def _make_voice_message(file_id: str = "voice123") -> MagicMock:
    msg = MagicMock()
    msg.document = None
    msg.voice = MagicMock()
    msg.voice.file_id = file_id
    msg.bot = MagicMock()
    msg.answer = AsyncMock(return_value=MagicMock(edit_text=AsyncMock()))
    return msg


class TestHandleDocument:
    @pytest.mark.asyncio
    async def test_unsupported_extension(self, setup_files):
        msg = _make_doc_message("file.exe")
        await files.handle_document(msg)
        msg.answer.assert_awaited_once()
        assert "unsupported" in msg.answer.call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_supported_extensions(self):
        for ext in [".pdf", ".txt", ".md", ".docx", ".py", ".json", ".csv", ".html", ".js"]:
            assert ext in files.SUPPORTED_EXTENSIONS


class TestFileProcessing:
    @pytest.mark.asyncio
    async def test_pdf_processing(self, setup_files, tmp_path):
        import fitz
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(fitz.Point(72, 72), "Test content for indexing with enough words here.")
        doc.save(str(pdf_path))
        doc.close()

        msg = _make_doc_message("test.pdf")
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        with patch.object(files, "_download_file", new_callable=AsyncMock, return_value=pdf_path):
            await files.handle_document(msg)
            processing.edit_text.assert_awaited_once()
            response = processing.edit_text.call_args[0][0]
            assert "saved" in response.lower() or "test" in response.lower()

    @pytest.mark.asyncio
    async def test_txt_processing(self, setup_files, tmp_path):
        txt_path = tmp_path / "notes.txt"
        txt_path.write_text("Important notes about Python programming and development", encoding="utf-8")

        msg = _make_doc_message("notes.txt")
        processing = MagicMock(edit_text=AsyncMock())
        msg.answer = AsyncMock(return_value=processing)

        with patch.object(files, "_download_file", new_callable=AsyncMock, return_value=txt_path):
            await files.handle_document(msg)
            processing.edit_text.assert_awaited_once()
