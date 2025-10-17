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
    sys.modules[spec.name] = mod  # make visible during exec
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def test_fast_mode_curates_targets(tmp_path: Path, monkeypatch):
    # Arrange: simulate pyproject mypy files with mixed prefixes
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
        [tool.mypy]
        files = [
            "api",
            "agents/core",
            "agents/interface/chainlit",
            "agents/experimental",
            "external/vendor",
        ]
        """,
        encoding="utf-8",
    )
    # Create allowed paths so fallback logic can validate existence
    for p in ["api", "agents/core", "agents/interface/chainlit"]:
        (tmp_path / p).mkdir(parents=True, exist_ok=True)

    # Ensure no explicit override present and fast mode is on
    monkeypatch.delenv("TYPECHECK_TARGETS", raising=False)
    monkeypatch.setenv("HEALTH_TYPECHECK_FAST", "1")
    monkeypatch.setenv("TYPECHECK_STRICT", "0")

    class FakeProc:
        def __init__(self, stdout: str, stderr: str = "", returncode: int = 0):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False, timeout=None):  # noqa: ARG001
        # mypy --version call
        if "--version" in cmd:
            return FakeProc(stdout="mypy 1.11.1")
        # Normal mypy run: pretend success to keep artifacts simple
        return FakeProc(stdout="Success: no issues found in 3 source files\n", returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    # Act
    mod = load_typecheck_module()
    out_base = tmp_path / "typecheck"
    ts = "2099-01-01_0101"
    rc = mod.main(["--repo-root", str(tmp_path), "--output-base", str(out_base), "--timestamp", ts])

    # Assert
    assert rc == 0
    payload = json.loads((out_base / ts / "report.json").read_text(encoding="utf-8"))
    checked = payload["checked_paths"]
    # Only curated prefixes should remain
    assert checked == [
        "api",
        "agents/core",
        "agents/interface/chainlit",
    ]
