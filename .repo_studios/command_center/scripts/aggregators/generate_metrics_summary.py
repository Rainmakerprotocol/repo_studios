#!/usr/bin/env python3
"""Compose a metrics_summary.json artifact for Phase 4 automation dry runs."""

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
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        TestRunResult,
        build_metrics_summary,
        build_standard_options,
        build_standard_paths,
        write_metrics_summary,
        write_report_artifacts,
    )
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - CLI fallback for script execution
    SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    from libraries import (  # type: ignore  # noqa: E402
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        TestRunResult,
        build_metrics_summary,
        build_standard_options,
        build_standard_paths,
        write_metrics_summary,
        write_report_artifacts,
    )
    from libraries.retention_policy import get_keep  # type: ignore  # noqa: E402

DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
VIEWER_SLUG = "commandview"
TOPIC_SLUG = "automation_metrics"
DEFAULT_KEEP = get_keep("generate_metrics_summary")
RUN_STEM = "metrics_summary"
SUMMARY_FILENAME = "metrics_summary.json"
DEFAULT_SCHEMA_VERSION = "1.0"


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


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root (defaults to ancestor traversal)")
    parser.add_argument(
        "--output-dir",
        help="Directory for timestamped metrics summaries",
    )
    parser.add_argument(
        "--keep",
        type=int,
        default=DEFAULT_KEEP,
        help="Number of historical runs to retain",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO8601 timestamp for run directory naming (UTC if absent)",
    )
    parser.add_argument(
        "--schema-version",
        default=DEFAULT_SCHEMA_VERSION,
        help="Schema version to embed in metrics summary",
    )
    parser.add_argument("--run-id", required=True, help="Unique identifier for the automation run")
    parser.add_argument(
        "--target",
        dest="targets",
        action="append",
        required=True,
        help="Slugged target processed during the run (repeatable)",
    )
    parser.add_argument("--lines-touched", type=int, required=True, help="Total lines changed during the run")
    parser.add_argument("--files-changed", type=int, required=True, help="Count of files modified")
    parser.add_argument(
        "--duplicate-groups-resolved",
        type=int,
        required=True,
        help="Number of duplicate groups addressed",
    )
    parser.add_argument(
        "--runtime-seconds",
        type=float,
        required=True,
        help="Wall-clock execution time for the run",
    )
    parser.add_argument(
        "--tests-file",
        required=True,
        help="Path to JSON describing executed test suites (status, duration, artifacts)",
    )
    parser.add_argument("--notes", default="", help="Optional operator notes to include in the summary")
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

    timestamp = _parse_timestamp(args.timestamp)

    summary = build_metrics_summary(
        schema_version=args.schema_version,
        run_id=args.run_id,
        targets=args.targets,
        lines_touched=args.lines_touched,
        files_changed=args.files_changed,
        duplicate_groups_resolved=args.duplicate_groups_resolved,
        runtime_seconds=args.runtime_seconds,
        tests_executed=tests,
        notes=args.notes,
    )

    def _write_summary(run_dir: Path) -> Path:
        target = run_dir / SUMMARY_FILENAME
        return write_metrics_summary(summary, target)

    artifacts = [
        ReportArtifact(
            filename=SUMMARY_FILENAME,
            writer=_write_summary,
        )
    ]

    result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer=VIEWER_SLUG,
        topic=TOPIC_SLUG,
    )

    logging.info("Metrics summary written to %s", result.artifacts[SUMMARY_FILENAME])
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
