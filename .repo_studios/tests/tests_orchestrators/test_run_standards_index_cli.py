"""Tests for the run_standards_index_cli orchestrator modernization."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Sequence

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "orchestrators" / "run_standards_index_cli.py"


def _load_module() -> ModuleType:
    module_name = f"run_standards_index_cli_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load orchestrator module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_index(repo_root: Path) -> Path:
    reports_dir = (
        repo_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "standards_index_reports"
    )
    reports_dir.mkdir(parents=True, exist_ok=True)
    index_path = reports_dir / "latest_index.yaml"
    index_payload = {
        "integrity_hash": "abc123",
        "rules": [
            {
                "id": "STD001",
                "summary": "Ensure hashing is salted",
                "rationale": "Protect against rainbow tables",
                "severity": "info",
                "category_ids": ["security", "python_coding"],
                "applies_to": ["python"],
                "source": "docs/standards/security.md",
            },
            {
                "id": "STD002",
                "summary": "Avoid hard-coded credentials",
                "rationale": "Secrets must not ship",
                "severity": "error",
                "category_ids": ["security"],
                "applies_to": ["python", "infrastructure"],
                "source": "docs/standards/security.md",
            },
        ],
    }
    index_path.write_text(yaml.safe_dump(index_payload, sort_keys=False), encoding="utf-8")
    return index_path


def _enable_legacy(module: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(module.LEGACY_ENV_FLAG, "1")


def test_redirects_to_topic_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_index(repo_root)
    output_dir = repo_root / "out"

    monkeypatch.delenv(module.LEGACY_ENV_FLAG, raising=False)

    captured: dict[str, list[str]] = {}

    def fake_run(args: Sequence[str] | None = None) -> int:
        captured["argv"] = list(args or [])
        return 0

    monkeypatch.setattr(module.standards_topic_runner, "run", fake_run)

    result = module.run([
        "--repo-root",
        str(repo_root),
        "--output-dir",
        str(output_dir),
        "stats",
    ])

    assert result["redirect"]["target"] == module.TOPIC_TARGET
    assert result["redirect"]["status"] == "success"
    redirected_args = captured["argv"]
    assert redirected_args[0:2] == ["--repo-root", str(repo_root.resolve())]
    for flag in (
        "--index-output-dir",
        "--index-path",
        "--artifacts-to-keep",
        "--index-artifacts-to-keep",
        "--gap-artifacts-to-keep",
        "--diff-artifacts-to-keep",
        "--prompt-artifacts-to-keep",
    ):
        assert flag in redirected_args
    assert result["exit_code"] == 0
    assert result["summary"]["severity_counts"] == {"info": 1, "error": 1}


def test_list_command_writes_structured_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    index_path = _write_index(repo_root)
    assert index_path.exists()
    output_dir = repo_root / "out"

    _enable_legacy(module, monkeypatch)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--log-level",
            "INFO",
            "list",
            "--severity",
            "error",
        ]
    )

    assert result["exit_code"] == 0
    assert result["stdout_lines"] == ["STD002"]

    run_dir = Path(result["run_dir"])
    assert run_dir.is_dir()

    bundle_summary = json.loads((run_dir / "bundle_summary.json").read_text(encoding="utf-8"))
    assert bundle_summary["items_returned"] == 1
    assert bundle_summary["command"] == "list"

    latest_report = output_dir / "latest_report.json"
    assert latest_report.exists()
    report_payload = json.loads(latest_report.read_text(encoding="utf-8"))
    assert report_payload["summary"]["items_returned"] == 1
    assert report_payload["results"]["rule_ids"] == ["STD002"]


def test_show_missing_rule_returns_exit_three(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    index_path = _write_index(repo_root)
    assert index_path.exists()
    output_dir = repo_root / "out"

    _enable_legacy(module, monkeypatch)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "show",
            "--id",
            "UNKNOWN",
        ]
    )

    assert result["exit_code"] == 3
    assert result["summary"]["overall_status"] == "failed"
    assert "error" in result["summary"]

    run_dir = Path(result["run_dir"])
    assert run_dir.is_dir()
    report_payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_payload["error"] == "rule not found: UNKNOWN"


def test_stats_command_reports_severity_counts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    index_path = _write_index(repo_root)
    assert index_path.exists()
    output_dir = repo_root / "out"

    _enable_legacy(module, monkeypatch)

    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "stats",
        ]
    )

    assert result["exit_code"] == 0
    assert len(result["stdout_lines"]) == 4

    report_payload = json.loads((Path(result["report_json"]).read_text(encoding="utf-8")))
    stats = report_payload["results"]["stats"]
    assert stats["rules_total"] == 2
    assert stats["severity_counts"] == {"error": 1, "info": 1}

    stdout_pointer = output_dir / "latest_stdout.txt"
    assert stdout_pointer.exists()
    stdout_text = stdout_pointer.read_text(encoding="utf-8")
    assert "rules_total: 2" in stdout_text
