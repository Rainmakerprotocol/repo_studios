#!/usr/bin/env python3
"""Topic orchestrator for the Docs Health workflow.

Exports Healthview bundles to `.repo_studios/reports/healthview/orchestrator_reports/docs_health/<timestamp>/`
and replaces the legacy docs inventory/anchor/analysis chain that previously ran ad hoc. The
pipeline regenerates the doc index, validates anchors, aggregates health signals, and publishes the
summary bundle that feeds both CommandView and Healthview. Typical runs span roughly six to eight
minutes depending on anchor validation and churn aggregation time.
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

from libraries import (  # noqa: E402
    CatalogRegistry,
    GuardrailViolationError,
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
    enforce_report_naming,
    measure_artifact_directory,
    step_failed,
    step_skipped,
    step_success,
    write_report_artifacts,
)
from libraries.report_paths import (  # noqa: E402
    AGGREGATOR_REPORTS,
    HEALTHVIEW_ROOT,
    ORCHESTRATOR_REPORTS,
    PRODUCER_REPORTS,
    build_topic_path,
)

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "docs-health"
HEALTHVIEW_TOPIC = "docs_health"
# VIEWER_SLUG is the tier class for HOP path structure: healthview_root/viewer/topic/timestamp
VIEWER_SLUG = "orchestrator_reports"
SCHEMA_VERSION = 1

DOC_INDEX_SCRIPT = Path(".repo_studios/scripts/producers/generate_doc_index.py")
DOC_INDEX_MODULE = "scripts.producers.generate_doc_index"
ANCHOR_INVENTORY_SCRIPT = Path(
    ".repo_studios/scripts/producers/generate_anchor_inventory.py"
)
ANCHOR_INVENTORY_MODULE = "scripts.producers.generate_anchor_inventory"
ANCHOR_VALIDATION_SCRIPT = Path(
    ".repo_studios/scripts/producers/validate_markdown_anchors.py"
)
ANCHOR_VALIDATION_MODULE = "scripts.producers.validate_markdown_anchors"
DOCS_INTEGRITY_SCRIPT = Path(".repo_studios/scripts/producers/verify_docs_integrity.py")
DOCS_INTEGRITY_MODULE = "scripts.producers.verify_docs_integrity"
METRICS_STUB_SCRIPT = Path(
    ".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py"
)
METRICS_STUB_MODULE = "scripts.producers.validate_metrics_anchor_stubs"
CHURN_SCRIPT = Path(".repo_studios/scripts/producers/generate_code_doc_churn_report.py")
CHURN_MODULE = "scripts.producers.generate_code_doc_churn_report"
UNDOCUMENTED_SCRIPT = Path(
    ".repo_studios/scripts/producers/generate_undocumented_logic_report.py"
)
UNDOCUMENTED_MODULE = "scripts.producers.generate_undocumented_logic_report"
AGGREGATOR_SCRIPT = Path(
    ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py"
)
AGGREGATOR_MODULE = "scripts.aggregators.aggregate_docs_health_signals"
ORCHESTRATOR_SCRIPT = Path(
    ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py"
)

DEFAULT_DOC_INDEX_OUTPUT = build_topic_path("producer", "doc_index")
DEFAULT_ANCHOR_INVENTORY_OUTPUT = build_topic_path("producer", "anchor_inventory")
DEFAULT_ANCHOR_VALIDATION_OUTPUT = build_topic_path("producer", "markdown_anchor_validation")
DEFAULT_DOCS_INTEGRITY_OUTPUT = build_topic_path("producer", "docs_integrity_validation")
DEFAULT_METRICS_STUB_OUTPUT = build_topic_path("producer", "metrics_anchor_stub_validation")
DEFAULT_CHURN_OUTPUT = build_topic_path("producer", "code_doc_churn")
DEFAULT_UNDOCUMENTED_OUTPUT = build_topic_path("producer", "undocumented_logic")
DEFAULT_PLACEHOLDER_OUTPUT = build_topic_path("producer", "code_placeholders")
DEFAULT_MONKEY_PATCH_OUTPUT = build_topic_path("producer", "monkey_patches")
DEFAULT_AGGREGATOR_OUTPUT = build_topic_path("aggregator", "docs_health_signals")
DEFAULT_HEALTHVIEW_ROOT = HEALTHVIEW_ROOT

ANCHOR_VALIDATION_TOPIC = "markdown_anchor_validation"
DOCS_INTEGRITY_TOPIC = "docs_integrity_validation"
METRICS_STUB_TOPIC = "metrics_anchor_stub_validation"


@dataclass(frozen=True)
class Paths:
    """Immutable path configuration for the docs health orchestrator.

    Attributes:
        repo_root: Repository root directory.
        doc_index_output_dir: Output directory for doc index artifacts.
        anchor_inventory_output_dir: Output directory for anchor inventory.
        anchor_validation_output_dir: Output directory for anchor validation.
        docs_integrity_output_dir: Output directory for docs integrity.
        metrics_stub_output_dir: Output directory for metrics stub validation.
        churn_output_dir: Output directory for code-doc churn report.
        undocumented_output_dir: Output directory for undocumented logic report.
        placeholder_output_dir: Output directory for placeholder scan.
        monkey_patch_output_dir: Output directory for monkey patch scan.
        aggregator_output_dir: Output directory for aggregated signals.
        healthview_root: Root directory for healthview exports.
    """

    repo_root: Path
    doc_index_output_dir: Path
    anchor_inventory_output_dir: Path
    anchor_validation_output_dir: Path
    docs_integrity_output_dir: Path
    metrics_stub_output_dir: Path
    churn_output_dir: Path
    undocumented_output_dir: Path
    placeholder_output_dir: Path
    monkey_patch_output_dir: Path
    aggregator_output_dir: Path
    healthview_root: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "doc_index_output_dir": PathSpec(
            field="doc_index_output_dir",
            default=DEFAULT_DOC_INDEX_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "anchor_inventory_output_dir": PathSpec(
            field="anchor_inventory_output_dir",
            default=DEFAULT_ANCHOR_INVENTORY_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "anchor_validation_output_dir": PathSpec(
            field="anchor_validation_output_dir",
            default=DEFAULT_ANCHOR_VALIDATION_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "docs_integrity_output_dir": PathSpec(
            field="docs_integrity_output_dir",
            default=DEFAULT_DOCS_INTEGRITY_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "metrics_stub_output_dir": PathSpec(
            field="metrics_stub_output_dir",
            default=DEFAULT_METRICS_STUB_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "churn_output_dir": PathSpec(
            field="churn_output_dir",
            default=DEFAULT_CHURN_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "undocumented_output_dir": PathSpec(
            field="undocumented_output_dir",
            default=DEFAULT_UNDOCUMENTED_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "placeholder_output_dir": PathSpec(
            field="placeholder_output_dir",
            default=DEFAULT_PLACEHOLDER_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "monkey_patch_output_dir": PathSpec(
            field="monkey_patch_output_dir",
            default=DEFAULT_MONKEY_PATCH_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "aggregator_output_dir": PathSpec(
            field="aggregator_output_dir",
            default=DEFAULT_AGGREGATOR_OUTPUT,
            ensure_dir=True,
            within_repo=False,
        ),
        "healthview_root": PathSpec(
            field="healthview_root",
            default=DEFAULT_HEALTHVIEW_ROOT,
            ensure_dir=True,
            within_repo=False,
        ),
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepParameters:
    """Retention settings for per-stage artifact pruning.

    Attributes:
        artifacts_to_keep: Default artifact retention count.
        doc_index_keep: Retention count for doc index runs.
        anchor_inventory_keep: Retention count for anchor inventory runs.
        anchor_validation_keep: Retention count for anchor validation runs.
        docs_integrity_keep: Retention count for docs integrity runs.
        metrics_stub_keep: Retention count for metrics stub runs.
        churn_keep: Retention count for churn report runs.
        undocumented_keep: Retention count for undocumented logic runs.
        aggregator_keep: Retention count for aggregator runs.
    """

    artifacts_to_keep: int
    doc_index_keep: int
    anchor_inventory_keep: int
    anchor_validation_keep: int
    docs_integrity_keep: int
    metrics_stub_keep: int
    churn_keep: int
    undocumented_keep: int
    aggregator_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepParameters,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "doc_index_keep": KeepSpec(field="doc_index_artifacts_to_keep", minimum=1),
        "anchor_inventory_keep": KeepSpec(
            field="anchor_inventory_artifacts_to_keep", minimum=1
        ),
        "anchor_validation_keep": KeepSpec(
            field="anchor_validation_artifacts_to_keep", minimum=1
        ),
        "docs_integrity_keep": KeepSpec(
            field="docs_integrity_artifacts_to_keep", minimum=1
        ),
        "metrics_stub_keep": KeepSpec(
            field="metrics_stub_artifacts_to_keep", minimum=1
        ),
        "churn_keep": KeepSpec(field="churn_artifacts_to_keep", minimum=1),
        "undocumented_keep": KeepSpec(
            field="undocumented_artifacts_to_keep", minimum=1
        ),
        "aggregator_keep": KeepSpec(field="aggregator_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    """Runtime options for the docs health orchestrator.

    Attributes:
        log_level: Logging verbosity level.
        artifacts_to_keep: Default artifact retention count.
        doc_index_keep: Retention count for doc index.
        anchor_inventory_keep: Retention count for anchor inventory.
        anchor_validation_keep: Retention count for anchor validation.
        docs_integrity_keep: Retention count for docs integrity.
        metrics_stub_keep: Retention count for metrics stub.
        churn_keep: Retention count for churn report.
        undocumented_keep: Retention count for undocumented logic.
        aggregator_keep: Retention count for aggregator.
        skip_doc_index: Skip doc index generation.
        skip_anchor_inventory: Skip anchor inventory generation.
        skip_anchor_validation: Skip anchor validation.
        skip_docs_integrity: Skip docs integrity validation.
        skip_metrics_stub: Skip metrics stub validation.
        skip_churn: Skip churn report generation.
        skip_undocumented: Skip undocumented logic report.
        skip_aggregator: Skip aggregator stage.
        skip_hygiene_signals: Skip hygiene signal inputs.
        run_timestamp: Shared timestamp for this pipeline run.
    """

    log_level: str
    artifacts_to_keep: int
    doc_index_keep: int
    anchor_inventory_keep: int
    anchor_validation_keep: int
    docs_integrity_keep: int
    metrics_stub_keep: int
    churn_keep: int
    undocumented_keep: int
    aggregator_keep: int
    skip_doc_index: bool
    skip_anchor_inventory: bool
    skip_anchor_validation: bool
    skip_docs_integrity: bool
    skip_metrics_stub: bool
    skip_churn: bool
    skip_undocumented: bool
    skip_aggregator: bool
    skip_hygiene_signals: bool
    run_timestamp: datetime


@dataclass(frozen=True)
class DocIndexOutcome:
    """Result of the doc index generation stage.

    Attributes:
        run_dir: Timestamped output directory.
        slug: Run timestamp slug.
        documents: Number of documents indexed.
        headings: Number of headings found.
        links: Number of links catalogued.
        artifacts: Mapping of artifact names to paths.
    """

    run_dir: Path | None
    slug: str | None
    documents: int | None
    headings: int | None
    links: int | None
    artifacts: dict[str, Path]


@dataclass(frozen=True)
class AnchorInventoryOutcome:
    """Result of the anchor inventory generation stage.

    Attributes:
        run_dir: Timestamped output directory.
        slug: Run timestamp slug.
        total_slugs: Total anchor slugs inventoried.
        duplicates: Number of duplicate anchors.
        artifacts: Mapping of artifact names to paths.
    """

    run_dir: Path | None
    slug: str | None
    total_slugs: int | None
    duplicates: int | None
    artifacts: dict[str, Path]


@dataclass(frozen=True)
class AnchorValidationOutcome:
    """Result of the anchor validation stage.

    Attributes:
        run_dir: Timestamped output directory.
        status: Validation status (ok or error).
        issue_count: Number of broken anchor issues.
        report_path: Path to the validation report.
    """

    run_dir: Path | None
    status: str | None
    issue_count: int | None
    report_path: Path | None


@dataclass(frozen=True)
class DocsIntegrityOutcome:
    """Result of the docs integrity validation stage.

    Attributes:
        run_dir: Timestamped output directory.
        status: Integrity check status.
        mismatched_blocks: Number of mismatched JSON blocks.
        payload: Full telemetry payload from the producer.
    """

    run_dir: Path | None
    status: str | None
    mismatched_blocks: int | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class MetricsStubOutcome:
    """Result of the metrics stub validation stage.

    Attributes:
        run_dir: Timestamped output directory.
        status: Validation status.
        missing_count: Number of missing anchor stubs.
        payload: Full telemetry payload from the producer.
    """

    run_dir: Path | None
    status: str | None
    missing_count: int | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class ChurnOutcome:
    """Result of the code-doc churn report stage.

    Attributes:
        run_dir: Timestamped output directory.
        summary: Summary metrics from churn analysis.
        artifacts: Mapping of artifact names to paths.
    """

    run_dir: Path | None
    summary: dict[str, Any] | None
    artifacts: dict[str, Path]


@dataclass(frozen=True)
class UndocumentedOutcome:
    """Result of the undocumented logic report stage.

    Attributes:
        run_dir: Timestamped output directory.
        summary: Summary metrics from undocumented logic scan.
        artifacts: Mapping of artifact names to paths.
    """

    run_dir: Path | None
    summary: dict[str, Any] | None
    artifacts: dict[str, Path]


@dataclass(frozen=True)
class AggregatorOutcome:
    """Result of the docs health signals aggregator stage.

    Attributes:
        run_dir: Timestamped output directory.
        report_json: Path to the JSON report.
        report_md: Path to the Markdown summary.
        signals_tsv: Path to the TSV export.
        signals_csv: Path to the CSV export.
        bundle_summary: Path to the bundle summary JSON.
        summary: Summary metrics from aggregation.
    """

    run_dir: Path | None
    report_json: Path | None
    report_md: Path | None
    signals_tsv: Path | None
    signals_csv: Path | None
    bundle_summary: Path | None
    summary: dict[str, Any] | None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the docs health orchestrator.

    Args:
        argv: Command-line arguments. Defaults to sys.argv if None.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--doc-index-output-dir", default=str(DEFAULT_DOC_INDEX_OUTPUT))
    parser.add_argument(
        "--anchor-inventory-output-dir", default=str(DEFAULT_ANCHOR_INVENTORY_OUTPUT)
    )
    parser.add_argument(
        "--anchor-validation-output-dir", default=str(DEFAULT_ANCHOR_VALIDATION_OUTPUT)
    )
    parser.add_argument(
        "--docs-integrity-output-dir", default=str(DEFAULT_DOCS_INTEGRITY_OUTPUT)
    )
    parser.add_argument(
        "--metrics-stub-output-dir", default=str(DEFAULT_METRICS_STUB_OUTPUT)
    )
    parser.add_argument("--churn-output-dir", default=str(DEFAULT_CHURN_OUTPUT))
    parser.add_argument(
        "--undocumented-output-dir", default=str(DEFAULT_UNDOCUMENTED_OUTPUT)
    )
    parser.add_argument(
        "--placeholder-output-dir", default=str(DEFAULT_PLACEHOLDER_OUTPUT)
    )
    parser.add_argument(
        "--monkey-patch-output-dir", default=str(DEFAULT_MONKEY_PATCH_OUTPUT)
    )
    parser.add_argument(
        "--aggregator-output-dir", default=str(DEFAULT_AGGREGATOR_OUTPUT)
    )
    parser.add_argument("--healthview-root", default=str(DEFAULT_HEALTHVIEW_ROOT))
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=5,
        help="Healthview manifest retention budget",
    )
    parser.add_argument("--doc-index-artifacts-to-keep", type=int, default=1)
    parser.add_argument("--anchor-inventory-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--anchor-validation-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--docs-integrity-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--metrics-stub-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--churn-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--undocumented-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--aggregator-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--skip-doc-index", action="store_true")
    parser.add_argument("--skip-anchor-inventory", action="store_true")
    parser.add_argument("--skip-anchor-validation", action="store_true")
    parser.add_argument("--skip-docs-integrity", action="store_true")
    parser.add_argument("--skip-metrics-stub", action="store_true")
    parser.add_argument("--skip-churn", action="store_true")
    parser.add_argument("--skip-undocumented", action="store_true")
    parser.add_argument("--skip-aggregator", action="store_true")
    parser.add_argument("--skip-hygiene-signals", action="store_true")
    parser.add_argument(
        "--timestamp", help="ISO-8601 timestamp for orchestrator outputs"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def _parse_timestamp(raw: str | None) -> datetime:
    """Parse an ISO-8601 timestamp string to a UTC datetime.

    Args:
        raw: Timestamp string or None for current time.

    Returns:
        Parsed datetime in UTC timezone.

    Raises:
        SystemExit: If the timestamp format is invalid.
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
    """Build Paths instance from parsed arguments.

    Args:
        args: Parsed argument namespace.

    Returns:
        Configured Paths dataclass.
    """
    return cast(Paths, build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    """Build Options instance from parsed arguments.

    Args:
        args: Parsed argument namespace.

    Returns:
        Configured Options dataclass.
    """
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        doc_index_keep=keep_values.doc_index_keep,
        anchor_inventory_keep=keep_values.anchor_inventory_keep,
        anchor_validation_keep=keep_values.anchor_validation_keep,
        docs_integrity_keep=keep_values.docs_integrity_keep,
        metrics_stub_keep=keep_values.metrics_stub_keep,
        churn_keep=keep_values.churn_keep,
        undocumented_keep=keep_values.undocumented_keep,
        aggregator_keep=keep_values.aggregator_keep,
        skip_doc_index=bool(args.skip_doc_index),
        skip_anchor_inventory=bool(args.skip_anchor_inventory),
        skip_anchor_validation=bool(args.skip_anchor_validation),
        skip_docs_integrity=bool(args.skip_docs_integrity),
        skip_metrics_stub=bool(args.skip_metrics_stub),
        skip_churn=bool(args.skip_churn),
        skip_undocumented=bool(args.skip_undocumented),
        skip_aggregator=bool(args.skip_aggregator),
        skip_hygiene_signals=bool(args.skip_hygiene_signals),
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
    )


def configure_logging(level: str) -> None:
    """Configure root logger with specified verbosity level.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, etc.).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )


def _load_callable(
    script_path: Path, module_name: str, attribute: str
) -> Callable[[Sequence[str] | None], object]:
    """Dynamically load a callable from a Python script.

    Args:
        script_path: Path to the Python script file.
        module_name: Module name for sys.modules registration.
        attribute: Name of the callable to retrieve.

    Returns:
        The loaded callable.

    Raises:
        ImportError: If the module cannot be loaded.
        AttributeError: If the callable is missing.
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
    return cast(Callable[[Sequence[str] | None], object], func)


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    """Convert a path to a repo-relative POSIX string.

    Args:
        path: Absolute or relative path to convert.
        repo_root: Repository root for relative calculation.

    Returns:
        POSIX-style relative path, or None if path is None.
    """
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _read_json(path: Path) -> dict[str, Any] | None:
    """Read and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed dictionary, or None if file is missing or invalid.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _filter_artifacts(artifacts: dict[str, Path]) -> dict[str, Path]:
    """Filter artifact mapping to only existing paths.

    Args:
        artifacts: Mapping of artifact names to paths.

    Returns:
        Filtered mapping containing only existing files.
    """
    usable: dict[str, Path] = {}
    for name, value in artifacts.items():
        if value.exists():
            usable[name] = value
    return usable


def _execute_doc_index(paths: Paths, options: Options) -> DocIndexOutcome:
    """Execute the doc index generation producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        DocIndexOutcome with artifacts and summary metrics.

    Raises:
        RuntimeError: If the producer returns an unexpected payload.
    """
    run_callable = _load_callable(
        paths.repo_root / DOC_INDEX_SCRIPT, DOC_INDEX_MODULE, "run"
    )
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.doc_index_output_dir),
        "--artifacts-to-keep",
        str(options.doc_index_keep),
        "--timestamp",
        options.run_timestamp.isoformat(),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_doc_index returned unexpected payload")
    run_dir = Path(payload.get("run_dir", "")) if payload.get("run_dir") else None
    if run_dir and not run_dir.exists():
        run_dir = None
    artifacts_payload = payload.get("artifacts")
    artifacts: dict[str, Path] = {}
    if isinstance(artifacts_payload, dict):
        for name, value in artifacts_payload.items():
            candidate = Path(value)
            artifacts[name] = candidate
    documents = (
        payload.get("documents") if isinstance(payload.get("documents"), int) else None
    )
    headings = (
        payload.get("headings") if isinstance(payload.get("headings"), int) else None
    )
    links = payload.get("links") if isinstance(payload.get("links"), int) else None
    return DocIndexOutcome(
        run_dir=run_dir,
        slug=payload.get("slug") if isinstance(payload.get("slug"), str) else None,
        documents=documents,
        headings=headings,
        links=links,
        artifacts=_filter_artifacts(artifacts),
    )


def _execute_anchor_inventory(paths: Paths, options: Options) -> AnchorInventoryOutcome:
    """Execute the anchor inventory generation producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        AnchorInventoryOutcome with artifacts and summary metrics.

    Raises:
        RuntimeError: If the producer returns an unexpected payload.
    """
    run_callable = _load_callable(
        paths.repo_root / ANCHOR_INVENTORY_SCRIPT, ANCHOR_INVENTORY_MODULE, "run"
    )
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.anchor_inventory_output_dir),
        "--artifacts-to-keep",
        str(options.anchor_inventory_keep),
        "--timestamp",
        options.run_timestamp.isoformat(),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_anchor_inventory returned unexpected payload")
    run_dir = Path(payload.get("run_dir", "")) if payload.get("run_dir") else None
    if run_dir and not run_dir.exists():
        run_dir = None
    artifacts_payload = payload.get("artifacts")
    artifacts: dict[str, Path] = {}
    if isinstance(artifacts_payload, dict):
        for name, value in artifacts_payload.items():
            candidate = Path(value)
            artifacts[name] = candidate
    total_slugs = (
        payload.get("total_slugs")
        if isinstance(payload.get("total_slugs"), int)
        else None
    )
    duplicates = (
        payload.get("duplicates")
        if isinstance(payload.get("duplicates"), int)
        else None
    )
    return AnchorInventoryOutcome(
        run_dir=run_dir,
        slug=payload.get("slug") if isinstance(payload.get("slug"), str) else None,
        total_slugs=total_slugs,
        duplicates=duplicates,
        artifacts=_filter_artifacts(artifacts),
    )


def _execute_anchor_validation(
    paths: Paths, options: Options
) -> AnchorValidationOutcome:
    """Execute the markdown anchor validation producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        AnchorValidationOutcome with status and issue count.

    Raises:
        RuntimeError: If the producer exits with non-zero status.
    """
    run_callable = _load_callable(
        paths.repo_root / ANCHOR_VALIDATION_SCRIPT, ANCHOR_VALIDATION_MODULE, "main"
    )
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.anchor_validation_output_dir),
        "--artifacts-to-keep",
        str(options.anchor_validation_keep),
        "--timestamp",
        options.run_timestamp.isoformat(),
        "--log-level",
        options.log_level,
    ]
    exit_code_result = run_callable(argv)
    if isinstance(exit_code_result, int):
        exit_code = exit_code_result
    elif isinstance(exit_code_result, str):
        try:
            exit_code = int(exit_code_result)
        except ValueError as exc:  # pragma: no cover - defensive
            raise RuntimeError(
                "validate_markdown_anchors returned non-integer exit code"
            ) from exc
    else:
        raise RuntimeError("validate_markdown_anchors returned invalid exit code")
    if exit_code != 0:
        raise RuntimeError(f"validate_markdown_anchors exited with {exit_code}")
    run_timestamp = options.run_timestamp.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")
    run_dir_candidate = (
        paths.anchor_validation_output_dir
        / "healthview"
        / ANCHOR_VALIDATION_TOPIC
        / run_timestamp
    )
    run_dir: Path | None = run_dir_candidate if run_dir_candidate.exists() else None

    telemetry_path: Path | None = (
        (run_dir / "telemetry.json") if run_dir is not None else None
    )
    if telemetry_path and not telemetry_path.exists():
        telemetry_path = None
    telemetry = _read_json(telemetry_path) if telemetry_path else None

    report_payload: dict[str, Any] | None = None
    if isinstance(telemetry, dict):
        payload = telemetry.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("report"), dict):
            report_payload = payload["report"]

    status = report_payload.get("status") if isinstance(report_payload, dict) else None
    issue_count = (
        report_payload.get("issue_count") if isinstance(report_payload, dict) else None
    )
    if isinstance(issue_count, str):
        try:
            issue_count = int(issue_count)
        except ValueError:  # pragma: no cover - defensive
            issue_count = None
    return AnchorValidationOutcome(
        run_dir=run_dir,
        status=status,
        issue_count=issue_count,
        report_path=telemetry_path,
    )


def _execute_docs_integrity(paths: Paths, options: Options) -> DocsIntegrityOutcome:
    """Execute the docs integrity validation producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        DocsIntegrityOutcome with status and mismatch count.

    Raises:
        RuntimeError: If the producer returns an unexpected payload.
    """
    run_callable = _load_callable(
        paths.repo_root / DOCS_INTEGRITY_SCRIPT, DOCS_INTEGRITY_MODULE, "run"
    )
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.docs_integrity_output_dir),
        "--artifacts-to-keep",
        str(options.docs_integrity_keep),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("verify_docs_integrity returned unexpected payload")
    payload_dict = cast(dict[str, Any], payload)
    run_dir = (
        Path(payload_dict.get("run_dir", "")) if payload_dict.get("run_dir") else None
    )
    if run_dir and not run_dir.exists():
        run_dir = None
    summary_payload = payload_dict.get("summary")
    summary: dict[str, Any] = (
        cast(dict[str, Any], summary_payload) if isinstance(summary_payload, dict) else {}
    )
    mismatched_blocks = (
        summary.get("mismatched_blocks")
        if isinstance(summary.get("mismatched_blocks"), int)
        else None
    )
    status = (
        payload_dict.get("status") if isinstance(payload_dict.get("status"), str) else None
    )
    return DocsIntegrityOutcome(
        run_dir=run_dir,
        status=status,
        mismatched_blocks=mismatched_blocks,
        payload=payload_dict,
    )


def _execute_metrics_stub(paths: Paths, options: Options) -> MetricsStubOutcome:
    """Execute the metrics stub validation producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        MetricsStubOutcome with status and missing count.

    Raises:
        RuntimeError: If the producer returns an unexpected payload.
    """
    run_callable = _load_callable(
        paths.repo_root / METRICS_STUB_SCRIPT, METRICS_STUB_MODULE, "run"
    )
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.metrics_stub_output_dir),
        "--artifacts-to-keep",
        str(options.metrics_stub_keep),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("validate_metrics_anchor_stubs returned unexpected payload")
    payload_dict = cast(dict[str, Any], payload)
    run_dir = (
        Path(payload_dict.get("run_dir", "")) if payload_dict.get("run_dir") else None
    )
    if run_dir and not run_dir.exists():
        run_dir = None
    summary_payload = payload_dict.get("summary")
    summary: dict[str, Any] = (
        cast(dict[str, Any], summary_payload) if isinstance(summary_payload, dict) else {}
    )
    missing = (
        summary.get("missing_count")
        if isinstance(summary.get("missing_count"), int)
        else None
    )
    status = (
        payload_dict.get("status") if isinstance(payload_dict.get("status"), str) else None
    )
    return MetricsStubOutcome(
        run_dir=run_dir, status=status, missing_count=missing, payload=payload_dict
    )


def _execute_churn(paths: Paths, options: Options) -> ChurnOutcome:
    """Execute the code-doc churn report producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        ChurnOutcome with summary and artifacts.

    Raises:
        RuntimeError: If the producer returns an unexpected payload.
    """
    run_callable = _load_callable(paths.repo_root / CHURN_SCRIPT, CHURN_MODULE, "run")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.churn_output_dir),
        "--artifacts-to-keep",
        str(options.churn_keep),
        "--log-level",
        options.log_level,
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("generate_code_doc_churn_report returned unexpected payload")
    payload_dict = cast(dict[str, Any], payload)
    run_dir = (
        Path(payload_dict.get("run_dir", "")) if payload_dict.get("run_dir") else None
    )
    if run_dir and not run_dir.exists():
        run_dir = None
    artifacts_payload = payload_dict.get("artifacts")
    artifacts: dict[str, Path] = {}
    if isinstance(artifacts_payload, dict):
        for name, value in artifacts_payload.items():
            candidate = Path(value)
            artifacts[name] = candidate
    summary = (
        payload_dict.get("summary")
        if isinstance(payload_dict.get("summary"), dict)
        else None
    )
    return ChurnOutcome(
        run_dir=run_dir, summary=summary, artifacts=_filter_artifacts(artifacts)
    )


def _execute_undocumented(paths: Paths, options: Options) -> UndocumentedOutcome:
    """Execute the undocumented logic report producer.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        UndocumentedOutcome with summary and artifacts.

    Raises:
        RuntimeError: If the producer returns an unexpected payload.
    """
    run_callable = _load_callable(
        paths.repo_root / UNDOCUMENTED_SCRIPT, UNDOCUMENTED_MODULE, "run"
    )
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.undocumented_output_dir),
        "--artifacts-to-keep",
        str(options.undocumented_keep),
        "--log-level",
        options.log_level,
        "--include-command-center",
    ]
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "generate_undocumented_logic_report returned unexpected payload"
        )
    payload_dict = cast(dict[str, Any], payload)
    run_dir = (
        Path(payload_dict.get("run_dir", "")) if payload_dict.get("run_dir") else None
    )
    if run_dir and not run_dir.exists():
        run_dir = None
    artifacts_payload = payload_dict.get("artifacts")
    artifacts: dict[str, Path] = {}
    if isinstance(artifacts_payload, dict):
        for name, value in artifacts_payload.items():
            candidate = Path(value)
            artifacts[name] = candidate
    summary = (
        payload_dict.get("summary")
        if isinstance(payload_dict.get("summary"), dict)
        else None
    )
    return UndocumentedOutcome(
        run_dir=run_dir, summary=summary, artifacts=_filter_artifacts(artifacts)
    )


def _latest_pointer(paths: Paths, *, name: str) -> Path:
    """Return a pointer path under the doc index output directory.

    Args:
        paths: Orchestrator path configuration.
        name: Pointer file or subdirectory name.

    Returns:
        Path to the named pointer location.
    """
    return paths.doc_index_output_dir / name


def _latest_anchor_inventory(paths: Paths) -> Path:
    """Return the anchor inventory output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the anchor inventory output directory.
    """
    # Output dir already contains full topic path via report_paths
    return paths.anchor_inventory_output_dir


def _latest_anchor_validation(paths: Paths) -> Path:
    """Return the anchor validation output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the anchor validation output directory.
    """
    # Output dir already contains full topic path via report_paths
    return paths.anchor_validation_output_dir


def _latest_docs_integrity(paths: Paths) -> Path:
    """Return the docs integrity output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the docs integrity output directory.
    """
    # Output dir already contains full topic path via report_paths
    return paths.docs_integrity_output_dir


def _latest_metrics_stub(paths: Paths) -> Path:
    """Return the metrics stub output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the metrics stub output directory.
    """
    # Output dir already contains full topic path via report_paths
    return paths.metrics_stub_output_dir


def _latest_churn(paths: Paths) -> Path:
    """Return the churn report output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the churn report output directory.
    """
    # Output dir already contains full topic path via report_paths
    return paths.churn_output_dir


def _latest_undocumented(paths: Paths) -> Path:
    """Return the undocumented logic output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the undocumented logic output directory.
    """
    # Output dir already contains full topic path via report_paths
    return paths.undocumented_output_dir


def _latest_placeholder(paths: Paths) -> Path:
    """Return the placeholder scan output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the placeholder scan output directory.
    """
    return paths.placeholder_output_dir


def _latest_monkey_patch(paths: Paths) -> Path:
    """Return the monkey patch scan output directory.

    Args:
        paths: Orchestrator path configuration.

    Returns:
        Path to the monkey patch scan output directory.
    """
    return paths.monkey_patch_output_dir


def _execute_aggregator(paths: Paths, options: Options) -> AggregatorOutcome:
    """Execute the docs health signals aggregator.

    Args:
        paths: Orchestrator path configuration.
        options: Orchestrator runtime options.

    Returns:
        AggregatorOutcome with report paths and summary.

    Raises:
        RuntimeError: If the aggregator returns an unexpected payload.
    """
    run_callable = _load_callable(
        paths.repo_root / AGGREGATOR_SCRIPT, AGGREGATOR_MODULE, "run"
    )
    argv: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.aggregator_output_dir),
        "--artifacts-to-keep",
        str(options.aggregator_keep),
        "--log-level",
        options.log_level,
        "--churn-report",
        str(_latest_churn(paths)),
        "--undocumented-report",
        str(_latest_undocumented(paths)),
        "--anchor-inventory",
        str(_latest_anchor_inventory(paths)),
        "--anchor-validation",
        str(_latest_anchor_validation(paths)),
        "--docs-integrity",
        str(_latest_docs_integrity(paths)),
        "--metrics-stub",
        str(_latest_metrics_stub(paths)),
    ]
    if options.skip_hygiene_signals:
        argv.append("--skip-hygiene")
    else:
        argv.extend(
            [
                "--placeholder-report",
                str(_latest_placeholder(paths)),
                "--monkey-patch-report",
                str(_latest_monkey_patch(paths)),
            ]
        )
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("aggregate_docs_health_signals returned unexpected payload")
    run_dir = Path(payload.get("run_dir", "")) if payload.get("run_dir") else None
    if run_dir and not run_dir.exists():
        run_dir = None
    report_json = (
        Path(payload.get("report_json", "")) if payload.get("report_json") else None
    )
    if report_json and not report_json.exists():
        report_json = None
    report_md = Path(payload.get("report_md", "")) if payload.get("report_md") else None
    if report_md and not report_md.exists():
        report_md = None
    signals_tsv = (
        Path(payload.get("signals_tsv", "")) if payload.get("signals_tsv") else None
    )
    if signals_tsv and not signals_tsv.exists():
        signals_tsv = None
    signals_csv = (
        Path(payload.get("signals_csv", "")) if payload.get("signals_csv") else None
    )
    if signals_csv and not signals_csv.exists():
        signals_csv = None
    bundle_summary = (
        Path(payload.get("bundle_summary", ""))
        if payload.get("bundle_summary")
        else None
    )
    if bundle_summary and not bundle_summary.exists():
        bundle_summary = None
    summary = (
        payload.get("summary") if isinstance(payload.get("summary"), dict) else None
    )
    return AggregatorOutcome(
        run_dir=run_dir,
        report_json=report_json,
        report_md=report_md,
        signals_tsv=signals_tsv,
        signals_csv=signals_csv,
        bundle_summary=bundle_summary,
        summary=summary,
    )


def _register_catalog(registry: CatalogRegistry) -> None:
    """Register producer and aggregator scripts with the catalog.

    Args:
        registry: CatalogRegistry instance for script registration.
    """
    registry.register(
        script_path=str(DOC_INDEX_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(
        script_path=str(ANCHOR_INVENTORY_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(
        script_path=str(ANCHOR_VALIDATION_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(
        script_path=str(DOCS_INTEGRITY_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(
        script_path=str(METRICS_STUB_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(script_path=str(CHURN_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(
        script_path=str(UNDOCUMENTED_SCRIPT), topic=TOPIC_SLUG, role="producer"
    )
    registry.register(
        script_path=str(AGGREGATOR_SCRIPT), topic=TOPIC_SLUG, role="aggregator"
    )
    registry.register(
        script_path=str(ORCHESTRATOR_SCRIPT), topic=TOPIC_SLUG, role="orchestrator"
    )


def _summarize_steps(steps: Sequence[Any]) -> str:
    """Render step outcomes as a Markdown summary.

    Args:
        steps: Sequence of TopicStep instances.

    Returns:
        Markdown-formatted summary string.
    """
    lines = ["# Docs Health Run", ""]
    for step in steps:
        detail = f" ({step.detail})" if step.detail else ""
        lines.append(f"- {step.name}: {step.status}{detail}")
    return "\n".join(lines) + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    """Execute the docs health orchestrator pipeline.

    Coordinate producers and aggregator stages for the docs health topic.

    Args:
        argv: Command-line arguments. Defaults to sys.argv if None.

    Returns:
        Exit code (0 on success).
    """
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    registry = CatalogRegistry()
    _register_catalog(registry)

    context = TopicContext(paths=paths, options=options, metadata={})

    doc_index_holder: dict[str, DocIndexOutcome] = {}
    anchor_inventory_holder: dict[str, AnchorInventoryOutcome] = {}
    anchor_validation_holder: dict[str, AnchorValidationOutcome] = {}
    docs_integrity_holder: dict[str, DocsIntegrityOutcome] = {}
    metrics_stub_holder: dict[str, MetricsStubOutcome] = {}
    churn_holder: dict[str, ChurnOutcome] = {}
    undocumented_holder: dict[str, UndocumentedOutcome] = {}
    aggregator_holder: dict[str, AggregatorOutcome] = {}

    def doc_index_step(_: TopicContext):
        if options.skip_doc_index:
            return step_skipped(detail="doc index skipped")
        try:
            outcome = _execute_doc_index(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        doc_index_holder["value"] = outcome
        context.add_metadata(
            "doc_index",
            {
                "documents": outcome.documents,
                "headings": outcome.headings,
                "links": outcome.links,
            },
        )
        detail_bits: list[str] = []
        if outcome.documents is not None:
            detail_bits.append(f"docs={outcome.documents}")
        if outcome.headings is not None:
            detail_bits.append(f"headings={outcome.headings}")
        detail = ", ".join(detail_bits) if detail_bits else "doc index completed"
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "slug": outcome.slug,
        }
        return step_success(detail=detail, payload=payload)

    def anchor_inventory_step(_: TopicContext):
        if options.skip_anchor_inventory:
            return step_skipped(detail="anchor inventory skipped")
        try:
            outcome = _execute_anchor_inventory(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        anchor_inventory_holder["value"] = outcome
        context.add_metadata(
            "anchor_inventory",
            {
                "total_slugs": outcome.total_slugs,
                "duplicates": outcome.duplicates,
            },
        )
        detail_bits: list[str] = []
        if outcome.total_slugs is not None:
            detail_bits.append(f"slugs={outcome.total_slugs}")
        if outcome.duplicates is not None:
            detail_bits.append(f"duplicates={outcome.duplicates}")
        detail = ", ".join(detail_bits) if detail_bits else "anchor inventory completed"
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "slug": outcome.slug,
        }
        return step_success(detail=detail, payload=payload)

    def anchor_validation_step(_: TopicContext):
        if options.skip_anchor_validation:
            return step_skipped(detail="anchor validation skipped")
        try:
            outcome = _execute_anchor_validation(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        anchor_validation_holder["value"] = outcome
        context.add_metadata(
            "anchor_validation",
            {
                "status": outcome.status,
                "issue_count": outcome.issue_count,
            },
        )
        detail = f"status={outcome.status or 'unknown'}"
        if outcome.issue_count is not None:
            detail += f", issues={outcome.issue_count}"
        payload = {
            "report": _relativize(outcome.report_path, paths.repo_root),
            "status": outcome.status,
            "issues": outcome.issue_count,
        }
        return step_success(detail=detail, payload=payload)

    def docs_integrity_step(_: TopicContext):
        if options.skip_docs_integrity:
            return step_skipped(detail="docs integrity skipped")
        try:
            outcome = _execute_docs_integrity(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        docs_integrity_holder["value"] = outcome
        context.add_metadata("docs_integrity", outcome.payload)
        detail = f"status={outcome.status or 'unknown'}"
        if outcome.mismatched_blocks is not None:
            detail += f", mismatches={outcome.mismatched_blocks}"
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "status": outcome.status,
            "mismatches": outcome.mismatched_blocks,
        }
        return step_success(detail=detail, payload=payload)

    def metrics_stub_step(_: TopicContext):
        if options.skip_metrics_stub:
            return step_skipped(detail="metrics stub skipped")
        try:
            outcome = _execute_metrics_stub(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        metrics_stub_holder["value"] = outcome
        context.add_metadata("metrics_stub", outcome.payload)
        detail = f"status={outcome.status or 'unknown'}"
        if outcome.missing_count is not None:
            detail += f", missing={outcome.missing_count}"
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "status": outcome.status,
            "missing": outcome.missing_count,
        }
        return step_success(detail=detail, payload=payload)

    def churn_step(_: TopicContext):
        if options.skip_churn:
            return step_skipped(detail="churn skipped")
        try:
            outcome = _execute_churn(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        churn_holder["value"] = outcome
        context.add_metadata("churn", outcome.summary or {})
        summary = outcome.summary or {}
        missing = summary.get("modules_without_doc_updates")
        detail = (
            f"missing_docs={missing}" if isinstance(missing, int) else "churn completed"
        )
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "summary": summary,
        }
        return step_success(detail=detail, payload=payload)

    def undocumented_step(_: TopicContext):
        if options.skip_undocumented:
            return step_skipped(detail="undocumented logic skipped")
        try:
            outcome = _execute_undocumented(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        undocumented_holder["value"] = outcome
        context.add_metadata("undocumented", outcome.summary or {})
        summary = outcome.summary or {}
        findings = summary.get("modules_with_findings")
        detail = (
            f"modules_with_findings={findings}"
            if isinstance(findings, int)
            else "undocumented scan completed"
        )
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "summary": summary,
        }
        return step_success(detail=detail, payload=payload)

    def aggregator_step(_: TopicContext):
        if options.skip_aggregator:
            return step_skipped(detail="aggregator skipped")
        try:
            outcome = _execute_aggregator(paths, options)
        except Exception as exc:  # pragma: no cover - defensive
            return step_failed(detail=str(exc))
        aggregator_holder["value"] = outcome
        context.add_metadata("aggregator", outcome.summary or {})
        overall = None
        if outcome.summary:
            overall = outcome.summary.get("overall_score")
        detail = f"overall={overall}" if overall is not None else "aggregated signals"
        payload = {
            "run_dir": _relativize(outcome.run_dir, paths.repo_root),
            "overall_score": overall,
        }
        return step_success(detail=detail, payload=payload)

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="doc-index", runner=doc_index_step),
            TopicStep(name="anchor-inventory", runner=anchor_inventory_step),
            TopicStep(name="anchor-validation", runner=anchor_validation_step),
            TopicStep(name="docs-integrity", runner=docs_integrity_step),
            TopicStep(name="metrics-stub", runner=metrics_stub_step),
            TopicStep(name="code-doc-churn", runner=churn_step),
            TopicStep(name="undocumented-logic", runner=undocumented_step),
            TopicStep(name="aggregate", runner=aggregator_step),
        ]
    )

    result = pipeline.run(context)
    try:
        result.raise_for_failure()
    except RuntimeError as exc:  # pragma: no cover - defensive
        LOGGER.error("Pipeline failed: %s", exc)
        return 1

    doc_index_outcome = doc_index_holder.get("value")
    anchor_inventory_outcome = anchor_inventory_holder.get("value")
    anchor_validation_outcome = anchor_validation_holder.get("value")
    docs_integrity_outcome = docs_integrity_holder.get("value")
    metrics_stub_outcome = metrics_stub_holder.get("value")
    churn_outcome = churn_holder.get("value")
    undocumented_outcome = undocumented_holder.get("value")
    aggregator_outcome = aggregator_holder.get("value")

    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    telemetry = build_pipeline_telemetry(
        result, viewer=VIEWER_SLUG, topic=HEALTHVIEW_TOPIC, run_slug=run_slug
    )
    completed_at = datetime.now(timezone.utc)
    telemetry_payload = telemetry.as_dict()

    artifacts_section: dict[str, str | None] = {
        "doc_index_run": _relativize(
            doc_index_outcome.run_dir if doc_index_outcome else None, paths.repo_root
        ),
        "doc_index_report": _relativize(
            doc_index_outcome.artifacts.get("telemetry.json")
            if doc_index_outcome
            else None,
            paths.repo_root,
        ),
        "anchor_inventory_run": _relativize(
            anchor_inventory_outcome.run_dir if anchor_inventory_outcome else None,
            paths.repo_root,
        ),
        "anchor_inventory_report": _relativize(
            anchor_inventory_outcome.artifacts.get("telemetry.json")
            if anchor_inventory_outcome
            else None,
            paths.repo_root,
        ),
        "anchor_validation_report": _relativize(
            anchor_validation_outcome.report_path
            if anchor_validation_outcome
            else None,
            paths.repo_root,
        ),
        "docs_integrity_run": _relativize(
            docs_integrity_outcome.run_dir if docs_integrity_outcome else None,
            paths.repo_root,
        ),
        "metrics_stub_run": _relativize(
            metrics_stub_outcome.run_dir if metrics_stub_outcome else None,
            paths.repo_root,
        ),
        "churn_report": _relativize(
            churn_outcome.artifacts.get("telemetry.json") if churn_outcome else None,
            paths.repo_root,
        ),
        "undocumented_report": _relativize(
            undocumented_outcome.artifacts.get("report.json")
            if undocumented_outcome
            else None,
            paths.repo_root,
        ),
        "aggregator_run": _relativize(
            aggregator_outcome.run_dir if aggregator_outcome else None, paths.repo_root
        ),
        "aggregator_report_json": _relativize(
            aggregator_outcome.report_json if aggregator_outcome else None,
            paths.repo_root,
        ),
        "aggregator_report_md": _relativize(
            aggregator_outcome.report_md if aggregator_outcome else None,
            paths.repo_root,
        ),
        "aggregator_signals_tsv": _relativize(
            aggregator_outcome.signals_tsv if aggregator_outcome else None,
            paths.repo_root,
        ),
        "aggregator_signals_csv": _relativize(
            aggregator_outcome.signals_csv if aggregator_outcome else None,
            paths.repo_root,
        ),
        "aggregator_bundle_summary": _relativize(
            aggregator_outcome.bundle_summary if aggregator_outcome else None,
            paths.repo_root,
        ),
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "summary": aggregator_outcome.summary
        if aggregator_outcome and aggregator_outcome.summary
        else {},
        "artifacts": artifacts_section,
        "inputs": {
            "doc_index_output_dir": _relativize(
                paths.doc_index_output_dir, paths.repo_root
            ),
            "anchor_inventory_output_dir": _relativize(
                paths.anchor_inventory_output_dir, paths.repo_root
            ),
            "anchor_validation_output_dir": _relativize(
                paths.anchor_validation_output_dir, paths.repo_root
            ),
            "docs_integrity_output_dir": _relativize(
                paths.docs_integrity_output_dir, paths.repo_root
            ),
            "metrics_stub_output_dir": _relativize(
                paths.metrics_stub_output_dir, paths.repo_root
            ),
            "churn_output_dir": _relativize(paths.churn_output_dir, paths.repo_root),
            "undocumented_output_dir": _relativize(
                paths.undocumented_output_dir, paths.repo_root
            ),
            "placeholder_output_dir": _relativize(
                paths.placeholder_output_dir, paths.repo_root
            ),
            "monkey_patch_output_dir": _relativize(
                paths.monkey_patch_output_dir, paths.repo_root
            ),
            "aggregator_output_dir": _relativize(
                paths.aggregator_output_dir, paths.repo_root
            ),
            "skip_doc_index": options.skip_doc_index,
            "skip_anchor_inventory": options.skip_anchor_inventory,
            "skip_anchor_validation": options.skip_anchor_validation,
            "skip_docs_integrity": options.skip_docs_integrity,
            "skip_metrics_stub": options.skip_metrics_stub,
            "skip_churn": options.skip_churn,
            "skip_undocumented": options.skip_undocumented,
            "skip_aggregator": options.skip_aggregator,
            "skip_hygiene_signals": options.skip_hygiene_signals,
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
    }

    summary_markdown = _summarize_steps(result.steps)

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: manifest),
        ReportArtifact(
            filename="summary.md", kind="text", content=lambda: summary_markdown
        ),
        ReportArtifact(
            filename="telemetry.json", kind="json", content=lambda: telemetry_payload
        ),
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

    artifact_metrics = measure_artifact_directory(result_artifacts.run_dir)
    metrics_section = telemetry_payload.setdefault("metrics", {})
    metrics_section.update(artifact_metrics.as_dict())
    manifest["telemetry"] = telemetry_payload
    manifest["metrics"] = dict(metrics_section)

    manifest_path = result_artifacts.artifacts["manifest.json"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    telemetry_path = result_artifacts.artifacts["telemetry.json"]
    telemetry_path.write_text(
        json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    try:
        enforce_report_naming(
            reports_root=paths.healthview_root,
            run_dir=result_artifacts.run_dir,
            viewer=VIEWER_SLUG,
            topic=HEALTHVIEW_TOPIC,
            artifact_roles=(
                "manifest.json",
                "summary.md",
                "summary.json",
                "telemetry.json",
            ),
        )
    except GuardrailViolationError as exc:
        LOGGER.error("Report naming audit failed: %s", exc)
        return 1

    LOGGER.info("Docs Health orchestrator complete (slug=%s)", run_slug)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    """Entry point for CLI invocation.

    Args:
        argv: Command-line arguments. Defaults to sys.argv if None.

    Raises:
        SystemExit: Always raises with the run exit code.
    """
    raise SystemExit(run(argv))


__all__ = [
    "run",
    "main",
    "parse_args",
    "build_paths",
    "build_options",
    "configure_logging",
    "DocIndexOutcome",
    "AnchorInventoryOutcome",
    "AnchorValidationOutcome",
    "DocsIntegrityOutcome",
    "MetricsStubOutcome",
    "ChurnOutcome",
    "UndocumentedOutcome",
    "AggregatorOutcome",
]


if __name__ == "__main__":
    main()
