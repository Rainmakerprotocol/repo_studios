#!/usr/bin/env python3
"""Collect structured summaries for pytest log runs.

This producer converts raw pytest log runs (JUnit XML + pytest text output) into
the canonical Repo Studios report bundle:

- manifest.json
- summary.md
- telemetry.json

Outputs follow positional encoding under the configured reports root:
<reports_root>/<viewer_slug>/<topic>/<YYYYMMDD-HHMM>/
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

REPO_STUDIOS_ROOT = ROOT / ".repo_studios"
repo_studios_root_str = str(REPO_STUDIOS_ROOT)
if repo_studios_root_str and repo_studios_root_str not in sys.path:
    sys.path.insert(0, repo_studios_root_str)

LIBRARIES_ROOT = ROOT / ".repo_studios" / "command_center" / "scripts"
libraries_root_str = str(LIBRARIES_ROOT)
if libraries_root_str and libraries_root_str not in sys.path:
    sys.path.insert(0, libraries_root_str)

from libraries import (  # noqa: E402
    TestLogAnalysisResult,
    build_test_log_report,
    prune_run_directories,
)
from libraries.database_integration import create_storage  # noqa: E402

DEFAULT_LOGS_BASE = Path(".repo_studios/command_center/reports/rawview/test_execution_runs")
LEGACY_LOGS_BASE = Path(".repo_studios/pytest_logs")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/healthview")
VIEWER_SLUG = "rawview"
TOPIC_SLUG = "test_log_reports"
DEFAULT_KEEP = 10


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect pytest log summaries into structured artifacts")
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_BASE)
    parser.add_argument("--logs-run", type=Path, default=None, help="Explicit pytest log run directory")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--run-timestamp",
        default=None,
        help="Override run timestamp slug (UTC, YYYYMMDD-HHMM). Useful for deterministic tests.",
    )
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_KEEP)
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args(argv)


def _discover_run_candidates(base: Path) -> list[Path]:
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
        entries = list(current.iterdir())
        has_logs = any(entry.is_file() and entry.name.startswith("pytest") for entry in entries)
        has_junit = any(entry.is_file() and entry.name.startswith("junit") for entry in entries)
        if has_logs or has_junit:
            candidates.append(current)
            continue
        for entry in entries:
            if entry.is_dir():
                stack.append(entry)
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates


def _resolve_run_dir(explicit: Path | None, logs_dir: Path) -> Path | None:
    if explicit is not None:
        return explicit
    candidates = _discover_run_candidates(logs_dir)
    return candidates[0] if candidates else None

def _resolve_timestamp_slug(explicit: str | None) -> str:
    if explicit is None:
        return datetime.now(UTC).strftime("%Y%m%d-%H%M")

    cleaned = explicit.strip()
    if len(cleaned) != 13 or cleaned[8] != "-":
        raise ValueError("run timestamp must be in YYYYMMDD-HHMM format")
    if not (cleaned[:8] + cleaned[9:]).isdigit():
        raise ValueError("run timestamp must be in YYYYMMDD-HHMM format")
    return cleaned


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        resolved = path.resolve()
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return str(path)


def _render_summary_markdown(
    *,
    timestamp: str,
    logs_dir: Path,
    logs_run: Path,
    warnings_total: int,
    slow_count: int,
    tracebacks: int,
    markdown_body: str,
) -> str:
    header = (
        "# Test Log Report\n\n"
        f"- Run slug: {timestamp} (UTC)\n"
        f"- Logs base: {logs_dir.as_posix()}\n"
        f"- Logs run: {logs_run.as_posix()}\n"
        f"- Warnings: {warnings_total}\n"
        f"- Slow tests: {slow_count}\n"
        f"- Tracebacks: {tracebacks}\n\n"
    )
    body = markdown_body.strip()
    return header + (body + "\n" if body else "")


def _write_artifacts(
    result: TestLogAnalysisResult,
    *,
    output_dir: Path,
    timestamp: str,
    logs_dir: Path,
    logs_run: Path,
    keep: int,
    logger: logging.Logger,
) -> Path:
    summary = result.report.get("summary", {}) if isinstance(result.report, dict) else {}
    warnings_total = int(summary.get("warnings_total", 0) or 0)
    tracebacks = int(summary.get("tracebacks", 0) or 0)
    slow_tests = result.report.get("slow_tests", [])
    slow_count = len(slow_tests) if isinstance(slow_tests, list) else 0

    storage = create_storage(output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=timestamp)
    bundle_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG / timestamp

    manifest_path = bundle_dir / "manifest.json"
    summary_path = bundle_dir / "summary.md"
    telemetry_path = bundle_dir / "telemetry.json"

    now_iso = datetime.now(UTC).isoformat()
    repo_root = ROOT

    manifest: dict[str, object] = {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_at": now_iso,
        "status": "ok",
        "git_sha": None,
        "repo_root": str(repo_root),
        "inputs": {
            "logs_dir": _relativize(logs_dir, repo_root),
            "logs_run": _relativize(logs_run, repo_root),
            "allow_legacy": os.environ.get("PYTEST_LOG_REPORTS_ALLOW_LEGACY", "1"),
            "artifacts_to_keep": max(1, keep),
            "run_timestamp": timestamp,
        },
        "catalog": [
            {"artifact": "manifest.json", "path": _relativize(manifest_path, repo_root)},
            {"artifact": "summary.md", "path": _relativize(summary_path, repo_root)},
            {"artifact": "telemetry.json", "path": _relativize(telemetry_path, repo_root)},
        ],
        "provenance": {
            "script": "collect_test_log_reports.py",
            "trigger": "cli",
        },
    }

    telemetry: dict[str, object] = {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_at": now_iso,
        "status": "ok",
        "metrics": {
            "tests_total": int(summary.get("total", 0) or 0),
            "tests_passed": int(summary.get("passed", 0) or 0),
            "tests_failed": int(summary.get("failed", 0) or 0),
            "tests_skipped": int(summary.get("skipped", 0) or 0),
            "tests_xfailed": int(summary.get("xfailed", 0) or 0),
            "tests_errors": int(summary.get("errors", 0) or 0),
            "warnings_total": warnings_total,
            "tracebacks": tracebacks,
            "slow_tests_count": slow_count,
        },
        "inputs": {
            "logs_dir": _relativize(logs_dir, repo_root),
            "logs_run": _relativize(logs_run, repo_root),
        },
        "payload": {
            "summary": summary,
            "warnings": result.report.get("warnings") if isinstance(result.report, dict) else None,
            "slow_tests": slow_tests if isinstance(slow_tests, list) else [],
            "meta": result.report.get("meta") if isinstance(result.report, dict) else None,
        },
    }

    summary_markdown = _render_summary_markdown(
        timestamp=timestamp,
        logs_dir=logs_dir,
        logs_run=logs_run,
        warnings_total=warnings_total,
        slow_count=slow_count,
        tracebacks=tracebacks,
        markdown_body=result.markdown,
    )

    # DB_INTEGRATION_MARKER: Persist manifest bundle (report_runs + report_artifacts)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: Persist human-readable report summary (report_artifacts)
    storage.write_summary({"markdown": summary_markdown}, format="md")
    # DB_INTEGRATION_MARKER: Persist telemetry payload + extracted metrics (report_artifacts + test_metrics)
    storage.write_telemetry(telemetry)

    base_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG
    prune_run_directories(
        base_dir,
        keep=max(1, keep),
        current_run=bundle_dir,
        logger=logger,
    )

    return bundle_dir


def run(argv: Sequence[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s"
    )
    log = logging.getLogger("test_log_reports")

    logs_dir = args.logs_dir if isinstance(args.logs_dir, Path) else Path(args.logs_dir)
    logs_dir = logs_dir if logs_dir.is_absolute() else (Path.cwd() / logs_dir)
    logs_dir = logs_dir.resolve()
    if not logs_dir.exists():
        legacy = LEGACY_LOGS_BASE if LEGACY_LOGS_BASE.is_absolute() else (Path.cwd() / LEGACY_LOGS_BASE)
        legacy = legacy.resolve()
        allow_legacy = os.environ.get("PYTEST_LOG_REPORTS_ALLOW_LEGACY", "1").strip().lower()
        if allow_legacy not in {"0", "false", "no", "off"} and legacy.exists():
            log.info("Logs directory %s missing; falling back to legacy %s", logs_dir, legacy)
            logs_dir = legacy
    logs_run = args.logs_run.resolve() if args.logs_run else _resolve_run_dir(None, logs_dir)
    if logs_run is None or not logs_run.exists():
        log.info("No pytest log runs found under %s", logs_dir)
        return {"run_dir": None, "logs_dir": str(logs_dir), "output_dir": None, "artifacts": None}

    result = build_test_log_report(logs_run, generated=datetime.now(UTC))
    output_dir = args.output_dir.resolve()
    timestamp = _resolve_timestamp_slug(args.run_timestamp)
    artifacts_dir = _write_artifacts(
        result,
        output_dir=output_dir,
        timestamp=timestamp,
        logs_dir=logs_dir,
        logs_run=logs_run,
        keep=args.artifacts_to_keep,
        logger=log,
    )

    summary = result.report.get("summary", {}) if isinstance(result.report, dict) else {}
    warnings_total = int(summary.get("warnings_total", 0) or 0)
    slow_tests = result.report.get("slow_tests", [])
    slow_count = len(slow_tests) if isinstance(slow_tests, list) else 0

    log.info(
        "Pytest log report captured (run=%s, warnings=%s, slow_tests=%s, output=%s)",
        logs_run,
        warnings_total,
        slow_count,
        artifacts_dir,
    )
    return {
        "run_dir": str(logs_run.resolve()),
        "logs_dir": str(logs_dir),
        "output_dir": str(artifacts_dir),
        "warnings_total": warnings_total,
        "slow_tests": slow_count,
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
