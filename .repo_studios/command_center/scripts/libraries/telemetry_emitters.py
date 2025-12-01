"""Telemetry helpers for topic orchestrator pipeline runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .topic_pipeline import TopicPipelineResult


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

    def as_dict(self) -> dict[str, Any]:
        return {
            "viewer": self.viewer,
            "topic": self.topic,
            "run_slug": self.run_slug,
            "success": self.success,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "steps": self.steps,
        }


def build_pipeline_telemetry(
    result: TopicPipelineResult,
    *,
    viewer: str,
    topic: str,
    run_slug: str,
) -> TopicTelemetry:
    """Create telemetry payload describing a topic pipeline execution."""

    step_payloads: list[dict[str, Any]] = []
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
    return TopicTelemetry(
        viewer=viewer,
        topic=topic,
        run_slug=run_slug,
        success=result.succeeded,
        started_at=result.started_at,
        finished_at=result.finished_at,
        steps=step_payloads,
    )
