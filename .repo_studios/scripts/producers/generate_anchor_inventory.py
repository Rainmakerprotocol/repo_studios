#!/usr/bin/env python3
"""Anchor Inventory Tool.

Generates an inventory of top-level (H1/H2) markdown headings under the docs
tree and emits structured artifacts (JSON/Markdown/TSV) with pruning and latest
pointers managed by the shared Command Center helpers.
"""

import argparse
import json
import logging
import re
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/anchor_inventory_reports")
RUN_PREFIX = "anchor_inventory"
DEFAULT_ARTIFACTS_TO_KEEP = 10

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - import guard for standalone execution
    from libraries import (  # type: ignore import
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
    from libraries.artifacts import ReportArtifact, write_report_artifacts  # type: ignore import
except ModuleNotFoundError:  # pragma: no cover - fallback when script is run directly
    import sys

    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore import
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
    from libraries.artifacts import ReportArtifact, write_report_artifacts  # type: ignore import


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    docs_root: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


PATH_SPECS: dict[str, PathSpec] = {
    "docs_root": PathSpec(field="docs_root", default=Path("docs"), ensure_dir=False, within_repo=False),
    "output_dir": PathSpec(
        field="output_dir",
        default=DEFAULT_OUTPUT_DIR,
        ensure_dir=False,
        within_repo=False,
    ),
}

PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)

KEEP_SPECS: dict[str, KeepSpec] = {
    "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
}

OPTIONS_CONFIG = OptionsConfig(dataclass_type=Options, keep_specs=KEEP_SPECS)


def slugify(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"`+", "", s)
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for md in root.rglob("*.md"):
        if any(part in md.parts for part in ("coverage_history",)):
            continue
        yield md


@dataclass
class SlugStat:
    slug: str
    count: int
    file_count: int
    files: list[str]
    locations: list[str]


GENERIC_ALLOWED = {"overview", "introduction", "faq", "notes"}


def _compose_location(prefix: Path | None, relative_path: Path, line_number: int) -> str:
    parts: list[str] = []
    if prefix is not None:
        parts.extend(part for part in prefix.parts if part not in (".",))
    parts.extend(relative_path.parts)
    display_path = PurePosixPath(*parts) if parts else PurePosixPath(relative_path.as_posix())
    return f"{display_path}:{line_number}"


def _collect_from_root(root: Path, prefix: Path | None) -> dict[str, list[str]]:
    slug_locations: dict[str, list[str]] = defaultdict(list)
    for md in iter_markdown_files(root):
        text = md.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = HEADING_RE.match(line)
            if not match:
                continue
            level = len(match.group(1))
            if level > 2:
                continue
            slug = slugify(match.group(2))
            rel = md.relative_to(root)
            slug_locations[slug].append(_compose_location(prefix, rel, lineno))
    return slug_locations


def _compute_display_prefix(repo_root: Path, doc_root: Path) -> Path | None:
    try:
        relative = doc_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return None
    if str(relative) in ("", "."):
        return None
    return relative


def collect(doc_roots: Iterable[tuple[Path, Path | None]]) -> dict[str, SlugStat]:
    slug_locations: dict[str, list[str]] = defaultdict(list)
    for root, prefix in doc_roots:
        for slug, locations in _collect_from_root(root, prefix).items():
            slug_locations[slug].extend(locations)
    stats: dict[str, SlugStat] = {}
    for slug, locations in slug_locations.items():
        files = sorted({loc.split(":")[0] for loc in locations})
        stats[slug] = SlugStat(
            slug=slug,
            count=len(locations),
            file_count=len(files),
            files=files,
            locations=sorted(locations),
        )
    return stats


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate anchor inventory artifacts")
    parser.add_argument("--repo-root", help="Repository root override (defaults to script-relative resolution)")
    parser.add_argument("--docs-root", type=Path, default=Path("docs"), help="Docs directory to scan")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for inventory artifacts",
    )
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP)
    parser.add_argument("--timestamp", help="Override run timestamp (ISO 8601)")
    parser.add_argument("--json-out", type=Path, help="Optional legacy JSON mirror path")
    parser.add_argument(
        "--allow-file",
        type=Path,
        help="Optional file containing generic allowlist (one slug per line)",
    )
    parser.add_argument(
        "--test-file",
        type=Path,
        help="Path to test_global_anchors.py for ALLOWED baseline extraction",
    )
    parser.add_argument(
        "--additional-docs-root",
        action="append",
        default=[],
        type=Path,
        help="Additional documentation directories to scan (repeatable)",
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
        stripped = line.strip()
        if stripped.startswith("ALLOWED = {"):
            capture = True
            continue
        if capture:
            if stripped.startswith("}"):
                break
            match = re.search(r"\"([^\"]*)\"", stripped)
            if match:
                allowed_block.append(match.group(1))
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
    duplicates = [st for st in stats.values() if st.file_count > 1 and st.slug not in allow_set]
    duplicates.sort(key=lambda item: (-item.file_count, -item.count, item.slug))
    return duplicates


def build_report(
    *,
    docs_root: Path,
    stats: dict[str, SlugStat],
    duplicates: list[SlugStat],
    allow_set: set[str],
    allowlist_size: int | None,
    scanned_roots: Sequence[Path],
    generated_ts: datetime,
) -> tuple[dict[str, Any], list[SlugStat]]:
    ordered_slugs = sorted(stats.values(), key=lambda item: (-item.file_count, -item.count, item.slug))
    summary = build_summary(stats, duplicates, allow_set, allowlist_size)
    report = {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "docs_root": str(docs_root),
        "scanned_roots": [str(root) for root in scanned_roots],
        "summary": summary,
        "duplicates": [asdict(item) for item in duplicates],
        "slugs": [asdict(item) for item in ordered_slugs],
        "allow_generic": sorted(allow_set),
        "allowlist_size": allowlist_size,
    }
    return report, ordered_slugs


def render_markdown(report: dict[str, Any], ordered_slugs: list[SlugStat]) -> str:
    summary = report["summary"]
    lines: list[str] = [
        "# Anchor Inventory Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Docs Root: {report['docs_root']}",
        "",
        "## Summary",
        "",
        f"- total slugs: {summary['total_slugs']}",
        f"- cross-file duplicates: {summary['cross_file_duplicates']}",
        f"- generic allow size: {summary['generic_allow_size']}",
        f"- allowlist size: {summary['allowlist_size']}",
        "",
        "## Top Cross-File Duplicates (up to 25)",
        "",
    ]
    duplicates = report.get("duplicates", [])
    if duplicates:
        for dup in duplicates[:25]:
            lines.append(f"- `{dup['slug']}` — {dup['file_count']} files ({dup['count']} headings)")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Top Slugs by File Coverage (up to 25)")
    lines.append("")
    for stat in ordered_slugs[:25]:
        lines.append(f"- `{stat.slug}` — {stat.file_count} files ({stat.count} headings)")
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
    lines.append("## Source References")
    lines.append("")
    lines.append(f"- Docs Root: `{report['docs_root']}`")
    scanned_roots = report.get("scanned_roots", [])
    extra_roots = [root for root in scanned_roots if root != report["docs_root"]]
    for root in extra_roots:
        lines.append(f"- Additional Root: `{root}`")
    lines.append(f"- Generated UTC: `{report['generated_utc']}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_tsv(ordered_slugs: list[SlugStat]) -> str:
    lines = ["slug\tcount\tfile_count\tfiles\tlocations"]
    for stat in ordered_slugs:
        files = ",".join(stat.files)
        locations = ";".join(stat.locations)
        lines.append(f"{stat.slug}\t{stat.count}\t{stat.file_count}\t{files}\t{locations}")
    return "\n".join(lines)


def emit_summary_log(logger: logging.Logger, ordered_slugs: list[SlugStat], duplicates: list[SlugStat]) -> None:
    header = f"{'SLUG':40} {'CNT':>4} {'FILES':>5}"
    logger.info(header)
    logger.info("-" * len(header))
    for entry in ordered_slugs[:25]:
        logger.info("%s %4d %5d", f"{entry.slug[:40]:40}", entry.count, entry.file_count)
    if duplicates:
        logger.info("Top duplicates (up to 10):")
        for dup in duplicates[:10]:
            logger.info("  %s -> %d files (%d headings)", dup.slug, dup.file_count, dup.count)
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


def maybe_write_legacy_json(path: Path | None, payload: dict[str, Any], logger: logging.Logger) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    logger.info("Wrote baseline JSON: %s", path)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
        force=True,
    )
    logger = logging.getLogger("anchor_inventory")

    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    options = build_standard_options(args, OPTIONS_CONFIG)

    docs_root = paths.docs_root
    if not docs_root.exists():
        raise SystemExit(f"docs directory not found: {docs_root}")

    primary_root = docs_root.resolve()
    doc_roots: list[tuple[Path, Path | None]] = [(primary_root, None)]
    seen_roots: set[Path] = {primary_root}

    additional_candidates: list[Path] = []
    for raw_extra in args.additional_docs_root:
        candidate = raw_extra
        if not candidate.is_absolute():
            candidate = paths.repo_root / candidate
        additional_candidates.append(candidate.resolve())

    if args.docs_root == Path("docs"):
        repo_docs = (paths.repo_root / ".repo_studios" / "docs").resolve()
        additional_candidates.append(repo_docs)

    for candidate in additional_candidates:
        if candidate in seen_roots:
            continue
        if not candidate.exists():
            logger.warning("Additional docs root not found, skipping: %s", candidate)
            continue
        prefix = _compute_display_prefix(paths.repo_root, candidate)
        doc_roots.append((candidate, prefix))
        seen_roots.add(candidate)

    if len(doc_roots) > 1:
        extras = ", ".join(str(path) for path, _ in doc_roots[1:])
        logger.info("Including additional documentation roots: %s", extras)

    stats = collect(doc_roots)
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
        scanned_roots=[root for root, _ in doc_roots],
        generated_ts=generated_ts,
    )

    artifacts = [
        ReportArtifact(
            filename="report.json",
            pointer="latest_report.json",
            kind="json",
            content=report,
        ),
        ReportArtifact(
            filename="report.md",
            pointer="latest_report.md",
            kind="text",
            content=render_markdown(report, ordered_slugs),
        ),
        ReportArtifact(
            filename="slugs.tsv",
            pointer="latest_slugs.tsv",
            kind="text",
            content=render_tsv(ordered_slugs) + "\n",
        ),
    ]
    result = write_report_artifacts(
        stem=RUN_PREFIX,
        timestamp=generated_ts,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    maybe_write_legacy_json(args.json_out, report, logger)
    emit_summary_log(logger, ordered_slugs, duplicates)

    return {
        "run_dir": str(result.run_dir),
        "slug": result.slug,
        "artifacts": {name: str(path) for name, path in result.artifacts.items()},
        "docs_root": str(docs_root),
        "total_slugs": report["summary"]["total_slugs"],
        "duplicates": len(duplicates),
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
