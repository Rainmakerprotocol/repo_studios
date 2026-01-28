#!/usr/bin/env python3
"""Topic orchestrator for test execution telemetry.

Emits HealthView bundles under
`.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<timestamp>/` by chaining
log collection, coverage inventory, churn heatmap, hardening analysis, and the health report summarizer.

The pipeline stops on the first hard failure so missing or invalid inputs surface quickly. The
collector is responsible for being self-sufficient (reuse existing log runs when present, otherwise
capture a fresh pytest run).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence, cast

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
from libraries.database_integration import create_storage
from libraries.report_paths import build_topic_path
from libraries.retention_policy import get_keep, get_orchestrator_config

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "test-execution-telemetry"
HEALTHVIEW_TOPIC = "test_execution_telemetry"
SCHEMA_VERSION = 1

RETENTION_CONFIG = get_orchestrator_config("run_test_execution_telemetry")
DEFAULT_ARTIFACTS_TO_KEEP = (
    max(1, int(RETENTION_CONFIG.artifacts_to_keep)) if RETENTION_CONFIG is not None else 3
)
DEFAULT_COLLECTOR_KEEP = get_keep("collect_test_log_reports")
DEFAULT_HEALTH_KEEP = get_keep("generate_test_log_health_report")
DEFAULT_COVERAGE_KEEP = get_keep("generate_test_coverage_inventory")
DEFAULT_HEATMAP_KEEP = get_keep("generate_churn_complexity_heatmap")
DEFAULT_HARDENING_KEEP = get_keep("analyze_test_hardening")

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

DEFAULT_LOGS_DIR = build_topic_path("rawview", "test_execution_runs")
DEFAULT_TEST_LOG_REPORTS_DIR = build_topic_path("rawview", "test_log_reports")
DEFAULT_TEST_LOG_HEALTH_DIR = build_topic_path("consumer", "test_log_health_reports")
DEFAULT_COVERAGE_OUTPUT_DIR = build_topic_path("producer", "test_coverage_inventory")
DEFAULT_COVERAGE_XML = Path("coverage.xml")
DEFAULT_HEATMAP_OUTPUT_DIR = build_topic_path("aggregator", "churn_complexity_heatmap")
DEFAULT_HARDENING_OUTPUT_DIR = build_topic_path("producer", "test_hardening")
DEFAULT_HEALTHVIEW_ROOT = build_topic_path("orchestrator", HEALTHVIEW_TOPIC)
DEFAULT_SUMMARIZER_OUTPUT_DIR = build_topic_path("summarizer", HEALTHVIEW_TOPIC)

COVERAGE_CLASS_SLUG = "producer_reports"
COVERAGE_TOPIC_SLUG = "test_coverage_inventory"

HARDENING_CLASS_SLUG = "producer_reports"
HARDENING_TOPIC_SLUG = "test_hardening"


def _is_ci_environment() -> bool:
    """Return True when running under a CI environment.

    This is intentionally conservative and only checks well-known CI markers.
    """
    markers = [
        "CI",
        "GITHUB_ACTIONS",
        "TF_BUILD",
        "BUILD_BUILDID",
        "SYSTEM_TEAMPROJECT",
    ]
    for name in markers:
        value = os.environ.get(name)
        if value is None:
            continue
        cleaned = str(value).strip().lower()
        if cleaned and cleaned not in {"0", "false", "no", "off"}:
            return True
    return False


@dataclass(frozen=True)
class Paths:
    """Path configuration for the test execution telemetry orchestrator.

    Attributes:
        repo_root: Repository root path.
        logs_dir: Directory containing pytest log artifacts.
        test_log_reports_dir: Output directory for test log reports.
        test_log_health_dir: Output directory for health reports.
        coverage_output_dir: Output directory for coverage inventory.
        coverage_xml: Path to coverage.xml source file.
        heatmap_output_dir: Output directory for churn heatmap.
        hardening_output_dir: Output directory for hardening analysis.
        healthview_root: Root directory for healthview bundles.
        summarizer_output_dir: Output directory for summarizer artifacts.
    """

    repo_root: Path
    logs_dir: Path
    test_log_reports_dir: Path
    test_log_health_dir: Path
    coverage_output_dir: Path
    coverage_xml: Path
    heatmap_output_dir: Path
    hardening_output_dir: Path
    healthview_root: Path
    summarizer_output_dir: Path


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
        "summarizer_output_dir": PathSpec(
            field="summarizer_output_dir", default=DEFAULT_SUMMARIZER_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepParameters:
    """Retention policy parameters for various artifact types.

    Attributes:
        artifacts_to_keep: General artifact retention count.
        collector_keep: Retention count for collector reports.
        health_keep: Retention count for health reports.
        coverage_keep: Retention count for coverage inventory.
        heatmap_keep: Retention count for heatmap runs.
        hardening_keep: Retention count for hardening analysis.
    """

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
    """Runtime options for the orchestrator.

    Attributes:
        log_level: Logging verbosity level.
        artifacts_to_keep: General artifact retention count.
        collector_keep: Retention count for collector reports.
        health_keep: Retention count for health reports.
        coverage_keep: Retention count for coverage inventory.
        heatmap_keep: Retention count for heatmap runs.
        hardening_keep: Retention count for hardening analysis.
        heatmap_window: Number of commits for heatmap analysis.
        metrics_source: Optional path to precomputed metrics.
        run_timestamp: Timestamp for this orchestrator run.
    """

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
    """Result of the collect step execution.

    Attributes:
        report_dir: Directory containing the collected report.
        producer_bundle_dir: Directory containing producer bundle.
        warnings_total: Total warning count from test logs.
        slow_tests: Count of slow tests detected.
        payload: Full payload dictionary from the collector.
    """

    report_dir: Path | None
    producer_bundle_dir: Path | None
    warnings_total: int | None
    slow_tests: int | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class CoverageOutcome:
    """Result of the coverage inventory execution.

    Attributes:
        report_dir: Directory containing coverage reports.
        summary: Coverage summary dictionary.
    """

    report_dir: Path | None
    summary: dict[str, Any] | None


@dataclass(frozen=True)
class HeatmapOutcome:
    """Result of the churn complexity heatmap execution.

    Attributes:
        run_dir: Directory containing heatmap artifacts.
        payload: Full payload dictionary from the heatmap generator.
    """

    run_dir: Path | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class HardeningOutcome:
    """Result of the test hardening analysis execution.

    Attributes:
        run_dir: Directory containing hardening reports.
        payload: Full payload dictionary from the hardening analyzer.
    """

    run_dir: Path | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class HealthReportOutcome:
    """Result of the health report generation.

    Attributes:
        run_dir: Directory containing health report artifacts.
        bundle_summary: Path to the bundle_summary.json file.
        payload: Full payload dictionary from the health reporter.
    """

    run_dir: Path | None
    bundle_summary: Path | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class ChildOutcome:
    """Capture the outcome of a child script invocation.

    Attributes:
        name: Script filename for the child invocation.
        path: Repo-relative script path.
        status: Outcome status (ok, warn, no_data, error).
        exit_code: Exit code derived from the child outcome.
        run_dir: Output directory produced by the child script, if any.
        duration_seconds: Elapsed runtime in seconds.
        error: Error message when the child invocation fails.
    """

    name: str
    path: str
    status: str
    exit_code: int
    run_dir: str | None
    duration_seconds: float
    error: str | None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the outcome."""
        return {
            "name": self.name,
            "path": self.path,
            "status": self.status,
            "exit_code": self.exit_code,
            "run_dir": self.run_dir,
            "duration_seconds": self.duration_seconds,
            "error": self.error,
        }


def _exit_code_from_status(status: str) -> int:
    """Return an exit code for a child outcome status.

    Args:
        status: Child script status string.

    Returns:
        Integer exit code compatible with orchestrator summary semantics.
    """
    normalized = status.lower()
    if normalized in {"ok", "success"}:
        return 0
    if normalized in {"warn", "partial", "no_data", "skipped"}:
        return 1
    return 2


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the orchestrator.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Parsed argument namespace with paths, retention settings, and options.
    """
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
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Topic artifacts to retain",
    )
    parser.add_argument(
        "--collector-artifacts-to-keep",
        type=int,
        default=DEFAULT_COLLECTOR_KEEP,
        help="Retention window for log report runs",
    )
    parser.add_argument(
        "--health-artifacts-to-keep",
        type=int,
        default=DEFAULT_HEALTH_KEEP,
        help="Retention window for health report runs",
    )
    parser.add_argument(
        "--coverage-artifacts-to-keep",
        type=int,
        default=DEFAULT_COVERAGE_KEEP,
        help="Retention window for coverage inventory",
    )
    parser.add_argument(
        "--heatmap-artifacts-to-keep",
        type=int,
        default=DEFAULT_HEATMAP_KEEP,
        help="Retention window for churn heatmap runs",
    )
    parser.add_argument(
        "--hardening-artifacts-to-keep",
        type=int,
        default=DEFAULT_HARDENING_KEEP,
        help="Retention window for hardening analysis",
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
    """Parse an ISO timestamp string or return current UTC time.

    Args:
        raw: ISO datetime string or None.

    Returns:
        Parsed datetime in UTC.

    Raises:
        SystemExit: If the timestamp format is invalid.
    """
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
    """Build Paths configuration from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Paths dataclass with resolved file paths.
    """
    paths = cast(Paths, build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__)))
    healthview_root = paths.healthview_root
    if not (
        healthview_root.name == HEALTHVIEW_TOPIC
        and healthview_root.parent.name == "orchestrator_reports"
    ):
        healthview_root = (healthview_root / "orchestrator_reports" / HEALTHVIEW_TOPIC).resolve()
        healthview_root.mkdir(parents=True, exist_ok=True)
        paths = replace(paths, healthview_root=healthview_root)
    return paths


def build_options(args: argparse.Namespace) -> Options:
    """Build Options configuration from parsed arguments.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Options dataclass with runtime settings.
    """
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
    """Configure basic logging with the specified level.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, etc.).
    """
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_run_callable(script_path: Path, module_name: str):
    """Dynamically load a module and return its run() callable.

    Args:
        script_path: Path to the Python script.
        module_name: Module name for sys.modules registration.

    Returns:
        The run() callable from the loaded module.

    Raises:
        ImportError: If the module cannot be loaded.
        AttributeError: If the module lacks a callable run() function.
    """
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
    """Find the most recent directory matching a prefix.

    Args:
        base: Base directory to search.
        prefix: Prefix to filter directories.

    Returns:
        Path to the latest matching directory or None.
    """
    if not base.exists():
        return None
    candidates = [child for child in base.iterdir() if child.is_dir() and child.name.startswith(prefix)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.name)[-1]


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed dictionary or None if file missing or invalid.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    """Convert a path to a repo-relative POSIX string.

    Args:
        path: Path to convert (or None).
        repo_root: Repository root for relative calculation.

    Returns:
        POSIX-formatted relative or absolute path string, or None.
    """
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _execute_coverage(paths: Paths, options: Options) -> CoverageOutcome:
    """Execute the coverage inventory producer script.

    Args:
        paths: Paths configuration.
        options: Options configuration.

    Returns:
        CoverageOutcome with report directory and summary.

    Raises:
        RuntimeError: If the script returns non-zero exit code.
    """
    run_callable = _load_run_callable(paths.repo_root / COVERAGE_SCRIPT, COVERAGE_MODULE)
    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--coverage-xml",
        str(paths.coverage_xml),
        "--refresh-coverage-xml",
        "--refresh-continue-on-error",
        "--refresh-cov-target",
        ".",
        "--output-dir",
        str(paths.coverage_output_dir),
        "--timestamp",
        options.run_timestamp.isoformat(),
        "--artifacts-to-keep",
        str(options.coverage_keep),
        "--log-level",
        options.log_level,
    ]
    exit_code = int(run_callable(argv))
    if exit_code != 0:
        raise RuntimeError(f"Coverage inventory exit code {exit_code}")

    # The coverage producer writes directly under the configured output directory
    # (which is already a HOP topic root like .../producer_reports/test_coverage_inventory).
    expected_dir = paths.coverage_output_dir / run_slug
    run_dir: Path | None = expected_dir if expected_dir.exists() else None
    if run_dir is None:
        run_dir = _latest_directory(paths.coverage_output_dir, "")

    summary = None
    if run_dir is not None:
        telemetry = _read_json(run_dir / "telemetry.json")
        if isinstance(telemetry, dict):
            payload = telemetry.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("summary"), dict):
                summary = dict(payload["summary"])
    return CoverageOutcome(report_dir=run_dir, summary=summary)


def _execute_collect(paths: Paths, options: Options) -> CollectOutcome:
    """Execute the test log collection producer script.

    Args:
        paths: Paths configuration.
        options: Options configuration.

    Returns:
        CollectOutcome with report directory and metrics.

    Raises:
        RuntimeError: If the script returns unexpected payload.
    """
    run_callable = _load_run_callable(paths.repo_root / COLLECT_SCRIPT, COLLECT_MODULE)
    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--logs-dir",
        str(paths.logs_dir),
        "--output-dir",
        str(paths.test_log_reports_dir),
        "--run-timestamp",
        run_slug,
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
    if payload.get("status") == "no_data":
        producer_bundle_dir = None
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
    """Execute the churn complexity heatmap aggregator script.

    Args:
        paths: Paths configuration.
        options: Options configuration.

    Returns:
        HeatmapOutcome with run directory and payload.

    Raises:
        RuntimeError: If the script returns unexpected payload.
    """
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
    """Execute the test hardening analysis producer script.

    Args:
        paths: Paths configuration.
        options: Options configuration.

    Returns:
        HardeningOutcome with run directory and payload.

    Raises:
        RuntimeError: If the script returns unexpected payload.
    """
    run_callable = _load_run_callable(paths.repo_root / HARDENING_SCRIPT, HARDENING_MODULE)
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.hardening_output_dir),
        "--tests-dir",
        ".repo_studios/tests",
        "--timestamp",
        options.run_timestamp.isoformat(),
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
        timestamp_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
        positional_candidate = (
            paths.hardening_output_dir / HARDENING_CLASS_SLUG / HARDENING_TOPIC_SLUG / timestamp_slug
        )
        if positional_candidate.exists():
            run_dir = positional_candidate.resolve()

    if run_dir is None:
        timestamp = payload.get("timestamp")
        if timestamp:
            try:
                parsed = datetime.fromisoformat(str(timestamp))
                legacy_slug = parsed.strftime("%Y%m%d-%H%M")
                legacy_candidate = paths.repo_root / ".repo_studios" / "command_center" / "reports" / "healthview" / "test_hardening" / legacy_slug
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
    """Execute the test log health report consumer script.

    Args:
        paths: Paths configuration.
        options: Options configuration.
        producer_bundle_dir: Path to producer bundle for input.

    Returns:
        HealthReportOutcome with run directory and payload.

    Raises:
        RuntimeError: If the script returns unexpected payload.
    """
    run_callable = _load_run_callable(paths.repo_root / HEALTH_REPORT_SCRIPT, HEALTH_MODULE)
    argv = [
        "--logs-dir",
        str(paths.logs_dir),
        "--output-base",
        str(paths.test_log_health_dir),
        "--artifacts-to-keep",
        str(options.health_keep),
        "--timestamp",
        options.run_timestamp.isoformat(),
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
    """Register all pipeline scripts in the catalog registry.

    Args:
        registry: CatalogRegistry instance to populate.
    """
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


def _summarize_steps(result_steps: Sequence[Any]) -> str:
    """Generate a simple Markdown summary of pipeline steps.

    Args:
        result_steps: Sequence of step result objects.

    Returns:
        Markdown-formatted step summary.
    """
    lines = ["# Test Execution Telemetry Run", ""]
    for step in result_steps:
        detail = f" ({step.detail})" if step.detail else ""
        lines.append(f"- {step.name}: {step.status}{detail}")
    return "\n".join(lines) + "\n"


def _status_icon(status: str) -> str:
    """Return an emoji icon for a step status.

    Args:
        status: Step status string (success, skipped, or failed).

    Returns:
        Emoji icon corresponding to the status.
    """
    return "✅" if status == "success" else "⚠️" if status == "skipped" else "❌"


def _section_pipeline_status(result_steps: Sequence[Any]) -> list[str]:
    """Render the pipeline status section as Markdown lines.

    Args:
        result_steps: Sequence of step result objects.

    Returns:
        List of Markdown lines for the pipeline status table.
    """
    lines = [
        "## Pipeline Status",
        "",
        "| Step | Status | Detail | Duration (s) |",
        "| --- | --- | --- | ---: |",
    ]
    for step in result_steps:
        icon = _status_icon(step.status)
        detail = step.detail or ""
        duration_seconds = (step.finished_at - step.started_at).total_seconds()
        lines.append(f"| {step.name} | {icon} {step.status} | {detail} | {duration_seconds:.2f} |")
    lines.append("")
    return lines


def _section_test_results(
    collect_outcome: CollectOutcome,
    artifact_path: str | None,
    telemetry: dict[str, Any],
) -> list[str]:
    """Render the test results section as Markdown lines.

    Args:
        collect_outcome: CollectOutcome from the collect step.
        artifact_path: Relative path to the artifact directory.
        telemetry: Telemetry data loaded from artifact.

    Returns:
        List of Markdown lines for the test results section.
    """
    lines = ["## Test Results", ""]
    if artifact_path:
        lines.append(f"**Artifact:** `{artifact_path}`")
        lines.append("")

    # Prefer telemetry data from file, fall back to payload
    metrics = telemetry.get("metrics", {})
    payload = telemetry.get("payload", {})
    payload_summary = payload.get("summary", {})

    total = metrics.get("tests_total") or payload_summary.get("total", 0)
    passed = metrics.get("tests_passed") or payload_summary.get("passed", 0)
    failed = metrics.get("tests_failed") or payload_summary.get("failed", 0)
    warnings = metrics.get("warnings_total") or collect_outcome.warnings_total or 0
    slow = metrics.get("slow_tests_count") or collect_outcome.slow_tests or 0

    lines.extend([
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Total | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Warnings | {warnings} |",
        f"| Slow | {slow} |",
        "",
    ])

    concerns: list[str] = []
    if failed > 0:
        concerns.append(f"❌ {failed} test(s) failed")
    if warnings > 10:
        concerns.append(f"⚠️ {warnings} warnings detected")

    if concerns:
        lines.append("**Concerns:** " + "; ".join(concerns))
    else:
        lines.append("**Concerns:** None")
    lines.append("")
    return lines


def _section_coverage(
    coverage_outcome: CoverageOutcome,
    artifact_path: str | None,
    telemetry: dict[str, Any],
) -> list[str]:
    """Render the coverage analysis section as Markdown lines.

    Args:
        coverage_outcome: CoverageOutcome from the coverage step.
        artifact_path: Relative path to the artifact directory.
        telemetry: Telemetry data loaded from artifact.

    Returns:
        List of Markdown lines for the coverage section.
    """
    lines = ["## Coverage Analysis", ""]
    if artifact_path:
        lines.append(f"**Artifact:** `{artifact_path}`")
        lines.append("")

    def _first_defined(*candidates: Any, default: Any) -> Any:
        for candidate in candidates:
            if candidate is not None:
                return candidate
        return default

    # Prefer telemetry from file, fall back to outcome
    metrics = telemetry.get("metrics", {}) if isinstance(telemetry.get("metrics"), dict) else {}
    payload = telemetry.get("payload", {}) if isinstance(telemetry.get("payload"), dict) else {}
    payload_summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    summary = coverage_outcome.summary or {}

    total_files = _first_defined(
        metrics.get("total_files"),
        payload_summary.get("total_files"),
        summary.get("total_files"),
        default=0,
    )
    total_functions = _first_defined(
        metrics.get("total_functions"),
        payload_summary.get("total_functions"),
        summary.get("total_functions"),
        default=0,
    )
    covered_functions = _first_defined(
        metrics.get("covered_functions"),
        payload_summary.get("covered_functions"),
        summary.get("covered_functions"),
        default=0,
    )

    pct_raw = _first_defined(
        metrics.get("overall_coverage_pct"),
        payload_summary.get("overall_coverage_pct"),
        summary.get("overall_coverage_pct"),
        default=0.0,
    )
    try:
        pct = float(pct_raw)
    except (TypeError, ValueError):
        pct = 0.0

    threshold_candidates = (
        metrics.get("threshold"),
        payload_summary.get("threshold"),
        summary.get("threshold"),
    )
    threshold_configured = any(candidate is not None for candidate in threshold_candidates)
    threshold_raw = _first_defined(*threshold_candidates, default=50.0)
    try:
        threshold = float(threshold_raw)
    except (TypeError, ValueError):
        threshold = 50.0

    lines.extend([
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Files | {total_files} |",
        f"| Functions | {total_functions} |",
        f"| Covered | {covered_functions} |",
        f"| Coverage % | {pct:.1f} |",
        "",
    ])

    concerns: list[str] = []
    if pct < threshold:
        if threshold_configured:
            concerns.append(f"⚠️ Coverage at {pct:.1f}% — below {threshold:.1f}% threshold")
        else:
            concerns.append(
                f"⚠️ Coverage at {pct:.1f}% — below {threshold:.1f}% heuristic threshold (no min_coverage configured)"
            )

    if concerns:
        lines.append("**Concerns:** " + "; ".join(concerns))
    else:
        lines.append("**Concerns:** None")
    lines.append("")
    return lines


def _section_hardening(
    hardening_outcome: HardeningOutcome,
    artifact_path: str | None,
    telemetry: dict[str, Any],
) -> list[str]:
    """Render the test hardening section as Markdown lines.

    Args:
        hardening_outcome: HardeningOutcome from the hardening step.
        artifact_path: Relative path to the artifact directory.
        telemetry: Telemetry data loaded from artifact.

    Returns:
        List of Markdown lines for the hardening section.
    """
    lines = ["## Test Hardening", ""]
    if artifact_path:
        lines.append(f"**Artifact:** `{artifact_path}`")
        lines.append("")

    # Prefer producer telemetry.json schema.
    metrics = telemetry.get("metrics", {}) if isinstance(telemetry.get("metrics"), dict) else {}
    severity = metrics.get("severity", {}) if isinstance(metrics.get("severity"), dict) else {}
    summary = {}
    components = telemetry.get("components")
    if isinstance(components, dict):
        hardening_component = components.get("hardening")
        if isinstance(hardening_component, dict) and isinstance(hardening_component.get("summary"), dict):
            summary = hardening_component["summary"]

    # Fall back to any inline payload if present.
    payload = telemetry.get("payload")
    if not isinstance(payload, dict):
        payload = hardening_outcome.payload if isinstance(hardening_outcome.payload, dict) else {}

    files_analyzed = (
        metrics.get("total_files")
        or summary.get("total_files")
        or payload.get("total_files")
        or payload.get("files_analyzed")
        or 0
    )
    total_issues = (
        metrics.get("total_issues")
        or summary.get("total_issues")
        or payload.get("total_issues")
        or 0
    )
    high_severity = (
        severity.get("high")
        or (summary.get("severity_totals") or {}).get("high")
        or payload.get("high_severity")
        or 0
    )

    lines.extend([
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Files Analyzed | {files_analyzed} |",
        f"| Total Issues | {total_issues} |",
        f"| High Severity | {high_severity} |",
        "",
    ])

    concerns: list[str] = []
    if high_severity > 0:
        concerns.append(f"❌ {high_severity} high-severity issue(s)")
    if files_analyzed == 0:
        concerns.append("⚠️ No test files analyzed — check scope configuration")

    if concerns:
        lines.append("**Concerns:** " + "; ".join(concerns))
    else:
        lines.append("**Concerns:** None")
    lines.append("")
    return lines


def _section_hotspots(
    heatmap_outcome: HeatmapOutcome,
    artifact_path: str | None,
    heatmap_records: list[dict[str, Any]],
) -> list[str]:
    """Render the churn × complexity hotspots section as Markdown lines.

    Args:
        heatmap_outcome: HeatmapOutcome from the heatmap step.
        artifact_path: Relative path to the artifact directory.
        heatmap_records: List of file metric records from heatmap.json.

    Returns:
        List of Markdown lines for the hotspots section.
    """
    lines = ["## Churn × Complexity Hotspots", ""]
    if artifact_path:
        lines.append(f"**Artifact:** `{artifact_path}`")
        lines.append("")

    # Use loaded records from heatmap.json, sorted by score descending
    top_files = sorted(heatmap_records, key=lambda r: r.get("score", 0), reverse=True)[:5]
    threshold = 12.0

    if top_files:
        lines.extend([
            "| Rank | File | Score |",
            "| --- | --- | ---:|",
        ])
        exceeds_count = 0
        for i, entry in enumerate(top_files, 1):
            fname = entry.get("file", "unknown")
            if "/" in fname or "\\" in fname:
                fname = fname.replace("\\", "/").rsplit("/", 1)[-1]
            score = entry.get("score", 0.0)
            if score > threshold:
                exceeds_count += 1
            lines.append(f"| {i} | {fname} | {score:.2f} |")
        lines.append("")

        if exceeds_count > 0:
            lines.append(f"**Concerns:** ⚠️ {exceeds_count} file(s) exceed score threshold ({threshold})")
        else:
            lines.append("**Concerns:** None")
    else:
        lines.append("No hotspot data available.")
        lines.append("")
        lines.append("**Concerns:** ⚠️ Heatmap analysis produced no results")
    lines.append("")
    return lines


def _section_trend(
    health_outcome: HealthReportOutcome | None,
    artifact_path: str | None,
    comparisons: dict[str, Any],
) -> list[str]:
    """Render the pass rate trend section as Markdown lines.

    Args:
        health_outcome: HealthReportOutcome from the health step, or None.
        artifact_path: Relative path to the artifact directory.
        comparisons: Comparison data from bundle_summary.json.

    Returns:
        List of Markdown lines for the trend section.
    """
    lines = ["## Pass Rate Trend", ""]
    if artifact_path:
        lines.append(f"**Artifact:** `{artifact_path}`")
        lines.append("")

    if health_outcome is None:
        lines.append("No health report available.")
        lines.append("")
        lines.append("**Concerns:** ⚠️ Health report not generated")
        lines.append("")
        return lines

    # Use comparisons from bundle_summary.json if available
    prev_run = comparisons.get("previous_run", {})
    pass_rate = prev_run.get("pass_rate", {})

    current = pass_rate.get("current", 0.0)
    previous = pass_rate.get("previous")
    delta = pass_rate.get("delta")

    lines.extend([
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Current | {current:.1f}% |",
    ])
    if previous is not None:
        lines.append(f"| Previous | {previous:.1f}% |")
    if delta is not None:
        sign = "+" if delta >= 0 else ""
        lines.append(f"| Delta | {sign}{delta:.2f}% |")
    lines.append("")

    concerns: list[str] = []
    if delta is not None and delta < 0:
        concerns.append(f"❌ Pass rate declined by {abs(delta):.2f}%")

    if concerns:
        lines.append("**Concerns:** " + "; ".join(concerns))
    else:
        lines.append("**Concerns:** None — stable or improving")
    lines.append("")
    return lines


@dataclass
class EnhancedSummaryContext:
    """Context bundle for building the enhanced summary report.

    Attributes:
        run_slug: Timestamp-based identifier for this run.
        completed_at: UTC datetime when the run completed.
        result_steps: Sequence of pipeline step results.
        collect_outcome: CollectOutcome from the collect step.
        coverage_outcome: CoverageOutcome from the coverage step.
        heatmap_outcome: HeatmapOutcome from the heatmap step.
        hardening_outcome: HardeningOutcome from the hardening step.
        health_outcome: HealthReportOutcome from health step, or None.
        artifacts_section: Mapping of artifact names to relative paths.
        repo_root: Repository root path for resolving artifacts.
    """

    run_slug: str
    completed_at: datetime
    result_steps: Sequence[Any]
    collect_outcome: CollectOutcome
    coverage_outcome: CoverageOutcome
    heatmap_outcome: HeatmapOutcome
    hardening_outcome: HardeningOutcome
    health_outcome: HealthReportOutcome | None
    artifacts_section: dict[str, Any]
    repo_root: Path


def _load_artifact_telemetry(artifact_dir: Path | None) -> dict[str, Any]:
    """Load telemetry.json from an artifact directory.

    Args:
        artifact_dir: Path to the artifact directory, or None.

    Returns:
        Parsed telemetry dictionary, or empty dict if unavailable.
    """
    if artifact_dir is None or not artifact_dir.exists():
        return {}
    telemetry_path = artifact_dir / "telemetry.json"
    return _read_json(telemetry_path) or {}


def _load_heatmap_data(heatmap_dir: Path | None) -> list[dict[str, Any]]:
    """Load file metric records from heatmap.json.

    Args:
        heatmap_dir: Path to the heatmap artifact directory, or None.

    Returns:
        List of file metric records, or empty list if unavailable.
    """
    if heatmap_dir is None or not heatmap_dir.exists():
        return []
    heatmap_json = heatmap_dir / "heatmap.json"
    data = _read_json(heatmap_json)
    # Heatmap uses "items" key for file records
    if data and isinstance(data.get("items"), list):
        items: list[dict[str, Any]] = data["items"]
        return items
    return []


def _load_health_comparisons(health_dir: Path | None) -> dict[str, Any]:
    """Load comparison data from bundle_summary.json.

    Args:
        health_dir: Path to the health report directory, or None.

    Returns:
        Comparisons dictionary, or empty dict if unavailable.
    """
    if health_dir is None or not health_dir.exists():
        return {}
    bundle_path = health_dir / "bundle_summary.json"
    data = _read_json(bundle_path) or {}
    comparisons: dict[str, Any] = data.get("comparisons", {})
    return comparisons


def _build_enhanced_summary(ctx: EnhancedSummaryContext) -> str:
    """Build the enhanced Markdown summary from context.

    Args:
        ctx: EnhancedSummaryContext with all run data and outcomes.

    Returns:
        Complete Markdown summary string.
    """
    lines: list[str] = []

    lines.append("# Test Execution Telemetry Run")
    lines.append("")
    lines.append(f"Run: `{ctx.run_slug}` | Completed: {ctx.completed_at.isoformat()}")
    lines.append("")

    lines.extend(_section_pipeline_status(ctx.result_steps))
    lines.append("---")
    lines.append("")

    # Resolve artifact directories for data loading
    log_report_path = ctx.artifacts_section.get("log_report")
    log_report_dir = (ctx.repo_root / log_report_path) if log_report_path else None

    coverage_path = ctx.artifacts_section.get("coverage_report")
    coverage_dir = (ctx.repo_root / coverage_path) if coverage_path else None

    hardening_path = ctx.artifacts_section.get("hardening")
    hardening_dir = (ctx.repo_root / hardening_path) if hardening_path else None

    heatmap_path = ctx.artifacts_section.get("heatmap")
    heatmap_dir = (ctx.repo_root / heatmap_path) if heatmap_path else None

    health_path = ctx.artifacts_section.get("health_report")
    health_dir = (ctx.repo_root / health_path) if health_path else None

    # Load telemetry data from artifacts for richer summaries
    log_telemetry = _load_artifact_telemetry(log_report_dir)
    coverage_telemetry = _load_artifact_telemetry(coverage_dir)
    hardening_telemetry = _load_artifact_telemetry(hardening_dir)
    heatmap_records = _load_heatmap_data(heatmap_dir)
    health_comparisons = _load_health_comparisons(health_dir)

    lines.extend(_section_test_results(
        ctx.collect_outcome, log_report_path, log_telemetry
    ))
    lines.append("---")
    lines.append("")

    lines.extend(_section_coverage(
        ctx.coverage_outcome, coverage_path, coverage_telemetry
    ))
    lines.append("---")
    lines.append("")

    lines.extend(_section_hardening(
        ctx.hardening_outcome, hardening_path, hardening_telemetry
    ))
    lines.append("---")
    lines.append("")

    lines.extend(_section_hotspots(
        ctx.heatmap_outcome, heatmap_path, heatmap_records
    ))
    lines.append("---")
    lines.append("")

    lines.extend(_section_trend(
        ctx.health_outcome, health_path, health_comparisons
    ))

    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    """Execute the test execution telemetry orchestrator.

    Parse arguments, run the three-phase pipeline (collect, analyse,
    summarize), and write report artifacts.

    Args:
        argv: Command-line arguments, or None to use sys.argv.

    Returns:
        Payload dictionary with orchestrator status, artifacts, and child outcomes.
    """
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    registry = CatalogRegistry()
    _register_scripts(registry)

    context = TopicContext(paths=paths, options=options, metadata={})

    child_outcomes: list[ChildOutcome] = []

    def _record_child_outcome(
        *,
        name: str,
        path: Path,
        status: str,
        exit_code: int,
        run_dir: Path | None,
        duration_seconds: float,
        error: str | None,
    ) -> None:
        child_outcomes.append(
            ChildOutcome(
                name=name,
                path=path.as_posix(),
                status=status,
                exit_code=exit_code,
                run_dir=run_dir.as_posix() if run_dir is not None else None,
                duration_seconds=duration_seconds,
                error=error,
            )
        )

    collect_outcome_holder: dict[str, CollectOutcome] = {}
    coverage_outcome_holder: dict[str, CoverageOutcome] = {}
    heatmap_outcome_holder: dict[str, HeatmapOutcome] = {}
    hardening_outcome_holder: dict[str, HardeningOutcome] = {}
    health_outcome_holder: dict[str, HealthReportOutcome | None] = {"value": None}

    def collect_step(ctx: TopicContext):
        LOGGER.info("Collecting pytest telemetry artifacts")
        coverage_start = time.perf_counter()
        try:
            coverage = _execute_coverage(paths, options)
        except Exception as exc:
            duration = time.perf_counter() - coverage_start
            _record_child_outcome(
                name=COVERAGE_SCRIPT.name,
                path=COVERAGE_SCRIPT,
                status="error",
                exit_code=2,
                run_dir=None,
                duration_seconds=duration,
                error=str(exc),
            )
            raise
        else:
            duration = time.perf_counter() - coverage_start
            _record_child_outcome(
                name=COVERAGE_SCRIPT.name,
                path=COVERAGE_SCRIPT,
                status="ok",
                exit_code=0,
                run_dir=coverage.report_dir,
                duration_seconds=duration,
                error=None,
            )

        collect_start = time.perf_counter()
        try:
            collect = _execute_collect(paths, options)
        except Exception as exc:
            duration = time.perf_counter() - collect_start
            _record_child_outcome(
                name=COLLECT_SCRIPT.name,
                path=COLLECT_SCRIPT,
                status="error",
                exit_code=2,
                run_dir=None,
                duration_seconds=duration,
                error=str(exc),
            )
            raise
        else:
            duration = time.perf_counter() - collect_start
            status = str(collect.payload.get("status", "ok"))
            _record_child_outcome(
                name=COLLECT_SCRIPT.name,
                path=COLLECT_SCRIPT,
                status=status,
                exit_code=_exit_code_from_status(status),
                run_dir=collect.report_dir,
                duration_seconds=duration,
                error=None,
            )
        ctx.add_metadata("coverage", coverage)
        ctx.add_metadata("collect", collect)
        coverage_outcome_holder["value"] = coverage
        collect_outcome_holder["value"] = collect
        detail = "no pytest logs discovered" if collect.producer_bundle_dir is None else "log report captured"
        payload = {
            "coverage": coverage.summary or {},
            "log_report": {
                "warnings_total": collect.warnings_total,
                "slow_tests": collect.slow_tests,
            },
        }
        if collect.producer_bundle_dir is None:
            return step_failed(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    def analyse_step(ctx: TopicContext):
        LOGGER.info("Running telemetry analysis scripts")
        hardening_start = time.perf_counter()
        try:
            hardening = _execute_hardening(paths, options)
        except Exception as exc:
            duration = time.perf_counter() - hardening_start
            _record_child_outcome(
                name=HARDENING_SCRIPT.name,
                path=HARDENING_SCRIPT,
                status="error",
                exit_code=2,
                run_dir=None,
                duration_seconds=duration,
                error=str(exc),
            )
            raise
        else:
            duration = time.perf_counter() - hardening_start
            status = str(hardening.payload.get("status", "ok"))
            exit_code = int(hardening.payload.get("exit_code", _exit_code_from_status(status)))
            _record_child_outcome(
                name=HARDENING_SCRIPT.name,
                path=HARDENING_SCRIPT,
                status=status,
                exit_code=exit_code,
                run_dir=hardening.run_dir,
                duration_seconds=duration,
                error=None,
            )

        heatmap_start = time.perf_counter()
        try:
            heatmap = _execute_heatmap(paths, options)
        except Exception as exc:
            duration = time.perf_counter() - heatmap_start
            _record_child_outcome(
                name=HEATMAP_SCRIPT.name,
                path=HEATMAP_SCRIPT,
                status="error",
                exit_code=2,
                run_dir=None,
                duration_seconds=duration,
                error=str(exc),
            )
            raise
        else:
            duration = time.perf_counter() - heatmap_start
            status = str(heatmap.payload.get("status", "ok"))
            _record_child_outcome(
                name=HEATMAP_SCRIPT.name,
                path=HEATMAP_SCRIPT,
                status=status,
                exit_code=_exit_code_from_status(status),
                run_dir=heatmap.run_dir,
                duration_seconds=duration,
                error=None,
            )
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
        health_start = time.perf_counter()
        try:
            health = _execute_health_report(paths, options, producer_bundle_dir=collect_outcome.producer_bundle_dir)
        except Exception as exc:
            duration = time.perf_counter() - health_start
            _record_child_outcome(
                name=HEALTH_REPORT_SCRIPT.name,
                path=HEALTH_REPORT_SCRIPT,
                status="error",
                exit_code=2,
                run_dir=None,
                duration_seconds=duration,
                error=str(exc),
            )
            raise
        else:
            duration = time.perf_counter() - health_start
            status = str(health.payload.get("status", "ok"))
            _record_child_outcome(
                name=HEALTH_REPORT_SCRIPT.name,
                path=HEALTH_REPORT_SCRIPT,
                status=status,
                exit_code=_exit_code_from_status(status),
                run_dir=health.run_dir,
                duration_seconds=duration,
                error=None,
            )
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
    exit_code = 0
    status = "ok"
    try:
        result.raise_for_failure()
    except RuntimeError as exc:
        LOGGER.error("Pipeline failed: %s", exc)
        exit_code = 1
        status = "error"
    else:
        if any(step.status == "skipped" for step in result.steps):
            exit_code = 1
            status = "partial"

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
    telemetry = build_pipeline_telemetry(result, viewer="orchestrator_reports", topic=TOPIC_SLUG, run_slug=run_slug)
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
    telemetry_payload["status"] = status
    telemetry_payload["exit_code"] = exit_code

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "orchestrator_reports",
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "status": status,
        "exit_code": exit_code,
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "logs_dir": _relativize(paths.logs_dir, paths.repo_root),
            "coverage_xml": _relativize(paths.coverage_xml, paths.repo_root),
            "metrics_source": _relativize(options.metrics_source, paths.repo_root),
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
    }

    summary_ctx = EnhancedSummaryContext(
        run_slug=run_slug,
        completed_at=completed_at,
        result_steps=result.steps,
        collect_outcome=collect_outcome,
        coverage_outcome=coverage_outcome,
        heatmap_outcome=heatmap_outcome,
        hardening_outcome=hardening_outcome,
        health_outcome=health_outcome,
        artifacts_section=artifacts_section,
        repo_root=paths.repo_root,
    )
    summary_markdown = _build_enhanced_summary(summary_ctx)

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

    summarizer_start = time.perf_counter()
    summarizer_run = _load_run_callable(paths.repo_root / SUMMARIZER_SCRIPT, SUMMARIZER_MODULE)
    summary_args = [
        "--repo-root",
        str(paths.repo_root),
        "--manifest",
        str(result_artifacts.artifacts["manifest.json"]),
        "--telemetry",
        str(result_artifacts.artifacts["telemetry.json"]),
        "--output-dir",
        str(paths.summarizer_output_dir),
        "--artifacts-to-keep",
        str(options.artifacts_to_keep),
        "--log-level",
        options.log_level,
    ]
    summary_payload = summarizer_run(summary_args)
    summarizer_duration = time.perf_counter() - summarizer_start
    if not isinstance(summary_payload, dict) or summary_payload.get("status") != "ok":
        raise RuntimeError("summarize_test_execution_telemetry returned unexpected payload")

    _record_child_outcome(
        name=SUMMARIZER_SCRIPT.name,
        path=SUMMARIZER_SCRIPT,
        status=str(summary_payload.get("status", "ok")),
        exit_code=_exit_code_from_status(str(summary_payload.get("status", "ok"))),
        run_dir=Path(str(summary_payload.get("run_dir"))) if summary_payload.get("run_dir") else None,
        duration_seconds=summarizer_duration,
        error=None,
    )

    summary_artifacts_raw = summary_payload.get("artifacts")
    summary_artifacts: dict[str, str] = {}
    if isinstance(summary_artifacts_raw, dict):
        for name, path_str in summary_artifacts_raw.items():
            if isinstance(name, str) and isinstance(path_str, str):
                summary_artifacts[name] = path_str

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

    child_outcomes_payload = [outcome.as_dict() for outcome in child_outcomes]
    scripts_run = len(child_outcomes_payload)
    scripts_failed = sum(1 for outcome in child_outcomes_payload if outcome["exit_code"] != 0)
    scripts_passed = scripts_run - scripts_failed

    manifest["child_outcomes"] = child_outcomes_payload
    manifest["scripts_run"] = scripts_run
    manifest["scripts_passed"] = scripts_passed
    manifest["scripts_failed"] = scripts_failed

    artifact_metrics = measure_artifact_directory(result_artifacts.run_dir)
    metrics_section = telemetry_payload.setdefault("metrics", {})
    metrics_section.update(artifact_metrics.as_dict())
    manifest["telemetry"] = telemetry_payload
    manifest["metrics"] = dict(metrics_section)

    storage = create_storage(paths.healthview_root, "", "", timestamp=run_slug)
    # DB_INTEGRATION_MARKER: hop_manifests.run_slug — Orchestrator manifest payload
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: hop_summaries.content_md — Orchestrator summary markdown
    storage.write_summary({"markdown": summary_markdown}, format="md")
    # DB_INTEGRATION_MARKER: hop_telemetry.metrics_json — Orchestrator telemetry payload
    storage.write_telemetry(telemetry_payload)

    child_outcomes_path = result_artifacts.run_dir / "child_outcomes.json"
    # DB_INTEGRATION_MARKER: orchestrator_runs.child_outcomes — Child script outcomes
    child_outcomes_path.write_text(
        json.dumps(child_outcomes_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    LOGGER.info("Test Execution Telemetry orchestrator complete (slug=%s)", run_slug)
    return {
        "status": status,
        "exit_code": exit_code,
        "run_dir": str(result_artifacts.run_dir),
        "output_dir": str(paths.healthview_root),
        "run_id": run_slug,
        "manifest": manifest,
        "telemetry": telemetry_payload,
        "summary": summary_markdown,
        "child_outcomes": child_outcomes_payload,
        "scripts_run": scripts_run,
        "scripts_passed": scripts_passed,
        "scripts_failed": scripts_failed,
    }


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point for the test execution telemetry orchestrator.

    Args:
        argv: Command-line arguments, or None to use sys.argv.

    Raises:
        SystemExit: With run() return code.
    """
    payload = run(argv)
    exit_code = int(payload.get("exit_code", 1)) if isinstance(payload, dict) else 1
    raise SystemExit(exit_code)


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]


if __name__ == "__main__":
    main()
