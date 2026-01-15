import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "utilities" / "refresh_mypy_baselines.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("refresh_mypy_baselines", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _repo_paths(tmp_path: Path):
    repo_root = tmp_path / "repo"
    output_dir = (
        repo_root
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "rawview"
        / "mypy_baselines"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    return repo_root, output_dir


@pytest.fixture(autouse=True)
def _cleanup_env(monkeypatch):
    monkeypatch.delenv("PYTHONPATH", raising=False)


def test_refresh_success(tmp_path: Path, monkeypatch):
    module = _load_module()
    repo_root, output_dir = _repo_paths(tmp_path)

    calls: list[list[str]] = []

    def fake_invoke(root: Path, command):
        calls.append(list(command))
        return "success output", 0

    monkeypatch.setattr(module, "_invoke_mypy", fake_invoke)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-11-27T12:00:00+00:00",
            "--log-level",
            "CRITICAL",
        ]
    )

    assert result["status"] == "ok"
    assert len(calls) == 2
    run_dir = Path(result["run_dir"])
    assert run_dir.exists()

    baseline = run_dir / "mypy_agents_full.txt"
    assert baseline.exists()
    content = baseline.read_text(encoding="utf-8")
    assert "# Refreshed: 2025-11-27_120000" in content

    assert not (output_dir / "latest_mypy_agents_full.txt").exists()
    assert not (output_dir / "latest_bundle_summary.json").exists()

    summary_path = run_dir / "bundle_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    assert "agents_full" in summary["targets_meta"]


def test_refresh_failure_skips_pointer(tmp_path: Path, monkeypatch):
    module = _load_module()
    repo_root, output_dir = _repo_paths(tmp_path)

    responses = [
        ("first ok", 0),
        ("second failed", 1),
    ]

    def fake_invoke(root: Path, command):
        return responses.pop(0)

    monkeypatch.setattr(module, "_invoke_mypy", fake_invoke)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-11-27T13:00:00+00:00",
            "--log-level",
            "CRITICAL",
        ]
    )

    assert result["status"] == "error"

    assert not (output_dir / "latest_mypy_agents_full.txt").exists()
    assert not (output_dir / "latest_mypy_monitoring_full.txt").exists()

    run_dir = Path(result["run_dir"])
    err_file = run_dir / "mypy_monitoring_full_error.txt"
    assert err_file.exists()
    assert "second failed" in err_file.read_text(encoding="utf-8")


def test_refresh_custom_target(tmp_path: Path, monkeypatch):
    module = _load_module()
    repo_root, output_dir = _repo_paths(tmp_path)

    def fake_invoke(root: Path, command):
        return ("custom ok", 0)

    monkeypatch.setattr(module, "_invoke_mypy", fake_invoke)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2025-11-27T14:00:00+00:00",
            "--target",
            "docs=docs:docs_baseline.txt",
            "--log-level",
            "CRITICAL",
        ]
    )

    assert result["status"] == "ok"
    run_dir = Path(result["run_dir"])

    baseline = run_dir / "docs_baseline.txt"
    assert baseline.exists()
    assert "custom ok" in baseline.read_text(encoding="utf-8")

    assert not (output_dir / "latest_docs_baseline.txt").exists()

    bundle_json = json.loads((run_dir / "bundle_summary.json").read_text(encoding="utf-8"))
    assert "docs" in bundle_json["targets_meta"]