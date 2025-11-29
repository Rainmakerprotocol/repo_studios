from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "utilities" / "fault_run_analysis.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("fault_run_analysis", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ensure_manifest_creates_file(tmp_path: Path) -> None:
    module = _load_module()
    outdir = tmp_path / "run"
    outdir.mkdir()

    manifest = module.ensure_manifest(outdir)

    manifest_path = outdir / "MANIFEST.json"
    assert manifest_path.exists()
    round_trip = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert round_trip["ts"] == manifest["ts"]


def test_collect_signatures_groups_threads(tmp_path: Path) -> None:
    module = _load_module()

    stack_text = """Thread 0x1 (most recent call first):\n  File \"pkg/a.py\", line 10, in alpha\nThread 0x2 (most recent call first):\n  File \"pkg/a.py\", line 10, in alpha\nThread 0x3 (most recent call first):\n  File \"pkg/b.py\", line 5, in beta\n"""

    salt = "test-salt"
    now_iso = datetime.now(UTC).isoformat(timespec="seconds")
    signatures, thread_count = module.collect_signatures(
        stack_text,
        salt=salt,
        top_n=1,
        now_iso=now_iso,
    )

    assert thread_count == 3
    assert len(signatures) == 2
    counts = {sig.signature_id: sig.count for sig in signatures}
    assert sorted(counts.values(), reverse=True) == [2, 1]


def test_build_fault_report_emits_summary(tmp_path: Path) -> None:
    module = _load_module()

    outdir = tmp_path / "faulthandler" / "2025-01-01_000000"
    outdir.mkdir(parents=True)
    log_text = """Thread 0x1 (most recent call first):\n  File \"pkg/a.py\", line 10, in alpha\n"""
    (outdir / "stacks.log").write_text(log_text, encoding="utf-8")

    result = module.build_fault_report(outdir, now=datetime.now(UTC), top_n=1)

    assert result.report["summary"]["signature_count"] == 1
    assert result.report["summary"]["thread_block_count"] == 1
    assert result.report["signatures"][0]["top_file"].endswith("pkg/a.py")
    assert (outdir / "MANIFEST.json").exists()
