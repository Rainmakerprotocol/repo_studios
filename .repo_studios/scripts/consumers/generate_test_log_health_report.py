#!/usr/bin/env python3
"""Test Log Health Report — Warning/Exception Census + Slowest Tests.

Prefers structured bundles emitted by ``collect_test_log_reports.py`` and
falls back to direct log analysis when no producer artifact is available.

Outputs (under ``--output-base/<run_slug>/``)
- ``report.json``
- ``report.md``
- ``report.csv``
- ``bundle_summary.json``
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
UTILITIES_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

LIBRARIES_ROOT = ROOT / ".repo_studios" / "command_center" / "scripts"
libraries_root_str = str(LIBRARIES_ROOT)
if libraries_root_str and libraries_root_str not in sys.path:
    sys.path.insert(0, libraries_root_str)

for candidate in (SCRIPTS_ROOT, UTILITIES_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from libraries import (  # noqa: E402
    build_test_log_report,
    prune_run_directories,
    render_markdown,
)
from libraries.cli import resolve_repo_root  # noqa: E402
from libraries.report_paths import build_topic_path  # noqa: E402
from libraries.retention_policy import get_keep  # noqa: E402

LOGS_DIR_DEFAULT = ".repo_studios/reports/healthview/rawview/test_execution_runs"
TOPIC_SLUG = "test_log_health_reports"
PRODUCER_REPORTS_ROOT_DEFAULT = ".repo_studios/reports/healthview/rawview/test_log_reports"
OUTPUT_BASE_DEFAULT = build_topic_path("consumer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_test_log_health_report")

DEFAULT_TIMESTAMP_FORMAT = "%Y%m%d-%H%M"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse command-line arguments for the test log health report.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace with repo_root, logs_dir, output_base, etc.
    """
    parser = argparse.ArgumentParser(description="Generate test log health report")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument("--logs-dir", default=LOGS_DIR_DEFAULT)
    parser.add_argument("--output-base", default=OUTPUT_BASE_DEFAULT)
    parser.add_argument(
        "--producer-bundle-dir",
        default=None,
        help="Path to a collect_test_log_reports bundle directory containing telemetry.json",
    )
    parser.add_argument(
        "--producer-reports-root",
        default=PRODUCER_REPORTS_ROOT_DEFAULT,
        help="Root directory containing timestamped collect_test_log_reports bundles",
    )
    parser.add_argument(
        "--producer-report",
        default=None,
        help="(Legacy) Path to the old-style latest_report.json/report.json producer payload",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of timestamped run directories to retain (including the newest run)",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="ISO8601 timestamp used to derive the run directory slug (YYYYmmdd-HHMM, UTC)",
    )
    return parser.parse_args(argv)


def _timestamp_slug_from_iso(value: str) -> str | None:
    """Convert an ISO8601 timestamp string to a YYYYmmdd-HHMM slug.

    Args:
        value: ISO8601 formatted timestamp string.

    Returns:
        Formatted slug string or None if parsing fails.
    """
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC).strftime(DEFAULT_TIMESTAMP_FORMAT)


def _run_slug(args: argparse.Namespace) -> str:
    """Derive the run directory slug from arguments or current time.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Formatted timestamp slug for the output directory.
    """
    if args.timestamp:
        slug = _timestamp_slug_from_iso(str(args.timestamp))
        if slug:
            return slug
    return datetime.now(UTC).strftime(DEFAULT_TIMESTAMP_FORMAT)


def _ensure_out(base: Path, *, run_slug: str) -> Path:
    """Create and return the output directory for a run.

    Args:
        base: Base output directory path.
        run_slug: Timestamp slug for subdirectory naming.

    Returns:
        Path to the created run directory.
    """
    out_dir = base / run_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _iter_previous_runs(base: Path) -> list[Path]:
    """List previous run directories sorted by name descending.

    Args:
        base: Base output directory to scan.

    Returns:
        List of run directory paths, newest first.
    """
    if not base.exists():
        return []
    runs = [child for child in base.iterdir() if child.is_dir()]
    runs.sort(key=lambda path: path.name, reverse=True)
    return runs


def _load_previous_summary(base: Path) -> tuple[dict[str, Any] | None, Path | None]:
    """Load the most recent previous run summary for comparison.

    Scan previous run directories for bundle_summary.json or report.json.

    Args:
        base: Base output directory containing run subdirectories.

    Returns:
        Tuple of (summary dict, source directory path) or (None, None).
    """
    for run_dir in _iter_previous_runs(base):
        summary_path = run_dir / "bundle_summary.json"
        if summary_path.exists():
            try:
                data = json.loads(summary_path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            if isinstance(data, dict):
                summary = data.get("summary")
                if isinstance(summary, dict):
                    return summary, run_dir
        report_path = run_dir / "report.json"
        if report_path.exists():
            try:
                payload = json.loads(report_path.read_text(encoding="utf-8"))
            except Exception:
                payload = None
            if isinstance(payload, dict):
                summary = payload.get("summary")
                if isinstance(summary, dict):
                    return summary, run_dir
    return None, None


def _pass_rate(summary: dict[str, Any] | None) -> float | None:
    """Calculate pass rate percentage from a summary dictionary.

    Args:
        summary: Summary dict with total and passed counts.

    Returns:
        Pass rate as percentage (0-100) or None if unavailable.
    """
    if not summary:
        return None
    total = summary.get("total")
    passed = summary.get("passed")
    if not isinstance(total, int) or total <= 0:
        return None
    if not isinstance(passed, int):
        return None
    return (passed / total) * 100.0


def _build_comparisons(
    current_summary: dict[str, Any] | None,
    previous_summary: dict[str, Any] | None,
    previous_dir: Path | None,
) -> dict[str, Any]:
    """Build pass rate comparison data between current and previous runs.

    Args:
        current_summary: Summary dict from current run.
        previous_summary: Summary dict from previous run.
        previous_dir: Path to previous run directory.

    Returns:
        Comparison dictionary with pass rates and delta.
    """
    current_rate = _pass_rate(current_summary)
    previous_rate = _pass_rate(previous_summary)
    if current_rate is not None:
        current_rate = round(current_rate, 2)
    if previous_rate is not None:
        previous_rate = round(previous_rate, 2)
    if current_rate is not None and previous_rate is not None:
        delta = round(current_rate - previous_rate, 2)
    else:
        delta = None
    previous_path = str(previous_dir.resolve()) if previous_dir is not None else None
    return {
        "previous_run": {
            "summary_dir": previous_path,
            "pass_rate": {
                "current": current_rate,
                "previous": previous_rate,
                "delta": delta,
            },
        }
    }


def _load_producer_report(path: Path) -> dict[str, Any] | None:
    """Load a legacy producer report JSON file.

    Args:
        path: Path to the report.json file.

    Returns:
        Parsed report dictionary or None if loading fails.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _is_timestamp_slug(name: str) -> bool:
    """Check whether a directory name matches the YYYYmmdd-HHMM format.

    Args:
        name: Directory name to validate.

    Returns:
        True if name is a valid timestamp slug, False otherwise.
    """
    if len(name) != 13 or name[8] != "-":
        return False
    digits = name[:8] + name[9:]
    return digits.isdigit()


def _select_latest_bundle_dir(root: Path) -> Path | None:
    """Select the most recent producer bundle directory.

    Find timestamped subdirectories and return the latest one.

    Args:
        root: Root directory containing timestamped bundle subdirectories.

    Returns:
        Path to the latest bundle directory or None if none found.
    """
    if not root.exists() or not root.is_dir():
        return None
    candidates = [child for child in root.iterdir() if child.is_dir() and _is_timestamp_slug(child.name)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.name)[-1]


def _load_producer_bundle(bundle_dir: Path) -> tuple[dict[str, Any] | None, Path | None]:
    """Load report data from a producer bundle directory.

    Read telemetry.json and extract the payload for health report generation.

    Args:
        bundle_dir: Path to the producer bundle directory.

    Returns:
        Tuple of (report dict, telemetry path) or (None, path) on failure.
    """
    telemetry_path = bundle_dir / "telemetry.json"
    if not telemetry_path.exists():
        return None, None
    try:
        telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    except Exception:
        return None, telemetry_path
    if not isinstance(telemetry, dict):
        return None, telemetry_path
    payload = telemetry.get("payload")
    if not isinstance(payload, dict):
        return None, telemetry_path

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return None, telemetry_path

    report: dict[str, Any] = {
        "schema_version": 1,
        "meta": payload.get("meta") if isinstance(payload.get("meta"), dict) else {},
        "summary": summary,
        "warnings": payload.get("warnings") if isinstance(payload.get("warnings"), dict) else {},
        "slow_tests": payload.get("slow_tests") if isinstance(payload.get("slow_tests"), list) else [],
    }
    return report, telemetry_path


def _has_log_artifacts(directory: Path) -> bool:
    """Check whether a directory contains pytest or junit log files.

    Args:
        directory: Directory path to inspect.

    Returns:
        True if pytest/junit artifacts are found, False otherwise.
    """
    try:
        for entry in directory.iterdir():
            if not entry.is_file():
                continue
            name = entry.name
            if name.startswith("pytest") or name.startswith("junit"):
                return True
    except FileNotFoundError:
        return False
    except PermissionError:
        return False
    return False


def _discover_log_runs(base: Path) -> list[Path]:
    """Discover all directories containing log artifacts under a base path.

    Recursively scan for directories with pytest/junit files.

    Args:
        base: Base directory to search.

    Returns:
        List of directories with log artifacts, sorted by mtime descending.
    """
    if not base.exists():
        return []
    seen: set[Path] = set()
    candidates: list[Path] = []
    stack: list[Path] = [base]
    while stack:
        current = stack.pop()
        if current in seen or not current.exists():
            continue
        seen.add(current)
        if not current.is_dir():
            continue
        if _has_log_artifacts(current):
            candidates.append(current)
            continue
        try:
            for entry in current.iterdir():
                if entry.is_dir():
                    stack.append(entry)
        except (FileNotFoundError, PermissionError):
            continue
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates


def _select_logs_dir(logs_dir: Path) -> Path | None:
    """Select the most relevant log directory from a base path.

    Return the base if it has artifacts, otherwise discover subdirectories.

    Args:
        logs_dir: Base log directory path.

    Returns:
        Path to directory with log artifacts or None.
    """
    if _has_log_artifacts(logs_dir):
        return logs_dir
    runs = _discover_log_runs(logs_dir)
    return runs[0] if runs else None


def _empty_report(logs_dir: Path) -> dict[str, Any]:
    """Create an empty report structure when no logs are available.

    Args:
        logs_dir: Path to the logs directory for metadata.

    Returns:
        Dictionary with zero-value summary and empty collections.
    """
    generated = datetime.now(UTC).isoformat()
    return {
        "schema_version": 1,
        "meta": {
            "generated_at": generated,
            "logs_dir": str(logs_dir),
            "junit": None,
            "full_log": None,
        },
        "summary": {
            "total": 0,
            "passed": 0,
            "skipped": 0,
            "xfailed": 0,
            "failed": 0,
            "errors": 0,
            "warnings_total": 0,
            "tracebacks": 0,
        },
        "warnings": {
            "by_type": {},
            "by_file": {},
        },
        "slow_tests": [],
    }


def _append_delta_markdown(markdown: str, comparisons: dict[str, Any]) -> str:
    """Append pass rate delta section to markdown report.

    Args:
        markdown: Existing markdown content.
        comparisons: Comparison data with pass rate deltas.

    Returns:
        Updated markdown with delta section appended.
    """
    lines = markdown.rstrip("\n").splitlines()
    lines.append("")
    lines.append("## Pass Rate Delta")
    lines.append("")
    pass_rate = comparisons.get("previous_run", {}).get("pass_rate", {})
    current = pass_rate.get("current")
    previous = pass_rate.get("previous")
    delta = pass_rate.get("delta")
    if previous is None:
        lines.append("- Previous pass rate: N/A")
    else:
        lines.append(f"- Previous pass rate: {previous:.2f}%")
    if current is None:
        lines.append("- Current pass rate: N/A")
    else:
        lines.append(f"- Current pass rate: {current:.2f}%")
    if delta is None:
        lines.append("- Delta: N/A")
    else:
        lines.append(f"- Delta: {delta:+.2f} percentage points")
    return "\n".join(lines) + "\n"


def _inject_markdownlint_exception(markdown: str) -> str:
    """Prepend markdownlint disable comment to markdown content.

    Disable MD013 (line length) for generated reports.

    Args:
        markdown: Markdown content to modify.

    Returns:
        Markdown with lint exception comment at the top.
    """
    prefix = "<!-- markdownlint-disable MD013 MD041 -->"
    stripped = markdown.lstrip()
    if markdown.startswith(prefix):
        return markdown if markdown.endswith("\n") else markdown + "\n"
    if stripped.startswith(prefix):
        return markdown if markdown.endswith("\n") else markdown + "\n"
    if markdown.startswith("#"):
        return prefix + "\n" + markdown if markdown.endswith("\n") else prefix + "\n" + markdown + "\n"
    return prefix + "\n" + markdown if markdown.endswith("\n") else prefix + "\n" + markdown + "\n"


def _write_csv(out_dir: Path, payload: dict[str, Any], comparisons: dict[str, Any]) -> Path:
    """Write report data to a CSV file.

    Export summary metrics, pass rates, and slow test details.

    Args:
        out_dir: Output directory for the CSV file.
        payload: Report payload with summary and slow_tests.
        comparisons: Comparison data with pass rates.

    Returns:
        Path to the written CSV file.
    """
    summary = payload.get("summary") or {}
    pass_rate = comparisons.get("previous_run", {}).get("pass_rate", {})
    slow_tests = payload.get("slow_tests") or []
    csv_path = out_dir / "report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for field in (
            "total",
            "passed",
            "skipped",
            "xfailed",
            "failed",
            "errors",
            "warnings_total",
            "tracebacks",
        ):
            writer.writerow([field, summary.get(field, 0)])
        writer.writerow(["pass_rate_current_pct", "{0:.2f}".format(pass_rate.get("current")) if pass_rate.get("current") is not None else "N/A"])
        writer.writerow(["pass_rate_previous_pct", "{0:.2f}".format(pass_rate.get("previous")) if pass_rate.get("previous") is not None else "N/A"])
        writer.writerow(["pass_rate_delta_pct", "{0:+.2f}".format(pass_rate.get("delta")) if pass_rate.get("delta") is not None else "N/A"])
        writer.writerow(["slow_tests_count", len(slow_tests)])
        for idx, entry in enumerate(slow_tests, start=1):
            nodeid = entry.get("nodeid") or ""
            seconds = entry.get("seconds")
            writer.writerow([f"slow_test_{idx}", f"{seconds}s {nodeid}" if seconds is not None else nodeid])
    return csv_path


def _write_artifacts(
    out_dir: Path,
    payload: dict[str, Any],
    markdown: str,
    *,
    comparisons: dict[str, Any],
) -> Path:
    """Write all report artifacts to the output directory.

    Generate report.json, report.md, and report.csv files.

    Args:
        out_dir: Output directory for artifacts.
        payload: Report payload dictionary.
        markdown: Markdown report content.
        comparisons: Comparison data for delta section.

    Returns:
        Path to the written CSV file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "report.json"
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    updated_markdown = _append_delta_markdown(markdown, comparisons)
    updated_markdown = _inject_markdownlint_exception(updated_markdown)
    (out_dir / "report.md").write_text(updated_markdown, encoding="utf-8")
    csv_path = _write_csv(out_dir, payload, comparisons)
    return csv_path


def _write_metadata(
    out_dir: Path,
    *,
    source: str,
    producer_bundle_dir: Path | None,
    producer_telemetry: Path | None,
    producer_report: Path | None,
    logs_dir: Path,
    logs_source: Path | None,
    summary: dict[str, Any] | None,
    comparisons: dict[str, Any],
) -> Path:
    """Write bundle summary metadata and update markdown with source references.

    Args:
        out_dir: Output directory for metadata.
        source: Data source type (producer or logs).
        producer_bundle_dir: Path to producer bundle if used.
        producer_telemetry: Path to telemetry.json if used.
        producer_report: Path to legacy report.json if used.
        logs_dir: Configured logs directory.
        logs_source: Actual logs source directory.
        summary: Report summary dictionary.
        comparisons: Comparison data.

    Returns:
        Path to the written bundle_summary.json file.
    """
    generated = datetime.now(UTC)
    metadata = {
        "schema_version": 1,
        "generated_at": generated.isoformat(timespec="seconds"),
        "source": source,
        "producer_bundle_dir": str(producer_bundle_dir.resolve()) if producer_bundle_dir else None,
        "producer_telemetry": str(producer_telemetry.resolve()) if producer_telemetry else None,
        "producer_report": str(producer_report.resolve()) if producer_report else None,
        "logs_dir": str(logs_dir.resolve()),
        "logs_source": str(logs_source.resolve()) if logs_source else None,
        "artifacts": {
            "report_json": str((out_dir / "report.json").resolve()),
            "report_md": str((out_dir / "report.md").resolve()),
            "report_csv": str((out_dir / "report.csv").resolve()),
        },
        "summary": summary,
        "comparisons": comparisons,
    }
    meta_path = out_dir / "bundle_summary.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    md_path = out_dir / "report.md"
    if md_path.exists():
        lines = md_path.read_text(encoding="utf-8").rstrip("\n").splitlines()
        lines.append("")
        lines.append("## Source References")
        lines.append("")
        lines.append(f"- Source: {source}")
        if producer_bundle_dir:
            lines.append(f"- Producer Bundle: `{producer_bundle_dir.resolve()}`")
        if producer_telemetry:
            lines.append(f"- Producer Telemetry: `{producer_telemetry.resolve()}`")
        if producer_report:
            lines.append(f"- Producer Report: `{producer_report.resolve()}`")
        if logs_source:
            lines.append(f"- Logs Source: `{logs_source.resolve()}`")
        lines.append(f"- Logs Directory: `{logs_dir.resolve()}`")
        csv_path = out_dir / "report.csv"
        if csv_path.exists():
            lines.append(f"- CSV Export: `{csv_path.resolve()}`")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return meta_path


def _prune_history(base: Path, keep: int | None, current: Path, *, logger: logging.Logger | None) -> list[Path]:
    """Remove old run directories beyond the retention threshold.

    Args:
        base: Base output directory containing run subdirectories.
        keep: Number of runs to retain (minimum 1).
        current: Current run directory to preserve.
        logger: Logger for debug output.

    Returns:
        List of removed directory paths.
    """
    if keep is None:
        return []
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
        current_run=current,
        logger=logger,
    )
    return result.removed


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Execute the test log health report generation pipeline.

    Parse arguments, load or analyze logs, build comparisons, and write artifacts.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Dictionary containing output paths and metadata.
    """
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
        force=True,
    )
    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_absolute():
        logs_dir = (repo_root / logs_dir).resolve()
    else:
        logs_dir = logs_dir.resolve()

    out_base = Path(args.output_base)
    if not out_base.is_absolute():
        out_base = (repo_root / out_base).resolve()

    producer_bundle_dir: Path | None = None
    producer_telemetry: Path | None = None
    producer_report_path: Path | None = None
    if args.producer_report:
        candidate = Path(args.producer_report)
        producer_report_path = candidate if candidate.is_absolute() else (repo_root / candidate).resolve()

    producer_reports_root = Path(args.producer_reports_root)
    if not producer_reports_root.is_absolute():
        producer_reports_root = (repo_root / producer_reports_root).resolve()
    else:
        producer_reports_root = producer_reports_root.resolve()

    if args.producer_bundle_dir:
        candidate = Path(args.producer_bundle_dir)
        producer_bundle_dir = candidate if candidate.is_absolute() else (repo_root / candidate).resolve()

    payload = None
    source = "producer"
    used_report: Path | None = None
    used_bundle: Path | None = None
    logs_source: Path | None = None
    if producer_bundle_dir is None:
        producer_bundle_dir = _select_latest_bundle_dir(producer_reports_root)
    if producer_bundle_dir is not None and producer_bundle_dir.exists():
        payload, producer_telemetry = _load_producer_bundle(producer_bundle_dir)
        if payload is not None:
            used_bundle = producer_bundle_dir
            logging.info("Loaded pytest log bundle from %s", producer_bundle_dir)

    if payload is None and producer_report_path is not None and producer_report_path.exists():
        payload = _load_producer_report(producer_report_path)
        if payload is not None:
            used_report = producer_report_path
            logging.info("Loaded pytest log bundle from %s", producer_report_path)
    if payload is None:
        source = "logs"
        logging.info("Structured pytest log report not found; analyzing logs under %s", logs_dir)
        logs_source = _select_logs_dir(logs_dir)
        if logs_source is None:
            logging.info("No pytest artifacts discovered under %s; emitting empty report", logs_dir)
            payload = _empty_report(logs_dir)
            markdown = render_markdown(payload)
        else:
            result = build_test_log_report(logs_source)
            payload = result.report
            markdown = result.markdown
    else:
        markdown = render_markdown(payload)

    previous_summary, previous_dir = _load_previous_summary(out_base)
    out_dir = _ensure_out(out_base, run_slug=_run_slug(args))
    summary = payload.get("summary") if isinstance(payload, dict) else None
    comparisons = _build_comparisons(summary, previous_summary, previous_dir)
    payload = dict(payload)
    payload["comparisons"] = comparisons
    csv_path = _write_artifacts(out_dir, payload, markdown, comparisons=comparisons)
    summary = payload.get("summary") if isinstance(payload, dict) else None
    metadata_path = _write_metadata(
        out_dir,
        source=source,
        producer_bundle_dir=used_bundle,
        producer_telemetry=producer_telemetry,
        producer_report=used_report,
        logs_dir=logs_dir,
        logs_source=logs_source,
        summary=summary,
        comparisons=comparisons,
    )
    log = logging.getLogger("test_log_health")
    pruned = _prune_history(out_base, args.artifacts_to_keep, out_dir, logger=log)
    log.info(
        "Test log health report written to %s (source=%s, pruned=%d)",
        out_dir,
        source,
        len(pruned),
    )
    return {
        "status": "ok",
        "output_dir": str(out_dir.resolve()),
        "source": source,
        "producer_bundle_dir": str(used_bundle) if used_bundle else None,
        "producer_telemetry": str(producer_telemetry) if producer_telemetry else None,
        "producer_report": str(used_report) if used_report else None,
        "logs_dir": str(logs_dir.resolve()),
        "logs_source": str(logs_source.resolve()) if logs_source else None,
        "bundle_summary": str(metadata_path.resolve()),
        "artifacts_root": str(out_base.resolve()),
        "report_csv": str(csv_path.resolve()),
        "pruned": [str(p.resolve()) for p in pruned],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the test log health report script.

    Execute run() and return success exit code.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (always 0 on success).
    """
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
