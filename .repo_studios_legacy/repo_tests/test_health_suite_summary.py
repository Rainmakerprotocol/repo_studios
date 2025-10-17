import json
import subprocess
import sys
from pathlib import Path


def test_summary_includes_typecheck_section(tmp_path: Path, monkeypatch):
    # Arrange: synthesize a typecheck report folder matching the expected layout
    base = Path(".repo_studios/typecheck")
    ts = "2099-01-01_0000"
    run_dir = base / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "ERROR",
        "mypy_version": "mypy 1.x",
        "checked_paths": ["agents/core/jarvis_api.py"],
        "total_errors": 3,
        "files_with_issues": 2,
        "error_samples": [
            {"path": "a.py", "line": 1, "code": "attr-defined", "message": "x has no attribute y"},
            {
                "path": "b.py",
                "line": 2,
                "code": "return-value",
                "message": "Incompatible return value",
            },
        ],
        "invocation": [sys.executable, "-m", "mypy", "agents"],
        "timestamp": ts,
    }
    (run_dir / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text("# Typecheck Report\n- status: ERROR\n", encoding="utf-8")

    out_dir = Path(".repo_studios/health_suite")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Act: compose summary with the same timestamp (so link formatting is stable)
    rc = subprocess.call(
        [
            sys.executable,
            ".repo_studios/health_suite_summary.py",
            "--repo-root",
            ".",
            "--output-dir",
            str(out_dir),
            "--timestamp",
            ts,
        ]
    )

    # Assert
    assert rc == 0
    md_path = out_dir / f"health_suite_{ts}.md"
    text = md_path.read_text(encoding="utf-8")
    assert "## Typecheck — Summary" in text
    assert "- status: ERROR" in text
    assert "- total errors: 3" in text
    assert "- files with issues: 2" in text
    # ensure at least one sample line is rendered
    assert "a.py:1" in text
