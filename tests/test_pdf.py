import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from claw.processors.pdf import extract_pdf, PDFResult, MAX_FILE_SIZE


class TestExtractPDF:
    def test_file_not_found(self, tmp_path):
        result = extract_pdf(tmp_path / "nope.pdf")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_valid_pdf(self, tmp_path):
        import fitz
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        text_point = fitz.Point(72, 72)
        page.insert_text(text_point, "Hello world this is a test document with enough words.")
        doc.save(str(pdf_path))
        doc.close()

        result = extract_pdf(pdf_path)
        assert result.success is True
        assert result.pages == 1
        assert result.word_count > 0
        assert "Hello" in result.text or "world" in result.text

    def test_empty_pdf(self, tmp_path):
        import fitz
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        result = extract_pdf(pdf_path)
        assert result.success is True
        assert result.word_count == 0

    def test_result_immutable(self):
        result = PDFResult(text="t", pages=1, word_count=1, title="T", success=True, error="")
        with pytest.raises(AttributeError):
            result.text = "changed"

    def test_oversized_file(self, tmp_path):
        big_file = tmp_path / "big.pdf"
        big_file.write_bytes(b"0" * (MAX_FILE_SIZE + 1))
        result = extract_pdf(big_file)
        assert result.success is False
        assert "large" in result.error.lower()
