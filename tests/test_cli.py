"""Tests for CLI commands."""

import pytest
from pathlib import Path
from click.testing import CliRunner

from bookmark_graph.cli import main
from bookmark_graph.storage import Storage


FIXTURES_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'bookmark-graph' in result.output


def test_cli_version(runner):
    """Test CLI version command."""
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert '0.1.0' in result.output


def test_ingest_jsonl(runner, tmp_path):
    """Test ingesting JSONL file."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    
    result = runner.invoke(main, [
        'ingest',
        str(fixture),
        '--db', str(db_path)
    ])
    
    assert result.exit_code == 0
    assert 'Successfully ingested' in result.output
    assert db_path.exists()


def test_ingest_markdown(runner, tmp_path):
    """Test ingesting Markdown file."""
    fixture = FIXTURES_DIR / 'bookmarks.md'
    db_path = tmp_path / 'test.db'
    
    result = runner.invoke(main, [
        'ingest',
        str(fixture),
        '--db', str(db_path)
    ])
    
    assert result.exit_code == 0
    assert 'Successfully ingested' in result.output


def test_ingest_missing_file(runner, tmp_path):
    """Test ingesting non-existent file."""
    db_path = tmp_path / 'test.db'
    
    result = runner.invoke(main, [
        'ingest',
        '/nonexistent/file.jsonl',
        '--db', str(db_path)
    ])
    
    assert result.exit_code != 0


def test_stats_without_db(runner, tmp_path):
    """Test stats command without database."""
    db_path = tmp_path / 'nonexistent.db'
    
    result = runner.invoke(main, [
        'stats',
        '--db', str(db_path)
    ])
    
    assert result.exit_code != 0
    assert 'Database not found' in result.output


def test_stats_with_db(runner, tmp_path):
    """Test stats command with existing database."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    
    # First ingest data
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    # Then run stats
    result = runner.invoke(main, ['stats', '--db', str(db_path)])
    
    assert result.exit_code == 0
    assert 'Total Posts' in result.output


def test_query(runner, tmp_path):
    """Test query command."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    result = runner.invoke(main, [
        'query',
        'coffee',
        '--db', str(db_path)
    ])
    
    assert result.exit_code == 0
    assert 'Found' in result.output


def test_query_without_db(runner, tmp_path):
    """Test query without database."""
    db_path = tmp_path / 'nonexistent.db'
    
    result = runner.invoke(main, [
        'query',
        'test',
        '--db', str(db_path)
    ])
    
    assert result.exit_code != 0


def test_neighbors(runner, tmp_path):
    """Test neighbors command."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    result = runner.invoke(main, [
        'neighbors',
        '1001',
        '--db', str(db_path)
    ])
    
    assert result.exit_code == 0
    assert 'Original Post' in result.output


def test_neighbors_missing_post(runner, tmp_path):
    """Test neighbors command with missing post."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    result = runner.invoke(main, [
        'neighbors',
        '9999',
        '--db', str(db_path)
    ])
    
    assert result.exit_code != 0


def test_export_json(runner, tmp_path):
    """Test export as JSON."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    output_path = tmp_path / 'export.json'
    
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    result = runner.invoke(main, [
        'export',
        str(output_path),
        '--db', str(db_path),
        '--format', 'json'
    ])
    
    assert result.exit_code == 0
    assert output_path.exists()


def test_export_mermaid(runner, tmp_path):
    """Test export as Mermaid."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    output_path = tmp_path / 'export.mmd'
    
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    result = runner.invoke(main, [
        'export',
        str(output_path),
        '--db', str(db_path),
        '--format', 'mermaid'
    ])
    
    assert result.exit_code == 0
    assert output_path.exists()


def test_export_graphviz(runner, tmp_path):
    """Test export as Graphviz."""
    fixture = FIXTURES_DIR / 'bookmarks.jsonl'
    db_path = tmp_path / 'test.db'
    output_path = tmp_path / 'export.dot'
    
    runner.invoke(main, ['ingest', str(fixture), '--db', str(db_path)])
    
    result = runner.invoke(main, [
        'export',
        str(output_path),
        '--db', str(db_path),
        '--format', 'graphviz'
    ])
    
    assert result.exit_code == 0
    assert output_path.exists()


def test_export_without_db(runner, tmp_path):
    """Test export without database."""
    db_path = tmp_path / 'nonexistent.db'
    output_path = tmp_path / 'export.json'
    
    result = runner.invoke(main, [
        'export',
        str(output_path),
        '--db', str(db_path)
    ])
    
    assert result.exit_code != 0
