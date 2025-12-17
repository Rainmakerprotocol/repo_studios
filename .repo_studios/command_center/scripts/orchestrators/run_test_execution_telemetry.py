#!/usr/bin/env python3
"""Topic orchestrator for test execution telemetry.

Emits Healthview bundles under
`.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/` and replaces
the legacy `scripts/orchestrators/run_pytest_log_capture.py` flow by chaining log collection,
coverage inventory, churn heatmap, hardening analysis, and the health report summarizer. Expect a
roughly five to six minute runtime in CI when churn analysis is enabled; the pipeline stops on the
first hard failure so log gaps surface quickly.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from command_center.scripts.libraries import (
    CatalogRegistry,
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    ReportArtifact,
    TopicContext,
    TopicStep,
    build_pipeline_telemetry,
    build_standard_options,
    build_standard_paths,
    build_topic_pipeline,
    measure_artifact_directory,
    step_failed,
    step_skipped,
    step_success,
    write_report_artifacts,
)

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "test-execution-telemetry"
HEALTHVIEW_TOPIC = "test_execution_telemetry"
VIEWER_SLUG = "healthview"
SCHEMA_VERSION = 1

COLLECT_SCRIPT = Path(".repo_studios/scripts/producers/collect_test_log_reports.py")
HEALTH_REPORT_SCRIPT = Path(".repo_studios/scripts/consumers/generate_test_log_health_report.py")
HEATMAP_SCRIPT = Path(".repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py")
COVERAGE_SCRIPT = Path(".repo_studios/scripts/producers/generate_test_coverage_inventory.py")
HARDENING_SCRIPT = Path(".repo_studios/scripts/producers/analyze_test_hardening.py")

COLLECT_MODULE = "scripts.producers.collect_test_log_reports"
HEALTH_MODULE = "scripts.consumers.generate_test_log_health_report"
HEATMAP_MODULE = "scripts.aggregators.generate_churn_complexity_heatmap"
COVERAGE_MODULE = "scripts.producers.generate_test_coverage_inventory"
HARDENING_MODULE = "scripts.producers.analyze_test_hardening"
SUMMARIZER_SCRIPT = Path(
    ".repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py"
)
SUMMARIZER_MODULE = "command_center.scripts.summarizers.summarize_test_execution_telemetry"

DEFAULT_LOGS_DIR = Path(".repo_studios/command_center/reports/rawview/test_execution_runs")
DEFAULT_TEST_LOG_REPORTS_DIR = Path(".repo_studios/command_center/reports")
DEFAULT_TEST_LOG_HEALTH_DIR = Path(".repo_studios/reports/consumer_reports/test_log_health_reports")
DEFAULT_COVERAGE_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/test_coverage_reports")
DEFAULT_COVERAGE_XML = Path(".repo_studios/tests/fixtures/test_run_coverage/coverage.xml")
DEFAULT_HEATMAP_OUTPUT_DIR = Path(".repo_studios/reports/aggregator_reports/churn_complexity_heatmap")
DEFAULT_HARDENING_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
DEFAULT_HEALTHVIEW_ROOT = Path(".repo_studios/command_center/reports")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    logs_dir: Path
    test_log_reports_dir: Path
    test_log_health_dir: Path
    coverage_output_dir: Path
    coverage_xml: Path
    heatmap_output_dir: Path
    hardening_output_dir: Path
    healthview_root: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "logs_dir": PathSpec(field="logs_dir", default=DEFAULT_LOGS_DIR, ensure_dir=False, within_repo=False),
        "test_log_reports_dir": PathSpec(
            field="test_log_reports_dir", default=DEFAULT_TEST_LOG_REPORTS_DIR, ensure_dir=True, within_repo=False
        ),
        "test_log_health_dir": PathSpec(
            field="test_log_health_dir", default=DEFAULT_TEST_LOG_HEALTH_DIR, ensure_dir=True, within_repo=False
        ),
        "coverage_output_dir": PathSpec(
            field="test_coverage_output_dir", default=DEFAULT_COVERAGE_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "coverage_xml": PathSpec(
            field="test_coverage_xml", default=DEFAULT_COVERAGE_XML, ensure_dir=False, within_repo=False
        ),
        "heatmap_output_dir": PathSpec(
            field="heatmap_output_dir", default=DEFAULT_HEATMAP_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "hardening_output_dir": PathSpec(
            field="hardening_output_dir", default=DEFAULT_HARDENING_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "healthview_root": PathSpec(
            field="healthview_root", default=DEFAULT_HEALTHVIEW_ROOT, ensure_dir=True, within_repo=False
        ),
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepParameters:
    artifacts_to_keep: int
    collector_keep: int
    health_keep: int
    coverage_keep: int
    heatmap_keep: int
    hardening_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepParameters,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "collector_keep": KeepSpec(field="collector_artifacts_to_keep", minimum=1),
        "health_keep": KeepSpec(field="health_artifacts_to_keep", minimum=1),
        "coverage_keep": KeepSpec(field="coverage_artifacts_to_keep", minimum=1),
        "heatmap_keep": KeepSpec(field="heatmap_artifacts_to_keep", minimum=1),
        "hardening_keep": KeepSpec(field="hardening_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int
    collector_keep: int
    health_keep: int
    coverage_keep: int
    heatmap_keep: int
    hardening_keep: int
    heatmap_window: int
    metrics_source: Path | None
    run_timestamp: datetime


@dataclass(frozen=True)
class CollectOutcome:
    report_dir: Path | None
    producer_bundle_dir: Path | None
    warnings_total: int | None
    slow_tests: int | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class CoverageOutcome:
    report_dir: Path | None
    summary: dict[str, Any] | None


@dataclass(frozen=True)
class HeatmapOutcome:
    run_dir: Path | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class HardeningOutcome:
    run_dir: Path | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class HealthReportOutcome:
    run_dir: Path | None
    bundle_summary: Path | None
    payload: dict[str, Any]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--logs-dir", default=str(DEFAULT_LOGS_DIR))
    parser.add_argument("--test-log-reports-dir", default=str(DEFAULT_TEST_LOG_REPORTS_DIR))
    parser.add_argument("--test-log-health-dir", default=str(DEFAULT_TEST_LOG_HEALTH_DIR))
    parser.add_argument("--test-coverage-output-dir", default=str(DEFAULT_COVERAGE_OUTPUT_DIR))
    parser.add_argument("--test-coverage-xml", default=str(DEFAULT_COVERAGE_XML))
    parser.add_argument("--heatmap-output-dir", default=str(DEFAULT_HEATMAP_OUTPUT_DIR))
    parser.add_argument("--heatmap-metrics-source")
    parser.add_argument("--heatmap-window", type=int, default=500)
    parser.add_argument("--hardening-output-dir", default=str(DEFAULT_HARDENING_OUTPUT_DIR))
    parser.add_argument("--healthview-root", default=str(DEFAULT_HEALTHVIEW_ROOT))
    parser.add_argument("--artifacts-to-keep", type=int, default=3, help="Topic artifacts to retain")
    parser.add_argument(
        "--collector-artifacts-to-keep", type=int, default=10, help="Retention window for log report runs"
    )
    parser.add_argument(
        "--health-artifacts-to-keep", type=int, default=5, help="Retention window for health report runs"
    )
    parser.add_argument(
        "--coverage-artifacts-to-keep", type=int, default=10, help="Retention window for coverage inventory"
    )
    parser.add_argument(
        "--heatmap-artifacts-to-keep", type=int, default=10, help="Retention window for churn heatmap runs"
    )
    parser.add_argument(
        "--hardening-artifacts-to-keep", type=int, default=10, help="Retention window for hardening analysis"
    )
    parser.add_argument(
        "--timestamp",
        help="ISO8601 timestamp for the orchestrator run slug (defaults to current UTC)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    metrics_source = None
    if args.heatmap_metrics_source:
        metrics_source = Path(args.heatmap_metrics_source).expanduser().resolve()
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        collector_keep=keep_values.collector_keep,
        health_keep=keep_values.health_keep,
        coverage_keep=keep_values.coverage_keep,
        heatmap_keep=keep_values.heatmap_keep,
        hardening_keep=keep_values.hardening_keep,
        heatmap_window=int(args.heatmap_window),
        metrics_source=metrics_source,
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_run_callable(script_path: Path, module_name: str):
    script_path = script_path.resolve()
    if module_name in sys.modules:
        return getattr(sys.modules[module_name], "run")
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    run_callable = getattr(module, "run", None)
    if not callable(run_callable):
        raise AttributeError(f"Module at {script_path} does not expose a callable run() helper")
    return run_callable


def _latest_directory(base: Path, prefix: str) -> Path | None:
    if not base.exists():
        return None
    candidates = [child for child in base.iterdir() if child.is_dir() and child.name.startswith(prefix)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.name)[-1]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _execute_coverage(paths: Paths, options: Options) -> CoverageOutcome:
    run_callable = _load_run_callable(paths.repo_root / COVERAGE_SCRIPT, COVERAGE_MODULE)
    before = set(child for child in paths.coverage_output_dir.glob("test_coverage-*") if child.is_dir())
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--coverage-xml",
        str(paths.coverage_xml),
        "--output-dir",
        str(paths.coverage_output_dir),
        "--artifacts-to-keep",
        str(options.coverage_keep),
        "--log-level",
        options.log_level,
    ]
    exit_code = int(run_callable(argv))
    if exit_code != 0:
        raise RuntimeError(f"Coverage inventory exit code {exit_code}")
    after = set(child for child in paths.coverage_output_dir.glob("test_coverage-*") if child.is_dir())
    created = sorted(after - before)
    run_dir = created[-1] if created else _latest_directory(paths.coverage_output_dir, "test_coverage-")
    summary = None
    if run_dir is not None:
        report_path = run_dir / "report.json"
        payload = _read_json(report_path)
        if isinstance(payload, dict) and isinstance(payload.get("summary"), dict):
            summary_dict = dict(payload["summary"])
            status_value = summary_dict.get("status") or payload.get("status")
            if status_value is not None:
                summary_dict["status"] = status_value
            summary = summary_dict
    return CoverageOutcome(report_dir=run_dir, summary=summary)


def _execute_collect(paths: Paths, options: Options) -> CollectOutcome:
    run_callable = _load_run_callable(paths.repo_root / COLLECT_SCRIPT, COLLECT_MODULE)
    argv = [
        "--logs-dir",
        str(paths.logs_dir),
        "--output-dir",
        str(paths.test_log_reports_dir),
        "--artifacts-to-keep",
        str(options.collector_keep),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("collect_test_log_reports returned unexpected payload")
    report_dir = Path(payload["output_dir"]).resolve() if payload.get("output_dir") else None
    producer_bundle_dir = report_dir
    warnings_total = payload.get("warnings_total") if isinstance(payload.get("warnings_total"), int) else None
    slow_tests = payload.get("slow_tests") if isinstance(payload.get("slow_tests"), int) else None
    return CollectOutcome(
        report_dir=report_dir,
        producer_bundle_dir=producer_bundle_dir if producer_bundle_dir and producer_bundle_dir.exists() else None,
        warnings_total=warnings_total,
        slow_tests=slow_tests,
        payload=payload,
    )


def _execute_heatmap(paths: Paths, options: Options) -> HeatmapOutcome:
    run_callable = _load_run_callable(paths.repo_root / HEATMAP_SCRIPT, HEATMAP_MODULE)
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-base",
        str(paths.heatmap_output_dir),
        "--logs-dir",
        str(paths.logs_dir),
        "--artifacts-to-keep",
        str(options.heatmap_keep),
        "--window",
        str(options.heatmap_window),
        "--log-level",
        options.log_level,
    ]
    if options.metrics_source is not None:
        argv.extend(["--metrics-source", str(options.metrics_source)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_churn_complexity_heatmap returned unexpected payload")
    run_dir = Path(payload.get("output_dir", "")).resolve() if payload.get("output_dir") else None
    return HeatmapOutcome(run_dir=run_dir if run_dir and run_dir.exists() else None, payload=payload)


def _execute_hardening(paths: Paths, options: Options) -> HardeningOutcome:
    run_callable = _load_run_callable(paths.repo_root / HARDENING_SCRIPT, HARDENING_MODULE)
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.hardening_output_dir),
        "--artifacts-to-keep",
        str(options.hardening_keep),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("analyze_test_hardening returned unexpected payload")
    run_dir = None
    candidate_dir = payload.get("output_dir")
    if candidate_dir:
        candidate = Path(str(candidate_dir)).resolve()
        if candidate.exists() and candidate.is_dir():
            run_dir = candidate
    if run_dir is None:
        timestamp = payload.get("timestamp")
        if timestamp:
            try:
                parsed = datetime.fromisoformat(str(timestamp))
                slug = parsed.strftime("%Y%m%d_%H%M%S")
                legacy_candidate = paths.hardening_output_dir / f"test_hardening-{slug}"
                if legacy_candidate.exists():
                    run_dir = legacy_candidate.resolve()
            except ValueError:
                run_dir = None
    return HardeningOutcome(run_dir=run_dir, payload=payload)


def _execute_health_report(
    paths: Paths,
    options: Options,
    *,
    producer_bundle_dir: Path | None,
) -> HealthReportOutcome:
    run_callable = _load_run_callable(paths.repo_root / HEALTH_REPORT_SCRIPT, HEALTH_MODULE)
    argv = [
        "--logs-dir",
        str(paths.logs_dir),
        "--output-base",
        str(paths.test_log_health_dir),
        "--artifacts-to-keep",
        str(options.health_keep),
        "--log-level",
        options.log_level,
    ]
    if producer_bundle_dir is not None:
        argv.extend(["--producer-bundle-dir", str(producer_bundle_dir)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_test_log_health_report returned unexpected payload")
    run_dir = Path(payload.get("output_dir", "")).resolve() if payload.get("output_dir") else None
    bundle_summary = Path(payload.get("bundle_summary", "")).resolve() if payload.get("bundle_summary") else None
    return HealthReportOutcome(
        run_dir=run_dir if run_dir and run_dir.exists() else None,
        bundle_summary=bundle_summary if bundle_summary and bundle_summary.exists() else None,
        payload=payload,
    )


def _register_scripts(registry: CatalogRegistry) -> None:
    registry.register(
        script_path=str(Path(".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py")),
        topic=TOPIC_SLUG,
        role="orchestrator",
    )
    registry.register(script_path=str(COLLECT_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(HEALTH_REPORT_SCRIPT), topic=TOPIC_SLUG, role="consumer")
    registry.register(script_path=str(HEATMAP_SCRIPT), topic=TOPIC_SLUG, role="aggregator")
    registry.register(script_path=str(COVERAGE_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(HARDENING_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(SUMMARIZER_SCRIPT), topic=TOPIC_SLUG, role="summarizer")


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    registry = CatalogRegistry()
    _register_scripts(registry)

    context = TopicContext(paths=paths, options=options, metadata={})

    collect_outcome_holder: dict[str, CollectOutcome] = {}
    coverage_outcome_holder: dict[str, CoverageOutcome] = {}
    heatmap_outcome_holder: dict[str, HeatmapOutcome] = {}
    hardening_outcome_holder: dict[str, HardeningOutcome] = {}
    health_outcome_holder: dict[str, HealthReportOutcome | None] = {"value": None}

    def collect_step(ctx: TopicContext):
        LOGGER.info("Collecting pytest telemetry artifacts")
        coverage = _execute_coverage(paths, options)
        collect = _execute_collect(paths, options)
        ctx.add_metadata("coverage", coverage)
        ctx.add_metadata("collect", collect)
        coverage_outcome_holder["value"] = coverage
        collect_outcome_holder["value"] = collect
        detail = "no pytest logs discovered" if collect.report_dir is None else "log report captured"
        payload = {
            "coverage": coverage.summary or {},
            "log_report": {
                "warnings_total": collect.warnings_total,
                "slow_tests": collect.slow_tests,
            },
        }
        if collect.report_dir is None:
            return step_success(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    def analyse_step(ctx: TopicContext):
        LOGGER.info("Running telemetry analysis scripts")
        hardening = _execute_hardening(paths, options)
        heatmap = _execute_heatmap(paths, options)
        ctx.add_metadata("hardening", hardening)
        ctx.add_metadata("heatmap", heatmap)
        hardening_outcome_holder["value"] = hardening
        heatmap_outcome_holder["value"] = heatmap
        return step_success(
            detail="analysis completed",
            payload={
                "hardening_status": hardening.payload.get("status") if isinstance(hardening.payload, dict) else None,
                "heatmap_mode": heatmap.payload.get("mode") if isinstance(heatmap.payload, dict) else None,
            },
        )

    def summarize_step(ctx: TopicContext):
        collect_outcome = collect_outcome_holder.get("value")
        if collect_outcome is None or collect_outcome.producer_bundle_dir is None:
            return step_skipped(detail="no structured log report found")
        LOGGER.info("Generating test log health summary")
        health = _execute_health_report(paths, options, producer_bundle_dir=collect_outcome.producer_bundle_dir)
        ctx.add_metadata("health", health)
        health_outcome_holder["value"] = health
        return step_success(
            detail="health summary generated",
            payload={
                "source": health.payload.get("source") if isinstance(health.payload, dict) else None,
            },
        )

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="collect", runner=collect_step),
            TopicStep(name="analyse", runner=analyse_step),
            TopicStep(name="summarize", runner=summarize_step, continue_on_failure=False),
        ]
    )

    result = pipeline.run(context)
    try:
        result.raise_for_failure()
    except RuntimeError as exc:
        LOGGER.error("Pipeline failed: %s", exc)
        return 1

    collect_outcome = collect_outcome_holder.get("value")
    if collect_outcome is None:
        collect_outcome = CollectOutcome(
            report_dir=None,
            producer_bundle_dir=None,
            warnings_total=None,
            slow_tests=None,
            payload={},
        )
    coverage_outcome = coverage_outcome_holder.get("value")
    if coverage_outcome is None:
        coverage_outcome = CoverageOutcome(report_dir=None, summary=None)
    heatmap_outcome = heatmap_outcome_holder.get("value")
    if heatmap_outcome is None:
        heatmap_outcome = HeatmapOutcome(run_dir=None, payload={})
    hardening_outcome = hardening_outcome_holder.get("value")
    if hardening_outcome is None:
        hardening_outcome = HardeningOutcome(run_dir=None, payload={})
    health_outcome = health_outcome_holder.get("value")

    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    telemetry = build_pipeline_telemetry(result, viewer=VIEWER_SLUG, topic=TOPIC_SLUG, run_slug=run_slug)
    completed_at = datetime.now(timezone.utc)

    artifacts_section: dict[str, Any] = {
        "log_report": _relativize(collect_outcome.report_dir if collect_outcome else None, paths.repo_root),
        "coverage_report": _relativize(coverage_outcome.report_dir if coverage_outcome else None, paths.repo_root),
        "heatmap": _relativize(heatmap_outcome.run_dir if heatmap_outcome else None, paths.repo_root),
        "hardening": _relativize(hardening_outcome.run_dir if hardening_outcome else None, paths.repo_root),
        "health_report": _relativize(health_outcome.run_dir if health_outcome else None, paths.repo_root),
        "health_bundle_summary": _relativize(
            health_outcome.bundle_summary if health_outcome else None, paths.repo_root
        ),
    }

    telemetry_payload = telemetry.as_dict()

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "logs_dir": _relativize(paths.logs_dir, paths.repo_root),
            "coverage_xml": _relativize(paths.coverage_xml, paths.repo_root),
            "metrics_source": _relativize(options.metrics_source, paths.repo_root),
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
    }

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: manifest),
        ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
    ]
    result_artifacts = write_report_artifacts(
        stem=HEALTHVIEW_TOPIC,
        timestamp=options.run_timestamp,
        output_dir=paths.healthview_root,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer=VIEWER_SLUG,
        topic=HEALTHVIEW_TOPIC,
    )

    summarizer_run = _load_run_callable(paths.repo_root / SUMMARIZER_SCRIPT, SUMMARIZER_MODULE)
    summary_args = [
        "--repo-root",
        str(paths.repo_root),
        "--manifest",
        str(result_artifacts.artifacts["manifest.json"]),
        "--telemetry",
        str(result_artifacts.artifacts["telemetry.json"]),
        "--output-dir",
        str(paths.healthview_root),
        "--artifacts-to-keep",
        str(options.artifacts_to_keep),
        "--log-level",
        options.log_level,
    ]
    summary_payload = summarizer_run(summary_args)
    if not isinstance(summary_payload, dict) or summary_payload.get("status") != "ok":
        raise RuntimeError("summarize_test_execution_telemetry returned unexpected payload")

    summary_artifacts = summary_payload.get("artifacts") if isinstance(summary_payload.get("artifacts"), dict) else {}

    summary_markdown_path = None
    summary_json_path = None
    for name, path_str in summary_artifacts.items():
        candidate_path = Path(path_str)
        if name.endswith(".md"):
            summary_markdown_path = candidate_path
        elif name.endswith(".json"):
            summary_json_path = candidate_path

    if summary_markdown_path:
        artifacts_section["summary_markdown"] = _relativize(summary_markdown_path, paths.repo_root)
    if summary_json_path:
        artifacts_section["summary_json"] = _relativize(summary_json_path, paths.repo_root)

    artifact_metrics = measure_artifact_directory(result_artifacts.run_dir)
    metrics_section = telemetry_payload.setdefault("metrics", {})
    metrics_section.update(artifact_metrics.as_dict())
    manifest["telemetry"] = telemetry_payload
    manifest["metrics"] = dict(metrics_section)

    manifest_path = result_artifacts.artifacts["manifest.json"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    telemetry_path = result_artifacts.artifacts["telemetry.json"]
    telemetry_path.write_text(json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    LOGGER.info("Test Execution Telemetry orchestrator complete (slug=%s)", run_slug)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]
