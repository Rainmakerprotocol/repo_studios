#!/usr/bin/env python3
"""Repo Studios inventory validator.

Loads inventory YAML entries under `.repo_studios/inventory_schema/` and enforces
schema rules defined in `inventory_schema_spec.md` and `enums.yaml`.

Exit codes:
- 0: validation passed with no errors (warnings allowed)
- 1: validation failed (schema violations)
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "inventory_schema"
ENUMS_PATH = SCHEMA_ROOT / "enums.yaml"
TEMPLATE_PATH = SCHEMA_ROOT / "inventory_entry_template.yaml"
CONFIG_PATH = SCHEMA_ROOT / "validator_config.yaml"


class ValidationError(Exception):
    pass


@dataclass
class ValidationIssue:
    level: str
    file: Path
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "file": str(self.file.relative_to(ROOT)),
            "message": self.message,
            "context": self.context,
        }


@dataclass
class ValidationReport:
    issues: List[ValidationIssue] = field(default_factory=list)

    def add(self, level: str, file: Path, message: str, **context: Any) -> None:
        self.issues.append(ValidationIssue(level=level, file=file, message=message, context=context))

    @property
    def errors(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [issue for issue in self.issues if issue.level == "warning"]

    def to_json(self) -> str:
        return json.dumps({"issues": [issue.to_dict() for issue in self.issues]}, indent=2)


REQUIRED_FIELDS = {
    "id",
    "name",
    "path",
    "asset_kind",
    "roles",
    "maturity",
    "description",
    "consumers",
    "status",
    "artifact_type",
}

LIST_FIELDS = {
    "roles",
    "consumers",
    "governance_flags",
    "related_assets",
    "tags",
}


@dataclass
class EnumRegistry:
    enums: Dict[str, Sequence[str]]

    @classmethod
    def load(cls) -> "EnumRegistry":
        with ENUMS_PATH.open("r", encoding="utf-8") as fh:
            enums = yaml.safe_load(fh) or {}
        enums.setdefault("status", ["active", "needs_review", "archived"])
        return cls(enums=enums)

    def ensure(self, enum_name: str, values: Iterable[str], report: ValidationReport, file: Path, record_id: str) -> None:
        allowed = set(self.enums.get(enum_name, []))
        for value in values:
            if value not in allowed:
                report.add(
                    "error",
                    file,
                    f"Value '{value}' is not allowed for enum '{enum_name}'",
                    record_id=record_id,
                    enum=enum_name,
                )


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or []


def iterate_inventory_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.yaml")):
        if path.name in {ENUMS_PATH.name, TEMPLATE_PATH.name, CONFIG_PATH.name}:
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts
        if "views" in relative_parts:
            continue
        yield path


@dataclass
class ValidatorConfig:
    ignore_path_prefixes: Sequence[str] = ()
    suppress_ids: Sequence[str] = ()
    suppress_paths: Sequence[str] = ()

    @classmethod
    def load(cls, path: Path) -> "ValidatorConfig":
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        path_conf = data.get("path_existence", {})
        return cls(
            ignore_path_prefixes=tuple(path_conf.get("ignore_prefixes", [])),
            suppress_ids=tuple(path_conf.get("suppress_ids", [])),
            suppress_paths=tuple(path_conf.get("suppress_paths", [])),
        )

    def is_suppressed(self, record_id: str | None, path_value: str) -> bool:
        if record_id and record_id in self.suppress_ids:
            return True
        if path_value in self.suppress_paths:
            return True
        return any(path_value.startswith(prefix) for prefix in self.ignore_path_prefixes)


def _resolve_candidate_paths(path_value: str, schema_root: Path) -> List[Path]:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return [candidate]
    candidates = [ROOT / candidate]
    # allow relative paths during testing where schema root is temporary
    candidates.append(schema_root.parent / candidate)
    # Some inventory entries reference workspace-relative paths such as `.repo_studios/...`
    # so ensure the repository root is considered when resolving existence.
    if schema_root.parent.parent.exists():
        candidates.append(schema_root.parent.parent / candidate)
    return candidates


def _check_required_fields(record: Dict[str, Any], file: Path, report: ValidationReport) -> None:
    record_id = record.get("id") or "<unknown>"
    missing = REQUIRED_FIELDS - set(record.keys())
    if missing:
        report.add("error", file, f"Missing required fields: {sorted(missing)}", record_id=record_id)


def _check_list_fields(record: Dict[str, Any], file: Path, report: ValidationReport) -> None:
    record_id = record.get("id")
    for field in LIST_FIELDS:
        if field in record and not isinstance(record[field], list):
            report.add("error", file, f"Field '{field}' must be a list", record_id=record_id)


def _check_enums(record: Dict[str, Any], file: Path, registry: EnumRegistry, report: ValidationReport) -> None:
    record_id = record.get("id")
    enum_map = {
        "asset_kind": [record.get("asset_kind")],
        "maturity": [record.get("maturity")],
        "status": [record.get("status")],
    }
    for enum_name, values in enum_map.items():
        if values[0] is not None:
            registry.ensure(enum_name, values, report, file, record_id)

    if "roles" in record:
        registry.ensure("roles", record["roles"], report, file, record_id)
    if "consumers" in record:
        registry.ensure("consumers", record["consumers"], report, file, record_id)


def _check_dependencies(record: Dict[str, Any], file: Path, report: ValidationReport) -> None:
    record_id = record.get("id")
    deps = record.get("dependencies")
    if deps is None:
        return
    if not isinstance(deps, dict):
        report.add("error", file, "'dependencies' must be a mapping", record_id=record_id)
        return

    for key in ("internal_paths", "external_tools"):
        if key in deps and not isinstance(deps[key], list):
            report.add("error", file, f"'dependencies.{key}' must be a list", record_id=record_id)

    inputs = deps.get("inputs")
    if inputs is None:
        return
    if not isinstance(inputs, list):
        report.add("error", file, "'dependencies.inputs' must be a list", record_id=record_id)
        return
    for item in inputs:
        if not isinstance(item, dict) or "path" not in item:
            report.add(
                "error",
                file,
                "Each 'dependencies.inputs' entry must be a mapping with a 'path' key",
                record_id=record_id,
            )


def _check_paths(
    record: Dict[str, Any],
    file: Path,
    report: ValidationReport,
    config: ValidatorConfig,
    schema_root: Path,
) -> None:
    record_id = record.get("id")
    path_value = record.get("path")
    if path_value is None:
        return
    if not isinstance(path_value, str):
        report.add("error", file, "Field 'path' must be a string", record_id=record_id)
        return
    if config.is_suppressed(record_id, path_value):
        return

    for candidate in _resolve_candidate_paths(path_value, schema_root):
        if candidate.exists():
            return

    report.add(
        "error",
        file,
        f"Referenced path does not exist: {path_value}",
        record_id=record_id,
    )


def validate_record(
    record: Dict[str, Any],
    file: Path,
    registry: EnumRegistry,
    report: ValidationReport,
    config: ValidatorConfig,
    schema_root: Path,
) -> None:
    _check_required_fields(record, file, report)
    _check_list_fields(record, file, report)
    _check_enums(record, file, registry, report)
    _check_dependencies(record, file, report)
    _check_paths(record, file, report, config, schema_root)


def validate_file(
    path: Path,
    registry: EnumRegistry,
    report: ValidationReport,
    seen_ids: Dict[str, Path],
    config: ValidatorConfig,
    schema_root: Path,
) -> None:
    data = load_yaml(path)
    if not isinstance(data, list):
        report.add("error", path, "Top-level structure must be a list of records", record_id="<file>")
        return

    for record in data:
        if not isinstance(record, dict):
            report.add("error", path, "Each record must be a mapping", record_id=str(record))
            continue
        record_id = record.get("id")
        if not record_id:
            report.add("error", path, "Record missing 'id'", record_id="<unknown>")
        else:
            if record_id in seen_ids:
                report.add(
                    "error",
                    path,
                    "Duplicate id detected",
                    record_id=record_id,
                    first_occurrence=str(seen_ids[record_id].relative_to(ROOT)),
                )
            else:
                seen_ids[record_id] = path

    validate_record(record, path, registry, report, config, schema_root)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Repo Studios inventory YAML")
    parser.add_argument("--schema-root", default=str(SCHEMA_ROOT), help="Path to inventory schema directory")
    parser.add_argument(
        "--config-path",
        default=str(CONFIG_PATH),
        help="Optional validator configuration file (YAML)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON report")
    args = parser.parse_args(argv)

    schema_root = Path(args.schema_root).resolve()
    if not schema_root.exists():
        raise ValidationError(f"Schema root not found: {schema_root}")

    config_path = Path(args.config_path).resolve()
    config = ValidatorConfig.load(config_path)

    registry = EnumRegistry.load()
    report = ValidationReport()
    seen_ids: Dict[str, Path] = {}

    for file in iterate_inventory_files(schema_root):
        validate_file(file, registry, report, seen_ids, config, schema_root)

    if args.json:
        print(report.to_json())
    else:
        for issue in report.issues:
            rel = issue.file.relative_to(ROOT)
            print(f"[{issue.level.upper()}] {rel}: {issue.message}")

        if not report.issues:
            print("Inventory validation passed with no issues.")
        else:
            print(
                f"Inventory validation completed with {len(report.errors)} error(s) and {len(report.warnings)} warning(s)."
            )

    return 0 if not report.errors else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
