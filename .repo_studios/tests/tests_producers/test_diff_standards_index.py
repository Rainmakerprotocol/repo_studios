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
    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "standards_index_diff_reports"

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
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "5",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1

    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "changes"
    assert report["should_fail"] is True
    assert report["change_count"] == 4
    assert report["integrity_hash_changed"] is True
    assert {
        "id": "STD-001",
        "kind": "severity_changed",
        "from": "medium",
        "to": "high",
    } in report["changes"]
    assert {"id": "STD-002", "kind": "removed"} in report["changes"]
    assert {"id": "STD-003", "kind": "added"} in report["changes"]

    markdown = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Standards Index Diff Report" in markdown
    assert "| STD-001 | severity_changed" in markdown

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "status=changes" in log_text

    raw_json = json.loads((run_dir / "raw.json").read_text(encoding="utf-8"))
    assert raw_json["summary"]["severity_changed"] == 1

    raw_txt = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert "severity_changed" in raw_txt

    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_report.log").is_file()
    assert (output_dir / "latest_raw.json").is_file()
    assert (output_dir / "latest_raw.txt").is_file()


def test_no_changes_returns_zero_and_prunes(tmp_path: Path) -> None:
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "standards_index_diff_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_dir = output_dir / f"{mod.RUN_PREFIX}-20231231_235959"
    stale_dir.mkdir(parents=True, exist_ok=True)
    (stale_dir / "report.json").write_text("{}\n", encoding="utf-8")

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
            "--timestamp",
            "2024-02-01T12:00:00+00:00",
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0

    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240201_120000"
    assert run_dir.is_dir()
    assert not stale_dir.exists()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "no_changes"
    assert report["change_count"] == 0
    assert report["should_fail"] is False

    raw_txt = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert "changes" in raw_txt

    assert (output_dir / "latest_report.json").read_text(encoding="utf-8")
    assert (output_dir / "latest_raw.json").is_file()
    assert (output_dir / "latest_raw.txt").is_file()
