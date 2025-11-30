#!/usr/bin/env python3
"""Identify standards directives present in source markdown files but missing from the index."""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

import yaml

DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
VIEWER_SLUG = "commandview"
TOPIC_SLUG = "standards_index_gaps"
DEFAULT_INDEX_PATH = Path(
    ".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml"
)
LEGACY_INDEX_PATH = Path(".repo_studios/scripts/repo_standards_index.yaml")
DEFAULT_CATEGORIES_PATH = Path(".repo_studios/scripts/.repo_studios/standards_categories.yaml")
DEFAULT_ARTIFACTS_TO_KEEP = 5
RUN_STEM = "standards_index_gap"
RUN_PREFIX = RUN_STEM
SCHEMA_VERSION = 1

IMP_VERBS = re.compile(
    r"^(?:[-*]\s*|\d+\.\s*)?(?:avoid|ensure|prefer|use|never|do not|limit|prohibit|enforce|document|pin)\b",
    re.IGNORECASE,
)
STRIP_PREFIX = re.compile(r"^[-*]\s*|^\d+\.\s*")
WORD_EXTRACTOR = re.compile(r"[a-zA-Z]{4,}")

LIBRARIES_ROOT = Path(__file__).resolve().parents[1]

try:  # pragma: no cover - prefer import when packaged
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running in isolation
    import sys

    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )


@dataclass(frozen=True)
class GapCandidate:
    line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {"line": self.line, "text": self.text}


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    index_path: Path
    categories_path: Path


@dataclass
class Options:
    artifacts_to_keep: int
    max_show: int = 8
    timestamp: str | None = None


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=True),
        "index_path": PathSpec(field="index_path", default=DEFAULT_INDEX_PATH, within_repo=True),
        "categories_path": PathSpec(field="categories_path", default=DEFAULT_CATEGORIES_PATH, within_repo=True),
    },
    repo_root_depth=4,
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _ensure_index_path(paths: Paths, logger: logging.Logger) -> Paths:
    if paths.index_path.exists():
        return paths
    legacy_candidate = (paths.repo_root / LEGACY_INDEX_PATH).resolve()
    if legacy_candidate.exists():
        logger.warning(
            "standards index missing at %s; falling back to legacy snapshot %s",
            paths.index_path,
            legacy_candidate,
        )
        return replace(paths, index_path=legacy_candidate)
    return paths


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--output-dir", help="Directory for structured artifacts")
    parser.add_argument("--index-path", help="Path to repo_standards_index.yaml")
    parser.add_argument("--categories-path", help="Path to standards_categories.yaml")
    parser.add_argument("--json", dest="legacy_json", help="Optional legacy JSON output path")
    parser.add_argument(
        "--max",
        dest="max_show",
        type=int,
        default=8,
        help="Maximum candidates to display per source in logs",
    )
    parser.add_argument(
        "--timestamp",
        help="Override run timestamp (ISO 8601) for deterministic tests",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention count for timestamped runs",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def _configure_logging(level: str) -> logging.Logger:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")
    return logging.getLogger("analyze_standards_index_gaps")


def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def _resolve_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - defensive parsing
        raise RuntimeError(f"Invalid --timestamp value: {exc}")
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def load_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"Standards index not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Standards index payload must be a mapping: {path}")
    return data


def load_sources(categories_path: Path, repo_root: Path, logger: logging.Logger) -> list[Path]:
    if not categories_path.exists():
        logger.debug("Categories file missing; falling back to index sources")
        return []
    payload = yaml.safe_load(categories_path.read_text(encoding="utf-8")) or {}
    sources: list[Path] = []
    for entry in payload.get("sources", []) or []:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("path")
        if not raw:
            continue
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if candidate.exists():
            sources.append(candidate)
        else:
            logger.warning("Source listed in categories file but missing: %s", candidate)
    return sources


def sources_from_index(index: dict[str, Any], repo_root: Path, logger: logging.Logger) -> list[Path]:
    sources: list[Path] = []
    for entry in index.get("sources", []) or []:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("path")
        if not raw:
            continue
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        if candidate.exists():
            sources.append(candidate)
        else:
            logger.warning("Source listed in index but missing: %s", candidate)
    return sources


def build_existing_tokens(index: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for rule in index.get("rules", []) or []:
        if not isinstance(rule, dict):
            continue
        summary = str(rule.get("summary", ""))
        tokens.update(word.lower() for word in WORD_EXTRACTOR.findall(summary))
        rule_id = rule.get("id")
        if rule_id:
            tokens.add(str(rule_id).lower())
    return tokens


def scan_file(path: Path, *, existing_tokens: set[str]) -> list[GapCandidate]:
    results: list[GapCandidate] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as exc:  # pragma: no cover - defensive read
        logging.getLogger("analyze_standards_index_gaps").warning("Failed reading %s: %s", path, exc)
        return results
    for index, raw in enumerate(lines, start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if not IMP_VERBS.match(text):
            continue
        core = STRIP_PREFIX.sub("", text).lower()
        words = WORD_EXTRACTOR.findall(core)
        if words:
            overlap = sum(1 for token in words if token in existing_tokens)
            if overlap / len(words) > 0.6:
                continue
        results.append(GapCandidate(line=index, text=raw))
    return results


def run_gap_detection(index: dict[str, Any], sources: Iterable[Path]) -> dict[str, list[GapCandidate]]:
    existing_tokens = build_existing_tokens(index)
    gaps: dict[str, list[GapCandidate]] = {}
    repo_root_value = index.get("repo_root")
    repo_root = Path(repo_root_value) if repo_root_value else None
    for src in sources:
        candidates = scan_file(src, existing_tokens=existing_tokens)
        if not candidates:
            continue
        try:
            rel = str(src.relative_to(repo_root)) if repo_root else str(src)
        except ValueError:
            rel = str(src)
        gaps[rel] = candidates
    return gaps


def build_report(
    *,
    gaps: dict[str, list[GapCandidate]],
    generated_ts: datetime,
    index_path: Path,
    categories_path: Path,
    source_count: int,
) -> dict[str, Any]:
    total_candidates = sum(len(entries) for entries in gaps.values())
    top_source = max((len(entries) for entries in gaps.values()), default=0)
    sorted_sources = {
        path: [candidate.to_dict() for candidate in items]
        for path, items in sorted(gaps.items(), key=lambda item: item[0])
    }
    top_sources = [
        {"path": path, "candidate_count": len(items)}
        for path, items in sorted(gaps.items(), key=lambda item: (-len(item[1]), item[0]))[:10]
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_utc": generated_ts.isoformat(),
        "index_path": str(index_path),
        "categories_path": str(categories_path),
        "summary": {
            "total_candidates": total_candidates,
            "sources_with_candidates": len(gaps),
            "top_source_candidates": top_source,
            "scanned_sources": source_count,
        },
        "sources": sorted_sources,
        "top_sources": top_sources,
        "total_candidates": total_candidates,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = [
        "<!-- markdownlint-disable MD013 -->",
        "",
        "# Standards Index Gap Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Index Path: {report['index_path']}",
        f"Categories Path: {report['categories_path']}",
        "",
        "## Summary",
        "",
        f"- Total candidates: {report['summary']['total_candidates']}",
        f"- Sources with candidates: {report['summary']['sources_with_candidates']}",
        f"- Top source candidate count: {report['summary']['top_source_candidates']}",
        f"- Sources scanned: {report['summary']['scanned_sources']}",
        "",
        "## Sources With Candidates",
        "",
    ]
    sources = report.get("sources", {})
    if not sources:
        lines.append("- (none)")
    else:
        for path, items in sources.items():
            lines.append(f"- **{path}** — {len(items)} candidate(s)")
            for candidate in items[:5]:
                snippet = (
                    candidate["text"].strip().replace("`", "'").replace("<", "&lt;").replace(">", "&gt;")
                )
                lines.append(f"  - L{candidate['line']}: {snippet}")
            if len(items) > 5:
                lines.append(f"  - ... (+{len(items) - 5} more)")
    lines.extend(["", "<!-- markdownlint-enable MD013 -->"])
    return "\n".join(lines)


def render_tsv(report: dict[str, Any]) -> str:
    rows = ["source\tline\ttext"]
    for path, items in report.get("sources", {}).items():
        for candidate in items:
            text = candidate["text"].replace("\t", " ").replace("\n", " ")
            rows.append(f"{path}\t{candidate['line']}\t{text}")
    return "\n".join(rows) + "\n"


def emit_runtime_log(logger: logging.Logger, report: dict[str, Any], *, max_show: int) -> None:
    sources = report.get("sources", {})
    if not sources:
        logger.info("No candidate gaps detected")
        return
    for path, items in sources.items():
        logger.info("%s: %d candidate(s)", path, len(items))
        for entry in items[:max_show]:
            logger.info("  L%4d | %s", entry["line"], entry["text"].strip())
        if len(items) > max_show:
            logger.info("  ... (+%d more)", len(items) - max_show)
    logger.info("Total candidate directives: %d", report.get("total_candidates", 0))


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    logger = _configure_logging(args.log_level)

    paths = build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))
    paths = _ensure_index_path(paths, logger)
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    options = Options(
        artifacts_to_keep=base_options.artifacts_to_keep,
        max_show=max(1, args.max_show),
        timestamp=args.timestamp,
    )

    index = load_index(paths.index_path)
    index.setdefault("repo_root", str(paths.repo_root))

    sources = load_sources(paths.categories_path, paths.repo_root, logger)
    if not sources:
        sources = sources_from_index(index, paths.repo_root, logger)
    if not sources:
        raise RuntimeError("No standards sources available for scan.")

    gaps = run_gap_detection(index, sources)
    generated_ts = _resolve_timestamp(options.timestamp)
    report = build_report(
        gaps=gaps,
        generated_ts=generated_ts,
        index_path=paths.index_path,
        categories_path=paths.categories_path,
        source_count=len(sources),
    )

    markdown_payload = render_markdown(report)
    tsv_payload = render_tsv(report)
    bundle_summary = {
        "total_candidates": report["summary"]["total_candidates"],
        "sources_with_candidates": report["summary"]["sources_with_candidates"],
        "top_sources": report["top_sources"],
    }

    artifacts = [
        ReportArtifact(filename="report.json", kind="json", content=report),
        ReportArtifact(filename="report.md", kind="text", content=markdown_payload),
        ReportArtifact(filename="candidates.tsv", kind="text", content=tsv_payload),
        ReportArtifact(
            filename="bundle_summary.json",
            kind="json",
            content=bundle_summary,
        ),
    ]

    write_result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=generated_ts,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer=VIEWER_SLUG,
        topic=TOPIC_SLUG,
    )

    emit_runtime_log(logger, report, max_show=options.max_show)

    legacy_json = _resolve_optional_path(paths.repo_root, args.legacy_json)
    if legacy_json:
        legacy_json.parent.mkdir(parents=True, exist_ok=True)
        legacy_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        logger.info("Wrote legacy JSON payload: %s", legacy_json)

    return {
        "run_dir": str(write_result.run_dir),
        "report_json": str(write_result.artifacts["report.json"]),
        "report_md": str(write_result.artifacts["report.md"]),
        "candidates_tsv": str(write_result.artifacts["candidates.tsv"]),
        "bundle_summary": str(write_result.artifacts["bundle_summary.json"]),
        "legacy_json": str(legacy_json) if legacy_json else None,
        "summary": report["summary"],
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        run(argv)
    except RuntimeError as exc:
        logging.getLogger("analyze_standards_index_gaps").error("%s", exc)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
