#!/usr/bin/env python3
"""Anchor Inventory Tool

Generates an inventory of top-level (H1/H2) markdown heading slugs under the
docs tree and emits machine + human readable reports.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/anchor_inventory_reports/`
        - `anchor_inventory-<timestamp>/report.json`
        - `anchor_inventory-<timestamp>/report.md`
        - `anchor_inventory-<timestamp>/slugs.tsv`
        - `latest_report.(json|md|tsv)` hard links or file copies for quick access

The JSON payload includes summary counts, allowlisted generics, and a full
listing of slugs/duplicates. The markdown summary highlights the top duplicate
slugs for fast triage.

Usage:
    python scripts/producers/generate_anchor_inventory.py \
            [--docs-root docs] \
            [--output-dir .repo_studios/reports/producer_reports/anchor_inventory_reports] \
            [--allow-file tests/docs/anchor_allow_generic.txt] \
            [--test-file tests/docs/test_global_anchors.py] \
            [--timestamp 2024-01-01T00:00:00] \
            [--artifacts-to-keep 10]

Exit code 0 on success.
"""

import argparse
import json
import logging
import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/anchor_inventory_reports"
)
RUN_PREFIX = "anchor_inventory"


def slugify(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"`+", "", s)
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
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
            rel = md.relative_to(root)
            slug_locations[slug].append(f"{rel}:{lineno}")
    stats: dict[str, SlugStat] = {}
    for slug, locs in slug_locations.items():
        files = sorted({loc.split(":")[0] for loc in locs})
        stats[slug] = SlugStat(slug=slug, count=len(locs), file_count=len(files), files=files)
    return stats


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-root", type=Path, default=Path("docs"))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--artifacts-to-keep", type=int, default=10)
    parser.add_argument("--timestamp", help="Override run timestamp (ISO 8601)")
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
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args(argv)


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
    duplicates: list[SlugStat],
    allow_set: set[str],
    allowlist_size: int | None,
) -> dict[str, int | None]:
    return {
        "total_slugs": len(stats),
        "cross_file_duplicates": len(duplicates),
        "generic_allow_size": len(allow_set),
        "allowlist_size": allowlist_size,
    }


def build_cross_file_duplicates(stats: dict[str, SlugStat], allow_set: set[str]) -> list[SlugStat]:
    duplicates = [
        st for st in stats.values() if st.file_count > 1 and st.slug not in allow_set
    ]
    duplicates.sort(key=lambda s: (-s.file_count, -s.count, s.slug))
    return duplicates


def build_report(
    *,
    docs_root: Path,
    stats: dict[str, SlugStat],
    duplicates: list[SlugStat],
    allow_set: set[str],
    allowlist_size: int | None,
    generated_ts: datetime,
) -> tuple[dict, list[SlugStat]]:
    ordered_slugs = sorted(
        stats.values(), key=lambda s: (-s.file_count, -s.count, s.slug)
    )
    summary = build_summary(stats, duplicates, allow_set, allowlist_size)
    report = {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "docs_root": str(docs_root),
        "summary": summary,
        "duplicates": [asdict(s) for s in duplicates],
        "slugs": [asdict(s) for s in ordered_slugs],
        "allow_generic": sorted(allow_set),
        "allowlist_size": allowlist_size,
    }
    return report, ordered_slugs


def write_markdown(report: dict, ordered_slugs: list[SlugStat]) -> str:
    summary = report["summary"]
    lines: list[str] = [
        "# Anchor Inventory Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Docs Root: {report['docs_root']}",
        "",
        "## Summary",
        "",
        f"* total slugs: {summary['total_slugs']}",
        f"* cross-file duplicates: {summary['cross_file_duplicates']}",
        f"* generic allow size: {summary['generic_allow_size']}",
        f"* allowlist size: {summary['allowlist_size']}",
        "",
        "## Top Cross-File Duplicates (up to 25)",
        "",
    ]
    duplicates = report.get("duplicates", [])
    if duplicates:
        for dup in duplicates[:25]:
            lines.append(
                f"- `{dup['slug']}` — {dup['file_count']} files ({dup['count']} headings)"
            )
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Top Slugs by File Coverage (up to 25)")
    lines.append("")
    for stat in ordered_slugs[:25]:
        lines.append(
            f"- `{stat.slug}` — {stat.file_count} files ({stat.count} headings)"
        )
    lines.append("")
    lines.append("## Generic Allowlist")
    lines.append("")
    allow_generic = report.get("allow_generic", [])
    if allow_generic:
        for slug in allow_generic:
            lines.append(f"- `{slug}`")
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines) + "\n"


def write_artifacts(
    report: dict,
    ordered_slugs: list[SlugStat],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_ts = datetime.fromisoformat(report["generated_utc"])
    run_dir = output_dir / f"{RUN_PREFIX}-{generated_ts.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = run_dir / "report.md"
    md_path.write_text(write_markdown(report, ordered_slugs), encoding="utf-8")

    tsv_lines = ["slug\tcount\tfile_count\tfiles"]
    for stat in ordered_slugs:
        tsv_lines.append(
            f"{stat.slug}\t{stat.count}\t{stat.file_count}\t" + ",".join(stat.files)
        )
    tsv_path = run_dir / "slugs.tsv"
    tsv_path.write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")

    latest_pairs = [
        (json_path, output_dir / "latest_report.json"),
        (md_path, output_dir / "latest_report.md"),
        (tsv_path, output_dir / "latest_slugs.tsv"),
    ]
    for src, dest in latest_pairs:
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)
        except OSError:
            dest.write_bytes(src.read_bytes())

    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:
    keep = max(keep, 1)
    if not output_dir.exists():
        return []
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    candidates.sort(key=lambda p: p.name, reverse=True)
    removed: list[Path] = []
    for idx, path in enumerate(candidates):
        if idx < keep or path == current_run:
            continue
        removed.append(path)
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)  # type: ignore[attr-defined]
        path.rmdir()
    return removed


def emit_summary_log(
    logger: logging.Logger,
    ordered_slugs: list[SlugStat],
    duplicates: list[SlugStat],
) -> None:
    header = f"{'SLUG':40} {'CNT':>4} {'FILES':>5}"
    logger.info(header)
    logger.info("-" * len(header))
    for st in ordered_slugs[:25]:
        logger.info(f"{st.slug[:40]:40} {st.count:4d} {st.file_count:5d}")
    if duplicates:
        logger.info("Top duplicates (up to 10):")
        for dup in duplicates[:10]:
            logger.info(
                "  %s -> %d files (%d headings)", dup.slug, dup.file_count, dup.count
            )
    else:
        logger.info("No cross-file duplicates outside generic allowlist.")


def load_allow_set(defaults: set[str], allow_file: Path | None) -> set[str]:
    allow_set = set(defaults)
    if allow_file and allow_file.exists():
        for line in allow_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            slug = line.strip().lower()
            if slug:
                allow_set.add(slug)
    return allow_set


def _parse_timestamp(raw: str | None) -> datetime:
    if raw is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - validated via CLI
        raise SystemExit(f"Invalid --timestamp value: {exc}")


def maybe_write_legacy_json(path: Path | None, payload: dict, logger: logging.Logger) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    logger.info("Wrote baseline JSON: %s", path)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )
    log = logging.getLogger("anchor_inventory")
    docs_root = args.docs_root.resolve()
    if not docs_root.exists():
        raise SystemExit(f"docs directory not found: {docs_root}")

    stats = collect(docs_root)
    allow_set = load_allow_set(set(GENERIC_ALLOWED), args.allow_file)
    duplicates = build_cross_file_duplicates(stats, allow_set)
    allowlist_size = extract_test_allowlist_size(args.test_file) if args.test_file else None
    generated_ts = _parse_timestamp(args.timestamp)
    report, ordered_slugs = build_report(
        docs_root=docs_root,
        stats=stats,
        duplicates=duplicates,
        allow_set=allow_set,
        allowlist_size=allowlist_size,
        generated_ts=generated_ts,
    )

    output_dir = args.output_dir.resolve()
    run_dir = write_artifacts(report, ordered_slugs, output_dir)
    pruned = prune_old_runs(output_dir, keep=args.artifacts_to_keep, current_run=run_dir)
    if pruned:
        log.info("Pruned %d old run(s)", len(pruned))

    maybe_write_legacy_json(args.json_out, report, log)
    emit_summary_log(log, ordered_slugs, duplicates)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
