#!/usr/bin/env python3
"""Compose Healthview-ready summaries for Test Execution Telemetry runs."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

try:  # pragma: no cover - prefer import when packaged
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        WriteReportArtifactsResult,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running in isolation
    LIBRARIES_ROOT = Path(__file__).resolve().parents[1]
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        WriteReportArtifactsResult,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )

SUMMARY_STEM = "test_execution_telemetry_summary"
VIEWER_SLUG = "summarizer_reports"
TOPIC_SLUG = "test_execution_telemetry"
SCHEMA_VERSION = 1
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/healthview")


@dataclass(frozen=True)
class StepRecord:
    """Representation of a pipeline step for summary rendering."""

    name: str
    status: str
    started_at: datetime
    finished_at: datetime
    detail: str | None
    payload: Mapping[str, Any] | None

    @property
    def duration_seconds(self) -> float:
        return max((self.finished_at - self.started_at).total_seconds(), 0.0)


@dataclass(frozen=True)
class CollectSummary:
    report_dir: Path | None
    producer_report: Path | None
    warnings_total: int | None
    slow_tests_over_threshold: int | None


@dataclass(frozen=True)
class CoverageSummary:
    report_dir: Path | None
    summary: Mapping[str, Any] | None


@dataclass(frozen=True)
class HeatmapSummary:
    run_dir: Path | None
    payload: Mapping[str, Any] | None


@dataclass(frozen=True)
class HardeningSummary:
    run_dir: Path | None
    payload: Mapping[str, Any] | None


@dataclass(frozen=True)
class HealthSummary:
    run_dir: Path | None
    bundle_summary: Path | None
    payload: Mapping[str, Any] | None


@dataclass(frozen=True)
class SummaryInputs:
    repo_root: Path
    run_slug: str
    pipeline_success: bool
    completed_at: datetime
    artifacts: Mapping[str, str | None]
    steps: Sequence[StepRecord]
    collect: CollectSummary
    coverage: CoverageSummary
    heatmap: HeatmapSummary
    hardening: HardeningSummary
    health: HealthSummary | None


@dataclass(frozen=True)
class SummaryResult:
    json_payload: Mapping[str, Any]
    markdown: str


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    manifest_path: Path
    telemetry_path: Path
    output_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "manifest_path": PathSpec(field="manifest", default=Path("manifest.json"), within_repo=False),
        "telemetry_path": PathSpec(field="telemetry", default=Path("telemetry.json"), within_repo=False),
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=False),
    },
    repo_root_depth=5,
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--manifest", required=True, help="Path to orchestrator manifest.json")
    parser.add_argument("--telemetry", required=True, help="Path to orchestrator telemetry.json")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Destination directory for rendered summary artifacts",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=3,
        help="Retention window for generated summary artifacts",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    artifacts_to_keep = max(int(getattr(keep_values, "artifacts_to_keep", 3)), 1)
    return Options(log_level=str(args.log_level), artifacts_to_keep=artifacts_to_keep)


def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _summarize_failure_detail(step: StepRecord) -> str:
    detail = (step.detail or "failed").strip()
    if not detail:
        detail = "failed"
    return f"{step.name}: {detail}"


def _extract_hardening_high(payload: Mapping[str, Any] | None) -> int | None:
    if not isinstance(payload, Mapping):
        return None
    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        return None
    severity_totals = summary.get("severity_totals")
    if not isinstance(severity_totals, Mapping):
        return None
    value = severity_totals.get("high")
    return value if isinstance(value, int) else None


def _timestamp_from_slug(run_slug: str, *, fallback: datetime) -> datetime:
    try:
        parsed = datetime.strptime(run_slug, "%Y%m%d-%H%M")
        return parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return fallback.astimezone(timezone.utc)


def build_summary(inputs: SummaryInputs) -> SummaryResult:
    repo_root = inputs.repo_root
    warnings_total = inputs.collect.warnings_total
    slow_tests = inputs.collect.slow_tests_over_threshold
    heatmap_mode = None
    if isinstance(inputs.heatmap.payload, Mapping):
        heatmap_mode = inputs.heatmap.payload.get("mode")
    hardening_status = None
    hardening_payload = inputs.hardening.payload if isinstance(inputs.hardening.payload, Mapping) else None
    if hardening_payload:
        status = hardening_payload.get("status")
        hardening_status = status if isinstance(status, str) else None
    hardening_high = _extract_hardening_high(inputs.hardening.payload if isinstance(inputs.hardening.payload, Mapping) else None)
    coverage_status = None
    if isinstance(inputs.coverage.summary, Mapping):
        status_value = inputs.coverage.summary.get("status")
        coverage_status = status_value if isinstance(status_value, str) else None
    health_source = None
    if inputs.health and isinstance(inputs.health.payload, Mapping):
        raw_source = inputs.health.payload.get("source")
        health_source = raw_source if isinstance(raw_source, str) else None

    completed_iso = inputs.completed_at.astimezone(timezone.utc).isoformat(timespec="seconds")

    runtime_metrics: list[dict[str, Any]] = []
    step_outcomes_lines: list[str] = []
    for step in inputs.steps:
        detail_text = (step.detail or "").strip()
        runtime_metrics.append(
            {
                "name": step.name,
                "status": step.status,
                "duration_seconds": round(step.duration_seconds, 3),
                "detail": detail_text or None,
            }
        )
        step_outcome = f"- {step.name}: {step.status}"
        step_outcomes_lines.append(step_outcome)
        if detail_text:
            step_outcomes_lines.append(f"  - detail: {detail_text}")
        else:
            step_outcomes_lines.append("  - detail: (none)")

    failed_steps = [step for step in inputs.steps if step.status == "failed"]
    failure_examples = [_summarize_failure_detail(step) for step in failed_steps[:2]]

    artifacts_display = {
        "log_report": inputs.artifacts.get("log_report"),
        "coverage_report": inputs.artifacts.get("coverage_report"),
        "heatmap": inputs.artifacts.get("heatmap"),
        "hardening": inputs.artifacts.get("hardening"),
        "health_report": inputs.artifacts.get("health_report"),
        "health_bundle_summary": inputs.artifacts.get("health_bundle_summary"),
    }

    metrics_section = {
        "pipeline_status": "success" if inputs.pipeline_success else "failed",
        "log_report_available": inputs.collect.report_dir is not None,
        "warnings_total": warnings_total,
        "slow_tests_over_threshold": slow_tests,
        "heatmap_mode": heatmap_mode,
        "hardening_status": hardening_status,
        "hardening_high_severity": hardening_high,
        "coverage_status": coverage_status,
        "health_report_source": health_source,
    }

    components_section = {
        "collect": {
            "report_dir": _normalize_relative(inputs.collect.report_dir, repo_root),
            "producer_report": _normalize_relative(inputs.collect.producer_report, repo_root),
            "warnings_total": warnings_total,
            "slow_tests_over_threshold": slow_tests,
        },
        "coverage": {
            "report_dir": _normalize_relative(inputs.coverage.report_dir, repo_root),
            "summary": dict(inputs.coverage.summary) if isinstance(inputs.coverage.summary, Mapping) else None,
        },
        "heatmap": {
            "run_dir": _normalize_relative(inputs.heatmap.run_dir, repo_root),
            "payload": dict(inputs.heatmap.payload) if isinstance(inputs.heatmap.payload, Mapping) else None,
        },
        "hardening": {
            "run_dir": _normalize_relative(inputs.hardening.run_dir, repo_root),
            "payload": dict(inputs.hardening.payload) if isinstance(inputs.hardening.payload, Mapping) else None,
        },
        "health": {
            "run_dir": _normalize_relative(inputs.health.run_dir, repo_root) if inputs.health else None,
            "bundle_summary": _normalize_relative(inputs.health.bundle_summary, repo_root) if inputs.health else None,
            "payload": dict(inputs.health.payload) if inputs.health and isinstance(inputs.health.payload, Mapping) else None,
        },
    }

    summary_payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "generated_at": completed_iso,
        "run_slug": inputs.run_slug,
        "metrics": metrics_section,
        "runtime_metrics": runtime_metrics,
        "failures": {
            "detected": len(failed_steps),
            "examples": failure_examples,
        },
        "artifacts": dict(artifacts_display),
        "steps": [
            {
                "name": record.name,
                "status": record.status,
                "started_at": record.started_at.isoformat(),
                "finished_at": record.finished_at.isoformat(),
                "detail": (record.detail or "").strip() or None,
                "payload": dict(record.payload) if isinstance(record.payload, Mapping) else None,
            }
            for record in inputs.steps
        ],
        "components": components_section,
    }

    lines: list[str] = []
    lines.append("# Test Execution Telemetry Summary")
    lines.append("")
    lines.append(f"- run_slug: `{inputs.run_slug}`")
    lines.append(f"- pipeline_status: {'success' if inputs.pipeline_success else 'failed'}")
    lines.append(f"- log_report_available: {'yes' if inputs.collect.report_dir else 'no'}")
    lines.append(f"- warnings_total: {warnings_total if warnings_total is not None else 'unknown'}")
    lines.append(
        f"- slow_tests_over_threshold: {slow_tests if slow_tests is not None else 'unknown'}"
    )
    lines.append(f"- heatmap_mode: {heatmap_mode or 'unknown'}")
    lines.append(f"- hardening_status: {hardening_status or 'unknown'}")
    lines.append(f"- hardening_high_severity: {hardening_high if hardening_high is not None else 'unknown'}")
    lines.append(f"- coverage_status: {coverage_status or 'unknown'}")
    lines.append(f"- health_report_source: {health_source or 'none'}")
    lines.append(f"- completed_at: {completed_iso}")
    lines.append("")

    lines.append("## Runtime Metrics")
    lines.append("")
    lines.append("| Step | Status | Duration (s) | Detail |")
    lines.append("| --- | --- | --- | --- |")
    for metric in runtime_metrics:
        detail_value = metric["detail"] or "(none)"
        lines.append(
            "| {name} | {status} | {duration:.2f} | {detail} |".format(
                name=metric["name"],
                status=metric["status"],
                duration=float(metric["duration_seconds"]),
                detail=_escape_table_cell(detail_value),
            )
        )
    lines.append("")

    lines.append("## Failure Highlights")
    lines.append("")
    lines.append(f"- detected_failures: {len(failed_steps)}")
    lines.append("- failure_examples:")
    if failure_examples:
        for example in failure_examples:
            lines.append(f"  - {example}")
    else:
        lines.append("  - none")
    lines.append("")

    lines.append("## Artifact Locations")
    lines.append("")
    for key in [
        "log_report",
        "coverage_report",
        "heatmap",
        "hardening",
        "health_report",
        "health_bundle_summary",
    ]:
        value = artifacts_display.get(key)
        formatted = value if value else "(missing)"
        lines.append(f"- {key}: `{formatted}`" if value else f"- {key}: {formatted}")
    lines.append("")

    lines.append("## Step Outcomes")
    lines.append("")
    lines.extend(step_outcomes_lines)
    lines.append("")

    markdown = "\n".join(lines).rstrip() + "\n"

    return SummaryResult(json_payload=summary_payload, markdown=markdown)


def _read_json(path: Path) -> Mapping[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, Mapping) else None


def _resolve_artifact(raw: str | None, repo_root: Path) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate.resolve()


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_step_records(steps_data: Sequence[Mapping[str, Any]]) -> list[StepRecord]:
    records: list[StepRecord] = []
    for entry in steps_data:
        try:
            name = str(entry.get("name"))
            status = str(entry.get("status"))
            started = _parse_datetime(str(entry.get("started_at")))
            finished = _parse_datetime(str(entry.get("finished_at")))
        except Exception:
            continue
        detail = entry.get("detail")
        detail_str = str(detail) if isinstance(detail, str) else None
        payload = entry.get("payload") if isinstance(entry.get("payload"), Mapping) else None
        records.append(
            StepRecord(
                name=name,
                status=status,
                started_at=started,
                finished_at=finished,
                detail=detail_str,
                payload=payload,
            )
        )
    return records


def _build_inputs_from_files(paths: Paths) -> SummaryInputs:
    repo_root = paths.repo_root
    manifest_data = _read_json(paths.manifest_path)
    telemetry_data = _read_json(paths.telemetry_path)
    if manifest_data is None:
        raise FileNotFoundError(f"Manifest not readable: {paths.manifest_path}")
    if telemetry_data is None:
        raise FileNotFoundError(f"Telemetry not readable: {paths.telemetry_path}")

    run_slug = str(manifest_data.get("run_slug") or telemetry_data.get("run_slug") or "unknown")
    pipeline_success = bool(telemetry_data.get("success"))
    completed_at = _parse_datetime(manifest_data.get("generated_at") if isinstance(manifest_data.get("generated_at"), str) else None)

    artifacts_section = manifest_data.get("artifacts")
    artifacts = artifacts_section if isinstance(artifacts_section, Mapping) else {}

    steps_data = telemetry_data.get("steps") if isinstance(telemetry_data.get("steps"), Sequence) else []
    step_records = _load_step_records(steps_data)  # type: ignore[arg-type]

    collect_record = next((step for step in step_records if step.name == "collect"), None)
    collect_payload: Mapping[str, Any] = (
        collect_record.payload
        if collect_record is not None and isinstance(collect_record.payload, Mapping)
        else {}
    )
    raw_log_report_payload = collect_payload.get("log_report")
    log_report_payload: Mapping[str, Any] = (
        raw_log_report_payload if isinstance(raw_log_report_payload, Mapping) else {}
    )
    warnings_total = log_report_payload.get("warnings_total") if isinstance(log_report_payload.get("warnings_total"), int) else None
    slow_tests = log_report_payload.get("slow_tests") if isinstance(log_report_payload.get("slow_tests"), int) else None
    collect_dir = _resolve_artifact(artifacts.get("log_report"), repo_root)
    if collect_dir is not None:
        manifest_path = collect_dir / "manifest.json"
        collector_manifest = _read_json(manifest_path) if manifest_path.exists() else None
        if not isinstance(collector_manifest, Mapping):
            collect_dir = None
        else:
            collector_status = collector_manifest.get("status")
            if isinstance(collector_status, str) and collector_status == "no_data":
                collect_dir = None
    producer_report = collect_dir.joinpath("report.json") if collect_dir else None
    if producer_report is not None and not producer_report.exists():
        producer_report = None
    collect_summary = CollectSummary(
        report_dir=collect_dir,
        producer_report=producer_report,
        warnings_total=warnings_total,
        slow_tests_over_threshold=slow_tests,
    )

    coverage_payload = collect_payload.get("coverage") if isinstance(collect_payload.get("coverage"), Mapping) else None
    coverage_summary = CoverageSummary(
        report_dir=_resolve_artifact(artifacts.get("coverage_report"), repo_root),
        summary=coverage_payload,
    )

    analyse_record = next((step for step in step_records if step.name == "analyse"), None)
    analyse_payload = analyse_record.payload if analyse_record and isinstance(analyse_record.payload, Mapping) else {}
    heatmap_dir = _resolve_artifact(artifacts.get("heatmap"), repo_root)
    heatmap_payload: Mapping[str, Any] | None = None
    if heatmap_dir is not None:
        bundle_summary_path = heatmap_dir / "bundle_summary.json"
        loaded_bundle = _read_json(bundle_summary_path)
        if isinstance(loaded_bundle, Mapping):
            heatmap_payload = loaded_bundle
    if heatmap_payload is None and analyse_payload:
        mode = analyse_payload.get("heatmap_mode")
        if isinstance(mode, str):
            heatmap_payload = {"mode": mode}
    heatmap_summary = HeatmapSummary(run_dir=heatmap_dir, payload=heatmap_payload)

    hardening_payload: dict[str, Any] | None = None
    hardening_dir = _resolve_artifact(artifacts.get("hardening"), repo_root)
    if hardening_dir is not None:
        telemetry_json = hardening_dir / "telemetry.json"
        loaded_telemetry = _read_json(telemetry_json) if telemetry_json.exists() else None
        if isinstance(loaded_telemetry, Mapping):
            raw_components = loaded_telemetry.get("components")
            components = raw_components if isinstance(raw_components, Mapping) else {}
            raw_hardening_component = components.get("hardening")
            hardening_component = (
                raw_hardening_component if isinstance(raw_hardening_component, Mapping) else {}
            )
            raw_summary = hardening_component.get("summary")
            summary = raw_summary if isinstance(raw_summary, Mapping) else None
            status = loaded_telemetry.get("status")
            payload: dict[str, Any] = {}
            if isinstance(status, str):
                payload["status"] = status
            if summary is not None:
                payload["summary"] = dict(summary)
            if payload:
                hardening_payload = payload
    if hardening_payload is None and hardening_dir is not None:
        report_json = hardening_dir / "report.json"
        loaded_report = _read_json(report_json)
        hardening_payload = dict(loaded_report) if isinstance(loaded_report, Mapping) else None
    if hardening_payload is None and isinstance(analyse_payload.get("hardening_status"), str):
        hardening_payload = {"status": analyse_payload.get("hardening_status")}
    hardening_summary = HardeningSummary(run_dir=hardening_dir, payload=hardening_payload)

    summarize_record = next((step for step in step_records if step.name == "summarize"), None)
    health_payload_raw = (
        summarize_record.payload if summarize_record and isinstance(summarize_record.payload, Mapping) else None
    )
    health_dir = _resolve_artifact(artifacts.get("health_report"), repo_root)
    health_bundle = _resolve_artifact(artifacts.get("health_bundle_summary"), repo_root)
    health_payload: dict[str, Any] | None = (
        dict(health_payload_raw) if isinstance(health_payload_raw, Mapping) else None
    )
    if health_bundle is not None:
        bundle_loaded = _read_json(health_bundle)
        if isinstance(bundle_loaded, Mapping):
            if health_payload is None:
                health_payload = {}
            health_payload.setdefault("bundle_summary", dict(bundle_loaded))
    health_summary = None
    if any([health_dir, health_bundle, health_payload]):
        health_summary = HealthSummary(run_dir=health_dir, bundle_summary=health_bundle, payload=health_payload)

    return SummaryInputs(
        repo_root=repo_root,
        run_slug=run_slug,
        pipeline_success=pipeline_success,
        completed_at=completed_at,
        artifacts={str(k): v for k, v in artifacts.items()},
        steps=step_records,
        collect=collect_summary,
        coverage=coverage_summary,
        heatmap=heatmap_summary,
        hardening=hardening_summary,
        health=health_summary,
    )


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    logger = logging.getLogger("summarize_test_execution_telemetry")

    inputs = _build_inputs_from_files(paths)
    summary = build_summary(inputs)

    artifacts = [
        ReportArtifact(filename=f"{SUMMARY_STEM}.json", kind="json", content=lambda: dict(summary.json_payload)),
        ReportArtifact(filename=f"{SUMMARY_STEM}.md", kind="text", content=lambda: summary.markdown),
    ]

    result: WriteReportArtifactsResult = write_report_artifacts(
        stem=SUMMARY_STEM,
        timestamp=_timestamp_from_slug(inputs.run_slug, fallback=inputs.completed_at),
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer=VIEWER_SLUG,
        topic=TOPIC_SLUG,
    )

    logger.info("Test Execution Telemetry summary artifacts written to %s (slug=%s)", result.run_dir, result.slug)

    return {
        "status": "ok",
        "run_dir": str(result.run_dir),
        "slug": result.slug,
        "artifacts": {name: str(path) for name, path in result.artifacts.items()},
    }


def main(argv: Sequence[str] | None = None) -> None:
    outcome = run(argv)
    raise SystemExit(0 if outcome.get("status") == "ok" else 1)


__all__ = [
    "run",
    "main",
    "build_summary",
    "SummaryInputs",
    "SummaryResult",
    "StepRecord",
    "CollectSummary",
    "CoverageSummary",
    "HeatmapSummary",
    "HardeningSummary",
    "HealthSummary",
]


if __name__ == "__main__":  # pragma: no cover
    main()
