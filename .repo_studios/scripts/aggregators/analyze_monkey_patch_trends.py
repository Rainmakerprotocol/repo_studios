#!/usr/bin/env python3
"""Analyze monkey-patch risk trends from consumer bundles with provenance."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_CONSUMER_BASE = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_PRODUCER_BASE = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_MAX_RUNS = 20

CONSUMER_BUNDLE_PREFIX = "monkey_patch_risk-"
CONSUMER_SUMMARY_NAME = "summary.json"
CONSUMER_BUNDLE_SUMMARY_NAME = "bundle_summary.json"

AGGREGATOR_PREFIX = "monkey_patch_trends-"
TREND_JSON_NAME = "trend.json"
TREND_MD_NAME = "trend.md"
AGGREGATOR_BUNDLE_SUMMARY_NAME = "bundle_summary.json"
CONSUMER_TREND_COPY_NAME = "TREND_SNAPSHOT.md"

PRODUCER_REPORT_NAME = "report.json"

RISK_LEVELS: tuple[str, ...] = ("HIGH", "MODERATE", "SAFE")

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
UTILITIES_ROOT = Path(__file__).resolve().parents[2]
COMMAND_CENTER_SCRIPTS_ROOT = UTILITIES_ROOT / "command_center" / "scripts"
for candidate in (SCRIPTS_ROOT, UTILITIES_ROOT, COMMAND_CENTER_SCRIPTS_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from utilities.monkey_patch_risk import (  # noqa: E402
    FindingSignals,
    classify_monkey_patch,
)
from libraries import prune_run_directories  # noqa: E402
from libraries.cli import resolve_repo_root  # noqa: E402
from libraries.report_paths import build_topic_path  # noqa: E402
from libraries.retention_policy import get_keep  # noqa: E402

# Defaults that depend on imported functions
DEFAULT_OUTPUT_BASE = build_topic_path("aggregator", "monkey_patch_trends")
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("analyze_monkey_patch_trends")


@dataclass(frozen=True)
class TrendRun:
    """Immutable representation of a trend analysis run.

    Attributes:
        ts_label: Human-readable timestamp label.
        sort_key: Datetime used for chronological sorting.
        total: Total number of findings in this run.
        counts: Risk level counts (HIGH, MODERATE, SAFE).
        bundle_dir: Consumer bundle directory path if available.
        summary_path: Path to the summary JSON file.
        bundle_summary_path: Path to bundle summary if available.
        scan_dir: Source scan directory path if known.
        source: Source type indicator (consumer, producer_fallback).
        metadata: Additional metadata dictionary.
    """

    ts_label: str
    sort_key: datetime
    total: int
    counts: dict[str, int]
    bundle_dir: Path | None
    summary_path: Path | None
    bundle_summary_path: Path | None
    scan_dir: Path | None
    source: str
    metadata: dict[str, Any]


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse command-line arguments.

    Configure the argument parser with all trend analyzer options.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Parsed namespace with configuration options.
    """
    parser = argparse.ArgumentParser(
        description=("Blend monkey-patch consumer bundles (or producer fallbacks) into trend artifacts.")
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root override (auto-detected by scanning ancestors for a .repo_studios/ marker when omitted)"
        ),
    )
    parser.add_argument(
        "--consumer-base",
        type=Path,
        default=DEFAULT_CONSUMER_BASE,
        help="Directory containing timestamped monkey_patch_risk bundles",
    )
    parser.add_argument(
        "--consumer-summary",
        type=Path,
        help="Optional explicit consumer summary path to include in the run",
    )
    parser.add_argument(
        "--producer-base",
        type=Path,
        default=DEFAULT_PRODUCER_BASE,
        help="Producer scans directory for fallback reporting",
    )
    parser.add_argument(
        "--output-base",
        type=Path,
        default=DEFAULT_OUTPUT_BASE,
        help="Output directory for aggregator bundles",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of trend bundles to retain (including newest)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=DEFAULT_MAX_RUNS,
        help="Maximum runs to include when building the overview",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging verbosity (INFO, DEBUG, etc.)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Shortcut for --log-level DEBUG",
    )
    return parser.parse_args(argv)


def _resolve_repo_path(path: Path, *, repo_root: Path) -> Path:
    """Resolve a path relative to the repository root.

    Return absolute paths unchanged, otherwise resolve relative to repo_root.

    Args:
        path: Path to resolve.
        repo_root: Repository root for relative path resolution.

    Returns:
        Resolved absolute path.
    """
    if path.is_absolute():
        return path.expanduser().resolve()
    return (repo_root / path).resolve()


def _iso_to_datetime(value: str | None) -> datetime | None:
    """Parse an ISO format datetime string to a datetime object.

    Handle timezone normalization and return None for invalid inputs.

    Args:
        value: ISO format datetime string or None.

    Returns:
        Parsed datetime in UTC or None if parsing fails.
    """
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    candidate = candidate.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _dir_timestamp(name: str) -> datetime | None:
    """Extract a timestamp from a directory name.

    Strip known prefixes and parse common timestamp formats.

    Args:
        name: Directory name potentially containing a timestamp.

    Returns:
        Parsed datetime in UTC or None if no timestamp found.
    """
    stem = name
    if stem.startswith(CONSUMER_BUNDLE_PREFIX):
        stem = stem[len(CONSUMER_BUNDLE_PREFIX) :]
    if stem.startswith(AGGREGATOR_PREFIX):
        stem = stem[len(AGGREGATOR_PREFIX) :]
    for fmt in ("%Y-%m-%d_%H%M%S", "%Y%m%d%H%M%S"):
        try:
            parsed = datetime.strptime(stem, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=UTC)
    return None


def _classify(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Classify findings and count by risk level.

    Process each finding through the risk classifier and tally results.

    Args:
        findings: Iterable of finding dictionaries.

    Returns:
        Dictionary mapping risk levels to counts.
    """
    counts = {level: 0 for level in RISK_LEVELS}
    for finding in findings:
        risk = classify_monkey_patch(
            FindingSignals(
                category=str(finding.get("category", "")),
                is_test=bool(finding.get("is_test", False)),
                is_module_scope=bool(finding.get("is_module_scope", False)),
            )
        )
        counts[risk] += 1
    return counts


def _complete_counts(counts: dict[str, int]) -> dict[str, int]:
    """Ensure all risk levels have count entries.

    Fill in missing risk levels with zero counts.

    Args:
        counts: Partial or complete risk level counts.

    Returns:
        Complete dictionary with all risk levels.
    """
    return {level: int(counts.get(level, 0)) for level in RISK_LEVELS}


def _load_consumer_runs(
    base_dir: Path,
    summary_override: Path | None,
    logger: logging.Logger,
) -> list[TrendRun]:
    """Load trend runs from consumer bundle directories.

    Scan for timestamped consumer bundles and extract summary data.

    Args:
        base_dir: Base directory containing consumer bundles.
        summary_override: Optional explicit summary path to include.
        logger: Logger for diagnostic messages.

    Returns:
        Sorted list of TrendRun objects from consumer bundles.
    """
    candidates: dict[Path, Path] = {}
    if base_dir.exists():
        for child in base_dir.iterdir():
            if child.is_dir() and child.name.startswith(CONSUMER_BUNDLE_PREFIX):
                candidates[child.resolve()] = child
    if summary_override is not None:
        target = summary_override
        if target.is_file():
            target = target.parent
        if target.is_dir():
            candidates[target.resolve()] = target
    runs: list[TrendRun] = []
    for bundle_dir in sorted(candidates.values(), key=lambda p: p.name):
        summary_path = bundle_dir / CONSUMER_SUMMARY_NAME
        if not summary_path.exists():
            logger.debug("Skipping %s (missing %s)", bundle_dir, CONSUMER_SUMMARY_NAME)
            continue
        try:
            summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read consumer summary %s: %s", summary_path, exc)
            continue
        if not isinstance(summary_data, dict):
            logger.warning("Consumer summary %s must be a JSON object", summary_path)
            continue
        bundle_summary_path = bundle_dir / CONSUMER_BUNDLE_SUMMARY_NAME
        bundle_metadata: dict[str, Any] = {}
        if bundle_summary_path.exists():
            try:
                maybe_meta = json.loads(bundle_summary_path.read_text(encoding="utf-8"))
                if isinstance(maybe_meta, dict):
                    bundle_metadata = maybe_meta
            except Exception as exc:
                logger.warning("Failed to read bundle metadata %s: %s", bundle_summary_path, exc)
        timestamp = (
            _iso_to_datetime(bundle_metadata.get("generated_at"))
            or _dir_timestamp(bundle_dir.name)
            or datetime.fromtimestamp(bundle_dir.stat().st_mtime, UTC)
        )
        ts_label = bundle_metadata.get("generated_at") or timestamp.isoformat(timespec="seconds")
        counts_raw = summary_data.get("counts_by_risk", {})
        counts = _complete_counts(counts_raw if isinstance(counts_raw, dict) else {})
        total = int(summary_data.get("total_findings", sum(counts.values())))
        scan_dir_value = bundle_metadata.get("scan_dir")
        try:
            scan_path = Path(scan_dir_value).resolve() if scan_dir_value else None
        except Exception:
            scan_path = None
        runs.append(
            TrendRun(
                ts_label=ts_label,
                sort_key=timestamp,
                total=total,
                counts=counts,
                bundle_dir=bundle_dir,
                summary_path=summary_path,
                bundle_summary_path=bundle_summary_path if bundle_summary_path.exists() else None,
                scan_dir=scan_path,
                source=str(bundle_metadata.get("source", "consumer")),
                metadata={
                    "bundle_summary": bundle_metadata,
                    "run_metadata": summary_data.get("run_metadata", {}),
                },
            )
        )
    runs.sort(key=lambda run: run.sort_key)
    return runs


def _load_producer_runs(base_dir: Path, logger: logging.Logger) -> list[TrendRun]:
    """Load trend runs from producer report directories.

    Scan for producer scan directories as a fallback when no consumer
    bundles are available.

    Args:
        base_dir: Base directory containing producer scans.
        logger: Logger for diagnostic messages.

    Returns:
        Sorted list of TrendRun objects from producer reports.
    """
    runs: list[TrendRun] = []
    if not base_dir.exists():
        return runs
    for child in sorted(base_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        report_path = child / PRODUCER_REPORT_NAME
        if not report_path.exists():
            continue
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to read producer report %s: %s", report_path, exc)
            continue
        if not isinstance(data, list):
            logger.warning("Producer report %s must contain a list", report_path)
            continue
        counts = _classify(data)
        timestamp = _dir_timestamp(child.name) or datetime.fromtimestamp(child.stat().st_mtime, UTC)
        ts_label = timestamp.isoformat(timespec="seconds")
        runs.append(
            TrendRun(
                ts_label=ts_label,
                sort_key=timestamp,
                total=sum(counts.values()),
                counts=_complete_counts(counts),
                bundle_dir=None,
                summary_path=report_path,
                bundle_summary_path=None,
                scan_dir=child.resolve(),
                source="producer_fallback",
                metadata={"producer_report": str(report_path.resolve())},
            )
        )
    runs.sort(key=lambda run: run.sort_key)
    return runs


def _latest_delta(runs: list[TrendRun]) -> dict[str, Any] | None:
    """Compute the delta between the two most recent runs.

    Compare risk counts between the previous and current runs.

    Args:
        runs: List of TrendRun objects in chronological order.

    Returns:
        Delta dictionary with prev, cur, and delta sections, or None.
    """
    if len(runs) < 2:
        return None
    prev, cur = runs[-2], runs[-1]
    delta = {level: cur.counts.get(level, 0) - prev.counts.get(level, 0) for level in RISK_LEVELS}
    return {
        "prev": {
            "ts": prev.ts_label,
            "total": prev.total,
            "counts": _complete_counts(prev.counts),
        },
        "cur": {
            "ts": cur.ts_label,
            "total": cur.total,
            "counts": _complete_counts(cur.counts),
        },
        "delta": delta,
    }


def _render_markdown(
    *,
    generated_at: datetime,
    mode: str,
    runs: list[TrendRun],
    latest: dict[str, Any] | None,
    notes: list[str],
) -> str:
    """Render the trend summary as markdown.

    Format run overview tables, latest run details, and delta comparison.

    Args:
        generated_at: Generation timestamp.
        mode: Data source mode (consumer or producer_fallback).
        runs: List of TrendRun objects to display.
        latest: Delta comparison dictionary or None.
        notes: List of informational notes to include.

    Returns:
        Markdown-formatted trend summary string.
    """
    lines: list[str] = ["# Monkey Patch Trend Summary", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append(f"Mode: {'Consumer bundles' if mode == 'consumer' else 'Producer fallback'}")
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append("## Run Overview")
    lines.append("")
    if runs:
        lines.append("| Run | Total | HIGH | MODERATE | SAFE |")
        lines.append("|---|---:|---:|---:|---:|")
        for run in runs:
            counts = _complete_counts(run.counts)
            lines.append(
                f"| {run.ts_label} | {run.total} | {counts['HIGH']} | {counts['MODERATE']} | {counts['SAFE']} |"
            )
        lines.append("")
    else:
        lines.append("No runs available.")
        lines.append("")
    if runs:
        latest_run = runs[-1]
        lines.append("## Latest Run Detail")
        lines.append("")
        lines.append(f"- Run: {latest_run.ts_label}")
        lines.append(f"- Source: {latest_run.source}")
        if latest_run.scan_dir:
            lines.append(f"- Scan Dir: `{latest_run.scan_dir}`")
        if latest_run.summary_path:
            lines.append(f"- Summary: `{latest_run.summary_path}`")
        if latest_run.bundle_dir:
            lines.append(f"- Bundle: `{latest_run.bundle_dir}`")
        lines.append("")
    if latest:
        lines.append("## Delta vs Previous")
        lines.append("")
        lines.append("| Level | Prev | Curr | Δ |")
        lines.append("|---|---:|---:|---:|")
        for level in RISK_LEVELS:
            prev_val = latest["prev"]["counts"][level]
            cur_val = latest["cur"]["counts"][level]
            delta_val = latest["delta"][level]
            lines.append(f"| {level} | {prev_val} | {cur_val} | {delta_val:+d} |")
        lines.append("")
        lines.append(f"Total Δ: {latest['cur']['total'] - latest['prev']['total']:+d}")
        lines.append("")
    return "\n".join(lines) + "\n"


def _prune_history(base: Path, current: Path, keep: int, *, logger: logging.Logger | None) -> list[Path]:
    """Prune old aggregator bundle directories.

    Remove older bundles beyond the retention limit, keeping the current run.

    Args:
        base: Base directory containing bundle directories.
        current: Current bundle directory to preserve.
        keep: Number of bundles to retain.
        logger: Logger for pruning messages.

    Returns:
        List of removed directory paths.
    """
    try:
        keep_count = int(keep)
    except Exception:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    if keep_count < 0:
        keep_count = DEFAULT_ARTIFACTS_TO_KEEP
    keep_count = max(keep_count, 1)
    result = prune_run_directories(
        base,
        keep=keep_count,
        stem_prefix=AGGREGATOR_PREFIX,
        current_run=current,
        logger=logger,
    )
    return result.removed


def _copy_markdown_to_consumer(latest_run: TrendRun, trend_md: Path, logger: logging.Logger) -> Path | None:
    """Copy trend markdown to the consumer bundle directory.

    Mirror the trend summary for easy access alongside consumer artifacts.

    Args:
        latest_run: Most recent TrendRun with bundle_dir set.
        trend_md: Path to the trend markdown file.
        logger: Logger for diagnostic messages.

    Returns:
        Path to the copied file or None if copy failed.
    """
    if latest_run.bundle_dir is None:
        return None
    target = latest_run.bundle_dir / CONSUMER_TREND_COPY_NAME
    try:
        target.write_bytes(trend_md.read_bytes())
    except Exception as exc:
        logger.debug("Unable to mirror trend markdown to consumer bundle: %s", exc)
        return None
    return target


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Execute the monkey patch trend analyzer.

    Load consumer or producer runs, compute trends and deltas,
    and write aggregator bundle artifacts.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Result dictionary with paths and processing metadata.

    Raises:
        FileNotFoundError: If no runs are available for analysis.
    """
    args = _parse_args(argv)
    log_level = logging.DEBUG if args.verbose else getattr(logging, str(args.log_level).upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s", force=True)
    logger = logging.getLogger("analyze_monkey_patch_trends")

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))

    consumer_base = _resolve_repo_path(args.consumer_base, repo_root=repo_root)
    consumer_summary = (
        _resolve_repo_path(args.consumer_summary, repo_root=repo_root) if args.consumer_summary is not None else None
    )
    producer_base = _resolve_repo_path(args.producer_base, repo_root=repo_root)
    output_base = _resolve_repo_path(args.output_base, repo_root=repo_root)
    max_runs = max(int(args.max_runs or 0), 1)

    consumer_runs = _load_consumer_runs(consumer_base, consumer_summary, logger)
    mode = "consumer" if consumer_runs else "producer_fallback"
    runs = consumer_runs or _load_producer_runs(producer_base, logger)
    if not runs:
        raise FileNotFoundError("No consumer bundles or producer reports available for trend analysis.")
    runs = runs[-max_runs:]

    generated_at = datetime.now(UTC)
    bundle_dir = output_base / f"{AGGREGATOR_PREFIX}{generated_at.strftime('%Y-%m-%d_%H%M%S')}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    latest = _latest_delta(runs)
    notes: list[str] = []
    if mode != "consumer":
        notes.append("Consumer bundles not found; producer reports used for fallback analysis.")

    trend_json_path = bundle_dir / TREND_JSON_NAME
    trend_md_path = bundle_dir / TREND_MD_NAME
    trend_bundle_summary_path = bundle_dir / AGGREGATOR_BUNDLE_SUMMARY_NAME

    runs_payload = [
        {
            "ts": run.ts_label,
            "total_findings": run.total,
            "counts_by_risk": _complete_counts(run.counts),
            "bundle_dir": str(run.bundle_dir.resolve()) if run.bundle_dir else None,
            "summary_path": str(run.summary_path.resolve()) if run.summary_path else None,
            "bundle_summary": str(run.bundle_summary_path.resolve()) if run.bundle_summary_path else None,
            "scan_dir": str(run.scan_dir) if run.scan_dir else None,
            "source": run.source,
            "metadata": run.metadata,
        }
        for run in runs
    ]

    trend_payload = {
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "mode": mode,
        "requested_keep": int(args.artifacts_to_keep),
        "runs": runs_payload,
        "runs_considered": len(runs_payload),
        "latest": latest,
        "notes": notes,
    }
    trend_json_path.write_text(json.dumps(trend_payload, indent=2) + "\n", encoding="utf-8")

    trend_md = _render_markdown(generated_at=generated_at, mode=mode, runs=runs, latest=latest, notes=notes)
    trend_md_path.write_text(trend_md, encoding="utf-8")

    trend_bundle_summary = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "mode": mode,
        "trend_dir": str(bundle_dir.resolve()),
        "artifacts": {
            "trend_json": str(trend_json_path.resolve()),
            "trend_md": str(trend_md_path.resolve()),
        },
        "inputs": runs_payload,
        "latest": latest,
        "notes": notes,
    }
    trend_bundle_summary_path.write_text(json.dumps(trend_bundle_summary, indent=2) + "\n", encoding="utf-8")

    # HOP compliance: no pointer files
    pruned = _prune_history(output_base, bundle_dir, args.artifacts_to_keep, logger=logger)

    consumer_snapshot = None
    if runs and runs[-1].bundle_dir:
        consumer_snapshot = _copy_markdown_to_consumer(runs[-1], trend_md_path, logger)

    logger.info(
        "Trend bundle written to %s (mode=%s, runs=%d, pruned=%d)",
        bundle_dir,
        mode,
        len(runs),
        len(pruned),
    )

    return {
        "mode": mode,
        "trend_dir": str(bundle_dir.resolve()),
        "trend_json": str(trend_json_path.resolve()),
        "trend_markdown": str(trend_md_path.resolve()),
        "bundle_summary": str(trend_bundle_summary_path.resolve()),
        "latest_run": runs[-1].ts_label,
        "runs": len(runs),
        "pruned": [str(path.resolve()) for path in pruned],
        "consumer_snapshot": str(consumer_snapshot.resolve()) if consumer_snapshot else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the monkey patch trend analyzer.

    Run the analyzer and print results to stdout.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    try:
        result = run(argv)
    except Exception as exc:  # pragma: no cover - unexpected runtime failures
        logging.exception("Failed to analyze monkey patch trends: %s", exc)
        return 1
    import sys

    sys.stdout.write(json.dumps({"status": "OK", **result}) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
