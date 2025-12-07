"""Telemetry helpers for topic orchestrator pipeline runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .topic_pipeline import TopicPipelineResult


@dataclass(frozen=True)
class ArtifactMetrics:
    """File count and byte sizing for an artifact directory."""

    file_count: int
    total_bytes: int

    def as_dict(self) -> dict[str, int]:
        return {
            "artifact_files": self.file_count,
            "artifact_bytes": self.total_bytes,
        }


@dataclass(frozen=True)
class TopicTelemetry:
    """Container for orchestrator telemetry destined for Command Center manifests."""

    viewer: str
    topic: str
    run_slug: str
    success: bool
    started_at: datetime
    finished_at: datetime
    steps: list[dict[str, Any]]
    metrics: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "viewer": self.viewer,
            "topic": self.topic,
            "run_slug": self.run_slug,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "steps": self.steps,
            "metrics": dict(self.metrics),
        }


def build_pipeline_telemetry(
    result: TopicPipelineResult,
    *,
    viewer: str,
    topic: str,
    run_slug: str,
    extra_metrics: Mapping[str, Any] | None = None,
) -> TopicTelemetry:
    """Create telemetry payload describing a topic pipeline execution."""

    step_payloads: list[dict[str, Any]] = []
    succeeded_steps = 0
    failed_steps = 0
    skipped_steps = 0
    for step in result.steps:
        payload: dict[str, Any] = {
            "name": step.name,
            "status": step.status,
            "started_at": step.started_at.isoformat(),
            "finished_at": step.finished_at.isoformat(),
        }
        if step.detail:
            payload["detail"] = step.detail
        if step.payload:
            payload["payload"] = step.payload
        step_payloads.append(payload)
        if step.status == "success":
            succeeded_steps += 1
        elif step.status == "failed":
            failed_steps += 1
        else:
            skipped_steps += 1

    duration = (result.finished_at - result.started_at).total_seconds()
    metrics: dict[str, Any] = {
        "runtime_seconds": duration if duration >= 0 else 0.0,
        "step_count": len(result.steps),
        "steps_succeeded": succeeded_steps,
        "steps_failed": failed_steps,
        "steps_skipped": skipped_steps,
    }
    if extra_metrics:
        metrics.update(extra_metrics)
    return TopicTelemetry(
        viewer=viewer,
        topic=topic,
        run_slug=run_slug,
        success=result.succeeded,
        started_at=result.started_at,
        finished_at=result.finished_at,
        steps=step_payloads,
        metrics=metrics,
    )


def measure_artifact_directory(path: Path | None) -> ArtifactMetrics:
    """Return file counts and byte sizes for ``path`` (non-existent paths return zeros)."""

    if path is None:
        return ArtifactMetrics(file_count=0, total_bytes=0)
    resolved = path.resolve()
    if not resolved.exists():
        return ArtifactMetrics(file_count=0, total_bytes=0)

    file_count = 0
    total_bytes = 0
    for candidate in resolved.rglob("*"):
        if not candidate.is_file():
            continue
        file_count += 1
        try:
            total_bytes += candidate.stat().st_size
        except OSError:
            continue
    return ArtifactMetrics(file_count=file_count, total_bytes=total_bytes)
