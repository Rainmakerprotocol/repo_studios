from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "analyze_standards_index_gaps.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "analyze_standards_index_gaps",
        _MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_index(path: Path) -> None:
    payload = textwrap.dedent(
        """
        schema_version: 1
        rules:
          - id: STD-001
            summary: Encourage consistent linting across modules.
        """
    ).strip()
    path.write_text(payload + "\n", encoding="utf-8")


def _write_categories(path: Path, sources: list[Path]) -> None:
    body = ["sources:"]
    for src in sources:
        body.append(f"  - path: {src}")
    body.append("")
    path.write_text("\n".join(body), encoding="utf-8")


def test_basic_shim_delegates_to_command_center():
    mod = _load_module()
    impl = mod.COMMAND_CENTER_MODULE

    assert mod.run is impl.run
    assert mod.main is impl.main
    assert mod.RUN_PREFIX == impl.RUN_PREFIX
    assert mod.PATHS_CONFIG is impl.PATHS_CONFIG
    assert mod.COMMAND_CENTER_SCRIPT_PATH.is_file()


def test_structured_artifacts_created(tmp_path):
    mod = _load_module()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".repo_studios").mkdir(parents=True, exist_ok=True)

    docs = workspace / "docs"
    docs.mkdir()
    doc = docs / "std-project-guidelines.md"
    doc.write_text(
        """
        - Avoid direct database access for command handlers.
        - Enforce sandbox boundaries before running external tools.
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    index_path = workspace / "repo_standards_index.yaml"
    _write_index(index_path)

    categories_path = workspace / "standards_categories.yaml"
    _write_categories(categories_path, [doc])

    output_dir = workspace / ".repo_studios" / "reports" / "producer_reports" / "standards_gap_reports"
    legacy_json = workspace / "legacy_gap.json"

    result = mod.run(
        [
            "--repo-root",
            str(workspace),
            "--index-path",
            str(index_path),
            "--categories-path",
            str(categories_path),
            "--output-dir",
            str(output_dir),
            "--json",
            str(legacy_json),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    run_dir = Path(result["run_dir"])
    assert run_dir == output_dir / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0000"
    assert run_dir.is_dir()

    manifest = json.loads(Path(result["manifest_json"]).read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == mod.VIEWER_SLUG
    assert manifest["topic"] == mod.TOPIC_SLUG
    assert manifest["run_timestamp"] == "20240101-0000"
    assert "catalog" in manifest
    assert "inputs" in manifest

    telemetry = json.loads(Path(result["telemetry_json"]).read_text(encoding="utf-8"))
    assert telemetry["viewer_slug"] == mod.VIEWER_SLUG
    assert telemetry["topic"] == mod.TOPIC_SLUG
    assert "metrics" in telemetry

    summary = result["summary"]
    possible_keys = {
        str(doc),
        str(doc.relative_to(workspace)),
        str(doc.relative_to(workspace)).replace("\\", "/"),
    }
    key = next((candidate for candidate in possible_keys if candidate in telemetry["sources"]), None)
    assert key is not None
    assert summary["total_candidates"] == 2
    assert summary["sources_with_candidates"] == 1
    assert summary["top_source_candidates"] == 2
    assert summary["scanned_sources"] == 1
    assert telemetry["metrics"]["total_candidates"] == 2
    assert len(telemetry["sources"][key]) == 2
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "summary.md").is_file()
    assert (run_dir / "telemetry.json").is_file()

    legacy = json.loads(Path(result["legacy_json"]).read_text(encoding="utf-8"))
    assert legacy["metrics"]["total_candidates"] == summary["total_candidates"]


def test_pruning_keeps_recent_runs(tmp_path):
    mod = _load_module()
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    docs = workspace / "docs"
    docs.mkdir()
    doc = docs / "std-guidance.md"
    doc.write_text("- Avoid stale dependencies in production.\n", encoding="utf-8")

    index_path = workspace / "repo_standards_index.yaml"
    _write_index(index_path)

    categories_path = workspace / "standards_categories.yaml"
    _write_categories(categories_path, [doc])

    output_root = workspace / ".repo_studios" / "reports" / "producer_reports" / "standards_gap_reports"
    topic_dir = output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG
    topic_dir.mkdir(parents=True, exist_ok=True)

    stale_dirs = [
        topic_dir / "20230101-0000",
        topic_dir / "20230201-0000",
        topic_dir / "20230301-0000",
    ]
    for path in stale_dirs:
        path.mkdir(parents=True, exist_ok=True)
        (path / "telemetry.json").write_text("{}", encoding="utf-8")

    mod.run(
        [
            "--repo-root",
            str(workspace),
            "--index-path",
            str(index_path),
            "--categories-path",
            str(categories_path),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-02-03T00:00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    expected = {"20230301-0000", "20240203-0000"}
    remaining = {path.name for path in topic_dir.iterdir() if path.is_dir()}
    assert remaining == expected


def test_command_center_helpers_cover_basic_paths(monkeypatch, tmp_path):
    from command_center.scripts.producers import analyze_standards_index_gaps as producer

    assert producer._timestamp_slug(datetime(2024, 1, 1, 0, 0)) == "20240101-0000"

    monkeypatch.setenv("MAKELEVEL", "1")
    assert producer._detect_trigger_type() == "make"
    monkeypatch.delenv("MAKELEVEL", raising=False)

    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert producer._detect_trigger_type() == "ci"
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert producer._detect_trigger_type() == "cli"

    monkeypatch.setenv("GITHUB_ACTOR", "alice")
    assert producer._detect_requested_by() == "alice"
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)

    bad_index = tmp_path / "bad_index.yaml"
    bad_index.write_text("- not-a-mapping\n", encoding="utf-8")
    try:
        producer.load_index(bad_index)
    except RuntimeError as exc:
        assert "must be a mapping" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected load_index to reject non-mapping YAML")


def test_command_center_load_index_rejects_missing_file(tmp_path):
    from command_center.scripts.producers import analyze_standards_index_gaps as producer

    missing = tmp_path / "missing.yaml"
    try:
        producer.load_index(missing)
    except RuntimeError as exc:
        assert "Standards index not found" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected missing file to raise")


def test_command_center_ensure_index_path_prefers_legacy_snapshot(tmp_path, caplog):
    from command_center.scripts.producers import analyze_standards_index_gaps as producer

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    legacy = repo_root / producer.LEGACY_INDEX_PATH
    legacy.parent.mkdir(parents=True)
    legacy.write_text("sources: []\n", encoding="utf-8")

    paths = producer.Paths(
        repo_root=repo_root,
        output_dir=repo_root / "out",
        index_path=repo_root / "missing_index.yaml",
        categories_path=repo_root / "missing_categories.yaml",
    )
    logger = producer.logging.getLogger("test")
    updated = producer._ensure_index_path(paths, logger)
    assert updated.index_path == legacy.resolve()


def test_command_center_detect_git_sha_prefers_env(monkeypatch, tmp_path):
    from command_center.scripts.producers import analyze_standards_index_gaps as producer

    monkeypatch.setenv("GITHUB_SHA", "deadbeef")
    assert producer._detect_git_sha(tmp_path) == "deadbeef"
