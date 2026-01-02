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
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

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
from libraries.cli import resolve_repo_root  # noqa: E402
from libraries.database_integration import create_storage  # noqa: E402
from libraries.report_paths import build_topic_path  # noqa: E402
from libraries.retention_policy import get_keep  # noqa: E402

DEFAULT_LOGS_BASE = Path(".repo_studios/command_center/reports/rawview/test_execution_runs")
LEGACY_LOGS_BASE = Path(".repo_studios/pytest_logs")
TOPIC_SLUG = "test_log_reports"
DEFAULT_OUTPUT_DIR = build_topic_path("rawview", TOPIC_SLUG)
DEFAULT_KEEP = get_keep("collect_test_log_reports")


def _load_element_tree():
    """Load an XML ElementTree implementation with security preference.

    Attempts to import defusedxml for safer XML parsing. Falls back to
    the standard library xml.etree.ElementTree if defusedxml is unavailable.

    Returns:
        The ElementTree module to use for XML parsing.
    """
    try:
        import defusedxml.ElementTree as ElementTree  # type: ignore

        return ElementTree
    except Exception:
        import xml.etree.ElementTree as ElementTree

        return ElementTree


def _bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean value from an environment variable.

    Args:
        name: The environment variable name to read.
        default: Value to return if the variable is not set.

    Returns:
        True unless the value is explicitly falsy (0, false, no, off, or empty).
    """
    value = os.environ.get(name)
    if value is None:
        return default
    cleaned = value.strip().lower()
    return cleaned not in {"0", "false", "no", "off", ""}


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse command-line arguments for the test log collector.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Parsed argument namespace with all CLI options.
    """
    parser = argparse.ArgumentParser(description="Collect pytest log summaries into structured artifacts")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_BASE)
    parser.add_argument("--logs-run", type=Path, default=None, help="Explicit pytest log run directory")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--summarize-existing",
        action="store_true",
        default=False,
        help=(
            "Summarize an existing pytest log run (newest under --logs-dir, or the explicit --logs-run) without "
            "running pytest first."
        ),
    )
    parser.add_argument(
        "--run-pytest",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=(
            "Whether to run pytest first to populate a fresh logs run directory under --logs-dir, then build the "
            "report. Default: true when --logs-run is omitted; false when --logs-run is provided."
        ),
    )
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
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra pytest arguments (pass after '--' when using --run-pytest).",
    )
    return parser.parse_args(argv)


def _discover_run_candidates(base: Path) -> list[Path]:
    """Discover pytest log run directories under a base path.

    Recursively searches for directories containing pytest or junit artifacts,
    sorted by modification time (newest first).

    Args:
        base: The root directory to search for log runs.

    Returns:
        List of directories containing log artifacts, sorted newest first.
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
    """Resolve the pytest log run directory to use.

    Args:
        explicit: An explicitly specified run directory, if any.
        logs_dir: The base logs directory to search if no explicit path.

    Returns:
        The resolved run directory, or None if no runs are found.
    """
    if explicit is not None:
        return explicit
    candidates = _discover_run_candidates(logs_dir)
    return candidates[0] if candidates else None


def _capture_pytest_run(
    *,
    repo_root: Path,
    logs_dir: Path,
    logs_run: Path | None,
    log: logging.Logger,
    pytest_args: Sequence[str],
) -> tuple[Path, int, list[str]]:
    """Execute pytest and capture its output to a log directory.

    Creates a timestamped run directory, executes pytest with JUnit XML output,
    and captures stdout/stderr to a log file.

    Args:
        repo_root: Repository root for pytest execution context.
        logs_dir: Base directory for storing log runs.
        logs_run: Explicit run directory to use, or None to auto-generate.
        log: Logger instance for status messages.
        pytest_args: Additional arguments to pass to pytest.

    Returns:
        Tuple of (run_directory, pytest_exit_code, executed_command).
    """
    logs_dir.mkdir(parents=True, exist_ok=True)

    run_dir = logs_run
    if run_dir is None:
        stamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M")
        run_dir = logs_dir / f"pytest_log_capture-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Keep filenames compatible with existing parsers (startswith pytest/junit).
    junit_name = f"junit_{run_dir.name.replace('pytest_log_capture-', '')}.xml"
    log_name = f"pytest_{run_dir.name.replace('pytest_log_capture-', '')}.txt"
    junit_path = run_dir / junit_name
    pytest_log_path = run_dir / log_name

    args = list(pytest_args or [])
    if args and args[0] == "--":
        args = args[1:]

    has_junitxml = any(str(item).startswith("--junitxml") for item in args)
    cmd = [sys.executable, "-m", "pytest"]
    if not has_junitxml:
        cmd.extend(["--junitxml", str(junit_path)])
    cmd.extend(args)

    log.info("Running pytest to refresh logs: %s", " ".join(cmd))
    with pytest_log_path.open("w", encoding="utf-8", errors="replace") as handle:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_root),
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )

    if completed.returncode != 0:
        log.warning("pytest exited with code %s; proceeding to summarize captured artifacts", completed.returncode)

    return run_dir, int(completed.returncode), [str(item) for item in cmd]


def _extract_failures_from_junit(junit_path: Path | None, limit: int = 25) -> list[dict[str, Any]]:
    """Extract a compact set of failing test identities from a JUnit file.

    This is meant to be decision-grade ("what failed?") while keeping payloads small.
    """

    if junit_path is None or not junit_path.exists():
        return []

    ElementTree = _load_element_tree()
    try:
        root = ElementTree.parse(junit_path).getroot()
    except Exception:
        return []

    failures: list[dict[str, Any]] = []
    for testcase in root.iterfind(".//testcase"):
        failure = testcase.find("failure")
        error = testcase.find("error")
        node = failure if failure is not None else error
        if node is None:
            continue

        classname = testcase.get("classname")
        name = testcase.get("name")
        node_id = "::".join(part for part in [classname, name] if part)
        message = node.get("message")
        text = (node.text or "").strip() or None
        snippet = None
        if text:
            snippet = text.splitlines()[0][:240]

        failures.append(
            {
                "node_id": node_id or name or "(unknown)",
                "classname": classname,
                "name": name,
                "kind": node.tag,
                "message": message,
                "snippet": snippet,
            }
        )
        if len(failures) >= max(1, limit):
            break

    return failures

def _resolve_timestamp_slug(explicit: str | None) -> str:
    """Resolve or generate a timestamp slug for the run directory.

    Args:
        explicit: An explicit timestamp in YYYYMMDD-HHMM format, or None.

    Returns:
        A validated timestamp slug in YYYYMMDD-HHMM format.

    Raises:
        ValueError: If explicit timestamp does not match YYYYMMDD-HHMM format.
    """
    if explicit is None:
        return datetime.now(UTC).strftime("%Y%m%d-%H%M")

    cleaned = explicit.strip()
    if len(cleaned) != 13 or cleaned[8] != "-":
        raise ValueError("run timestamp must be in YYYYMMDD-HHMM format")
    if not (cleaned[:8] + cleaned[9:]).isdigit():
        raise ValueError("run timestamp must be in YYYYMMDD-HHMM format")
    return cleaned


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    """Convert an absolute path to a repo-relative POSIX path string.

    Args:
        path: The path to relativize, or None.
        repo_root: The repository root to compute relative paths from.

    Returns:
        The relative POSIX path string, or the original path as string if
        relativization fails. Returns None if path is None.
    """
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
    logs_run: Path | None,
    warnings_total: int,
    slow_count: int,
    tracebacks: int,
    tests_total: int,
    tests_failed: int,
    pytest_exit_code: int | None,
    markdown_body: str,
) -> str:
    """Render a markdown summary document for the test log report.

    Args:
        timestamp: Run timestamp slug (YYYYMMDD-HHMM).
        logs_dir: Base logs directory path.
        logs_run: Specific run directory path, or None.
        warnings_total: Total warning count from pytest output.
        slow_count: Number of slow tests identified.
        tracebacks: Number of tracebacks detected.
        tests_total: Total test count.
        tests_failed: Failed test count.
        pytest_exit_code: Pytest exit code, or None if not run.
        markdown_body: Pre-rendered markdown body content.

    Returns:
        Complete markdown document with header and body.
    """
    logs_run_display = logs_run.as_posix() if logs_run is not None else "(none)"
    outcome = "unknown"
    if pytest_exit_code is not None:
        outcome = "pass" if pytest_exit_code == 0 else "fail"

    header = (
        "# Test Log Report\n\n"
        f"- Run slug: {timestamp} (UTC)\n"
        f"- Logs base: {logs_dir.as_posix()}\n"
        f"- Logs run: {logs_run_display}\n"
        f"- Pytest exit code: {pytest_exit_code}\n"
        f"- Outcome: {outcome}\n"
        f"- Tests: {tests_total}, failed: {tests_failed}\n"
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
    repo_root: Path,
    timestamp: str,
    logs_dir: Path,
    logs_run: Path | None,
    pytest_ran: bool,
    pytest_exit_code: int | None,
    pytest_command: list[str] | None,
    keep: int,
    logger: logging.Logger,
) -> Path:
    """Write the structured report bundle to the output directory.

    Creates manifest.json, summary.md, and telemetry.json artifacts in a
    timestamped subdirectory. Prunes old runs according to retention policy.

    Args:
        result: The analysis result containing report data and markdown.
        output_dir: Base output directory for report bundles.
        repo_root: Repository root for path relativization.
        timestamp: Run timestamp slug for the bundle directory name.
        logs_dir: Source logs directory for provenance tracking.
        logs_run: Specific run directory analyzed, or None.
        pytest_ran: Whether pytest was executed in this run.
        pytest_exit_code: Pytest exit code, or None if not run.
        pytest_command: The pytest command executed, or None.
        keep: Number of historical run directories to retain.
        logger: Logger instance for status messages.

    Returns:
        Path to the created bundle directory.
    """
    summary = result.report.get("summary", {}) if isinstance(result.report, dict) else {}
    warnings_total = int(summary.get("warnings_total", 0) or 0)
    tracebacks = int(summary.get("tracebacks", 0) or 0)
    slow_tests = result.report.get("slow_tests", [])
    slow_count = len(slow_tests) if isinstance(slow_tests, list) else 0

    tests_total = int(summary.get("total", 0) or 0)
    tests_failed = int(summary.get("failed", 0) or 0)
    tests_errors = int(summary.get("errors", 0) or 0)
    meta = result.report.get("meta", {}) if isinstance(result.report, dict) else {}
    junit_path = None
    full_log_path = None
    if isinstance(meta, dict):
        junit_value = meta.get("junit")
        full_log_value = meta.get("full_log")
        if isinstance(junit_value, str) and junit_value:
            junit_path = Path(junit_value)
        if isinstance(full_log_value, str) and full_log_value:
            full_log_path = Path(full_log_value)

    failures = _extract_failures_from_junit(junit_path)
    has_junit = bool(junit_path and junit_path.exists())
    has_full_log = bool(full_log_path and full_log_path.exists())
    needs_verbose_logs = bool((tests_failed or tests_errors) and tracebacks == 0 and has_full_log)

    status = "ok"
    if logs_run is None:
        status = "no_data"
    elif pytest_exit_code not in (None, 0):
        status = "warn"

    storage = create_storage(output_dir, "", "", timestamp=timestamp)
    bundle_dir = output_dir / timestamp

    manifest_path = bundle_dir / "manifest.json"
    summary_path = bundle_dir / "summary.md"
    telemetry_path = bundle_dir / "telemetry.json"

    now_iso = datetime.now(UTC).isoformat()

    manifest: dict[str, object] = {
        "schema_version": 1,
        "viewer_slug": "rawview",
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_at": now_iso,
        "status": status,
        "git_sha": None,
        "repo_root": str(repo_root),
        "inputs": {
            "logs_dir": _relativize(logs_dir, repo_root),
            "logs_run": _relativize(logs_run, repo_root),
            "allow_legacy": os.environ.get("PYTEST_LOG_REPORTS_ALLOW_LEGACY", "1"),
            "artifacts_to_keep": max(1, keep),
            "run_timestamp": timestamp,
            "pytest_ran": pytest_ran,
            "pytest_exit_code": pytest_exit_code,
            "pytest_command": pytest_command,
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
        "viewer_slug": "rawview",
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_at": now_iso,
        "status": status,
        "metrics": {
            "tests_total": tests_total,
            "tests_passed": int(summary.get("passed", 0) or 0),
            "tests_failed": tests_failed,
            "tests_skipped": int(summary.get("skipped", 0) or 0),
            "tests_xfailed": int(summary.get("xfailed", 0) or 0),
            "tests_errors": tests_errors,
            "warnings_total": warnings_total,
            "tracebacks": tracebacks,
            "slow_tests_count": slow_count,
            "failures_sampled": len(failures),
        },
        "inputs": {
            "logs_dir": _relativize(logs_dir, repo_root),
            "logs_run": _relativize(logs_run, repo_root),
            "pytest_ran": pytest_ran,
            "pytest_exit_code": pytest_exit_code,
            "pytest_command": pytest_command,
        },
        "payload": {
            "summary": summary,
            "quality": {
                "has_junit": has_junit,
                "has_full_log": has_full_log,
                "needs_verbose_logs": needs_verbose_logs,
            },
            "failures": failures,
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
        tests_total=tests_total,
        tests_failed=tests_failed,
        pytest_exit_code=pytest_exit_code,
        markdown_body=result.markdown,
    )

    # DB_INTEGRATION_MARKER: Persist manifest bundle (report_runs + report_artifacts)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: Persist human-readable report summary (report_artifacts)
    storage.write_summary({"markdown": summary_markdown}, format="md")
    # DB_INTEGRATION_MARKER: Persist telemetry payload + extracted metrics (report_artifacts + test_metrics)
    storage.write_telemetry(telemetry)

    prune_run_directories(
        output_dir,
        keep=max(1, keep),
        current_run=bundle_dir,
        logger=logger,
    )

    return bundle_dir


def run(argv: Sequence[str] | None = None) -> dict[str, object]:
    """Execute the test log collection workflow.

    Main entry point for programmatic invocation. Parses arguments, optionally
    runs pytest, analyzes log artifacts, and writes structured report bundles.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Result dictionary containing bundle path, metrics, and status.
    """
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s"
    )
    log = logging.getLogger("test_log_reports")

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    pytest_exit_code: int | None = None
    pytest_command: list[str] | None = None

    logs_dir = args.logs_dir if isinstance(args.logs_dir, Path) else Path(args.logs_dir)
    logs_dir = logs_dir if logs_dir.is_absolute() else (repo_root / logs_dir)
    logs_dir = logs_dir.resolve()

    logs_run_candidate = args.logs_run.resolve() if args.logs_run else None
    run_pytest: bool | None = args.run_pytest
    if args.summarize_existing:
        run_pytest = False
    if run_pytest is None:
        run_pytest = logs_run_candidate is None

    if run_pytest:
        logs_run, pytest_exit_code, pytest_command = _capture_pytest_run(
            repo_root=repo_root,
            logs_dir=logs_dir,
            logs_run=logs_run_candidate,
            log=log,
            pytest_args=args.pytest_args,
        )
    elif not logs_dir.exists():
        legacy = LEGACY_LOGS_BASE if LEGACY_LOGS_BASE.is_absolute() else (repo_root / LEGACY_LOGS_BASE)
        legacy = legacy.resolve()
        allow_legacy = _bool_env("PYTEST_LOG_REPORTS_ALLOW_LEGACY", default=True)
        if allow_legacy and legacy.exists():
            log.info("Logs directory %s missing; falling back to legacy %s", logs_dir, legacy)
            logs_dir = legacy

    if not run_pytest:
        logs_run = logs_run_candidate if logs_run_candidate else _resolve_run_dir(None, logs_dir)

    output_dir = args.output_dir if isinstance(args.output_dir, Path) else Path(args.output_dir)
    output_dir = output_dir if output_dir.is_absolute() else (repo_root / output_dir)
    output_dir = output_dir.resolve()
    timestamp = _resolve_timestamp_slug(args.run_timestamp)

    if logs_run is None or not logs_run.exists():
        log.warning("No pytest log runs found under %s; emitting no-data bundle", logs_dir)
        # build_test_log_report requires a run directory. When none exist, emit a stable
        # zeroed bundle so downstream scripts and agents can make a deterministic choice.
        empty = TestLogAnalysisResult(
            report={
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
            "warnings": {"by_type": {}, "by_file": {}},
            "slow_tests": [],
            "meta": {
                "generated_at": datetime.now(UTC).isoformat(),
                "logs_dir": str(logs_dir),
                "junit": None,
                "full_log": None,
            },
            },
            markdown="## Test Log Health Report\n\n(no data)\n",
        )

        artifacts_dir = _write_artifacts(
            empty,
            output_dir=output_dir,
            repo_root=repo_root,
            timestamp=timestamp,
            logs_dir=logs_dir,
            logs_run=None,
            pytest_ran=bool(run_pytest),
            pytest_exit_code=pytest_exit_code,
            pytest_command=pytest_command,
            keep=args.artifacts_to_keep,
            logger=log,
        )
        return {
            "run_dir": None,
            "logs_dir": str(logs_dir),
            "output_dir": str(artifacts_dir),
            "pytest_ran": bool(run_pytest),
            "pytest_exit_code": pytest_exit_code,
            "pytest_command": pytest_command,
            "status": "no_data",
        }

    result = build_test_log_report(logs_run, generated=datetime.now(UTC))
    artifacts_dir = _write_artifacts(
        result,
        output_dir=output_dir,
        repo_root=repo_root,
        timestamp=timestamp,
        logs_dir=logs_dir,
        logs_run=logs_run,
        pytest_ran=bool(run_pytest),
        pytest_exit_code=pytest_exit_code,
        pytest_command=pytest_command,
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
        "pytest_ran": bool(run_pytest),
        "pytest_exit_code": pytest_exit_code,
        "pytest_command": pytest_command,
        "status": "warn" if pytest_exit_code not in (None, 0) else "ok",
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for the test log collector.

    Args:
        argv: Command-line arguments. Uses sys.argv if None.

    Returns:
        Exit code (always 0 on success).
    """
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
