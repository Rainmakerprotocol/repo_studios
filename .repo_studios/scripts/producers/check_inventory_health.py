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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, NamedTuple

LIBRARIES_ROOT = (
    Path(__file__).resolve().parents[3]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)

try:
    from libraries import (  # type: ignore
        KeepSpec,
        PathSpec,
        ReportArtifact,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback during standalone execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        PathSpec,
        ReportArtifact,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMMARY_PATH = Path("reports/summary/latest/summary.json")
DEFAULT_BASELINE_PATH = Path("reports/summary/main_baseline.json")
DEFAULT_THRESHOLDS_PATH = Path("config/ci_inventory_thresholds.json")
DEFAULT_OUTPUT_PATH = Path(
    ".repo_studios/reports/producer_reports/inventory_health_reports"
)

SUMMARY_LATEST = ROOT / DEFAULT_SUMMARY_PATH
BASELINE_PATH = ROOT / DEFAULT_BASELINE_PATH
THRESHOLD_PATH = ROOT / DEFAULT_THRESHOLDS_PATH

DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_PATH
RUN_PREFIX = "inventory_health"
DEFAULT_ARTIFACTS_TO_KEEP = 10


class Paths(NamedTuple):
    repo_root: Path
    summary: Path
    baseline: Path
    thresholds: Path
    output_dir: Path


class Options(NamedTuple):
    artifacts_to_keep: int
    timestamp: str | None = None
    log_level: str = "INFO"


PATH_SPECS: dict[str, PathSpec] = {
    "summary": PathSpec(field="summary", default=DEFAULT_SUMMARY_PATH, within_repo=False),
    "baseline": PathSpec(field="baseline", default=DEFAULT_BASELINE_PATH, within_repo=False),
    "thresholds": PathSpec(field="thresholds", default=DEFAULT_THRESHOLDS_PATH, within_repo=False),
    "output_dir": PathSpec(
        field="output_dir",
        default=DEFAULT_OUTPUT_PATH,
        ensure_dir=True,
        within_repo=False,
    ),
}


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)

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


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    return base_options._replace(
        timestamp=getattr(args, "timestamp", None),
        log_level=str(getattr(args, "log_level", "INFO")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Repo Studios inventory health thresholds."
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root (defaults to project root)",
    )
    parser.add_argument(
        "--summary",
        default=str(DEFAULT_SUMMARY_PATH),
        help="Path to summary JSON to validate",
    )
    parser.add_argument(
        "--baseline",
        default=str(DEFAULT_BASELINE_PATH),
        help="Path to baseline summary JSON",
    )
    parser.add_argument(
        "--thresholds",
        default=str(DEFAULT_THRESHOLDS_PATH),
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

    paths = build_paths(args)
    options = build_options(args)

    configure_logging(options.log_level)

    summary_path = paths.summary
    baseline_path = paths.baseline
    thresholds_path = paths.thresholds
    output_dir = paths.output_dir

    if not summary_path.exists():
        logging.error("summary file not found: %s", summary_path)
        return 2

    current = load_json(summary_path)
    baseline = load_json(baseline_path)
    thresholds = load_json(thresholds_path)

    status, issues, deltas = evaluate(current, baseline, thresholds)
    generated_ts = parse_timestamp(options.timestamp)

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

    artifacts = [
        ReportArtifact(
            filename="report.json",
            pointer="latest_report.json",
            kind="json",
            content=lambda: report,
        ),
        ReportArtifact(
            filename="report.md",
            pointer="latest_report.md",
            kind="text",
            content=lambda: write_markdown(report),
        ),
        ReportArtifact(
            filename="log.txt",
            pointer="latest_report.log",
            kind="text",
            content=lambda: write_log(report),
        ),
    ]

    result = write_report_artifacts(
        stem=RUN_PREFIX,
        timestamp=generated_ts,
        output_dir=output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )
    logging.info("inventory health artifacts written to %s", result.run_dir)

    return 1 if status == "failed" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
