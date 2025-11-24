"""Write Mermaid definitions to the viewer cache for debugging."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_CACHE_NAME = "debug_preview"
DEFAULT_TTL_HOURS = 24
DEFAULT_MAX_FILES = 5


@dataclass(frozen=True)
class CachePolicy:
    ttl: timedelta
    max_files: int


DEFAULT_TTL_HOURS = 24
DEFAULT_MAX_FILES = 5


def sanitize_name(value: str | None) -> str:
    """Convert arbitrary identifiers into filesystem-safe names."""
    if not value:
        return DEFAULT_CACHE_NAME
    sanitized = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")
    return sanitized or DEFAULT_CACHE_NAME


def ensure_cache_directory() -> Path:
    """Create the cache directory when missing and return the path."""
    CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    return CACHE_DIRECTORY


def read_definition(source: Path | None) -> str:
    """Read a Mermaid definition from a file or stdin."""
    if source is not None:
        return source.read_text(encoding="utf-8")
    data = sys.stdin.read()
    return data


def write_definition(definition: str, name: str) -> Path:
    """Write the Mermaid definition to the cache directory."""
    cache_dir = ensure_cache_directory()
    target = cache_dir / f"{sanitize_name(name)}.mmd"
    target.write_text(definition, encoding="utf-8")
    return target


def list_cached_files(extension: str = ".mmd") -> list[Path]:
    cache_dir = ensure_cache_directory()
    return sorted(cache_dir.glob(f"*{extension}"), key=lambda path: path.stat().st_mtime)


def evict_stale_files(policy: CachePolicy) -> list[Path]:
    """Remove cache files older than the TTL or exceeding the max file count."""
    removed: list[Path] = []
    now = datetime.utcnow()
    ttl_cutoff = now - policy.ttl

    for path in list_cached_files():
        modified = datetime.utcfromtimestamp(path.stat().st_mtime)
        if modified < ttl_cutoff:
            path.unlink(missing_ok=True)
            removed.append(path)

    remaining = [path for path in list_cached_files() if path not in removed]
    while len(remaining) > policy.max_files:
        victim = remaining.pop(0)
        victim.unlink(missing_ok=True)
        removed.append(victim)

    return removed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Mermaid definitions into the viewer cache for debugging.")
    parser.add_argument("--name", default=DEFAULT_CACHE_NAME, help="Cache file stem to use (default: debug_preview).")
    parser.add_argument("--source", type=Path, default=None, help="Optional path to a file containing the definition.")
    parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO).")
    parser.add_argument(
        "--ttl-hours",
        type=float,
        default=DEFAULT_TTL_HOURS,
        help="Evict cache files older than this many hours (default: 24).",
    )
    parser.add_argument(
        "--max-files", type=int, default=DEFAULT_MAX_FILES, help="Maximum Mermaid cache files to retain (default: 5)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level.upper(), format="%(levelname)s %(message)s")

    definition = read_definition(args.source)
    if not definition.strip():
        parser.error("Mermaid definition input required via --source or stdin.")

    policy = CachePolicy(ttl=timedelta(hours=max(args.ttl_hours, 0)), max_files=max(args.max_files, 1))
    removed = evict_stale_files(policy)
    for path in removed:
        logging.debug("Evicted Mermaid cache %s", path)

    target = write_definition(definition, args.name)
    logging.info("Cached Mermaid definition at %s", target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
