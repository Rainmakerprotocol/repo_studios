from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from command_center.scripts.orchestrators import run_monkey_patch_oversight as oversight


def test_monkey_patch_oversight_pipeline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)

    paths = oversight.Paths(
        repo_root=repo_root,
        scan_root=repo_root / "src",
        producer_output_dir=repo_root / "producer",
        consumer_output_dir=repo_root / "consumer",
        aggregator_output_dir=repo_root / "aggregator",
        summarizer_output_dir=repo_root / "summaries",
        healthview_root=repo_root / "healthview",
    )

    for directory in [
        paths.scan_root,
        paths.producer_output_dir,
        paths.consumer_output_dir,
        paths.aggregator_output_dir,
        paths.summarizer_output_dir,
        paths.healthview_root,
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    options = oversight.Options(
        log_level="ERROR",
        artifacts_to_keep=1,
        producer_keep=1,
        consumer_keep=1,
        aggregator_keep=1,
        summarizer_keep=1,
        trend_max_runs=5,
        producer_context_lines=7,
        producer_with_git=False,
        producer_strict=False,
        producer_project_packages=("demo",),
        producer_exclude_dirs=("tests",),
        producer_exclude_globs=("*.tmp",),
        skip_producer=False,
        skip_consumer=False,
        skip_aggregator=False,
        skip_summarizer=False,
        duplicate_matrix=None,
        run_timestamp=datetime(2025, 12, 1, 12, 34, tzinfo=timezone.utc),
    )

    producer_dir = paths.producer_output_dir / "producer_run"
    producer_dir.mkdir(parents=True, exist_ok=True)
    producer_report = producer_dir / "report.json"
    producer_report.write_text("{}", encoding="utf-8")
    producer_matches = producer_dir / "matches.json"
    producer_matches.write_text("[]", encoding="utf-8")

    consumer_dir = paths.consumer_output_dir / "consumer_run"
    consumer_dir.mkdir(parents=True, exist_ok=True)
    consumer_summary = consumer_dir / "SUMMARY.md"
    consumer_summary.write_text("# summary\n", encoding="utf-8")
    consumer_json = consumer_dir / "summary.json"
    consumer_json.write_text("{}", encoding="utf-8")
    consumer_bundle_summary = consumer_dir / "bundle_summary.json"
    consumer_bundle_summary.write_text("{}", encoding="utf-8")

    aggregator_dir = paths.aggregator_output_dir / "aggregator_run"
    aggregator_dir.mkdir(parents=True, exist_ok=True)
    aggregator_json = aggregator_dir / "trend.json"
    aggregator_json.write_text("{}", encoding="utf-8")
    aggregator_md = aggregator_dir / "trend.md"
    aggregator_md.write_text("# trend\n", encoding="utf-8")
    aggregator_bundle = aggregator_dir / "bundle_summary.json"
    aggregator_bundle.write_text("{}", encoding="utf-8")

    summarizer_dir = paths.summarizer_output_dir / "overview_run"
    summarizer_dir.mkdir(parents=True, exist_ok=True)
    overview_md = summarizer_dir / "overview.md"
    overview_md.write_text("# overview\n", encoding="utf-8")
    overview_json = summarizer_dir / "overview.json"
    overview_json.write_text("{}", encoding="utf-8")

    producer_outcome = oversight.ProducerOutcome(
        payload={"status": "ok", "total_findings": 2, "run_id": "producer_run"},
        run_dir=producer_dir,
        report_path=producer_report,
        matches_path=producer_matches,
        status="ok",
        total_findings=2,
        run_id="producer_run",
    )
    consumer_outcome = oversight.ConsumerOutcome(
        payload={"source": "scan", "bundle_dir": str(consumer_dir)},
        bundle_dir=consumer_dir,
        bundle_summary=consumer_bundle_summary,
        summary_json=consumer_json,
        summary_markdown=consumer_summary,
        source="scan",
    )
    aggregator_outcome = oversight.AggregatorOutcome(
        payload={"mode": "trend", "runs": 1},
        trend_dir=aggregator_dir,
        trend_json=aggregator_json,
        trend_markdown=aggregator_md,
        bundle_summary=aggregator_bundle,
        consumer_snapshot=consumer_json,
        mode="trend",
    )
    summarizer_outcome = oversight.SummarizerOutcome(
        payload={"status": "ok", "slug": "overview_run", "artifacts": {}},
        run_dir=summarizer_dir,
        artifacts={
            "overview.md": overview_md,
            "overview.json": overview_json,
        },
        slug="overview_run",
    )

    monkeypatch.setattr(oversight, "build_paths", lambda args: paths)
    monkeypatch.setattr(oversight, "build_options", lambda args, paths: options)
    monkeypatch.setattr(oversight, "configure_logging", lambda level: None)

    monkeypatch.setattr(oversight, "_execute_producer", lambda paths, options: producer_outcome)
    monkeypatch.setattr(oversight, "_execute_consumer", lambda paths, options, producer: consumer_outcome)
    monkeypatch.setattr(oversight, "_execute_aggregator", lambda paths, options, consumer: aggregator_outcome)
    monkeypatch.setattr(
        oversight,
        "_execute_summarizer",
        lambda paths, options, producer, consumer, aggregator: summarizer_outcome,
    )

    class FakeTelemetry:
        def __init__(self) -> None:
            self.payload = {"steps": []}

        def as_dict(self) -> dict[str, object]:
            return dict(self.payload)

    monkeypatch.setattr(oversight, "build_pipeline_telemetry", lambda *args, **kwargs: FakeTelemetry())

    class FakeMetrics:
        def as_dict(self) -> dict[str, int]:
            return {"files": 3}

    monkeypatch.setattr(oversight, "measure_artifact_directory", lambda run_dir: FakeMetrics())

    result_dir = paths.healthview_root / oversight.VIEWER_SLUG / oversight.HEALTHVIEW_TOPIC / "20251201-1234"
    result_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = result_dir / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    summary_path = result_dir / "summary.md"
    summary_path.write_text("", encoding="utf-8")
    telemetry_path = result_dir / "telemetry.json"
    telemetry_path.write_text("{}", encoding="utf-8")

    manifest_result = SimpleNamespace(
        run_dir=result_dir,
        slug="20251201-1234",
        artifacts={
            "manifest.json": manifest_path,
            "summary.md": summary_path,
            "telemetry.json": telemetry_path,
        },
    )

    def _fake_write_report_artifacts(**kwargs):
        for artifact in kwargs.get("artifacts", []):
            if artifact.filename == "manifest.json":
                manifest_payload = artifact.content()
                manifest_path.write_text(
                    json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
            elif artifact.filename == "summary.md":
                summary_path.write_text(str(artifact.content()), encoding="utf-8")
            elif artifact.filename == "telemetry.json":
                telemetry_payload = artifact.content()
                telemetry_path.write_text(
                    json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
        return manifest_result

    monkeypatch.setattr(oversight, "write_report_artifacts", _fake_write_report_artifacts)

    exit_code = oversight.run(["--repo-root", str(repo_root)])

    assert exit_code == 0
    assert manifest_path.read_text(encoding="utf-8").strip().startswith("{")
    assert telemetry_path.read_text(encoding="utf-8").strip().startswith("{")
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Monkey Patch Oversight Run" in summary_text
    assert "producer" in summary_text