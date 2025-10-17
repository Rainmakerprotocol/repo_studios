#!/usr/bin/env python3
"""Anchor Inventory Tool

Generates an inventory of top-level (H1/H2) markdown heading slugs under docs/.
Outputs:
 - STDOUT table (slug, count, file_count)
 - Optional JSON baseline file with summary metrics + per-slug stats.

Usage:
  python scripts/anchor_inventory.py [--json-out tests/docs/anchor_slug_baseline.json] [--allow-file tests/docs/anchor_allow_generic.txt]

Exit code 0 on success.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_slug_cleanup_re = re


def slugify(raw: str) -> str:
    s = raw.strip().lower()
    s = _slug_cleanup_re.sub(r"`+", "", s)
    s = _slug_cleanup_re.sub(r"[^a-z0-9\- ]", "", s)
    s = _slug_cleanup_re.sub(r"\s+", "-", s)
    s = _slug_cleanup_re.sub(r"-+", "-", s)
    return s.strip("-")


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for md in root.rglob("*.md"):
        if any(p in md.parts for p in ("coverage_history",)):
            continue
        yield md


@dataclass
class SlugStat:
    slug: str
    count: int
    file_count: int
    files: list[str]


GENERIC_ALLOWED = {"overview", "introduction", "faq", "notes"}


def collect(root: Path) -> dict[str, SlugStat]:
    slug_locations: dict[str, list[str]] = defaultdict(list)
    for md in iter_markdown_files(root):
        text = md.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            m = HEADING_RE.match(line)
            if not m:
                continue
            level = len(m.group(1))
            if level > 2:
                continue
            slug = slugify(m.group(2))
            slug_locations[slug].append(f"{md}:{lineno}")
    stats: dict[str, SlugStat] = {}
    for slug, locs in slug_locations.items():
        files = sorted({loc.split(":")[0] for loc in locs})
        stats[slug] = SlugStat(slug=slug, count=len(locs), file_count=len(files), files=files)
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--allow-file",
        type=Path,
        help="Optional file containing generic allowlist (one slug per line)",
    )
    parser.add_argument(
        "--test-file",
        type=Path,
        help="Path to test_global_anchors.py to extract current ALLOWED size for baseline",
    )
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def extract_test_allowlist_size(test_file: Path) -> int | None:
    if not test_file or not test_file.exists():  # type: ignore[arg-type]
        return None
    text = test_file.read_text(encoding="utf-8", errors="replace")
    allowed_block: list[str] = []
    capture = False
    for line in text.splitlines():
        if line.strip().startswith("ALLOWED = {"):
            capture = True
            continue
        if capture:
            if line.strip().startswith("}"):
                break
            m = re.search(r"\"([^\"]*)\"", line)
            if m:
                allowed_block.append(m.group(1))
    return len(allowed_block) if allowed_block else None


def build_summary(
    stats: dict[str, SlugStat],
    cross_file_dupes: dict[str, SlugStat],
    allow_set: set[str],
    allowlist_size: int | None,
) -> dict[str, int | None]:
    return {
        "total_slugs": len(stats),
        "cross_file_duplicates": len(cross_file_dupes),
        "generic_allow_size": len(allow_set),
        "allowlist_size": allowlist_size,
    }


def emit_report(
    log: logging.Logger, stats: dict[str, SlugStat], summary: dict[str, int | None]
) -> None:
    header = f"{'SLUG':40} {'CNT':>4} {'FILES':>5}"
    log.info(header)
    log.info("-" * len(header))
    for st in sorted(stats.values(), key=lambda s: (s.file_count, s.count), reverse=True):
        log.info(f"{st.slug[:40]:40} {st.count:4d} {st.file_count:5d}")
    log.info("Summary:")
    for k, v in summary.items():
        log.info(f"  {k}: {v}")


def maybe_write_json(
    path: Path | None,
    summary: dict[str, int | None],
    cross_file_dupes: dict[str, SlugStat],
    allow_set: set[str],
    allowlist_size: int | None,
    log: logging.Logger,
) -> None:
    if not path:
        return
    payload = {
        "schema_version": 1,
        "summary": summary,
        "cross_file_duplicates": {k: asdict(v) for k, v in cross_file_dupes.items()},
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "allow_generic": sorted(allow_set),
        "allowlist_size": allowlist_size,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.info("Wrote baseline JSON: %s", path)


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )
    log = logging.getLogger("anchor_inventory")
    docs_root = Path("docs")
    if not docs_root.exists():
        raise SystemExit("docs directory not found")
    stats = collect(docs_root)
    allow_set = set(GENERIC_ALLOWED)
    if args.allow_file and args.allow_file.exists():
        allow_set.update(s.strip() for s in args.allow_file.read_text().splitlines() if s.strip())
    cross_file_dupes = {
        s: st for s, st in stats.items() if st.file_count > 1 and s not in allow_set
    }
    allowlist_size = extract_test_allowlist_size(args.test_file) if args.test_file else None
    summary = build_summary(stats, cross_file_dupes, allow_set, allowlist_size)
    emit_report(log, stats, summary)
    maybe_write_json(args.json_out, summary, cross_file_dupes, allow_set, allowlist_size, log)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
