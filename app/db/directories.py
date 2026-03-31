"""Filesystem helpers for local runtime directories."""

from pathlib import Path


def ensure_runtime_directories(*directories: Path) -> None:
    """Ensure required local runtime directories exist."""
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
