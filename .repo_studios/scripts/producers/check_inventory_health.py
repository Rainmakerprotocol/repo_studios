#!/usr/bin/env python3
"""Inventory health validation with structured artifacts.

Artifacts (default):
    - `.repo_studios/command_center/reports/healthview/inventory_health/<YYYYMMDD-HHMM>/`
        - `manifest.json`
        - `summary.md`
        - `telemetry.json`

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
from typing import Any, Dict, NamedTuple, cast

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback during standalone execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
    from libraries.retention_policy import get_keep

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUMMARY_PATH = Path(".repo_studios/reports/producer_reports/healthview/inventory_overview")
DEFAULT_BASELINE_PATH = Path(".repo_studios/config/inventory/inventory_summary_baseline.json")
DEFAULT_THRESHOLDS_PATH = Path("config/ci_inventory_thresholds.json")
DEFAULT_OUTPUT_PATH = Path(".repo_studios/command_center/reports")

SUMMARY_LATEST = ROOT / DEFAULT_SUMMARY_PATH
BASELINE_PATH = ROOT / DEFAULT_BASELINE_PATH
THRESHOLD_PATH = ROOT / DEFAULT_THRESHOLDS_PATH

DEFAULT_OUTPUT_DIR = DEFAULT_OUTPUT_PATH
RUN_PREFIX = "inventory_health"
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("check_inventory_health")

VIEWER_SLUG = "healthview"
TOPIC_SLUG = "inventory_health"

logger = logging.getLogger(__name__)


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


def _latest_inventory_overview_run(topic_dir: Path) -> Path | None:
    if not topic_dir.exists():
        return None
    try:
        candidates = [node for node in topic_dir.iterdir() if node.is_dir()]
    except OSError:
        return None

    def _is_timestamp_dir(path: Path) -> bool:
        name = path.name
        if len(name) != 13:
            return False
        if name[8] != "-":
            return False
        return name[:8].isdigit() and name[9:].isdigit()

    timestamped = [node for node in candidates if _is_timestamp_dir(node)]
    if not timestamped:
        return None
    timestamped.sort(key=lambda node: node.name)
    return timestamped[-1]


def load_json(path: Path) -> JsonDict:
    if not path.exists():
        logging.debug("JSON source missing: %s", path)
        return {}
    if path.is_dir():
        latest_run = _latest_inventory_overview_run(path)
        if latest_run is None:
            logging.debug("No timestamped runs found under: %s", path)
            return {}
        telemetry_path = latest_run / "telemetry.json"
        if not telemetry_path.exists():
            logging.debug("Telemetry missing: %s", telemetry_path)
            return {}
        try:
            telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logging.error("failed to parse JSON from %s: %s", telemetry_path, exc)
            return {}
        if isinstance(telemetry, dict) and isinstance(telemetry.get("summary"), dict):
            return cast(JsonDict, telemetry["summary"])
        if isinstance(telemetry, dict):
            return cast(JsonDict, telemetry)
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - guarded by CI inputs
        logging.error("failed to parse JSON from %s: %s", path, exc)
        return {}
    return payload if isinstance(payload, dict) else {}


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
            issues[f"status:{status}"] = f"Status '{status}' count {value} exceeds limit {limit}"

    minimum_assets = thresholds.get("minimum_assets", {}) or {}
    for asset_kind, minimum in minimum_assets.items():
        value = current.get("by_asset_kind", {}).get(asset_kind, 0)
        if value < minimum:
            issues[f"asset:{asset_kind}"] = f"Asset kind '{asset_kind}' count {value} below minimum {minimum}"

    consumer_required = thresholds.get("consumer_required", []) or []
    consumers = current.get("consumers", {}) or {}
    for consumer in consumer_required:
        if consumers.get(consumer, 0) == 0:
            issues[f"consumer:{consumer}"] = f"Consumer '{consumer}' missing from summary"

    return issues


def evaluate(current: JsonDict, baseline: JsonDict, thresholds: JsonDict) -> tuple[str, Dict[str, str], JsonDict]:
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


def _timestamp_slug(timestamp: datetime) -> str:
    normalized = timestamp
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def build_manifest(
    *,
    status: str,
    generated_ts: datetime,
    run_slug: str,
    summary_path: Path,
    baseline_path: Path,
    thresholds_path: Path,
    artifacts_to_keep: int,
) -> JsonDict:
    return {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": run_slug,
        "generated_at": generated_ts.astimezone(timezone.utc).isoformat(),
        "status": status,
        "catalog": ["scripts.inventory.check_inventory_health"],
        "inputs": {
            "summary_path": str(summary_path),
            "baseline_path": str(baseline_path),
            "thresholds_path": str(thresholds_path),
            "artifacts_to_keep": artifacts_to_keep,
        },
    }


def build_telemetry(
    *,
    status: str,
    issues: Dict[str, str],
    deltas: JsonDict,
    current: JsonDict,
    baseline: JsonDict,
    thresholds: JsonDict,
    generated_ts: datetime,
    run_slug: str,
) -> JsonDict:
    issue_list = [{"id": key, "description": message} for key, message in sorted(issues.items())]
    summary = {
        "issues": len(issue_list),
        "total_assets": current.get("total"),
    }
    return {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": run_slug,
        "generated_utc": generated_ts.astimezone(timezone.utc).isoformat(),
        "status": status,
        "summary": summary,
        "deltas": deltas,
        "issues": issue_list,
        "snapshots": {
            "current": current,
            "baseline": baseline,
            "thresholds": thresholds,
        },
    }


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
    issue_list = [{"id": key, "description": message} for key, message in sorted(issues.items())]
    delta_list = [{"metric": key, "delta": value} for key, value in sorted(deltas.items())]
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
        f"Summary Path: {report['inputs']['summary_path']}",
        f"Baseline Path: {report['inputs']['baseline_path']}",
        f"Threshold Path: {report['inputs']['thresholds_path']}",
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
    raw_deltas = report.get("deltas", {})
    if isinstance(raw_deltas, dict):
        deltas = [{"metric": key, "delta": raw_deltas[key]} for key in sorted(raw_deltas)]
    else:
        deltas = list(raw_deltas)

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


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    base_options = cast(Options, build_standard_options(args, OPTIONS_CONFIG))
    return base_options._replace(
        timestamp=getattr(args, "timestamp", None),
        log_level=str(getattr(args, "log_level", "INFO")),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Repo Studios inventory health thresholds.")
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
        logging.error("summary source not found: %s", summary_path)
        return 2

    current = load_json(summary_path)
    baseline = load_json(baseline_path)
    thresholds = load_json(thresholds_path)

    status, issues, deltas = evaluate(current, baseline, thresholds)
    generated_ts = parse_timestamp(options.timestamp)

    run_slug = _timestamp_slug(generated_ts)


    manifest = build_manifest(
        status=status,
        generated_ts=generated_ts,
        run_slug=run_slug,
        summary_path=summary_path,
        baseline_path=baseline_path,
        thresholds_path=thresholds_path,
        artifacts_to_keep=options.artifacts_to_keep,
    )
    telemetry = build_telemetry(
        status=status,
        issues=issues,
        deltas=deltas,
        current=current,
        baseline=baseline,
        thresholds=thresholds,
        generated_ts=generated_ts,
        run_slug=run_slug,
    )

    storage = create_storage(output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=run_slug)

    # DB_INTEGRATION_MARKER: inventory health manifest
    storage.write_manifest(manifest)

    # DB_INTEGRATION_MARKER: inventory health summary markdown
    storage.write_summary({"markdown": write_markdown({**telemetry, "inputs": manifest["inputs"]})}, format="md")

    # DB_INTEGRATION_MARKER: inventory health telemetry
    storage.write_telemetry(telemetry)

    run_dir = storage.file_storage.bundle_dir
    prune_run_directories(
        output_dir / VIEWER_SLUG / TOPIC_SLUG,
        keep=options.artifacts_to_keep,
        current_run=run_dir,
        logger=logger,
    )

    logging.info("inventory health artifacts written to %s", run_dir)

    return 1 if status == "failed" else 0


def run(argv: list[str] | None = None) -> dict[str, Any]:
    """Orchestrator-callable entry point returning structured payload.

    Executes inventory health validation and returns a payload dict suitable
    for orchestrator chaining. Wraps main() logic with payload extraction.

    Args:
        argv: Command-line arguments (uses sys.argv[1:] if None)

    Returns:
        Payload dict with keys:
            - status: "passed" or "failed"
            - exit_code: 0 (ok), 1 (breach), or 2 (missing input)
            - run_dir: Path to output bundle directory
            - output_dir: Parent output directory
            - run_id: Timestamp slug (YYYYMMDD-HHMM)
            - manifest: Full manifest dict
            - telemetry: Full telemetry dict
            - summary: Summary metrics dict
    """
    parser = argparse.ArgumentParser(description="Validate Repo Studios inventory health thresholds.")
    parser.add_argument("--repo-root", help="Repository root (defaults to project root)")
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY_PATH), help="Path to summary JSON")
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE_PATH), help="Path to baseline JSON")
    parser.add_argument("--thresholds", default=str(DEFAULT_THRESHOLDS_PATH), help="Path to thresholds JSON")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="Retention")
    parser.add_argument("--timestamp", help="ISO timestamp for run directory")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args(argv)

    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    if not paths.summary.exists():
        logging.error("summary source not found: %s", paths.summary)
        return {
            "status": "error",
            "exit_code": 2,
            "error": f"summary source not found: {paths.summary}",
            "run_dir": None,
            "output_dir": str(paths.output_dir),
            "run_id": None,
            "manifest": None,
            "telemetry": None,
            "summary": None,
        }

    current = load_json(paths.summary)
    baseline = load_json(paths.baseline)
    thresholds = load_json(paths.thresholds)

    status, issues, deltas = evaluate(current, baseline, thresholds)
    generated_ts = parse_timestamp(options.timestamp)
    run_slug = _timestamp_slug(generated_ts)

    manifest = build_manifest(
        status=status,
        generated_ts=generated_ts,
        run_slug=run_slug,
        summary_path=paths.summary,
        baseline_path=paths.baseline,
        thresholds_path=paths.thresholds,
        artifacts_to_keep=options.artifacts_to_keep,
    )
    telemetry = build_telemetry(
        status=status,
        issues=issues,
        deltas=deltas,
        current=current,
        baseline=baseline,
        thresholds=thresholds,
        generated_ts=generated_ts,
        run_slug=run_slug,
    )

    storage = create_storage(paths.output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=run_slug)

    # DB_INTEGRATION_MARKER: inventory health manifest
    storage.write_manifest(manifest)

    # DB_INTEGRATION_MARKER: inventory health summary markdown
    storage.write_summary({"markdown": write_markdown({**telemetry, "inputs": manifest["inputs"]})}, format="md")

    # DB_INTEGRATION_MARKER: inventory health telemetry
    storage.write_telemetry(telemetry)

    run_dir = storage.file_storage.bundle_dir
    prune_run_directories(
        paths.output_dir / VIEWER_SLUG / TOPIC_SLUG,
        keep=options.artifacts_to_keep,
        current_run=run_dir,
        logger=logger,
    )

    logging.info("inventory health artifacts written to %s", run_dir)

    return {
        "status": status,
        "exit_code": 1 if status == "failed" else 0,
        "run_dir": str(run_dir),
        "output_dir": str(paths.output_dir),
        "run_id": run_slug,
        "manifest": manifest,
        "telemetry": telemetry,
        "summary": {
            "issues_count": len(issues),
            "total_assets": current.get("total"),
            "status": status,
        },
    }


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
