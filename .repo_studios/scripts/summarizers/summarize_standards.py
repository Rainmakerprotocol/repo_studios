#!/usr/bin/env python3
"""Generate a Healthview-ready summary of the standards index."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence, cast

try:
    import yaml as yaml_module
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    YAML_IMPORT_ERROR: BaseException | None = exc
    yaml: Any | None = None
else:  # pragma: no cover - executed when import succeeds
    YAML_IMPORT_ERROR = None
    yaml = yaml_module

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - preferred import when executed with packaged path
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
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
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
    from libraries.retention_policy import get_keep

DEFAULT_INDEX_PATH = Path(".repo_studios/scripts/repo_standards_index.yaml")
LEGACY_INDEX_PATH = Path(".repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml")
DEFAULT_PENDING_PATH = Path(".repo_studios/scripts/repo_standards_pending.yaml")
DEFAULT_OUTPUT_DIR = build_topic_path("summarizer", "standards_overview")
SUMMARY_STEM = "standards_overview"
VIEWER_SLUG = "healthview"
TOPIC_SLUG = "standards_overview"
SCHEMA_VERSION = 1
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("summarize_standards")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    index_path: Path
    pending_path: Path
    output_dir: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "index_path": PathSpec(field="index_path", default=DEFAULT_INDEX_PATH, within_repo=False),
        "pending_path": PathSpec(field="pending_path", default=DEFAULT_PENDING_PATH, within_repo=False),
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=False),
    },
    repo_root_depth=5,
)


@dataclass(frozen=True)
class Options:
    label: str
    log_level: str
    artifacts_to_keep: int
    run_timestamp: datetime


@dataclass(frozen=True)
class KeepValues:
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepValues,
    keep_specs={"artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1)},
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--index-path",
        default=os.environ.get("INDEX_PATH", str(DEFAULT_INDEX_PATH)),
        help="Path to the standards index YAML",
    )
    parser.add_argument(
        "--pending-path",
        default=os.environ.get("PENDING_PATH", str(DEFAULT_PENDING_PATH)),
        help="Path to the pending rules YAML",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Root directory for Healthview artifact emission",
    )
    parser.add_argument("--label", default="summary", help="Label used in emitted metadata")
    parser.add_argument(
        "--timestamp",
        help="ISO-8601 timestamp for emitted artifacts (defaults to current UTC time)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Retention budget for Healthview runs",
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


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    artifacts_to_keep = max(int(getattr(keep_values, "artifacts_to_keep", DEFAULT_ARTIFACTS_TO_KEEP)), 1)
    return Options(
        label=str(args.label),
        log_level=str(args.log_level),
        artifacts_to_keep=artifacts_to_keep,
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
    )


def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _resolve_index_path(paths: Paths, options: Options) -> Path:
    candidate = paths.index_path
    if candidate.exists():
        return candidate
    legacy_candidate = (paths.repo_root / LEGACY_INDEX_PATH).resolve()
    if legacy_candidate.exists():
        logging.warning(
            "[standards-%s] index missing at %s; falling back to legacy snapshot %s",
            options.label,
            candidate,
            legacy_candidate,
        )
        return legacy_candidate
    return candidate


def _load_index_payload(path: Path) -> Mapping[str, Any] | None:
    if yaml is None or not path.exists():
        return None
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - defensive read
        return None
    return loaded if isinstance(loaded, Mapping) else None


def _count_pending_lines(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for _ in handle)
    except OSError:  # pragma: no cover - defensive
        return None


def _extract_markdown_rules(rules: Any) -> list[str]:
    if not isinstance(rules, list):
        return []
    collected: list[str] = []
    for entry in rules:
        if isinstance(entry, Mapping):
            rule_id = entry.get("id")
            category_ids = entry.get("category_ids")
            if isinstance(category_ids, list) and "markdown" in category_ids:
                if isinstance(rule_id, str):
                    collected.append(rule_id)
                continue
            if isinstance(rule_id, str) and (rule_id.startswith("markdown-") or rule_id.startswith("md-")):
                collected.append(rule_id)
    return sorted(set(collected))


def _build_markdown(
    *,
    generated_at: datetime,
    label: str,
    metrics: Mapping[str, Any],
    markdown_sample: list[str],
    pending_lines: int | None,
    notes: list[str],
) -> str:
    lines: list[str] = ["# Standards Overview", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append(f"Label: {label}")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append(f"- Rules: {metrics.get('rule_count', 0)}")
    lines.append(f"- Markdown rules: {metrics.get('markdown_rule_count', 0)}")
    lines.append(f"- Extracted count: {metrics.get('extracted_count')}")
    lines.append(f"- Auto accept: {metrics.get('auto_accept')}")
    lines.append(f"- Pending lines: {pending_lines if pending_lines is not None else 'unknown'}")
    lines.append("")
    if markdown_sample:
        lines.append("## Markdown Rule Sample")
        lines.append("")
        for rule in markdown_sample:
            lines.append(f"- {rule}")
        lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    if YAML_IMPORT_ERROR is not None:
        logging.warning("[standards-summary] missing PyYAML: %s", YAML_IMPORT_ERROR)
        return {"status": "skipped", "reason": "missing PyYAML"}

    args = _parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)
    logger = logging.getLogger("summarize_standards")

    repo_root = paths.repo_root
    index_path = _resolve_index_path(paths, options)
    pending_path = paths.pending_path
    run_slug = options.run_timestamp.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")
    timestamp_slug = options.run_timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d_%H%M")

    notes: list[str] = []
    index_payload = _load_index_payload(index_path)
    if index_payload is None:
        notes.append("Standards index not found or unreadable; metrics may be stale.")
        extraction: Mapping[str, Any] = {}
        rules: list[Any] = []
    else:
        metadata = index_payload.get("metadata")
        extraction_candidate = metadata.get("extraction") if isinstance(metadata, Mapping) else {}
        extraction = extraction_candidate or {}
        rules_raw = index_payload.get("rules")
        rules = rules_raw if isinstance(rules_raw, list) else []

    markdown_rules = _extract_markdown_rules(rules)
    markdown_sample = markdown_rules[:5]

    metrics = {
        "rule_count": len(rules),
        "markdown_rule_count": len(markdown_rules),
        "extracted_count": extraction.get("extracted_count") if isinstance(extraction, Mapping) else None,
        "auto_accept": extraction.get("auto_accept") if isinstance(extraction, Mapping) else None,
    }

    pending_lines = _count_pending_lines(pending_path)
    if pending_lines is None:
        notes.append("Pending file missing or unreadable; pending line count unavailable.")

    artifact_paths = {
        "index_yaml": _normalize_relative(index_path if index_path.exists() else None, repo_root),
        "pending_yaml": _normalize_relative(pending_path if pending_path.exists() else None, repo_root),
        "legacy_index_yaml": _normalize_relative(
            (repo_root / LEGACY_INDEX_PATH).resolve() if (repo_root / LEGACY_INDEX_PATH).exists() else None,
            repo_root,
        ),
    }

    summary_payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "generated_at": options.run_timestamp.isoformat(timespec="seconds"),
        "run_slug": run_slug,
        "timestamp_slug": timestamp_slug,
        "label": options.label,
        "metrics": metrics,
        "markdown_rule_sample": markdown_sample,
        "pending_lines": pending_lines,
        "artifacts": artifact_paths,
        "notes": notes,
    }

    summary_markdown = _build_markdown(
        generated_at=options.run_timestamp,
        label=options.label,
        metrics=metrics,
        markdown_sample=markdown_sample,
        pending_lines=pending_lines,
        notes=notes,
    )

    # Build telemetry payload for HOP base package compliance
    telemetry_payload = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "run_timestamp": options.run_timestamp.isoformat(timespec="seconds"),
        "metrics": metrics,
    }

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: summary_payload),
        ReportArtifact(filename="summary.md", kind="text", content=lambda: summary_markdown),
        ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
    ]
    result: WriteReportArtifactsResult = write_report_artifacts(
        stem=SUMMARY_STEM,
        timestamp=options.run_timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer="",
        topic="",
    )

    logger.info("Standards overview artifacts written to %s (slug=%s)", result.run_dir, result.slug)

    return {
        "status": "ok",
        "run_dir": str(result.run_dir),
        "slug": result.slug,
        "artifacts": {name: str(path) for name, path in result.artifacts.items()},
        "notes": notes,
    }


def main(argv: Sequence[str] | None = None) -> None:
    result = run(argv)
    status = result.get("status")
    exit_code = 0 if status in {"ok", "skipped"} else 1
    raise SystemExit(exit_code)




def summarize(label: str, index_path: Path, pending_path: Path) -> int:
    """Backward-compatible shim for legacy orchestrators expecting summarize()."""

    repo_root = Path(__file__).resolve().parents[3]
    argv = [
        "--repo-root",
        str(repo_root),
        "--index-path",
        str(index_path),
        "--pending-path",
        str(pending_path),
        "--label",
        str(label),
    ]
    result = run(argv)
    status = result.get("status")
    return 0 if status in {"ok", "skipped"} else 1


__all__ = ["run", "main", "summarize", "build_paths", "build_options", "_resolve_index_path", "Paths", "Options"]


if __name__ == "__main__":  # pragma: no cover
    main()
