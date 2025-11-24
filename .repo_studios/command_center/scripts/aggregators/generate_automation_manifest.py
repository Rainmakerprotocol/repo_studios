#!/usr/bin/env python3
"""Generate automation manifest and metrics summary artifacts for Phase 4 rehearsals."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

try:
    from libraries import (
        GuardrailState,
        GuardrailViolationError,
        KeepSpec,
        ManifestFile,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        TestRunResult,
        enforce_run_size_limit,
        build_automation_manifest,
        build_metrics_summary,
        build_standard_options,
        build_standard_paths,
        load_guardrail_config,
        write_automation_manifest,
        write_metrics_summary,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - CLI fallback for script execution
    SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    from libraries import (  # type: ignore  # noqa: E402
        GuardrailState,
        GuardrailViolationError,
        KeepSpec,
        ManifestFile,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        TestRunResult,
        enforce_run_size_limit,
        build_automation_manifest,
        build_metrics_summary,
        build_standard_options,
        build_standard_paths,
        load_guardrail_config,
        write_automation_manifest,
        write_metrics_summary,
        write_report_artifacts,
    )

DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports/automation_runs")
DEFAULT_KEEP = 3
RUN_STEM = "automation_manifest"
MANIFEST_FILENAME = "manifest.json"
MANIFEST_POINTER = "latest_automation_manifest.json"
METRICS_FILENAME = "metrics_summary.json"
METRICS_POINTER = "latest_metrics_summary.json"
DEFAULT_MANIFEST_SCHEMA_VERSION = "1.0"
DEFAULT_METRICS_SCHEMA_VERSION = "1.0"
_ALLOWED_FILE_STATUSES = ("updated", "skipped", "conflicted")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True),
    },
)

OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="keep", minimum=DEFAULT_KEEP),
    },
)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - argparse guards in tests
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_tests(mapping: Mapping[str, object]) -> dict[str, TestRunResult]:
    results: dict[str, TestRunResult] = {}
    for name, payload in mapping.items():
        if not isinstance(name, str) or not name:
            raise ValueError("Test names must be non-empty strings")
        if not isinstance(payload, Mapping):
            raise ValueError(f"Test entry for {name!r} must be an object")
        status = payload.get("status")
        duration = payload.get("duration_seconds")
        artifacts = payload.get("artifacts", [])
        if status is None or duration is None:
            raise ValueError(f"Test entry for {name!r} requires status and duration_seconds")
        try:
            duration_value = float(duration)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid duration for {name!r}") from exc
        if not isinstance(artifacts, (list, tuple)):
            raise ValueError(f"Artifacts for {name!r} must be a list")
        artifacts_list = [str(item) for item in artifacts if str(item)]
        results[name] = TestRunResult(
            status=str(status),
            duration_seconds=duration_value,
            artifacts=tuple(artifacts_list),
        )
    if not results:
        raise ValueError("At least one test entry is required")
    return results


def _load_tests_from_file(path: Path) -> dict[str, TestRunResult]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Tests file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Tests file contains invalid JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Tests file must contain an object at the top level")
    return _load_tests(payload)


def _normalize_duplicate_groups(raw: object) -> tuple[str, ...]:
    if raw is None:
        return tuple()
    if isinstance(raw, (list, tuple)):
        return tuple(str(item) for item in raw if str(item))
    raise ValueError("duplicate_groups must be a list when provided")


def _parse_manifest_entry(entry: object) -> ManifestFile:
    if isinstance(entry, str):
        return ManifestFile(path=entry)
    if not isinstance(entry, Mapping):
        raise ValueError("File entries must be objects or strings")
    path = entry.get("path")
    if not isinstance(path, str) or not path:
        raise ValueError("Manifest entries require a non-empty 'path'")
    duplicate_groups = _normalize_duplicate_groups(entry.get("duplicate_groups"))
    return ManifestFile(path=path, duplicate_groups=duplicate_groups)


def _load_files(payload: Mapping[str, object]) -> tuple[dict[str, tuple[ManifestFile, ...]], int, int]:
    files: dict[str, tuple[ManifestFile, ...]] = {}
    total = 0
    changed = 0
    for status in _ALLOWED_FILE_STATUSES:
        entries_raw = payload.get(status, [])
        if entries_raw is None:
            entries_iterable: list[object] = []
        elif isinstance(entries_raw, (list, tuple)):
            entries_iterable = list(entries_raw)
        else:
            raise ValueError(f"Entries for status {status!r} must be a list")
        parsed = tuple(_parse_manifest_entry(item) for item in entries_iterable)
        files[status] = parsed
        total += len(parsed)
        if status in {"updated", "conflicted"}:
            changed += len(parsed)
    for status in payload.keys():
        if status not in _ALLOWED_FILE_STATUSES:
            raise ValueError(f"Unsupported file status: {status}")
    return files, changed, total


def _load_files_from_file(path: Path) -> tuple[dict[str, tuple[ManifestFile, ...]], int, int]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Files file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Files file contains invalid JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("Files file must contain an object at the top level")
    return _load_files(payload)


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root (defaults to ancestor traversal)")
    parser.add_argument("--output-dir", help="Directory for automation run artifacts")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="Number of historical runs to retain")
    parser.add_argument("--timestamp", help="ISO8601 timestamp for run directory naming (UTC if absent)")
    parser.add_argument(
        "--manifest-schema-version", default=DEFAULT_MANIFEST_SCHEMA_VERSION, help="Schema version to embed in manifest"
    )
    parser.add_argument(
        "--metrics-schema-version",
        default=DEFAULT_METRICS_SCHEMA_VERSION,
        help="Schema version to embed in metrics summary",
    )
    parser.add_argument("--run-id", required=True, help="Unique identifier for the automation run")
    parser.add_argument("--baseline-sha", required=True, help="Git commit SHA used as the automation baseline")
    parser.add_argument(
        "--target",
        dest="targets",
        action="append",
        required=True,
        help="Slugged target processed during the run (repeatable)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Flag indicating the run emitted artifacts only")
    parser.add_argument("--operator", help="Operator responsible for the run")
    parser.add_argument("--notes", default="", help="Optional operator notes to include in the manifest")
    parser.add_argument("--files-file", required=True, help="Path to JSON describing updated/skipped/conflicted files")
    parser.add_argument("--tests-file", required=True, help="Path to JSON describing executed test suites")
    parser.add_argument("--lines-touched", type=int, required=True, help="Total lines changed during the run")
    parser.add_argument("--files-changed", type=int, required=True, help="Count of files modified")
    parser.add_argument(
        "--duplicate-groups-resolved", type=int, required=True, help="Number of duplicate groups addressed"
    )
    parser.add_argument("--runtime-seconds", type=float, required=True, help="Wall-clock execution time for the run")
    parser.add_argument("--guardrail-config", help="Path to guardrail configuration YAML to snapshot in the manifest")
    parser.add_argument(
        "--guardrail-override", action="store_true", help="Indicate whether the guardrail override flag was used"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    try:
        paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
        options = build_standard_options(args, OPTIONS_CONFIG)
    except Exception as exc:  # pragma: no cover - defensive
        logging.error("Failed to resolve paths: %s", exc)
        return 2

    try:
        tests = _load_tests_from_file(Path(args.tests_file))
    except ValueError as exc:
        logging.error("Failed to load tests metadata: %s", exc)
        return 1

    try:
        files_mapping, changed_count, total_files = _load_files_from_file(Path(args.files_file))
    except ValueError as exc:
        logging.error("Failed to load file manifest details: %s", exc)
        return 1

    if changed_count != args.files_changed:
        logging.error(
            "Files changed mismatch between manifest entries (%s) and provided value (%s)",
            changed_count,
            args.files_changed,
        )
        return 1

    guardrail_state = None
    if args.guardrail_config:
        try:
            config = load_guardrail_config(Path(args.guardrail_config))
        except Exception as exc:
            logging.error("Failed to load guardrail configuration: %s", exc)
            return 1
        candidate_paths = [
            (paths.repo_root / Path(entry.path)).resolve()
            for status in ("updated", "conflicted")
            for entry in files_mapping.get(status, tuple())
        ]
        try:
            limit, considered = enforce_run_size_limit(
                candidate_paths,
                config,
                override=bool(args.guardrail_override),
            )
        except GuardrailViolationError as exc:
            logging.error("Guardrail violation: %s", exc)
            return 1
        guardrail_state = GuardrailState(
            max_files_per_run=limit,
            files_considered=considered,
            override_applied=bool(args.guardrail_override),
            config_path=config.config_path,
            allow_list_source=config.allow_list_source,
            metadata=config.metadata,
        )

    timestamp = _parse_timestamp(args.timestamp)

    metrics_summary = build_metrics_summary(
        schema_version=args.metrics_schema_version,
        run_id=args.run_id,
        targets=args.targets,
        lines_touched=args.lines_touched,
        files_changed=args.files_changed,
        duplicate_groups_resolved=args.duplicate_groups_resolved,
        runtime_seconds=args.runtime_seconds,
        tests_executed=tests,
        notes=args.notes,
    )

    def _write_metrics(run_dir: Path) -> Path:
        target = run_dir / METRICS_FILENAME
        return write_metrics_summary(metrics_summary, target)

    def _write_manifest(run_dir: Path) -> Path:
        manifest = build_automation_manifest(
            schema_version=args.manifest_schema_version,
            run_id=args.run_id,
            timestamp=timestamp,
            targets=args.targets,
            baseline_sha=args.baseline_sha,
            dry_run=bool(args.dry_run),
            operator=args.operator,
            notes=args.notes,
            files=files_mapping,
            guardrail_state=guardrail_state,
            metrics_summary=metrics_summary,
            metrics_summary_path=METRICS_FILENAME,
        )
        return write_automation_manifest(manifest, run_dir / MANIFEST_FILENAME)

    artifacts = [
        ReportArtifact(
            filename=METRICS_FILENAME,
            pointer=METRICS_POINTER,
            writer=_write_metrics,
        ),
        ReportArtifact(
            filename=MANIFEST_FILENAME,
            pointer=MANIFEST_POINTER,
            writer=_write_manifest,
        ),
    ]

    result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    logging.info("Automation manifest written to %s", result.artifacts[MANIFEST_FILENAME])
    logging.info("Metrics summary written to %s", result.artifacts[METRICS_FILENAME])
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
