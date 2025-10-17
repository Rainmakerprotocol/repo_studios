#!/usr/bin/env python
"""Identify potential standards directives present in source markdown files but absent from the index.

Heuristic (phase 1 minimal):
  - Candidate lines begin with one of: '-', '*', numerical list '1.' style, or uppercase imperative verbs.
  - We look for imperative-like tokens at start: (avoid|ensure|prefer|use|never|do not|limit|prohibit|enforce|document|pin|avoid) case-insensitive.
  - Exclude lines already mapped to a rule (matching summary substring or rule id anchor pattern).

Output:
  - Human summary to stdout listing per-source file gaps
  - Optional JSON via --json for machine consumption with fields:
        { "sources": { path: [ {"line": N, "text": original_line } ... ] }, "total_candidates": X }

Exit codes:
  0 success (runs; gaps may or may not exist)
  2 parse / IO error

Limitations (documented for future refinement):
  - Does not parse markdown tables yet.
  - Does not deduplicate semantically similar lines across files.
  - Very small false-positive filter; rely on manual triage or future semantic scoring.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "repo_standards_index.yaml"
CATEGORIES_FILE = ROOT / ".repo_studios" / "standards_categories.yaml"

IMP_VERBS = re.compile(
    r"^(?:[-*]\s*|\d+\.\s*)?(?:avoid|ensure|prefer|use|never|do not|limit|prohibit|enforce|document|pin)\b",
    re.IGNORECASE,
)
STRIP_PREFIX = re.compile(r"^[-*]\s*|^\d+\.\s*")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        logging.error("index file missing: %s", INDEX_PATH)
        sys.exit(2)
    try:
        return yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # pragma: no cover
        logging.exception("failed to parse index: %s", exc)
        sys.exit(2)


def load_sources() -> list[Path]:
    if not CATEGORIES_FILE.exists():
        logging.error("categories file missing: %s", CATEGORIES_FILE)
        sys.exit(2)
    data = yaml.safe_load(CATEGORIES_FILE.read_text(encoding="utf-8")) or {}
    out: list[Path] = []
    for src in data.get("sources", []) or []:
        p = ROOT / src.get("path", "")
        if p.exists():
            out.append(p)
        else:
            logging.warning("source file listed but missing: %s", p)
    return out


def build_existing_tokens(index: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for r in index.get("rules", []) or []:
        # Lowercased words from summary to reduce false positives
        summary = r.get("summary", "").lower()
        for w in re.findall(r"[a-zA-Z]{4,}", summary):
            tokens.add(w)
        rid = r.get("id")
        if rid:
            tokens.add(rid.lower())
    return tokens


def scan_file(path: Path, existing_tokens: set[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # pragma: no cover
        logging.warning("failed to read %s: %s", path, exc)
        return results
    for idx, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if not IMP_VERBS.match(text):
            continue
        core = STRIP_PREFIX.sub("", text).lower()
        # Simple suppression heuristic: if more than half the words already appear in existing tokens
        words = [w for w in re.findall(r"[a-zA-Z]{4,}", core) if w]
        if words and sum(1 for w in words if w in existing_tokens) / len(words) > 0.6:
            continue
        results.append({"line": idx, "text": raw})
    return results


def run_gap_detection() -> dict[str, Any]:
    index = load_index()
    existing_tokens = build_existing_tokens(index)
    sources = load_sources()
    gaps: dict[str, list[dict[str, Any]]] = {}
    for src in sources:
        cands = scan_file(src, existing_tokens)
        if cands:
            gaps[str(src.relative_to(ROOT))] = cands
    total = sum(len(v) for v in gaps.values())
    return {"sources": gaps, "total_candidates": total}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="standards_index_gap",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__,
    )
    p.add_argument("--json", dest="json_out", help="Write JSON report to this path")
    p.add_argument(
        "--max", dest="max_show", type=int, default=8, help="Max candidates to show per file"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report = run_gap_detection()
    if not report["sources"]:
        logging.info("No candidate gaps detected")
    else:
        for path, items in sorted(report["sources"].items()):
            logging.info("%s: %d candidates", path, len(items))
            for item in items[: args.max_show]:
                sys.stdout.write(f"  L{item['line']:>4} | {item['text'].strip()}\n")
            if len(items) > args.max_show:
                sys.stdout.write(f"  ... (+{len(items) - args.max_show} more)\n")
        logging.info("Total candidate directives: %d", report["total_candidates"])
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
