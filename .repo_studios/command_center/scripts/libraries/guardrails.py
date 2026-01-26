"""Guardrail configuration helpers for automation planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml
from utilities import reports_naming_audit


class GuardrailConfigError(ValueError):
    """Raised when the guardrail configuration file is invalid."""


class GuardrailViolationError(RuntimeError):
    """Raised when a proposed automation run violates configured guardrails."""


@dataclass(frozen=True)
class GuardrailConstraints:
    max_files_per_run: int
    max_groups_per_run: int | None = None
    require_lock_check: bool = False
    allow_override_flag: str = "allow-ignore"


@dataclass(frozen=True)
class GuardrailConfig:
    config_path: Path
    allow_list_source: Path
    constraints: GuardrailConstraints
    metadata: dict[str, str]


def load_guardrail_config(config_path: Path) -> GuardrailConfig:
    """Load the guardrail configuration YAML and normalize paths."""
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    metadata = data.get("metadata") or {}
    allow_list = data.get("allow_list") or {}
    allow_source_value = allow_list.get("source")
    if not allow_source_value:
        raise GuardrailConfigError("Guardrail config missing allow_list.source")

    constraints_data = data.get("constraints") or {}
    max_files = constraints_data.get("max_files_per_run")
    if max_files is None:
        raise GuardrailConfigError("Guardrail config missing constraints.max_files_per_run")

    try:
        max_files_int = int(max_files)
    except (TypeError, ValueError) as exc:
        raise GuardrailConfigError("constraints.max_files_per_run must be an integer") from exc
    if max_files_int <= 0:
        raise GuardrailConfigError("constraints.max_files_per_run must be positive")

    max_groups_value = constraints_data.get("max_groups_per_run")
    max_groups_int = int(max_groups_value) if max_groups_value is not None else None

    require_lock_check_value = constraints_data.get("require_lock_check", False)
    allow_override_flag_value = constraints_data.get("allow_override_flag", "allow-ignore")

    config_dir = config_path.parent
    allow_list_path = (config_dir / allow_source_value).resolve()

    constraints = GuardrailConstraints(
        max_files_per_run=max_files_int,
        max_groups_per_run=max_groups_int,
        require_lock_check=bool(require_lock_check_value),
        allow_override_flag=str(allow_override_flag_value),
    )
    return GuardrailConfig(
        config_path=config_path.resolve(),
        allow_list_source=allow_list_path,
        constraints=constraints,
        metadata={str(key): str(value) for key, value in metadata.items()},
    )


def enforce_run_size_limit(
    candidate_files: Sequence[Path] | Iterable[Path],
    config: GuardrailConfig,
    *,
    override: bool = False,
) -> tuple[int, int]:
    """Ensure the candidate file set respects the configured max file budget."""
    files = tuple(candidate_files)
    run_size = len(files)
    limit = config.constraints.max_files_per_run
    if override:
        return limit, run_size
    if run_size > limit:
        raise GuardrailViolationError(
            (
                f"Proposed automation run would touch {run_size} files, "
                f"exceeding the configured guardrail limit of {limit} defined in "
                f"{config.config_path}."
            )
        )
    return limit, run_size


def _topic_ignore_prefixes(reports_root: Path, viewer: str, topic: str) -> list[str]:
    prefixes: list[str] = []
    if not reports_root.exists():
        return prefixes
    for entry in reports_root.iterdir():
        name = entry.name
        if entry.is_dir():
            if name != viewer:
                prefixes.append(name)
                continue
            for child in entry.iterdir():
                child_name = child.name
                child_prefix = f"{viewer}/{child_name}"
                if child.is_dir():
                    if child_name != topic:
                        prefixes.append(child_prefix)
                else:
                    prefixes.append(child_prefix)
        else:
            prefixes.append(name)
    return prefixes


def enforce_report_naming(
    *,
    reports_root: Path,
    run_dir: Path,
    viewer: str,
    topic: str,
    artifact_roles: Iterable[str] | None = None,
    extra_ignore_prefixes: Iterable[str] | None = None,
) -> dict[str, object]:
    resolved_root = reports_root.resolve()
    resolved_run_dir = run_dir.resolve()
    try:
        rel_run_dir = resolved_run_dir.relative_to(resolved_root)
    except ValueError as exc:
        raise GuardrailViolationError(
            f"Run directory {resolved_run_dir} is not within reports root {resolved_root}."
        ) from exc
    parts = rel_run_dir.parts
    if len(parts) < 3:
        raise GuardrailViolationError(
            f"Run directory {resolved_run_dir} is missing viewer/topic/timestamp depth."
        )
    run_viewer, run_topic = parts[0], parts[1]
    if run_viewer != viewer or run_topic != topic:
        raise GuardrailViolationError(
            (
                "Run directory {dir} mapped to viewer/topic {found_viewer}/{found_topic} "
                "does not match expected {expected_viewer}/{expected_topic}."
            ).format(
                dir=resolved_run_dir,
                found_viewer=run_viewer,
                found_topic=run_topic,
                expected_viewer=viewer,
                expected_topic=topic,
            )
        )

    ignore_prefixes = list(extra_ignore_prefixes or [])
    ignore_prefixes.extend(_topic_ignore_prefixes(resolved_root, viewer, topic))

    roles = tuple(str(role) for role in (artifact_roles or ()))
    summary = reports_naming_audit.audit_reports(
        resolved_root,
        artifact_roles=roles,
        allowed_viewers=[viewer],
        ignore_prefixes=ignore_prefixes,
    )

    topic_prefix = f"{viewer}/{topic}"
    violations = []
    violations_raw = summary.get("violations")
    if isinstance(violations_raw, list):
        for entry in violations_raw:
            if not isinstance(entry, dict):
                continue
            raw_path = entry.get("path")
            if not isinstance(raw_path, str):
                continue
            if not raw_path.startswith(topic_prefix):
                continue
            issues = entry.get("issues", [])
            rendered = ", ".join(str(issue) for issue in issues) if isinstance(issues, list) else ""
            violations.append((raw_path, rendered))

    if violations:
        details = "\n".join(f"{path}: {detail}" if detail else path for path, detail in violations)
        raise GuardrailViolationError(
            (
                f"Report naming violations detected under {topic_prefix}:\n"
                f"{details}"
            )
        )

    return summary
