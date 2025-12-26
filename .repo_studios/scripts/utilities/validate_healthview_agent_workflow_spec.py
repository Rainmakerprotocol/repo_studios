#!/usr/bin/env python3
"""Validate the HealthView agent workflow YAML spec.

This validates:
1) JSON Schema compliance
2) Minimal semantic invariants required for deterministic automation

It is intentionally conservative: if the spec is ambiguous, it should fail.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"
if str(LIBRARIES_ROOT) not in sys.path:
    sys.path.insert(0, str(LIBRARIES_ROOT))

from libraries.cli import resolve_repo_root  # type: ignore

LOG = logging.getLogger(__name__)
LOG.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()


def _configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(message)s", force=True)


def _default_schema_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "pipeline"
        / "healthview_orchestration_pipeline"
        / "workflows"
        / "schema"
        / "healthview_agent_execution_loop.schema.json"
    )


def _default_spec_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "pipeline"
        / "healthview_orchestration_pipeline"
        / "workflows"
        / "healthview_agent_execution_loop.v1.yaml"
    )


def load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Workflow spec must be a YAML mapping")
    return payload


def load_schema(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Workflow schema must be a JSON object")
    return payload


def validate_schema(spec: dict[str, Any], schema: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(spec), key=str):
        loc = "/".join(str(item) for item in err.path)
        prefix = f"{loc}: " if loc else ""
        errors.append(prefix + err.message)
    return tuple(errors)


def validate_semantics(spec: dict[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []

    if spec.get("version") != "1.0":
        errors.append('version must be "1.0"')

    selection = spec.get("selection")
    if not isinstance(selection, dict):
        errors.append("selection must be a mapping")
        return tuple(errors)

    if selection.get("source") != "checkbox_report_csv":
        errors.append('selection.source must be "checkbox_report_csv"')
    if selection.get("strict_stage_order") is not True:
        errors.append("selection.strict_stage_order must be true")

    inputs = spec.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("inputs must be a mapping")
        return tuple(errors)

    tier1_gate_files = inputs.get("tier1_gate_files")
    if not isinstance(tier1_gate_files, list) or not tier1_gate_files:
        errors.append("inputs.tier1_gate_files must be a non-empty list")

    mapping = spec.get("mapping")
    if not isinstance(mapping, dict):
        errors.append("mapping must be a mapping")
        return tuple(errors)

    if mapping.get("extract_tier2_link_from_checkbox_text") is not True:
        errors.append("mapping.extract_tier2_link_from_checkbox_text must be true")
    if mapping.get("require_link_anchor") is not True:
        errors.append("mapping.require_link_anchor must be true")

    doc_index_command = inputs.get("doc_index_command")
    if not isinstance(doc_index_command, list) or not doc_index_command:
        errors.append("inputs.doc_index_command must be a non-empty list")

    return tuple(errors)


def validate_workflow_spec(spec_path: Path, schema_path: Path | None = None) -> ValidationResult:
    schema_path = schema_path or _default_schema_path()
    errors: list[str] = []

    if not spec_path.exists():
        return ValidationResult(ok=False, errors=(f"spec not found: {spec_path}",))
    if not schema_path.exists():
        return ValidationResult(ok=False, errors=(f"schema not found: {schema_path}",))

    spec = load_yaml(spec_path)
    schema = load_schema(schema_path)

    errors.extend(validate_schema(spec, schema))
    errors.extend(validate_semantics(spec))

    return ValidationResult(ok=not errors, errors=tuple(errors))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the HealthView agent workflow spec")
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=_default_spec_path(),
        help="Path to workflow YAML spec",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Optional schema override (defaults to repo schema path)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.log_level)

    repo_root = resolve_repo_root(explicit=args.repo_root, origin=Path(__file__))
    spec_path = args.spec
    if not spec_path.is_absolute():
        spec_path = (repo_root / spec_path).resolve()
    schema_path = args.schema
    if schema_path is not None and not schema_path.is_absolute():
        schema_path = (repo_root / schema_path).resolve()

    result = validate_workflow_spec(spec_path, schema_path)
    if result.ok:
        LOG.info("OK: workflow spec valid: %s", spec_path.as_posix())
        return 0

    LOG.error("Workflow spec validation failed (%d issue(s)):", len(result.errors))
    for item in result.errors:
        LOG.error("- %s", item)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
