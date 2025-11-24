import json
import importlib.util
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
        str(Path(".repo_studios/reports/producer_reports/typecheck_reports")),
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

    slug = "20251022_123456"
    out_dir = tmp_path / ".repo_studios" / "reports" / "producer_reports" / "typecheck_reports"
    run_dir = out_dir / f"typecheck-{slug}"
    return module, out_dir, run_dir, slug


def test_typecheck_success(tmp_path: Path, monkeypatch):
    _write_pyproject(tmp_path, ["src"])
    (tmp_path / "src").mkdir()

    legacy_dir = tmp_path / ".repo_studios" / "reports" / "producer_reports" / "typecheck_reports"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    (legacy_dir / "typecheck-20251020_010101").mkdir()
    (legacy_dir / "typecheck-20251019_010101").mkdir()

    def runner(repo_root: Path, invocation: list[str]):
        assert repo_root == tmp_path
        if invocation[-1] == "--version":
            return "mypy 1.11.0", 0
        return "Success: no issues found in 1 source file", 0

    module, out_dir, run_dir, slug = _run_with_module(tmp_path, monkeypatch, runner)

    report_json = run_dir / "report.json"
    report_md = run_dir / "report.md"
    log_txt = run_dir / "log.txt"
    raw_txt = run_dir / "raw.txt"
    assert all(path.exists() for path in (report_json, report_md, log_txt, raw_txt))

    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["status"] == "ok"
    assert payload["summary"]["error_count"] == 0
    assert payload["summary"]["files_with_issues"] == 0
    assert payload["summary"]["paths_checked"] == ["src"]
    assert payload["timestamp"] == slug

    latest_json = out_dir / "latest_report.json"
    latest_md = out_dir / "latest_report.md"
    latest_log = out_dir / "latest_report.log"
    latest_raw = out_dir / "latest_raw.txt"

    assert latest_json.read_text(encoding="utf-8") == report_json.read_text(encoding="utf-8")
    assert latest_md.read_text(encoding="utf-8") == report_md.read_text(encoding="utf-8")
    assert latest_log.read_text(encoding="utf-8") == log_txt.read_text(encoding="utf-8")
    assert latest_raw.read_text(encoding="utf-8") == raw_txt.read_text(encoding="utf-8")

    remaining_runs = sorted(node.name for node in out_dir.iterdir() if node.is_dir())
    assert set(remaining_runs) == {f"typecheck-{slug}", "typecheck-20251020_010101"}
    assert "typecheck-20251019_010101" not in remaining_runs


def test_typecheck_failure(tmp_path: Path, monkeypatch):
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

    payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "error"
    assert payload["summary"]["error_count"] == 1
    assert payload["summary"]["files_with_issues"] == 1
    assert payload["error_samples"][0]["path"] == "pkg/module.py"
    assert payload["error_samples"][0]["line"] == 7
    assert payload["error_samples"][0]["code"] == "assignment"
    assert slug in payload["timestamp"]

    raw_txt = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert "Found 1 error" in raw_txt
