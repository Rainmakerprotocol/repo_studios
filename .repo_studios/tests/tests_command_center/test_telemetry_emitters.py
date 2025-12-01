from __future__ import annotations

from command_center.scripts.libraries import (
    TopicContext,
    TopicStep,
    build_pipeline_telemetry,
    build_topic_pipeline,
    step_success,
)


def test_build_pipeline_telemetry() -> None:
    context = TopicContext(paths={}, options={})

    def sample_step(_: TopicContext):
        return step_success(detail="completed", payload={"metric": 1})

    pipeline = build_topic_pipeline(steps=[TopicStep(name="sample", runner=sample_step)])

    result = pipeline.run(context)
    telemetry = build_pipeline_telemetry(result, viewer="healthview", topic="test-execution-telemetry", run_slug="20251130-1200")
    payload = telemetry.as_dict()

    assert payload["viewer"] == "healthview"
    assert payload["topic"] == "test-execution-telemetry"
    assert payload["run_slug"] == "20251130-1200"
    assert payload["success"] is True
    assert len(payload["steps"]) == 1
    step = payload["steps"][0]
    assert step["name"] == "sample"
    assert step["status"] == "success"
    assert step["detail"] == "completed"
    assert step["payload"] == {"metric": 1}
    assert "started_at" in step and "finished_at" in step
