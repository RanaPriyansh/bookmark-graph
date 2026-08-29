"""Tests for CLI path validation."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from bookmark_graph.cli import validate_db_path


def test_validate_db_path_simple():
    """Test validation of simple database path."""
    path = validate_db_path('test.db')
    assert path.name == 'test.db'


def test_validate_db_path_with_directory():
    """Test validation of path with directory."""
    path = validate_db_path('data/test.db')
    assert 'test.db' in str(path)


def test_validate_db_path_rejects_traversal():
    """Test that path traversal is rejected."""
    with pytest.raises(Exception):
        validate_db_path('../../../etc/passwd')


def test_validate_db_path_rejects_etc():
    """Test that /etc paths are rejected."""
    with pytest.raises(Exception):
        validate_db_path('/etc/test.db')


def test_validate_db_path_rejects_sys():
    """Test that /sys paths are rejected."""
    with pytest.raises(Exception):
        validate_db_path('/sys/test.db')


def test_validate_db_path_absolute_safe(tmp_path):
    """Test that safe absolute paths are allowed."""
    db_path = tmp_path / 'safe.db'
    path = validate_db_path(str(db_path))
    assert path == db_path.resolve()
