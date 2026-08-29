"""SQLite storage for bookmark graph."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Set

from .models import Post, GraphStats


class Storage:
    """SQLite storage for posts and graph data."""
    
    def __init__(self, db_path: Path):
        """Initialize storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    author TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    url TEXT,
                    reply_to TEXT
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS mentions (
                    post_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    PRIMARY KEY (post_id, username)
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS hashtags (
                    post_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    PRIMARY KEY (post_id, tag)
                )
            """)
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    post_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    PRIMARY KEY (post_id, url)
                )
            """)
            
            # Create indexes for common queries
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_author ON posts(author)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reply_to ON posts(reply_to)
            """)
    
    def insert_posts(self, posts: List[Post]):
        """Insert posts into database.
        
        Args:
            posts: List of Post objects to insert
        """
        with self.conn:
            for post in posts:
                # Insert post
                self.conn.execute("""
                    INSERT OR REPLACE INTO posts
                    (id, text, author, created_at, url, reply_to)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (post.id, post.text, post.author, post.created_at,
                      post.url, post.reply_to))
                
                # Delete old relationships
                self.conn.execute("DELETE FROM mentions WHERE post_id = ?", (post.id,))
                self.conn.execute("DELETE FROM hashtags WHERE post_id = ?", (post.id,))
                self.conn.execute("DELETE FROM urls WHERE post_id = ?", (post.id,))
                
                # Insert mentions
                for mention in post.mentions:
                    self.conn.execute("""
                        INSERT INTO mentions (post_id, username)
                        VALUES (?, ?)
                    """, (post.id, mention))
                
                # Insert hashtags
                for hashtag in post.hashtags:
                    self.conn.execute("""
                        INSERT INTO hashtags (post_id, tag)
                        VALUES (?, ?)
                    """, (post.id, hashtag))
                
                # Insert URLs
                for url in post.urls:
                    self.conn.execute("""
                        INSERT INTO urls (post_id, url)
                        VALUES (?, ?)
                    """, (post.id, url))
    
    def get_post(self, post_id: str) -> Optional[Post]:
        """Get a single post by ID.
        
        Args:
            post_id: Post ID
            
        Returns:
            Post object or None if not found
        """
        cursor = self.conn.execute("""
            SELECT id, text, author, created_at, url, reply_to
            FROM posts
            WHERE id = ?
        """, (post_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return self._row_to_post(row)
    
    def get_all_posts(self) -> List[Post]:
        """Get all posts.
        
        Returns:
            List of all Post objects
        """
        cursor = self.conn.execute("""
            SELECT id, text, author, created_at, url, reply_to
            FROM posts
            ORDER BY created_at
        """)
        
        return [self._row_to_post(row) for row in cursor.fetchall()]
    
    def search_posts(self, query: str) -> List[Post]:
        """Search posts by text content.
        
        Args:
            query: Search query
            
        Returns:
            List of matching Post objects
        """
        cursor = self.conn.execute("""
            SELECT id, text, author, created_at, url, reply_to
            FROM posts
            WHERE text LIKE ?
            ORDER BY created_at
        """, (f'%{query}%',))
        
        return [self._row_to_post(row) for row in cursor.fetchall()]
    
    def get_neighbors(self, post_id: str) -> dict:
        """Get neighboring posts (replies, mentions, same author).
        
        Args:
            post_id: Post ID
            
        Returns:
            Dictionary with 'replies', 'mentioned_in', 'by_same_author'
        """
        post = self.get_post(post_id)
        if not post:
            return {'replies': [], 'mentioned_in': [], 'by_same_author': []}
        
        # Get replies to this post
        cursor = self.conn.execute("""
            SELECT id, text, author, created_at, url, reply_to
            FROM posts
            WHERE reply_to = ?
        """, (post_id,))
        replies = [self._row_to_post(row) for row in cursor.fetchall()]
        
        # Get posts that mention this author
        cursor = self.conn.execute("""
            SELECT DISTINCT p.id, p.text, p.author, p.created_at, p.url, p.reply_to
            FROM posts p
            JOIN mentions m ON p.id = m.post_id
            WHERE m.username = ? AND p.id != ?
        """, (post.author, post_id))
        mentioned_in = [self._row_to_post(row) for row in cursor.fetchall()]
        
        # Get other posts by same author
        cursor = self.conn.execute("""
            SELECT id, text, author, created_at, url, reply_to
            FROM posts
            WHERE author = ? AND id != ?
            LIMIT 10
        """, (post.author, post_id))
        by_same_author = [self._row_to_post(row) for row in cursor.fetchall()]
        
        return {
            'replies': replies,
            'mentioned_in': mentioned_in,
            'by_same_author': by_same_author,
        }
    
    def get_stats(self) -> GraphStats:
        """Get graph statistics.
        
        Returns:
            GraphStats object
        """
        cursor = self.conn.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(DISTINCT author) FROM posts")
        total_authors = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(DISTINCT tag) FROM hashtags")
        total_hashtags = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(DISTINCT username) FROM mentions")
        total_mentions = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(DISTINCT url) FROM urls")
        total_urls = cursor.fetchone()[0]
        
        cursor = self.conn.execute("SELECT COUNT(*) FROM posts WHERE reply_to IS NOT NULL")
        total_replies = cursor.fetchone()[0]
        
        return GraphStats(
            total_posts=total_posts,
            total_authors=total_authors,
            total_hashtags=total_hashtags,
            total_mentions=total_mentions,
            total_urls=total_urls,
            total_replies=total_replies,
        )
    
    def _row_to_post(self, row) -> Post:
        """Convert database row to Post object."""
        post_id = row['id']
        
        # Get mentions
        cursor = self.conn.execute("""
            SELECT username FROM mentions WHERE post_id = ?
        """, (post_id,))
        mentions = [r[0] for r in cursor.fetchall()]
        
        # Get hashtags
        cursor = self.conn.execute("""
            SELECT tag FROM hashtags WHERE post_id = ?
        """, (post_id,))
        hashtags = [r[0] for r in cursor.fetchall()]
        
        # Get URLs
        cursor = self.conn.execute("""
            SELECT url FROM urls WHERE post_id = ?
        """, (post_id,))
        urls = [r[0] for r in cursor.fetchall()]
        
        return Post(
            id=row['id'],
            text=row['text'],
            author=row['author'],
            created_at=row['created_at'],
            url=row['url'],
            mentions=mentions,
            hashtags=hashtags,
            urls=urls,
            reply_to=row['reply_to'],
        )
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
