"""Tests for storage module."""

import pytest
from pathlib import Path

from bookmark_graph.storage import Storage
from bookmark_graph.models import Post


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    yield storage
    storage.close()


@pytest.fixture
def sample_posts():
    """Create sample posts for testing."""
    return [
        Post(
            id='1001',
            text='Test post one #test',
            author='user1',
            created_at='2024-01-01T00:00:00Z',
            mentions=['user2'],
            hashtags=['test']
        ),
        Post(
            id='1002',
            text='Test post two @user1',
            author='user2',
            created_at='2024-01-01T01:00:00Z',
            mentions=['user1'],
            reply_to='1001'
        ),
        Post(
            id='1003',
            text='Test post three',
            author='user1',
            created_at='2024-01-01T02:00:00Z'
        ),
    ]


def test_storage_creation(tmp_path):
    """Test creating storage."""
    db_path = tmp_path / 'test.db'
    storage = Storage(db_path)
    assert storage.db_path == db_path
    assert storage.conn is not None
    storage.close()


def test_insert_posts(temp_db, sample_posts):
    """Test inserting posts."""
    temp_db.insert_posts(sample_posts)
    
    post = temp_db.get_post('1001')
    assert post is not None
    assert post.id == '1001'
    assert post.author == 'user1'


def test_get_post(temp_db, sample_posts):
    """Test getting a single post."""
    temp_db.insert_posts(sample_posts)
    
    post = temp_db.get_post('1001')
    assert post.id == '1001'
    assert post.text == 'Test post one #test'


def test_get_post_not_found(temp_db):
    """Test getting non-existent post."""
    post = temp_db.get_post('9999')
    assert post is None


def test_get_all_posts(temp_db, sample_posts):
    """Test getting all posts."""
    temp_db.insert_posts(sample_posts)
    
    posts = temp_db.get_all_posts()
    assert len(posts) == 3


def test_search_posts(temp_db, sample_posts):
    """Test searching posts."""
    temp_db.insert_posts(sample_posts)
    
    results = temp_db.search_posts('one')
    assert len(results) == 1
    assert results[0].id == '1001'


def test_search_posts_no_match(temp_db, sample_posts):
    """Test searching with no matches."""
    temp_db.insert_posts(sample_posts)
    
    results = temp_db.search_posts('nonexistent')
    assert len(results) == 0


def test_get_neighbors_replies(temp_db, sample_posts):
    """Test getting neighbor replies."""
    temp_db.insert_posts(sample_posts)
    
    neighbors = temp_db.get_neighbors('1001')
    assert len(neighbors['replies']) == 1
    assert neighbors['replies'][0].id == '1002'


def test_get_neighbors_same_author(temp_db, sample_posts):
    """Test getting neighbors by same author."""
    temp_db.insert_posts(sample_posts)
    
    neighbors = temp_db.get_neighbors('1001')
    assert len(neighbors['by_same_author']) > 0


def test_get_neighbors_mentioned_in(temp_db, sample_posts):
    """Test getting posts that mention the author."""
    temp_db.insert_posts(sample_posts)
    
    neighbors = temp_db.get_neighbors('1001')
    # user1 is mentioned by user2 in post 1002
    assert any(p.id == '1002' for p in neighbors['mentioned_in'])


def test_get_stats(temp_db, sample_posts):
    """Test getting statistics."""
    temp_db.insert_posts(sample_posts)
    
    stats = temp_db.get_stats()
    assert stats.total_posts == 3
    assert stats.total_authors == 2
    assert stats.total_replies == 1


def test_get_stats_empty_db(temp_db):
    """Test getting statistics from empty database."""
    stats = temp_db.get_stats()
    assert stats.total_posts == 0
    assert stats.total_authors == 0


def test_insert_posts_with_mentions(temp_db):
    """Test inserting posts with mentions."""
    post = Post(
        id='1001',
        text='Hello @user1 and @user2',
        author='user3',
        created_at='2024-01-01T00:00:00Z',
        mentions=['user1', 'user2']
    )
    temp_db.insert_posts([post])
    
    retrieved = temp_db.get_post('1001')
    assert len(retrieved.mentions) == 2
    assert 'user1' in retrieved.mentions
    assert 'user2' in retrieved.mentions


def test_insert_posts_with_hashtags(temp_db):
    """Test inserting posts with hashtags."""
    post = Post(
        id='1001',
        text='Testing #test #demo',
        author='user1',
        created_at='2024-01-01T00:00:00Z',
        hashtags=['test', 'demo']
    )
    temp_db.insert_posts([post])
    
    retrieved = temp_db.get_post('1001')
    assert len(retrieved.hashtags) == 2
    assert 'test' in retrieved.hashtags
    assert 'demo' in retrieved.hashtags


def test_insert_posts_with_urls(temp_db):
    """Test inserting posts with URLs."""
    post = Post(
        id='1001',
        text='Check out https://example.com',
        author='user1',
        created_at='2024-01-01T00:00:00Z',
        urls=['https://example.com']
    )
    temp_db.insert_posts([post])
    
    retrieved = temp_db.get_post('1001')
    assert len(retrieved.urls) == 1
    assert 'https://example.com' in retrieved.urls


def test_context_manager(tmp_path):
    """Test storage as context manager."""
    db_path = tmp_path / 'test.db'
    
    with Storage(db_path) as storage:
        assert storage.conn is not None
    
    # Connection should be closed after exiting context


def test_insert_replace_post(temp_db, sample_posts):
    """Test replacing an existing post."""
    temp_db.insert_posts(sample_posts)
    
    # Update post 1001
    updated_post = Post(
        id='1001',
        text='Updated text',
        author='user1',
        created_at='2024-01-01T00:00:00Z'
    )
    temp_db.insert_posts([updated_post])
    
    retrieved = temp_db.get_post('1001')
    assert retrieved.text == 'Updated text'
