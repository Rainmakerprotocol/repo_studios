#!/usr/bin/env python3
"""Audit helper adoption across Repo Studios command center scripts."""

from __future__ import annotations

import argparse
import ast
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import yaml

try:
    from libraries import (
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running as script
    LIBRARIES_ROOT = Path(__file__).resolve().parents[1]
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore  # noqa: E402
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        write_report_artifacts,
    )

DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports/helper_adoption")
DEFAULT_ALLOW_LIST = Path(".repo_studios/command_center/docs/guardrails/allowed_targets.yaml")
DEFAULT_HELPERS: tuple[str, ...] = (
    "slugify_relative",
    "copy_latest_artifact",
    "write_report_artifacts",
    "build_standard_paths",
    "build_standard_options",
)
RUN_STEM = "helper_adoption"
JSON_FILENAME = "helper_adoption.json"
JSON_POINTER = "latest_helper_adoption.json"
MARKDOWN_FILENAME = "helper_adoption.md"
MARKDOWN_POINTER = "latest_helper_adoption.md"
DEFAULT_KEEP = 3
DEFAULT_SCHEMA_VERSION = "1.0"
STATUSES: tuple[str, ...] = ("adopted", "legacy", "not_applicable")
LEGACY_NAMES: dict[str, frozenset[str]] = {
    "slugify_relative": frozenset({"_slugify_relative"}),
    "copy_latest_artifact": frozenset({"_copy_latest"}),
    "write_report_artifacts": frozenset({"write_report_artifacts", "write_artifacts"}),
    "build_standard_paths": frozenset({"build_paths"}),
    "build_standard_options": frozenset({"build_options"}),
}


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int


@dataclass(frozen=True)
class TargetScope:
    slug: str
    root: Path
    configured_path: str


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True),
    },
    repo_root_depth=5,
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
    except ValueError as exc:
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric, format="%(levelname)s: %(message)s")


def _resolve_helpers(raw_values: Sequence[str] | None) -> list[str]:
    if not raw_values:
        return list(DEFAULT_HELPERS)
    resolved: list[str] = []
    for entry in raw_values:
        for part in entry.split(","):
            name = part.strip()
            if not name or name in resolved:
                continue
            resolved.append(name)
    if not resolved:
        raise SystemExit("At least one helper name must be provided")
    return resolved


def _resolve_formats(raw_values: Sequence[str] | None) -> list[str]:
    if not raw_values:
        return ["json", "markdown"]
    selected: list[str] = []
    for entry in raw_values:
        value = entry.strip().lower()
        if value == "all":
            for option in ("json", "markdown"):
                if option not in selected:
                    selected.append(option)
            continue
        if value not in {"json", "markdown"}:
            raise SystemExit(f"Unsupported format: {entry}")
        if value not in selected:
            selected.append(value)
    if not selected:
        raise SystemExit("At least one output format must be selected")
    return selected


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _collect_python_files(root: Path) -> Iterable[Path]:
    for candidate in root.rglob("*.py"):
        if "__pycache__" in candidate.parts:
            continue
        if candidate.is_file():
            yield candidate


def _collect_imported_helpers(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "libraries":
            for alias in node.names:
                names.add(alias.name)
    return names


def _collect_defined_helpers(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
    return names


def _determine_status(helper: str, imported: set[str], defined: set[str]) -> str:
    if helper in imported:
        return "adopted"
    legacy_names = LEGACY_NAMES.get(helper, frozenset())
    if legacy_names.intersection(defined):
        return "legacy"
    return "not_applicable"


def _load_allow_list(repo_root: Path, override: str | None) -> tuple[TargetScope, ...]:
    config_path = Path(override) if override else DEFAULT_ALLOW_LIST
    if not config_path.is_absolute():
        config_path = (repo_root / config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Allow-list file not found: {config_path}")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    targets = data.get("targets", [])
    if not isinstance(targets, list) or not targets:
        raise ValueError("Allow-list must define a non-empty 'targets' list")
    scopes: list[TargetScope] = []
    for entry in targets:
        if not isinstance(entry, dict):
            raise ValueError("Allow-list entries must be objects")
        slug = entry.get("slug")
        path_value = entry.get("path")
        if not slug or not path_value:
            raise ValueError("Each allow-list entry requires 'slug' and 'path'")
        candidate = Path(path_value)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError(f"Allow-list path for slug {slug!r} must reside within repo") from exc
        if not candidate.exists() or not candidate.is_dir():
            raise ValueError(f"Allow-list path for slug {slug!r} is not a directory: {candidate}")
        scopes.append(TargetScope(slug=slug, root=candidate, configured_path=str(entry.get("path"))))
    return tuple(scopes)


def _initialize_helper_map(helpers: Sequence[str], scopes: Sequence[TargetScope]) -> dict[str, dict[str, object]]:
    structure: dict[str, dict[str, object]] = {}
    for helper in helpers:
        target_payload = {
            scope.slug: {
                "status": {status: 0 for status in STATUSES},
                "files": {"adopted": [], "legacy": []},
            }
            for scope in scopes
        }
        structure[helper] = {
            "summary": {status: 0 for status in STATUSES},
            "files": {"adopted": [], "legacy": []},
            "targets": target_payload,
        }
    return structure


def _scan_targets(
    repo_root: Path,
    helper_names: Sequence[str],
    scopes: Sequence[TargetScope],
) -> tuple[dict[str, dict[str, object]], dict[str, int]]:
    helper_map = _initialize_helper_map(helper_names, scopes)
    file_counts: dict[str, int] = {scope.slug: 0 for scope in scopes}
    for scope in scopes:
        for path in _collect_python_files(scope.root):
            file_counts[scope.slug] += 1
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            imported = _collect_imported_helpers(tree)
            defined = _collect_defined_helpers(tree)
            for helper in helper_names:
                status = _determine_status(helper, imported, defined)
                helper_payload = helper_map[helper]
                helper_payload["summary"][status] += 1  # type: ignore[index]
                target_payload = helper_payload["targets"][scope.slug]  # type: ignore[index]
                target_payload["status"][status] += 1  # type: ignore[index]
                if status in {"adopted", "legacy"}:
                    relative = _relative_path(path, repo_root)
                    helper_payload["files"][status].append(relative)  # type: ignore[index]
                    target_payload["files"][status].append(relative)  # type: ignore[index]
    return helper_map, file_counts


def _build_report(
    repo_root: Path,
    helper_names: Sequence[str],
    scopes: Sequence[TargetScope],
    schema_version: str,
    timestamp: datetime,
) -> dict[str, object]:
    helper_map, file_counts = _scan_targets(repo_root, helper_names, scopes)
    helper_entries: list[dict[str, object]] = []
    for helper in helper_names:
        payload = helper_map[helper]
        helper_entry: dict[str, object] = {
            "name": helper,
            "summary": payload["summary"],
            "files": {
                "adopted": sorted(payload["files"]["adopted"]),
                "legacy": sorted(payload["files"]["legacy"]),
            },
            "targets": [],
        }
        for scope in scopes:
            target_payload = payload["targets"][scope.slug]
            helper_entry["targets"].append(
                {
                    "slug": scope.slug,
                    "path": scope.configured_path,
                    "status": target_payload["status"],
                    "files": {
                        "adopted": sorted(target_payload["files"]["adopted"]),
                        "legacy": sorted(target_payload["files"]["legacy"]),
                    },
                }
            )
        helper_entries.append(helper_entry)
    return {
        "schema_version": schema_version,
        "generated_at": timestamp.isoformat(),
        "repo_root": str(repo_root),
        "helpers": helper_entries,
        "targets": [
            {
                "slug": scope.slug,
                "path": scope.configured_path,
                "files_scanned": file_counts[scope.slug],
            }
            for scope in scopes
        ],
    }


def _render_markdown(report: dict[str, object]) -> str:
    helpers = report.get("helpers", [])
    timestamp = report.get("generated_at", "")
    schema = report.get("schema_version", "")
    lines: list[str] = [
        "# Helper Adoption Summary",
        "",
        f"- generated_at: `{timestamp}`",
        f"- schema_version: `{schema}`",
        "",
        "| Helper | Target | Adopted | Legacy | Not Applicable |",
        "| --- | --- | --- | --- | --- |",
    ]
    for helper in helpers:
        name = helper["name"]
        for target in helper["targets"]:
            status = target["status"]
            lines.append(
                f"| `{name}` | {target['slug']} | {status['adopted']} | {status['legacy']} | {status['not_applicable']} |"
            )
    lines.append("")
    for helper in helpers:
        name = helper["name"]
        lines.append(f"## {name}")
        for target in helper["targets"]:
            adopted = target["files"]["adopted"]
            legacy = target["files"]["legacy"]
            lines.append(f"### {target['slug']}")
            if adopted:
                lines.append("Adopted:")
                for entry in adopted:
                    lines.append(f"- `{entry}`")
            if legacy:
                if adopted:
                    lines.append("")
                lines.append("Legacy:")
                for entry in legacy:
                    lines.append(f"- `{entry}`")
            if not adopted and not legacy:
                lines.append("No adoption signals detected.")
            lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root (defaults to ancestor traversal)")
    parser.add_argument("--output-dir", help="Directory for helper adoption reports")
    parser.add_argument("--keep", type=int, default=DEFAULT_KEEP, help="Number of historical runs to retain")
    parser.add_argument("--timestamp", help="ISO8601 timestamp for run directory naming (UTC if absent)")
    parser.add_argument("--schema-version", default=DEFAULT_SCHEMA_VERSION, help="Schema version for the JSON report")
    parser.add_argument("--helper", dest="helpers", action="append", help="Helper name to audit (repeatable)")
    parser.add_argument("--helpers", dest="helpers", action="append", help="Helper name to audit (repeatable)")
    parser.add_argument("--format", dest="formats", action="append", help="Report format: json, markdown, or all (repeatable)")
    parser.add_argument(
        "--allow-list",
        help="Path to allowed targets YAML (defaults to .repo_studios/command_center/docs/guardrails/allowed_targets.yaml)",
    )
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging verbosity")
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.log_level)
    try:
        paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    except ValueError as exc:
        logging.error("%s", exc)
        return 1
    opts = build_standard_options(args, OPTIONS_CONFIG)
    helper_names = _resolve_helpers(args.helpers)
    formats = _resolve_formats(args.formats)
    timestamp = _parse_timestamp(args.timestamp)
    try:
        scopes = _load_allow_list(paths.repo_root, args.allow_list)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("%s", exc)
        return 1
    if not scopes:
        logging.error("No targets available for audit")
        return 1
    report = _build_report(paths.repo_root, helper_names, scopes, args.schema_version, timestamp)
    artifacts: list[ReportArtifact] = []
    if "json" in formats:
        artifacts.append(
            ReportArtifact(
                filename=JSON_FILENAME,
                pointer=JSON_POINTER,
                kind="json",
                content=lambda payload=report: payload,
            )
        )
    if "markdown" in formats:
        markdown = _render_markdown(report)
        artifacts.append(
            ReportArtifact(
                filename=MARKDOWN_FILENAME,
                pointer=MARKDOWN_POINTER,
                kind="text",
                content=markdown,
            )
        )
    result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=timestamp,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=opts.artifacts_to_keep,
    )
    for helper in report["helpers"]:
        summary = helper["summary"]
        logging.info(
            "helper=%s adopted=%d legacy=%d not_applicable=%d",
            helper["name"],
            summary["adopted"],
            summary["legacy"],
            summary["not_applicable"],
        )
    logging.info("Helper adoption report written to %s", result.run_dir)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return run(argv)


__all__ = ["run", "main", "build_parser"]
