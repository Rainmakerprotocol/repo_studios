#!/usr/bin/env python3
"""Anchor Drift Checker

Scans the repository for markdown links referencing legacy orchestrator metrics anchors and
verifies that each referenced anchor has a corresponding stub section in
`docs/api/metrics_orchestrator.md`.

Exit codes:
  0: All references satisfied (no drift)
  1: Missing anchor stub(s) detected
  2: Internal error (unexpected exception)

Usage:
  python scripts/check_doc_anchors.py [--write-report REPORT_PATH]

Behavior:
  * Collect all markdown files (*.md) excluding vendor/ and .repo_studios/.
  * Find links matching pattern: metrics_orchestrator.md#<anchor>
  * Parse `docs/api/metrics_orchestrator.md` for headings and legacy anchor stubs.
  * Report any referenced anchors not present in stub set.
  * Optionally writes a JSON report with fields: {"checked": int, "unique_anchors": [...],
    "missing": [...]}.

Design choices:
  * Simple regex parsing (performance sufficient for current repo size).
  * Headings converted to GitHub-style anchors: lowercase, spaces -> '-', remove punctuation
    (basic subset aligned with existing anchors we created).
  * Legacy stub detection: headings under "Legacy Anchor Compatibility" section (## or ###).

Limitations:
  * Does not validate external/HTTP links.
  * Assumes anchor generation scheme remains stable; if rules change, update `_normalize_anchor`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path

RE_MD_LINK = re.compile(r"metrics_orchestrator\.md#([a-zA-Z0-9\-._]+)")
RE_HEADING = re.compile(r"^(#{2,6})\s+(.*)$")

ROOT = Path(__file__).resolve().parent.parent
LEGACY_FILE = ROOT / "docs/api/metrics_orchestrator.md"


def _normalize_anchor(text: str) -> str:
    # Basic GitHub-style anchor normalization
    t = text.strip().lower()
    # remove backticks
    t = t.replace("`", "")
    # replace spaces with hyphens
    t = re.sub(r"\s+", "-", t)
    # drop chars not alnum, dash, underscore, dot
    t = re.sub(r"[^a-z0-9._-]", "", t)
    return t


def collect_referenced_anchors(paths: Iterable[Path]) -> set[str]:
    anchors: set[str] = set()
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in RE_MD_LINK.finditer(text):
            anchors.add(m.group(1).lower())
    return anchors


def collect_legacy_stub_anchors() -> set[str]:
    if not LEGACY_FILE.exists():
        return set()
    anchors: set[str] = set()
    try:
        lines = LEGACY_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return set()

    in_legacy_block = False
    for line in lines:
        if line.strip().lower().startswith("## legacy anchor compatibility"):
            in_legacy_block = True
            continue
        if (
            in_legacy_block
            and line.startswith("## ")
            and not line.lower().startswith("## legacy anchor compatibility")
        ):
            # Exited legacy section
            in_legacy_block = False
        if not in_legacy_block:
            continue
        m = RE_HEADING.match(line)
        if m:
            heading_text = m.group(2).strip()
            anchors.add(_normalize_anchor(heading_text))
    return anchors


def iter_markdown_files() -> Iterable[Path]:
    for path in ROOT.rglob("*.md"):
        rel = path.relative_to(ROOT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if rel.parts[0] in {"vendor", "external"}:
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check orchestrator metrics legacy anchor drift")
    parser.add_argument("--write-report", dest="report", help="Optional JSON report output path")
    args = parser.parse_args()

    md_files = list(iter_markdown_files())
    referenced = collect_referenced_anchors(md_files)
    legacy = collect_legacy_stub_anchors()

    missing = sorted(a for a in referenced if a not in legacy)

    report = {
        "checked": len(md_files),
        "unique_anchors": sorted(referenced),
        "legacy_stubs": sorted(legacy),
        "missing": missing,
    }

    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if missing:
        sys.stderr.write("Missing legacy anchor stub(s): " + ", ".join(missing) + "\n")
        return 1

    sys.stdout.write(
        "Anchor drift check OK (" + str(len(referenced)) + " referenced, none missing)\n"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Internal error: {exc}\n")
        raise SystemExit(2) from None
