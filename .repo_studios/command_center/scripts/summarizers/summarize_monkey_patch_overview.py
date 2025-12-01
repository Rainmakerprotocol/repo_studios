#!/usr/bin/env python3
"""Generate healthview-ready Monkey Patch Oversight overview artifacts."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from command_center.scripts.libraries import (
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    ReportArtifact,
    WriteReportArtifactsResult,
    build_standard_options,
    build_standard_paths,
    write_report_artifacts,
)

DEFAULT_CONSUMER_OUTPUT_DIR = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_PRODUCER_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_AGGREGATOR_OUTPUT_DIR = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT_DIR = Path(".repo_studios/reports/summarizer_reports/monkey_patch_overview")
SUMMARY_STEM = "monkey_patch_overview"
VIEWER_SLUG = "commandview"
TOPIC_SLUG = "monkey_patch_overview"
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    consumer_output_dir: Path
    producer_output_dir: Path
    aggregator_output_dir: Path
    output_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "consumer_output_dir": PathSpec(
            field="consumer_output_dir", default=DEFAULT_CONSUMER_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "producer_output_dir": PathSpec(
            field="producer_output_dir", default=DEFAULT_PRODUCER_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "aggregator_output_dir": PathSpec(
            field="aggregator_output_dir", default=DEFAULT_AGGREGATOR_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_SUMMARIZER_OUTPUT_DIR, ensure_dir=True, within_repo=False),
    },
    repo_root_depth=5,
)


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int
    log_level: str
    run_timestamp: datetime
    duplicate_matrix: Path | None
    consumer_summary_override: Path | None
    consumer_bundle_summary_override: Path | None
    trend_json_override: Path | None
    trend_markdown_override: Path | None
    trend_bundle_summary_override: Path | None
    producer_report_override: Path | None
    producer_matches_override: Path | None


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--consumer-output-dir", default=str(DEFAULT_CONSUMER_OUTPUT_DIR))
    parser.add_argument("--producer-output-dir", default=str(DEFAULT_PRODUCER_OUTPUT_DIR))
    parser.add_argument("--aggregator-output-dir", default=str(DEFAULT_AGGREGATOR_OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_SUMMARIZER_OUTPUT_DIR))
    parser.add_argument("--consumer-summary", help="Explicit consumer summary.json path override")
    parser.add_argument("--consumer-bundle-summary", help="Explicit consumer bundle_summary.json path override")
    parser.add_argument("--trend-json", help="Explicit aggregator trend.json path override")
    parser.add_argument("--trend-markdown", help="Explicit aggregator trend markdown override")
    parser.add_argument("--trend-bundle-summary", help="Explicit aggregator bundle_summary.json override")
    parser.add_argument("--producer-report", help="Explicit producer report.json override")
    parser.add_argument("--producer-matches", help="Explicit producer matches.json override")
    parser.add_argument("--duplicate-matrix", help="Optional duplicate detection matrix to cross-check")
    parser.add_argument("--artifacts-to-keep", type=int, default=5, help="Retention budget for overview artifacts")
    parser.add_argument(
        "--timestamp",
        help="ISO-8601 timestamp for the emitted artifacts (defaults to current UTC time)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - defensive parsing
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace, *, paths: Paths) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)

    return Options(
        artifacts_to_keep=max(int(getattr(keep_values, "artifacts_to_keep", 1)), 1),
        log_level=str(args.log_level),
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
        duplicate_matrix=_resolve_optional_path(paths.repo_root, getattr(args, "duplicate_matrix", None)),
        consumer_summary_override=_resolve_optional_path(paths.repo_root, getattr(args, "consumer_summary", None)),
        consumer_bundle_summary_override=_resolve_optional_path(
            paths.repo_root, getattr(args, "consumer_bundle_summary", None)
        ),
        trend_json_override=_resolve_optional_path(paths.repo_root, getattr(args, "trend_json", None)),
        trend_markdown_override=_resolve_optional_path(paths.repo_root, getattr(args, "trend_markdown", None)),
        trend_bundle_summary_override=_resolve_optional_path(
            paths.repo_root, getattr(args, "trend_bundle_summary", None)
        ),
        producer_report_override=_resolve_optional_path(paths.repo_root, getattr(args, "producer_report", None)),
        producer_matches_override=_resolve_optional_path(paths.repo_root, getattr(args, "producer_matches", None)),
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _read_json(path: Path | None) -> Any | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _latest_pointer(base: Path, name: str) -> Path | None:
    pointer = base / name
    if pointer.exists():
        return pointer.resolve()
    return None


def _latest_run_artifact(base: Path, stem: str, filename: str) -> Path | None:
    if not base.exists():
        return None
    candidates = [child for child in base.iterdir() if child.is_dir() and child.name.startswith(stem)]
    if not candidates:
        return None
    candidates.sort(key=lambda node: node.name)
    latest = candidates[-1] / filename
    return latest.resolve() if latest.exists() else None


def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _collect_duplicate_targets(payload: Any) -> set[str]:
    collected: set[str] = set()
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if isinstance(value, str) and key.lower() in {"file", "path", "module", "module_path", "source"}:
                collected.add(value)
            else:
                collected.update(_collect_duplicate_targets(value))
    elif isinstance(payload, Iterable) and not isinstance(payload, (str, bytes)):
        for item in payload:
            collected.update(_collect_duplicate_targets(item))
    return collected


def _collect_monkey_patch_files(matches_payload: Any) -> set[str]:
    if not isinstance(matches_payload, list):
        return set()
    files: set[str] = set()
    for entry in matches_payload:
        if isinstance(entry, Mapping):
            value = entry.get("file")
            if isinstance(value, str):
                files.add(value)
    return files


def _ensure_path(source: Path | None, *, base: Path, pointer_name: str, stem: str | None, filename: str) -> Path | None:
    if source and source.exists():
        return source
    pointer = _latest_pointer(base, pointer_name)
    if pointer:
        return pointer
    if stem:
        return _latest_run_artifact(base, stem, filename)
    return None


def _build_markdown(
    *,
    generated_at: datetime,
    counts: Mapping[str, int],
    total_findings: int | None,
    producer_report: str | None,
    producer_matches: str | None,
    consumer_summary: str | None,
    trend_json: str | None,
    trend_markdown: str | None,
    duplicate_matrix: str | None,
    overlap: list[dict[str, Any]],
    notes: list[str],
) -> str:
    lines: list[str] = ["# Monkey Patch Oversight Overview", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Portfolio Snapshot")
    lines.append("")
    if total_findings is not None:
        lines.append(f"- Total Findings: {total_findings}")
    lines.append(f"- High Risk: {counts.get('HIGH', 0)}")
    lines.append(f"- Moderate Risk: {counts.get('MODERATE', 0)}")
    lines.append(f"- Safe: {counts.get('SAFE', 0)}")
    if producer_report:
        lines.append(f"- Latest Producer Report: `{producer_report}`")
    if consumer_summary:
        lines.append(f"- Consumer Summary: `{consumer_summary}`")
    if trend_json:
        lines.append(f"- Trend JSON: `{trend_json}`")
    lines.append("")
    lines.append("## Trend Signals")
    lines.append("")
    if trend_markdown:
        lines.append(f"- Trend Markdown: `{trend_markdown}`")
    if trend_json:
        lines.append(f"- Trend JSON: `{trend_json}`")
    else:
        lines.append("- Trend JSON: unavailable")
    lines.append("")
    lines.append("## Duplicate Follow-up")
    lines.append("")
    if duplicate_matrix:
        lines.append(f"- Duplicate Matrix: `{duplicate_matrix}`")
    else:
        lines.append("- Duplicate Matrix: unavailable")
    if overlap:
        lines.append("- Overlapping Monkey Patch Files:")
        for entry in overlap:
            lines.append(f"  - `{entry['file']}`")
            refs = entry.get("duplicate_refs", [])
            for ref in refs:
                lines.append(f"    - matches `{ref}`")
    else:
        lines.append("- Overlapping Monkey Patch Files: none detected")
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(argv: Iterable[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    paths = build_paths(args)
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)
    logger = logging.getLogger("summarize_monkey_patch_overview")

    consumer_summary_path = _ensure_path(
        options.consumer_summary_override,
        base=paths.consumer_output_dir,
        pointer_name="latest_summary.json",
        stem="monkey_patch_risk-",
        filename="summary.json",
    )
    consumer_bundle_summary_path = _ensure_path(
        options.consumer_bundle_summary_override,
        base=paths.consumer_output_dir,
        pointer_name="latest_bundle_summary.json",
        stem="monkey_patch_risk-",
        filename="bundle_summary.json",
    )
    trend_json_path = _ensure_path(
        options.trend_json_override,
        base=paths.aggregator_output_dir,
        pointer_name="latest_trend.json",
        stem="monkey_patch_trends-",
        filename="trend.json",
    )
    trend_markdown_path = _ensure_path(
        options.trend_markdown_override,
        base=paths.aggregator_output_dir,
        pointer_name="latest_trend.md",
        stem="monkey_patch_trends-",
        filename="trend.md",
    )
    trend_bundle_summary_path = _ensure_path(
        options.trend_bundle_summary_override,
        base=paths.aggregator_output_dir,
        pointer_name="latest_bundle_summary.json",
        stem="monkey_patch_trends-",
        filename="bundle_summary.json",
    )
    producer_report_path = _ensure_path(
        options.producer_report_override,
        base=paths.producer_output_dir,
        pointer_name="latest_report.json",
        stem="monkey_patch_scan-",
        filename="report.json",
    )
    producer_matches_path = _ensure_path(
        options.producer_matches_override,
        base=paths.producer_output_dir,
        pointer_name="latest_matches.json",
        stem="monkey_patch_scan-",
        filename="matches.json",
    )

    consumer_summary_payload = _read_json(consumer_summary_path)
    consumer_bundle_payload = _read_json(consumer_bundle_summary_path)
    trend_payload = _read_json(trend_json_path)
    duplicate_payload = _read_json(options.duplicate_matrix)
    matches_payload = _read_json(producer_matches_path)

    counts = {}
    total_findings = None
    if isinstance(consumer_summary_payload, Mapping):
        counts_raw = consumer_summary_payload.get("counts_by_risk")
        if isinstance(counts_raw, Mapping):
            counts = {key: int(value) for key, value in counts_raw.items() if isinstance(value, (int, float))}
        total = consumer_summary_payload.get("total_findings")
        if isinstance(total, (int, float)):
            total_findings = int(total)
    if not counts and isinstance(trend_payload, Mapping):
        latest = trend_payload.get("latest")
        if isinstance(latest, Mapping):
            cur = latest.get("cur")
            if isinstance(cur, Mapping):
                counts_raw = cur.get("counts")
                if isinstance(counts_raw, Mapping):
                    counts = {key: int(value) for key, value in counts_raw.items() if isinstance(value, (int, float))}
                total = cur.get("total")
                if isinstance(total, (int, float)):
                    total_findings = int(total)
    counts = {"HIGH": counts.get("HIGH", 0), "MODERATE": counts.get("MODERATE", 0), "SAFE": counts.get("SAFE", 0)}

    duplicate_targets = _collect_duplicate_targets(duplicate_payload) if duplicate_payload is not None else set()
    monkey_patch_files = _collect_monkey_patch_files(matches_payload)
    overlap: list[dict[str, Any]] = []
    if duplicate_targets and monkey_patch_files:
        for file_path in sorted(monkey_patch_files):
            hits = sorted({target for target in duplicate_targets if file_path in target or target in file_path})
            if hits:
                overlap.append({"file": file_path, "duplicate_refs": hits})

    notes: list[str] = []
    if consumer_summary_path is None:
        notes.append("Consumer summary not located; counts derived from trend data where possible.")
    if trend_json_path is None:
        notes.append("Trend summary unavailable; skip aggregator step or rerun aggregator.")
    if not overlap and duplicate_targets:
        notes.append("No overlapping monkey patch files were detected against the supplied duplicate matrix.")

    overview_payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "generated_at": options.run_timestamp.isoformat(timespec="seconds"),
        "counts_by_risk": counts,
        "total_findings": total_findings,
        "artifacts": {
            "producer_report": _normalize_relative(producer_report_path, paths.repo_root),
            "producer_matches": _normalize_relative(producer_matches_path, paths.repo_root),
            "consumer_summary": _normalize_relative(consumer_summary_path, paths.repo_root),
            "consumer_bundle_summary": _normalize_relative(consumer_bundle_summary_path, paths.repo_root),
            "trend_json": _normalize_relative(trend_json_path, paths.repo_root),
            "trend_markdown": _normalize_relative(trend_markdown_path, paths.repo_root),
            "trend_bundle_summary": _normalize_relative(trend_bundle_summary_path, paths.repo_root),
            "duplicate_matrix": _normalize_relative(options.duplicate_matrix, paths.repo_root),
        },
        "overlap": overlap,
        "notes": notes,
    }

    summary_markdown = _build_markdown(
        generated_at=options.run_timestamp,
        counts=counts,
        total_findings=total_findings,
        producer_report=overview_payload["artifacts"].get("producer_report"),
        producer_matches=overview_payload["artifacts"].get("producer_matches"),
        consumer_summary=overview_payload["artifacts"].get("consumer_summary"),
        trend_json=overview_payload["artifacts"].get("trend_json"),
        trend_markdown=overview_payload["artifacts"].get("trend_markdown"),
        duplicate_matrix=overview_payload["artifacts"].get("duplicate_matrix"),
        overlap=overlap,
        notes=notes,
    )

    artifacts = [
        ReportArtifact(filename=f"{SUMMARY_STEM}.json", kind="json", content=lambda: overview_payload),
        ReportArtifact(filename=f"{SUMMARY_STEM}.md", kind="text", content=lambda: summary_markdown),
    ]
    result: WriteReportArtifactsResult = write_report_artifacts(
        stem=SUMMARY_STEM,
        timestamp=options.run_timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    logger.info(
        "Monkey Patch overview artifacts written to %s (slug=%s)",
        result.run_dir,
        result.slug,
    )

    return {
        "status": "ok",
        "run_dir": str(result.run_dir),
        "slug": result.slug,
        "artifacts": {name: str(path) for name, path in result.artifacts.items()},
    }


def main(argv: Iterable[str] | None = None) -> None:
    raise SystemExit(0 if run(argv).get("status") == "ok" else 1)


__all__ = ["run", "main", "build_paths", "build_options"]
