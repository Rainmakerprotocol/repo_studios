from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "producers"
    / "generate_lizard_report.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "generate_lizard_report", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_structured_artifacts_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    target_dir = repo_root / "src"
    target_dir.mkdir()

    payload = [
        {
            "filename": str(target_dir / "module.py"),
            "function_list": [
                {
                    "name": "complex_fn",
                    "cyclomatic_complexity": 30,
                    "length": 120,
                },
                {
                    "name": "simple_fn",
                    "cyclomatic_complexity": 5,
                    "length": 20,
                },
            ],
        }
    ]

    def fake_run(cmd, capture_output, text):
        assert cmd[-1] == str(target_dir.resolve())
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    output_dir = (
        repo_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "lizard_reports"
    )

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--targets",
            "src",
            "--artifacts-to-keep",
            "5",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["status"] == "issues"
    assert report["issue_count"] == 1
    assert report["files_scanned"] == 1
    assert report["generated_utc"].startswith("2024-01-01T00:00:00")
    assert report["offenders"] == [
        {
            "path": str(target_dir / "module.py"),
            "name": "complex_fn",
            "cyclomatic_complexity": 30,
            "length": 120,
        }
    ]

    markdown = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Lizard Complexity Report" in markdown
    assert "complex_fn" in markdown

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "status=issues" in log_text
    assert "offenders:" in log_text

    raw_json = json.loads((run_dir / "raw.json").read_text(encoding="utf-8"))
    assert raw_json == payload

    raw_txt = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert "complex_fn" in raw_txt
    assert "[stderr]" not in raw_txt

    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_report.log").is_file()
    assert (output_dir / "latest_raw.json").is_file()
    assert (output_dir / "latest_raw.txt").is_file()


def test_no_targets_and_pruning(tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    output_dir = (
        repo_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "lizard_reports"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_dirs = [
        output_dir / f"{mod.RUN_PREFIX}-20240101_000000",
        output_dir / f"{mod.RUN_PREFIX}-20240115_000000",
    ]
    for path in stale_dirs:
        path.mkdir(parents=True, exist_ok=True)
        (path / "report.json").write_text("{}\n", encoding="utf-8")

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-02-03T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240203_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "no_targets"
    assert report["issue_count"] == 0
    assert "No targets resolved" in report["notes"]

    log_text = (output_dir / "latest_report.log").read_text(encoding="utf-8")
    assert "status=no_targets" in log_text

    raw_txt = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert raw_txt == ""
    assert not (run_dir / "raw.json").exists()
    assert not (output_dir / "latest_raw.json").exists()

    remaining = sorted(
        path.name
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)
    )
    assert remaining == [
        f"{mod.RUN_PREFIX}-20240115_000000",
        f"{mod.RUN_PREFIX}-20240203_000000",
    ]
