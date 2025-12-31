#!/usr/bin/env python3
"""Topic orchestrator for the Monkey Patch Oversight workflow.

Outputs Healthview bundles at
`.repo_studios/command_center/reports/healthview/monkey_patch_oversight/<timestamp>/` and replaces the
monkey patch stages that previously lived inside `orchestrate_health_suite.py` alongside the
standalone summarizer invocation. The pipeline scans, classifies, aggregates, and summarizes monkey
patch risk before emitting manifest, summary, and telemetry artifacts. Runs usually finish within
four to seven minutes when Git history enrichment is enabled; trend aggregation scales with the
configured history window.
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
from typing import Any, Callable, Sequence

LIBRARIES_ROOT = Path(__file__).resolve().parents[1]
if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))

from libraries import (
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
from libraries.report_paths import build_topic_path

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "monkey-patch-oversight"
HEALTHVIEW_TOPIC = "monkey_patch_oversight"
VIEWER_SLUG = "healthview"
SCHEMA_VERSION = 1

PRODUCER_SCRIPT = Path(".repo_studios/scripts/producers/scan_monkey_patches.py")
PRODUCER_MODULE = "scripts.producers.scan_monkey_patches"
CONSUMER_SCRIPT = Path(".repo_studios/scripts/consumers/classify_monkey_patches.py")
CONSUMER_MODULE = "scripts.consumers.classify_monkey_patches"
AGGREGATOR_SCRIPT = Path(".repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py")
AGGREGATOR_MODULE = "scripts.aggregators.analyze_monkey_patch_trends"
ORCHESTRATOR_SCRIPT = Path(".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py")
SUMMARIZER_SCRIPT = Path(".repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py")
SUMMARIZER_MODULE = "command_center.scripts.summarizers.summarize_monkey_patch_overview"
UTILITY_SCRIPT = Path(".repo_studios/scripts/utilities/monkey_patch_risk.py")

DEFAULT_SCAN_ROOT = Path(".")
DEFAULT_PRODUCER_OUTPUT = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
DEFAULT_CONSUMER_OUTPUT = Path(".repo_studios/reports/consumer_reports/monkey_patch_risk")
DEFAULT_AGGREGATOR_OUTPUT = Path(".repo_studios/reports/aggregator_reports/monkey_patch_trends")
DEFAULT_SUMMARIZER_OUTPUT = Path(".repo_studios/reports/summarizer_reports/monkey_patch_overview")
DEFAULT_HEALTHVIEW_ROOT = build_topic_path("orchestrator", "monkey_patch_oversight")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    scan_root: Path
    producer_output_dir: Path
    consumer_output_dir: Path
    aggregator_output_dir: Path
    summarizer_output_dir: Path
    healthview_root: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "scan_root": PathSpec(field="scan_root", default=DEFAULT_SCAN_ROOT, within_repo=False),
        "producer_output_dir": PathSpec(
            field="producer_output_dir", default=DEFAULT_PRODUCER_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "consumer_output_dir": PathSpec(
            field="consumer_output_dir", default=DEFAULT_CONSUMER_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "aggregator_output_dir": PathSpec(
            field="aggregator_output_dir", default=DEFAULT_AGGREGATOR_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "summarizer_output_dir": PathSpec(
            field="summarizer_output_dir", default=DEFAULT_SUMMARIZER_OUTPUT, ensure_dir=True, within_repo=False
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
    producer_keep: int
    consumer_keep: int
    aggregator_keep: int
    summarizer_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepParameters,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "producer_keep": KeepSpec(field="producer_artifacts_to_keep", minimum=1),
        "consumer_keep": KeepSpec(field="consumer_artifacts_to_keep", minimum=1),
        "aggregator_keep": KeepSpec(field="aggregator_artifacts_to_keep", minimum=1),
        "summarizer_keep": KeepSpec(field="summarizer_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int
    aggregator_keep: int
    summarizer_keep: int
    trend_max_runs: int
    producer_context_lines: int
    producer_with_git: bool
    producer_strict: bool
    producer_project_packages: tuple[str, ...]
    producer_exclude_dirs: tuple[str, ...]
    producer_exclude_globs: tuple[str, ...]
    skip_producer: bool
    skip_consumer: bool
    skip_aggregator: bool
    skip_summarizer: bool
    duplicate_matrix: Path | None
    run_timestamp: datetime


@dataclass(frozen=True)
class ProducerOutcome:
    payload: dict[str, Any]
    run_dir: Path | None
    report_path: Path | None
    matches_path: Path | None
    status: str | None
    total_findings: int | None
    run_id: str | None


@dataclass(frozen=True)
class ConsumerOutcome:
    payload: dict[str, Any]
    bundle_dir: Path | None
    bundle_summary: Path | None
    summary_json: Path | None
    summary_markdown: Path | None
    source: str | None


@dataclass(frozen=True)
class AggregatorOutcome:
    payload: dict[str, Any]
    trend_dir: Path | None
    trend_json: Path | None
    trend_markdown: Path | None
    bundle_summary: Path | None
    consumer_snapshot: Path | None
    mode: str | None


@dataclass(frozen=True)
class SummarizerOutcome:
    payload: dict[str, Any]
    run_dir: Path | None
    artifacts: dict[str, Path]
    slug: str | None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--scan-root", default=str(DEFAULT_SCAN_ROOT))
    parser.add_argument("--producer-output-dir", default=str(DEFAULT_PRODUCER_OUTPUT))
    parser.add_argument("--consumer-output-dir", default=str(DEFAULT_CONSUMER_OUTPUT))
    parser.add_argument("--aggregator-output-dir", default=str(DEFAULT_AGGREGATOR_OUTPUT))
    parser.add_argument("--summarizer-output-dir", default=str(DEFAULT_SUMMARIZER_OUTPUT))
    parser.add_argument("--healthview-root", default=str(DEFAULT_HEALTHVIEW_ROOT))
    parser.add_argument("--artifacts-to-keep", type=int, default=3, help="Retention budget for manifest artifacts")
    parser.add_argument("--producer-artifacts-to-keep", type=int, default=10)
    parser.add_argument("--consumer-artifacts-to-keep", type=int, default=10)
    parser.add_argument("--aggregator-artifacts-to-keep", type=int, default=10)
    parser.add_argument("--summarizer-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--trend-max-runs", type=int, default=20, help="Maximum trend runs to blend")
    parser.add_argument("--producer-context-lines", type=int, default=2)
    parser.add_argument("--producer-with-git", action="store_true")
    parser.add_argument("--producer-strict", action="store_true")
    parser.add_argument(
        "--producer-project-packages",
        nargs="*",
        help="Optional override for owned project packages forwarded to the producer",
    )
    parser.add_argument("--producer-exclude-dirs", nargs="*", help="Directories excluded from the producer scan")
    parser.add_argument("--producer-exclude-globs", nargs="*", help="Glob patterns excluded from the producer scan")
    parser.add_argument("--duplicate-matrix", help="Optional duplicate matrix to surface in the summarizer")
    parser.add_argument("--skip-producer", action="store_true")
    parser.add_argument("--skip-consumer", action="store_true")
    parser.add_argument("--skip-aggregator", action="store_true")
    parser.add_argument("--skip-summarizer", action="store_true")
    parser.add_argument("--timestamp", help="ISO-8601 timestamp for orchestrator outputs")
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
    except ValueError as exc:  # pragma: no cover - defensive parsing
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace, *, paths: Paths) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    project_packages = tuple(getattr(args, "producer_project_packages", []) or ())
    exclude_dirs = tuple(getattr(args, "producer_exclude_dirs", []) or ())
    exclude_globs = tuple(getattr(args, "producer_exclude_globs", []) or ())
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        producer_keep=keep_values.producer_keep,
        consumer_keep=keep_values.consumer_keep,
        aggregator_keep=keep_values.aggregator_keep,
        summarizer_keep=keep_values.summarizer_keep,
        trend_max_runs=max(int(args.trend_max_runs or 1), 1),
        producer_context_lines=max(int(args.producer_context_lines or 0), 0),
        producer_with_git=bool(args.producer_with_git),
        producer_strict=bool(args.producer_strict),
        producer_project_packages=project_packages,
        producer_exclude_dirs=exclude_dirs,
        producer_exclude_globs=exclude_globs,
        skip_producer=bool(args.skip_producer),
        skip_consumer=bool(args.skip_consumer),
        skip_aggregator=bool(args.skip_aggregator),
        skip_summarizer=bool(args.skip_summarizer),
        duplicate_matrix=_resolve_optional_path(paths.repo_root, getattr(args, "duplicate_matrix", None)),
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str] | None], Any]:
    script_path = script_path.resolve()
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load module from {script_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)  # type: ignore[call-arg]
    func = getattr(module, attribute, None)
    if not callable(func):
        raise AttributeError(f"Module {module_name} missing callable {attribute}()")
    return func


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _execute_producer(paths: Paths, options: Options) -> ProducerOutcome:
    run_callable = _load_callable(paths.repo_root / PRODUCER_SCRIPT, PRODUCER_MODULE, "run")
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--root",
        str(paths.scan_root),
        "--output-dir",
        str(paths.producer_output_dir),
        "--context-lines",
        str(options.producer_context_lines),
        "--artifacts-to-keep",
        str(options.producer_keep),
        "--log-level",
        options.log_level,
    ]
    if options.producer_with_git:
        argv.append("--with-git")
    if options.producer_strict:
        argv.append("--strict")
    if options.producer_project_packages:
        argv.extend(["--project-packages", *options.producer_project_packages])
    if options.producer_exclude_dirs:
        argv.extend(["--exclude-dirs", *options.producer_exclude_dirs])
    if options.producer_exclude_globs:
        argv.extend(["--exclude-globs", *options.producer_exclude_globs])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("scan_monkey_patches returned unexpected payload")
    run_id = payload.get("run_id")
    run_dir = None
    if isinstance(run_id, str):
        candidate = (paths.producer_output_dir / run_id).resolve()
        run_dir = candidate if candidate.exists() else None
    report_path = None
    matches_path = None
    if run_dir is not None:
        report_candidate = run_dir / "report.json"
        matches_candidate = run_dir / "matches.json"
        if report_candidate.exists():
            report_path = report_candidate
        if matches_candidate.exists():
            matches_path = matches_candidate
    status = payload.get("status") if isinstance(payload.get("status"), str) else None
    total_findings = payload.get("total_findings")
    if not isinstance(total_findings, int):
        total_findings = None
    return ProducerOutcome(
        payload=payload,
        run_dir=run_dir,
        report_path=report_path,
        matches_path=matches_path,
        status=status,
        total_findings=total_findings,
        run_id=run_id if isinstance(run_id, str) else None,
    )


def _execute_consumer(paths: Paths, options: Options, producer: ProducerOutcome | None) -> ConsumerOutcome:
    run_callable = _load_callable(paths.repo_root / CONSUMER_SCRIPT, CONSUMER_MODULE, "run")
    argv: list[str] = [
        "--base-dir",
        str(paths.producer_output_dir),
        "--output-base",
        str(paths.consumer_output_dir),
        "--artifacts-to-keep",
        str(options.consumer_keep),
        "--log-level",
        options.log_level,
    ]
    if producer and producer.run_dir is not None:
        argv.extend(["--scan-dir", str(producer.run_dir)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("classify_monkey_patches returned unexpected payload")
    bundle_dir = Path(payload.get("bundle_dir", "")) if payload.get("bundle_dir") else None
    if bundle_dir and not bundle_dir.exists():
        bundle_dir = None
    bundle_summary = Path(payload.get("bundle_summary", "")) if payload.get("bundle_summary") else None
    if bundle_summary and not bundle_summary.exists():
        bundle_summary = None
    summary_json = bundle_dir / "summary.json" if bundle_dir else None
    if summary_json and not summary_json.exists():
        summary_json = None
    summary_md = bundle_dir / "SUMMARY.md" if bundle_dir else None
    if summary_md and not summary_md.exists():
        summary_md = None
    source = payload.get("source") if isinstance(payload.get("source"), str) else None
    return ConsumerOutcome(
        payload=payload,
        bundle_dir=bundle_dir,
        bundle_summary=bundle_summary,
        summary_json=summary_json,
        summary_markdown=summary_md,
        source=source,
    )


def _execute_aggregator(paths: Paths, options: Options, consumer: ConsumerOutcome | None) -> AggregatorOutcome:
    run_callable = _load_callable(paths.repo_root / AGGREGATOR_SCRIPT, AGGREGATOR_MODULE, "run")
    argv: list[str] = [
        "--consumer-base",
        str(paths.consumer_output_dir),
        "--producer-base",
        str(paths.producer_output_dir),
        "--output-base",
        str(paths.aggregator_output_dir),
        "--artifacts-to-keep",
        str(options.aggregator_keep),
        "--max-runs",
        str(options.trend_max_runs),
        "--log-level",
        options.log_level,
    ]
    if consumer and consumer.summary_json is not None:
        argv.extend(["--consumer-summary", str(consumer.summary_json)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("analyze_monkey_patch_trends returned unexpected payload")
    trend_dir = Path(payload.get("trend_dir", "")) if payload.get("trend_dir") else None
    if trend_dir and not trend_dir.exists():
        trend_dir = None
    trend_json = Path(payload.get("trend_json", "")) if payload.get("trend_json") else None
    if trend_json and not trend_json.exists():
        trend_json = None
    trend_markdown = Path(payload.get("trend_markdown", "")) if payload.get("trend_markdown") else None
    if trend_markdown and not trend_markdown.exists():
        trend_markdown = None
    bundle_summary = Path(payload.get("bundle_summary", "")) if payload.get("bundle_summary") else None
    if bundle_summary and not bundle_summary.exists():
        bundle_summary = None
    consumer_snapshot = Path(payload.get("consumer_snapshot", "")) if payload.get("consumer_snapshot") else None
    if consumer_snapshot and not consumer_snapshot.exists():
        consumer_snapshot = None
    mode = payload.get("mode") if isinstance(payload.get("mode"), str) else None
    return AggregatorOutcome(
        payload=payload,
        trend_dir=trend_dir,
        trend_json=trend_json,
        trend_markdown=trend_markdown,
        bundle_summary=bundle_summary,
        consumer_snapshot=consumer_snapshot,
        mode=mode,
    )


def _execute_summarizer(
    paths: Paths,
    options: Options,
    producer: ProducerOutcome | None,
    consumer: ConsumerOutcome | None,
    aggregator: AggregatorOutcome | None,
) -> SummarizerOutcome:
    run_callable = _load_callable(paths.repo_root / SUMMARIZER_SCRIPT, SUMMARIZER_MODULE, "run")
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--consumer-output-dir",
        str(paths.consumer_output_dir),
        "--producer-output-dir",
        str(paths.producer_output_dir),
        "--aggregator-output-dir",
        str(paths.aggregator_output_dir),
        "--output-dir",
        str(paths.summarizer_output_dir),
        "--artifacts-to-keep",
        str(options.summarizer_keep),
        "--log-level",
        options.log_level,
        "--timestamp",
        options.run_timestamp.isoformat(),
    ]
    if consumer:
        if consumer.summary_json is not None:
            argv.extend(["--consumer-summary", str(consumer.summary_json)])
        if consumer.bundle_summary is not None:
            argv.extend(["--consumer-bundle-summary", str(consumer.bundle_summary)])
    if producer:
        if producer.report_path is not None:
            argv.extend(["--producer-report", str(producer.report_path)])
        if producer.matches_path is not None:
            argv.extend(["--producer-matches", str(producer.matches_path)])
    if aggregator:
        if aggregator.trend_json is not None:
            argv.extend(["--trend-json", str(aggregator.trend_json)])
        if aggregator.trend_markdown is not None:
            argv.extend(["--trend-markdown", str(aggregator.trend_markdown)])
        if aggregator.bundle_summary is not None:
            argv.extend(["--trend-bundle-summary", str(aggregator.bundle_summary)])
    if options.duplicate_matrix is not None:
        argv.extend(["--duplicate-matrix", str(options.duplicate_matrix)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("summarize_monkey_patch_overview returned unexpected payload")
    run_dir = Path(payload.get("run_dir", "")) if payload.get("run_dir") else None
    if run_dir and not run_dir.exists():
        run_dir = None
    artifacts_map: dict[str, Path] = {}
    artifacts_payload = payload.get("artifacts")
    if isinstance(artifacts_payload, dict):
        for name, value in artifacts_payload.items():
            path = Path(value) if isinstance(value, str) else None
            if path and path.exists():
                artifacts_map[name] = path
    slug = payload.get("slug") if isinstance(payload.get("slug"), str) else None
    status = payload.get("status")
    if status not in {"ok", "OK"}:
        raise RuntimeError("Monkey Patch overview summarizer signalled failure")
    return SummarizerOutcome(payload=payload, run_dir=run_dir, artifacts=artifacts_map, slug=slug)


def _register_scripts(registry: CatalogRegistry) -> None:
    registry.register(script_path=str(PRODUCER_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(CONSUMER_SCRIPT), topic=TOPIC_SLUG, role="consumer")
    registry.register(script_path=str(AGGREGATOR_SCRIPT), topic=TOPIC_SLUG, role="aggregator")
    registry.register(script_path=str(SUMMARIZER_SCRIPT), topic=TOPIC_SLUG, role="summarizer")
    registry.register(script_path=str(UTILITY_SCRIPT), topic=TOPIC_SLUG, role="utility")
    registry.register(script_path=str(ORCHESTRATOR_SCRIPT), topic=TOPIC_SLUG, role="orchestrator")


def _summarize_steps(result_steps: Sequence[Any]) -> str:
    lines = ["# Monkey Patch Oversight Run", ""]
    for step in result_steps:
        detail = f" ({step.detail})" if step.detail else ""
        lines.append(f"- {step.name}: {step.status}{detail}")
    return "\n".join(lines) + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)

    registry = CatalogRegistry()
    _register_scripts(registry)

    context = TopicContext(paths=paths, options=options, metadata={})

    producer_holder: dict[str, ProducerOutcome] = {}
    consumer_holder: dict[str, ConsumerOutcome] = {}
    aggregator_holder: dict[str, AggregatorOutcome] = {}
    summarizer_holder: dict[str, SummarizerOutcome] = {}

    def producer_step(_: TopicContext):
        if options.skip_producer:
            return step_skipped(detail="producer step skipped by flag")
        try:
            outcome = _execute_producer(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        producer_holder["value"] = outcome
        context.add_metadata("producer", outcome.payload)
        detail_bits = []
        if outcome.status:
            detail_bits.append(f"status={outcome.status}")
        if outcome.total_findings is not None:
            detail_bits.append(f"findings={outcome.total_findings}")
        detail = ", ".join(detail_bits) if detail_bits else "producer completed"
        step_payload = {
            "status": outcome.status,
            "total_findings": outcome.total_findings,
            "run_id": outcome.run_id,
        }
        return step_success(detail=detail, payload=step_payload)

    def consumer_step(_: TopicContext):
        if options.skip_consumer:
            return step_skipped(detail="consumer step skipped by flag")
        try:
            producer_outcome = producer_holder.get("value")
            outcome = _execute_consumer(paths, options, producer_outcome)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        consumer_holder["value"] = outcome
        context.add_metadata("consumer", outcome.payload)
        detail = f"source={outcome.source}" if outcome.source else "consumer completed"
        step_payload = {
            "bundle_dir": _relativize(outcome.bundle_dir, paths.repo_root),
            "source": outcome.source,
        }
        return step_success(detail=detail, payload=step_payload)

    def aggregator_step(_: TopicContext):
        if options.skip_aggregator:
            return step_skipped(detail="aggregator step skipped by flag")
        try:
            consumer_outcome = consumer_holder.get("value")
            outcome = _execute_aggregator(paths, options, consumer_outcome)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        aggregator_holder["value"] = outcome
        context.add_metadata("aggregator", outcome.payload)
        detail = f"mode={outcome.mode}" if outcome.mode else "trend analysis complete"
        step_payload = {
            "mode": outcome.mode,
            "runs": outcome.payload.get("runs"),
        }
        return step_success(detail=detail, payload=step_payload)

    def summarizer_step(_: TopicContext):
        if options.skip_summarizer:
            return step_skipped(detail="summarizer step skipped by flag")
        try:
            producer_outcome = producer_holder.get("value")
            consumer_outcome = consumer_holder.get("value")
            aggregator_outcome = aggregator_holder.get("value")
            outcome = _execute_summarizer(paths, options, producer_outcome, consumer_outcome, aggregator_outcome)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        summarizer_holder["value"] = outcome
        context.add_metadata("summarizer", outcome.payload)
        detail = f"slug={outcome.slug}" if outcome.slug else "overview artifacts generated"
        step_payload = {
            "slug": outcome.slug,
        }
        return step_success(detail=detail, payload=step_payload)

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="producer", runner=producer_step),
            TopicStep(name="consumer", runner=consumer_step),
            TopicStep(name="aggregator", runner=aggregator_step),
            TopicStep(name="summarizer", runner=summarizer_step, continue_on_failure=False),
        ]
    )

    result = pipeline.run(context)
    try:
        result.raise_for_failure()
    except RuntimeError as exc:
        LOGGER.error("Pipeline failed: %s", exc)
        return 1

    producer_outcome = producer_holder.get("value")
    consumer_outcome = consumer_holder.get("value")
    aggregator_outcome = aggregator_holder.get("value")
    summarizer_outcome = summarizer_holder.get("value")

    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    telemetry = build_pipeline_telemetry(result, viewer=VIEWER_SLUG, topic=HEALTHVIEW_TOPIC, run_slug=run_slug)
    completed_at = datetime.now(timezone.utc)
    telemetry_payload = telemetry.as_dict()

    artifacts_section = {
        "producer_report": _relativize(producer_outcome.report_path if producer_outcome else None, paths.repo_root),
        "producer_matches": _relativize(
            producer_outcome.matches_path if producer_outcome else None, paths.repo_root
        ),
        "consumer_bundle": _relativize(consumer_outcome.bundle_dir if consumer_outcome else None, paths.repo_root),
        "consumer_summary": _relativize(
            consumer_outcome.bundle_summary if consumer_outcome else None, paths.repo_root
        ),
        "trend_dir": _relativize(aggregator_outcome.trend_dir if aggregator_outcome else None, paths.repo_root),
        "trend_json": _relativize(aggregator_outcome.trend_json if aggregator_outcome else None, paths.repo_root),
        "trend_markdown": _relativize(
            aggregator_outcome.trend_markdown if aggregator_outcome else None, paths.repo_root
        ),
        "summarizer_run": _relativize(
            summarizer_outcome.run_dir if summarizer_outcome else None, paths.repo_root
        ),
    }
    if summarizer_outcome:
        for name, path in summarizer_outcome.artifacts.items():
            artifacts_section[f"overview_{name}"] = _relativize(path, paths.repo_root)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "scan_root": _relativize(paths.scan_root, paths.repo_root),
            "duplicate_matrix": _relativize(options.duplicate_matrix, paths.repo_root),
            "trend_max_runs": options.trend_max_runs,
            "producer_with_git": options.producer_with_git,
            "producer_strict": options.producer_strict,
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
    }

    summary_markdown = _summarize_steps(result.steps)

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: manifest),
        ReportArtifact(filename="summary.md", kind="text", content=lambda: summary_markdown),
        ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
    ]
    result_artifacts = write_report_artifacts(
        stem=HEALTHVIEW_TOPIC,
        timestamp=options.run_timestamp,
        output_dir=paths.healthview_root,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer="",
        topic="",
    )

    artifact_metrics = measure_artifact_directory(result_artifacts.run_dir)
    metrics_section = telemetry_payload.setdefault("metrics", {})
    metrics_section.update(artifact_metrics.as_dict())
    manifest["telemetry"] = telemetry_payload
    manifest["metrics"] = dict(metrics_section)

    manifest_path = result_artifacts.artifacts["manifest.json"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    telemetry_path = result_artifacts.artifacts["telemetry.json"]
    telemetry_path.write_text(json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    LOGGER.info("Monkey Patch Oversight orchestrator complete (slug=%s)", run_slug)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]
