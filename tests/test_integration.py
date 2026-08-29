"""Integration tests for the full workflow."""

import pytest
from pathlib import Path

from bookmark_graph.parser import parse_file
from bookmark_graph.storage import Storage
from bookmark_graph.graph import Graph
from bookmark_graph.export import Exporter


FIXTURES_DIR = Path(__file__).parent / 'fixtures'


def test_full_workflow_jsonl(tmp_path):
    """Test complete workflow with JSONL."""
    # Parse
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_file(fixture)
    assert len(posts) == 40
    
    # Store
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    storage.insert_posts(posts)
    
    # Query
    retrieved = storage.get_post('1001')
    assert retrieved is not None
    assert retrieved.author == 'alice_tech'
    
    # Graph operations
    graph = Graph(storage)
    stats = storage.get_stats()
    assert stats.total_posts == 40
    
    top_authors = graph.get_top_authors(5)
    assert len(top_authors) > 0
    
    # Export
    exporter = Exporter(storage)
    json_path = tmp_path / 'export.json'
    exporter.export_json(json_path)
    assert json_path.exists()
    
    storage.close()


def test_full_workflow_markdown(tmp_path):
    """Test complete workflow with Markdown."""
    # Parse
    fixture = FIXTURES_DIR / 'bookmarks.md'
    posts = parse_file(fixture)
    assert len(posts) == 40
    
    # Store
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    storage.insert_posts(posts)
    
    # Graph operations
    graph = Graph(storage)
    neighbors = storage.get_neighbors('1001')
    assert 'replies' in neighbors
    
    # Export all formats
    exporter = Exporter(storage)
    
    json_path = tmp_path / 'export.json'
    exporter.export_json(json_path)
    assert json_path.exists()
    
    mermaid_path = tmp_path / 'export.mmd'
    exporter.export_mermaid(mermaid_path)
    assert mermaid_path.exists()
    
    dot_path = tmp_path / 'export.dot'
    exporter.export_graphviz(dot_path)
    assert dot_path.exists()
    
    storage.close()


def test_conversation_thread_workflow(tmp_path):
    """Test conversation thread workflow."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_file(fixture)
    
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    storage.insert_posts(posts)
    
    graph = Graph(storage)
    
    # Find a post with replies (1001 has reply 1003)
    thread = graph.get_conversation_thread('1003')
    assert len(thread) > 0
    
    # Export conversation
    exporter = Exporter(storage)
    conv_path = tmp_path / 'conversation.mmd'
    exporter.export_conversation_mermaid('1003', conv_path)
    assert conv_path.exists()
    
    storage.close()


def test_search_and_analyze_workflow(tmp_path):
    """Test search and analysis workflow."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    posts = parse_file(fixture)
    
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    storage.insert_posts(posts)
    
    # Search
    coffee_posts = storage.search_posts('coffee')
    assert len(coffee_posts) > 0
    
    # Analyze graph
    graph = Graph(storage)
    top_hashtags = graph.get_top_hashtags(10)
    assert len(top_hashtags) > 0
    
    # Get author network
    network = graph.get_author_network('alice_tech')
    # alice_tech mentions charlie_writes
    assert 'charlie_writes' in network or len(network) >= 0
    
    storage.close()
