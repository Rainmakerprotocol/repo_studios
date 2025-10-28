#!/usr/bin/env python3
"""Validate Repo Studios inventory entries and emit structured artifacts."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import yaml

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA_ROOT = Path(".repo_studios/inventory_schema")
DEFAULT_ENUMS_PATH = DEFAULT_SCHEMA_ROOT / "enums.yaml"
DEFAULT_TEMPLATE_PATH = DEFAULT_SCHEMA_ROOT / "inventory_entry_template.yaml"
DEFAULT_CONFIG_PATH = DEFAULT_SCHEMA_ROOT / "validator_config.yaml"
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/validate_inventory")
RUN_PREFIX = "validate_inventory"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1

LIBRARIES_ROOT = DEFAULT_REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import copy_latest_artifact
except ModuleNotFoundError:  # pragma: no cover - fallback when executed as script
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import copy_latest_artifact

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


class ValidationError(Exception):
    """Raised when the validator cannot run due to configuration issues."""


@dataclass
class ValidationIssue:
    level: str
    file: Path
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, repo_root: Path) -> Dict[str, Any]:
        try:
            relative = self.file.relative_to(repo_root)
        except ValueError:
            relative = self.file
        return {
            "level": self.level,
            "file": str(relative).replace("\\", "/"),
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

    def to_json(self, repo_root: Path) -> str:
        return json.dumps({"issues": [issue.to_dict(repo_root) for issue in self.issues]}, indent=2)


@dataclass
class ValidationStats:
    files_checked: int = 0
    records_checked: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "files_checked": self.files_checked,
            "records_checked": self.records_checked,
        }


@dataclass
class EnumRegistry:
    enums: Dict[str, Sequence[str]]

    @classmethod
    def load(cls, enums_path: Path) -> "EnumRegistry":
        if not enums_path.exists():
            raise ValidationError(f"Enums file not found: {enums_path}")
        with enums_path.open("r", encoding="utf-8") as handle:
            enums = yaml.safe_load(handle) or {}
        enums.setdefault("status", ["active", "needs_review", "archived"])
        return cls(enums=enums)

    def ensure(
        self,
        enum_name: str,
        values: Iterable[str],
        report: ValidationReport,
        file: Path,
        record_id: str | None,
    ) -> None:
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


@dataclass
class ValidatorConfig:
    ignore_path_prefixes: Sequence[str] = ()
    suppress_ids: Sequence[str] = ()
    suppress_paths: Sequence[str] = ()
    path_checks_enabled: bool = False

    @classmethod
    def load(cls, path: Path) -> "ValidatorConfig":
        if not path.exists():
            return cls()
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        path_conf = data.get("path_existence")
        if path_conf is None:
            path_conf = {}
            enabled = False
        else:
            enabled_raw = path_conf.get("enabled")
            enabled = bool(enabled_raw) if enabled_raw is not None else True
        return cls(
            ignore_path_prefixes=tuple(path_conf.get("ignore_prefixes", [])),
            suppress_ids=tuple(path_conf.get("suppress_ids", [])),
            suppress_paths=tuple(path_conf.get("suppress_paths", [])),
            path_checks_enabled=enabled,
        )

    def is_suppressed(self, record_id: str | None, path_value: str) -> bool:
        if record_id and record_id in self.suppress_ids:
            return True
        if path_value in self.suppress_paths:
            return True
        return any(path_value.startswith(prefix) for prefix in self.ignore_path_prefixes)


def _current_time() -> datetime:
    return datetime.now(timezone.utc)


def _format_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d_%H%M%S")


def _sanitize_slug(slug: str) -> str:
    return slug.replace("/", "_").replace("\\", "_")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _prepare_run_dir(output_dir: Path, slug: str) -> Path:
    run_dir = output_dir / f"{RUN_PREFIX}-{_sanitize_slug(slug)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    runs = [node for node in output_dir.iterdir() if node.is_dir() and node.name.startswith(f"{RUN_PREFIX}-")]
    runs.sort(key=lambda node: node.name, reverse=True)
    for index, node in enumerate(runs):
        if index < keep or node == current_run:
            continue
        for child in node.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
        node.rmdir()


_copy_latest = copy_latest_artifact


def update_latest_artifacts(run_dir: Path, output_dir: Path) -> None:
    mapping = {
        "latest_report.json": run_dir / "report.json",
        "latest_report.md": run_dir / "report.md",
        "latest_report.log": run_dir / "log.txt",
        "latest_raw.json": run_dir / "raw.json",
    }
    for filename, src in mapping.items():
        _copy_latest(src, output_dir / filename)


def _resolve_candidate_paths(path_value: str, repo_root: Path, schema_root: Path) -> List[Path]:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return [candidate]
    return [
        repo_root / candidate,
        schema_root.parent / candidate,
        repo_root / ".repo_studios" / candidate,
    ]


def _load_inventory_data(path: Path, report: ValidationReport) -> List[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or []
    except yaml.YAMLError as exc:
        report.add("error", path, f"YAML parse failure: {exc}")
        return []
    if not isinstance(data, list):
        report.add("error", path, "Top-level structure must be a list of records", record_id="<file>")
        return []
    return data


def iterate_inventory_files(
    schema_root: Path,
    *,
    enums_path: Path,
    template_path: Path,
    config_path: Path,
) -> Iterable[Path]:
    skip_files = {enums_path.resolve(), template_path.resolve(), config_path.resolve()}
    for candidate in sorted(schema_root.rglob("*.yaml")):
        if candidate.resolve() in skip_files:
            continue
        try:
            parts = candidate.relative_to(schema_root).parts
        except ValueError:
            parts = candidate.parts
        if "views" in parts:
            continue
        yield candidate


def _check_required_fields(record: Dict[str, Any], file: Path, report: ValidationReport) -> None:
    record_id = record.get("id") or "<unknown>"
    missing = REQUIRED_FIELDS - set(record.keys())
    if missing:
        report.add("error", file, f"Missing required fields: {sorted(missing)}", record_id=record_id)


def _check_list_fields(record: Dict[str, Any], file: Path, report: ValidationReport) -> None:
    record_id = record.get("id")
    for list_field in LIST_FIELDS:
        if list_field in record and not isinstance(record[list_field], list):
            report.add("error", file, f"Field '{list_field}' must be a list", record_id=record_id)


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
    repo_root: Path,
    schema_root: Path,
) -> None:
    if not config.path_checks_enabled:
        return
    record_id = record.get("id")
    path_value = record.get("path")
    if path_value is None:
        return
    if not isinstance(path_value, str):
        report.add("error", file, "Field 'path' must be a string", record_id=record_id)
        return
    if config.is_suppressed(record_id, path_value):
        return

    for candidate in _resolve_candidate_paths(path_value, repo_root, schema_root):
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
    repo_root: Path,
    schema_root: Path,
) -> None:
    _check_required_fields(record, file, report)
    _check_list_fields(record, file, report)
    _check_enums(record, file, registry, report)
    _check_dependencies(record, file, report)
    _check_paths(record, file, report, config, repo_root, schema_root)


def validate_file(
    path: Path,
    *,
    registry: EnumRegistry,
    report: ValidationReport,
    seen_ids: Dict[str, Path],
    config: ValidatorConfig,
    repo_root: Path,
    schema_root: Path,
    stats: ValidationStats,
) -> None:
    stats.files_checked += 1
    records = _load_inventory_data(path, report)
    for record in records:
        if not isinstance(record, dict):
            report.add("error", path, "Each record must be a mapping", record_id=str(record))
            continue
        stats.records_checked += 1
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
                    first_occurrence=str(seen_ids[record_id].relative_to(repo_root)).replace("\\", "/"),
                )
            else:
                seen_ids[record_id] = path
        validate_record(record, path, registry, report, config, repo_root, schema_root)


def render_markdown(report_payload: Dict[str, Any]) -> str:
    summary = report_payload.get("summary", {})
    issue_counts = summary.get("issue_counts", {})
    lines = ["# Inventory Validation Report\n\n"]
    lines.append(f"- generated_utc: {report_payload['generated_utc']}\n")
    lines.append(f"- status: {report_payload['status']}\n")
    lines.append(f"- output_dir: {report_payload['output_dir']}\n")
    lines.append("\n## Summary\n\n")
    lines.append("| Metric | Value |\n")
    lines.append("|---|---:|\n")
    lines.append(f"| files_checked | {summary.get('files_checked', 0)} |\n")
    lines.append(f"| records_checked | {summary.get('records_checked', 0)} |\n")
    lines.append(f"| errors | {issue_counts.get('errors', 0)} |\n")
    lines.append(f"| warnings | {issue_counts.get('warnings', 0)} |\n")
    lines.append("\n## Notes\n\n")
    lines.append("(none)\n")
    return "".join(lines)


def render_log(report_payload: Dict[str, Any]) -> str:
    summary = report_payload.get("summary", {})
    issue_counts = summary.get("issue_counts", {})
    return "\n".join(
        [
            f"status={report_payload['status']}",
            f"timestamp={report_payload['timestamp']}",
            f"files_checked={summary.get('files_checked', 0)}",
            f"records_checked={summary.get('records_checked', 0)}",
            f"errors={issue_counts.get('errors', 0)}",
            f"warnings={issue_counts.get('warnings', 0)}",
        ]
    ) + "\n"


def write_run_artifacts(run_dir: Path, report_payload: Dict[str, Any], raw_payload: Dict[str, Any]) -> None:
    (run_dir / "report.json").write_text(json.dumps(report_payload, indent=2) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown(report_payload), encoding="utf-8")
    (run_dir / "log.txt").write_text(render_log(report_payload), encoding="utf-8")
    (run_dir / "raw.json").write_text(json.dumps(raw_payload, indent=2) + "\n", encoding="utf-8")


def compose_payload(
    *,
    repo_root: Path,
    run_dir: Path,
    slug: str,
    generated_at: datetime,
    stats: ValidationStats,
    report: ValidationReport,
    schema_root: Path,
    config_path: Path,
    enums_path: Path,
) -> Dict[str, Any]:
    issue_counts = {
        "total": len(report.issues),
        "errors": len(report.errors),
        "warnings": len(report.warnings),
    }
    summary = {
        **stats.to_dict(),
        "issue_counts": issue_counts,
    }
    status = "ok" if issue_counts["errors"] == 0 else "error"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "timestamp": slug,
        "generated_utc": generated_at.isoformat(),
        "repo_root": str(repo_root),
        "output_dir": str(run_dir),
        "inputs": {
            "schema_root": str(schema_root),
            "config_path": str(config_path),
            "enums_path": str(enums_path),
        },
        "summary": summary,
    }


def compose_raw_payload(report_payload: Dict[str, Any], report: ValidationReport, repo_root: Path) -> Dict[str, Any]:
    issues_all = [issue.to_dict(repo_root) for issue in report.issues]
    issues_errors = [issue for issue in issues_all if issue["level"] == "error"]
    issues_warnings = [issue for issue in issues_all if issue["level"] == "warning"]
    return {
        **report_payload,
        "issues": {
            "all": issues_all,
            "errors": issues_errors,
            "warnings": issues_warnings,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Repo Studios inventory YAML and emit structured artifacts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="Repository root used to resolve paths")
    parser.add_argument("--schema-root", default=str(DEFAULT_SCHEMA_ROOT), help="Path to inventory schema directory")
    parser.add_argument("--enums-path", default=str(DEFAULT_ENUMS_PATH), help="Path to enums YAML file")
    parser.add_argument("--template-path", default=str(DEFAULT_TEMPLATE_PATH), help="Path to inventory entry template (ignored)" )
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH), help="Optional validator configuration file (YAML)")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory for structured artifacts")
    parser.add_argument("--timestamp", help="Override run timestamp (ISO8601)")
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="Number of historical runs to retain")
    parser.add_argument("--json", action="store_true", help="Emit validation issues to stdout in JSON (legacy mode)")
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s: %(message)s")

    repo_root = Path(args.repo_root).resolve()
    schema_root = _ensure_dir(_resolve(repo_root, args.schema_root))

    def _resolve_schema_relative(arg_value: str, default_path: Path, filename: str) -> Path:
        if arg_value == str(default_path):
            return (schema_root / filename).resolve()
        return _resolve(repo_root, arg_value)

    enums_path = _resolve_schema_relative(args.enums_path, DEFAULT_ENUMS_PATH, "enums.yaml")
    template_path = _resolve_schema_relative(
        args.template_path,
        DEFAULT_TEMPLATE_PATH,
        "inventory_entry_template.yaml",
    )
    config_path = _resolve_schema_relative(args.config_path, DEFAULT_CONFIG_PATH, "validator_config.yaml")
    output_dir = _ensure_dir(_resolve(repo_root, args.output_dir))

    generated_at = _current_time() if args.timestamp is None else datetime.fromisoformat(args.timestamp)
    slug = _format_slug(generated_at)
    run_dir = _prepare_run_dir(output_dir, slug)

    registry = EnumRegistry.load(enums_path)
    config = ValidatorConfig.load(config_path)
    report = ValidationReport()
    stats = ValidationStats()
    seen_ids: Dict[str, Path] = {}

    for file in iterate_inventory_files(
        schema_root,
        enums_path=enums_path,
        template_path=template_path,
        config_path=config_path,
    ):
        validate_file(
            file,
            registry=registry,
            report=report,
            seen_ids=seen_ids,
            config=config,
            repo_root=repo_root,
            schema_root=schema_root,
            stats=stats,
        )

    report_payload = compose_payload(
        repo_root=repo_root,
        run_dir=run_dir,
        slug=slug,
        generated_at=generated_at,
        stats=stats,
        report=report,
        schema_root=schema_root,
        config_path=config_path,
        enums_path=enums_path,
    )
    raw_payload = compose_raw_payload(report_payload, report, repo_root)

    write_run_artifacts(run_dir, report_payload, raw_payload)
    update_latest_artifacts(run_dir, output_dir)
    prune_old_runs(output_dir, keep=args.artifacts_to_keep, current_run=run_dir)

    if args.json:
        print(ValidationReport(issues=report.issues).to_json(repo_root))
    else:
        if report.errors:
            for issue in report.errors:
                details = issue.to_dict(repo_root)
                print(f"[ERROR] {details['file']}: {details['message']}")
        else:
            print("Inventory validation passed")

    logging.info(
        "validate_inventory status=%s files=%s records=%s errors=%s warnings=%s",
        report_payload["status"],
        report_payload["summary"].get("files_checked", 0),
        report_payload["summary"].get("records_checked", 0),
        report_payload["summary"]["issue_counts"].get("errors", 0),
        report_payload["summary"]["issue_counts"].get("warnings", 0),
    )

    return 0 if report_payload["summary"]["issue_counts"]["errors"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
