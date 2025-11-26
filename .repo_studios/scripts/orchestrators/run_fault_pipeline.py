#!/usr/bin/env python3
"""Orchestrate the faulthandler producer + consumer pipeline."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from command_center.scripts.libraries.artifacts import (
    ReportArtifact,
    copy_latest_artifact,
    write_report_artifacts,
)
from command_center.scripts.libraries.cli import (
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    build_standard_options,
    build_standard_paths,
)

SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_REL = Path(".repo_studios/faulthandler")
DEFAULT_PRODUCER_OUTPUT_REL = Path(".repo_studios/reports/producer_reports/faulthandler_reports")
DEFAULT_PRODUCER_CC_REL = Path(".repo_studios/command_center/reports/fault_artifacts_producer")
DEFAULT_CONSUMER_OUTPUT_REL = Path(".repo_studios/reports/consumer_reports/fault_artifacts")
DEFAULT_CONSUMER_CC_REL = Path(".repo_studios/command_center/reports/fault_artifacts_consumer")
DEFAULT_ORCHESTRATOR_OUTPUT_REL = Path(".repo_studios/reports/orchestrator_runs/fault_pipeline")
DEFAULT_ORCHESTRATOR_CC_REL = Path(".repo_studios/command_center/reports/fault_pipeline_orchestrator")
DEFAULT_KEEP = 5
STEM = "fault_pipeline"
SUMMARY_JSON = "summary.json"
SUMMARY_MD = "SUMMARY.md"
BUNDLE_SUMMARY = "bundle_summary.json"
PIPELINE_LOG = "pipeline.log"

PRODUCER_PATH = SCRIPTS_ROOT / "producers" / "collect_faulthandler_reports.py"
CONSUMER_PATH = SCRIPTS_ROOT / "consumers" / "generate_fault_artifacts.py"


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    runs_dir: Path
    producer_output_dir: Path
    producer_command_center_dir: Path
    consumer_output_dir: Path
    consumer_command_center_dir: Path
    orchestrator_output_dir: Path
    orchestrator_command_center_dir: Path


@dataclass(frozen=True)
class KeepOptions:
    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int
    log_level: str = "INFO"
    skip_producer: bool = False
    skip_consumer: bool = False
    reuse_report: Path | None = None


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "runs_dir": PathSpec(field="runs_dir", default=DEFAULT_RUNS_REL, ensure_dir=False, within_repo=False),
        "producer_output_dir": PathSpec(
            field="producer_output_dir", default=DEFAULT_PRODUCER_OUTPUT_REL, ensure_dir=True, within_repo=False
        ),
        "producer_command_center_dir": PathSpec(
            field="producer_command_center_dir",
            default=DEFAULT_PRODUCER_CC_REL,
            ensure_dir=True,
            within_repo=False,
        ),
        "consumer_output_dir": PathSpec(
            field="consumer_output_dir", default=DEFAULT_CONSUMER_OUTPUT_REL, ensure_dir=True, within_repo=False
        ),
        "consumer_command_center_dir": PathSpec(
            field="consumer_command_center_dir",
            default=DEFAULT_CONSUMER_CC_REL,
            ensure_dir=True,
            within_repo=False,
        ),
        "orchestrator_output_dir": PathSpec(
            field="output_dir", default=DEFAULT_ORCHESTRATOR_OUTPUT_REL, ensure_dir=True, within_repo=False
        ),
        "orchestrator_command_center_dir": PathSpec(
            field="command_center_dir",
            default=DEFAULT_ORCHESTRATOR_CC_REL,
            ensure_dir=True,
            within_repo=False,
        ),
    },
    repo_root_depth=4,
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepOptions,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "producer_keep": KeepSpec(field="producer_artifacts_to_keep", minimum=1),
        "consumer_keep": KeepSpec(field="consumer_artifacts_to_keep", minimum=1),
    },
)

_COLLECT_MODULE = None
_CONSUMER_MODULE = None


def _load_module(module_key: str, path: Path) -> Any:
    cached = sys.modules.get(module_key)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(module_key, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Unable to load module {module_key} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_key] = module
    spec.loader.exec_module(module)
    return module


def _collect_module() -> Any:
    global _COLLECT_MODULE
    if _COLLECT_MODULE is None:
        _COLLECT_MODULE = _load_module("repo_studios.collect_faulthandler_reports", PRODUCER_PATH)
    return _COLLECT_MODULE


def _consumer_module() -> Any:
    global _CONSUMER_MODULE
    if _CONSUMER_MODULE is None:
        _CONSUMER_MODULE = _load_module("repo_studios.generate_fault_artifacts", CONSUMER_PATH)
    return _CONSUMER_MODULE


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the faulthandler pipeline (producer + consumer) with structured outputs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root (defaults to auto-detect)")
    parser.add_argument("--runs-dir", help="Directory containing faulthandler run folders")
    parser.add_argument("--run-dir", help="Explicit faulthandler run directory to process")
    parser.add_argument("--producer-output-dir", help="Destination for producer artifacts")
    parser.add_argument("--producer-command-center-dir", help="Mirror destination for producer artifacts")
    parser.add_argument("--consumer-output-dir", help="Destination for consumer artifacts")
    parser.add_argument("--consumer-command-center-dir", help="Mirror destination for consumer artifacts")
    parser.add_argument("--output-dir", help="Destination for orchestrator run bundles")
    parser.add_argument(
        "--command-center-dir",
        help="Mirror destination for orchestrator summaries under command center reports",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=None,
        help="Number of orchestrator run bundles to retain",
    )
    parser.add_argument(
        "--producer-artifacts-to-keep",
        type=int,
        default=None,
        help="Override producer retention (defaults to orchestrator keep)",
    )
    parser.add_argument(
        "--consumer-artifacts-to-keep",
        type=int,
        default=None,
        help="Override consumer retention (defaults to orchestrator keep)",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity (e.g. INFO, DEBUG)")
    parser.add_argument(
        "--skip-producer",
        action="store_true",
        help="Reuse existing producer artifacts instead of generating a new report",
    )
    parser.add_argument(
        "--skip-consumer",
        action="store_true",
        help="Stop after the producer run (or skip entirely if producer also skipped)",
    )
    parser.add_argument(
        "--reuse-report",
        help="Path to an existing faulthandler producer report.json to reuse when skipping the producer",
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    base = build_standard_options(args, OPTIONS_CONFIG)
    reuse_report = Path(args.reuse_report).resolve() if args.reuse_report else None
    artifacts_to_keep = base.artifacts_to_keep if args.artifacts_to_keep is not None else DEFAULT_KEEP
    producer_keep = base.producer_keep if args.producer_artifacts_to_keep is not None else artifacts_to_keep
    consumer_keep = base.consumer_keep if args.consumer_artifacts_to_keep is not None else artifacts_to_keep
    return Options(
        artifacts_to_keep=artifacts_to_keep,
        producer_keep=producer_keep,
        consumer_keep=consumer_keep,
        log_level=str(args.log_level or "INFO"),
        skip_producer=bool(args.skip_producer),
        skip_consumer=bool(args.skip_consumer),
        reuse_report=reuse_report,
    )


def _discover_latest_report(output_dir: Path) -> Path | None:
    pointer = output_dir / "latest_report.json"
    if pointer.exists():
        return pointer.resolve()
    if not output_dir.exists():
        return None
    candidates = [node for node in output_dir.iterdir() if node.is_dir() and node.name.startswith("faulthandler_report-")]
    candidates.sort(key=lambda node: node.name, reverse=True)
    for candidate in candidates:
        report_path = candidate / "report.json"
        if report_path.exists():
            return report_path.resolve()
    return None


def _load_json(path: Path) -> Mapping[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_run_dir_from_report(report_path: Path) -> Path | None:
    payload = _load_json(report_path)
    if not payload:
        return None
    run_dir = payload.get("run_dir")
    if not run_dir:
        return None
    return Path(run_dir).resolve()


def _extract_severity(bundle_dir: Path) -> Mapping[str, Any]:
    summary_path = bundle_dir / SUMMARY_JSON
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    summary = payload.get("summary")
    buckets = summary.get("severity_buckets") if isinstance(summary, Mapping) else None
    if not isinstance(buckets, Mapping):
        return {}
    return {
        "repeat_offender": int(buckets.get("repeat_offender", 0)),
        "multi_hit": int(buckets.get("multi_hit", 0)),
        "single_hit": int(buckets.get("single_hit", 0)),
    }


def _format_duration(duration: float | None) -> float:
    if duration is None:
        return 0.0
    return round(duration, 4)


def _build_markdown_summary(
    *,
    generated_at: datetime,
    overall_status: str,
    run_dir: Path | None,
    report_path: Path | None,
    producer_info: Mapping[str, Any],
    consumer_info: Mapping[str, Any],
    severity: Mapping[str, Any],
    steps: Sequence[Mapping[str, Any]],
) -> str:
    lines: list[str] = []
    lines.append("# Fault Pipeline Orchestrator Summary")
    lines.append("")
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append(f"Overall Status: {overall_status.upper()}")
    lines.append("")
    lines.append("## Run Context")
    lines.append("")
    lines.append(f"- Run Directory: `{run_dir}`" if run_dir else "- Run Directory: (unknown)")
    lines.append(f"- Producer Report: `{report_path}`" if report_path else "- Producer Report: (none)")
    lines.append("")
    lines.append("## Producer")
    lines.append("")
    for key in ("status", "output_dir", "run_dir", "report_path", "signatures", "repeat_offender_signatures"):
        value = producer_info.get(key)
        lines.append(f"- {key}: {value}")
    if producer_info.get("notes"):
        lines.append("- notes:")
        for note in producer_info["notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("## Consumer")
    lines.append("")
    for key in ("status", "consumer_report", "bundle_summary", "signatures", "repeat_offender_signatures"):
        value = consumer_info.get(key)
        lines.append(f"- {key}: {value}")
    if severity:
        lines.append("- severity buckets:")
        for bucket, count in severity.items():
            lines.append(f"  - {bucket}: {count}")
    if consumer_info.get("notes"):
        lines.append("- notes:")
        for note in consumer_info["notes"]:
            lines.append(f"  - {note}")
    lines.append("")
    lines.append("## Steps")
    lines.append("")
    for step in steps:
        lines.append(f"- {step['name']}: {step['status']} ({step['duration_seconds']}s)")
        for note in step.get("notes", []):
            lines.append(f"  - {note}")
    lines.append("")
    return "\n".join(lines)


def _write_log(log_lines: Sequence[str], run_dir: Path) -> Path:
    log_path = run_dir / PIPELINE_LOG
    text = "\n".join(log_lines).strip() + "\n"
    log_path.write_text(text, encoding="utf-8")
    return log_path


def _mirror_to_command_center(bundle_dir: Path, *, command_center_dir: Path, keep: int) -> None:
    command_center_dir.mkdir(parents=True, exist_ok=True)
    mirror_dir = command_center_dir / bundle_dir.name
    if mirror_dir.exists():
        shutil.rmtree(mirror_dir, ignore_errors=True)
    mirror_dir.mkdir(parents=True, exist_ok=True)
    for name in (SUMMARY_JSON, SUMMARY_MD, BUNDLE_SUMMARY, PIPELINE_LOG):
        src = bundle_dir / name
        if not src.exists():
            continue
        dest = mirror_dir / name
        dest.write_bytes(src.read_bytes())
        copy_latest_artifact(src, command_center_dir / f"latest_{name}")
    keep = max(int(keep), 1)
    candidates = sorted(
        [node for node in command_center_dir.iterdir() if node.is_dir() and node.name.startswith(f"{STEM}-")],
        key=lambda node: node.name,
        reverse=True,
    )
    for index, node in enumerate(candidates):
        if node == mirror_dir:
            continue
        if index >= keep:
            shutil.rmtree(node, ignore_errors=True)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)

    log_level = getattr(logging, options.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s %(message)s", force=True)
    log = logging.getLogger("fault_pipeline_orchestrator")

    steps: list[dict[str, Any]] = []
    log_lines: list[str] = []
    overall_status = "success"

    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    report_path = options.reuse_report.resolve() if options.reuse_report else None

    producer_info: dict[str, Any] = {"status": "skipped" if options.skip_producer else "pending", "notes": []}
    consumer_info: dict[str, Any] = {"status": "skipped" if options.skip_consumer else "pending", "notes": []}
    severity: Mapping[str, Any] = {}

    producer_result: Mapping[str, Any] | None = None

    if options.skip_producer:
        reason = "skip requested"
        producer_info["status"] = "skipped"
        producer_info.setdefault("notes", []).append(reason)
        steps.append({"name": "collect_faulthandler_reports", "status": "skipped", "duration_seconds": 0.0, "notes": [reason]})
        log_lines.append("Producer step skipped via --skip-producer")
    else:
        collect_args = [
            "--repo-root",
            str(paths.repo_root),
            "--runs-dir",
            str(paths.runs_dir),
            "--output-dir",
            str(paths.producer_output_dir),
            "--command-center-dir",
            str(paths.producer_command_center_dir),
            "--artifacts-to-keep",
            str(options.producer_keep),
            "--log-level",
            options.log_level,
        ]
        if run_dir is not None:
            collect_args.extend(["--run-dir", str(run_dir)])
        log_lines.append("Starting collect_faulthandler_reports")
        start = time.perf_counter()
        try:
            producer_result = _collect_module().run(collect_args)
            duration = time.perf_counter() - start
            log_lines.append(f"collect_faulthandler_reports completed in {duration:.2f}s")
            producer_info.update(
                {
                    "status": "success",
                    "run_dir": producer_result.get("run_dir"),
                    "output_dir": producer_result.get("output_dir"),
                    "report_path": producer_result.get("report"),
                    "signatures": producer_result.get("signatures"),
                    "repeat_offender_signatures": producer_result.get("repeat_offender_signatures"),
                    "duration_seconds": _format_duration(duration),
                }
            )
            steps.append(
                {
                    "name": "collect_faulthandler_reports",
                    "status": "success",
                    "duration_seconds": _format_duration(duration),
                    "notes": [],
                }
            )
            run_dir = Path(producer_result.get("run_dir")).resolve() if producer_result.get("run_dir") else run_dir
            report_path = Path(producer_result.get("report")).resolve() if producer_result.get("report") else report_path
        except Exception as exc:  # pragma: no cover - defensive guard
            duration = time.perf_counter() - start
            log.exception("Producer step failed: %s", exc)
            log_lines.append(f"collect_faulthandler_reports failed after {duration:.2f}s: {exc}")
            producer_info.update(
                {
                    "status": "failed",
                    "notes": [f"Exception: {exc}"],
                    "duration_seconds": _format_duration(duration),
                }
            )
            steps.append(
                {
                    "name": "collect_faulthandler_reports",
                    "status": "failed",
                    "duration_seconds": _format_duration(duration),
                    "notes": [str(exc)],
                }
            )
            overall_status = "failed"

    if producer_info.get("status") == "skipped" and report_path is None:
        report_path = _discover_latest_report(paths.producer_output_dir)
        if report_path:
            producer_info.setdefault("notes", []).append("Reusing latest producer report")
            log_lines.append(f"Reusing latest producer report at {report_path}")

    if report_path and (run_dir is None or not run_dir.exists()):
        derived_run_dir = _extract_run_dir_from_report(report_path)
        if derived_run_dir is not None:
            run_dir = derived_run_dir
            log_lines.append(f"Derived run directory {run_dir} from report metadata")

    if report_path is not None:
        producer_info.setdefault("report_path", str(report_path))
    if run_dir is not None:
        producer_info.setdefault("run_dir", str(run_dir))

    if options.skip_consumer:
        consumer_info["status"] = "skipped"
        consumer_info.setdefault("notes", []).append("skip requested")
        steps.append({"name": "generate_fault_artifacts", "status": "skipped", "duration_seconds": 0.0, "notes": ["skip requested"]})
        log_lines.append("Consumer step skipped via --skip-consumer")
    elif overall_status == "failed":
        consumer_info["status"] = "skipped"
        consumer_info.setdefault("notes", []).append("producer failed")
        steps.append(
            {
                "name": "generate_fault_artifacts",
                "status": "skipped",
                "duration_seconds": 0.0,
                "notes": ["producer failed"],
            }
        )
    else:
        if run_dir is None or not run_dir.exists():
            note = "run directory unavailable"
            consumer_info["status"] = "skipped"
            consumer_info.setdefault("notes", []).append(note)
            steps.append(
                {
                    "name": "generate_fault_artifacts",
                    "status": "skipped",
                    "duration_seconds": 0.0,
                    "notes": [note],
                }
            )
            overall_status = "failed"
            log_lines.append("Consumer step skipped: run directory unavailable")
        else:
            consumer_args = [
                "--outdir",
                str(run_dir),
                "--output-dir",
                str(paths.consumer_output_dir),
                "--command-center-dir",
                str(paths.consumer_command_center_dir),
                "--artifacts-to-keep",
                str(options.consumer_keep),
                "--log-level",
                options.log_level,
            ]
            if report_path is not None:
                consumer_args.extend(["--report", str(report_path)])
            log_lines.append("Starting generate_fault_artifacts")
            start = time.perf_counter()
            try:
                consumer_result = _consumer_module().run(consumer_args)
                duration = time.perf_counter() - start
                bundle_dir = Path(consumer_result.get("consumer_report")) if consumer_result.get("consumer_report") else None
                severity = _extract_severity(bundle_dir) if bundle_dir else {}
                consumer_info.update(
                    {
                        "status": "success",
                        "consumer_report": consumer_result.get("consumer_report"),
                        "bundle_summary": consumer_result.get("bundle_summary"),
                        "signatures": consumer_result.get("signatures"),
                        "repeat_offender_signatures": consumer_result.get("repeat_offender_signatures"),
                        "duration_seconds": _format_duration(duration),
                    }
                )
                steps.append(
                    {
                        "name": "generate_fault_artifacts",
                        "status": "success",
                        "duration_seconds": _format_duration(duration),
                        "notes": [],
                    }
                )
                log_lines.append(f"generate_fault_artifacts completed in {duration:.2f}s")
            except Exception as exc:  # pragma: no cover - defensive guard
                duration = time.perf_counter() - start
                log.exception("Consumer step failed: %s", exc)
                consumer_info.update(
                    {
                        "status": "failed",
                        "notes": [f"Exception: {exc}"],
                        "duration_seconds": _format_duration(duration),
                    }
                )
                steps.append(
                    {
                        "name": "generate_fault_artifacts",
                        "status": "failed",
                        "duration_seconds": _format_duration(duration),
                        "notes": [str(exc)],
                    }
                )
                log_lines.append(f"generate_fault_artifacts failed after {duration:.2f}s: {exc}")
                overall_status = "failed"

    generated_at = datetime.now(UTC)

    def _summary_writer(run_dir_path: Path) -> Path:
        summary_path = run_dir_path / SUMMARY_JSON
        payload = {
            "schema_version": 1,
            "generated_at": generated_at.isoformat(timespec="seconds"),
            "status": overall_status,
            "run_dir": str(run_dir.resolve()) if run_dir else None,
            "report_path": str(report_path.resolve()) if report_path else None,
            "producer": producer_info,
            "consumer": consumer_info,
            "steps": steps,
            "severity_buckets": severity,
            "artifacts": {
                "summary_json": str(summary_path.resolve()),
                "summary_md": str((run_dir_path / SUMMARY_MD).resolve()),
                "bundle_summary": str((run_dir_path / BUNDLE_SUMMARY).resolve()),
                "pipeline_log": str((run_dir_path / PIPELINE_LOG).resolve()),
            },
        }
        summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return summary_path

    markdown_summary = _build_markdown_summary(
        generated_at=generated_at,
        overall_status=overall_status,
        run_dir=run_dir.resolve() if run_dir else None,
        report_path=report_path.resolve() if report_path else None,
        producer_info=producer_info,
        consumer_info=consumer_info,
        severity=severity,
        steps=steps,
    )

    def _markdown_writer(run_dir_path: Path) -> Path:
        md_path = run_dir_path / SUMMARY_MD
        md_path.write_text(markdown_summary, encoding="utf-8")
        return md_path

    def _bundle_summary_writer(run_dir_path: Path) -> Path:
        bundle_path = run_dir_path / BUNDLE_SUMMARY
        payload = {
            "schema_version": 1,
            "generated_at": generated_at.isoformat(timespec="seconds"),
            "status": overall_status,
            "run_dir": str(run_dir.resolve()) if run_dir else None,
            "report_path": str(report_path.resolve()) if report_path else None,
            "producer": producer_info,
            "consumer": consumer_info,
            "severity_buckets": severity,
        }
        bundle_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return bundle_path

    artifacts = [
        ReportArtifact(filename=PIPELINE_LOG, pointer="latest_pipeline.log", writer=lambda dir_path: _write_log(log_lines, dir_path)),
        ReportArtifact(filename=SUMMARY_JSON, pointer="latest_summary.json", writer=_summary_writer),
        ReportArtifact(filename=SUMMARY_MD, pointer="latest_SUMMARY.md", writer=_markdown_writer),
        ReportArtifact(filename=BUNDLE_SUMMARY, pointer="latest_bundle_summary.json", writer=_bundle_summary_writer),
    ]

    write_result = write_report_artifacts(
        stem=STEM,
        timestamp=generated_at,
        output_dir=paths.orchestrator_output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    _mirror_to_command_center(
        write_result.run_dir,
        command_center_dir=paths.orchestrator_command_center_dir,
        keep=options.artifacts_to_keep,
    )

    summary_path = write_result.artifacts[SUMMARY_JSON].resolve()
    summary_md_path = write_result.artifacts[SUMMARY_MD].resolve()
    bundle_summary_path = write_result.artifacts[BUNDLE_SUMMARY].resolve()
    log_path = write_result.artifacts[PIPELINE_LOG].resolve()

    return {
        "status": overall_status,
        "summary_path": str(summary_path),
        "summary_md_path": str(summary_md_path),
        "bundle_summary_path": str(bundle_summary_path),
        "log_path": str(log_path),
        "run_dir": str(run_dir.resolve()) if run_dir else None,
        "report_path": str(report_path.resolve()) if report_path else None,
        "producer": producer_info,
        "consumer": consumer_info,
        "steps": steps,
    }


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
