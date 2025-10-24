#!/usr/bin/env python3
"""Inventory health validation with structured artifacts.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/inventory_health_reports/`
        - `inventory_health-<timestamp>/report.json`
        - `inventory_health-<timestamp>/report.md`
        - `inventory_health-<timestamp>/log.txt`
        - `latest_report.(json|md|log)` copies for quick access

Exit codes:
    0 success (no threshold breaches)
    1 threshold breach detected
    2 summary input missing
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
SUMMARY_LATEST = ROOT / "reports" / "summary" / "latest" / "summary.json"
BASELINE_PATH = ROOT / "reports" / "summary" / "main_baseline.json"
THRESHOLD_PATH = ROOT / "config" / "ci_inventory_thresholds.json"

DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/inventory_health_reports"
)
RUN_PREFIX = "inventory_health"
DEFAULT_ARTIFACTS_TO_KEEP = 10

JsonDict = Dict[str, Any]


def load_json(path: Path) -> JsonDict:
    if not path.exists():
        logging.debug("JSON source missing: %s", path)
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - guarded by CI inputs
        logging.error("failed to parse JSON from %s: %s", path, exc)
        return {}


def compute_deltas(current: JsonDict, baseline: JsonDict) -> JsonDict:
    deltas: JsonDict = {}
    for key in ("total",):
        if key in current and key in baseline:
            try:
                deltas[key] = int(current[key]) - int(baseline[key])
            except (TypeError, ValueError):
                logging.debug("non-numeric delta skipped for key: %s", key)
    return deltas


def check_thresholds(current: JsonDict, thresholds: JsonDict) -> Dict[str, str]:
    issues: Dict[str, str] = {}

    status_limits = thresholds.get("status_limits", {}) or {}
    for status, limit in status_limits.items():
        value = current.get("by_status", {}).get(status, 0)
        if value > limit:
            issues[f"status:{status}"] = (
                f"Status '{status}' count {value} exceeds limit {limit}"
            )

    minimum_assets = thresholds.get("minimum_assets", {}) or {}
    for asset_kind, minimum in minimum_assets.items():
        value = current.get("by_asset_kind", {}).get(asset_kind, 0)
        if value < minimum:
            issues[f"asset:{asset_kind}"] = (
                f"Asset kind '{asset_kind}' count {value} below minimum {minimum}"
            )

    consumer_required = thresholds.get("consumer_required", []) or []
    consumers = current.get("consumers", {}) or {}
    for consumer in consumer_required:
        if consumers.get(consumer, 0) == 0:
            issues[f"consumer:{consumer}"] = (
                f"Consumer '{consumer}' missing from summary"
            )

    return issues


def evaluate(
    current: JsonDict, baseline: JsonDict, thresholds: JsonDict
) -> tuple[str, Dict[str, str], JsonDict]:
    issues = check_thresholds(current, thresholds)
    deltas = compute_deltas(current, baseline)
    status = "failed" if issues else "passed"
    return status, issues, deltas


def parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_latest(src: Path, dest: Path) -> None:
    try:
        if dest.exists():
            dest.unlink()
        dest.hardlink_to(src)
    except OSError:
        dest.write_bytes(src.read_bytes())


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    candidates.sort(key=lambda p: p.name, reverse=True)
    for index, path in enumerate(candidates):
        if index < keep or path == current_run:
            continue
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)  # type: ignore[attr-defined]
        path.rmdir()


def build_report(
    *,
    status: str,
    issues: Dict[str, str],
    deltas: JsonDict,
    current: JsonDict,
    baseline: JsonDict,
    thresholds: JsonDict,
    generated_ts: datetime,
    summary_path: Path,
    baseline_path: Path,
    thresholds_path: Path,
) -> JsonDict:
    issue_list = [
        {"id": key, "description": message}
        for key, message in sorted(issues.items())
    ]
    delta_list = [
        {"metric": key, "delta": value}
        for key, value in sorted(deltas.items())
    ]
    summary = {
        "status": status,
        "issues": len(issue_list),
        "total_assets": current.get("total"),
    }
    return {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "status": status,
        "summary": summary,
        "summary_path": str(summary_path),
        "baseline_path": str(baseline_path),
        "thresholds_path": str(thresholds_path),
        "issues": issue_list,
        "deltas": delta_list,
        "current_snapshot": current,
        "baseline_snapshot": baseline,
        "threshold_snapshot": thresholds,
    }


def write_markdown(report: JsonDict) -> str:
    lines = [
        "# Inventory Health Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Summary Path: {report['summary_path']}",
        f"Baseline Path: {report['baseline_path']}",
        f"Threshold Path: {report['thresholds_path']}",
        "",
        "## Outcome",
        "",
        f"* status: {report['status']}",
        f"* issues: {report['summary']['issues']}",
        f"* total assets: {report['summary']['total_assets']}",
        "",
        "## Deltas",
        "",
    ]
    deltas = report.get("deltas", [])
    if not deltas:
        lines.append("- (none)")
    else:
        for item in deltas:
            lines.append(f"- {item['metric']}: {item['delta']:+d}")

    lines.extend(["", "## Issues", ""])
    issues = report.get("issues", [])
    if not issues:
        lines.append("- (none)")
    else:
        for issue in issues:
            lines.append(f"- {issue['id']}: {issue['description']}")

    return "\n".join(lines) + "\n"


def write_log(report: JsonDict) -> str:
    lines = [
        f"status={report['status']}",
        f"issues={report['summary']['issues']}",
        f"total_assets={report['summary']['total_assets']}",
        "deltas:",
    ]
    for item in report.get("deltas", []):
        lines.append(f"  {item['metric']}={item['delta']:+d}")
    lines.append("issues:")
    for issue in report.get("issues", []):
        lines.append(f"  {issue['id']}: {issue['description']}")
    if report.get("issues"):
        lines.append("failure_reason=threshold breach detected")
    return "\n".join(lines) + "\n"


def write_artifacts(
    report: JsonDict,
    *,
    output_dir: Path,
    keep: int,
) -> Path:
    ensure_output_dir(output_dir)
    generated_ts = datetime.fromisoformat(report["generated_utc"]).astimezone(
        timezone.utc
    )
    run_dir = output_dir / f"{RUN_PREFIX}-{generated_ts.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    json_path = run_dir / "report.json"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md_path = run_dir / "report.md"
    md_path.write_text(write_markdown(report), encoding="utf-8")

    log_path = run_dir / "log.txt"
    log_path.write_text(write_log(report), encoding="utf-8")

    latest_pairs = [
        (json_path, output_dir / "latest_report.json"),
        (md_path, output_dir / "latest_report.md"),
        (log_path, output_dir / "latest_report.log"),
    ]
    for src, dest in latest_pairs:
        copy_latest(src, dest)

    prune_old_runs(output_dir, keep=keep, current_run=run_dir)
    return run_dir


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Repo Studios inventory health thresholds."
    )
    parser.add_argument(
        "--summary",
        default=str(SUMMARY_LATEST),
        help="Path to summary JSON to validate",
    )
    parser.add_argument(
        "--baseline",
        default=str(BASELINE_PATH),
        help="Path to baseline summary JSON",
    )
    parser.add_argument(
        "--thresholds",
        default=str(THRESHOLD_PATH),
        help="Path to CI threshold configuration",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for reports and log artifacts",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="How many historical runs to retain",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO timestamp used for the run directory (UTC if absent)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    summary_path = Path(args.summary).resolve()
    baseline_path = Path(args.baseline).resolve()
    thresholds_path = Path(args.thresholds).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not summary_path.exists():
        logging.error("summary file not found: %s", summary_path)
        return 2

    current = load_json(summary_path)
    baseline = load_json(baseline_path)
    thresholds = load_json(thresholds_path)

    status, issues, deltas = evaluate(current, baseline, thresholds)
    generated_ts = parse_timestamp(args.timestamp)

    report = build_report(
        status=status,
        issues=issues,
        deltas=deltas,
        current=current,
        baseline=baseline,
        thresholds=thresholds,
        generated_ts=generated_ts,
        summary_path=summary_path,
        baseline_path=baseline_path,
        thresholds_path=thresholds_path,
    )

    run_dir = write_artifacts(
        report,
        output_dir=output_dir,
        keep=args.artifacts_to_keep,
    )
    logging.info("inventory health artifacts written to %s", run_dir)

    return 1 if status == "failed" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
