from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "command_center"
    / "scripts"
    / "aggregators"
    / "generate_automation_manifest.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_automation_manifest", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_automation_manifest_bundle(tmp_path: Path) -> None:
    mod = _load_module()

    files_payload = {
        "updated": [
            {"path": "src/module_a.py", "duplicate_groups": ["dup-1"]},
            "src/module_b.py",
        ],
        "skipped": ["docs/README.md"],
        "conflicted": [],
    }
    files_file = tmp_path / "files.json"
    files_file.write_text(json.dumps(files_payload), encoding="utf-8")

    tests_payload = {
        "library_integration": {
            "status": "passed",
            "duration_seconds": 90.0,
            "artifacts": ["reports/library.xml"],
        }
    }
    tests_file = tmp_path / "tests.json"
    tests_file.write_text(json.dumps(tests_payload), encoding="utf-8")

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    allowed_targets = config_dir / "allowed_targets.yaml"
    allowed_targets.write_text("targets: []\n", encoding="utf-8")
    guardrail_config = config_dir / "automation_config.yaml"
    guardrail_config.write_text(
        (
            "metadata:\n"
            "  version: 1\n"
            "allow_list:\n"
            "  source: allowed_targets.yaml\n"
            "constraints:\n"
            "  max_files_per_run: 10\n"
            "  max_groups_per_run: 5\n"
            "  require_lock_check: true\n"
        ),
        encoding="utf-8",
    )

    output_dir = tmp_path / "reports" / "automation_runs"

    exit_code = mod.main(
        [
            "--repo-root",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
            "--tests-file",
            str(tests_file),
            "--files-file",
            str(files_file),
            "--run-id",
            "2025-11-02T19-30-00Z",
            "--baseline-sha",
            "abcdef123456",
            "--target",
            "library",
            "--lines-touched",
            "120",
            "--files-changed",
            "2",
            "--duplicate-groups-resolved",
            "1",
            "--runtime-seconds",
            "18.5",
            "--notes",
            "dry run",
            "--timestamp",
            "2025-11-02T19:30:00+00:00",
            "--operator",
            "genet",
            "--dry-run",
            "--guardrail-config",
            str(guardrail_config),
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0

    run_dir = output_dir / f"{mod.RUN_STEM}-20251102_193000"
    manifest_path = run_dir / mod.MANIFEST_FILENAME
    metrics_path = run_dir / mod.METRICS_FILENAME
    assert manifest_path.is_file()
    assert metrics_path.is_file()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_payload["baseline_sha"] == "abcdef123456"
    assert manifest_payload["files"]["updated"][0]["duplicate_groups"] == ["dup-1"]
    assert manifest_payload["metrics_summary"]["files_changed"] == 2
    assert manifest_payload["metrics_summary_path"] == mod.METRICS_FILENAME
    guardrails = manifest_payload["guardrails"]
    assert guardrails["max_files_per_run"] == 10
    assert guardrails["files_considered"] == 3
    assert guardrails["config_path"].endswith("automation_config.yaml")

    manifest_pointer = output_dir / mod.MANIFEST_POINTER
    metrics_pointer = output_dir / mod.METRICS_POINTER
    assert manifest_pointer.is_file()
    assert metrics_pointer.is_file()
    assert manifest_pointer.read_text(encoding="utf-8") == manifest_path.read_text(encoding="utf-8")
    assert metrics_pointer.read_text(encoding="utf-8") == metrics_path.read_text(encoding="utf-8")


def test_manifest_files_changed_mismatch(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    mod = _load_module()

    files_payload = {"updated": ["src/module_a.py"], "skipped": [], "conflicted": []}
    files_file = tmp_path / "files.json"
    files_file.write_text(json.dumps(files_payload), encoding="utf-8")

    tests_payload = {
        "library_integration": {
            "status": "passed",
            "duration_seconds": 10.0,
        }
    }
    tests_file = tmp_path / "tests.json"
    tests_file.write_text(json.dumps(tests_payload), encoding="utf-8")

    output_dir = tmp_path / "reports"

    with caplog.at_level("ERROR"):
        exit_code = mod.main(
            [
                "--repo-root",
                str(tmp_path),
                "--output-dir",
                str(output_dir),
                "--tests-file",
                str(tests_file),
                "--files-file",
                str(files_file),
                "--run-id",
                "run-mismatch",
                "--baseline-sha",
                "deadbeef",
                "--target",
                "library",
                "--lines-touched",
                "10",
                "--files-changed",
                "2",
                "--duplicate-groups-resolved",
                "0",
                "--runtime-seconds",
                "5.0",
                "--log-level",
                "ERROR",
            ]
        )

    assert exit_code == 1
    assert any("Files changed mismatch" in message for message in caplog.messages)
