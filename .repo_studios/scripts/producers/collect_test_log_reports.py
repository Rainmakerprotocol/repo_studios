#!/usr/bin/env python3
"""Collect structured summaries for pytest log runs."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from utilities.test_log_analysis import TestLogAnalysisResult, build_test_log_report  # noqa: E402

DEFAULT_LOGS_BASE = Path(".repo_studios/pytest_logs")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/test_log_reports")
RUN_PREFIX = "test_log_report"
DEFAULT_KEEP = 10


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect pytest log summaries into structured artifacts")
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_BASE)
    parser.add_argument("--logs-run", type=Path, default=None, help="Explicit pytest log run directory")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
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


def _format_timestamp(ts: datetime) -> str:
    return ts.strftime("%Y%m%d_%H%M%S")


def _ensure_run_dir(output_dir: Path, generated_at: str | None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    if generated_at:
        try:
            parsed = datetime.fromisoformat(generated_at)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
        except Exception:
            parsed = datetime.now(UTC)
    else:
        parsed = datetime.now(UTC)
    run_dir = output_dir / f"{RUN_PREFIX}-{_format_timestamp(parsed)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_json(run_dir: Path, result: TestLogAnalysisResult) -> Path:
    path = run_dir / "report.json"
    path.write_text(json.dumps(result.report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_markdown(run_dir: Path, result: TestLogAnalysisResult) -> Path:
    path = run_dir / "report.md"
    path.write_text(result.markdown, encoding="utf-8")
    return path


def _write_counter_csv(run_dir: Path, counter: dict[str, int], name: str) -> Path:
    path = run_dir / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if name == "warnings_by_type":
            writer.writerow(["type", "count"])
        elif name == "warnings_by_file":
            writer.writerow(["file", "count"])
        else:
            writer.writerow(["key", "count"])
        for key, value in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
            writer.writerow([key, value])
    return path


def _write_slow_tests_csv(run_dir: Path, slow_tests: list[dict[str, object]]) -> Path:
    path = run_dir / "slow_tests.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["seconds", "nodeid"])
        writer.writeheader()
        for item in slow_tests:
            writer.writerow(
                {
                    "seconds": f"{float(item.get('seconds', 0.0)):.3f}",
                    "nodeid": str(item.get("nodeid", "?")),
                }
            )
    return path


def _write_combined_log(run_dir: Path, report: dict[str, object]) -> Path | None:
    combined_source = report.get("meta", {}).get("full_log")
    if not combined_source:
        return None
    try:
        source_path = Path(str(combined_source)).resolve()
    except Exception:
        return None
    if not source_path.exists():
        return None
    dest = run_dir / "combined.log"
    try:
        shutil.copy2(source_path, dest)
    except Exception:
        return None
    return dest


def _update_latest(output_dir: Path, run_dir: Path) -> None:
    latest_pairs = {
        "report.json": output_dir / "latest_report.json",
        "report.md": output_dir / "latest_report.md",
        "warnings_by_type.csv": output_dir / "latest_warnings_by_type.csv",
        "warnings_by_file.csv": output_dir / "latest_warnings_by_file.csv",
        "slow_tests.csv": output_dir / "latest_slow_tests.csv",
        "combined.log": output_dir / "latest_combined.log",
    }
    for name, dest in latest_pairs.items():
        src = run_dir / name
        if not src.exists():
            continue
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)
        except Exception:
            dest.write_bytes(src.read_bytes())


def _prune_old_runs(output_dir: Path, keep: int, current_run: Path) -> list[Path]:
    keep = max(1, keep)
    if not output_dir.exists():
        return []
    runs = [child for child in output_dir.iterdir() if child.is_dir() and child.name.startswith(RUN_PREFIX)]
    runs.sort(key=lambda path: path.name, reverse=True)
    removed: list[Path] = []
    for index, path in enumerate(runs):
        if index < keep or path == current_run:
            continue
        try:
            shutil.rmtree(path)
            removed.append(path)
        except Exception:
            continue
    return removed


def _write_artifacts(result: TestLogAnalysisResult, output_dir: Path, *, keep: int) -> Path:
    generated_at = str(result.report.get("meta", {}).get("generated_at")) if result.report.get("meta") else None
    run_dir = _ensure_run_dir(output_dir, generated_at)
    report_json = _write_json(run_dir, result)
    _ = report_json  # suppress unused warning in linters
    _write_markdown(run_dir, result)
    warnings = result.report.get("warnings", {})
    by_type_data = warnings.get("by_type", {}) if isinstance(warnings, dict) else {}
    by_file_data = warnings.get("by_file", {}) if isinstance(warnings, dict) else {}
    if not isinstance(by_type_data, dict):
        by_type_data = dict(by_type_data.items()) if hasattr(by_type_data, "items") else {}
    if not isinstance(by_file_data, dict):
        by_file_data = dict(by_file_data.items()) if hasattr(by_file_data, "items") else {}
    _write_counter_csv(run_dir, by_type_data, "warnings_by_type")
    _write_counter_csv(run_dir, by_file_data, "warnings_by_file")
    slow_tests = result.report.get("slow_tests", [])
    if not isinstance(slow_tests, list):
        slow_tests = []
    _write_slow_tests_csv(run_dir, slow_tests)
    _write_combined_log(run_dir, result.report)
    _update_latest(output_dir, run_dir)
    _prune_old_runs(output_dir, keep, run_dir)
    return run_dir


def run(argv: Sequence[str] | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s"
    )
    log = logging.getLogger("test_log_reports")

    logs_dir = args.logs_dir.resolve()
    logs_run = args.logs_run.resolve() if args.logs_run else _resolve_run_dir(None, logs_dir)
    if logs_run is None or not logs_run.exists():
        log.info("No pytest log runs found under %s", logs_dir)
        return {"run_dir": None, "logs_dir": str(logs_dir), "output_dir": None, "artifacts": None}

    result = build_test_log_report(logs_run, generated=datetime.now(UTC))
    output_dir = args.output_dir.resolve()
    artifacts_dir = _write_artifacts(result, output_dir, keep=args.artifacts_to_keep)

    summary = result.report.get("summary", {}) if isinstance(result.report, dict) else {}
    warnings_total = summary.get("warnings_total", 0)
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
