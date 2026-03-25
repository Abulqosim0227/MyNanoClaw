import pytest
from claw.rag.chunker import split_text, Chunk, CHUNK_SIZE, MIN_CHUNK_SIZE


class TestSplitText:
    def test_short_text_single_chunk(self):
        chunks = split_text("hello world", "https://a.com", "Title")
        assert len(chunks) == 1
        assert chunks[0].text == "hello world"
        assert chunks[0].source_url == "https://a.com"
        assert chunks[0].chunk_index == 0
        assert chunks[0].total_chunks == 1

    def test_long_text_multiple_chunks(self):
        words = " ".join(f"word{i}" for i in range(1000))
        chunks = split_text(words, "https://a.com", "Title")
        assert len(chunks) > 1
        for c in chunks:
            assert c.total_chunks == len(chunks)

    def test_overlap_between_chunks(self):
        words = " ".join(f"w{i}" for i in range(1000))
        chunks = split_text(words, "https://a.com", "T", chunk_size=100, overlap=20)
        if len(chunks) >= 2:
            words_0 = set(chunks[0].text.split())
            words_1 = set(chunks[1].text.split())
            assert len(words_0 & words_1) > 0

    def test_empty_text(self):
        assert split_text("", "https://a.com", "T") == []

    def test_whitespace_only(self):
        assert split_text("   ", "https://a.com", "T") == []

    def test_chunk_immutable(self):
        chunks = split_text("hello world", "https://a.com", "T")
        with pytest.raises(AttributeError):
            chunks[0].text = "changed"

    def test_metadata_preserved(self):
        chunks = split_text("enough words here for a chunk", "https://example.com/page", "My Page")
        assert chunks[0].source_url == "https://example.com/page"
        assert chunks[0].source_title == "My Page"

    def test_sequential_indices(self):
        words = " ".join(f"w{i}" for i in range(1000))
        chunks = split_text(words, "https://a.com", "T")
        for i, c in enumerate(chunks):
            assert c.chunk_index == i
