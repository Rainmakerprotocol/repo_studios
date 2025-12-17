from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import importlib.util
import sys


class FakeFaulthandler:
    def __init__(self) -> None:
        self.enable_calls: list[tuple[Any, bool]] = []
        self.register_calls: list[Any] = []
        self.dump_later_calls: list[tuple[int, bool, Any]] = []
        self.cancel_later_calls: int = 0

    def enable(self, file=None, all_threads=False):  # noqa: D401 - mimic stdlib
        self.enable_calls.append((file, all_threads))

    def register(self, sig, file=None, all_threads=False):  # noqa: D401
        self.register_calls.append((sig, file, all_threads))

    def dump_traceback_later(self, timeout, repeat=False, file=None):  # noqa: D401
        self.dump_later_calls.append((timeout, repeat, file))

    def cancel_dump_traceback_later(self) -> None:  # noqa: D401 - mimic stdlib
        self.cancel_later_calls += 1


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "utilities" / "configure_faulthandler_runtime.py"


def _import_module(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FAULT_DISABLE", "1")
    sys.modules.pop("configure_faulthandler_runtime", None)
    spec = importlib.util.spec_from_file_location("configure_faulthandler_runtime", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for key in list(os.environ):
        if key.startswith("FAULT_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("CI", raising=False)
    yield


def test_bootstrap_writes_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _import_module(monkeypatch)
    fake = FakeFaulthandler()
    monkeypatch.setitem(sys.modules, "faulthandler", fake)

    module.root = tmp_path
    module.root_str = str(tmp_path)
    module.ACTIVE_WRITER = None
    module.LAST_BOOTSTRAP = None

    monkeypatch.setenv("FAULT_DISABLE", "0")
    monkeypatch.setenv("FAULT_ENABLE", "1")
    monkeypatch.setenv("FAULT_DUMP_LATER", "1")
    monkeypatch.setenv("FAULT_TEE_STDERR", "0")
    monkeypatch.setenv("FAULT_ARTIFACTS_TO_KEEP", "2")

    fixed_time = datetime(2025, 1, 2, 3, 4, tzinfo=UTC)
    result = module.bootstrap(env=dict(os.environ), now_factory=lambda: fixed_time)

    assert result["status"] in {"enabled", "warning"}

    base_dir = (
        tmp_path
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "rawview"
        / "fault_diagnostics_runs"
    )
    outdir = base_dir / "2025-01-02_0304"

    assert outdir.exists()
    manifest_path = outdir / "MANIFEST.json"
    summary_path = outdir / "bundle_summary.json"
    assert manifest_path.exists()
    assert summary_path.exists()

    manifest = json.loads(manifest_path.read_text())
    summary = json.loads(summary_path.read_text())

    assert manifest["resolved"]["outdir"] == str(outdir)
    assert manifest["retention"]["keep"] == 2
    assert summary["retention"]["keep"] == 2
    assert summary["status"] == result["status"]

    assert fake.enable_calls, "faulthandler.enable should be invoked"
    assert fake.dump_later_calls, "faulthandler.dump_traceback_later should be invoked when enabled"


def test_bootstrap_prunes_old_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _import_module(monkeypatch)
    monkeypatch.setitem(sys.modules, "faulthandler", FakeFaulthandler())

    module.root = tmp_path
    module.root_str = str(tmp_path)
    module.ACTIVE_WRITER = None
    module.LAST_BOOTSTRAP = None

    base_dir = (
        tmp_path
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "rawview"
        / "fault_diagnostics_runs"
    )
    base_dir.mkdir(parents=True)
    for index in range(3):
        run_dir = base_dir / f"2024-01-0{index}_0000"
        run_dir.mkdir()
        os.utime(run_dir, (index, index))

    monkeypatch.setenv("FAULT_DISABLE", "0")
    monkeypatch.setenv("FAULT_ENABLE", "1")
    monkeypatch.setenv("FAULT_ARTIFACTS_TO_KEEP", "2")

    result = module.bootstrap(env=dict(os.environ), now_factory=lambda: datetime(2025, 1, 1, tzinfo=UTC))

    assert result["status"] in {"enabled", "warning"}
    remaining = [p for p in base_dir.iterdir() if p.is_dir()]
    assert len(remaining) == 2
    assert result["pruned"] >= 1


def test_bootstrap_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    module = _import_module(monkeypatch)
    module.root = tmp_path
    module.root_str = str(tmp_path)
    module.ACTIVE_WRITER = None
    module.LAST_BOOTSTRAP = None

    monkeypatch.setenv("FAULT_DISABLE", "0")
    monkeypatch.setenv("FAULT_ENABLE", "0")

    result = module.bootstrap(env=dict(os.environ), now_factory=lambda: datetime(2025, 1, 1, tzinfo=UTC))
    assert result["status"] == "disabled"

    base_dir = (
        tmp_path
        / ".repo_studios"
        / "command_center"
        / "reports"
        / "rawview"
        / "fault_diagnostics_runs"
    )
    assert not base_dir.exists()
