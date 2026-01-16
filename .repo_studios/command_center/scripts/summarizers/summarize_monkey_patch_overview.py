#!/usr/bin/env python3
"""Generate healthview-ready Monkey Patch Oversight overview artifacts."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, cast

try:  # pragma: no cover - prefer import when packaged
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        WriteReportArtifactsResult,
        build_standard_options,
        build_standard_paths,
        measure_artifact_directory,
        write_report_artifacts,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when running in isolation
    LIBRARIES_ROOT = Path(__file__).resolve().parents[1]
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        WriteReportArtifactsResult,
        build_standard_options,
        build_standard_paths,
        measure_artifact_directory,
        write_report_artifacts,
    )
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

DEFAULT_CONSUMER_OUTPUT_DIR = build_topic_path("consumer", "monkey_patch_risk")
DEFAULT_PRODUCER_OUTPUT_DIR = build_topic_path("producer", "monkey_patch_scans")
DEFAULT_AGGREGATOR_OUTPUT_DIR = build_topic_path("aggregator", "monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT_DIR = build_topic_path("summarizer", "monkey_patch_overview")
SUMMARY_STEM = "monkey_patch_overview"
VIEWER_SLUG = "healthview"
TOPIC_SLUG = "monkey_patch_overview"
SCHEMA_VERSION = 1

DEFAULT_ARTIFACTS_TO_KEEP = get_keep("summarize_monkey_patch_overview")

_HOP_RUN_SLUG_RE = re.compile(r"^\d{8}-\d{4}$")


@dataclass(frozen=True)
class Paths:
    """Resolved path configuration for the summarizer.

    Attributes:
        repo_root: Repository root directory.
        consumer_output_dir: Consumer reports output directory.
        producer_output_dir: Producer reports output directory.
        aggregator_output_dir: Aggregator reports output directory.
        output_dir: Summarizer output directory.
    """

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
    """Runtime options for the summarizer.

    Attributes:
        artifacts_to_keep: Number of artifact bundles to retain.
        log_level: Logging verbosity level.
        run_timestamp: Timestamp for artifact generation.
        duplicate_matrix: Optional path to duplicate detection matrix.
        consumer_summary_override: Explicit consumer summary path.
        consumer_bundle_summary_override: Explicit consumer bundle summary path.
        trend_json_override: Explicit aggregator trend JSON path.
        trend_markdown_override: Explicit aggregator trend markdown path.
        trend_bundle_summary_override: Explicit aggregator bundle summary path.
        producer_report_override: Explicit producer report path.
        producer_matches_override: Explicit producer matches path.
    """

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
    """Retention configuration values.

    Attributes:
        artifacts_to_keep: Number of artifact bundles to retain.
    """

    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse command-line arguments.

    Configure the argument parser with all summarizer options.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Parsed namespace with configuration options.
    """
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
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention budget for overview artifacts",
    )
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
    """Parse an optional timestamp string to datetime.

    Parse ISO-8601 format timestamp, defaulting to current UTC time.

    Args:
        raw: ISO-8601 timestamp string or None.

    Returns:
        Parsed datetime in UTC timezone.

    Raises:
        SystemExit: If timestamp format is invalid.
    """
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
    """Resolve an optional path string to an absolute path.

    Expand user home and resolve relative paths against repo root.

    Args:
        repo_root: Repository root for relative path resolution.
        raw: Path string or None.

    Returns:
        Resolved absolute Path or None if raw is empty.
    """
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def build_paths(args: argparse.Namespace) -> Paths:
    """Build resolved path configuration from CLI arguments.

    Use the standard path builder with the summarizer's path configuration.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Resolved Paths dataclass.
    """
    return cast(Paths, build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace, *, paths: Paths) -> Options:
    """Build runtime options from CLI arguments.

    Resolve all optional path overrides and retention settings.

    Args:
        args: Parsed command-line arguments.
        paths: Resolved path configuration.

    Returns:
        Populated Options dataclass.
    """
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
    """Configure the logging subsystem.

    Set up basic logging with the specified verbosity level.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _read_json(path: Path | None) -> Any | None:
    """Read and parse a JSON file.

    Return None if the path is None, does not exist, or parsing fails.

    Args:
        path: Path to JSON file or None.

    Returns:
        Parsed JSON content or None on failure.
    """
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _latest_run_artifact(base: Path, stem: str | None, filename: str) -> Path | None:
    """Find the latest artifact file under timestamped run directories.

    Prefer HOP timestamp-only directory names (YYYYMMDD-HHMM). When stem is
    supplied, legacy prefixed runs (e.g., <stem><timestamp>) are also supported
    for compatibility.

    Args:
        base: Base directory containing run directories.
        stem: Optional directory name prefix to match.
        filename: Artifact filename to look for.

    Returns:
        Path to the artifact if found, None otherwise.
    """
    if not base.exists():
        return None

    def _dir_timestamp(name: str) -> datetime | None:
        candidate = name.strip()
        if not candidate:
            return None
        if stem:
            candidate = candidate[len(stem) :] if candidate.startswith(stem) else candidate
        if _HOP_RUN_SLUG_RE.fullmatch(candidate):
            try:
                return datetime.strptime(candidate, "%Y%m%d-%H%M").replace(tzinfo=UTC)
            except ValueError:
                return None
        for fmt in ("%Y-%m-%d_%H%M%S", "%Y%m%d%H%M%S"):
            try:
                return datetime.strptime(candidate, fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
        return None

    run_dirs: list[Path] = []
    for child in base.iterdir():
        if not child.is_dir():
            continue
        if stem and child.name.startswith(stem):
            run_dirs.append(child)
            continue
        if _dir_timestamp(child.name) is not None:
            run_dirs.append(child)

    if not run_dirs:
        return None

    run_dirs.sort(key=lambda node: (_dir_timestamp(node.name) or datetime.min.replace(tzinfo=UTC), node.name))
    latest = run_dirs[-1] / filename
    return latest.resolve() if latest.exists() else None


def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:
    """Convert a path to a POSIX relative path string.

    Attempt to make the path relative to repo_root, fall back to absolute.

    Args:
        path: Path to normalize or None.
        repo_root: Repository root for relative path computation.

    Returns:
        POSIX path string or None if path is None.
    """
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _collect_duplicate_targets(payload: Any) -> set[str]:
    """Recursively collect file paths from a duplicate matrix payload.

    Extract all string values from keys indicating file paths.

    Args:
        payload: Nested dictionary or list structure.

    Returns:
        Set of collected file path strings.
    """
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
    """Extract file paths from monkey patch matches payload.

    Parse the matches list and collect unique file paths.

    Args:
        matches_payload: List of match dictionaries.

    Returns:
        Set of file path strings.
    """
    if not isinstance(matches_payload, list):
        return set()
    files: set[str] = set()
    for entry in matches_payload:
        if isinstance(entry, Mapping):
            value = entry.get("file")
            if isinstance(value, str):
                files.add(value)
    return files


def _ensure_path(source: Path | None, *, base: Path, stem: str | None, filename: str) -> Path | None:
    """Resolve an artifact path with fallback strategies.

    Prefer explicit overrides, otherwise locate the latest run artifact from
    timestamped run directories.

    Args:
        source: Explicit source path or None.
        base: Base directory for fallback searches.
        stem: Directory stem prefix for run directory search.
        filename: Artifact filename to look for.

    Returns:
        Resolved path if found through any strategy, None otherwise.
    """
    if source and source.exists():
        return source
    if stem is not None:
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
    trend_signals: Mapping[str, Any] | None,
    top_files: list[tuple[str, int]],
    top_categories: list[tuple[str, int]],
    duplicate_matrix: str | None,
    overlap: list[dict[str, Any]],
    notes: list[str],
) -> str:
    """Build the overview markdown summary.

    Format portfolio snapshot, trend signals, duplicate follow-up,
    and notes into a complete markdown document.

    Args:
        generated_at: Generation timestamp.
        counts: Risk level counts dictionary.
        total_findings: Total finding count or None.
        producer_report: Relative path to producer report.
        producer_matches: Relative path to producer matches.
        consumer_summary: Relative path to consumer summary.
        trend_json: Relative path to trend JSON.
        trend_markdown: Relative path to trend markdown.
        trend_signals: Optional signals payload from trend.json.
        top_files: Top file finding counts from consumer bundle summary.
        top_categories: Top category counts from consumer bundle summary.
        duplicate_matrix: Relative path to duplicate matrix.
        overlap: List of overlapping file entries.
        notes: List of informational notes.

    Returns:
        Markdown-formatted overview string.
    """

    def _format_pct(value: object) -> str:
        if value is None:
            return "n/a"
        if isinstance(value, (int, float)):
            return f"{value * 100:+.1f}%"
        return "n/a"

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

    latest_signal: Mapping[str, Any] | None = None
    if isinstance(trend_signals, Mapping):
        maybe_latest = trend_signals.get("latest")
        if isinstance(maybe_latest, Mapping):
            latest_signal = cast(Mapping[str, Any], maybe_latest)

    if latest_signal is not None:
        delta_total = latest_signal.get("delta_total")
        delta_by_risk = latest_signal.get("delta_by_risk")
        pct_total = latest_signal.get("pct_total")
        changed = latest_signal.get("changed")
        changed_levels = latest_signal.get("changed_levels")
        if isinstance(delta_total, int):
            lines.append(f"- Delta Total: {delta_total:+d}")
        else:
            lines.append("- Delta Total: n/a")
        if isinstance(delta_by_risk, Mapping):
            high = int(delta_by_risk.get("HIGH", 0))
            moderate = int(delta_by_risk.get("MODERATE", 0))
            safe = int(delta_by_risk.get("SAFE", 0))
            lines.append(f"- Delta HIGH/MODERATE/SAFE: {high:+d} / {moderate:+d} / {safe:+d}")
        lines.append(f"- Percent Total: {_format_pct(pct_total)}")
        lines.append(f"- Changed: {str(bool(changed)).lower()}")
        if isinstance(changed_levels, list) and changed_levels:
            lines.append(f"- Changed Levels: {', '.join(str(v) for v in changed_levels)}")
        else:
            lines.append("- Changed Levels: none")

    rolling_3 = trend_signals.get("rolling_3") if isinstance(trend_signals, Mapping) else None
    if isinstance(rolling_3, Mapping) and "total_avg" in rolling_3:
        try:
            lines.append(f"- Rolling(3) Total Avg: {float(rolling_3['total_avg']):.2f}")
        except Exception:
            pass
    lines.append("")

    lines.append("## Top Drivers")
    lines.append("")
    if top_files:
        lines.append("### Top Files")
        lines.append("")
        lines.append("| File | Findings |")
        lines.append("|---|---:|")
        for file_path, count in top_files:
            lines.append(f"| {file_path} | {count} |")
        lines.append("")
    if top_categories:
        lines.append("### Top Categories")
        lines.append("")
        lines.append("| Category | Findings |")
        lines.append("|---|---:|")
        for category, count in top_categories:
            lines.append(f"| {category} | {count} |")
        lines.append("")

    lines.append("## Actions")
    lines.append("")
    if latest_signal is not None and isinstance(latest_signal.get("delta_by_risk"), Mapping):
        delta_high = int(cast(Mapping[str, Any], latest_signal["delta_by_risk"]).get("HIGH", 0))
        if delta_high > 0:
            lines.append("- HIGH risk increased: open the trend markdown and review top HIGH files.")
        elif bool(latest_signal.get("changed")):
            lines.append("- Risk profile changed: review deltas and reconcile drivers listed above.")
        else:
            lines.append("- No risk deltas detected: spot-check HIGH findings and monitor trend.")
    else:
        lines.append("- Trend signals unavailable: open the trend JSON/markdown if present.")
    if not duplicate_matrix:
        lines.append("- Provide a duplicate matrix to enable overlap cross-checking (optional).")
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


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Execute the monkey patch overview summarizer.

    Collect artifacts from producer, consumer, and aggregator tiers,
    compute overlap with duplicate matrix, and write overview artifacts.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Result dictionary with status and artifact paths.
    """
    args = _parse_args(argv)
    paths = build_paths(args)
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)
    logger = logging.getLogger("summarize_monkey_patch_overview")

    consumer_summary_path = _ensure_path(
        options.consumer_summary_override,
        base=paths.consumer_output_dir,
        stem="",
        filename="summary.json",
    )
    consumer_bundle_summary_path = _ensure_path(
        options.consumer_bundle_summary_override,
        base=paths.consumer_output_dir,
        stem="",
        filename="bundle_summary.json",
    )
    trend_json_path = _ensure_path(
        options.trend_json_override,
        base=paths.aggregator_output_dir,
        stem="",
        filename="trend.json",
    )
    trend_markdown_path = _ensure_path(
        options.trend_markdown_override,
        base=paths.aggregator_output_dir,
        stem="",
        filename="trend.md",
    )
    trend_bundle_summary_path = _ensure_path(
        options.trend_bundle_summary_override,
        base=paths.aggregator_output_dir,
        stem="",
        filename="bundle_summary.json",
    )
    producer_report_path = _ensure_path(
        options.producer_report_override,
        base=paths.producer_output_dir,
        stem="",
        filename="report.json",
    )
    producer_matches_path = _ensure_path(
        options.producer_matches_override,
        base=paths.producer_output_dir,
        stem="",
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

    trend_signals: Mapping[str, Any] | None = None
    if isinstance(trend_payload, Mapping):
        maybe_signals = trend_payload.get("signals")
        if isinstance(maybe_signals, Mapping):
            trend_signals = cast(Mapping[str, Any], maybe_signals)

    top_files: list[tuple[str, int]] = []
    top_categories: list[tuple[str, int]] = []
    if isinstance(consumer_bundle_payload, Mapping):
        maybe_files = consumer_bundle_payload.get("top_files")
        if isinstance(maybe_files, list):
            for entry in maybe_files[:5]:
                if (
                    isinstance(entry, list)
                    and len(entry) == 2
                    and isinstance(entry[0], str)
                    and isinstance(entry[1], (int, float))
                ):
                    top_files.append((entry[0].replace("\\\\", "/"), int(entry[1])))
        maybe_categories = consumer_bundle_payload.get("top_categories")
        if isinstance(maybe_categories, list):
            for entry in maybe_categories[:5]:
                if (
                    isinstance(entry, list)
                    and len(entry) == 2
                    and isinstance(entry[0], str)
                    and isinstance(entry[1], (int, float))
                ):
                    top_categories.append((entry[0], int(entry[1])))

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

    artifacts_dict: dict[str, str | None] = {
        "producer_report": _normalize_relative(producer_report_path, paths.repo_root),
        "producer_matches": _normalize_relative(producer_matches_path, paths.repo_root),
        "consumer_summary": _normalize_relative(consumer_summary_path, paths.repo_root),
        "consumer_bundle_summary": _normalize_relative(consumer_bundle_summary_path, paths.repo_root),
        "trend_json": _normalize_relative(trend_json_path, paths.repo_root),
        "trend_markdown": _normalize_relative(trend_markdown_path, paths.repo_root),
        "trend_bundle_summary": _normalize_relative(trend_bundle_summary_path, paths.repo_root),
        "duplicate_matrix": _normalize_relative(options.duplicate_matrix, paths.repo_root),
    }
    overview_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "generated_at": options.run_timestamp.isoformat(timespec="seconds"),
        "counts_by_risk": counts,
        "total_findings": total_findings,
        "artifacts": artifacts_dict,
        "overlap": overlap,
        "notes": notes,
    }

    telemetry_payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "generated_at": options.run_timestamp.isoformat(timespec="seconds"),
        "status": "ok",
        "counts_by_risk": counts,
        "total_findings": total_findings,
        "overlap_count": len(overlap),
        "notes": notes,
    }

    summary_markdown = _build_markdown(
        generated_at=options.run_timestamp,
        counts=counts,
        total_findings=total_findings,
        producer_report=artifacts_dict.get("producer_report"),
        producer_matches=artifacts_dict.get("producer_matches"),
        consumer_summary=artifacts_dict.get("consumer_summary"),
        trend_json=artifacts_dict.get("trend_json"),
        trend_markdown=artifacts_dict.get("trend_markdown"),
        trend_signals=trend_signals,
        top_files=top_files,
        top_categories=top_categories,
        duplicate_matrix=artifacts_dict.get("duplicate_matrix"),
        overlap=overlap,
        notes=notes,
    )

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: overview_payload),
        ReportArtifact(filename="summary.md", kind="text", content=lambda: summary_markdown),
        ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
    ]
    # HOP-compliant: pass viewer="" and topic="" to enable timestamp-only directory naming
    result: WriteReportArtifactsResult = write_report_artifacts(
        stem=SUMMARY_STEM,
        timestamp=options.run_timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer="",
        topic="",
    )

    artifact_metrics = measure_artifact_directory(result.run_dir)
    telemetry_payload.setdefault("metrics", {}).update(artifact_metrics.as_dict())
    overview_payload.setdefault("metrics", {}).update(artifact_metrics.as_dict())
    overview_payload["telemetry"] = telemetry_payload

    manifest_path = result.artifacts.get("manifest.json")
    if manifest_path is not None:
        manifest_path.write_text(
            json.dumps(overview_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    telemetry_path = result.artifacts.get("telemetry.json")
    if telemetry_path is not None:
        telemetry_path.write_text(
            json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
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


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for the monkey patch overview summarizer.

    Run the summarizer and exit with appropriate status code.

    Args:
        argv: Command-line arguments or None for sys.argv.
    """
    raise SystemExit(0 if run(argv).get("status") == "ok" else 1)


__all__ = ["run", "main", "build_paths", "build_options"]
