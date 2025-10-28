"""Path-related helpers shared across Command Center scripts."""

from __future__ import annotations

from pathlib import Path


def slugify_relative(relative_path: Path) -> str:
    """Convert a repository-relative path into a slug suitable for filenames."""
    parts: list[str] = []
    for part in relative_path.parts:
        cleaned = []
        for ch in part:
            if ch.isalnum():
                cleaned.append(ch.lower())
            elif ch in {"-", "_"}:
                cleaned.append(ch)
            else:
                cleaned.append("-")
        slug = "".join(cleaned).strip("-_") or "segment"
        parts.append(slug)
    return "__".join(parts) or "root"
