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


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path


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


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[3]
    target_candidate = Path(args.target)
    target = target_candidate if target_candidate.is_absolute() else (repo_root / target_candidate)
    target = target.resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Target path must reside within repo root: {target}") from exc
    return Paths(repo_root=repo_root, target=target)


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
    for entry in inventory.get("files", []):
        rel_path = entry.get("relative_path") or entry.get("path")
        for func in entry.get("functions", []):
            results.append(
                {
                    "name": func.get("name"),
                    "docstring": func.get("docstring"),
                    "line": func.get("line", 0),
                    "path": rel_path,
                    "signature": func.get("signature"),
                    "line_count": func.get("line_count"),
                }
            )
    return results


def identify_duplicate_groups(functions: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in functions:
        name = item.get("name")
        if not name:
            continue
        signature = item.get("signature") or name
        doc_key = item.get("docstring") or ""
        key = (signature.strip(), doc_key.strip())
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
                },
                "instances": group,
                "metrics": {
                    "duplicate_count": len(group),
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
    total_functions = sum(len(group) for group in findings)
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


def write_analysis(paths: Paths, inventory_path: Path, inventory_payload: dict[str, Any], payload: dict[str, Any]) -> Path:
    index_dir = inventory_path.parent
    target_stem = paths.target.name
    legacy = index_dir / f"{target_stem}_analysis.json"
    if legacy.exists():
        legacy.unlink()
    for existing in index_dir.glob(f"{target_stem}_analysis-*.json"):
        if existing.is_file():
            existing.unlink()
    date_stamp = analysis_date(inventory_path, inventory_payload)
    output_file = index_dir / f"{target_stem}_analysis-{date_stamp}.json"
    temp_file = output_file.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(output_file)
    return output_file


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
    output_file = write_analysis(paths, inventory_path, inventory_payload, analysis_payload)
    logging.info(
        "Analysis generated: path=%s duplicate_groups=%d duplicates=%d",
        output_file,
        len(findings),
        sum(len(group) for group in duplicate_groups),
    )
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
