#!/usr/bin/env python
"""Stage 11.1 orchestrator for Available Scripts holding area.

Coordinates execution of scripts in the Stage 11.1 holding area, executing
producers first, then consumers. Scripts without ``run(argv)`` entry points
or in deprecated/utility status are excluded.

Execution flow:

1. Phase 1 — Producers (parallel-capable):
   - validate_import_boundaries.py (ASR-005)
   - check_inventory_health.py (ASR-007)
   - validate_inventory.py (ASR-008)
   - render_inventory_views.py (ASR-010)
   - generate_lizard_report.py (ASR-011)

2. Phase 2 — Consumers (depends on producers):
   - generate_anchor_health_report.py (ASR-001)

Excluded scripts:

- ASR-002, ASR-003, ASR-004: Utilities (invoked by other scripts)
- ASR-006: Library module (no CLI)
- ASR-009: Deprecated summarizer
- ASR-013: Library module (no CLI)

Output bundle is written to::

    .repo_studios/reports/healthview/orchestrator_reports/available_scripts_oversight/<YYYYMMDD-HHMM>/

Required artifacts: manifest.json, summary.md, telemetry.json.

Usage::

    python run_available_scripts_oversight.py --repo-root /path/to/repo
    python run_available_scripts_oversight.py --skip-consumers
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

# Library imports from command center
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
    build_topic_path,
    build_topic_pipeline,
    measure_artifact_directory,
    step_failed,
    step_skipped,
    step_success,
    write_report_artifacts,
)

LOGGER = logging.getLogger(__name__)

# --- Topic constants -----------------------------------------------------------
TOPIC_SLUG = "available-scripts-oversight"
HEALTHVIEW_TOPIC = "available_scripts_oversight"
SCHEMA_VERSION = 1


# --- Script configuration ------------------------------------------------------
@dataclass
class ScriptConfig:
    """Configuration for a script to be executed.

    Attributes:
        name: Script identifier.
        path: Relative path from repo root.
        supports_artifacts_to_keep: Whether script accepts --artifacts-to-keep.
        supports_output_dir: Whether script accepts --output-dir override from
            orchestrator. Default is False to preserve script's topic-aware
            default path built with build_topic_path(). Set to True ONLY if
            you understand that the orchestrator will pass a generic parent
            directory which may cause cross-topic pruning collisions.
        uses_argv_kwarg: Whether run() expects argv as keyword argument.
        custom_args: Additional custom arguments for this script.
    """

    name: str
    path: str
    supports_artifacts_to_keep: bool = True
    supports_output_dir: bool = False  # Safe default: let scripts use topic-aware paths
    uses_argv_kwarg: bool = False
    custom_args: list[str] | None = None


PRODUCER_CONFIGS = [
    ScriptConfig(
        name="validate_import_boundaries",
        path=".repo_studios/scripts/producers/validate_import_boundaries.py",
        supports_output_dir=False,  # Uses topic-aware default: build_topic_path("producer", "import_boundary")
    ),
    ScriptConfig(
        name="check_inventory_health",
        path=".repo_studios/scripts/producers/check_inventory_health.py",
        supports_output_dir=False,  # Uses topic-aware default with VIEWER_SLUG/TOPIC_SLUG
    ),
    ScriptConfig(
        name="validate_inventory",
        path=".repo_studios/scripts/producers/validate_inventory.py",
        supports_output_dir=False,  # Uses topic-aware default: build_topic_path("producer", "validate_inventory")
    ),
    ScriptConfig(
        name="render_inventory_views",
        path=".repo_studios/scripts/producers/render_inventory_views.py",
        supports_artifacts_to_keep=False,  # Uses --timestamp only
        supports_output_dir=False,  # Uses topic-aware default with VIEWER_SLUG/TOPIC_SLUG
    ),
    ScriptConfig(
        name="generate_lizard_report",
        path=".repo_studios/scripts/producers/generate_lizard_report.py",
        supports_output_dir=False,  # Uses topic-aware default: build_topic_path("producer", "lizard_complexity")
        supports_artifacts_to_keep=True,  # Uses --artifacts-to-keep flag
    ),
]

CONSUMER_CONFIGS = [
    ScriptConfig(
        name="generate_anchor_health_report",
        path=".repo_studios/scripts/consumers/generate_anchor_health_report.py",
        uses_argv_kwarg=True,  # run(*, ..., argv=...) signature
        supports_output_dir=False,  # Uses topic-aware default: build_topic_path("consumer", "anchor_health")
    ),
]

ORCHESTRATOR_SCRIPT = ".repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py"

# --- Default paths -------------------------------------------------------------
DEFAULT_PRODUCER_OUTPUT = Path(".repo_studios/reports/healthview/producer_reports")
DEFAULT_CONSUMER_OUTPUT = Path(".repo_studios/reports/healthview/consumer_reports")
DEFAULT_ORCHESTRATOR_OUTPUT = build_topic_path("orchestrator", "available_scripts_oversight")


# --- Dataclasses ---------------------------------------------------------------
@dataclass(frozen=True)
class Paths:
    """Resolved path configuration for orchestrator.

    Attributes:
        repo_root: Repository root directory.
        producer_output_dir: Output directory for producer artifacts.
        consumer_output_dir: Output directory for consumer artifacts.
        orchestrator_output_dir: Output directory for orchestrator bundles.
    """

    repo_root: Path
    producer_output_dir: Path
    consumer_output_dir: Path
    orchestrator_output_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "producer_output_dir": PathSpec(
            field="producer_output_dir", default=DEFAULT_PRODUCER_OUTPUT, ensure_dir=True, within_repo=False
        ),
        "consumer_output_dir": PathSpec(
            field="consumer_output_dir", default=DEFAULT_CONSUMER_OUTPUT, ensure_dir=True, within_repo=False
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
    """

    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "producer_keep": KeepSpec(field="producer_artifacts_to_keep", minimum=1),
        "consumer_keep": KeepSpec(field="consumer_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    """Runtime options for orchestrator.

    Attributes:
        log_level: Logging verbosity level.
        artifacts_to_keep: Number of orchestrator artifact bundles to retain.
        producer_keep: Retention budget for producer reports.
        consumer_keep: Retention budget for consumer artifacts.
        skip_producers: Skip all producer steps if True.
        skip_consumers: Skip all consumer steps if True.
        run_timestamp: UTC timestamp for artifact generation.
    """

    log_level: str
    artifacts_to_keep: int
    producer_keep: int
    consumer_keep: int
    skip_producers: bool
    skip_consumers: bool
    run_timestamp: datetime


@dataclass(frozen=True)
class StepOutcome:
    """Result from executing a single script step.

    Attributes:
        script_name: Name identifier for the script.
        payload: Raw return dict from script's run().
        status: Execution status (ok, skipped, failed).
        detail: Human-readable detail message.
        exit_code: Script exit code if available.
        run_dir: Output directory path if available.
    """

    script_name: str
    payload: dict[str, Any] | None
    status: str
    detail: str | None
    exit_code: int | None
    run_dir: Path | None


# --- Argument parsing ----------------------------------------------------------
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for orchestrator.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--producer-output-dir", default=str(DEFAULT_PRODUCER_OUTPUT))
    parser.add_argument("--consumer-output-dir", default=str(DEFAULT_CONSUMER_OUTPUT))
    parser.add_argument("--orchestrator-output-dir", default=str(DEFAULT_ORCHESTRATOR_OUTPUT))
    parser.add_argument("--artifacts-to-keep", type=int, default=3, help="Retention budget for manifest artifacts")
    parser.add_argument("--producer-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--consumer-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--skip-producers", action="store_true", help="Skip all producer steps")
    parser.add_argument("--skip-consumers", action="store_true", help="Skip all consumer steps")
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
        paths: Resolved Paths instance (unused but kept for pattern consistency).

    Returns:
        Fully resolved Options instance.
    """
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        producer_keep=keep_values.producer_keep,
        consumer_keep=keep_values.consumer_keep,
        skip_producers=bool(args.skip_producers),
        skip_consumers=bool(args.skip_consumers),
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


# --- Script loading and execution ----------------------------------------------
def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[..., Any]:
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
    return cast(Callable[..., Any], func)


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


def _execute_script(
    config: ScriptConfig,
    paths: Paths,
    options: Options,
    *,
    is_consumer: bool = False,
) -> StepOutcome:
    """Execute a single script and capture its outcome.

    Args:
        config: Script configuration with path and CLI flags.
        paths: Resolved path configuration.
        options: Runtime options.
        is_consumer: True if script is a consumer (uses consumer output dir).

    Returns:
        StepOutcome with execution results.
    """
    script_name = config.name
    script_path = config.path
    module_name = f"orchestrated_{script_name}"
    full_path = paths.repo_root / script_path

    if not full_path.exists():
        return StepOutcome(
            script_name=script_name,
            payload=None,
            status="failed",
            detail=f"Script not found: {script_path}",
            exit_code=None,
            run_dir=None,
        )

    try:
        run_callable = _load_callable(full_path, module_name, "run")
    except (ImportError, AttributeError) as exc:
        return StepOutcome(
            script_name=script_name,
            payload=None,
            status="failed",
            detail=f"Failed to load run(): {exc}",
            exit_code=None,
            run_dir=None,
        )

    output_dir = paths.consumer_output_dir if is_consumer else paths.producer_output_dir
    keep_count = options.consumer_keep if is_consumer else options.producer_keep

    # Build argv based on script's supported flags
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        options.log_level,
    ]

    if config.supports_output_dir:
        argv.extend(["--output-dir", str(output_dir)])

    if config.supports_artifacts_to_keep:
        argv.extend(["--artifacts-to-keep", str(keep_count)])

    if config.custom_args:
        argv.extend(config.custom_args)

    LOGGER.info("Executing %s...", script_name)
    try:
        if config.uses_argv_kwarg:
            payload = run_callable(argv=argv)
        else:
            payload = run_callable(argv)
    except SystemExit as exc:
        # Some scripts raise SystemExit on completion
        exit_code = exc.code if isinstance(exc.code, int) else 1
        return StepOutcome(
            script_name=script_name,
            payload=None,
            status="failed" if exit_code != 0 else "ok",
            detail=f"SystemExit({exit_code})",
            exit_code=exit_code,
            run_dir=None,
        )
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Script %s raised exception", script_name)
        return StepOutcome(
            script_name=script_name,
            payload=None,
            status="failed",
            detail=str(exc),
            exit_code=None,
            run_dir=None,
        )

    if not isinstance(payload, dict):
        return StepOutcome(
            script_name=script_name,
            payload=None,
            status="ok",
            detail="run() returned non-dict",
            exit_code=0,
            run_dir=None,
        )

    exit_code = payload.get("exit_code")
    if not isinstance(exit_code, int):
        # Infer exit_code from status if not explicit
        if payload.get("status") in ("ok", "OK", "success"):
            exit_code = 0
        elif payload.get("status") in ("fail", "failed", "error"):
            exit_code = 1
        else:
            exit_code = None

    run_dir_raw = payload.get("run_dir") or payload.get("output_dir")
    run_dir = Path(run_dir_raw) if run_dir_raw else None
    if run_dir and not run_dir.exists():
        run_dir = None

    # Determine status: ok only if explicitly success or exit_code==0
    status_str = payload.get("status", "")
    if status_str in ("ok", "OK", "success"):
        status = "ok"
    elif status_str in ("fail", "failed", "error") or (exit_code is not None and exit_code != 0):
        status = "failed"
    else:
        status = "ok"  # Default to ok if no failure indicators
    detail = payload.get("detail") or f"exit_code={exit_code}"

    return StepOutcome(
        script_name=script_name,
        payload=payload,
        status=status,
        detail=detail,
        exit_code=exit_code,
        run_dir=run_dir,
    )


# --- Catalog registration ------------------------------------------------------
def _register_scripts(registry: CatalogRegistry, paths: Paths) -> None:
    """Register topic scripts in catalog registry.

    Args:
        registry: CatalogRegistry instance to populate.
        paths: Resolved paths (unused but kept for pattern).
    """
    for config in PRODUCER_CONFIGS:
        registry.register(script_path=config.path, topic=TOPIC_SLUG, role="producer")
    for config in CONSUMER_CONFIGS:
        registry.register(script_path=config.path, topic=TOPIC_SLUG, role="consumer")
    registry.register(script_path=ORCHESTRATOR_SCRIPT, topic=TOPIC_SLUG, role="orchestrator")


# --- Summary generation --------------------------------------------------------
def _status_badge(status: str) -> str:
    """Format a status string with a badge emoji.

    Args:
        status: Status string to format.

    Returns:
        Status string with emoji prefix.
    """
    normalized = (status or "").lower()
    if normalized in ("ok", "success", "completed"):
        return "✅ " + status
    if normalized == "skipped":
        return "⏭️ skipped"
    if normalized == "failed":
        return "❌ failed"
    return status


def _build_summary_markdown(
    *,
    run_slug: str,
    completed_at: datetime,
    producer_outcomes: list[StepOutcome],
    consumer_outcomes: list[StepOutcome],
    skipped_producers: bool,
    skipped_consumers: bool,
) -> str:
    """Generate a Markdown summary for the orchestrator bundle.

    Args:
        run_slug: Timestamp slug for the run.
        completed_at: Completion timestamp.
        producer_outcomes: List of producer step outcomes.
        consumer_outcomes: List of consumer step outcomes.
        skipped_producers: Whether producers were skipped.
        skipped_consumers: Whether consumers were skipped.

    Returns:
        Markdown summary string.
    """
    lines: list[str] = []
    lines.append("# Available Scripts Oversight Run")
    lines.append("")
    lines.append(f"Run: `{run_slug}` | Completed: {completed_at.isoformat()}")

    lines.append("")
    lines.append("## Pipeline Status")
    lines.append("")
    lines.append("| Phase | Step | Status | Detail |")
    lines.append("| --- | --- | --- | --- |")

    if skipped_producers:
        lines.append("| Producers | (all) | ⏭️ skipped | --skip-producers flag |")
    else:
        for outcome in producer_outcomes:
            lines.append(f"| Producer | {outcome.script_name} | {_status_badge(outcome.status)} | {outcome.detail or ''} |")

    if skipped_consumers:
        lines.append("| Consumers | (all) | ⏭️ skipped | --skip-consumers flag |")
    else:
        for outcome in consumer_outcomes:
            lines.append(f"| Consumer | {outcome.script_name} | {_status_badge(outcome.status)} | {outcome.detail or ''} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Producer Artifacts")
    lines.append("")
    if skipped_producers:
        lines.append("_(producers skipped)_")
    elif not producer_outcomes:
        lines.append("_(no producers executed)_")
    else:
        for outcome in producer_outcomes:
            run_dir_str = f"`{outcome.run_dir}`" if outcome.run_dir else "(none)"
            lines.append(f"- **{outcome.script_name}:** {run_dir_str}")

    lines.append("")
    lines.append("## Consumer Artifacts")
    lines.append("")
    if skipped_consumers:
        lines.append("_(consumers skipped)_")
    elif not consumer_outcomes:
        lines.append("_(no consumers executed)_")
    else:
        for outcome in consumer_outcomes:
            run_dir_str = f"`{outcome.run_dir}`" if outcome.run_dir else "(none)"
            lines.append(f"- **{outcome.script_name}:** {run_dir_str}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Excluded Scripts")
    lines.append("")
    lines.append("The following scripts are excluded from orchestration:")
    lines.append("")
    lines.append("- ASR-002, ASR-003, ASR-004: Utilities (invoked by other scripts)")
    lines.append("- ASR-006: Library module (no CLI)")
    lines.append("- ASR-009: Deprecated summarizer")
    lines.append("- ASR-011: Missing run(argv) entry point")
    lines.append("- ASR-013: Library module (no CLI)")
    lines.append("")

    return "\n".join(lines)


# --- Main execution ------------------------------------------------------------
def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Execute available scripts oversight orchestrator pipeline.

    Chain producer scripts → consumer scripts and write HOP-compliant
    orchestrator artifacts.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].

    Returns:
        Payload dict with status, exit_code, run_dir, and artifact paths.

    Note:
        Output is written to
        ``.repo_studios/reports/healthview/orchestrator_reports/available_scripts_oversight/<YYYYMMDD-HHMM>/``.
    """
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)

    LOGGER.debug(
        "Resolved paths: producer_output_dir=%s consumer_output_dir=%s orchestrator_output_dir=%s",
        paths.producer_output_dir,
        paths.consumer_output_dir,
        paths.orchestrator_output_dir,
    )
    LOGGER.debug(
        "Resolved options: artifacts_to_keep=%s producer_keep=%s consumer_keep=%s skip_producers=%s skip_consumers=%s run_timestamp=%s",
        options.artifacts_to_keep,
        options.producer_keep,
        options.consumer_keep,
        options.skip_producers,
        options.skip_consumers,
        options.run_timestamp.isoformat(),
    )

    registry = CatalogRegistry()
    _register_scripts(registry, paths)

    producer_outcomes: list[StepOutcome] = []
    consumer_outcomes: list[StepOutcome] = []
    failed = False

    # Phase 1: Execute producers
    if options.skip_producers:
        LOGGER.info("Skipping producer phase (--skip-producers)")
    else:
        LOGGER.info("=== Phase 1: Producers ===")
        for config in PRODUCER_CONFIGS:
            outcome = _execute_script(config, paths, options, is_consumer=False)
            producer_outcomes.append(outcome)
            if outcome.status == "failed":
                LOGGER.warning("Producer %s failed: %s", config.name, outcome.detail)
                failed = True

    # Phase 2: Execute consumers
    if options.skip_consumers:
        LOGGER.info("Skipping consumer phase (--skip-consumers)")
    else:
        LOGGER.info("=== Phase 2: Consumers ===")
        for config in CONSUMER_CONFIGS:
            outcome = _execute_script(config, paths, options, is_consumer=True)
            consumer_outcomes.append(outcome)
            if outcome.status == "failed":
                LOGGER.warning("Consumer %s failed: %s", config.name, outcome.detail)
                failed = True

    # Build pipeline steps for telemetry
    all_steps: list[TopicStep] = []
    for outcome in producer_outcomes:
        # Create local binding for closure
        outcome_ref = outcome
        all_steps.append(
            TopicStep(
                name=outcome.script_name,
                runner=lambda _, o=outcome_ref: step_success() if o.status != "failed" else step_failed(detail=o.detail),
            )
        )
    for outcome in consumer_outcomes:
        outcome_ref = outcome
        all_steps.append(
            TopicStep(
                name=outcome.script_name,
                runner=lambda _, o=outcome_ref: step_success() if o.status != "failed" else step_failed(detail=o.detail),
            )
        )

    # Add a placeholder step if all steps were skipped (pipeline requires ≥1 step)
    if not all_steps:
        all_steps.append(
            TopicStep(
                name="noop",
                runner=lambda _: step_skipped(detail="all phases skipped"),
            )
        )

    context = TopicContext(paths=paths, options=options, metadata={})
    pipeline = build_topic_pipeline(steps=all_steps)
    result = pipeline.run(context)

    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    telemetry = build_pipeline_telemetry(result, viewer="healthview", topic=TOPIC_SLUG, run_slug=run_slug)
    completed_at = datetime.now(timezone.utc)
    telemetry_payload = telemetry.as_dict()

    # Build artifacts section
    artifacts_section: dict[str, str | None] = {}
    for outcome in producer_outcomes:
        key = f"producer_{outcome.script_name}"
        artifacts_section[key] = _relativize(outcome.run_dir, paths.repo_root)
    for outcome in consumer_outcomes:
        key = f"consumer_{outcome.script_name}"
        artifacts_section[key] = _relativize(outcome.run_dir, paths.repo_root)

    # Build manifest
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "skip_producers": options.skip_producers,
            "skip_consumers": options.skip_consumers,
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
        "step_outcomes": {
            "producers": [
                {
                    "script": o.script_name,
                    "status": o.status,
                    "detail": o.detail,
                    "exit_code": o.exit_code,
                    "run_dir": _relativize(o.run_dir, paths.repo_root),
                }
                for o in producer_outcomes
            ],
            "consumers": [
                {
                    "script": o.script_name,
                    "status": o.status,
                    "detail": o.detail,
                    "exit_code": o.exit_code,
                    "run_dir": _relativize(o.run_dir, paths.repo_root),
                }
                for o in consumer_outcomes
            ],
        },
    }

    summary_markdown = _build_summary_markdown(
        run_slug=run_slug,
        completed_at=completed_at,
        producer_outcomes=producer_outcomes,
        consumer_outcomes=consumer_outcomes,
        skipped_producers=options.skip_producers,
        skipped_consumers=options.skip_consumers,
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

    exit_code = 1 if failed else 0
    LOGGER.info("Available Scripts Oversight orchestrator complete (slug=%s, exit_code=%d)", run_slug, exit_code)

    return {
        "status": "ok" if not failed else "failed",
        "exit_code": exit_code,
        "run_dir": str(result_artifacts.run_dir),
        "slug": run_slug,
        "manifest_path": str(manifest_path),
        "summary_path": str(result_artifacts.artifacts["summary.md"]),
        "telemetry_path": str(telemetry_path),
        "producer_count": len(producer_outcomes),
        "consumer_count": len(consumer_outcomes),
        "failed_count": sum(1 for o in producer_outcomes + consumer_outcomes if o.status == "failed"),
    }


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for available scripts oversight orchestrator.

    Args:
        argv: Command-line arguments; defaults to sys.argv[1:].
    """
    payload = run(argv)
    raise SystemExit(payload.get("exit_code", 0))


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]


if __name__ == "__main__":
    main()
