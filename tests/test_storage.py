import pytest
from claw.scraper.storage import PageStorage, StoredPage


class TestPageStorage:
    def test_save_and_load(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        stored = storage.save(
            url="https://example.com/page",
            title="Test",
            text="Some content here",
            word_count=3,
            description="A test",
        )
        assert stored.url == "https://example.com/page"
        assert stored.word_count == 3

        loaded = storage.load("https://example.com/page")
        assert loaded is not None
        assert loaded.text == "Some content here"
        assert loaded.title == "Test"

    def test_exists(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        assert storage.exists("https://nope.com") is False
        storage.save("https://nope.com", "T", "text", 1, "")
        assert storage.exists("https://nope.com") is True

    def test_is_duplicate_same_content(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        storage.save("https://a.com", "T", "same content", 2, "")
        assert storage.is_duplicate("https://a.com", "same content") is True

    def test_is_duplicate_different_content(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        storage.save("https://a.com", "T", "original", 1, "")
        assert storage.is_duplicate("https://a.com", "changed") is False

    def test_is_duplicate_not_exists(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        assert storage.is_duplicate("https://nope.com", "text") is False

    def test_list_pages(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        storage.save("https://a.com", "A", "text a", 2, "")
        storage.save("https://b.com", "B", "text b", 2, "")
        pages = storage.list_pages()
        assert len(pages) == 2

    def test_delete(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        storage.save("https://a.com", "A", "text", 1, "")
        assert storage.delete("https://a.com") is True
        assert storage.exists("https://a.com") is False

    def test_delete_nonexistent(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        assert storage.delete("https://nope.com") is False

    def test_stats(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        storage.save("https://a.com", "A", "one two three", 3, "")
        storage.save("https://b.com", "B", "four five", 2, "")
        stats = storage.stats()
        assert stats["total_pages"] == 2
        assert stats["total_words"] == 5

    def test_load_nonexistent(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        assert storage.load("https://nope.com") is None

    def test_creates_directories(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "deep" / "nested" / "knowledge")
        storage.save("https://a.com", "A", "text", 1, "")
        assert storage.exists("https://a.com")

    def test_stored_page_immutable(self, tmp_path):
        storage = PageStorage(base_dir=tmp_path / "knowledge")
        stored = storage.save("https://a.com", "A", "text", 1, "")
        with pytest.raises(AttributeError):
            stored.url = "changed"
