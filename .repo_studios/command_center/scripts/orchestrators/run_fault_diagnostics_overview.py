#!/usr/bin/env python3
"""Topic orchestrator for the Fault Diagnostics workflow.

Writes manifest, summary, and telemetry bundles to
`.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/`.
This runner sequentially executes faulthandler collection, artifact generation, and summary emission.
Most runs complete within three to five minutes, with producer log replay accounting for the majority of
execution time; the summarizer step is tolerant so investigations continue even when only warnings
are raised.
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
from libraries.report_paths import build_topic_path, HEALTHVIEW_ROOT

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "fault_diagnostics_overview"
PRODUCER_TOPIC_SLUG = "faulthandler_reports"
CONSUMER_TOPIC_SLUG = "fault_artifacts"
SUMMARIZER_TOPIC_SLUG = "fault_diagnostics_overview"
SCHEMA_VERSION = 1

PRODUCER_SCRIPT = Path(".repo_studios/scripts/producers/collect_faulthandler_reports.py")
PRODUCER_MODULE = "scripts.producers.collect_faulthandler_reports"
CONSUMER_SCRIPT = Path(".repo_studios/scripts/consumers/generate_fault_artifacts.py")
CONSUMER_MODULE = "scripts.consumers.generate_fault_artifacts"
SUMMARIZER_SCRIPT = Path(".repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py")
SUMMARIZER_MODULE = "command_center.scripts.summarizers.summarize_fault_diagnostics_overview"
ORCHESTRATOR_SCRIPT = Path(".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py")

DEFAULT_RUNS_DIR = build_topic_path("rawview", "fault_diagnostics_runs")
DEFAULT_PRODUCER_OUTPUT = build_topic_path("producer", PRODUCER_TOPIC_SLUG)
DEFAULT_CONSUMER_OUTPUT = build_topic_path("consumer", CONSUMER_TOPIC_SLUG)
DEFAULT_SUMMARIZER_OUTPUT = build_topic_path("summarizer", SUMMARIZER_TOPIC_SLUG)
DEFAULT_ORCHESTRATOR_OUTPUT = build_topic_path("orchestrator", TOPIC_SLUG)


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    runs_dir: Path
    producer_output_dir: Path
    consumer_output_dir: Path
    summarizer_output_dir: Path
    orchestrator_output_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "runs_dir": PathSpec(field="runs_dir", default=DEFAULT_RUNS_DIR, ensure_dir=False, within_repo=False),
        "producer_output_dir": PathSpec(
            field="producer_output_dir", default=DEFAULT_PRODUCER_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "consumer_output_dir": PathSpec(
            field="consumer_output_dir", default=DEFAULT_CONSUMER_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "summarizer_output_dir": PathSpec(
            field="summarizer_output_dir", default=DEFAULT_SUMMARIZER_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "orchestrator_output_dir": PathSpec(
            field="orchestrator_output_dir", default=DEFAULT_ORCHESTRATOR_OUTPUT, ensure_dir=True, within_repo=False
        ),
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int
    summarizer_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "producer_keep": KeepSpec(field="producer_artifacts_to_keep", minimum=1),
        "consumer_keep": KeepSpec(field="consumer_artifacts_to_keep", minimum=1),
        "summarizer_keep": KeepSpec(field="summarizer_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int
    summarizer_keep: int
    skip_producer: bool
    skip_consumer: bool
    skip_summarizer: bool
    run_dir: Path | None
    reuse_report: Path | None
    producer_top_frames: int | None
    run_timestamp: datetime


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    parser.add_argument("--run-dir", help="Explicit faulthandler run directory to process")
    parser.add_argument("--producer-output-dir", default=str(DEFAULT_PRODUCER_OUTPUT))
    parser.add_argument("--consumer-output-dir", default=str(DEFAULT_CONSUMER_OUTPUT))
    parser.add_argument("--summarizer-output-dir", default=str(DEFAULT_SUMMARIZER_OUTPUT))
    parser.add_argument("--orchestrator-output-dir", default=str(DEFAULT_ORCHESTRATOR_OUTPUT))
    parser.add_argument("--artifacts-to-keep", type=int, default=3, help="Retention budget for manifest artifacts")
    parser.add_argument("--producer-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--consumer-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--summarizer-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--reuse-report", help="Reuse an existing producer report JSON")
    parser.add_argument("--producer-top-frames", type=int, help="Override the producer top frame depth")
    parser.add_argument("--skip-producer", action="store_true")
    parser.add_argument("--skip-consumer", action="store_true")
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


def _resolve_path(repo_root: Path, raw: str | None) -> Path | None:
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
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        producer_keep=keep_values.producer_keep,
        consumer_keep=keep_values.consumer_keep,
        summarizer_keep=keep_values.summarizer_keep,
        skip_producer=bool(args.skip_producer),
        skip_consumer=bool(args.skip_consumer),
        skip_summarizer=bool(args.skip_summarizer),
        run_dir=_resolve_path(paths.repo_root, getattr(args, "run_dir", None)),
        reuse_report=_resolve_path(paths.repo_root, getattr(args, "reuse_report", None)),
        producer_top_frames=int(args.producer_top_frames) if args.producer_top_frames is not None else None,
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str] | None], Any]:
    script_abs = script_path.resolve()
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, script_abs)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load module from {script_abs}")
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


@dataclass(frozen=True)
class ProducerOutcome:
    payload: dict[str, Any]
    run_dir: Path | None
    report_path: Path | None
    repeat_offender: int | None
    signatures: int | None


@dataclass(frozen=True)
class ConsumerOutcome:
    payload: dict[str, Any]
    bundle_dir: Path | None
    bundle_summary: Path | None
    summary_json: Path | None
    summary_markdown: Path | None
    repeat_offender: int | None
    signatures: int | None


@dataclass(frozen=True)
class SummarizerOutcome:
    payload: dict[str, Any]
    run_dir: Path | None
    artifacts: dict[str, Path]
    slug: str | None


def _execute_producer(paths: Paths, options: Options) -> ProducerOutcome:
    run_callable = _load_callable(paths.repo_root / PRODUCER_SCRIPT, PRODUCER_MODULE, "run")
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--runs-dir",
        str(paths.runs_dir),
        "--output-dir",
        str(paths.producer_output_dir),
        "--artifacts-to-keep",
        str(options.producer_keep),
        "--log-level",
        options.log_level,
    ]
    if options.run_dir is not None:
        argv.extend(["--run-dir", str(options.run_dir)])
    if options.producer_top_frames is not None:
        argv.extend(["--top-frames", str(options.producer_top_frames)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("collect_faulthandler_reports returned unexpected payload")
    run_dir = Path(payload.get("run_dir", "")) if payload.get("run_dir") else None
    if run_dir and not run_dir.exists():
        run_dir = None
    report_path = Path(payload.get("report", "")) if payload.get("report") else None
    if report_path and not report_path.exists():
        report_path = None
    repeat_offender = payload.get("repeat_offender_signatures")
    if not isinstance(repeat_offender, int):
        repeat_offender = None
    signatures = payload.get("signatures")
    if not isinstance(signatures, int):
        signatures = None
    return ProducerOutcome(
        payload=payload,
        run_dir=run_dir,
        report_path=report_path,
        repeat_offender=repeat_offender,
        signatures=signatures,
    )


def _execute_consumer(paths: Paths, options: Options, producer: ProducerOutcome | None) -> ConsumerOutcome:
    run_callable = _load_callable(paths.repo_root / CONSUMER_SCRIPT, CONSUMER_MODULE, "run")
    argv: list[str] = [
        "--output-dir",
        str(paths.consumer_output_dir),
        "--artifacts-to-keep",
        str(options.consumer_keep),
        "--log-level",
        options.log_level,
    ]
    source_outdir: Path | None = None
    if options.run_dir is not None:
        source_outdir = options.run_dir
    elif producer and producer.run_dir is not None:
        source_outdir = producer.run_dir
    if source_outdir is not None:
        argv.extend(["--outdir", str(source_outdir)])
    if options.reuse_report is not None:
        argv.extend(["--report", str(options.reuse_report)])
    elif producer and producer.report_path is not None:
        argv.extend(["--report", str(producer.report_path)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_fault_artifacts returned unexpected payload")
    bundle_dir = Path(payload.get("consumer_report", "")) if payload.get("consumer_report") else None
    if bundle_dir and not bundle_dir.exists():
        bundle_dir = None
    bundle_summary_path = Path(payload.get("bundle_summary", "")) if payload.get("bundle_summary") else None
    if bundle_summary_path and not bundle_summary_path.exists():
        bundle_summary_path = None
    summary_json = bundle_dir / "summary.json" if bundle_dir else None
    if summary_json and not summary_json.exists():
        summary_json = None
    summary_markdown = bundle_dir / "SUMMARY.md" if bundle_dir else None
    if summary_markdown and not summary_markdown.exists():
        summary_markdown = None
    repeat_offender = payload.get("repeat_offender_signatures")
    if not isinstance(repeat_offender, int):
        repeat_offender = None
    signatures = payload.get("signatures")
    if not isinstance(signatures, int):
        signatures = None
    return ConsumerOutcome(
        payload=payload,
        bundle_dir=bundle_dir,
        bundle_summary=bundle_summary_path,
        summary_json=summary_json,
        summary_markdown=summary_markdown,
        repeat_offender=repeat_offender,
        signatures=signatures,
    )


def _execute_summarizer(
    paths: Paths,
    options: Options,
    producer: ProducerOutcome | None,
    consumer: ConsumerOutcome | None,
) -> SummarizerOutcome:
    run_callable = _load_callable(paths.repo_root / SUMMARIZER_SCRIPT, SUMMARIZER_MODULE, "run")
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--consumer-output-dir",
        str(paths.consumer_output_dir),
        "--producer-output-dir",
        str(paths.producer_output_dir),
        "--output-dir",
        str(paths.summarizer_output_dir),
        "--artifacts-to-keep",
        str(options.summarizer_keep),
        "--log-level",
        options.log_level,
        "--timestamp",
        options.run_timestamp.isoformat(),
    ]
    if consumer and consumer.summary_json is not None:
        argv.extend(["--consumer-summary", str(consumer.summary_json)])
    if consumer and consumer.bundle_summary is not None:
        argv.extend(["--consumer-bundle-summary", str(consumer.bundle_summary)])
    if producer and producer.report_path is not None:
        argv.extend(["--producer-report", str(producer.report_path)])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("summarize_fault_diagnostics_overview returned unexpected payload")
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
        raise RuntimeError("Fault Diagnostics overview summarizer signalled failure")
    return SummarizerOutcome(payload=payload, run_dir=run_dir, artifacts=artifacts_map, slug=slug)


def _register_scripts(registry: CatalogRegistry) -> None:
    registry.register(script_path=str(PRODUCER_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(CONSUMER_SCRIPT), topic=TOPIC_SLUG, role="consumer")
    registry.register(script_path=str(SUMMARIZER_SCRIPT), topic=TOPIC_SLUG, role="summarizer")
    registry.register(script_path=str(ORCHESTRATOR_SCRIPT), topic=TOPIC_SLUG, role="orchestrator")


def _summarize_steps(result_steps: Sequence[Any]) -> str:
    lines = ["# Fault Diagnostics Run", ""]
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
        if outcome.signatures is not None:
            detail_bits.append(f"signatures={outcome.signatures}")
        if outcome.repeat_offender is not None:
            detail_bits.append(f"repeat_offender={outcome.repeat_offender}")
        detail = ", ".join(detail_bits) if detail_bits else "producer completed"
        payload = {
            "signatures": outcome.signatures,
            "repeat_offender": outcome.repeat_offender,
        }
        return step_success(detail=detail, payload=payload)

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
        detail_bits = []
        if outcome.signatures is not None:
            detail_bits.append(f"signatures={outcome.signatures}")
        if outcome.repeat_offender is not None:
            detail_bits.append(f"repeat_offender={outcome.repeat_offender}")
        detail = ", ".join(detail_bits) if detail_bits else "consumer completed"
        payload = {
            "signatures": outcome.signatures,
            "repeat_offender": outcome.repeat_offender,
        }
        return step_success(detail=detail, payload=payload)

    def summarizer_step(_: TopicContext):
        if options.skip_summarizer:
            return step_skipped(detail="summarizer step skipped by flag")
        try:
            producer_outcome = producer_holder.get("value")
            consumer_outcome = consumer_holder.get("value")
            outcome = _execute_summarizer(paths, options, producer_outcome, consumer_outcome)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        summarizer_holder["value"] = outcome
        context.add_metadata("summarizer", outcome.payload)
        detail = f"slug={outcome.slug}" if outcome.slug else "overview artifacts generated"
        payload = {"slug": outcome.slug}
        return step_success(detail=detail, payload=payload)

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="producer", runner=producer_step),
            TopicStep(name="consumer", runner=consumer_step),
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
    summarizer_outcome = summarizer_holder.get("value")

    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    telemetry = build_pipeline_telemetry(result, viewer="healthview", topic=TOPIC_SLUG, run_slug=run_slug)
    completed_at = datetime.now(timezone.utc)
    telemetry_payload = telemetry.as_dict()

    artifacts_section = {
        "producer_report": _relativize(producer_outcome.report_path if producer_outcome else None, paths.repo_root),
        "consumer_bundle": _relativize(consumer_outcome.bundle_dir if consumer_outcome else None, paths.repo_root),
        "consumer_bundle_summary": _relativize(
            consumer_outcome.bundle_summary if consumer_outcome else None, paths.repo_root
        ),
        "summarizer_run": _relativize(summarizer_outcome.run_dir if summarizer_outcome else None, paths.repo_root),
    }
    if summarizer_outcome:
        for name, path in summarizer_outcome.artifacts.items():
            artifacts_section[f"overview_{name}"] = _relativize(path, paths.repo_root)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "runs_dir": _relativize(paths.runs_dir, paths.repo_root),
            "run_dir": _relativize(options.run_dir, paths.repo_root),
            "reuse_report": _relativize(options.reuse_report, paths.repo_root),
            "producer_top_frames": options.producer_top_frames,
            "skip_producer": options.skip_producer,
            "skip_consumer": options.skip_consumer,
            "skip_summarizer": options.skip_summarizer,
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
        stem=TOPIC_SLUG,
        timestamp=options.run_timestamp,
        output_dir=paths.orchestrator_output_dir,
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

    LOGGER.info("Fault Diagnostics orchestrator complete (slug=%s)", run_slug)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]
