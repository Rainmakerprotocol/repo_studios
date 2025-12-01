"""Topic pipeline assembly helpers for Command Center orchestrators."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Iterable, Literal, Sequence

StepStatus = Literal["success", "skipped", "failed"]


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class TopicStepOutcome:
    """Result returned by a pipeline step runner."""

    status: StepStatus
    detail: str | None = None
    payload: dict[str, Any] | None = None


def step_success(*, detail: str | None = None, payload: dict[str, Any] | None = None) -> TopicStepOutcome:
    """Construct a successful :class:`TopicStepOutcome`."""

    return TopicStepOutcome(status="success", detail=detail, payload=payload)


def step_skipped(*, detail: str | None = None) -> TopicStepOutcome:
    """Construct a skipped :class:`TopicStepOutcome`."""

    return TopicStepOutcome(status="skipped", detail=detail, payload=None)


def step_failed(*, detail: str | None = None, payload: dict[str, Any] | None = None) -> TopicStepOutcome:
    """Construct a failed :class:`TopicStepOutcome`."""

    return TopicStepOutcome(status="failed", detail=detail, payload=payload)


class SkipTopicStep(RuntimeError):
    """Raised by a step runner to indicate the step should be skipped."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "")
        self.message = message or ""


@dataclass
class TopicContext:
    """Context object threaded through topic orchestrator steps."""

    paths: Any
    options: Any
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value


@dataclass(frozen=True)
class TopicStep:
    """Definition of a single pipeline step."""

    name: str
    runner: Callable[[TopicContext], TopicStepOutcome | None]
    description: str = ""
    continue_on_failure: bool = False


@dataclass(frozen=True)
class TopicStepReport:
    """Execution details captured for each pipeline step."""

    name: str
    status: StepStatus
    started_at: datetime
    finished_at: datetime
    detail: str | None
    payload: dict[str, Any] | None


@dataclass(frozen=True)
class TopicPipelineResult:
    """Aggregate status returned after running a topic pipeline."""

    steps: list[TopicStepReport]
    succeeded: bool
    started_at: datetime
    finished_at: datetime

    @property
    def failed_steps(self) -> list[TopicStepReport]:
        return [step for step in self.steps if step.status == "failed"]

    def raise_for_failure(self) -> None:
        if self.succeeded:
            return
        messages = [f"{step.name}: {step.detail or 'failed'}" for step in self.failed_steps]
        raise RuntimeError("; ".join(messages))


@dataclass(frozen=True)
class TopicPipeline:
    """Callable wrapper returned by :func:`build_topic_pipeline`."""

    steps: Sequence[TopicStep]
    stop_on_failure: bool = True

    def run(self, context: TopicContext) -> TopicPipelineResult:
        pipeline_started = datetime.now(timezone.utc)
        reports: list[TopicStepReport] = []
        for step in self.steps:
            LOGGER.debug("Starting topic step %s", step.name)
            step_started = datetime.now(timezone.utc)
            outcome: TopicStepOutcome
            try:
                result = step.runner(context)
                if result is None:
                    outcome = step_success()
                else:
                    outcome = result
            except SkipTopicStep as exc:
                outcome = step_skipped(detail=exc.message or "skipped")
            except Exception as exc:  # pragma: no cover - defensive branch executed in error flows
                LOGGER.exception("Step %s raised unexpected error", step.name)
                outcome = step_failed(detail=str(exc))

            step_finished = datetime.now(timezone.utc)
            reports.append(
                TopicStepReport(
                    name=step.name,
                    status=outcome.status,
                    started_at=step_started,
                    finished_at=step_finished,
                    detail=outcome.detail,
                    payload=outcome.payload,
                )
            )

            if outcome.status == "failed" and self.stop_on_failure and not step.continue_on_failure:
                LOGGER.error("Step %s failed: %s", step.name, outcome.detail or "failed")
                break
            elif outcome.status == "failed":
                LOGGER.error("Step %s failed: %s", step.name, outcome.detail or "failed")
            elif outcome.status == "skipped":
                LOGGER.info("Step %s skipped: %s", step.name, outcome.detail or "skipped")
            else:
                LOGGER.debug("Step %s completed successfully", step.name)

        pipeline_finished = datetime.now(timezone.utc)
        succeeded = all(report.status != "failed" for report in reports)
        return TopicPipelineResult(
            steps=reports,
            succeeded=succeeded,
            started_at=pipeline_started,
            finished_at=pipeline_finished,
        )


def build_topic_pipeline(*, steps: Iterable[TopicStep], stop_on_failure: bool = True) -> TopicPipeline:
    """Create a :class:`TopicPipeline` from step definitions."""

    step_list = list(steps)
    if not step_list:
        raise ValueError("Topic pipeline requires at least one step")
    return TopicPipeline(steps=step_list, stop_on_failure=stop_on_failure)
