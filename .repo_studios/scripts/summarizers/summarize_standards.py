#!/usr/bin/env python
"""Print a concise summary of the current standards index / pending file.

Usage:
    python scripts/standards_summary.py [--label grow|sync]

Environment (optional):
    INDEX_PATH   Path to index YAML (default: .repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml)
    PENDING_PATH Path to pending YAML (default: .repo_studios/scripts/repo_standards_pending.yaml)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

DEFAULT_INDEX_PATH = Path(
    ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml"
)
LEGACY_INDEX_PATH = Path(".repo_studios/scripts/repo_standards_index.yaml")
DEFAULT_PENDING_PATH = Path(".repo_studios/scripts/repo_standards_pending.yaml")

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover - simple util
    logging.warning("[standards-summary] missing PyYAML: %s", exc)
    sys.exit(0)


def _resolve_path(path: Path) -> Path:
    """Return an absolute path for the supplied value."""

    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def _resolve_index_path(label: str, candidate: Path) -> Path:
    """Return the index path, falling back to the legacy snapshot when needed."""

    absolute_candidate = _resolve_path(candidate)
    if absolute_candidate.exists():
        return absolute_candidate

    legacy_candidate = _resolve_path(LEGACY_INDEX_PATH)
    if legacy_candidate.exists():
        logging.warning(
            "[standards-%s] index missing at %s; falling back to legacy snapshot %s",
            label,
            absolute_candidate,
            legacy_candidate,
        )
        return legacy_candidate

    return absolute_candidate


def summarize(label: str, index_path: Path, pending_path: Path) -> int:
    """Summarize the current standards index and optional pending file."""
    if not index_path.exists():
        logging.warning("[standards-%s] index missing (%s)", label, index_path)
        return 0
    try:
        data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover
        logging.exception("[standards-%s] failed to load index: %s", label, exc)
        return 1

    extraction = (data.get("metadata", {}) or {}).get("extraction", {}) or {}
    rules = data.get("rules", []) or []
    logging.info(
        "[standards-%s] rules=%d extracted_count=%s auto_accept=%s pending_file=%s",
        label,
        len(rules),
        extraction.get("extracted_count"),
        extraction.get("auto_accept"),
        extraction.get("pending_file"),
    )

    md_ids = [r.get("id") for r in rules if isinstance(r, dict) and str(r.get("id", "")).startswith("markdown-")]
    if md_ids:
        md_ids_sorted = sorted(set(md_ids))
        logging.info(
            "[standards-%s] markdown-rule-count=%d sample=%s",
            label,
            len(md_ids_sorted),
            ", ".join(md_ids_sorted[:5]),
        )

    if extraction.get("pending_file") and pending_path.exists():
        try:
            pending_lines = sum(1 for _ in pending_path.open("r", encoding="utf-8"))
            logging.info("[standards-%s] pending_lines=%d", label, pending_lines)
        except Exception:  # pragma: no cover
            pass
    return 0


def main() -> int:  # pragma: no cover - tiny wrapper
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="summary", help="label for log prefix (grow|sync|summary)")
    args = parser.parse_args()
    logging.basicConfig(level=os.environ.get("STANDARDS_SUMMARY_LOG_LEVEL", "INFO"))
    index_path_env = Path(os.environ.get("INDEX_PATH", str(DEFAULT_INDEX_PATH)))
    pending_path_env = Path(os.environ.get("PENDING_PATH", str(DEFAULT_PENDING_PATH)))
    index_path = _resolve_index_path(args.label, index_path_env)
    pending_path = _resolve_path(pending_path_env)
    return summarize(args.label, index_path, pending_path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
