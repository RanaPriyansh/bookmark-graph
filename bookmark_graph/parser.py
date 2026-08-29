"""Parser for X bookmark exports (JSONL and Markdown)."""

import json
import re
from pathlib import Path
from typing import List, Iterator

from .models import Post


class ParserError(Exception):
    """Raised when parsing fails."""
    pass


def parse_jsonl(file_path: Path) -> List[Post]:
    """Parse JSONL bookmark export file.
    
    Args:
        file_path: Path to JSONL file
        
    Returns:
        List of Post objects
        
    Raises:
        ParserError: If file is malformed or invalid
    """
    posts = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    post = _parse_json_post(data, line_num)
                    posts.append(post)
                except json.JSONDecodeError as e:
                    raise ParserError(f"Invalid JSON on line {line_num}: {e}")
                except (KeyError, TypeError) as e:
                    raise ParserError(f"Invalid post structure on line {line_num}: {e}")
    except FileNotFoundError:
        raise ParserError(f"File not found: {file_path}")
    except Exception as e:
        raise ParserError(f"Error reading file: {e}")
    
    return posts


def parse_markdown(file_path: Path) -> List[Post]:
    """Parse Markdown bookmark export file.
    
    Args:
        file_path: Path to Markdown file
        
    Returns:
        List of Post objects
        
    Raises:
        ParserError: If file is malformed or invalid
    """
    posts = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into post blocks - look for patterns like "## Post 1234567890"
        # or headers with post IDs
        post_blocks = _split_markdown_posts(content)
        
        for block_num, block in enumerate(post_blocks, 1):
            try:
                post = _parse_markdown_post(block, block_num)
                if post:
                    posts.append(post)
            except Exception as e:
                raise ParserError(f"Error parsing post block {block_num}: {e}")
    except FileNotFoundError:
        raise ParserError(f"File not found: {file_path}")
    except Exception as e:
        raise ParserError(f"Error reading file: {e}")
    
    return posts


def _parse_json_post(data: dict, line_num: int) -> Post:
    """Parse a single post from JSON data."""
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")
    
    required_fields = ['id', 'text', 'author', 'created_at']
    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing required field: {field}")
    
    return Post(
        id=str(data['id']),
        text=data['text'],
        author=data['author'],
        created_at=data['created_at'],
        url=data.get('url'),
        mentions=data.get('mentions', []),
        hashtags=data.get('hashtags', []),
        urls=data.get('urls', []),
        reply_to=data.get('reply_to'),
    )


def _split_markdown_posts(content: str) -> List[str]:
    """Split markdown content into individual post blocks."""
    # Look for post separators (headers with "Post" or "---")
    # This is a simple heuristic - adjust based on actual export format
    
    # Try splitting by horizontal rules
    if '\n---\n' in content or '\n---' in content:
        blocks = re.split(r'\n---+\n?', content)
        return [b.strip() for b in blocks if b.strip()]
    
    # Try splitting by headers
    header_pattern = r'(?:^|\n)#{1,3}\s+(?:Post|Tweet)\s+\d+'
    if re.search(header_pattern, content, re.MULTILINE | re.IGNORECASE):
        blocks = re.split(header_pattern, content, flags=re.MULTILINE | re.IGNORECASE)
        return [b.strip() for b in blocks if b.strip()]
    
    # If no clear separators, treat as single block
    return [content.strip()] if content.strip() else []


def _parse_markdown_post(block: str, block_num: int) -> Post:
    """Parse a single post from markdown block."""
    lines = block.strip().split('\n')
    
    # Extract metadata and text
    post_id = None
    text = []
    author = None
    created_at = None
    url = None
    mentions = []
    hashtags = []
    urls = []
    reply_to = None
    
    for line in lines:
        line = line.strip()
        
        # Try to extract structured metadata
        if line.startswith('**ID:**') or line.startswith('ID:'):
            post_id = re.sub(r'^(?:\*\*)?ID:(?:\*\*)?\s*', '', line).strip()
        elif line.startswith('**Author:**') or line.startswith('Author:'):
            author = re.sub(r'^(?:\*\*)?Author:(?:\*\*)?\s*@?', '', line).strip()
        elif line.startswith('**Date:**') or line.startswith('Date:'):
            created_at = re.sub(r'^(?:\*\*)?Date:(?:\*\*)?\s*', '', line).strip()
        elif line.startswith('**URL:**') or line.startswith('URL:'):
            url = re.sub(r'^(?:\*\*)?URL:(?:\*\*)?\s*', '', line).strip()
        elif line.startswith('**Reply to:**') or line.startswith('Reply to:'):
            reply_to = re.sub(r'^(?:\*\*)?Reply to:(?:\*\*)?\s*', '', line).strip()
        elif line and not line.startswith('#') and not line.startswith('**') and not line.startswith('-'):
            text.append(line)
    
    # Extract entities from text
    full_text = ' '.join(text)
    
    if not post_id or not full_text:
        return None
    
    # Extract @mentions
    mentions = list(set(re.findall(r'@(\w+)', full_text)))
    
    # Extract #hashtags
    hashtags = list(set(re.findall(r'#(\w+)', full_text)))
    
    # Extract URLs
    url_pattern = r'https?://[^\s)]+'
    urls = list(set(re.findall(url_pattern, full_text)))
    
    # Default author and date if not found
    if not author:
        author = 'unknown'
    if not created_at:
        created_at = '2020-01-01T00:00:00Z'
    
    return Post(
        id=post_id,
        text=full_text,
        author=author,
        created_at=created_at,
        url=url,
        mentions=mentions,
        hashtags=hashtags,
        urls=urls,
        reply_to=reply_to,
    )


def detect_format(file_path: Path) -> str:
    """Detect file format (jsonl or markdown).
    
    Args:
        file_path: Path to file
        
    Returns:
        'jsonl' or 'markdown'
    """
    suffix = file_path.suffix.lower()
    
    if suffix in ['.jsonl', '.json']:
        return 'jsonl'
    elif suffix in ['.md', '.markdown']:
        return 'markdown'
    
    # Try to detect by content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith('{'):
                return 'jsonl'
            elif first_line.startswith('#'):
                return 'markdown'
    except Exception:
        pass
    
    return 'markdown'


def parse_file(file_path: Path) -> List[Post]:
    """Parse bookmark export file, auto-detecting format.
    
    Args:
        file_path: Path to export file
        
    Returns:
        List of Post objects
        
    Raises:
        ParserError: If parsing fails
    """
    file_path = Path(file_path)
    format_type = detect_format(file_path)
    
    if format_type == 'jsonl':
        return parse_jsonl(file_path)
    else:
        return parse_markdown(file_path)
