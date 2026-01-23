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
from typing import Any, Callable, Sequence, cast

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

# TOPIC_SLUG is the hyphenated CLI/catalog token.
TOPIC_SLUG = "fault-diagnostics"
# HEALTHVIEW_TOPIC is the on-disk bundle directory token used under healthview/*_reports/<topic>/.
HEALTHVIEW_TOPIC = "fault_diagnostics_overview"
PRODUCER_TOPIC_SLUG = "faulthandler_reports"
CONSUMER_TOPIC_SLUG = "fault_artifacts"
SUMMARIZER_TOPIC_SLUG = HEALTHVIEW_TOPIC
SCHEMA_VERSION = 1

PRODUCER_SCRIPT = Path(".repo_studios/scripts/producers/collect_faulthandler_reports.py")
PRODUCER_MODULE = "scripts.producers.collect_faulthandler_reports"
CONSUMER_SCRIPT = Path(".repo_studios/scripts/consumers/generate_fault_artifacts.py")
CONSUMER_MODULE = "scripts.consumers.generate_fault_artifacts"
SUMMARIZER_SCRIPT = Path(".repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py")
SUMMARIZER_MODULE = "command_center.scripts.summarizers.summarize_fault_diagnostics_overview"
ORCHESTRATOR_SCRIPT = Path(".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py")

DEFAULT_RUNS_DIR = build_topic_path("rawview", "fault_diagnostics")
DEFAULT_PRODUCER_OUTPUT = build_topic_path("producer", PRODUCER_TOPIC_SLUG)
DEFAULT_CONSUMER_OUTPUT = build_topic_path("consumer", CONSUMER_TOPIC_SLUG)
DEFAULT_SUMMARIZER_OUTPUT = build_topic_path("summarizer", SUMMARIZER_TOPIC_SLUG)
DEFAULT_ORCHESTRATOR_OUTPUT = build_topic_path("orchestrator", HEALTHVIEW_TOPIC)


@dataclass(frozen=True)
class Paths:
    """Resolved path configuration for orchestrator execution.

    Attributes:
        repo_root: Repository root directory.
        runs_dir: Directory containing faulthandler run outputs.
        producer_output_dir: Producer report output location.
        consumer_output_dir: Consumer artifact output location.
        summarizer_output_dir: Summarizer output location.
        orchestrator_output_dir: Orchestrator manifest output location.
    """

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
    """Retention budget values extracted from CLI arguments.

    Attributes:
        artifacts_to_keep: Number of orchestrator artifact bundles to retain.
        producer_keep: Retention budget for producer reports.
        consumer_keep: Retention budget for consumer artifacts.
        summarizer_keep: Retention budget for summarizer bundles.
    """

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
    """Runtime options for orchestrator execution.

    Attributes:
        log_level: Logging verbosity level.
        artifacts_to_keep: Number of orchestrator artifact bundles to retain.
        producer_keep: Retention budget for producer reports.
        consumer_keep: Retention budget for consumer artifacts.
        summarizer_keep: Retention budget for summarizer bundles.
        skip_producer: Skip producer step if True.
        skip_consumer: Skip consumer step if True.
        skip_summarizer: Skip summarizer step if True.
        run_dir: Explicit faulthandler run directory override.
        reuse_report: Explicit producer report to reuse.
        producer_top_frames: Override producer top frame depth.
        run_timestamp: UTC timestamp for artifact generation.
    """

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
    """Parse command-line arguments for orchestrator.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Parsed argument namespace.
    """
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
    """Parse ISO-8601 timestamp or return current UTC time.

    Args:
        raw: ISO-8601 timestamp string or None.

    Returns:
        Parsed datetime in UTC.

    Raises:
        SystemExit: If timestamp format is invalid.
    """
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
    """Resolve optional path relative to repo root.

    Args:
        repo_root: Repository root for relative resolution.
        raw: Raw path string or None.

    Returns:
        Resolved Path or None.
    """
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def build_paths(args: argparse.Namespace) -> Paths:
    """Construct Paths dataclass from parsed CLI arguments.

    Args:
        args: Parsed argument namespace from parse_args().

    Returns:
        Resolved path configuration.
    """
    result = build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))
    return Paths(**{f.name: getattr(result, f.name) for f in result.__dataclass_fields__.values()})


def build_options(args: argparse.Namespace, *, paths: Paths) -> Options:
    """Construct Options from parsed CLI arguments.

    Args:
        args: Parsed argument namespace from parse_args().
        paths: Resolved Paths instance.

    Returns:
        Fully resolved Options instance.
    """
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
    """Configure root logger with specified level.

    Args:
        level: Logging level name (e.g., "DEBUG", "INFO").
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
        force=True,
    )


def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str] | None], Any]:
    """Dynamically load a callable from a script module.

    Args:
        script_path: Path to the Python script.
        module_name: Module name for sys.modules registration.
        attribute: Name of the callable attribute to retrieve.

    Returns:
        Loaded callable.

    Raises:
        ImportError: If module cannot be loaded.
        AttributeError: If callable not found.
    """
    script_abs = script_path.resolve()
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, script_abs)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load module from {script_abs}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    func = getattr(module, attribute, None)
    if not callable(func):
        raise AttributeError(f"Module {module_name} missing callable {attribute}()")
    return cast(Callable[[Sequence[str] | None], Any], func)


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    """Convert path to repo-relative POSIX string.

    Args:
        path: Path to relativize or None.
        repo_root: Repository root for relative resolution.

    Returns:
        Relative POSIX path string or None.
    """
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


@dataclass(frozen=True)
class ProducerOutcome:
    """Result from producer step execution.

    Attributes:
        payload: Raw return dict from producer run().
        run_dir: Faulthandler run directory processed.
        bundle_dir: Path to generated producer bundle directory.
        repeat_offender: Count of repeat offender signatures.
        signatures: Total signature count.
    """

    payload: dict[str, Any]
    run_dir: Path | None
    bundle_dir: Path | None
    repeat_offender: int | None
    signatures: int | None


@dataclass(frozen=True)
class ConsumerOutcome:
    """Result from consumer step execution.

    Attributes:
        payload: Raw return dict from consumer run().
        bundle_dir: Path to generated consumer bundle directory.
        summary_markdown: Path to summary.md within bundle.
        repeat_offender: Count of repeat offender signatures.
        signatures: Total signature count.
    """

    payload: dict[str, Any]
    bundle_dir: Path | None
    summary_markdown: Path | None
    repeat_offender: int | None
    signatures: int | None


@dataclass(frozen=True)
class SummarizerOutcome:
    """Result from summarizer step execution.

    Attributes:
        payload: Raw return dict from summarizer run().
        run_dir: Path to generated summarizer output directory.
        artifacts: Mapping of artifact names to paths.
        slug: Timestamp slug for the output bundle.
    """

    payload: dict[str, Any]
    run_dir: Path | None
    artifacts: dict[str, Path]
    slug: str | None


def _execute_producer(paths: Paths, options: Options) -> ProducerOutcome:
    """Execute faulthandler report producer step.

    Args:
        paths: Resolved path configuration.
        options: Runtime options.

    Returns:
        Producer execution outcome.

    Raises:
        RuntimeError: If producer returns unexpected payload.
    """
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
    bundle_dir = Path(payload.get("output_dir", "")) if payload.get("output_dir") else None
    if bundle_dir and not bundle_dir.exists():
        bundle_dir = None
    if not payload.get("manifest"):
        bundle_dir = None
    repeat_offender = payload.get("repeat_offender_signatures")
    if not isinstance(repeat_offender, int):
        repeat_offender = None
    signatures = payload.get("signatures")
    if not isinstance(signatures, int):
        signatures = None
    return ProducerOutcome(
        payload=payload,
        run_dir=run_dir,
        bundle_dir=bundle_dir,
        repeat_offender=repeat_offender,
        signatures=signatures,
    )


def _execute_consumer(paths: Paths, options: Options, producer: ProducerOutcome | None) -> ConsumerOutcome:
    """Execute fault artifact consumer step.

    Args:
        paths: Resolved path configuration.
        options: Runtime options.
        producer: Producer outcome for chaining, or None.

    Returns:
        Consumer execution outcome.

    Raises:
        RuntimeError: If consumer returns unexpected payload.
    """
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
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_fault_artifacts returned unexpected payload")
    bundle_dir = Path(payload.get("consumer_report", "")) if payload.get("consumer_report") else None
    if bundle_dir and not bundle_dir.exists():
        bundle_dir = None
    summary_markdown = bundle_dir / "summary.md" if bundle_dir else None
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
    """Execute fault diagnostics summarizer step.

    Args:
        paths: Resolved path configuration.
        options: Runtime options.
        producer: Producer outcome for artifact references, or None.
        consumer: Consumer outcome for artifact references, or None.

    Returns:
        Summarizer execution outcome.

    Raises:
        RuntimeError: If summarizer returns unexpected payload or fails.
    """
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
    """Register topic scripts in catalog registry.

    Args:
        registry: CatalogRegistry instance to populate.
    """
    registry.register(script_path=str(PRODUCER_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(CONSUMER_SCRIPT), topic=TOPIC_SLUG, role="consumer")
    registry.register(script_path=str(SUMMARIZER_SCRIPT), topic=TOPIC_SLUG, role="summarizer")
    registry.register(script_path=str(ORCHESTRATOR_SCRIPT), topic=TOPIC_SLUG, role="orchestrator")


def _summarize_steps(result_steps: Sequence[Any]) -> str:
    """Legacy wrapper for summary rendering.

    Note:
        Prefer `_build_summary_markdown` which includes artifacts and snapshot.
    """
    lines = ["# Fault Diagnostics Run", ""]
    for step in result_steps:
        detail = f" ({step.detail})" if step.detail else ""
        lines.append(f"- {step.name}: {step.status}{detail}")
    return "\n".join(lines) + "\n"


def _status_badge(status: str) -> str:
    """Format a status string with a Docs Health-style badge."""
    normalized = (status or "").lower()
    if normalized == "success":
        return "✅ success"
    if normalized == "skipped":
        return "⏭️ skipped"
    if normalized == "failed":
        return "❌ failed"
    return status


def _load_json(path: Path | None) -> dict[str, Any] | None:
    """Load a JSON file, returning None when missing/unreadable."""
    if path is None:
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except Exception:  # pragma: no cover - best effort for summary rendering
        return None


def _build_summary_markdown(
    *,
    run_slug: str,
    completed_at: datetime,
    result_steps: Sequence[Any],
    artifacts_section: dict[str, str | None],
    summarizer_manifest: dict[str, Any] | None,
) -> str:
    """Generate a Docs Health-style Markdown summary for the orchestrator bundle."""
    step_index: dict[str, Any] = {}
    for step in result_steps:
        name = getattr(step, "name", None)
        if isinstance(name, str):
            step_index[name] = step

    lines: list[str] = []
    lines.append("# Fault Diagnostics Run")
    lines.append("")
    lines.append(f"Run: `{run_slug}` | Completed: {completed_at.isoformat()}")

    lines.append("")
    lines.append("## Pipeline Status")
    lines.append("")
    lines.append("| Step | Status | Detail |")
    lines.append("| --- | --- | --- |")
    for step in result_steps:
        detail = step.detail or ""
        lines.append(f"| {step.name} | {_status_badge(step.status)} | {detail} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Artifacts")
    lines.append("")
    producer_bundle = artifacts_section.get("producer_report")
    consumer_bundle = artifacts_section.get("consumer_bundle")
    summarizer_run = artifacts_section.get("summarizer_run")
    overview_manifest = artifacts_section.get("overview_manifest.json")
    overview_summary = artifacts_section.get("overview_summary.md")
    overview_telemetry = artifacts_section.get("overview_telemetry.json")

    lines.append(f"- Producer bundle: `{producer_bundle}`" if producer_bundle else "- Producer bundle: (none)")
    lines.append(f"- Consumer bundle: `{consumer_bundle}`" if consumer_bundle else "- Consumer bundle: (none)")
    lines.append(f"- Summarizer bundle: `{summarizer_run}`" if summarizer_run else "- Summarizer bundle: (none)")
    if overview_manifest or overview_summary or overview_telemetry:
        lines.append(
            f"- Overview: manifest=`{overview_manifest}` summary=`{overview_summary}` telemetry=`{overview_telemetry}`"
        )

    def render_step_section(step_name: str, *, artifact: str | None, extra_artifacts: list[str] | None = None) -> None:
        step = step_index.get(step_name)
        status = getattr(step, "status", "") if step else ""
        detail = getattr(step, "detail", "") if step else ""
        payload = getattr(step, "payload", None) if step else None

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## {step_name.capitalize()}")
        lines.append("")
        lines.append(f"Status: {_status_badge(str(status))}" + (f" — {detail}" if detail else ""))
        lines.append("")
        lines.append(f"**Artifact:** `{artifact}`" if artifact else "**Artifact:** (none)")
        if extra_artifacts:
            for entry in extra_artifacts:
                lines.append(f"- {entry}")

        if isinstance(payload, dict) and payload:
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("| --- | ---: |")
            for key, value in payload.items():
                lines.append(f"| {key} | {value} |")

        if str(status).lower() == "failed":
            lines.append("")
            lines.append("**Concerns:** ❌ step failed")

    render_step_section(
        "producer",
        artifact=producer_bundle,
    )
    render_step_section(
        "consumer",
        artifact=consumer_bundle,
    )
    summarizer_extras: list[str] = []
    if overview_manifest:
        summarizer_extras.append(f"manifest: `{overview_manifest}`")
    if overview_summary:
        summarizer_extras.append(f"summary: `{overview_summary}`")
    if overview_telemetry:
        summarizer_extras.append(f"telemetry: `{overview_telemetry}`")
    render_step_section(
        "summarizer",
        artifact=summarizer_run,
        extra_artifacts=summarizer_extras if summarizer_extras else None,
    )

    notes: list[str] = []
    snapshot_metrics: dict[str, Any] | None = None
    baseline: dict[str, Any] | None = None
    if summarizer_manifest:
        raw_notes = summarizer_manifest.get("notes")
        if isinstance(raw_notes, list):
            notes = [str(item) for item in raw_notes if item]
        raw_metrics = summarizer_manifest.get("metrics")
        snapshot_metrics = raw_metrics if isinstance(raw_metrics, dict) else None
        raw_baseline = summarizer_manifest.get("baseline")
        baseline = raw_baseline if isinstance(raw_baseline, dict) else None

    if snapshot_metrics:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Snapshot")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | ---: |")
        for key in (
            "signature_count",
            "active_signature_count",
            "repeat_offender",
            "multi_hit",
            "single_hit",
            "thread_block_count",
        ):
            if key in snapshot_metrics:
                lines.append(f"| {key} | {snapshot_metrics.get(key)} |")

    if baseline:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Baseline")
        lines.append("")
        bundle = baseline.get("bundle")
        lines.append(f"- Previous Bundle: `{bundle}`" if bundle else "- Previous Bundle: (none)")
        summary = baseline.get("summary")
        if isinstance(summary, dict):
            new_ids = summary.get("new_signature_ids")
            removed_ids = summary.get("removed_signature_ids")
            if isinstance(new_ids, list):
                lines.append(f"- New Signatures: {len(new_ids)}")
            if isinstance(removed_ids, list):
                lines.append(f"- Retired Signatures: {len(removed_ids)}")

    if notes:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Concerns")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")

    lines.append("")
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    """Execute fault diagnostics orchestrator pipeline.

    Chain producer → consumer → summarizer steps and write
    HOP-compliant orchestrator artifacts.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).

    Note:
        Output is written to
        ``.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/``.
    """
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)

    LOGGER.debug(
        "Resolved paths: runs_dir=%s producer_output_dir=%s consumer_output_dir=%s summarizer_output_dir=%s orchestrator_output_dir=%s",
        paths.runs_dir,
        paths.producer_output_dir,
        paths.consumer_output_dir,
        paths.summarizer_output_dir,
        paths.orchestrator_output_dir,
    )
    LOGGER.debug(
        "Resolved options: artifacts_to_keep=%s producer_keep=%s consumer_keep=%s summarizer_keep=%s skip_producer=%s skip_consumer=%s skip_summarizer=%s run_timestamp=%s",
        options.artifacts_to_keep,
        options.producer_keep,
        options.consumer_keep,
        options.summarizer_keep,
        options.skip_producer,
        options.skip_consumer,
        options.skip_summarizer,
        options.run_timestamp.isoformat(),
    )

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
        "producer_report": _relativize(producer_outcome.bundle_dir if producer_outcome else None, paths.repo_root),
        "consumer_bundle": _relativize(consumer_outcome.bundle_dir if consumer_outcome else None, paths.repo_root),
        "consumer_bundle_summary": _relativize(consumer_outcome.summary_markdown if consumer_outcome else None, paths.repo_root),
        "summarizer_run": _relativize(summarizer_outcome.run_dir if summarizer_outcome else None, paths.repo_root),
    }
    if summarizer_outcome:
        for name, path in summarizer_outcome.artifacts.items():
            artifacts_section[f"overview_{name}"] = _relativize(path, paths.repo_root)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": HEALTHVIEW_TOPIC,
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

    summarizer_manifest_path: Path | None = None
    if summarizer_outcome:
        summarizer_manifest_path = summarizer_outcome.artifacts.get("manifest.json")
    summarizer_manifest_payload = _load_json(summarizer_manifest_path)
    summary_markdown = _build_summary_markdown(
        run_slug=run_slug,
        completed_at=completed_at,
        result_steps=result.steps,
        artifacts_section=artifacts_section,
        summarizer_manifest=summarizer_manifest_payload,
    )

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: manifest),
        ReportArtifact(filename="summary.md", kind="text", content=lambda: summary_markdown),
        ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
    ]
    LOGGER.debug(
        "Writing orchestrator artifacts: output_dir=%s viewer=%r topic=%r timestamp=%s",
        paths.orchestrator_output_dir,
        "",
        "",
        options.run_timestamp.isoformat(),
    )
    result_artifacts = write_report_artifacts(
        stem=TOPIC_SLUG,
        timestamp=options.run_timestamp,
        output_dir=paths.orchestrator_output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer="",
        topic="",
    )
    LOGGER.debug("Orchestrator artifacts written: run_dir=%s slug=%s", result_artifacts.run_dir, result_artifacts.slug)

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
    """CLI entry point for fault diagnostics orchestrator.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].
    """
    raise SystemExit(run(argv))


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]


if __name__ == "__main__":
    main()
