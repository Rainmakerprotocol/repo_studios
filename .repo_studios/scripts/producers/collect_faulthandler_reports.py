#!/usr/bin/env python3
"""Collect structured summaries for faulthandler runs.

This producer converts raw faulthandler run directories into positional-encoded
artifacts under:

`.repo_studios/reports/healthview/producer_reports/faulthandler_reports/<YYYYMMDD-HHMM>/`

It emits the canonical artifact trio:

- `manifest.json`
- `summary.md`
- `telemetry.json`
"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any, Sequence, cast

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
REPO_LIB_ROOT = Path(__file__).resolve().parents[2]
for candidate in (SCRIPTS_ROOT, REPO_LIB_ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from libraries.cli import (  # noqa: E402
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    build_standard_options,
    build_standard_paths,
)
from libraries.database_integration import create_storage  # noqa: E402
from libraries.retention_policy import get_keep  # noqa: E402
from libraries.prune_logs import prune_run_directories  # noqa: E402
from libraries.report_paths import build_topic_path  # noqa: E402
from utilities.fault_run_analysis import (  # noqa: E402
    FaultAnalysisResult,
    build_fault_report,
)

DEFAULT_RUNS_RELATIVE = Path(".repo_studios/command_center/reports/rawview/fault_diagnostics_runs")
LEGACY_RUNS_RELATIVE = Path(".repo_studios/faulthandler")
TOPIC_SLUG = "faulthandler_reports"
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)
DEFAULT_KEEP = get_keep("collect_faulthandler_reports")
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    runs_dir: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int
    log_level: str = "INFO"
    validate_only: bool = False
    top_frames: int | None = None
    timestamp: str | None = None


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "runs_dir": PathSpec(field="runs_dir", default=DEFAULT_RUNS_RELATIVE, ensure_dir=False, within_repo=False),
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=False,
        ),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="collect_faulthandler_reports",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root (defaults to auto-detect)")
    parser.add_argument("--runs-dir", help="Directory containing faulthandler capture folders")
    parser.add_argument("--run-dir", help="Explicit faulthandler run directory to process")
    parser.add_argument("--output-dir", help="Reports root directory for positional output bundles")
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_KEEP,
        help="Number of historical runs to retain (minimum 1)",
    )
    parser.add_argument(
        "--timestamp",
        help="Optional timestamp override (ISO-8601 or YYYYMMDD-HHMM; UTC assumed when absent)",
    )
    parser.add_argument(
        "--top-frames",
        type=int,
        default=None,
        help="Override the number of frames captured per signature",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the latest report.json schema without writing new artifacts",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    base = cast(Options, build_standard_options(args, OPTIONS_CONFIG))
    return replace(
        base,
        log_level=str(args.log_level),
        validate_only=bool(args.validate_only),
        top_frames=int(args.top_frames) if args.top_frames is not None else None,
        timestamp=str(args.timestamp) if getattr(args, "timestamp", None) else None,
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _allow_legacy_runs() -> bool:
    flag = os.environ.get("FAULT_LOGS_ALLOW_LEGACY", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _timestamp_slug(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def _resolve_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    raw = raw.strip()
    if not raw:
        return datetime.now(timezone.utc)
    if len(raw) == 13 and raw[8] == "-":
        try:
            moment = datetime.strptime(raw, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)
            return moment
        except ValueError as exc:
            raise RuntimeError(f"Invalid --timestamp value: {exc}") from exc
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid --timestamp value: {exc}") from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _detect_trigger_type() -> str:
    if os.getenv("MAKELEVEL"):
        return "make"
    if os.getenv("GITHUB_ACTIONS"):
        return "ci"
    return "cli"


def _detect_requested_by() -> str | None:
    return os.getenv("GITHUB_ACTOR") or os.getenv("USERNAME") or os.getenv("USER")


def _detect_git_sha(repo_root: Path) -> str | None:
    import subprocess

    env_sha = os.getenv("GITHUB_SHA")
    if env_sha:
        return env_sha
    if not (repo_root / ".git").exists():
        return None
    try:
        value = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:  # pragma: no cover - best effort
        return None
    value = value.strip()
    return value or None


def _resolve_runs_base(paths: Paths) -> Path:
    runs_dir = paths.runs_dir
    if runs_dir.exists():
        return runs_dir

    legacy = LEGACY_RUNS_RELATIVE
    if not legacy.is_absolute():
        legacy = paths.repo_root / legacy

    if _allow_legacy_runs() and legacy.exists():
        logging.getLogger("faulthandler_report").info(
            "Faulthandler runs directory %s missing; falling back to legacy %s",
            runs_dir,
            legacy,
        )
        return legacy

    return runs_dir


def _find_latest_run(runs_base: Path) -> Path | None:
    try:
        candidates = [p for p in runs_base.iterdir() if p.is_dir()]
    except FileNotFoundError:
        return None
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _resolve_run_dir(explicit: str | None, runs_base: Path) -> Path | None:
    if explicit:
        return Path(explicit)
    return _find_latest_run(runs_base)


def _render_markdown(report: dict[str, Any]) -> str:
    raw_summary = report.get("summary")
    summary = cast(dict[str, Any], raw_summary) if isinstance(raw_summary, dict) else {}
    raw_signatures = report.get("signatures")
    signatures = raw_signatures if isinstance(raw_signatures, list) else []
    lines: list[str] = []
    lines.append("# Faulthandler Report Summary")
    lines.append("")
    lines.append(f"Generated (UTC): {report.get('generated_utc', 'unknown')}")
    lines.append(f"Source Run Dir: {report.get('run_dir', 'unknown')}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- signature_count: {summary.get('signature_count', len(signatures))}")
    lines.append(f"- active_signature_count: {summary.get('active_signature_count')}")
    lines.append(f"- thread_block_count: {summary.get('thread_block_count')}")
    lines.append(f"- top_frame_limit: {summary.get('top_frame_limit')}")
    lines.append(f"- stack_log_exists: {summary.get('stack_log_exists')}")
    lines.append(f"- stack_text_bytes: {summary.get('stack_text_bytes')}")
    lines.append(f"- first_seen_utc: {summary.get('first_seen_utc')}")
    lines.append(f"- last_seen_utc: {summary.get('last_seen_utc')}")
    lines.append("")
    raw_severity = summary.get("severity_buckets")
    if isinstance(raw_severity, dict):
        lines.append("## Severity Buckets")
        lines.append("")
        severity = cast(dict[str, Any], raw_severity)
        lines.append(f"- repeat_offender: {severity.get('repeat_offender', 0)}")
        lines.append(f"- multi_hit: {severity.get('multi_hit', 0)}")
        lines.append(f"- single_hit: {severity.get('single_hit', 0)}")
        lines.append("")
    return "\n".join(lines) + "\n"

def build_manifest(*, paths: Paths, options: Options, analysis: FaultAnalysisResult, run_slug: str) -> dict[str, Any]:
    bundle_dir = paths.output_dir / run_slug
    return {
        "schema_version": SCHEMA_VERSION,
        "viewer_slug": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_slug,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _detect_git_sha(paths.repo_root),
        "status": "ok",
        "catalog": [
            {
                "script_path": str(Path(".repo_studios/scripts/producers/collect_faulthandler_reports.py")),
                "role": "producer",
            }
        ],
        "paths": {
            "repo_root": str(paths.repo_root),
            "reports_root": str(paths.output_dir),
            "bundle_dir": str(bundle_dir),
        },
        "inputs": {
            "runs_dir": str(paths.runs_dir),
            "run_dir": analysis.report.get("run_dir"),
            "top_frames": options.top_frames,
            "artifacts_to_keep": options.artifacts_to_keep,
            "allow_legacy_runs": _allow_legacy_runs(),
        },
        "provenance": {
            "trigger_type": _detect_trigger_type(),
            "requested_by": _detect_requested_by(),
        },
    }


def build_telemetry(*, analysis: FaultAnalysisResult, run_slug: str) -> dict[str, Any]:
    raw_summary = analysis.report.get("summary")
    summary = cast(dict[str, Any], raw_summary) if isinstance(raw_summary, dict) else {}
    raw_severity = summary.get("severity_buckets")
    severity = cast(dict[str, Any], raw_severity) if isinstance(raw_severity, dict) else {}
    return {
        "schema_version": SCHEMA_VERSION,
        "viewer_slug": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_slug,
        "generated_utc": analysis.report.get("generated_utc"),
        "status": "ok",
        "metrics": {
            "signature_count": summary.get("signature_count", len(analysis.signatures)),
            "active_signature_count": summary.get("active_signature_count"),
            "thread_block_count": summary.get("thread_block_count"),
            "stack_text_bytes": summary.get("stack_text_bytes"),
            "repeat_offender_signatures": severity.get("repeat_offender", 0),
        },
        "components": {
            "faulthandler": {
                "summary": summary,
                "signatures": analysis.report.get("signatures", []),
                "manifest": analysis.report.get("manifest"),
            }
        },
    }


def _validate_latest(paths: Paths, log: logging.Logger) -> dict[str, Any]:
    topic_dir = paths.output_dir
    if not topic_dir.exists():
        return {"status": "fail", "issues": [f"missing topic dir: {topic_dir}"], "bundle_dir": None}
    candidates = [p for p in topic_dir.iterdir() if p.is_dir()]
    candidates.sort(key=lambda p: p.name, reverse=True)
    if not candidates:
        return {"status": "fail", "issues": ["no bundles found"], "bundle_dir": None}
    bundle_dir = candidates[0]
    issues: list[str] = []
    for required in ("manifest.json", "summary.md", "telemetry.json"):
        if not (bundle_dir / required).exists():
            issues.append(f"missing {required}")
    status = "pass" if not issues else "fail"
    for entry in issues:
        log.error("Validation issue: %s", entry)
    return {"status": status, "issues": issues, "bundle_dir": str(bundle_dir.resolve())}


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    log = logging.getLogger("faulthandler_report")

    runs_dir = _resolve_runs_base(paths)

    if options.validate_only:
        return _validate_latest(paths, log)

    run_dir_path = _resolve_run_dir(args.run_dir, runs_dir)
    if run_dir_path is None or not Path(run_dir_path).exists():
        log.info("No faulthandler runs available under %s", runs_dir)
        return {
            "run_dir": None,
            "artifacts": None,
            "output_dir": str(paths.output_dir),
        }

    run_dir = Path(run_dir_path).resolve()
    now = _resolve_timestamp(options.timestamp)
    analysis = build_fault_report(run_dir, now=now, top_n=options.top_frames or 0) if options.top_frames else build_fault_report(run_dir, now=now)
    run_slug = _timestamp_slug(now)

    storage = create_storage(paths.output_dir, "", "", timestamp=run_slug)
    manifest = build_manifest(paths=paths, options=options, analysis=analysis, run_slug=run_slug)
    telemetry = build_telemetry(analysis=analysis, run_slug=run_slug)
    markdown = _render_markdown(analysis.report)

    # DB_INTEGRATION_MARKER: faulthandler manifest
    storage.write_manifest(manifest)

    # DB_INTEGRATION_MARKER: faulthandler summary markdown
    storage.write_summary({"markdown": markdown}, format="md")

    # DB_INTEGRATION_MARKER: faulthandler telemetry
    storage.write_telemetry(telemetry)

    run_bundle_dir = storage.file_storage.bundle_dir
    prune_run_directories(
        paths.output_dir,
        keep=options.artifacts_to_keep,
        current_run=run_bundle_dir,
        logger=log,
    )

    summary = analysis.report.get("summary", {}) if isinstance(analysis.report, dict) else {}
    severity = summary.get("severity_buckets", {}) if isinstance(summary, dict) else {}
    log.info(
        "Faulthandler report captured (run_dir=%s, signatures=%d, repeat_offender=%s, output=%s)",
        run_dir,
        len(analysis.signatures),
        severity.get("repeat_offender", 0),
        run_bundle_dir,
    )
    return {
        "run_dir": str(run_dir),
        "output_dir": str(run_bundle_dir),
        "manifest": str((run_bundle_dir / "manifest.json").resolve()),
        "summary_md": str((run_bundle_dir / "summary.md").resolve()),
        "telemetry": str((run_bundle_dir / "telemetry.json").resolve()),
        "signatures": len(analysis.signatures),
        "repeat_offender_signatures": int(severity.get("repeat_offender", 0)),
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
