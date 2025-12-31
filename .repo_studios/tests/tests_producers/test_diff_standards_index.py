from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "diff_standards_index.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("diff_standards_index", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_index(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")


def test_diff_detects_changes_and_writes_artifacts(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()
    output_dir = repo_root / mod.DEFAULT_OUTPUT_DIR

    old_index = {
        "integrity_hash": "abc123",
        "rules": [
            {
                "id": "STD-001",
                "severity": "medium",
                "summary": "Old summary",
                "rationale": "baseline",
                "applies_to": ["python"],
                "category_ids": ["lint"],
            },
            {
                "id": "STD-002",
                "severity": "low",
                "summary": "Keep",
                "rationale": "",
                "applies_to": [],
                "category_ids": [],
            },
        ],
    }
    new_index = {
        "integrity_hash": "def456",
        "rules": [
            {
                "id": "STD-001",
                "severity": "high",
                "summary": "New summary",
                "rationale": "baseline",
                "applies_to": ["python"],
                "category_ids": ["lint"],
            },
            {
                "id": "STD-003",
                "severity": "medium",
                "summary": "Added",
                "rationale": "new",
                "applies_to": ["python"],
                "category_ids": ["lint"],
            },
        ],
    }

    old_path = repo_root / "repo_standards_index_old.yaml"
    new_path = repo_root / "repo_standards_index_new.yaml"
    _write_index(old_path, old_index)
    _write_index(new_path, new_index)

    exit_code = mod.main(
        [
            str(old_path),
            str(new_path),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--run-timestamp",
            "20240101-0000",
            "--artifacts-to-keep",
            "5",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1

    bundle_dir = output_dir / "20240101-0000"
    assert bundle_dir.is_dir()

    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "standards_index_diff"
    assert manifest["run_timestamp"] == "20240101-0000"
    assert manifest["status"] == "ok"

    telemetry = json.loads((bundle_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["status"] == "changes"
    assert telemetry["metrics"]["change_count"] == 4
    assert telemetry["metrics"]["integrity_hash_changed"] is True
    assert telemetry["metrics"]["should_fail"] is True
    changes = telemetry["payload"]["changes"]
    assert {
        "id": "STD-001",
        "kind": "severity_changed",
        "from": "medium",
        "to": "high",
    } in changes
    assert {"id": "STD-002", "kind": "removed"} in changes
    assert {"id": "STD-003", "kind": "added"} in changes

    markdown = (bundle_dir / "summary.md").read_text(encoding="utf-8")
    assert "# Standards Index Diff Report" in markdown
    assert "| STD-001 | severity_changed" in markdown
    assert telemetry["payload"]["summary"]["severity_changed"] == 1


def test_no_changes_returns_zero_and_prunes(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()
    output_dir = repo_root / mod.DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    base_dir = output_dir
    stale_dir = base_dir / "20231231-2359"
    stale_dir.mkdir(parents=True, exist_ok=True)
    (stale_dir / "manifest.json").write_text("{}\n", encoding="utf-8")

    index_payload = {
        "integrity_hash": "zzz",
        "rules": [
            {
                "id": "STD-010",
                "severity": "low",
                "summary": "Baseline",
                "rationale": "",
                "applies_to": [],
                "category_ids": [],
            }
        ],
    }

    old_path = repo_root / "a.yaml"
    new_path = repo_root / "b.yaml"
    _write_index(old_path, index_payload)
    _write_index(new_path, index_payload)

    exit_code = mod.main(
        [
            str(old_path),
            str(new_path),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--run-timestamp",
            "20240201-1200",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0

    run_dir = output_dir / "20240201-1200"
    assert run_dir.is_dir()
    assert not stale_dir.exists()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["status"] == "no_changes"
    assert telemetry["metrics"]["change_count"] == 0
    assert telemetry["metrics"]["should_fail"] is False

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "ok"
