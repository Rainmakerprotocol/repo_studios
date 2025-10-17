#!/usr/bin/env python
"""Markdown Anchor & Link Checker

Scans selected markdown files for:
  * Internal document anchors: [text](#anchor)
  * Cross-file relative links: [text](path/to/file.md#optional-anchor)

Validates that:
  * Target files exist
  * Target anchors exist (heading-derived slug)

Slug generation follows GitHub-style simplification (lowercase, spaces -> dashes,
strip non-alphanumeric except dashes) and collapses consecutive dashes.

Exit codes:
  0 - success, no issues
  1 - issues found (printed)

Usage:
  python scripts/check_markdown_anchors.py [--root .] [--glob docs/**/*.md]

Defaults choose a curated file set (README + docs/agents/*quickstart* + step5 plan).
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")  # capture link target


class Issue(NamedTuple):
    file: Path
    line: int
    kind: str
    target: str
    message: str


def slugify(raw: str) -> str:
    s = raw.strip().lower()
    # remove code spans/backticks
    s = re.sub(r"`+", "", s)
    # remove anything not alphanumeric/space/-
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def collect_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        anchors.add(slugify(m.group(2)))
    return anchors


def iter_files(patterns: Iterable[str], root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for pat in patterns:
        for path in root.glob(pat):
            if path.is_file() and path.suffix == ".md" and path not in seen:
                seen.add(path)
                yield path


def parse_links(text: str) -> Iterable[tuple[int, str]]:
    for idx, line in enumerate(text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            yield idx, m.group(1)


def check_file(path: Path, root: Path, anchors_cache: dict[Path, set[str]]) -> list[Issue]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, target in parse_links(text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue  # external
        if target.startswith("#"):
            # intra-file anchor
            anchor = target[1:]
            anchor_slug = slugify(anchor)
            anchors = anchors_cache.setdefault(path, collect_anchors(text))
            if anchor_slug not in anchors:
                issues.append(
                    Issue(
                        path,
                        line_no,
                        "anchor",
                        target,
                        f"Missing anchor slug '{anchor_slug}' in same file",
                    )
                )
            continue
        # file or file#anchor
        file_part, _, anchor_part = target.partition("#")
        # normalize relative path
        target_path = (path.parent / file_part).resolve()
        try:
            target_path.relative_to(root.resolve())
        except ValueError:
            # outside root; skip for safety
            continue
        if not target_path.exists():
            issues.append(Issue(path, line_no, "file", target, "Target file does not exist"))
            continue
        if anchor_part:
            tgt_text = target_path.read_text(encoding="utf-8", errors="replace")
            anchors = anchors_cache.setdefault(target_path, collect_anchors(tgt_text))
            slug = slugify(anchor_part)
            if slug not in anchors:
                issues.append(
                    Issue(
                        path,
                        line_no,
                        "anchor",
                        target,
                        f"Missing anchor slug '{slug}' in target file",
                    )
                )
    return issues


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Check markdown internal links & anchors")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--glob",
        action="append",
        help="Glob pattern (repeatable)",
        dest="globs",
    )
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    patterns = args.globs or [
        "README.md",
        "docs/agents/config_quickstart.md",
        "docs/agents/step5_agent_config_system.md",
    ]
    anchors_cache: dict[Path, set[str]] = {}
    all_issues: list[Issue] = []
    for md_file in iter_files(patterns, root):
        all_issues.extend(check_file(md_file, root, anchors_cache))
    if all_issues:
        logging.error("Markdown anchor/link issues detected (%d)", len(all_issues))
        for issue in all_issues:
            rel = issue.file.relative_to(root)
            logging.error(
                "%s:%d: [%s] %s -> %s",
                rel,
                issue.line,
                issue.kind,
                issue.target,
                issue.message,
            )
        return 1
    logging.info(
        "All checked markdown anchors OK (files: %s)",
        ", ".join(str(p.relative_to(root)) for p in anchors_cache),
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
