from __future__ import annotations

import importlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "utilities" / "dump_faulthandler_snapshot.py"


def _load_module(monkeypatch: pytest.MonkeyPatch):
    sys.modules.pop("dump_faulthandler_snapshot", None)
    spec = importlib.util.spec_from_file_location("dump_faulthandler_snapshot", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeFaulthandler(ModuleType):
    def __init__(self) -> None:
        super().__init__("faulthandler")
        self.enabled_before = False
        self.enable_calls: list[tuple[bool]] = []
        self.dump_calls: list[dict[str, Any]] = []

    def is_enabled(self) -> bool:
        return self.enabled_before

    def enable(self, all_threads: bool = False) -> None:  # noqa: D401
        self.enable_calls.append((all_threads,))
        self.enabled_before = True

    def dump_traceback(self, file=None, all_threads=True):  # noqa: D401
        assert file is not None
        self.dump_calls.append({"all_threads": all_threads})
        file.write("fake traceback")


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch: pytest.MonkeyPatch):
    for key in list(os.environ):
        if key.startswith("FAULT_"):
            monkeypatch.delenv(key, raising=False)
    yield


def test_dump_snapshot_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_module(monkeypatch)
    fake = FakeFaulthandler()
    monkeypatch.setitem(sys.modules, "faulthandler", fake)

    module.ROOT = tmp_path
    now_value = datetime(2025, 11, 28, 12, 0, 0, tzinfo=UTC)
    result = module.dump_snapshot(
        env={"FAULT_ENABLE": "1"},
        now_factory=lambda: now_value,
    )

    assert result["status"] == "ok"
    outdir = tmp_path / ".repo_studios" / "reports" / "orchestrator_logs" / "faulthandler_snapshots" / "2025-11-28_120000"
    assert outdir.exists()
    snapshot_file = outdir / "snapshot.txt"
    manifest_file = outdir / "MANIFEST.json"
    bundle_file = outdir / "bundle_summary.json"

    assert snapshot_file.read_text() == "fake traceback"
    assert manifest_file.exists()
    assert bundle_file.exists()

    manifest = json.loads((outdir / "MANIFEST.json").read_text())
    assert manifest["faulthandler"]["dumped"] is True
    summary = json.loads(bundle_file.read_text())
    assert summary["status"] == "ok"


def test_dump_snapshot_prunes_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _load_module(monkeypatch)
    monkeypatch.setitem(sys.modules, "faulthandler", FakeFaulthandler())

    base_dir = tmp_path / ".repo_studios" / "reports" / "orchestrator_logs" / "faulthandler_snapshots"
    base_dir.mkdir(parents=True)
    for idx in range(4):
        run_dir = base_dir / f"2025-11-28_11010{idx}"
        run_dir.mkdir()
        os.utime(run_dir, (idx, idx))

    module.ROOT = tmp_path
    result = module.dump_snapshot(
        env={"FAULT_SNAPSHOT_TO_KEEP": "2"},
        now_factory=lambda: datetime(2025, 11, 28, 13, 0, 0, tzinfo=UTC),
    )

    assert result["status"] == "ok"
    dirs = [p for p in base_dir.iterdir() if p.is_dir()]
    assert len(dirs) == 2


def test_dump_snapshot_import_failure(monkeypatch: pytest.MonkeyPatch):
    module = _load_module(monkeypatch)

    def fake_import(name: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(importlib, "import_module", fake_import)

    result = module.dump_snapshot(env={}, now_factory=lambda: datetime.now(UTC))
    assert result["status"] == "warning"