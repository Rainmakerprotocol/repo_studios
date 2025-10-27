#!/usr/bin/env python3
"""Generate companion analysis insights from an existing function inventory."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_SCHEMA_VERSION = 1
ANALYSIS_VERSION = "1.0.0"
DEFAULT_REPORTS_ROOT_RELATIVE = Path(".repo_studios/command_center/reports/index_scan_analysis")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path
    target_relative: Path
    reports_root: Path


@dataclass(frozen=True)
class Options:
    schema_version: int
    log_level: str
    inventory_file: Path | None


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
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
        help="Repository root. Defaults to script's grandparent directory.",
    )
    parser.add_argument(
        "--reports-root",
        help=(
            "Optional directory for centralized analysis copies. Defaults to "
            ".repo_studios/command_center/reports/duplicates_scan within the repo root."
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


def _slugify_relative(relative_path: Path) -> str:
    parts: list[str] = []
    for part in relative_path.parts:
        slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in part)
        slug = slug.strip("-") or "segment"
        parts.append(slug)
    return "__".join(parts) or "root"


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
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
        reports_root = reports_candidate if reports_candidate.is_absolute() else repo_root / reports_candidate
    else:
        reports_root = repo_root / DEFAULT_REPORTS_ROOT_RELATIVE
    reports_root = reports_root.resolve()
    try:
        reports_root.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Reports root must reside within repo root: {reports_root}") from exc
    reports_root.mkdir(parents=True, exist_ok=True)
    return Paths(repo_root=repo_root, target=target, target_relative=target_relative, reports_root=reports_root)


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
    index_dir = paths.target / f"{paths.target.name}_index"
    if not index_dir.exists():
        raise FileNotFoundError(f"Inventory directory not found: {index_dir}")
    candidates = sorted(index_dir.glob(f"{paths.target.name}_index-*.json"))
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


def _write_analysis_copy(directory: Path, source_name: str, payload: dict[str, Any], date_stamp: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    legacy = directory / f"{source_name}_analysis.json"
    if legacy.exists():
        legacy.unlink()
    for existing in directory.glob(f"{source_name}_analysis-*.json"):
        if existing.is_file():
            existing.unlink()
    output_file = directory / f"{source_name}_analysis-{date_stamp}.json"
    temp_file = output_file.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(output_file)
    latest_pointer = directory / "latest.json"
    if latest_pointer.exists():
        latest_pointer.unlink()
    return output_file


def analysis_date(inventory_path: Path, inventory_payload: dict[str, Any]) -> str:
    stem = inventory_path.stem
    parts = stem.split("-")
    if parts and parts[-1].isdigit() and len(parts[-1]) == 8:
        return f"{parts[-1][:4]}-{parts[-1][4:6]}-{parts[-1][6:]}"
    if len(parts) >= 2:
        candidate = parts[-1]
        if len(candidate) == 10 and candidate[4] == "-" and candidate[7] == "-":
            return candidate
    generated_at = inventory_payload.get("metadata", {}).get("generated_at")
    if generated_at:
        try:
            return datetime.fromisoformat(generated_at).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def write_analysis(
    paths: Paths,
    inventory_path: Path,
    inventory_payload: dict[str, Any],
    payload: dict[str, Any],
) -> tuple[Path, Path]:
    index_dir = inventory_path.parent
    target_stem = paths.target.name
    date_stamp = analysis_date(inventory_path, inventory_payload)
    primary = _write_analysis_copy(index_dir, target_stem, payload, date_stamp)
    reports_slug = _slugify_relative(paths.target_relative)
    mirror_dir = paths.reports_root / f"{reports_slug}_analysis"
    mirror = _write_analysis_copy(mirror_dir, target_stem, payload, date_stamp)
    return primary, mirror


def run(argv: Iterable[str] | None = None) -> int:
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
    primary_file, mirror_file = write_analysis(paths, inventory_path, inventory_payload, analysis_payload)
    logging.info(
        "Analysis generated: primary=%s mirror=%s duplicate_groups=%d duplicates=%d",
        primary_file,
        mirror_file,
        len(findings),
        sum(len(group) for group in duplicate_groups),
    )
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
