"""Tests for bookmark parser."""

import pytest
from pathlib import Path

from bookmark_graph.parser import (
    parse_jsonl, parse_markdown, parse_file,
    detect_format, ParserError
)


FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def test_parse_jsonl_fixture():
    """Test parsing JSONL fixture file."""
    fixture_path = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_jsonl(fixture_path)
    
    assert len(posts) == 40
    assert posts[0].id == '1001'
    assert posts[0].author == 'alice_tech'
    assert 'coffee' in posts[0].hashtags


def test_parse_markdown_fixture():
    """Test parsing Markdown fixture file."""
    fixture_path = FIXTURES_DIR / 'bookmarks.md'
    posts = parse_markdown(fixture_path)
    
    assert len(posts) == 40
    assert posts[0].id == '1001'
    assert posts[0].author == 'alice_tech'


def test_parse_jsonl_with_mentions():
    """Test parsing JSONL with mentions."""
    fixture_path = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_jsonl(fixture_path)
    
    # Post 1003 mentions alice_tech
    post = next(p for p in posts if p.id == '1003')
    assert 'alice_tech' in post.mentions


def test_parse_jsonl_with_reply():
    """Test parsing JSONL with replies."""
    fixture_path = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_jsonl(fixture_path)
    
    # Post 1003 is a reply to 1001
    post = next(p for p in posts if p.id == '1003')
    assert post.reply_to == '1001'


def test_parse_jsonl_missing_file():
    """Test parsing non-existent JSONL file."""
    with pytest.raises(ParserError, match='File not found'):
        parse_jsonl(Path('/nonexistent/file.jsonl'))


def test_parse_markdown_missing_file():
    """Test parsing non-existent Markdown file."""
    with pytest.raises(ParserError, match='File not found'):
        parse_markdown(Path('/nonexistent/file.md'))


def test_detect_format_jsonl():
    """Test format detection for JSONL."""
    fixture_path = FIXTURES_DIR / 'bookmarks.jsonl'
    assert detect_format(fixture_path) == 'jsonl'


def test_detect_format_markdown():
    """Test format detection for Markdown."""
    fixture_path = FIXTURES_DIR / 'bookmarks.md'
    assert detect_format(fixture_path) == 'markdown'


def test_parse_file_auto_detect_jsonl():
    """Test auto-detecting and parsing JSONL."""
    fixture_path = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_file(fixture_path)
    assert len(posts) == 40


def test_parse_file_auto_detect_markdown():
    """Test auto-detecting and parsing Markdown."""
    fixture_path = FIXTURES_DIR / 'bookmarks.md'
    posts = parse_file(fixture_path)
    assert len(posts) == 40


def test_parse_jsonl_invalid_json(tmp_path):
    """Test parsing invalid JSON."""
    invalid_file = tmp_path / 'invalid.jsonl'
    invalid_file.write_text('{"invalid": json}\n')
    
    with pytest.raises(ParserError, match='Invalid JSON'):
        parse_jsonl(invalid_file)


def test_parse_jsonl_missing_required_field(tmp_path):
    """Test parsing JSON with missing required field."""
    invalid_file = tmp_path / 'invalid.jsonl'
    invalid_file.write_text('{"id": "1001"}\n')
    
    with pytest.raises(ParserError, match='Missing required field'):
        parse_jsonl(invalid_file)


def test_parse_jsonl_empty_file(tmp_path):
    """Test parsing empty JSONL file."""
    empty_file = tmp_path / 'empty.jsonl'
    empty_file.write_text('')
    
    posts = parse_jsonl(empty_file)
    assert len(posts) == 0


def test_parse_markdown_empty_file(tmp_path):
    """Test parsing empty Markdown file."""
    empty_file = tmp_path / 'empty.md'
    empty_file.write_text('')
    
    posts = parse_markdown(empty_file)
    assert len(posts) == 0


def test_parse_jsonl_with_urls():
    """Test parsing JSONL with URLs."""
    fixture_path = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_jsonl(fixture_path)
    
    # Post 1002 has a URL
    post = next(p for p in posts if p.id == '1002')
    assert len(post.urls) > 0
    assert 'github.example.com' in post.urls[0]
