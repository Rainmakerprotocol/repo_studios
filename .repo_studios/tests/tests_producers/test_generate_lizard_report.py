from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_lizard_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_lizard_report", _MODULE_PATH)
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

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"

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
    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC / "20240101-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["schema_version"] == 1
    assert telemetry["metrics"]["status"] == "issues"
    assert telemetry["metrics"]["issue_count"] == 1
    assert telemetry["metrics"]["files_scanned"] == 1
    assert telemetry["generated_utc"].startswith("2024-01-01T00:00:00")

    payload_out = telemetry["payload"]
    assert payload_out["schema_version"] == 1
    assert payload_out["status"] == "issues"
    assert payload_out["issue_count"] == 1
    assert payload_out["files_scanned"] == 1
    assert payload_out["generated_utc"].startswith("2024-01-01T00:00:00")
    offenders = payload_out["offenders"]
    assert len(offenders) == 1
    offender = offenders[0]
    assert offender["path"] == str(target_dir / "module.py")
    assert offender["name"] == "complex_fn"
    assert offender["cyclomatic_complexity"] == 30
    assert offender["length"] == 120
    # Helper now records threshold deltas for tooling; ensure they are non-negative
    assert offender["ccn_over_limit"] >= 0
    assert offender["length_over_limit"] >= 0

    markdown = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Lizard Complexity Report" in markdown
    assert "complex_fn" in markdown

    log_text = payload_out["log_text"]
    assert "status=issues" in log_text
    assert "complex_fn" in log_text
    assert "delta_ccn" in log_text

    raw_txt = payload_out["raw"]["text"]
    assert "complex_fn" in raw_txt
    assert "[stderr]" not in raw_txt

    assert not any(path.name.startswith("latest_") for path in output_dir.rglob("*") if path.is_file())


def test_no_targets_and_pruning(tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    topic_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC
    topic_dir.mkdir(parents=True, exist_ok=True)

    stale_dirs = [
        topic_dir / "20240101-0000",
        topic_dir / "20240115-0000",
    ]
    for path in stale_dirs:
        path.mkdir(parents=True, exist_ok=True)
        (path / "telemetry.json").write_text("{}\n", encoding="utf-8")

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
    run_dir = topic_dir / "20240203-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    report = telemetry["payload"]
    assert report["status"] == "no_targets"
    assert report["issue_count"] == 0
    assert "No targets resolved" in report["notes"]

    log_text = report["log_text"]
    assert "status=no_targets" in log_text

    raw_txt = report["raw"]["text"]
    assert raw_txt == ""

    remaining = sorted(
        path.name for path in topic_dir.iterdir() if path.is_dir()
    )
    assert remaining == [
        "20240115-0000",
        "20240203-0000",
    ]


def test_rejects_newline_arguments(tmp_path: Path):
    mod = _load_module()

    offender = mod.Offender(
        path="demo.py",
        name="fn",
        cyclomatic_complexity=20,
        length=200,
        start_line=10,
        end_line=20,
    )
    payload = offender.to_payload(max_ccn=15, max_length=80, rank=1)
    assert payload["start_line"] == 10
    assert payload["end_line"] == 20

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "src").mkdir()

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-03-03T00:00:00+00:00",
            "--targets",
            "src",
            "--extra-args",
            "bad\narg",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / mod.VIEWER_SLUG / mod.TOPIC / "20240303-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["metrics"]["status"] == "error"
    assert "Unsafe command argument" in telemetry["payload"]["notes"]

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "failed"
