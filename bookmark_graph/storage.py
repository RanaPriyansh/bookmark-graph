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
            
            # Index for mention lookups in get_neighbors
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mentions_username ON mentions(username)
            """)
            
            # Index for hashtag lookups
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hashtags_tag ON hashtags(tag)
            """)
            
            # Index for bulk fetches by post_id
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mentions_post_id ON mentions(post_id)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hashtags_post_id ON hashtags(post_id)
            """)
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_urls_post_id ON urls(post_id)
            """)
    
    def insert_posts(self, posts: List[Post]):
        """Insert posts into database.
        
        Args:
            posts: List of Post objects to insert
        """
        if not posts:
            return
        
        # Batch all operations in a single transaction
        with self.conn:
            # Collect all data for bulk operations
            post_rows = []
            mention_rows = []
            hashtag_rows = []
            url_rows = []
            post_ids = []
            
            for post in posts:
                post_ids.append((post.id,))
                post_rows.append((
                    post.id, post.text, post.author, 
                    post.created_at, post.url, post.reply_to
                ))
                
                for mention in post.mentions:
                    mention_rows.append((post.id, mention))
                
                for hashtag in post.hashtags:
                    hashtag_rows.append((post.id, hashtag))
                
                for url in post.urls:
                    url_rows.append((post.id, url))
            
            # Delete old relationships in bulk
            self.conn.executemany(
                "DELETE FROM mentions WHERE post_id = ?", post_ids
            )
            self.conn.executemany(
                "DELETE FROM hashtags WHERE post_id = ?", post_ids
            )
            self.conn.executemany(
                "DELETE FROM urls WHERE post_id = ?", post_ids
            )
            
            # Insert posts in bulk
            self.conn.executemany("""
                INSERT OR REPLACE INTO posts
                (id, text, author, created_at, url, reply_to)
                VALUES (?, ?, ?, ?, ?, ?)
            """, post_rows)
            
            # Insert relationships in bulk
            if mention_rows:
                self.conn.executemany(
                    "INSERT INTO mentions (post_id, username) VALUES (?, ?)",
                    mention_rows
                )
            
            if hashtag_rows:
                self.conn.executemany(
                    "INSERT INTO hashtags (post_id, tag) VALUES (?, ?)",
                    hashtag_rows
                )
            
            if url_rows:
                self.conn.executemany(
                    "INSERT INTO urls (post_id, url) VALUES (?, ?)",
                    url_rows
                )
    
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
        
        rows = cursor.fetchall()
        if not rows:
            return []
        
        return self._bulk_rows_to_posts(rows)
    
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
        
        rows = cursor.fetchall()
        if not rows:
            return []
        
        return self._bulk_rows_to_posts(rows)
    
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
    
    def _bulk_rows_to_posts(self, rows) -> List[Post]:
        """Convert multiple database rows to Post objects efficiently.
        
        Fetches all relationships in bulk (3 queries) instead of per-post (3N queries).
        """
        if not rows:
            return []
        
        post_ids = [row['id'] for row in rows]
        
        # Fetch all mentions in one query
        placeholders = ','.join('?' * len(post_ids))
        cursor = self.conn.execute(f"""
            SELECT post_id, username 
            FROM mentions 
            WHERE post_id IN ({placeholders})
        """, post_ids)
        mentions_map = {}
        for row in cursor.fetchall():
            post_id = row[0]
            if post_id not in mentions_map:
                mentions_map[post_id] = []
            mentions_map[post_id].append(row[1])
        
        # Fetch all hashtags in one query
        cursor = self.conn.execute(f"""
            SELECT post_id, tag 
            FROM hashtags 
            WHERE post_id IN ({placeholders})
        """, post_ids)
        hashtags_map = {}
        for row in cursor.fetchall():
            post_id = row[0]
            if post_id not in hashtags_map:
                hashtags_map[post_id] = []
            hashtags_map[post_id].append(row[1])
        
        # Fetch all URLs in one query
        cursor = self.conn.execute(f"""
            SELECT post_id, url 
            FROM urls 
            WHERE post_id IN ({placeholders})
        """, post_ids)
        urls_map = {}
        for row in cursor.fetchall():
            post_id = row[0]
            if post_id not in urls_map:
                urls_map[post_id] = []
            urls_map[post_id].append(row[1])
        
        # Build Post objects
        posts = []
        for row in rows:
            post_id = row['id']
            posts.append(Post(
                id=post_id,
                text=row['text'],
                author=row['author'],
                created_at=row['created_at'],
                url=row['url'],
                mentions=mentions_map.get(post_id, []),
                hashtags=hashtags_map.get(post_id, []),
                urls=urls_map.get(post_id, []),
                reply_to=row['reply_to'],
            ))
        
        return posts
    
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
