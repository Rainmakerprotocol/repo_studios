#!/usr/bin/env python3
"""Meta orchestrator that executes every topic runner sequentially."""

from __future__ import annotations

import argparse
import importlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from command_center.scripts.libraries import (
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    ReportArtifact,
    ArtifactMetrics,
    measure_artifact_directory,
    build_standard_options,
    build_standard_paths,
    write_report_artifacts,
)

LOGGER = logging.getLogger(__name__)

SCHEMA_VERSION = 1
META_VIEWER = "healthview"
META_TOPIC = "full_diagnostic"

DEFAULT_REPORTS_ROOT = Path(".repo_studios/command_center/reports")


@dataclass(frozen=True)
class TopicDefinition:
    slug: str
    module: str
    description: str = ""


TOPIC_DEFINITIONS: tuple[TopicDefinition, ...] = (
    TopicDefinition(
        slug="test-execution-telemetry",
        module="command_center.scripts.orchestrators.run_test_execution_telemetry",
        description="Test execution telemetry topic orchestrator",
    ),
    TopicDefinition(
        slug="docs-health",
        module="command_center.scripts.orchestrators.run_docs_health_overview",
        description="Docs health overview orchestrator",
    ),
    TopicDefinition(
        slug="fault-diagnostics",
        module="command_center.scripts.orchestrators.run_fault_diagnostics_overview",
        description="Fault diagnostics orchestrator",
    ),
    TopicDefinition(
        slug="dependency-import-hygiene",
        module="command_center.scripts.orchestrators.run_dependency_import_hygiene",
        description="Dependency and import hygiene orchestrator",
    ),
    TopicDefinition(
        slug="monkey-patch-oversight",
        module="command_center.scripts.orchestrators.run_monkey_patch_oversight",
        description="Monkey patch oversight orchestrator",
    ),
    TopicDefinition(
        slug="standards-integrity",
        module="command_center.scripts.orchestrators.run_standards_integrity",
        description="Standards integrity orchestrator",
    ),
)


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    reports_root: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "reports_root": PathSpec(
            field="reports_root",
            default=DEFAULT_REPORTS_ROOT,
            ensure_dir=True,
            within_repo=False,
        )
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


@dataclass(frozen=True)
class Options:
    log_level: str
    stop_on_first_failure: bool
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    run_timestamp: datetime
    artifacts_to_keep: int


@dataclass(frozen=True)
class TopicRunRecord:
    slug: str
    module: str
    viewer: str | None
    topic: str | None
    status: str
    exit_code: int | None
    started_at: datetime | None
    finished_at: datetime | None
    run_slug: str | None
    artifact_dir: Path | None
    argv: tuple[str, ...]
    message: str | None

    def duration_seconds(self) -> float | None:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def _parse_topic_list(values: Iterable[str] | None) -> tuple[str, ...]:
    seen: list[str] = []
    if values:
        for raw in values:
            for part in raw.split(","):
                cleaned = part.strip()
                if cleaned and cleaned not in seen:
                    seen.append(cleaned)
    return tuple(seen)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        candidate = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if candidate.tzinfo is None:
        return candidate.replace(tzinfo=timezone.utc)
    return candidate.astimezone(timezone.utc)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--reports-root", default=str(DEFAULT_REPORTS_ROOT))
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--timestamp", help="ISO-8601 timestamp forwarded to topic orchestrators")
    parser.add_argument("--artifacts-to-keep", type=int, default=3)
    parser.add_argument("--include", action="append", help="Limit execution to the provided topic slug(s)")
    parser.add_argument("--exclude", action="append", help="Skip the provided topic slug(s)")
    parser.add_argument(
        "--stop-on-first-failure",
        dest="stop_on_first_failure",
        action="store_true",
        help="Abort remaining topics after the first failure",
    )
    parser.add_argument(
        "--keep-going",
        dest="stop_on_first_failure",
        action="store_false",
        help="Continue running topics even when failures occur",
    )
    parser.set_defaults(stop_on_first_failure=True)
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    return Options(
        log_level=str(args.log_level),
        stop_on_first_failure=bool(args.stop_on_first_failure),
        include=_parse_topic_list(args.include),
        exclude=_parse_topic_list(args.exclude),
        run_timestamp=_parse_timestamp(args.timestamp),
        artifacts_to_keep=keep_values.artifacts_to_keep,
    )


def _select_topics(definitions: Sequence[TopicDefinition], *, include: tuple[str, ...], exclude: tuple[str, ...]) -> list[TopicDefinition]:
    index = {definition.slug: definition for definition in definitions}
    unknown_includes = [slug for slug in include if slug not in index]
    if unknown_includes:
        raise SystemExit(f"Unknown --include topic(s): {', '.join(sorted(unknown_includes))}")
    unknown_excludes = [slug for slug in exclude if slug not in index]
    if unknown_excludes:
        raise SystemExit(f"Unknown --exclude topic(s): {', '.join(sorted(unknown_excludes))}")

    if include:
        ordered = [index[slug] for slug in include]
    else:
        ordered = list(definitions)

    filtered: list[TopicDefinition] = []
    excluded = set(exclude)
    for definition in ordered:
        if definition.slug in excluded:
            continue
        filtered.append(definition)
    if not filtered:
        raise SystemExit("No topics selected for execution")
    return filtered


def _load_topic_module(name: str):
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise SystemExit(f"Unable to import orchestrator module '{name}': {exc}") from exc


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path.resolve())


def _build_topic_record(
    *,
    definition: TopicDefinition,
    module,
    status: str,
    exit_code: int | None,
    started_at: datetime | None,
    finished_at: datetime | None,
    run_slug: str | None,
    reports_root: Path,
    argv: tuple[str, ...],
    message: str | None,
) -> TopicRunRecord:
    viewer_slug = getattr(module, "VIEWER_SLUG", None)
    topic_slug = getattr(module, "HEALTHVIEW_TOPIC", getattr(module, "TOPIC_SLUG", None))
    artifact_dir: Path | None = None
    if run_slug and viewer_slug and topic_slug:
        artifact_dir = reports_root / viewer_slug / topic_slug / run_slug
    return TopicRunRecord(
        slug=definition.slug,
        module=definition.module,
        viewer=viewer_slug,
        topic=topic_slug,
        status=status,
        exit_code=exit_code,
        started_at=started_at,
        finished_at=finished_at,
        run_slug=run_slug,
        artifact_dir=artifact_dir,
        argv=argv,
        message=message,
    )


def _summarize(records: Sequence[TopicRunRecord]) -> str:
    lines = ["# Full Diagnostic Run", ""]
    for record in records:
        status = record.status.upper()
        detail_bits: list[str] = []
        if record.viewer and record.topic:
            detail_bits.append(f"{record.viewer}/{record.topic}")
        if record.message:
            detail_bits.append(record.message)
        if record.exit_code not in (None, 0):
            detail_bits.append(f"exit={record.exit_code}")
        detail = f" ({'; '.join(detail_bits)})" if detail_bits else ""
        lines.append(f"- {record.slug}: {status}{detail}")
    return "\n".join(lines) + "\n"


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    meta_started = datetime.now(timezone.utc)

    LOGGER.info("Starting full diagnostic orchestrator (stop_on_first_failure=%s)", options.stop_on_first_failure)

    selected_order = _select_topics(
        TOPIC_DEFINITIONS,
        include=options.include,
        exclude=options.exclude,
    )

    meta_run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")

    module_cache: dict[str, object] = {}

    def get_module(definition: TopicDefinition):
        if definition.module not in module_cache:
            module_cache[definition.module] = _load_topic_module(definition.module)
        return module_cache[definition.module]

    records_by_slug: dict[str, TopicRunRecord] = {}
    failures: list[TopicRunRecord] = []
    executed_slugs: set[str] = set()

    for definition in selected_order:
        module = get_module(definition)
        runner = getattr(module, "run", None)
        if not callable(runner):
            raise SystemExit(f"Module '{definition.module}' is missing a callable run() helper")
        topic_args_list = [
            "--repo-root",
            str(paths.repo_root),
            "--log-level",
            options.log_level,
            "--timestamp",
            options.run_timestamp.isoformat(),
        ]
        start = datetime.now(timezone.utc)
        try:
            exit_code = int(runner(topic_args_list))
            message: str | None = None
        except Exception as exc:  # pragma: no cover - defensive fallback
            LOGGER.exception("Topic %s raised an unexpected error", definition.slug)
            exit_code = 1
            message = str(exc)
        end = datetime.now(timezone.utc)

        if exit_code != 0 and message is None:
            message = "non-zero exit"

        status = "succeeded" if exit_code == 0 else "failed"
        record = _build_topic_record(
            definition=definition,
            module=module,
            status=status,
            exit_code=exit_code,
            started_at=start,
            finished_at=end,
            run_slug=meta_run_slug,
            reports_root=paths.reports_root,
            argv=tuple(topic_args_list),
            message=message,
        )
        records_by_slug[definition.slug] = record
        executed_slugs.add(definition.slug)
        if exit_code != 0:
            failures.append(record)
            LOGGER.error("Topic %s failed with exit code %s", definition.slug, exit_code)
            if options.stop_on_first_failure:
                LOGGER.info("Stopping after failure due to --stop-on-first-failure")
                break

    selected_slugs = {definition.slug for definition in selected_order}

    for definition in TOPIC_DEFINITIONS:
        if definition.slug in records_by_slug:
            continue
        module = get_module(definition)
        if definition.slug in selected_slugs and definition.slug not in executed_slugs:
            message = "skipped after earlier failure"
        else:
            message = "skipped via include/exclude"
        records_by_slug[definition.slug] = _build_topic_record(
            definition=definition,
            module=module,
            status="skipped",
            exit_code=None,
            started_at=None,
            finished_at=None,
            run_slug=None,
            reports_root=paths.reports_root,
            argv=tuple(),
            message=message,
        )

    records = [records_by_slug[definition.slug] for definition in TOPIC_DEFINITIONS]

    success = not failures
    overall_exit = 0 if success else 1

    finished_at = datetime.now(timezone.utc)

    artifact_metrics_by_slug: dict[str, ArtifactMetrics] = {}
    total_topic_runtime = 0.0
    succeeded_topics = 0
    failed_topics = 0
    skipped_topics = 0
    artifact_file_total = 0
    artifact_byte_total = 0

    for record in records:
        metrics = measure_artifact_directory(record.artifact_dir)
        artifact_metrics_by_slug[record.slug] = metrics
        artifact_file_total += metrics.file_count
        artifact_byte_total += metrics.total_bytes
        duration = record.duration_seconds()
        if duration:
            total_topic_runtime += duration
        if record.status == "succeeded":
            succeeded_topics += 1
        elif record.status == "failed":
            failed_topics += 1
        else:
            skipped_topics += 1

    overall_runtime = (finished_at - meta_started).total_seconds()
    metrics_payload: dict[str, float | int] = {
        "topics_total": len(records),
        "topics_succeeded": succeeded_topics,
        "topics_failed": failed_topics,
        "topics_skipped": skipped_topics,
        "topics_duration_seconds": total_topic_runtime,
        "runtime_seconds": overall_runtime if overall_runtime >= 0 else 0.0,
        "artifact_files": artifact_file_total,
        "artifact_bytes": artifact_byte_total,
    }

    manifest_topics = [
        {
            "slug": record.slug,
            "module": record.module,
            "viewer": record.viewer,
            "topic": record.topic,
            "status": record.status,
            "exit_code": record.exit_code,
            "started_at": record.started_at.isoformat() if record.started_at else None,
            "finished_at": record.finished_at.isoformat() if record.finished_at else None,
            "duration_seconds": record.duration_seconds(),
            "run_slug": record.run_slug,
            "artifact_dir": _relativize(record.artifact_dir, paths.repo_root),
            "artifact_files": artifact_metrics_by_slug[record.slug].file_count,
            "artifact_bytes": artifact_metrics_by_slug[record.slug].total_bytes,
            "argv": list(record.argv),
            "message": record.message,
        }
        for record in records
    ]

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": META_VIEWER,
        "topic": META_TOPIC,
        "run_slug": meta_run_slug,
        "generated_at": finished_at.isoformat(),
        "success": success,
        "inputs": {
            "log_level": options.log_level,
            "timestamp": options.run_timestamp.isoformat(),
            "stop_on_first_failure": options.stop_on_first_failure,
            "include": list(options.include),
            "exclude": list(options.exclude),
            "artifacts_to_keep": options.artifacts_to_keep,
        },
        "topics": manifest_topics,
        "metrics": dict(metrics_payload),
    }

    summary_markdown = _summarize(records)
    telemetry_topics = [
        {
            "slug": record.slug,
            "status": record.status,
            "exit_code": record.exit_code,
            "duration_seconds": record.duration_seconds(),
            "artifact_files": artifact_metrics_by_slug[record.slug].file_count,
            "artifact_bytes": artifact_metrics_by_slug[record.slug].total_bytes,
        }
        for record in records
    ]

    telemetry_payload = {
        "viewer": META_VIEWER,
        "topic": META_TOPIC,
        "run_slug": meta_run_slug,
        "success": success,
        "started_at": options.run_timestamp.isoformat(),
        "finished_at": finished_at.isoformat(),
        "topics": telemetry_topics,
        "metrics": dict(metrics_payload),
    }

    report_artifacts = write_report_artifacts(
        stem=META_TOPIC,
        timestamp=options.run_timestamp,
        output_dir=paths.reports_root,
        artifacts=[
            ReportArtifact(filename="manifest.json", kind="json", content=lambda: manifest),
            ReportArtifact(filename="summary.md", kind="text", content=lambda: summary_markdown),
            ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
        ],
        keep=options.artifacts_to_keep,
        viewer=META_VIEWER,
        topic=META_TOPIC,
    )

    meta_artifact_metrics = measure_artifact_directory(report_artifacts.run_dir)
    metrics_payload.update(
        {
            "meta_artifact_files": meta_artifact_metrics.file_count,
            "meta_artifact_bytes": meta_artifact_metrics.total_bytes,
        }
    )
    manifest["metrics"] = dict(metrics_payload)
    telemetry_payload["metrics"] = dict(metrics_payload)

    manifest_path = report_artifacts.artifacts["manifest.json"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    telemetry_path = report_artifacts.artifacts["telemetry.json"]
    telemetry_path.write_text(json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if success:
        LOGGER.info("Full diagnostic orchestrator completed successfully")
    else:
        LOGGER.error("Full diagnostic orchestrator completed with failures")
    return overall_exit


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))


__all__ = [
    "run",
    "main",
    "parse_args",
    "build_paths",
    "build_options",
    "TOPIC_DEFINITIONS",
]
