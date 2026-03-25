import pytest
from claw.scraper.parser import parse_html, ParsedPage


SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Page</title>
<meta name="description" content="A test description">
</head>
<body>
<nav><a href="/menu">Menu</a></nav>
<main>
<h1>Hello World</h1>
<p>This is a test paragraph with enough words to pass the minimum threshold for content extraction by trafilatura.</p>
<p>Second paragraph with more content to ensure we have sufficient text for extraction to work properly.</p>
<a href="/about">About</a>
<a href="/contact">Contact</a>
<a href="https://external.com">External</a>
</main>
<footer>Footer content</footer>
<script>var x = 1;</script>
</body>
</html>
"""


class TestParseHtml:
    def test_extracts_title(self):
        result = parse_html(SIMPLE_HTML, base_url="https://example.com")
        assert result.title in ("Test Page", "Hello World")

    def test_extracts_description(self):
        result = parse_html(SIMPLE_HTML, base_url="https://example.com")
        assert result.description == "A test description"

    def test_extracts_text(self):
        result = parse_html(SIMPLE_HTML, base_url="https://example.com")
        assert "Hello World" in result.text or "test paragraph" in result.text

    def test_word_count_positive(self):
        result = parse_html(SIMPLE_HTML, base_url="https://example.com")
        assert result.word_count > 0

    def test_extracts_same_domain_links(self):
        result = parse_html(SIMPLE_HTML, base_url="https://example.com")
        urls = [l for l in result.links if "example.com" in l]
        assert len(urls) >= 1

    def test_excludes_external_links(self):
        result = parse_html(SIMPLE_HTML, base_url="https://example.com")
        external = [l for l in result.links if "external.com" in l]
        assert len(external) == 0

    def test_no_links_without_base_url(self):
        result = parse_html(SIMPLE_HTML)
        assert result.links == []

    def test_empty_html(self):
        result = parse_html("")
        assert result.word_count == 0

    def test_returns_parsed_page(self):
        result = parse_html(SIMPLE_HTML)
        assert isinstance(result, ParsedPage)
