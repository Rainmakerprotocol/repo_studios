#!/usr/bin/env python3
"""Generate companion analysis insights from an existing function inventory."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

try:
    from libraries import (  # noqa: E402
        ReportArtifact,
        WriteReportArtifactsResult,
        resolve_repo_root,
        slugify_relative,
        write_report_artifacts,
    )
    from libraries.retention_policy import get_keep  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover - CLI fallback
    script_dir = Path(__file__).resolve().parent
    scripts_root = script_dir.parent
    repo_studios_root = scripts_root.parents[1]
    for candidate in (repo_studios_root, scripts_root):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    from libraries import (  # noqa: E402
        ReportArtifact,
        WriteReportArtifactsResult,
        resolve_repo_root,
        slugify_relative,
        write_report_artifacts,
    )
    from libraries.retention_policy import get_keep  # noqa: E402

DEFAULT_SCHEMA_VERSION = 1
ANALYSIS_VERSION = "1.0.0"
DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
DEFAULT_KEEP_RUNS = get_keep("generate_function_analysis")
VIEWER_SLUG = "commandview"
TOPIC_SLUG = "function_analysis"


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path
    target_relative: Path
    output_dir: Path
    target_slug: str
    target_index_dir: Path


@dataclass(frozen=True)
class Options:
    schema_version: int
    log_level: str
    inventory_file: Path | None


@dataclass(frozen=True)
class RunArtifacts:
    """Locations of the emitted analysis artifacts."""

    slug: str
    viewer_analysis: Path
    index_analysis: Path


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_function_analysis",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "target",
        help="Directory whose inventory should be analyzed. Relative paths resolve within the repo root.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root (auto-discovered via .repo_studios marker when omitted).",
    )
    parser.add_argument(
        "--reports-root",
        help=(
            "Optional base directory for viewer/topic analysis artifacts. Defaults to "
            f"{DEFAULT_OUTPUT_DIR} within the repo root."
        ),
    )
    parser.add_argument(
        "--schema-version",
        type=int,
        default=DEFAULT_SCHEMA_VERSION,
        help="Schema version to use for the analysis output.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    parser.add_argument(
        "--inventory-file",
        help="Optional explicit path to the inventory JSON to analyze.",
    )
    return parser.parse_args(argv)


_slugify_relative = slugify_relative


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    target_candidate = Path(args.target)
    target = target_candidate if target_candidate.is_absolute() else (repo_root / target_candidate)
    target = target.resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Target path must reside within repo root: {target}") from exc
    target_relative = target.relative_to(repo_root)
    if getattr(args, "reports_root", None):
        reports_candidate = Path(args.reports_root)
        output_dir = reports_candidate if reports_candidate.is_absolute() else repo_root / reports_candidate
    else:
        output_dir = repo_root / DEFAULT_OUTPUT_DIR
    output_dir = output_dir.resolve()
    try:
        output_dir.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Reports root must reside within repo root: {output_dir}") from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    target_index_dir = target / f"{target.name}_index"
    target_index_dir.mkdir(parents=True, exist_ok=True)
    target_slug = slugify_relative(target_relative)
    return Paths(
        repo_root=repo_root,
        target=target,
        target_relative=target_relative,
        output_dir=output_dir,
        target_slug=target_slug,
        target_index_dir=target_index_dir,
    )


def build_options(args: argparse.Namespace) -> Options:
    inventory_file = Path(args.inventory_file).resolve() if args.inventory_file else None
    return Options(schema_version=int(args.schema_version), log_level=args.log_level, inventory_file=inventory_file)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def locate_inventory_file(paths: Paths, options: Options) -> Path:
    if options.inventory_file:
        if not options.inventory_file.exists():
            raise FileNotFoundError(f"Inventory file not found: {options.inventory_file}")
        return options.inventory_file
    index_dir = paths.target_index_dir
    if not index_dir.exists():
        raise FileNotFoundError(f"Inventory directory not found: {index_dir}")
    candidates = sorted(
        path for path in index_dir.glob(f"{paths.target.name}_commandview_*.json") if "_screening_" not in path.name
    )
    if not candidates:
        raise FileNotFoundError(f"No inventory JSON files found in {index_dir}")
    return candidates[-1]


def read_inventory(inventory_path: Path) -> tuple[dict[str, Any], str]:
    content = inventory_path.read_text(encoding="utf-8")
    payload = json.loads(content)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return payload, digest


def collect_functions(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def _append(entry: dict[str, Any], module_meta: dict[str, Any]) -> None:
        rel_path = module_meta["relative_path"]
        module_id = module_meta["module_id"]
        qualified_name = entry.get("qualified_name")
        if not qualified_name and module_id:
            qualified_name = f"{module_id}::{entry.get('name')}"
        results.append(
            {
                "name": entry.get("name"),
                "docstring": entry.get("docstring"),
                "line": entry.get("line", 0),
                "path": rel_path,
                "signature": entry.get("signature"),
                "line_count": entry.get("line_count"),
                "hash": entry.get("hash"),
                "qualified_name": qualified_name,
                "module_id": module_id,
                "returns_kind": entry.get("returns_kind"),
                "todo_tags": entry.get("todo_tags", 0),
                "io_effects": entry.get("io_effects", {}),
                "logging_calls": entry.get("logging_calls", []),
                "calls": entry.get("calls", []),
            }
        )

    for module in inventory.get("files", []):
        module_meta = {
            "relative_path": module.get("relative_path") or module.get("path"),
            "module_id": module.get("module_id"),
        }
        for func in module.get("functions", []):
            _append(func, module_meta)
        for cls in module.get("classes", []):
            for method in cls.get("methods", []):
                _append(method, module_meta)
    return results


def identify_duplicate_groups(functions: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    buckets: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for item in functions:
        signature = item.get("signature") or item.get("name")
        if not signature:
            continue
        doc_key = (item.get("docstring") or "").strip()
        returns_kind = item.get("returns_kind") or ""
        key = (signature.strip(), doc_key, returns_kind)
        buckets.setdefault(key, []).append(item)
    return [group for group in buckets.values() if len(group) > 1]


def slugify(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-") or "unknown"


def build_findings(duplicate_groups: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for group in duplicate_groups:
        name = group[0].get("name", "<unknown>")
        signature = group[0].get("signature") or name
        doc = group[0].get("docstring") or ""
        slug = slugify(f"duplicate-{signature}")
        targets = [f"{item.get('path')}:{item.get('line')}" for item in group]
        findings.append(
            {
                "id": f"duplicate_function::{slug}",
                "kind": "duplicate_function",
                "severity": "medium",
                "summary": f"{len(group)} functions share the signature '{signature}'",
                "details": {
                    "function_name": name,
                    "signature": signature,
                    "shared_docstring": doc,
                    "line_counts": [item.get("line_count") for item in group],
                    "qualified_names": [item.get("qualified_name") for item in group],
                    "hash": group[0].get("hash"),
                },
                "instances": group,
                "metrics": {
                    "duplicate_count": len(group),
                    "todo_tags": sum(int(item.get("todo_tags", 0) or 0) for item in group),
                },
                "action_items": [
                    {
                        "type": "review_duplicate_function",
                        "description": "Review duplicate implementations for consolidation or reuse.",
                        "targets": targets,
                    }
                ],
            }
        )
    return findings


def compose_payload(
    paths: Paths,
    options: Options,
    inventory_path: Path,
    inventory_payload: dict[str, Any],
    inventory_hash: str,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    metadata = inventory_payload.get("metadata", {})
    generated_at = datetime.now(timezone.utc).isoformat()
    total_functions = sum(len(finding.get("instances", [])) for finding in findings)
    summary = {
        "duplicate_groups": len(findings),
        "total_duplicate_functions": total_functions,
        "total_files_scanned": len(inventory_payload.get("files", [])),
    }
    payload: dict[str, Any] = {
        "schema_version": options.schema_version,
        "metadata": {
            "analysis_version": ANALYSIS_VERSION,
            "generated_at": generated_at,
            "folder_path": str(paths.target),
            "folder_name": paths.target.name,
            "repo_root": str(paths.repo_root),
            "source_index_file": str(inventory_path),
            "source_index_generated_at": metadata.get("generated_at"),
            "source_index_hash": inventory_hash,
        },
        "summary": summary,
        "findings": findings,
    }
    return payload


def _write_index_artifact(*, paths: Paths, payload: dict[str, Any], slug: str) -> Path:
    filename = f"{paths.target.name}_analysis-{slug}.json"
    legacy = paths.target_index_dir / f"{paths.target.name}_analysis.json"
    if legacy.exists():
        legacy.unlink()
    destination = paths.target_index_dir / filename
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def _prune_index_artifacts(paths: Paths, *, keep: int) -> None:
    keep = max(keep, 1)
    pattern = f"{paths.target.name}_analysis-*.json"
    candidates = sorted(paths.target_index_dir.glob(pattern), key=lambda item: item.name, reverse=True)
    for stale in candidates[keep:]:
        try:
            stale.unlink()
        except FileNotFoundError:
            continue


def write_analysis(
    paths: Paths,
    payload: dict[str, Any],
    *,
    timestamp: datetime | None = None,
    keep: int = DEFAULT_KEEP_RUNS,
) -> RunArtifacts:
    moment = timestamp or datetime.now(timezone.utc)
    analysis_filename = f"{paths.target.name}_analysis.json"

    def _write_analysis(run_dir: Path) -> Path:
        target = run_dir / analysis_filename
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    report_result: WriteReportArtifactsResult = write_report_artifacts(
        stem=f"{paths.target_slug}_function_analysis",
        timestamp=moment,
        output_dir=paths.output_dir,
        artifacts=[ReportArtifact(filename=analysis_filename, writer=_write_analysis)],
        keep=max(keep, 1),
        viewer=VIEWER_SLUG,
        topic=TOPIC_SLUG,
    )

    index_artifact = _write_index_artifact(paths=paths, payload=payload, slug=report_result.slug)
    _prune_index_artifacts(paths=paths, keep=keep)

    return RunArtifacts(
        slug=report_result.slug,
        viewer_analysis=report_result.artifacts[analysis_filename],
        index_analysis=index_artifact,
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging(options.log_level)
    try:
        paths = build_paths(args)
    except ValueError as exc:
        logging.error("%s", exc)
        return 1
    if not paths.target.exists():
        logging.error("Target does not exist: %s", paths.target)
        return 1
    if not paths.target.is_dir():
        logging.error("Target is not a directory: %s", paths.target)
        return 1
    try:
        inventory_path = locate_inventory_file(paths, options)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1
    try:
        inventory_payload, inventory_hash = read_inventory(inventory_path)
    except (OSError, json.JSONDecodeError) as exc:
        logging.error("Failed to read inventory %s: %s", inventory_path, exc)
        return 1
    functions = collect_functions(inventory_payload)
    duplicate_groups = identify_duplicate_groups(functions)
    findings = build_findings(duplicate_groups)
    analysis_payload = compose_payload(paths, options, inventory_path, inventory_payload, inventory_hash, findings)
    artifacts = write_analysis(paths, analysis_payload)
    logging.info(
        "Analysis generated: viewer=%s index=%s duplicate_groups=%d duplicates=%d",
        artifacts.viewer_analysis,
        artifacts.index_analysis,
        len(findings),
        sum(len(group) for group in duplicate_groups),
    )
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
