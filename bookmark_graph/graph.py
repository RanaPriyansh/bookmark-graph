"""Graph operations and analysis."""

from typing import Dict, List, Set, Tuple
from collections import defaultdict

from .models import Post
from .storage import Storage


class Graph:
    """Knowledge graph operations."""
    
    def __init__(self, storage: Storage):
        """Initialize graph.
        
        Args:
            storage: Storage instance
        """
        self.storage = storage
    
    def build_adjacency_list(self) -> Dict[str, Set[str]]:
        """Build adjacency list for the graph.
        
        Returns:
            Dictionary mapping post IDs to sets of connected post IDs
        """
        adjacency = defaultdict(set)
        posts = self.storage.get_all_posts()
        
        for post in posts:
            # Add reply connections
            if post.reply_to:
                adjacency[post.id].add(post.reply_to)
                adjacency[post.reply_to].add(post.id)
            
            # Add mention connections
            for mention in post.mentions:
                # Find posts by mentioned author
                for other_post in posts:
                    if other_post.author == mention and other_post.id != post.id:
                        adjacency[post.id].add(other_post.id)
        
        return dict(adjacency)
    
    def find_connected_component(self, post_id: str) -> Set[str]:
        """Find all posts connected to a given post.
        
        Args:
            post_id: Starting post ID
            
        Returns:
            Set of connected post IDs
        """
        adjacency = self.build_adjacency_list()
        
        if post_id not in adjacency and not self.storage.get_post(post_id):
            return set()
        
        visited = set()
        stack = [post_id]
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            
            visited.add(current)
            
            if current in adjacency:
                for neighbor in adjacency[current]:
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        return visited
    
    def get_author_network(self, author: str) -> Dict[str, int]:
        """Get network of authors connected to a given author.
        
        Args:
            author: Author username
            
        Returns:
            Dictionary mapping author names to connection counts
        """
        posts = self.storage.get_all_posts()
        author_posts = [p for p in posts if p.author == author]
        
        connections = defaultdict(int)
        
        for post in author_posts:
            # Count mentions
            for mention in post.mentions:
                connections[mention] += 1
            
            # Count replies
            if post.reply_to:
                reply_post = self.storage.get_post(post.reply_to)
                if reply_post:
                    connections[reply_post.author] += 1
        
        # Remove self-connections
        if author in connections:
            del connections[author]
        
        return dict(connections)
    
    def get_hashtag_network(self, hashtag: str) -> List[Post]:
        """Get posts that use a given hashtag.
        
        Args:
            hashtag: Hashtag (without #)
            
        Returns:
            List of posts using the hashtag
        """
        posts = self.storage.get_all_posts()
        return [p for p in posts if hashtag in p.hashtags]
    
    def get_top_authors(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top authors by post count.
        
        Args:
            limit: Maximum number of authors to return
            
        Returns:
            List of (author, post_count) tuples
        """
        posts = self.storage.get_all_posts()
        author_counts = defaultdict(int)
        
        for post in posts:
            author_counts[post.author] += 1
        
        sorted_authors = sorted(
            author_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_authors[:limit]
    
    def get_top_hashtags(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top hashtags by usage count.
        
        Args:
            limit: Maximum number of hashtags to return
            
        Returns:
            List of (hashtag, usage_count) tuples
        """
        posts = self.storage.get_all_posts()
        hashtag_counts = defaultdict(int)
        
        for post in posts:
            for hashtag in post.hashtags:
                hashtag_counts[hashtag] += 1
        
        sorted_hashtags = sorted(
            hashtag_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_hashtags[:limit]
    
    def get_conversation_thread(self, post_id: str) -> List[Post]:
        """Get full conversation thread for a post.
        
        Args:
            post_id: Post ID
            
        Returns:
            List of posts in the thread, ordered chronologically
        """
        thread = []
        visited = set()
        
        # Walk up the reply chain to find root
        current_id = post_id
        while current_id and current_id not in visited:
            visited.add(current_id)
            post = self.storage.get_post(current_id)
            if not post:
                break
            thread.append(post)
            current_id = post.reply_to
        
        # Reverse to get chronological order (root first)
        thread.reverse()
        
        # Walk down from root to get all replies
        if thread:
            root_id = thread[0].id
            all_replies = self._get_all_replies(root_id)
            
            # Merge with existing thread
            thread_ids = {p.id for p in thread}
            for reply in all_replies:
                if reply.id not in thread_ids:
                    thread.append(reply)
        
        # Sort by created_at
        thread.sort(key=lambda p: p.created_at)
        
        return thread
    
    def _get_all_replies(self, post_id: str) -> List[Post]:
        """Recursively get all replies to a post."""
        all_posts = self.storage.get_all_posts()
        replies = [p for p in all_posts if p.reply_to == post_id]
        
        result = []
        for reply in replies:
            result.append(reply)
            result.extend(self._get_all_replies(reply.id))
        
        return result
