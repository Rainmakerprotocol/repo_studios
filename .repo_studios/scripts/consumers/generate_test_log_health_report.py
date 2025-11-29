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
import csv
import json
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

LOGS_DIR_DEFAULT = ".repo_studios/reports/orchestrator_logs/pytest_log_capture_logs"
LEGACY_LOGS_DIR = ".repo_studios/pytest_logs"
PRODUCER_REPORT_DEFAULT = ".repo_studios/reports/producer_reports/test_log_reports/latest_report.json"
OUTPUT_BASE_DEFAULT = ".repo_studios/reports/consumer_reports/test_log_health_reports"
DEFAULT_ARTIFACTS_TO_KEEP = 5

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
UTILITIES_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(__file__).resolve().parents[3]
root_str = str(ROOT)
if root_str and root_str not in sys.path:
    sys.path.insert(0, root_str)

LIBRARIES_ROOT = ROOT / "command_center" / "scripts"
libraries_root_str = str(LIBRARIES_ROOT)
if libraries_root_str and libraries_root_str not in sys.path:
    sys.path.insert(0, libraries_root_str)

for candidate in (SCRIPTS_ROOT, UTILITIES_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from utilities.test_log_analysis import build_test_log_report, render_markdown  # noqa: E402
from command_center.scripts.libraries import prune_run_directories  # noqa: E402


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
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of timestamped run directories to retain (including the newest run)",
    )
    return parser.parse_args(argv)


def _ensure_out(base: Path) -> Path:
    ts = datetime.now(UTC).strftime("%Y-%m-%d_%H%M")
    out_dir = base / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _iter_previous_runs(base: Path) -> list[Path]:
    if not base.exists():
        return []
    runs = [child for child in base.iterdir() if child.is_dir()]
    runs.sort(key=lambda path: path.name, reverse=True)
    return runs


def _load_previous_summary(base: Path) -> tuple[dict[str, Any] | None, Path | None]:
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


def _allow_legacy_logs() -> bool:
    flag = os.environ.get("TEST_LOG_HEALTH_ALLOW_LEGACY", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _resolve_legacy_logs_base(repo_root: Path) -> Path:
    base = Path(LEGACY_LOGS_DIR)
    if not base.is_absolute():
        base = (repo_root / base).resolve()
    return base


def _empty_report(logs_dir: Path) -> dict[str, Any]:
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
    prefix = "<!-- markdownlint-disable MD013 -->"
    stripped = markdown.lstrip()
    if markdown.startswith(prefix):
        return markdown if markdown.endswith("\n") else markdown + "\n"
    if stripped.startswith(prefix):
        return markdown if markdown.endswith("\n") else markdown + "\n"
    if markdown.startswith("#"):
        return prefix + "\n" + markdown if markdown.endswith("\n") else prefix + "\n" + markdown + "\n"
    return prefix + "\n" + markdown if markdown.endswith("\n") else prefix + "\n" + markdown + "\n"


def _write_csv(out_dir: Path, payload: dict[str, Any], comparisons: dict[str, Any]) -> Path:
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
    producer_report: Path | None,
    logs_dir: Path,
    logs_source: Path | None,
    summary: dict[str, Any] | None,
    comparisons: dict[str, Any],
) -> Path:
    generated = datetime.now(UTC)
    metadata = {
        "schema_version": 1,
        "generated_at": generated.isoformat(timespec="seconds"),
        "source": source,
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
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
        force=True,
    )
    repo_root = Path(".").resolve()

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_absolute():
        logs_dir = (repo_root / logs_dir).resolve()
    else:
        logs_dir = logs_dir.resolve()

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
        if logs_source is None and _allow_legacy_logs():
            legacy_base = _resolve_legacy_logs_base(repo_root)
            if legacy_base.exists():
                legacy_candidate = _select_logs_dir(legacy_base)
                if legacy_candidate is not None:
                    logging.info(
                        "Logs directory %s missing artifacts; falling back to legacy %s",
                        logs_dir,
                        legacy_base,
                    )
                    logs_dir = legacy_base
                    logs_source = legacy_candidate
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
    out_dir = _ensure_out(out_base)
    summary = payload.get("summary") if isinstance(payload, dict) else None
    comparisons = _build_comparisons(summary, previous_summary, previous_dir)
    payload = dict(payload)
    payload["comparisons"] = comparisons
    csv_path = _write_artifacts(out_dir, payload, markdown, comparisons=comparisons)
    summary = payload.get("summary") if isinstance(payload, dict) else None
    metadata_path = _write_metadata(
        out_dir,
        source=source,
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
        "output_dir": str(out_dir.resolve()),
        "source": source,
        "producer_report": str(used_report) if used_report else None,
        "logs_dir": str(logs_dir.resolve()),
        "logs_source": str(logs_source.resolve()) if logs_source else None,
        "bundle_summary": str(metadata_path.resolve()),
        "artifacts_root": str(out_base.resolve()),
        "report_csv": str(csv_path.resolve()),
        "pruned": [str(p.resolve()) for p in pruned],
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
