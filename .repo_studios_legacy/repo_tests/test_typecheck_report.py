import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_typecheck_module():
    path = Path(".repo_studios/typecheck_report.py").resolve()
    spec = importlib.util.spec_from_file_location("typecheck_report", str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Ensure module is visible in sys.modules during execution so dataclasses
    # with postponed annotations can resolve the module name.
    sys.modules[spec.name] = mod  # type: ignore[index]
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def test_typecheck_report_with_mocked_mypy_output(tmp_path: Path, monkeypatch):
    # Arrange: create an output base under tmp and point the script at repo root
    out_base = tmp_path / "typecheck"
    ts = "2099-01-01_0000"

    # Mock mypy execution by pointing TYPECHECK_TARGETS to an empty dir and intercepting mypy call
    # Instead, set TYPECHECK_TARGETS to current dir; we will monkeypatch subprocess.run used by the script
    class FakeProc:
        def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False, timeout=None):  # noqa: ARG001
        # Simulate a mypy output with 2 errors in 1 file
        sample = (
            "agents/core/jarvis_api.py:10: error: Missing type annotation for self [no-untyped-def]\n"
            "agents/core/jarvis_api.py:42: error: Incompatible return value type [return-value]\n"
            "Found 2 errors in 1 file (checked 1 source file)\n"
        )
        if "--version" in cmd:
            return FakeProc(stdout="mypy 1.11.1")
        return FakeProc(stdout=sample, stderr="", returncode=1)

    monkeypatch.setenv("TYPECHECK_TARGETS", "agents/core/jarvis_api.py")
    monkeypatch.setenv("TYPECHECK_STRICT", "0")
    monkeypatch.setenv("HEALTH_TYPECHECK_FAST", "1")
    monkeypatch.setenv("PYTHONPATH", str(Path.cwd()))
    monkeypatch.setattr(subprocess, "run", fake_run)

    # Act
    mod = load_typecheck_module()
    rc = mod.main(["--repo-root", ".", "--output-base", str(out_base), "--timestamp", ts])

    # Assert
    assert rc == 0
    run_dir = out_base / ts
    assert run_dir.is_dir()
    raw = (run_dir / "raw.txt").read_text(encoding="utf-8")
    assert "Found 2 errors" in raw
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "ERROR"
    assert report["total_errors"] == 2
    assert report["files_with_issues"] == 1
    assert isinstance(report["error_samples"], list) and len(report["error_samples"]) >= 2
    md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Typecheck Report" in md
    assert "Top Issues" in md
