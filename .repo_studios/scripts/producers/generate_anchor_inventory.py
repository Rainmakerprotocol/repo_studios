#!/usr/bin/env python3
"""Anchor Inventory Tool.

Generates an inventory of top-level (H1/H2) markdown headings under the docs
tree and emits structured artifacts (JSON/Markdown/TSV) with pruning and latest
pointers managed by the shared Command Center helpers.
"""

import argparse
import csv
import json
import logging
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path, PurePosixPath
from typing import Any

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/anchor_inventory_reports")
RUN_PREFIX = "anchor_inventory"
DEFAULT_ARTIFACTS_TO_KEEP = 5

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


@dataclass
class DocumentSummary:
    path: str
    slug_counts: dict[str, int]
    h1_count: int
    h2_count: int

    def heading_count(self) -> int:
        return self.h1_count + self.h2_count

    def unique_slugs(self) -> int:
        return len(self.slug_counts)

    def duplicate_slugs(self) -> list[str]:
        return sorted(slug for slug, count in self.slug_counts.items() if count > 1)

    def missing_h1(self) -> bool:
        return self.h1_count == 0

    def missing_h2(self) -> bool:
        return self.h1_count > 0 and self.h2_count == 0


def _compose_display_path(prefix: Path | None, relative_path: Path) -> PurePosixPath:
    parts: list[str] = []
    if prefix is not None:
        parts.extend(part for part in prefix.parts if part not in (".",))
    parts.extend(relative_path.parts)
    return PurePosixPath(*parts) if parts else PurePosixPath(relative_path.as_posix())


def _document_root_key(path: str) -> str:
    parts = path.split("/")
    if not parts or not parts[0]:
        return "."
    if len(parts) == 1:
        return "."
    return parts[0]


def _compose_location(prefix: Path | None, relative_path: Path, line_number: int) -> str:
    display_path = _compose_display_path(prefix, relative_path)
    return f"{display_path}:{line_number}"


def _collect_from_root(root: Path, prefix: Path | None) -> tuple[dict[str, list[str]], list[DocumentSummary]]:
    slug_locations: dict[str, list[str]] = defaultdict(list)
    document_summaries: list[DocumentSummary] = []
    for md in iter_markdown_files(root):
        text = md.read_text(encoding="utf-8", errors="replace")
        slug_counts: dict[str, int] = defaultdict(int)
        h1_count = 0
        h2_count = 0
        rel = md.relative_to(root)
        for lineno, line in enumerate(text.splitlines(), start=1):
            match = HEADING_RE.match(line)
            if not match:
                continue
            level = len(match.group(1))
            if level > 2:
                continue
            slug = slugify(match.group(2))
            slug_counts[slug] += 1
            if level == 1:
                h1_count += 1
            elif level == 2:
                h2_count += 1
            slug_locations[slug].append(_compose_location(prefix, rel, lineno))
        document_summaries.append(
            DocumentSummary(
                path=str(_compose_display_path(prefix, rel)),
                slug_counts=dict(slug_counts),
                h1_count=h1_count,
                h2_count=h2_count,
            )
        )
    return slug_locations, document_summaries


def _compute_display_prefix(repo_root: Path, doc_root: Path) -> Path | None:
    try:
        relative = doc_root.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return None
    if str(relative) in ("", "."):
        return None
    return relative


def collect(doc_roots: Iterable[tuple[Path, Path | None]]) -> tuple[dict[str, SlugStat], list[DocumentSummary]]:
    slug_locations: dict[str, list[str]] = defaultdict(list)
    documents: dict[str, DocumentSummary] = {}
    for root, prefix in doc_roots:
        root_locations, root_documents = _collect_from_root(root, prefix)
        for slug, locations in root_locations.items():
            slug_locations[slug].extend(locations)
        for doc in root_documents:
            existing = documents.get(doc.path)
            if existing is None:
                documents[doc.path] = doc
                continue
            for slug, count in doc.slug_counts.items():
                existing.slug_counts[slug] = existing.slug_counts.get(slug, 0) + count
            existing.h1_count += doc.h1_count
            existing.h2_count += doc.h2_count
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
    ordered_documents = sorted(documents.values(), key=lambda item: item.path)
    return stats, ordered_documents


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
    documents: Sequence[DocumentSummary],
    cross_file_membership: dict[str, list[str]],
) -> dict[str, Any]:
    cross_file_members = set(cross_file_membership.keys())
    missing_h1 = sum(1 for doc in documents if doc.missing_h1())
    missing_h2 = sum(1 for doc in documents if doc.missing_h2())
    repeated = sum(1 for doc in documents if doc.duplicate_slugs())
    root_counter = Counter(_document_root_key(doc.path) for doc in documents)
    top_roots = [
        {"root": root, "count": count}
        for root, count in root_counter.most_common(10)
    ]
    return {
        "total_slugs": len(stats),
        "cross_file_duplicates": len(duplicates),
        "generic_allow_size": len(allow_set),
        "allowlist_size": allowlist_size,
        "total_documents": len(documents),
        "documents_missing_h1": missing_h1,
        "documents_missing_h2": missing_h2,
        "documents_with_repeated_anchors": repeated,
        "documents_with_cross_file_duplicates": len(cross_file_members),
        "top_document_roots": top_roots,
    }


def build_cross_file_duplicates(stats: dict[str, SlugStat], allow_set: set[str]) -> list[SlugStat]:
    duplicates = [st for st in stats.values() if st.file_count > 1 and st.slug not in allow_set]
    duplicates.sort(key=lambda item: (-item.file_count, -item.count, item.slug))
    return duplicates


def build_cross_file_membership(duplicates: Sequence[SlugStat]) -> dict[str, list[str]]:
    membership: dict[str, list[str]] = defaultdict(list)
    for entry in duplicates:
        for path in entry.files:
            membership[path].append(entry.slug)
    for slugs in membership.values():
        slugs.sort()
    return {path: slugs for path, slugs in sorted(membership.items())}


def build_document_payload(
    documents: Sequence[DocumentSummary],
    allow_set: set[str],
    cross_file_membership: dict[str, list[str]],
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for doc in documents:
        slug_counts = {slug: doc.slug_counts[slug] for slug in sorted(doc.slug_counts)}
        allowlisted = sorted(slug for slug in slug_counts if slug in allow_set)
        payload.append(
            {
                "path": doc.path,
                "h1_count": doc.h1_count,
                "h2_count": doc.h2_count,
                "heading_count": doc.heading_count(),
                "unique_slugs": doc.unique_slugs(),
                "duplicate_slugs": doc.duplicate_slugs(),
                "cross_file_duplicate_slugs": cross_file_membership.get(doc.path, []),
                "allowlisted_slugs": allowlisted,
                "slug_counts": slug_counts,
            }
        )
    return payload


def build_report(
    *,
    docs_root: Path,
    stats: dict[str, SlugStat],
    documents: Sequence[DocumentSummary],
    duplicates: list[SlugStat],
    allow_set: set[str],
    allowlist_size: int | None,
    scanned_roots: Sequence[Path],
    generated_ts: datetime,
) -> tuple[dict[str, Any], list[SlugStat], list[dict[str, Any]]]:
    ordered_slugs = sorted(stats.values(), key=lambda item: (-item.file_count, -item.count, item.slug))
    cross_file_membership = build_cross_file_membership(duplicates)
    documents_payload = build_document_payload(documents, allow_set, cross_file_membership)
    summary = build_summary(stats, duplicates, allow_set, allowlist_size, documents, cross_file_membership)
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
        "documents": documents_payload,
    }
    return report, ordered_slugs, documents_payload


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
        f"- total documents: {summary.get('total_documents')}",
        f"- documents missing H1: {summary.get('documents_missing_h1')}",
        f"- documents missing H2 (with H1 present): {summary.get('documents_missing_h2')}",
        f"- documents with repeated anchors (same file): {summary.get('documents_with_repeated_anchors')}",
        f"- documents with cross-file duplicates: {summary.get('documents_with_cross_file_duplicates')}",
        "",
        "## Document Root Coverage",
        "",
        "Top directories by document count (up to 10):",
        "",
    ]
    for entry in summary.get("top_document_roots", [])[:10]:
        lines.append(f"- `{entry['root']}` — {entry['count']} documents")
    if not summary.get("top_document_roots"):
        lines.append("- (none)")
    lines.append("")
    lines.extend([
        "## Top Cross-File Duplicates (up to 25)",
        "",
    ])
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
    documents = report.get("documents", [])
    cross_file_docs = [doc for doc in documents if doc.get("cross_file_duplicate_slugs")]
    lines.append("## Documents With Cross-File Duplicates (up to 15)")
    lines.append("")
    lines.append("<!-- markdownlint-disable MD013 -->")
    lines.append("")
    if cross_file_docs:
        for doc in cross_file_docs[:15]:
            slugs = ", ".join(f"`{slug}`" for slug in doc.get("cross_file_duplicate_slugs", []))
            lines.append(f"- `{doc['path']}` — {slugs}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("<!-- markdownlint-enable MD013 -->")
    lines.append("")
    missing_h2_docs = [doc for doc in documents if doc.get("h1_count", 0) > 0 and doc.get("h2_count", 0) == 0]
    lines.append("## Documents Missing H2 Headings (up to 15)")
    lines.append("")
    if missing_h2_docs:
        for doc in missing_h2_docs[:15]:
            lines.append(f"- `{doc['path']}` — H1 count {doc['h1_count']}")
    else:
        lines.append("- (none)")
    lines.append("")
    repeated_anchor_docs = [doc for doc in documents if doc.get("duplicate_slugs")]
    lines.append("## Documents With Repeated Anchors (up to 15)")
    lines.append("")
    if repeated_anchor_docs:
        for doc in repeated_anchor_docs[:15]:
            slugs = ", ".join(f"`{slug}`" for slug in doc.get("duplicate_slugs", []))
            lines.append(f"- `{doc['path']}` — {slugs}")
    else:
        lines.append("- (none)")
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


def render_documents_csv(documents: Sequence[dict[str, Any]]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "path",
            "h1_count",
            "h2_count",
            "heading_count",
            "unique_slugs",
            "duplicate_slugs",
            "cross_file_duplicate_slugs",
            "allowlisted_slugs",
        ]
    )
    for doc in documents:
        writer.writerow(
            [
                doc["path"],
                doc["h1_count"],
                doc["h2_count"],
                doc["heading_count"],
                doc["unique_slugs"],
                ";".join(doc.get("duplicate_slugs", [])),
                ";".join(doc.get("cross_file_duplicate_slugs", [])),
                ";".join(doc.get("allowlisted_slugs", [])),
            ]
        )
    return buffer.getvalue().rstrip("\n")


def emit_summary_log(
    logger: logging.Logger,
    ordered_slugs: list[SlugStat],
    duplicates: list[SlugStat],
    summary: dict[str, Any],
    documents: Sequence[dict[str, Any]],
) -> None:
    logger.info(
        "Documents scanned=%s missing_h1=%s missing_h2=%s repeated=%s cross_file_members=%s",
        summary.get("total_documents"),
        summary.get("documents_missing_h1"),
        summary.get("documents_missing_h2"),
        summary.get("documents_with_repeated_anchors"),
        summary.get("documents_with_cross_file_duplicates"),
    )
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
    if documents:
        cross_file_docs = [doc for doc in documents if doc.get("cross_file_duplicate_slugs")]
        if cross_file_docs:
            logger.info("Cross-file duplicate members (up to 5):")
            for doc in cross_file_docs[:5]:
                logger.info(
                    "  %s -> %s",
                    doc["path"],
                    ", ".join(doc.get("cross_file_duplicate_slugs", [])),
                )
        missing_h2_docs = [doc for doc in documents if doc.get("h1_count", 0) > 0 and doc.get("h2_count", 0) == 0]
        if missing_h2_docs:
            logger.info(
                "Docs missing H2 (up to 5): %s",
                ", ".join(doc["path"] for doc in missing_h2_docs[:5]),
            )


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

    stats, documents = collect(doc_roots)
    allow_set = load_allow_set(set(GENERIC_ALLOWED), args.allow_file)
    duplicates = build_cross_file_duplicates(stats, allow_set)
    allowlist_size = extract_test_allowlist_size(args.test_file) if args.test_file else None
    generated_ts = _parse_timestamp(args.timestamp)
    report, ordered_slugs, documents_payload = build_report(
        docs_root=docs_root,
        stats=stats,
        documents=documents,
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
        ReportArtifact(
            filename="documents.csv",
            pointer="latest_documents.csv",
            kind="text",
            content=render_documents_csv(documents_payload) + "\n",
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
    emit_summary_log(logger, ordered_slugs, duplicates, report["summary"], report.get("documents", []))

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
