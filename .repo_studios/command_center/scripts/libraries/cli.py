"""CLI helper utilities shared across Command Center producers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Type


@dataclass(frozen=True)
class PathSpec:
    field: str
    default: Path
    ensure_dir: bool = False
    within_repo: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "default", Path(self.default))


@dataclass(frozen=True)
class KeepSpec:
    field: str
    minimum: int = 1
    env_override: str | None = None
    env_truthy: frozenset[str] = frozenset({"1", "true", "TRUE"})

    def __post_init__(self) -> None:
        object.__setattr__(self, "env_truthy", frozenset(self.env_truthy))


@dataclass(frozen=True)
class PathsConfig:
    dataclass_type: Type[Any]
    path_specs: Mapping[str, PathSpec]
    repo_root_depth: int = 3
    include_repo_root: bool = True
    repo_root_field: str = "repo_root"


@dataclass(frozen=True)
class OptionsConfig:
    dataclass_type: Type[Any]
    keep_specs: Mapping[str, KeepSpec]


def _source_value(source: Any, field: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(field)
    return getattr(source, field, None)


def resolve_repo_root(explicit: str | None, *, fallback_depth: int = 3, origin: Path | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    origin = origin or Path(__file__)
    cursor = origin.resolve()
    for _ in range(fallback_depth):
        cursor = cursor.parent
    return cursor


def resolve_path(
    explicit: str | None,
    *,
    repo_root: Path,
    default: Path,
    ensure_dir: bool = False,
    within_repo: bool = True,
) -> Path:
    candidate = Path(explicit).expanduser() if explicit else default
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if within_repo:
        try:
            candidate.relative_to(repo_root)
        except ValueError as exc:
            raise ValueError(f"Path must reside within the repo root: {candidate}") from exc
    if ensure_dir:
        candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def normalize_keep_count(raw: int | None, *, minimum: int = 1, env_override: str | None = None, env_truthy: frozenset[str] | None = None) -> int:
    env_truthy = env_truthy or frozenset({"1", "true", "TRUE"})
    value = raw if raw is not None else minimum
    if env_override and os.getenv(env_override) in env_truthy:
        return max(minimum, 1)
    try:
        return max(int(value), minimum)
    except (TypeError, ValueError):
        return minimum


def build_paths(config: Mapping[str, PathSpec], *, args: Any, repo_root: Path) -> dict[str, Path]:
    resolved: dict[str, Path] = {}
    for alias, spec in config.items():
        raw_value = _source_value(args, spec.field)
        resolved[alias] = resolve_path(
            raw_value,
            repo_root=repo_root,
            default=spec.default,
            ensure_dir=spec.ensure_dir,
            within_repo=spec.within_repo,
        )
    return resolved


def build_keep_counts(config: Mapping[str, KeepSpec], *, args: Any) -> dict[str, int]:
    resolved: dict[str, int] = {}
    for alias, spec in config.items():
        raw_value = _source_value(args, spec.field)
        resolved[alias] = normalize_keep_count(raw_value, minimum=spec.minimum, env_override=spec.env_override, env_truthy=spec.env_truthy)
    return resolved


def build_standard_paths(args: Any, config: PathsConfig, *, origin: Path) -> Any:
    repo_root = resolve_repo_root(getattr(args, "repo_root", None), fallback_depth=config.repo_root_depth, origin=origin)
    resolved = build_paths(config.path_specs, args=args, repo_root=repo_root)
    payload: dict[str, Any] = {}
    if config.include_repo_root:
        payload[config.repo_root_field] = repo_root
    for alias, value in resolved.items():
        payload[alias] = value
    return config.dataclass_type(**payload)


def build_standard_options(args: Any, config: OptionsConfig) -> Any:
    resolved = build_keep_counts(config.keep_specs, args=args)
    return config.dataclass_type(**resolved)
