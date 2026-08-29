"""Tests for graph module."""

import pytest
from pathlib import Path

from bookmark_graph.storage import Storage
from bookmark_graph.graph import Graph
from bookmark_graph.models import Post


@pytest.fixture
def temp_db_with_posts(tmp_path):
    """Create a temporary database with sample posts."""
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    
    posts = [
        Post(
            id='1001',
            text='Root post #test',
            author='alice',
            created_at='2024-01-01T00:00:00Z',
            hashtags=['test']
        ),
        Post(
            id='1002',
            text='Reply to alice @alice',
            author='bob',
            created_at='2024-01-01T01:00:00Z',
            mentions=['alice'],
            reply_to='1001'
        ),
        Post(
            id='1003',
            text='Another post #test',
            author='charlie',
            created_at='2024-01-01T02:00:00Z',
            hashtags=['test']
        ),
        Post(
            id='1004',
            text='Alice again',
            author='alice',
            created_at='2024-01-01T03:00:00Z'
        ),
        Post(
            id='1005',
            text='Reply to bob @bob',
            author='alice',
            created_at='2024-01-01T04:00:00Z',
            mentions=['bob'],
            reply_to='1002'
        ),
    ]
    
    storage.insert_posts(posts)
    yield storage
    storage.close()


def test_graph_creation(temp_db_with_posts):
    """Test creating a graph."""
    graph = Graph(temp_db_with_posts)
    assert graph.storage == temp_db_with_posts


def test_build_adjacency_list(temp_db_with_posts):
    """Test building adjacency list."""
    graph = Graph(temp_db_with_posts)
    adjacency = graph.build_adjacency_list()
    
    # Post 1002 replies to 1001
    assert '1001' in adjacency['1002']
    assert '1002' in adjacency['1001']


def test_find_connected_component(temp_db_with_posts):
    """Test finding connected component."""
    graph = Graph(temp_db_with_posts)
    component = graph.find_connected_component('1001')
    
    # Should include reply chain
    assert '1001' in component
    assert '1002' in component


def test_find_connected_component_nonexistent(temp_db_with_posts):
    """Test finding connected component for non-existent post."""
    graph = Graph(temp_db_with_posts)
    component = graph.find_connected_component('9999')
    
    assert len(component) == 0


def test_get_author_network(temp_db_with_posts):
    """Test getting author network."""
    graph = Graph(temp_db_with_posts)
    network = graph.get_author_network('alice')
    
    # Alice mentions bob
    assert 'bob' in network
    assert network['bob'] > 0


def test_get_author_network_no_posts(temp_db_with_posts):
    """Test getting author network for non-existent author."""
    graph = Graph(temp_db_with_posts)
    network = graph.get_author_network('nonexistent')
    
    assert len(network) == 0


def test_get_hashtag_network(temp_db_with_posts):
    """Test getting hashtag network."""
    graph = Graph(temp_db_with_posts)
    posts = graph.get_hashtag_network('test')
    
    # Two posts have #test
    assert len(posts) == 2


def test_get_hashtag_network_no_matches(temp_db_with_posts):
    """Test getting hashtag network with no matches."""
    graph = Graph(temp_db_with_posts)
    posts = graph.get_hashtag_network('nonexistent')
    
    assert len(posts) == 0


def test_get_top_authors(temp_db_with_posts):
    """Test getting top authors."""
    graph = Graph(temp_db_with_posts)
    top = graph.get_top_authors(limit=5)
    
    # Alice has 3 posts
    assert len(top) > 0
    assert top[0][0] == 'alice'
    assert top[0][1] == 3


def test_get_top_authors_with_limit(temp_db_with_posts):
    """Test getting top authors with limit."""
    graph = Graph(temp_db_with_posts)
    top = graph.get_top_authors(limit=2)
    
    assert len(top) <= 2


def test_get_top_hashtags(temp_db_with_posts):
    """Test getting top hashtags."""
    graph = Graph(temp_db_with_posts)
    top = graph.get_top_hashtags(limit=5)
    
    # 'test' appears twice
    assert len(top) > 0
    assert top[0][0] == 'test'
    assert top[0][1] == 2


def test_get_top_hashtags_with_limit(temp_db_with_posts):
    """Test getting top hashtags with limit."""
    graph = Graph(temp_db_with_posts)
    top = graph.get_top_hashtags(limit=1)
    
    assert len(top) <= 1


def test_get_conversation_thread(temp_db_with_posts):
    """Test getting conversation thread."""
    graph = Graph(temp_db_with_posts)
    thread = graph.get_conversation_thread('1002')
    
    # Should include 1001, 1002, 1005
    assert len(thread) >= 2
    assert any(p.id == '1001' for p in thread)
    assert any(p.id == '1002' for p in thread)


def test_get_conversation_thread_root(temp_db_with_posts):
    """Test getting conversation thread from root."""
    graph = Graph(temp_db_with_posts)
    thread = graph.get_conversation_thread('1001')
    
    # Should include all replies
    assert len(thread) >= 1


def test_get_conversation_thread_nonexistent(temp_db_with_posts):
    """Test getting conversation thread for non-existent post."""
    graph = Graph(temp_db_with_posts)
    thread = graph.get_conversation_thread('9999')
    
    assert len(thread) == 0
