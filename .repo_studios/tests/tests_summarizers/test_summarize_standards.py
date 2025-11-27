"""Tests for the summarize_standards telemetry helper."""

from __future__ import annotations

import importlib.util
import logging
import sys
import uuid
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "summarizers" / "summarize_standards.py"


def _load_module():
    module_name = f"summarize_standards_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load summarizer module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_index(repo_root: Path, pending_path: Path) -> Path:
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
        "rules": [
            {"id": "STD001"},
            {"id": "markdown-auto-001"},
        ],
        "metadata": {
            "extraction": {
                "extracted_count": 1,
                "auto_accept": False,
                "pending_file": str(pending_path),
            }
        },
    }
    index_path.write_text(yaml.safe_dump(index_payload, sort_keys=False), encoding="utf-8")
    return index_path


def test_summarize_logs_counts(tmp_path: Path, caplog) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    pending_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_pending.yaml"
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text("line1\nline2\n", encoding="utf-8")
    index_path = _write_index(repo_root, pending_path)

    caplog.set_level(logging.INFO)
    result = module.summarize("summary", index_path, pending_path)

    assert result == 0
    log_output = "\n".join(caplog.messages)
    assert "rules=2" in log_output
    assert "extracted_count=1" in log_output
    assert "markdown-rule-count=1" in log_output
    assert "pending_lines=2" in log_output


def test_resolve_index_path_falls_back_to_legacy(tmp_path: Path, caplog, monkeypatch) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    candidate_path = repo_root / ".repo_studios" / "reports" / "producer_reports" / "standards_index_reports" / "latest_index.yaml"
    legacy_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_index.yaml"
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_payload = {"rules": []}
    legacy_path.write_text(yaml.safe_dump(legacy_payload, sort_keys=False), encoding="utf-8")

    monkeypatch.chdir(repo_root)
    caplog.set_level(logging.WARNING)
    resolved = module._resolve_index_path("summary", candidate_path)  # type: ignore[attr-defined]

    assert resolved == legacy_path.resolve()
    assert any("falling back to legacy snapshot" in message for message in caplog.messages)