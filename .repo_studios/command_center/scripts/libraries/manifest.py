"""Helpers for composing automation manifest payloads."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Mapping

from .metrics import MetricsSummary

_ALLOWED_STATUSES = ("updated", "skipped", "conflicted")


def _ensure_non_empty(value: str, name: str) -> None:
	if not value:
		raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class ManifestFile:
	path: str
	duplicate_groups: tuple[str, ...] = field(default_factory=tuple)

	def __post_init__(self) -> None:
		_ensure_non_empty(self.path, "path")
		object.__setattr__(self, "duplicate_groups", tuple(self.duplicate_groups))

	def to_dict(self) -> Dict[str, object]:
		return {
			"path": self.path,
			"duplicate_groups": list(self.duplicate_groups),
		}


@dataclass(frozen=True)
class GuardrailState:
	max_files_per_run: int
	files_considered: int
	override_applied: bool
	config_path: Path | None = None
	allow_list_source: Path | None = None
	metadata: Mapping[str, str] = field(default_factory=dict)

	def to_dict(self) -> Dict[str, object]:
		payload: Dict[str, object] = {
			"max_files_per_run": self.max_files_per_run,
			"files_considered": self.files_considered,
			"override_applied": self.override_applied,
		}
		if self.config_path is not None:
			payload["config_path"] = str(self.config_path)
		if self.allow_list_source is not None:
			payload["allow_list_source"] = str(self.allow_list_source)
		if self.metadata:
			payload["metadata"] = dict(self.metadata)
		return payload


@dataclass(frozen=True)
class AutomationManifest:
	schema_version: str
	run_id: str
	timestamp: datetime
	targets: tuple[str, ...]
	baseline_sha: str
	dry_run: bool
	operator: str | None
	notes: str
	files: Mapping[str, tuple[ManifestFile, ...]]
	guardrails: GuardrailState | None
	metrics_summary: MetricsSummary
	metrics_summary_path: str

	def __post_init__(self) -> None:
		_ensure_non_empty(self.schema_version, "schema_version")
		_ensure_non_empty(self.run_id, "run_id")
		_ensure_non_empty(self.baseline_sha, "baseline_sha")
		_ensure_non_empty(self.metrics_summary_path, "metrics_summary_path")
		object.__setattr__(self, "targets", tuple(self.targets))
		if not self.targets:
			raise ValueError("At least one target is required")
		files_dict: Dict[str, tuple[ManifestFile, ...]] = {}
		for status, entries in self.files.items():
			if status not in _ALLOWED_STATUSES:
				raise ValueError(f"Unsupported manifest status: {status}")
			files_dict[status] = tuple(entries)
		for status in _ALLOWED_STATUSES:
			files_dict.setdefault(status, tuple())
		object.__setattr__(self, "files", files_dict)

	def to_dict(self) -> Dict[str, object]:
		return {
			"schema_version": self.schema_version,
			"run_id": self.run_id,
			"timestamp": self.timestamp.isoformat(),
			"targets": list(self.targets),
			"baseline_sha": self.baseline_sha,
			"dry_run": self.dry_run,
			"operator": self.operator,
			"notes": self.notes,
			"files": {
				status: [entry.to_dict() for entry in entries]
				for status, entries in self.files.items()
			},
			"guardrails": self.guardrails.to_dict() if self.guardrails else None,
			"metrics_summary_path": self.metrics_summary_path,
			"metrics_summary": self.metrics_summary.to_dict(),
		}


def build_automation_manifest(
	*,
	schema_version: str,
	run_id: str,
	timestamp: datetime,
	targets: Iterable[str],
	baseline_sha: str,
	dry_run: bool,
	operator: str | None,
	notes: str,
	files: Mapping[str, Iterable[ManifestFile]],
	guardrail_state: GuardrailState | None,
	metrics_summary: MetricsSummary,
	metrics_summary_path: str,
) -> AutomationManifest:
	return AutomationManifest(
		schema_version=schema_version,
		run_id=run_id,
		timestamp=timestamp,
		targets=tuple(targets),
		baseline_sha=baseline_sha,
		dry_run=dry_run,
		operator=operator,
		notes=notes,
		files={status: tuple(entries) for status, entries in files.items()},
		guardrails=guardrail_state,
		metrics_summary=metrics_summary,
		metrics_summary_path=metrics_summary_path,
	)


def write_automation_manifest(manifest: AutomationManifest, output_path: Path) -> Path:
	payload = manifest.to_dict()
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
	return output_path
