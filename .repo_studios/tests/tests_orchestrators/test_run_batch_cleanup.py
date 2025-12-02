"""Tests for the run_batch_cleanup orchestrator modernization."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Callable, Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "orchestrators" / "run_batch_cleanup.py"


def _load_module() -> ModuleType:
    module_name = f"run_batch_cleanup_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _prepare_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / "metrics_storage" / "storage").mkdir(parents=True)
    for candidate in (
        repo_root / "agents" / "core" / "monitoring",
        repo_root / "agents" / "interface" / "chainlit",
    ):
        candidate.mkdir(parents=True)
    (repo_root / ".markdownlint.json").write_text("{}\n", encoding="utf-8")
    standards_doc = repo_root / ".repo_studios" / "docs" / "project_tree_overview.md"
    standards_doc.parent.mkdir(parents=True)
    standards_doc.write_text(
        "\n".join(
            [
                "# Repo Standards",
                "intro text",
                "<!-- tree:begin -->",
                "Updated: 01/01/2000_00:00:00",
                "```text",
                "repo/",
                "```",
                "<!-- tree:end -->",
            ]
        ),
        encoding="utf-8",
    )
    return repo_root


def _stub_executor(
    return_codes: Sequence[int] | None = None,
) -> tuple[Callable[[Sequence[str]], subprocess.CompletedProcess[str]], list[list[str]]]:
    calls: list[list[str]] = []
    codes = list(return_codes or [])

    def _run(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        returncode = codes.pop(0) if codes else 0
        return subprocess.CompletedProcess(cmd, returncode, stdout="ok\n", stderr="")

    return _run, calls


def _patch_common(
    module: ModuleType,
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    use_legacy: bool = True,
) -> None:
    monkeypatch.setattr(module, "PROJECT_ROOT", repo_root)
    monkeypatch.setattr(module, "RUFF_CONFIG", repo_root / ".repo_studios" / "ruff_clean.toml")
    monkeypatch.setattr(module, "DEFAULT_OUTPUT_BASE", Path(".reports/run_batch_cleanup"))
    monkeypatch.delenv("BATCH_CLEAN_ONLY", raising=False)
    monkeypatch.delenv("BATCH_CLEAN_TARGET_DIR", raising=False)
    monkeypatch.delenv("BATCH_CLEAN_TARGETS", raising=False)
    monkeypatch.delenv("BATCH_CLEAN_NO_PYTEST", raising=False)
    if use_legacy:
        monkeypatch.setenv(module.LEGACY_ENV_FLAG, "1")
    else:
        monkeypatch.delenv(module.LEGACY_ENV_FLAG, raising=False)


def test_redirects_to_topic_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()
    _patch_common(module, repo_root, monkeypatch, use_legacy=False)

    captured: dict[str, list[str]] = {}

    def _fake_run(args: Sequence[str] | None = None) -> int:
        captured["argv"] = list(args or [])
        return 0

    monkeypatch.setattr(module.hygiene_topic_runner, "run", _fake_run)

    result = module.run([
        "--output-base",
        "./custom",
        "--artifacts-to-keep",
        "3",
        "--verbose",
    ])

    assert result["status"] == "success"
    assert result["exit_code"] == 0
    redirect = result["redirect"]
    assert redirect["target"] == module.TOPIC_TARGET
    forwarded = redirect["argv"]
    assert forwarded == captured["argv"]
    assert forwarded[0] == "--repo-root"
    assert forwarded[1] == str(repo_root)
    assert "--trigger-batch-cleanup" in forwarded
    assert "--skip-import-graph" in forwarded
    assert "--skip-typecheck" in forwarded
    assert "--cleanup-artifacts-to-keep" in forwarded
    assert "3" in forwarded
    assert "--batch-cleanup-output-base" in forwarded
    assert "./custom" in forwarded
    # verbose should promote log-level to DEBUG for the redirect
    assert "--log-level" in forwarded
    assert "DEBUG" in forwarded


def test_run_creates_structured_bundle_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()
    _patch_common(module, repo_root, monkeypatch)

    executor, calls = _stub_executor()
    monkeypatch.setattr(module, "_run_subprocess", executor)
    monkeypatch.setattr(module.shutil, "which", lambda name: "npx" if name == "npx" else None)

    output_base = repo_root / "out"
    result = module.run(["--output-base", str(output_base), "--log-level", "INFO"])

    assert result["status"] == "success"
    summary_path = Path(result["summary_path"])
    log_path = Path(result["log_path"])
    assert summary_path.exists()
    assert log_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "success"
    labels = [step["label"] for step in summary["steps"]]
    assert labels == [
        "Ruff format",
        "Ruff check --fix",
        "markdownlint --fix (npx)",
        "markdownlint check (npx)",
        "Mypy",
        "Pytest",
    ]
    assert all(step["status"] == "success" for step in summary["steps"])
    assert summary["tree_refresh"]["updated"] is True
    assert not result["pruned"]
    standards_doc = repo_root / ".repo_studios" / "docs" / "project_tree_overview.md"
    refreshed = standards_doc.read_text(encoding="utf-8")
    assert "Updated:" in refreshed and "metrics_storage/" in refreshed
    latest_summary = output_base / "latest_cleanup_summary.json"
    latest_log = output_base / "latest_cleanup_log.txt"
    latest_bundle = output_base / "latest_bundle_summary.json"
    assert latest_summary.exists()
    assert latest_log.exists()
    assert latest_bundle.exists()
    assert len(calls) == 6


def test_run_markdown_mode_without_tooling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()
    _patch_common(module, repo_root, monkeypatch)

    executor, calls = _stub_executor()
    monkeypatch.setattr(module, "_run_subprocess", executor)
    monkeypatch.setattr(module.shutil, "which", lambda name: None)

    output_base = repo_root / "reports"
    result = module.run(["--mode", "markdown", "--output-base", str(output_base)])

    assert result["status"] == "success"
    summary = json.loads(Path(result["summary_path"]).read_text(encoding="utf-8"))
    assert summary["steps"]
    assert summary["steps"][0]["status"] == "skipped"
    assert "markdownlint skipped" in summary["notes"][0]
    assert "mode=markdown" in summary["notes"][1]
    assert not calls


def test_run_prunes_old_bundles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()
    _patch_common(module, repo_root, monkeypatch)

    executor, _ = _stub_executor()
    monkeypatch.setattr(module, "_run_subprocess", executor)
    monkeypatch.setattr(module.shutil, "which", lambda name: "npx" if name == "npx" else None)

    output_base = repo_root / "reports"
    keep = 2
    old_dirs = [
        output_base / "run_batch_cleanup-2024-01-01_000000",
        output_base / "run_batch_cleanup-2024-01-02_000000",
        output_base / "run_batch_cleanup-2024-01-03_000000",
    ]
    for directory in old_dirs:
        directory.mkdir(parents=True)
        (directory / "cleanup_summary.json").write_text("{}\n", encoding="utf-8")
        (directory / "cleanup_log.txt").write_text("log\n", encoding="utf-8")
        (directory / "bundle_summary.json").write_text("{}\n", encoding="utf-8")

    result = module.run(["--output-base", str(output_base), "--artifacts-to-keep", str(keep), "--log-level", "INFO"])

    pruned = result["pruned"]
    assert pruned
    remaining = [path for path in output_base.iterdir() if path.is_dir()]
    assert len(remaining) == keep


def test_run_reports_command_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()
    _patch_common(module, repo_root, monkeypatch)

    executor, calls = _stub_executor(return_codes=[1])
    monkeypatch.setattr(module, "_run_subprocess", executor)
    monkeypatch.setattr(module.shutil, "which", lambda name: "npx" if name == "npx" else None)

    output_base = repo_root / "reports"
    result = module.run(["--output-base", str(output_base)])

    assert result["status"] == "failed"
    summary = json.loads(Path(result["summary_path"]).read_text(encoding="utf-8"))
    assert summary["status"] == "failed"
    assert summary["steps"][0]["status"] == "failed"
    assert len(summary["steps"]) == 1
    assert len(calls) == 1
