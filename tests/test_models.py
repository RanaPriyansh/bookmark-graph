"""Tests for data models."""

from bookmark_graph.models import Post, GraphStats


def test_post_creation():
    """Test creating a post."""
    post = Post(
        id='1001',
        text='Test post',
        author='test_user',
        created_at='2024-01-01T00:00:00Z'
    )
    assert post.id == '1001'
    assert post.text == 'Test post'
    assert post.author == 'test_user'
    assert post.mentions == []
    assert post.hashtags == []
    assert post.urls == []


def test_post_with_entities():
    """Test creating a post with entities."""
    post = Post(
        id='1001',
        text='Test post',
        author='test_user',
        created_at='2024-01-01T00:00:00Z',
        mentions=['user1', 'user2'],
        hashtags=['test', 'demo'],
        urls=['https://example.com']
    )
    assert post.mentions == ['user1', 'user2']
    assert post.hashtags == ['test', 'demo']
    assert post.urls == ['https://example.com']


def test_post_to_dict():
    """Test converting post to dictionary."""
    post = Post(
        id='1001',
        text='Test post',
        author='test_user',
        created_at='2024-01-01T00:00:00Z',
        mentions=['user1']
    )
    data = post.to_dict()
    assert data['id'] == '1001'
    assert data['text'] == 'Test post'
    assert data['author'] == 'test_user'
    assert data['mentions'] == ['user1']


def test_post_from_dict():
    """Test creating post from dictionary."""
    data = {
        'id': '1001',
        'text': 'Test post',
        'author': 'test_user',
        'created_at': '2024-01-01T00:00:00Z',
        'mentions': ['user1'],
        'hashtags': ['test'],
        'urls': ['https://example.com'],
        'reply_to': '1000'
    }
    post = Post.from_dict(data)
    assert post.id == '1001'
    assert post.text == 'Test post'
    assert post.author == 'test_user'
    assert post.mentions == ['user1']
    assert post.hashtags == ['test']
    assert post.urls == ['https://example.com']
    assert post.reply_to == '1000'


def test_graph_stats_creation():
    """Test creating graph stats."""
    stats = GraphStats(
        total_posts=100,
        total_authors=50,
        total_hashtags=30,
        total_mentions=20,
        total_urls=10,
        total_replies=5
    )
    assert stats.total_posts == 100
    assert stats.total_authors == 50
    assert stats.total_hashtags == 30


def test_graph_stats_to_dict():
    """Test converting stats to dictionary."""
    stats = GraphStats(
        total_posts=100,
        total_authors=50,
        total_hashtags=30,
        total_mentions=20,
        total_urls=10,
        total_replies=5
    )
    data = stats.to_dict()
    assert data['total_posts'] == 100
    assert data['total_authors'] == 50
    assert data['total_replies'] == 5
