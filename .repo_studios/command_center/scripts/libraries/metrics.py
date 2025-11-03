"""Helpers for building automation metrics summaries."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Mapping

_ALLOWED_TEST_STATUSES = {"passed", "failed", "skipped"}


def _ensure_non_negative(name: str, value: int | float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True)
class TestRunResult:
    status: str
    duration_seconds: float
    artifacts: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in _ALLOWED_TEST_STATUSES:
            raise ValueError(f"Unsupported test status: {self.status}")
        _ensure_non_negative("duration_seconds", self.duration_seconds)
        object.__setattr__(self, "artifacts", tuple(self.artifacts))

    def to_dict(self) -> Dict[str, object]:
        return {
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "artifacts": list(self.artifacts),
        }


@dataclass(frozen=True)
class MetricsSummary:
    schema_version: str
    run_id: str
    targets: tuple[str, ...]
    lines_touched: int
    files_changed: int
    duplicate_groups_resolved: int
    runtime_seconds: float
    tests_executed: Mapping[str, TestRunResult]
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("schema_version is required")
        if not self.run_id:
            raise ValueError("run_id is required")
        if not self.targets:
            raise ValueError("At least one target is required")
        object.__setattr__(self, "targets", tuple(self.targets))
        _ensure_non_negative("lines_touched", self.lines_touched)
        _ensure_non_negative("files_changed", self.files_changed)
        _ensure_non_negative("duplicate_groups_resolved", self.duplicate_groups_resolved)
        _ensure_non_negative("runtime_seconds", self.runtime_seconds)
        if not self.tests_executed:
            raise ValueError("tests_executed cannot be empty")

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "targets": list(self.targets),
            "lines_touched": self.lines_touched,
            "files_changed": self.files_changed,
            "duplicate_groups_resolved": self.duplicate_groups_resolved,
            "runtime_seconds": self.runtime_seconds,
            "tests_executed": {name: result.to_dict() for name, result in self.tests_executed.items()},
            "notes": self.notes,
        }


def build_metrics_summary(
    *,
    schema_version: str,
    run_id: str,
    targets: Iterable[str],
    lines_touched: int,
    files_changed: int,
    duplicate_groups_resolved: int,
    runtime_seconds: float,
    tests_executed: Mapping[str, TestRunResult],
    notes: str = "",
) -> MetricsSummary:
    return MetricsSummary(
        schema_version=schema_version,
        run_id=run_id,
        targets=tuple(targets),
        lines_touched=lines_touched,
        files_changed=files_changed,
        duplicate_groups_resolved=duplicate_groups_resolved,
        runtime_seconds=runtime_seconds,
        tests_executed=dict(tests_executed),
        notes=notes,
    )


def write_metrics_summary(summary: MetricsSummary, output_path: Path) -> Path:
    payload = summary.to_dict()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return output_path
