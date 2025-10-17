import json
import subprocess
import sys
from pathlib import Path


def test_orchestrator_includes_typecheck_step(tmp_path: Path):
    # Run orchestrator with a fixed timestamp into a temp logs dir
    ts = "2099-01-01_0000"
    logs_dir = Path(".repo_studios/health_suite/logs") / ts
    # Clean any existing
    if logs_dir.exists():
        for p in logs_dir.rglob("*"):
            try:
                p.unlink()
            except IsADirectoryError:
                pass
        try:
            logs_dir.rmdir()
        except Exception:
            pass
    rc = subprocess.call(
        [
            sys.executable,
            ".repo_studios/health_suite_orchestrator.py",
            "--timestamp",
            ts,
            "--step-timeout-sec",
            "1",
            "--heartbeat-sec",
            "0",
        ],
        timeout=60,
    )
    assert rc == 0
    status_path = logs_dir / "status.json"
    assert status_path.exists()
    data = json.loads(status_path.read_text(encoding="utf-8"))
    steps = data.get("steps", [])
    names = [s.get("name") for s in steps]
    assert "typecheck_report" in names, f"missing typecheck_report in steps: {names}"
    # Ensure the step either ran OK/ERROR or was marked skipped if missing locally
    idx = names.index("typecheck_report")
    st = steps[idx]
    assert ("status" in st) or st.get("skipped"), f"unexpected step record: {st}"
