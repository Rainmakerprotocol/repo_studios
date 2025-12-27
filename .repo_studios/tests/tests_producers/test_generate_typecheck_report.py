import json
import importlib.util
import os
import sys
from pathlib import Path
from typing import Callable

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_typecheck_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_typecheck_report", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("TYPECHECK_TARGETS", raising=False)
    monkeypatch.delenv("TYPECHECK_STRICT", raising=False)
    monkeypatch.delenv("HEALTH_TYPECHECK_FAST", raising=False)


def _write_pyproject(tmp_path: Path, targets: list[str]) -> None:
    content = "[tool.mypy]\nfiles = [\n"
    content += "".join(f'    "{target}",\n' for target in targets)
    content += "]\n"
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")


def _run_with_module(tmp_path: Path, monkeypatch, runner: Callable[[Path, list[str]], tuple[str, int]]):
    module = _load_module()
    args = [
        "--repo-root",
        str(tmp_path),
        "--output-dir",
        str(Path(".repo_studios/reports/producer_reports")),
        "--timestamp",
        "2025-10-22T12:34:56+00:00",
        "--artifacts-to-keep",
        "2",
        "--log-level",
        "INFO",
    ]
    monkeypatch.setattr(module, "_run_mypy", runner)
    monkeypatch.setattr(module, "_get_mypy_version", lambda _repo_root: "mypy 1.11.0")
    module.main(args)

    slug = "20251022-1234"
    out_dir = tmp_path / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "typecheck_report"
    run_dir = out_dir / slug
    return module, out_dir, run_dir, slug


def test_typecheck_success(tmp_path: Path, monkeypatch):
    (tmp_path / ".repo_studios").mkdir()
    _write_pyproject(tmp_path, ["src"])
    (tmp_path / "src").mkdir()

    topic_dir = tmp_path / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "typecheck_report"
    topic_dir.mkdir(parents=True, exist_ok=True)
    older = topic_dir / "20251020-0101"
    oldest = topic_dir / "20251019-0101"
    older.mkdir()
    oldest.mkdir()
    os.utime(oldest, (1, 1))
    os.utime(older, (2, 2))

    def runner(repo_root: Path, invocation: list[str]):
        assert repo_root == tmp_path
        if invocation[-1] == "--version":
            return "mypy 1.11.0", 0
        return "Success: no issues found in 1 source file", 0

    module, out_dir, run_dir, slug = _run_with_module(tmp_path, monkeypatch, runner)

    manifest_path = run_dir / "manifest.json"
    summary_path = run_dir / "summary.md"
    telemetry_path = run_dir / "telemetry.json"
    assert all(path.exists() for path in (manifest_path, summary_path, telemetry_path))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == "healthview"
    assert manifest["topic"] == "typecheck_report"
    assert manifest["status"] == "ok"
    assert manifest["summary"]["error_count"] == 0
    assert manifest["summary"]["files_with_issues"] == 0
    assert manifest["summary"]["paths_checked"] == ["src"]
    assert manifest["run_timestamp"] == slug
    assert "Success: no issues" in manifest.get("raw_output", "")
    assert "# Typecheck Report" in summary_path.read_text(encoding="utf-8")

    remaining_runs = sorted(node.name for node in out_dir.iterdir() if node.is_dir())
    assert set(remaining_runs) == {slug, "20251020-0101"}
    assert "20251019-0101" not in remaining_runs


def test_typecheck_failure(tmp_path: Path, monkeypatch):
    (tmp_path / ".repo_studios").mkdir()
    _write_pyproject(tmp_path, ["pkg"])
    (tmp_path / "pkg").mkdir()

    error_output = (
        "pkg/module.py:7: error: Incompatible types [assignment]\n"
        "pkg/module.py:7: note: Revealed type is 'builtins.str'\n"
        "Found 1 error in 1 file (checked 1 source file)"
    )

    def runner(repo_root: Path, invocation: list[str]):
        if invocation[-1] == "--version":
            return "mypy 1.11.0", 0
        return error_output, 1

    module, out_dir, run_dir, slug = _run_with_module(tmp_path, monkeypatch, runner)

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "error"
    assert manifest["summary"]["error_count"] == 1
    assert manifest["summary"]["files_with_issues"] == 1
    assert manifest["error_samples"][0]["path"] == "pkg/module.py"
    assert manifest["error_samples"][0]["line"] == 7
    assert manifest["error_samples"][0]["code"] == "assignment"
    assert slug == manifest["run_timestamp"]
    assert "Found 1 error" in manifest.get("raw_output", "")


def test_typecheck_skips_when_no_targets(tmp_path: Path, monkeypatch):
    (tmp_path / ".repo_studios").mkdir()
    _write_pyproject(tmp_path, [])

    def runner(repo_root: Path, invocation: list[str]):
        raise AssertionError("mypy should not run when no targets are configured")

    module, out_dir, run_dir, slug = _run_with_module(tmp_path, monkeypatch, runner)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "skipped"
    assert "skipping mypy execution" in manifest.get("notes", "")
    assert manifest["summary"]["paths_checked"] == []
    assert slug == manifest["run_timestamp"]


def test_typecheck_missing_target_output_is_skipped(tmp_path: Path, monkeypatch):
    (tmp_path / ".repo_studios").mkdir()
    _write_pyproject(tmp_path, ["src"])

    def runner(repo_root: Path, invocation: list[str]):
        message = (
            "usage: mypy [-h] [-v] [-V] [more options; see below]\n"
            "            [-m MODULE] [-p PACKAGE] [-c PROGRAM_TEXT] [files ...]\n"
            "mypy: error: Missing target module, package, files, or command.\n"
        )
        return message, 2

    module, out_dir, run_dir, _slug = _run_with_module(tmp_path, monkeypatch, runner)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "skipped"
    assert "missing target module" in manifest.get("notes", "").lower()
    assert manifest["summary"]["error_count"] == 0
    assert manifest["summary"]["files_with_issues"] == 0
