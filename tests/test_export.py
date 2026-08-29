"""Tests for export module."""

import pytest
import json
from pathlib import Path

from bookmark_graph.storage import Storage
from bookmark_graph.export import Exporter
from bookmark_graph.models import Post


@pytest.fixture
def temp_db_with_posts(tmp_path):
    """Create a temporary database with sample posts."""
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    
    posts = [
        Post(
            id='1001',
            text='Post one',
            author='alice',
            created_at='2024-01-01T00:00:00Z'
        ),
        Post(
            id='1002',
            text='Post two',
            author='bob',
            created_at='2024-01-01T01:00:00Z',
            reply_to='1001'
        ),
    ]
    
    storage.insert_posts(posts)
    yield storage
    storage.close()


def test_exporter_creation(temp_db_with_posts):
    """Test creating an exporter."""
    exporter = Exporter(temp_db_with_posts)
    assert exporter.storage == temp_db_with_posts


def test_export_json(temp_db_with_posts, tmp_path):
    """Test exporting as JSON."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.json'
    
    exporter.export_json(output_path)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert 'stats' in data
    assert 'posts' in data
    assert len(data['posts']) == 2


def test_export_json_contains_stats(temp_db_with_posts, tmp_path):
    """Test that JSON export contains statistics."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.json'
    
    exporter.export_json(output_path)
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert 'total_posts' in data['stats']
    assert data['stats']['total_posts'] == 2


def test_export_mermaid(temp_db_with_posts, tmp_path):
    """Test exporting as Mermaid."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.mmd'
    
    exporter.export_mermaid(output_path)
    
    assert output_path.exists()
    
    content = output_path.read_text()
    assert 'graph TD' in content


def test_export_mermaid_contains_nodes(temp_db_with_posts, tmp_path):
    """Test that Mermaid export contains nodes."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.mmd'
    
    exporter.export_mermaid(output_path)
    
    content = output_path.read_text()
    assert 'post_1001' in content
    assert 'alice' in content


def test_export_graphviz(temp_db_with_posts, tmp_path):
    """Test exporting as Graphviz."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.dot'
    
    exporter.export_graphviz(output_path)
    
    assert output_path.exists()
    
    content = output_path.read_text()
    assert 'digraph BookmarkGraph' in content


def test_export_graphviz_contains_nodes(temp_db_with_posts, tmp_path):
    """Test that Graphviz export contains nodes."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.dot'
    
    exporter.export_graphviz(output_path)
    
    content = output_path.read_text()
    assert 'post_1001' in content


def test_export_conversation_mermaid(temp_db_with_posts, tmp_path):
    """Test exporting conversation as Mermaid."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'conversation.mmd'
    
    exporter.export_conversation_mermaid('1001', output_path)
    
    assert output_path.exists()
    
    content = output_path.read_text()
    assert 'graph TD' in content
    assert 'post_1001' in content


def test_sanitize_id():
    """Test ID sanitization."""
    from bookmark_graph.export import Exporter
    
    assert Exporter._sanitize_id('1234') == 'post_1234'
    assert Exporter._sanitize_id('abc-def') == 'post_abc_def'


def test_truncate_text():
    """Test text truncation."""
    from bookmark_graph.export import Exporter
    
    short_text = 'Short text'
    assert Exporter._truncate_text(short_text, 20) == 'Short text'
    
    long_text = 'This is a very long text that should be truncated'
    result = Exporter._truncate_text(long_text, 20)
    assert len(result) <= 20
    assert result.endswith('...')


def test_escape_dot():
    """Test DOT format escaping."""
    from bookmark_graph.export import Exporter
    
    text = 'Text with "quotes"'
    escaped = Exporter._escape_dot(text)
    assert '\\\\"' in escaped


def test_export_mermaid_max_nodes(temp_db_with_posts, tmp_path):
    """Test Mermaid export with max nodes limit."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.mmd'
    
    exporter.export_mermaid(output_path, max_nodes=1)
    
    content = output_path.read_text()
    # Should only have one node
    node_count = content.count('[')
    assert node_count <= 2  # One for the node definition


def test_export_graphviz_max_nodes(temp_db_with_posts, tmp_path):
    """Test Graphviz export with max nodes limit."""
    exporter = Exporter(temp_db_with_posts)
    output_path = tmp_path / 'export.dot'
    
    exporter.export_graphviz(output_path, max_nodes=1)
    
    content = output_path.read_text()
    assert 'post_1001' in content
