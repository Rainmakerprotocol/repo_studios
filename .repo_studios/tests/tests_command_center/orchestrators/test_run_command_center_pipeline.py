from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from command_center.scripts.orchestrators import run_command_center_pipeline as pipeline


def _stub_loader(target_dir: Path, inventory_dir: Path, analysis_ts: str, scan_ts: str):
    def loader(script_path: Path, module_name: str):
        if "generate_commandview_inventory" in module_name:
            def run_inventory(argv: list[str] | None = None) -> int:
                timestamp = datetime(2025, 12, 1, 12, 34, tzinfo=timezone.utc).strftime("%Y%m%d-%H%M")
                run_file = inventory_dir / f"{target_dir.name}_commandview_{timestamp}.json"
                inventory_dir.mkdir(parents=True, exist_ok=True)
                run_file.write_text(json.dumps({"slug": target_dir.name}), encoding="utf-8")
                return 0

            return run_inventory

        if "generate_function_analysis" in module_name:
            def run_analysis(argv: list[str] | None = None) -> int:
                analysis_dir = inventory_dir
                analysis_path = analysis_dir / f"{target_dir.name}_analysis-{analysis_ts}.json"
                analysis_dir.mkdir(parents=True, exist_ok=True)
                analysis_path.write_text(json.dumps({"inventory": target_dir.name}), encoding="utf-8")
                return 0

            return run_analysis

        if "scan_duplicates" in module_name:
            def run_scan(argv: list[str] | None = None) -> int:
                matrix_path = inventory_dir / f"{target_dir.name}_duplicate_matrix-{scan_ts}.json"
                summary_path = inventory_dir / f"{target_dir.name}_duplicate_summary-{scan_ts}.md"
                matrix_path.write_text(json.dumps({"matrix": []}), encoding="utf-8")
                summary_path.write_text("# summary\n", encoding="utf-8")
                return 0

            return run_scan

        raise AssertionError(f"Unexpected module requested: {module_name}")

    return loader


def test_pipeline_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / ".reports" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)
    inventory_dir = target_dir / f"{target_dir.name}_index"

    loader = _stub_loader(target_dir, inventory_dir, "20251201-1234", "20251201-1234")
    monkeypatch.setattr(pipeline, "_load_run_function", loader)

    exit_code = pipeline.run([
        str(target_dir),
        "--repo-root",
        str(repo_root),
        "--log-level",
        "ERROR",
    ])

    assert exit_code == 0
    assert (inventory_dir / f"{target_dir.name}_commandview_20251201-1234.json").exists()
    assert (inventory_dir / f"{target_dir.name}_analysis-20251201-1234.json").exists()
    assert (inventory_dir / f"{target_dir.name}_duplicate_matrix-20251201-1234.json").exists()
    assert (inventory_dir / f"{target_dir.name}_duplicate_summary-20251201-1234.md").exists()


def test_pipeline_stops_on_inventory_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "reports" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)

    def loader(script_path: Path, module_name: str):
        if "generate_commandview_inventory" in module_name:
            return lambda argv=None: 2
        if "generate_function_analysis" in module_name or "scan_duplicates" in module_name:
            return lambda argv=None: pytest.fail("Downstream steps should not execute on inventory failure")
        raise AssertionError

    monkeypatch.setattr(pipeline, "_load_run_function", loader)

    exit_code = pipeline.run([
        str(target_dir),
        "--repo-root",
        str(repo_root),
        "--log-level",
        "ERROR",
    ])

    assert exit_code == 2


def test_pipeline_rejects_missing_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "missing"

    exit_code = pipeline.run([
        str(target_dir),
        "--repo-root",
        str(repo_root),
    ])

    assert exit_code == 1


def test_pipeline_errors_when_inventory_artifact_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "reports" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)

    def loader(script_path: Path, module_name: str):
        if "generate_commandview_inventory" in module_name:
            return lambda argv=None: 0
        if "generate_function_analysis" in module_name or "scan_duplicates" in module_name:
            return lambda argv=None: pytest.fail("Pipeline should stop before downstream steps on missing inventory artifact")
        raise AssertionError

    monkeypatch.setattr(pipeline, "_load_run_function", loader)

    exit_code = pipeline.run([
        str(target_dir),
        "--repo-root",
        str(repo_root),
        "--log-level",
        "ERROR",
    ])

    assert exit_code == 1


def test_pipeline_propagates_analysis_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "reports" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)
    inventory_dir = target_dir / f"{target_dir.name}_index"

    def loader(script_path: Path, module_name: str):
        if "generate_commandview_inventory" in module_name:
            def run_inventory(argv=None):
                slug = "20251201-1234"
                inventory_dir.mkdir(parents=True, exist_ok=True)
                (inventory_dir / f"{target_dir.name}_commandview_{slug}.json").write_text("{}", encoding="utf-8")
                return 0

            return run_inventory

        if "generate_function_analysis" in module_name:
            return lambda argv=None: 5

        if "scan_duplicates" in module_name:
            return lambda argv=None: pytest.fail("Scan should not run when analysis fails")

        raise AssertionError

    monkeypatch.setattr(pipeline, "_load_run_function", loader)

    exit_code = pipeline.run([
        str(target_dir),
        "--repo-root",
        str(repo_root),
        "--log-level",
        "ERROR",
    ])

    assert exit_code == 5


def test_pipeline_detects_missing_scan_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "reports" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)
    inventory_dir = target_dir / f"{target_dir.name}_index"

    def loader(script_path: Path, module_name: str):
        if "generate_commandview_inventory" in module_name:
            def run_inventory(argv=None):
                slug = "20251201-1234"
                inventory_dir.mkdir(parents=True, exist_ok=True)
                (inventory_dir / f"{target_dir.name}_commandview_{slug}.json").write_text("{}", encoding="utf-8")
                return 0

            return run_inventory

        if "generate_function_analysis" in module_name:
            def run_analysis(argv=None):
                (inventory_dir / f"{target_dir.name}_analysis-20251201-1234.json").write_text("{}", encoding="utf-8")
                return 0

            return run_analysis

        if "scan_duplicates" in module_name:
            def run_scan(argv=None):
                # produce only one of the expected artifacts to trigger the error path
                (inventory_dir / f"{target_dir.name}_duplicate_matrix-20251201-1234.json").write_text("{}", encoding="utf-8")
                return 0

            return run_scan

        raise AssertionError

    monkeypatch.setattr(pipeline, "_load_run_function", loader)

    exit_code = pipeline.run([
        str(target_dir),
        "--repo-root",
        str(repo_root),
        "--log-level",
        "ERROR",
    ])

    assert exit_code == 1


def test_pipeline_rejects_file_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    target_file = repo_root / "reports.txt"
    target_file.write_text("placeholder", encoding="utf-8")

    exit_code = pipeline.run([
        str(target_file),
        "--repo-root",
        str(repo_root),
    ])

    assert exit_code == 1


def test_build_paths_rejects_outside_repo(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    outside = repo_root.parent / "elsewhere"

    args = pipeline.argparse.Namespace(target=str(outside), repo_root=str(repo_root), log_level="INFO")

    with pytest.raises(ValueError):
        pipeline.build_paths(args)


def test_build_paths_accepts_prefixed_relative_target(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    target_dir = repo_root / "reports" / "demo"
    target_dir.mkdir(parents=True, exist_ok=True)

    args = pipeline.argparse.Namespace(target="/.reports/demo", repo_root=str(repo_root), log_level="INFO")

    paths = pipeline.build_paths(args)

    assert paths.target == (repo_root / ".reports" / "demo").resolve()


def test_load_run_function_requires_existing_script(tmp_path: Path) -> None:
    script_path = tmp_path / "missing.py"

    with pytest.raises(FileNotFoundError):
        pipeline._load_run_function(script_path, "tests.missing_module")


def test_load_run_function_requires_callable_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script_path = tmp_path / "module.py"
    script_path.write_text("VALUE = 1\n", encoding="utf-8")

    try:
        with pytest.raises(RuntimeError):
            pipeline._load_run_function(script_path, "command_center.tests.module_without_run")
    finally:
        sys.modules.pop("command_center.tests.module_without_run", None)