"""Tests for the modernized standards summarizer."""

from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "summarizers" / "summarize_standards.py"
FIXED_TIMESTAMP = "2025-12-02T12:00:00+00:00"


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
    scripts_dir = repo_root / ".repo_studios" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    index_path = scripts_dir / "repo_standards_index.yaml"
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


def test_run_emits_healthview_bundle(tmp_path: Path) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    pending_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_pending.yaml"
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text("line1\nline2\n", encoding="utf-8")
    index_path = _write_index(repo_root, pending_path)

    output_dir = repo_root / "artifacts"
    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--index-path",
            str(index_path),
            "--pending-path",
            str(pending_path),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            FIXED_TIMESTAMP,
            "--label",
            "sync",
        ]
    )

    assert result["status"] == "ok"
    run_dir = Path(result["run_dir"])
    assert run_dir.exists()

    artifacts = {name: Path(path) for name, path in result["artifacts"].items()}
    json_path = artifacts["manifest.json"]
    markdown_path = artifacts["summary.md"]
    telemetry_path = artifacts["telemetry.json"]

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["viewer"] == module.VIEWER_SLUG
    assert payload["topic"] == module.TOPIC_SLUG
    assert payload["metrics"]["rule_count"] == 2
    assert payload["markdown_rule_sample"] == ["markdown-auto-001"]
    assert payload["run_slug"] == "20251202-1200"

    markdown_content = markdown_path.read_text(encoding="utf-8")
    assert "# Standards Overview" in markdown_content
    assert "Rules: 2" in markdown_content
    assert "markdown-auto-001" in markdown_content

    # HOP base package: telemetry.json must exist
    assert telemetry_path.exists()


def test_resolve_index_path_falls_back_to_legacy(tmp_path: Path) -> None:
    module = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    candidate_path = repo_root / ".repo_studios" / "scripts" / "repo_standards_index.yaml"
    legacy_path = (
        repo_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "standards_index_reports"
        / "latest_index.yaml"
    )
    legacy_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_payload = {"rules": []}
    legacy_path.write_text(yaml.safe_dump(legacy_payload, sort_keys=False), encoding="utf-8")

    paths = module.Paths(
        repo_root=repo_root,
        index_path=candidate_path,
        pending_path=legacy_path,
        output_dir=repo_root / "out",
    )
    options = module.Options(
        label="summary",
        log_level="INFO",
        artifacts_to_keep=1,
        run_timestamp=datetime.now(timezone.utc),
    )

    resolved = module._resolve_index_path(paths, options)  # type: ignore[attr-defined]

    assert resolved == legacy_path.resolve()