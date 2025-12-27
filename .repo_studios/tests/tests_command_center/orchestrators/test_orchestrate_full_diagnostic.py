from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

MODULE_NAME = "command_center.scripts.orchestrators.orchestrate_full_diagnostic"


def _reload_module():
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def _make_stub(
    *,
    name: str,
    slug: str,
    viewer: str = "healthview",
    topic: str | None = None,
    exit_code: int = 0,
    executions: list[str] | None = None,
):
    module_name = f"tests.command_center.meta_stub.{name}"
    stub = types.ModuleType(module_name)
    calls: list[list[str]] = []

    def run(argv):
        calls.append(list(argv))
        if executions is not None:
            executions.append(slug)
        return exit_code

    stub.run = run  # type: ignore[attr-defined]
    stub.VIEWER_SLUG = viewer
    stub.TOPIC_SLUG = slug
    stub.HEALTHVIEW_TOPIC = topic or slug.replace("-", "_")
    stub._calls = calls
    sys.modules[module_name] = stub
    return stub, module_name


def test_run_emits_manifest_and_respects_includes(tmp_path):
    module = _reload_module()
    (tmp_path / ".repo_studios").mkdir()
    original_definitions = module.TOPIC_DEFINITIONS
    try:
        executions: list[str] = []
        stub_a, name_a = _make_stub(name="topic_a", slug="topic-a", executions=executions)
        stub_b, name_b = _make_stub(name="topic_b", slug="topic-b", executions=executions)
        stub_c, name_c = _make_stub(name="topic_c", slug="topic-c")
        module.TOPIC_DEFINITIONS = (
            module.TopicDefinition(slug="topic-c", module=name_c),
            module.TopicDefinition(slug="topic-b", module=name_b),
            module.TopicDefinition(slug="topic-a", module=name_a),
        )

        reports_root = tmp_path / "reports"
        timestamp = "2025-12-04T12:30:00+00:00"
        exit_code = module.run(
            [
                "--repo-root",
                str(tmp_path),
                "--reports-root",
                str(reports_root),
                "--timestamp",
                timestamp,
                "--log-level",
                "ERROR",
                "--include",
                "topic-a",
                "--include",
                "topic-b",
            ]
        )
        assert exit_code == 0
        assert stub_a._calls  # type: ignore[attr-defined]
        assert stub_b._calls  # type: ignore[attr-defined]
        assert not stub_c._calls  # type: ignore[attr-defined]
        assert executions == ["topic-a", "topic-b"]

        run_slug = "20251204-1230"
        manifest_path = reports_root / module.META_VIEWER / module.META_TOPIC / run_slug / "manifest.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        statuses = {entry["slug"]: entry["status"] for entry in manifest["topics"]}
        assert statuses == {"topic-a": "succeeded", "topic-b": "succeeded", "topic-c": "skipped"}
        artifact_dirs = {
            entry["slug"]: entry["artifact_dir"] for entry in manifest["topics"] if entry["artifact_dir"]
        }
        assert "topic-a" in artifact_dirs
        assert artifact_dirs["topic-a"].endswith(str(Path(stub_a.HEALTHVIEW_TOPIC) / run_slug))  # type: ignore[attr-defined]
        summary_path = manifest_path.with_name("summary.md")
        assert summary_path.is_file()
        telemetry_path = manifest_path.with_name("telemetry.json")
        assert telemetry_path.is_file()
    finally:
        module.TOPIC_DEFINITIONS = original_definitions


def test_stop_on_first_failure_blocks_remaining(tmp_path):
    module = _reload_module()
    (tmp_path / ".repo_studios").mkdir()
    original_definitions = module.TOPIC_DEFINITIONS
    try:
        failing_stub, failing_name = _make_stub(name="fail", slug="topic-a", exit_code=1)
        skipped_stub, skipped_name = _make_stub(name="skipped", slug="topic-b")
        module.TOPIC_DEFINITIONS = (
            module.TopicDefinition(slug="topic-a", module=failing_name),
            module.TopicDefinition(slug="topic-b", module=skipped_name),
        )

        reports_root = tmp_path / "reports"
        exit_code = module.run(
            [
                "--repo-root",
                str(tmp_path),
                "--reports-root",
                str(reports_root),
                "--timestamp",
                "2025-12-04T12:45:00+00:00",
                "--log-level",
                "ERROR",
            ]
        )
        assert exit_code == 1
        assert failing_stub._calls  # type: ignore[attr-defined]
        assert not skipped_stub._calls  # type: ignore[attr-defined]

        manifest_path = next(reports_root.rglob("manifest.json"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        status_map = {entry["slug"]: entry["status"] for entry in manifest["topics"]}
        assert status_map == {"topic-a": "failed", "topic-b": "skipped"}
        reason_map = {entry["slug"]: entry["message"] for entry in manifest["topics"]}
        assert reason_map["topic-b"] == "skipped after earlier failure"
    finally:
        module.TOPIC_DEFINITIONS = original_definitions


def test_keep_going_runs_all_topics_after_failure(tmp_path):
    module = _reload_module()
    (tmp_path / ".repo_studios").mkdir()
    original_definitions = module.TOPIC_DEFINITIONS
    try:
        first_stub, first_name = _make_stub(name="first", slug="topic-a", exit_code=1)
        second_stub, second_name = _make_stub(name="second", slug="topic-b")
        module.TOPIC_DEFINITIONS = (
            module.TopicDefinition(slug="topic-a", module=first_name),
            module.TopicDefinition(slug="topic-b", module=second_name),
        )

        reports_root = tmp_path / "reports"
        exit_code = module.run(
            [
                "--repo-root",
                str(tmp_path),
                "--reports-root",
                str(reports_root),
                "--timestamp",
                "2025-12-04T12:50:00+00:00",
                "--log-level",
                "ERROR",
                "--keep-going",
            ]
        )
        assert exit_code == 1
        assert first_stub._calls  # type: ignore[attr-defined]
        assert second_stub._calls  # type: ignore[attr-defined]

        manifest_path = next(reports_root.rglob("manifest.json"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        status_map = {entry["slug"]: entry["status"] for entry in manifest["topics"]}
        assert status_map == {"topic-a": "failed", "topic-b": "succeeded"}
    finally:
        module.TOPIC_DEFINITIONS = original_definitions
