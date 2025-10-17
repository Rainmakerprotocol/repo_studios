import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def load_lizard_module():
    path = Path(".repo_studios/lizard_report.py").resolve()
    spec = importlib.util.spec_from_file_location("lizard_report", str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # type: ignore[index]
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


class FakeProc:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_lizard_report_records_offenders(tmp_path: Path, monkeypatch):
    ts = "2099-01-01_0000"
    out_base = tmp_path / "lizard"

    payload = [
        {
            "filename": "agents/core/example.py",
            "function_list": [
                {"name": "foo", "cyclomatic_complexity": 21, "length": 90},
                {"name": "bar", "cyclomatic_complexity": 5, "length": 20},
            ],
        },
        {
            "filename": "api/routes/sample.py",
            "function_list": [
                {"name": "baz", "cyclomatic_complexity": 16, "length": 50},
            ],
        },
    ]

    def fake_run(cmd, cwd=None, capture_output=False, text=False):  # noqa: ARG001
        return FakeProc(stdout=json.dumps(payload), stderr="", returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    mod = load_lizard_module()
    argv = [
        "lizard_report.py",
        "--repo-root",
        ".",
        "--output-base",
        str(out_base),
        "--timestamp",
        ts,
        "--max-ccn",
        "15",
        "--max-length",
        "80",
        "--targets",
        "agents/core",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    rc = mod.main()

    assert rc == 0
    out_dir = out_base / ts
    assert out_dir.is_dir()

    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "issues"
    assert report["issue_count"] == 2
    assert report["files_scanned"] == 2
    assert "lizard" in report["command_str"]

    md = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "Top Offenders" in md
    assert "agents/core/example.py" in md
    assert "api/routes/sample.py" in md

    raw_json_path = out_dir / "raw.json"
    assert raw_json_path.exists()
    raw_data = json.loads(raw_json_path.read_text(encoding="utf-8"))
    assert isinstance(raw_data, list) and len(raw_data) == 2


def test_lizard_report_handles_missing_module(tmp_path: Path, monkeypatch):
    ts = "2099-01-01_0101"
    out_base = tmp_path / "lizard"

    def fake_run(cmd, cwd=None, capture_output=False, text=False):  # noqa: ARG001
        return FakeProc(stdout="", stderr="Traceback: No module named lizard", returncode=1)

    monkeypatch.setattr(subprocess, "run", fake_run)

    mod = load_lizard_module()
    argv = [
        "lizard_report.py",
        "--repo-root",
        ".",
        "--output-base",
        str(out_base),
        "--timestamp",
        ts,
    ]
    monkeypatch.setattr(sys, "argv", argv)
    rc = mod.main()

    assert rc == 0
    out_dir = out_base / ts
    assert out_dir.is_dir()

    report = json.loads((out_dir / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "error"
    assert report["notes"] == "lizard module not installed"
    assert report["issue_count"] == 0

    raw_txt = (out_dir / "raw.txt").read_text(encoding="utf-8")
    assert "No module named" in raw_txt
    assert not (out_dir / "raw.json").exists()
