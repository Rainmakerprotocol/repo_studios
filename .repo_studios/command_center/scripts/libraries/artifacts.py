"""Artifact lifecycle helpers for Command Center scripts."""

from __future__ import annotations

from pathlib import Path


def copy_latest_artifact(src: Path, dest: Path) -> None:
    """Mirror ``src`` to ``dest`` using a hard link when possible."""
    try:
        if dest.exists():
            dest.unlink()
        dest.hardlink_to(src)
    except OSError:
        dest.write_bytes(src.read_bytes())
