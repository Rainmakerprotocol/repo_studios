from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.tests_command_center.monkey_patch.helpers import load_scan_producer_module


def test_structured_artifacts(tmp_path: Path) -> None:
    mod = load_scan_producer_module()

    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
    src_dir = repo_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "monkey_patch.py").write_text(
        """
import requests
requests.adapters.DEFAULT_POOLSIZE = 1

import os
os.environ[\"EXAMPLE_FLAG\"] = \"1\"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--context-lines",
            "1",
            "--keep",
            "5",
            "--timestamp",
            "20250101-0000",
        ]
    )
    assert payload["status"] == "ok"
    assert payload["run_timestamp"] == "20250101-0000"

    base_dir = repo_root / ".repo_studios" / "reports" / "healthview" / "producer_reports" / "monkey_patches"
    run_dir = base_dir / "20250101-0000"
    assert run_dir.exists()

    manifest_path = run_dir / "manifest.json"
    summary_path = run_dir / "summary.md"
    telemetry_path = run_dir / "telemetry.json"
    assert manifest_path.exists()
    assert summary_path.exists()
    assert telemetry_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "monkey_patches"
    assert manifest["run_timestamp"] == "20250101-0000"
    assert manifest["status"] == "ok"
    assert "catalog" in manifest
    assert "inputs" in manifest

    payload_obj = manifest.get("payload", {})
    assert payload_obj.get("scan_root") == "src"
    assert payload_obj.get("files_scanned") == 1
    assert int(payload_obj.get("total_findings", 0) or 0) >= 2

    summary = payload_obj.get("summary", {})
    by_category = summary.get("by_category", {})
    assert by_category.get("global_env_mutation") == 1
    assert int(by_category.get("attribute_reassignment_on_import", 0) or 0) >= 1

    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["viewer"] == "healthview"
    assert telemetry["topic"] == "monkey_patches"
    assert telemetry["run_timestamp"] == "20250101-0000"
    metrics = telemetry.get("metrics", {})
    assert int(metrics.get("files_scanned", 0) or 0) == 1
    assert int(metrics.get("total_findings", 0) or 0) >= 2

    # Canonical producers must not emit mutable latest pointers or legacy aliases.
    assert not (base_dir / "latest").exists()
    assert not (repo_root / ".repo_studios" / "monkey_patch").exists()


def test_prune_history(tmp_path: Path) -> None:
    mod = load_scan_producer_module()

    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
    src_dir = repo_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "first.py").write_text(
        "import builtins\nbuiltins.open = lambda *args, **kwargs: None\n",
        encoding="utf-8",
    )

    base_dir = repo_root / ".repo_studios" / "reports" / "healthview" / "producer_reports" / "monkey_patches"

    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--keep",
            "1",
            "--timestamp",
            "20250101-0000",
        ]
    )

    # Second run should prune history down to a single directory.
    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--keep",
            "1",
            "--timestamp",
            "20250101-0001",
        ]
    )

    run_dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    assert run_dirs[0].name == "20250101-0001"
    assert not (base_dir / "latest").exists()
    assert not (repo_root / ".repo_studios" / "monkey_patch").exists()


def test_resolve_run_timestamp_validation(tmp_path: Path) -> None:
    mod = load_scan_producer_module()

    now = datetime(2025, 1, 2, 3, 4, tzinfo=UTC)
    assert mod._resolve_run_timestamp(override=None, now=now) == "20250102-0304"
    assert mod._resolve_run_timestamp(override="20250102-0304", now=now) == "20250102-0304"

    with pytest.raises(ValueError):
        mod._resolve_run_timestamp(override="2025-01-02", now=now)


def test_scan_file_detects_multiple_categories_and_git_blame(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = load_scan_producer_module()

    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
    src_dir = repo_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    target = src_dir / "sample.py"
    target.write_text(
        """
import builtins
import logging
import os
import sys
from unittest.mock import patch

import requests

sys.modules[\"example\"] = object()
del sys.modules[\"example\"]

builtins.open = lambda *args, **kwargs: None
os.environ[\"FLAG\"] = \"1\"
os.environ.update({\"FLAG2\": \"2\"})

logging.getLogger = lambda *args, **kwargs: None
requests.adapters.DEFAULT_POOLSIZE = 1
setattr(requests.adapters, \"DEFAULT_POOLSIZE\", 2)

@patch(\"requests.get\")
def test_something(mock_get):
    return None
""".strip()
        + "\n",
        encoding="utf-8",
    )

    def _fake_run(argv: list[str], **_kwargs: object):
        # Minimal porcelain blame output
        stdout = (
            "deadbeef1234567890abcdef1234567890abcdef 1 1 1\n"
            "author Test Author\n"
            "author-mail <test@example.com>\n"
            "author-time 1735689600\n"
            "author-tz +0000\n"
            "committer Test Author\n"
            "committer-mail <test@example.com>\n"
            "committer-time 1735689600\n"
            "committer-tz +0000\n"
            "summary Initial commit\n"
            "filename sample.py\n"
            "\timport builtins\n"
        )
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)

    findings = mod.scan_file(
        repo_root=repo_root,
        file_path=target,
        project_pkgs={"src"},
        context_lines=1,
        strict=False,
    )
    categories = {f.category for f in findings}

    assert mod.CATEGORY_SYS_MODULES in categories
    assert mod.CATEGORY_BUILTINS in categories
    assert mod.CATEGORY_GLOBAL_ENV in categories
    assert mod.CATEGORY_SINGLETON_REBIND in categories
    assert mod.CATEGORY_ATTRIBUTE_REASSIGNMENT in categories
    assert mod.CATEGORY_SETATTR in categories
    assert mod.CATEGORY_TEST_PATCH_MISUSE in categories

    # Git blame parsing should not raise.
    author, commit, date_iso = mod.add_git_blame(repo_root, target, 1)
    assert author == "Test Author"
    # author-time 1735689600 -> 2025-01-01 00:00:00 UTC
    assert date_iso is not None and date_iso.startswith("2025-01-01")
    assert commit == "deadbeef1234567890abcdef1234567890abcdef"


def test_scan_file_strict_mode_raises_on_parse_error(tmp_path: Path) -> None:
    mod = load_scan_producer_module()

    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True)
    src_dir = repo_root / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    target = src_dir / "broken.py"
    target.write_text("def oops(:\n", encoding="utf-8")

    with pytest.raises(Exception):
        mod.scan_file(
            repo_root=repo_root,
            file_path=target,
            project_pkgs=set(),
            context_lines=1,
            strict=True,
        )


def test_compose_manifest_telemetry_and_summary_round_trip(tmp_path: Path) -> None:
    mod = load_scan_producer_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir(parents=True)
    (repo_root / ".repo_studios").mkdir()
    scan_root = repo_root / "src"
    scan_root.mkdir(parents=True)
    paths = mod.Paths(repo_root=repo_root, scan_root=scan_root, output_dir=repo_root / "out")
    run_timestamp = "20250101-0000"
    timestamp = datetime(2025, 1, 1, tzinfo=UTC)

    bundle_dir = paths.output_dir / run_timestamp
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = bundle_dir / "manifest.json"
    summary_path = bundle_dir / "summary.md"
    telemetry_path = bundle_dir / "telemetry.json"

    scan_options = mod.ScanOptions(
        project_packages=set(),
        exclude_dirs=set(),
        exclude_globs=set(),
        context_lines=1,
        with_git=False,
        strict=False,
        keep=1,
    )

    manifest = mod.compose_manifest(
        paths=paths,
        options=scan_options,
        run_timestamp=run_timestamp,
        timestamp=timestamp,
        generated_at=timestamp.isoformat(),
        bundle_dir=bundle_dir,
        findings=[],
        files_scanned=0,
        parse_errors=0,
        duration_ms=5,
    )

    assert manifest["viewer"] == "healthview"
    assert manifest["topic"] == "monkey_patches"
    assert manifest["run_timestamp"] == run_timestamp
    assert manifest["status"] == "ok"

    telemetry = mod.compose_telemetry(
        manifest=manifest,
        run_timestamp=run_timestamp,
        generated_at=timestamp.isoformat(),
    )
    assert telemetry["run_timestamp"] == run_timestamp
    assert telemetry["metrics"]["total_findings"] == 0

    markdown = mod.render_summary_markdown(manifest)
    assert "Monkey Patch Scan Report" in markdown
