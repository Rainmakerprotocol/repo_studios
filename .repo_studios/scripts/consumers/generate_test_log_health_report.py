#!/usr/bin/env python3
"""Test Log Health Report — Warning/Exception Census + Slowest Tests.

Prefers structured bundles emitted by ``collect_test_log_reports.py`` and
falls back to direct log analysis when no producer artifact is available.

Outputs (under ``--output-base/<ts>/``)
- ``report.json``
- ``report.md``
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

LOGS_DIR_DEFAULT = ".repo_studios/pytest_logs"
PRODUCER_REPORT_DEFAULT = ".repo_studios/reports/producer_reports/test_log_reports/latest_report.json"
OUTPUT_BASE_DEFAULT = ".repo_studios/reports/consumer_reports/test_log_health_reports"

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
UTILITIES_ROOT = Path(__file__).resolve().parents[2]
for candidate in (SCRIPTS_ROOT, UTILITIES_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from utilities.test_log_analysis import build_test_log_report, render_markdown  # noqa: E402


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate test log health report")
    parser.add_argument("--logs-dir", default=LOGS_DIR_DEFAULT)
    parser.add_argument("--output-base", default=OUTPUT_BASE_DEFAULT)
    parser.add_argument("--producer-report", default=PRODUCER_REPORT_DEFAULT)
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser.parse_args(argv)


def _ensure_out(base: Path) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_dir = base / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _load_producer_report(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _has_log_artifacts(directory: Path) -> bool:
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
    if _has_log_artifacts(logs_dir):
        return logs_dir
    runs = _discover_log_runs(logs_dir)
    return runs[0] if runs else None


def _empty_report(logs_dir: Path) -> dict[str, Any]:
    generated = datetime.now().isoformat()
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


def _write_artifacts(out_dir: Path, payload: dict[str, Any], markdown: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "report.json"
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(markdown, encoding="utf-8")


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s %(message)s")
    repo_root = Path(".").resolve()

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_absolute():
        logs_dir = (repo_root / logs_dir).resolve()

    out_base = Path(args.output_base)
    if not out_base.is_absolute():
        out_base = (repo_root / out_base).resolve()

    producer_report_path = Path(args.producer_report)
    if not producer_report_path.is_absolute():
        producer_report_path = (repo_root / producer_report_path).resolve()

    payload = None
    source = "producer"
    used_report: Path | None = None
    logs_source: Path | None = None
    if producer_report_path.exists():
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

    out_dir = _ensure_out(out_base)
    _write_artifacts(out_dir, payload, markdown)
    logging.info("Test log health report written to %s (source=%s)", out_dir, source)
    return {
        "output_dir": str(out_dir),
        "source": source,
        "producer_report": str(used_report) if used_report else None,
        "logs_dir": str(logs_dir),
        "logs_source": str(logs_source) if logs_source else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
