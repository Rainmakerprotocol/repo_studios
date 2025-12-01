from __future__ import annotations

import logging

from command_center.scripts.libraries import (
    SkipTopicStep,
    TopicContext,
    TopicStep,
    build_topic_pipeline,
    step_failed,
    step_skipped,
    step_success,
)


def test_pipeline_runs_steps_in_order() -> None:
    context = TopicContext(paths={}, options={})
    order: list[str] = []

    def first_step(ctx: TopicContext):
        order.append("first")
        ctx.add_metadata("first", True)
        return step_success(payload={"value": 1})

    def second_step(ctx: TopicContext):
        order.append("second")
        return step_success(detail="done")

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="first", runner=first_step),
            TopicStep(name="second", runner=second_step),
        ]
    )

    result = pipeline.run(context)

    assert result.succeeded is True
    assert [report.name for report in result.steps] == ["first", "second"]
    assert order == ["first", "second"]
    assert context.metadata["first"] is True
    assert result.steps[0].payload == {"value": 1}
    assert result.steps[1].detail == "done"


def test_pipeline_stops_on_failure() -> None:
    context = TopicContext(paths={}, options={})
    executed: list[str] = []

    def failing_step(ctx: TopicContext):
        executed.append("fail")
        return step_failed(detail="boom")

    def should_not_run(_: TopicContext):
        executed.append("later")
        return step_success()

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="fail", runner=failing_step),
            TopicStep(name="next", runner=should_not_run),
        ]
    )

    result = pipeline.run(context)

    assert result.succeeded is False
    assert [report.name for report in result.steps] == ["fail"]
    assert executed == ["fail"]


def test_pipeline_skips_on_exception() -> None:
    context = TopicContext(paths={}, options={})

    def skip_step(_: TopicContext):
        raise SkipTopicStep("no data")

    pipeline = build_topic_pipeline(steps=[TopicStep(name="maybe", runner=skip_step)])

    result = pipeline.run(context)

    assert result.succeeded is True
    assert result.steps[0].status == "skipped"
    assert result.steps[0].detail == "no data"


def test_pipeline_honours_continue_on_failure() -> None:
    context = TopicContext(paths={}, options={})
    executed: list[str] = []

    def failing_step(_: TopicContext):
        executed.append("fail")
        return step_failed(detail="recoverable")

    def later_step(_: TopicContext):
        executed.append("later")
        return step_success()

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="fail", runner=failing_step, continue_on_failure=True),
            TopicStep(name="later", runner=later_step),
        ]
    )

    result = pipeline.run(context)

    assert result.succeeded is False
    assert [report.name for report in result.steps] == ["fail", "later"]
    assert executed == ["fail", "later"]


def test_build_topic_pipeline_requires_steps() -> None:
    try:
        build_topic_pipeline(steps=[])
    except ValueError as exc:  # pragma: no cover - explicit branch
        assert "requires" in str(exc)
    else:  # pragma: no cover - should not reach
        raise AssertionError("Expected ValueError for empty pipeline")


def test_pipeline_emits_logging_for_step_outcomes(caplog) -> None:
    caplog.set_level(logging.DEBUG)
    context = TopicContext(paths={}, options={})

    def success_step(_: TopicContext):
        return step_success(detail="ready")

    def skipped_step(_: TopicContext):
        raise SkipTopicStep("not required")

    def failing_step(_: TopicContext):
        raise ValueError("boom")

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="alpha", runner=success_step),
            TopicStep(name="beta", runner=skipped_step),
            TopicStep(name="gamma", runner=failing_step, continue_on_failure=True),
        ]
    )

    pipeline.run(context)

    messages = [record.getMessage() for record in caplog.records]
    assert any("Starting topic step alpha" in message for message in messages)
    assert any("Step alpha completed successfully" in message for message in messages)
    assert any("Step beta skipped: not required" in message for message in messages)
    assert any("Step gamma failed: boom" in message for message in messages)
