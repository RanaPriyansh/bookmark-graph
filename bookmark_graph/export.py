"""Export graph data in various formats."""

import json
from typing import Dict, List, TextIO
from pathlib import Path

from .models import Post
from .storage import Storage
from .graph import Graph


class Exporter:
    """Export graph data to various formats."""
    
    def __init__(self, storage: Storage):
        """Initialize exporter.
        
        Args:
            storage: Storage instance
        """
        self.storage = storage
        self.graph = Graph(storage)
    
    def export_json(self, output_path: Path):
        """Export graph as JSON.
        
        Args:
            output_path: Path to output file
        """
        posts = self.storage.get_all_posts()
        stats = self.storage.get_stats()
        
        data = {
            'stats': stats.to_dict(),
            'posts': [post.to_dict() for post in posts],
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export_mermaid(self, output_path: Path, max_nodes: int = 50):
        """Export graph as Mermaid diagram.
        
        Args:
            output_path: Path to output file
            max_nodes: Maximum number of nodes to include
        """
        posts = self.storage.get_all_posts()[:max_nodes]
        adjacency = self.graph.build_adjacency_list()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("graph TD\n")
            
            # Write nodes
            for post in posts:
                node_id = self._sanitize_id(post.id)
                label = self._truncate_text(post.text, 30)
                f.write(f'    {node_id}["{label}<br/>@{post.author}"]\\n')
            
            # Write edges
            post_ids = {p.id for p in posts}
            for post in posts:
                if post.id in adjacency:
                    for neighbor_id in adjacency[post.id]:
                        if neighbor_id in post_ids:
                            src = self._sanitize_id(post.id)
                            dst = self._sanitize_id(neighbor_id)
                            f.write(f'    {src} --> {dst}\\n')
    
    def export_graphviz(self, output_path: Path, max_nodes: int = 50):
        """Export graph as Graphviz DOT format.
        
        Args:
            output_path: Path to output file
            max_nodes: Maximum number of nodes to include
        """
        posts = self.storage.get_all_posts()[:max_nodes]
        adjacency = self.graph.build_adjacency_list()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('digraph BookmarkGraph {\\n')
            f.write('    node [shape=box, style=rounded];\\n')
            f.write('    rankdir=LR;\\n\\n')
            
            # Write nodes
            for post in posts:
                node_id = self._sanitize_id(post.id)
                label = self._escape_dot(self._truncate_text(post.text, 40))
                author = self._escape_dot(post.author)
                f.write(f'    {node_id} [label="{label}\\\\n@{author}"];\\n')
            
            # Write edges
            post_ids = {p.id for p in posts}
            edges_written = set()
            
            for post in posts:
                if post.id in adjacency:
                    for neighbor_id in adjacency[post.id]:
                        if neighbor_id in post_ids:
                            src = self._sanitize_id(post.id)
                            dst = self._sanitize_id(neighbor_id)
                            edge = (src, dst)
                            
                            # Avoid duplicate edges
                            if edge not in edges_written:
                                f.write(f'    {src} -> {dst};\\n')
                                edges_written.add(edge)
            
            f.write('}\\n')
    
    def export_conversation_mermaid(self, post_id: str, output_path: Path):
        """Export a conversation thread as Mermaid diagram.
        
        Args:
            post_id: Root post ID
            output_path: Path to output file
        """
        thread = self.graph.get_conversation_thread(post_id)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("graph TD\n")
            
            for post in thread:
                node_id = self._sanitize_id(post.id)
                label = self._truncate_text(post.text, 30)
                f.write(f'    {node_id}["{label}<br/>@{post.author}"]\\n')
            
            for post in thread:
                if post.reply_to:
                    src = self._sanitize_id(post.reply_to)
                    dst = self._sanitize_id(post.id)
                    f.write(f'    {src} --> {dst}\\n')
    
    @staticmethod
    def _sanitize_id(post_id: str) -> str:
        """Sanitize post ID for use in diagrams."""
        # Replace non-alphanumeric characters with underscores
        return 'post_' + ''.join(c if c.isalnum() else '_' for c in post_id)
    
    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """Truncate text to maximum length."""
        text = text.replace('\\n', ' ').strip()
        if len(text) > max_length:
            return text[:max_length-3] + '...'
        return text
    
    @staticmethod
    def _escape_dot(text: str) -> str:
        """Escape special characters for DOT format."""
        return text.replace('"', '\\\\"').replace('\\n', '\\\\n')
