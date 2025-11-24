"""Guardrail configuration helpers for automation planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml


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
