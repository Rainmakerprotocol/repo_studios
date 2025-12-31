#!/usr/bin/env python3
"""
Generate HealthView Fault Diagnostics overview bundle.

This summarizer consumes fault artifact bundles from the consumer stage
and produces a consolidated overview with baseline comparison.

Input Path Contract
-------------------
Consumer artifacts from:
``.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/``

Expected consumer artifacts:

- ``manifest.json`` — bundle metadata
- ``telemetry.json`` — metrics and signatures
- ``summary.md`` — human-readable digest

Output Path Contract (HOP)
--------------------------
``.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/``

Base Package
------------
- ``manifest.json`` — overview metadata
- ``summary.md`` — consolidated digest with baseline comparison
- ``telemetry.json`` — aggregated metrics

CLI Arguments
-------------
--consumer-output-dir
    Consumer bundle location. Defaults to HOP path.
--consumer-telemetry
    Explicit telemetry.json path override.
--consumer-manifest
    Explicit manifest.json path override.
--output-dir
    Summarizer output root. Defaults to HOP path.
--artifacts-to-keep
    Retention budget for timestamped bundles.

Notes
-----
- Discovers latest consumer bundle via timestamp-sorted directory listing.
- No pointer files (``latest_*``) are used for discovery per HOP contract.
- Compares current run against previous bundle for baseline delta.

.. seealso::
    :doc:`REPORT_NAMING_STANDARDS` for HOP path contract.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:  # pragma: no cover - prefer import when packaged
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        WriteReportArtifactsResult,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
    from libraries.report_paths import build_topic_path
except ModuleNotFoundError:  # pragma: no cover - fallback when running in isolation
    LIBRARIES_ROOT = Path(__file__).resolve().parents[1]
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        WriteReportArtifactsResult,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
    from libraries.report_paths import build_topic_path

CONSUMER_TOPIC_SLUG = "fault_artifacts"
PRODUCER_TOPIC_SLUG = "faulthandler_reports"
TOPIC_SLUG = "fault_diagnostics_overview"
DEFAULT_CONSUMER_OUTPUT_DIR = build_topic_path("consumer", CONSUMER_TOPIC_SLUG)
DEFAULT_PRODUCER_OUTPUT_DIR = build_topic_path("producer", PRODUCER_TOPIC_SLUG)
DEFAULT_SUMMARIZER_OUTPUT_DIR = build_topic_path("summarizer", TOPIC_SLUG)
SUMMARY_STEM = "fault_diagnostics_overview"
SCHEMA_VERSION = 1

# HOP consumer artifact names
CONSUMER_MANIFEST_NAME = "manifest.json"
CONSUMER_TELEMETRY_NAME = "telemetry.json"
CONSUMER_SUMMARY_NAME = "summary.md"

# HOP timestamp pattern: YYYYMMDD-HHMM (13 chars)
HOP_TIMESTAMP_PATTERN = re.compile(r"^\d{8}-\d{4}$")


@dataclass(frozen=True)
class Paths:
    """
    Resolved path configuration for summarizer execution.

    :ivar repo_root: Repository root directory.
    :ivar consumer_output_dir: Consumer artifact location.
    :ivar producer_output_dir: Producer report location.
    :ivar output_dir: Summarizer output root.
    """

    repo_root: Path
    consumer_output_dir: Path
    producer_output_dir: Path
    output_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "consumer_output_dir": PathSpec(
            field="consumer_output_dir", default=DEFAULT_CONSUMER_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "producer_output_dir": PathSpec(
            field="producer_output_dir", default=DEFAULT_PRODUCER_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_SUMMARIZER_OUTPUT_DIR, ensure_dir=True, within_repo=False),
    },
    repo_root_depth=5,
)


@dataclass(frozen=True)
class Options:
    """
    Runtime options for summarizer execution.

    :ivar artifacts_to_keep: Retention budget for output bundles.
    :ivar log_level: Logging verbosity level.
    :ivar run_timestamp: UTC timestamp for artifact generation.
    :ivar consumer_telemetry_override: Explicit telemetry.json path.
    :ivar consumer_manifest_override: Explicit manifest.json path.
    :ivar producer_report_override: Explicit producer report path.
    """

    artifacts_to_keep: int
    log_level: str
    run_timestamp: datetime
    consumer_telemetry_override: Path | None
    consumer_manifest_override: Path | None
    producer_report_override: Path | None


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _parse_args(argv: Iterable[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--consumer-output-dir", default=str(DEFAULT_CONSUMER_OUTPUT_DIR))
    parser.add_argument("--producer-output-dir", default=str(DEFAULT_PRODUCER_OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_SUMMARIZER_OUTPUT_DIR))
    parser.add_argument("--consumer-telemetry", help="Explicit consumer telemetry.json path override")
    parser.add_argument("--consumer-manifest", help="Explicit consumer manifest.json path override")
    parser.add_argument("--producer-report", help="Explicit producer report.json override")
    parser.add_argument("--artifacts-to-keep", type=int, default=5, help="Retention budget for overview artifacts")
    parser.add_argument(
        "--timestamp",
        help="ISO-8601 timestamp for the emitted artifacts (defaults to current UTC time)",
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
    """Construct Options from parsed CLI arguments.

    :param args: Parsed argument namespace from _parse_args().
    :type args: argparse.Namespace
    :param paths: Resolved Paths instance.
    :type paths: Paths
    :returns: Fully resolved Options instance.
    :rtype: Options
    """
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    return Options(
        artifacts_to_keep=max(int(getattr(keep_values, "artifacts_to_keep", 1)), 1),
        log_level=str(args.log_level),
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
        consumer_telemetry_override=_resolve_optional_path(
            paths.repo_root, getattr(args, "consumer_telemetry", None)
        ),
        consumer_manifest_override=_resolve_optional_path(
            paths.repo_root, getattr(args, "consumer_manifest", None)
        ),
        producer_report_override=_resolve_optional_path(paths.repo_root, getattr(args, "producer_report", None)),
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_json(path: Path | None) -> Any | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _ensure_path(source: Path | None, *, base: Path, filename: str) -> Path | None:
    """Resolve artifact path from override or latest HOP timestamp directory.

    Locates the most recent HOP-compliant timestamp directory (YYYYMMDD-HHMM)
    under *base* and returns the path to *filename* within it.

    :param source: Explicit override path (returned if exists).
    :type source: Path | None
    :param base: Base directory containing timestamp directories.
    :type base: Path
    :param filename: Artifact filename to locate within timestamp directory.
    :type filename: str
    :returns: Resolved path to artifact, or None if not found.
    :rtype: Path | None
    """
    if source and source.exists():
        return source
    if not base.exists():
        return None
    candidates = [
        child for child in base.iterdir()
        if child.is_dir() and HOP_TIMESTAMP_PATTERN.match(child.name)
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda node: node.name)
    target = candidates[-1] / filename
    return target.resolve() if target.exists() else None


def _find_previous_bundle(base: Path, current_bundle: str | None) -> Path | None:
    """Find the most recent HOP bundle directory excluding the current one.

    Scans *base* for HOP-compliant timestamp directories (YYYYMMDD-HHMM)
    and returns the newest one that is not *current_bundle*.

    :param base: Base directory containing timestamp directories.
    :type base: Path
    :param current_bundle: Name of current bundle directory to exclude.
    :type current_bundle: str | None
    :returns: Path to previous bundle directory, or None if not found.
    :rtype: Path | None
    """
    if not base.exists():
        return None
    candidates = [
        child for child in base.iterdir()
        if child.is_dir() and HOP_TIMESTAMP_PATTERN.match(child.name)
    ]
    candidates.sort(key=lambda node: node.name)
    for node in reversed(candidates):
        if node.name != current_bundle:
            return node
    return None


def _extract_metrics(bundle_summary: Mapping[str, Any] | None) -> dict[str, int | None]:
    metrics: Mapping[str, Any] | None = None
    if isinstance(bundle_summary, Mapping):
        raw = bundle_summary.get("metrics")
        if isinstance(raw, Mapping):
            metrics = raw
    return {
        "signature_count": _coerce_int(metrics, "signature_count"),
        "active_signature_count": _coerce_int(metrics, "active_signature_count"),
        "repeat_offender": _coerce_int(metrics, "repeat_offender"),
        "multi_hit": _coerce_int(metrics, "multi_hit"),
        "single_hit": _coerce_int(metrics, "single_hit"),
        "thread_block_count": _coerce_int(metrics, "thread_block_count"),
    }


def _coerce_int(payload: Mapping[str, Any] | None, key: str) -> int | None:
    if not isinstance(payload, Mapping):
        return None
    value = payload.get(key)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _extract_severity(summary_payload: Mapping[str, Any] | None) -> dict[str, int | None]:
    severity: Mapping[str, Any] | None = None
    summary = summary_payload.get("summary") if isinstance(summary_payload, Mapping) else None
    if isinstance(summary, Mapping):
        candidate = summary.get("severity_buckets")
        if isinstance(candidate, Mapping):
            severity = candidate
    return {
        "repeat_offender": _coerce_int(severity, "repeat_offender") or 0,
        "multi_hit": _coerce_int(severity, "multi_hit") or 0,
        "single_hit": _coerce_int(severity, "single_hit") or 0,
    }


def _collect_signature_ids(summary_payload: Mapping[str, Any] | None) -> set[str]:
    if not isinstance(summary_payload, Mapping):
        return set()
    signatures = summary_payload.get("signatures")
    if not isinstance(signatures, list):
        return set()
    collected: set[str] = set()
    for entry in signatures:
        if isinstance(entry, Mapping):
            signature_id = entry.get("signature_id")
            if isinstance(signature_id, str) and signature_id:
                collected.add(signature_id)
    return collected


def _extract_producer_repeat_offender(payload: Mapping[str, Any] | None) -> int | None:
    if not isinstance(payload, Mapping):
        return None
    summary = payload.get("summary")
    if not isinstance(summary, Mapping):
        return None
    severity = summary.get("severity_buckets")
    return _coerce_int(severity if isinstance(severity, Mapping) else None, "repeat_offender")


def _build_markdown(
    *,
    generated_at: datetime,
    metrics: Mapping[str, int | None],
    severity: Mapping[str, int | None],
    baseline: Mapping[str, Any] | None,
    notes: list[str],
) -> str:
    lines: list[str] = ["# Fault Diagnostics Overview", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("## Current Snapshot")
    lines.append("")
    lines.append(f"- Total Signatures: {metrics.get('signature_count') or 0}")
    lines.append(f"- Active Signatures: {metrics.get('active_signature_count') or 0}")
    lines.append(f"- Repeat Offender: {severity.get('repeat_offender') or 0}")
    lines.append(f"- Multi Hit: {severity.get('multi_hit') or 0}")
    lines.append(f"- Single Hit: {severity.get('single_hit') or 0}")
    lines.append(f"- Thread Block Count: {metrics.get('thread_block_count') or 0}")
    lines.append("")
    lines.append("## Baseline Comparison")
    lines.append("")
    if baseline:
        bundle = baseline.get("bundle")
        lines.append(f"- Previous Bundle: {bundle}")
        summary = baseline.get("summary")
        if isinstance(summary, Mapping):
            new_ids = summary.get("new_signature_ids") or []
            removed_ids = summary.get("removed_signature_ids") or []
            lines.append(f"- New Signatures: {len(new_ids)}")
            if new_ids:
                for sig in new_ids:
                    lines.append(f"  - {sig}")
            lines.append(f"- Retired Signatures: {len(removed_ids)}")
            if removed_ids:
                for sig in removed_ids:
                    lines.append(f"  - {sig}")
    else:
        lines.append("- No prior bundle located for comparison.")
    if notes:
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(argv: Iterable[str] | None = None) -> dict[str, Any]:
    """Execute the summarizer and write HOP-compliant artifacts.

    Loads consumer telemetry/manifest artifacts, producer report, compares
    against previous bundles, and writes a summary overview bundle.

    :param argv: CLI arguments (uses sys.argv if None).
    :type argv: Iterable[str] | None
    :returns: Execution result with status, run_dir, slug, and artifacts.
    :rtype: dict[str, Any]
    """
    args = _parse_args(argv)
    paths = build_paths(args)
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)
    logger = logging.getLogger("summarize_fault_diagnostics_overview")

    consumer_telemetry_path = _ensure_path(
        options.consumer_telemetry_override,
        base=paths.consumer_output_dir,
        filename=CONSUMER_TELEMETRY_NAME,
    )
    consumer_manifest_path = _ensure_path(
        options.consumer_manifest_override,
        base=paths.consumer_output_dir,
        filename=CONSUMER_MANIFEST_NAME,
    )
    consumer_summary_md_path = _ensure_path(
        None,
        base=paths.consumer_output_dir,
        filename=CONSUMER_SUMMARY_NAME,
    )
    producer_report_path = _ensure_path(
        options.producer_report_override,
        base=paths.producer_output_dir,
        filename="report.json",
    )

    consumer_telemetry_payload = _load_json(consumer_telemetry_path)
    consumer_manifest_payload = _load_json(consumer_manifest_path)
    producer_payload = _load_json(producer_report_path)

    metrics = _extract_metrics(consumer_manifest_payload if isinstance(consumer_manifest_payload, Mapping) else None)
    severity = _extract_severity(consumer_telemetry_payload if isinstance(consumer_telemetry_payload, Mapping) else None)

    bundle_name = None
    if isinstance(consumer_manifest_payload, Mapping):
        raw_bundle = consumer_manifest_payload.get("bundle")
        if isinstance(raw_bundle, str):
            bundle_name = raw_bundle

    previous_bundle_dir = _find_previous_bundle(paths.consumer_output_dir, bundle_name)
    previous_manifest_payload = _load_json(previous_bundle_dir / CONSUMER_MANIFEST_NAME) if previous_bundle_dir else None
    previous_telemetry_payload = _load_json(previous_bundle_dir / CONSUMER_TELEMETRY_NAME) if previous_bundle_dir else None

    baseline_summary = None
    if previous_bundle_dir and isinstance(previous_manifest_payload, Mapping):
        previous_metrics = _extract_metrics(previous_manifest_payload)
        previous_severity = _extract_severity(previous_telemetry_payload if isinstance(previous_telemetry_payload, Mapping) else None)
        current_signatures = _collect_signature_ids(consumer_telemetry_payload if isinstance(consumer_telemetry_payload, Mapping) else None)
        previous_signatures = _collect_signature_ids(previous_telemetry_payload if isinstance(previous_telemetry_payload, Mapping) else None)
        new_signatures = sorted(current_signatures - previous_signatures)
        retired_signatures = sorted(previous_signatures - current_signatures)
        baseline_summary = {
            "bundle": previous_bundle_dir.name,
            "metrics": previous_metrics,
            "severity": previous_severity,
            "summary": {
                "new_signature_ids": new_signatures,
                "removed_signature_ids": retired_signatures,
            },
        }

    notes: list[str] = []
    if consumer_telemetry_path is None:
        notes.append("Consumer telemetry not located; ensure generate_fault_artifacts has been refreshed.")
    if consumer_manifest_path is None:
        notes.append("Consumer manifest missing; baseline comparison may be incomplete.")
    if producer_report_path is None:
        notes.append("Producer report unavailable; repeat offender counts may be stale.")

    artifacts_section = {
        "consumer_telemetry": _normalize_relative(consumer_telemetry_path, paths.repo_root),
        "consumer_manifest": _normalize_relative(consumer_manifest_path, paths.repo_root),
        "consumer_summary": _normalize_relative(consumer_summary_md_path, paths.repo_root),
        "producer_report": _normalize_relative(producer_report_path, paths.repo_root),
        "previous_bundle": _normalize_relative(previous_bundle_dir, paths.repo_root) if previous_bundle_dir else None,
    }

    overview_payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "generated_at": options.run_timestamp.isoformat(timespec="seconds"),
        "metrics": metrics,
        "severity_buckets": severity,
        "baseline": baseline_summary,
        "artifacts": artifacts_section,
        "producer_repeat_offender": _extract_producer_repeat_offender(
            producer_payload if isinstance(producer_payload, Mapping) else None
        ),
        "notes": notes,
    }

    summary_markdown = _build_markdown(
        generated_at=options.run_timestamp,
        metrics=metrics,
        severity=severity,
        baseline=baseline_summary,
        notes=notes,
    )

    artifacts = [
        ReportArtifact(filename=f"{SUMMARY_STEM}.json", kind="json", content=lambda: overview_payload),
        ReportArtifact(filename=f"{SUMMARY_STEM}.md", kind="text", content=lambda: summary_markdown),
    ]
    result: WriteReportArtifactsResult = write_report_artifacts(
        stem=SUMMARY_STEM,
        timestamp=options.run_timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    logger.info(
        "Fault Diagnostics overview artifacts written to %s (slug=%s)",
        result.run_dir,
        result.slug,
    )

    return {
        "status": "ok",
        "run_dir": str(result.run_dir),
        "slug": result.slug,
        "artifacts": {name: str(path) for name, path in result.artifacts.items()},
    }


def main(argv: Iterable[str] | None = None) -> None:
    raise SystemExit(0 if run(argv).get("status") == "ok" else 1)


__all__ = ["run", "main", "build_paths", "build_options"]
