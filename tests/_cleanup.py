"""Test helper utilities for cleaning up temporary directories."""

from __future__ import annotations

from pathlib import Path


def cleanup_directory(path: Path) -> None:
    """Recursively remove all files and directories under ``path``.

    Files are removed with :meth:`Path.unlink`, while directories are removed
    with :meth:`Path.rmdir`. The helper is careful to walk nested structures so
    that temporary directory trees are fully deleted without raising.
    """

    if not path.exists():
        return

    for child in path.iterdir():
        if child.is_dir():
            cleanup_directory(child)
        else:
            child.unlink()

    path.rmdir()
