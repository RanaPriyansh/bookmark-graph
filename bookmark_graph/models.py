"""Data models for bookmark graph."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Post:
    """Represents a single post/tweet."""
    
    id: str
    text: str
    author: str
    created_at: str
    url: Optional[str] = None
    mentions: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None
    urls: Optional[List[str]] = None
    reply_to: Optional[str] = None
    
    def __post_init__(self):
        if self.mentions is None:
            self.mentions = []
        if self.hashtags is None:
            self.hashtags = []
        if self.urls is None:
            self.urls = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert post to dictionary."""
        return {
            'id': self.id,
            'text': self.text,
            'author': self.author,
            'created_at': self.created_at,
            'url': self.url,
            'mentions': self.mentions,
            'hashtags': self.hashtags,
            'urls': self.urls,
            'reply_to': self.reply_to,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Post':
        """Create post from dictionary."""
        return cls(
            id=data['id'],
            text=data['text'],
            author=data['author'],
            created_at=data['created_at'],
            url=data.get('url'),
            mentions=data.get('mentions', []),
            hashtags=data.get('hashtags', []),
            urls=data.get('urls', []),
            reply_to=data.get('reply_to'),
        )


@dataclass
class GraphStats:
    """Statistics about the bookmark graph."""
    
    total_posts: int
    total_authors: int
    total_hashtags: int
    total_mentions: int
    total_urls: int
    total_replies: int
    
    def to_dict(self) -> Dict[str, int]:
        """Convert stats to dictionary."""
        return {
            'total_posts': self.total_posts,
            'total_authors': self.total_authors,
            'total_hashtags': self.total_hashtags,
            'total_mentions': self.total_mentions,
            'total_urls': self.total_urls,
            'total_replies': self.total_replies,
        }
