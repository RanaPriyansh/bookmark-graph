# bookmark-graph

A local CLI tool that turns X (Twitter) bookmark exports into knowledge graphs stored in SQLite.

Inspired by prior work like Graphify, this tool runs entirely on your machine with your own bookmark exports.

## What It Does

- **Ingest** X bookmark exports (JSONL or Markdown format)
- **Store** posts and relationships in a local SQLite database
- **Query** bookmarks by text content
- **Analyze** connections between posts, authors, and hashtags
- **Export** graphs in JSON, Mermaid, or Graphviz format

## Performance

Engineered for speed with bulk operations and proper indexing:
- **~95,000 posts/sec** insertion rate
- **~140,000 posts/sec** read rate
- Handles 10,000+ posts in under 200ms
- Optimized bulk inserts (no N+1 queries)
- Indexed foreign key lookups

## Installation

```bash
# Clone the repository
git clone https://github.com/RanaPriyansh/bookmark-graph.git
cd bookmark-graph

# Install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Run tests to verify installation
pytest

# Ingest your bookmark export
bookmark-graph ingest your-bookmarks.jsonl

# View statistics
bookmark-graph stats

# Search bookmarks
bookmark-graph query "machine learning"

# View post connections
bookmark-graph neighbors 1234567890

# Export as JSON
bookmark-graph export output.json --format json

# Export as Mermaid diagram
bookmark-graph export graph.mmd --format mermaid

# Export as Graphviz DOT
bookmark-graph export graph.dot --format graphviz
```

## Commands

- `ingest <file>` - Import bookmark export (auto-detects JSONL or Markdown)
- `stats` - Show graph statistics (posts, authors, hashtags, etc.)
- `query <text>` - Search posts by text content
- `neighbors <post-id>` - Show connected posts (replies, mentions, same author)
- `export <file>` - Export graph data (--format: json, mermaid, graphviz)

## Export File Formats

This tool expects X bookmark exports in one of two formats:

### JSONL Format

```jsonl
{"id": "1234567890", "text": "Post content", "author": "username", "created_at": "2024-01-01T00:00:00Z", "mentions": ["user1"], "hashtags": ["tag1"], "urls": ["https://example.com"], "reply_to": null}
```

### Markdown Format

```markdown
## Post 1234567890

**ID:** 1234567890
**Author:** username
**Date:** 2024-01-01T00:00:00Z

Post content with @mentions and #hashtags
```

## Storage

All data is stored in a local SQLite database (`bookmarks.db` by default). Specify a different database with `--db <path>`.

**Security:** Database paths are validated to prevent path traversal attacks. Paths containing `..` or targeting system directories like `/etc` or `/sys` are rejected.

## Requirements

- Python 3.8+
- No API keys needed
- No live internet connection required
- Works entirely with local export files

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=bookmark_graph

# Run CI locally (same as GitHub Actions)
pytest -v --cov=bookmark_graph --cov-report=term-missing
```

### Continuous Integration

GitHub Actions runs tests automatically on:
- Every push to `main` or feature branches
- All pull requests
- Python versions: 3.8, 3.9, 3.10, 3.11, 3.12

CI will **fail the build** if any test fails, ensuring code quality.

### Performance Benchmarks

Run benchmarks to measure performance:

```bash
python3 benchmark.py           # Quick benchmark with fixture
python3 benchmark_scale.py     # Scale test (100-10,000 posts)
```

## License

MIT License - see LICENSE file

## What This Is Not

- Not a hosted service or SaaS
- Not a live X API client
- Not a general-purpose CRM
- Only works with your own exported bookmark files
