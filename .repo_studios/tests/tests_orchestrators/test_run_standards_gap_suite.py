from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Sequence

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "orchestrators" / "run_standards_gap_suite.py"


def _load_module() -> ModuleType:
    module_name = f"run_standards_gap_suite_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_redirects_to_topic_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv("STANDARDS_GAP_USE_LEGACY", raising=False)

    captured: dict[str, list[str]] = {}

    def fake_run(args: Sequence[str] | None = None) -> int:
        captured["argv"] = list(args or [])
        return 0

    monkeypatch.setattr(module.standards_topic_runner, "run", fake_run)

    result = module.run(
        [
            "--repo-root",
            ".",
            "--index-output-dir",
            "./index",
            "--gap-output-dir",
            "./gap",
            "--max-show",
            "7",
        ]
    )

    assert result["status"] == "success"
    assert result["exit_code"] == 0
    redirect = result["redirect"]
    assert redirect["target"] == module.TOPIC_TARGET
    forwarded = captured["argv"]
    assert redirect["argv"] == forwarded
    assert "--gap-max-show" in forwarded
    assert "--max-show" not in forwarded
    assert "./gap" in forwarded


def test_run_success_invokes_both_steps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setenv("STANDARDS_GAP_USE_LEGACY", "1")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    calls: dict[str, Sequence[str]] = {}

    def fake_loader(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str]], Any]:
        if attribute == "main":
            def _main(argv: Sequence[str]) -> int:
                calls["generate"] = list(argv)
                return 0

            return _main
        if attribute == "run":
            def _run(argv: Sequence[str]) -> dict[str, Any]:
                calls["gap"] = list(argv)
                return {
                    "run_dir": str(repo_root / "run"),
                    "summary": {"total_candidates": 0},
                }

            return _run
        raise AssertionError(f"Unexpected attribute {attribute}")

    monkeypatch.setattr(module, "_load_callable", fake_loader)

    legacy_json = repo_root / "legacy.json"
    result = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--index-output-dir",
            str(repo_root / "index_out"),
            "--gap-output-dir",
            str(repo_root / "gap_out"),
            "--index-path",
            str(repo_root / "repo_standards_index.yaml"),
            "--categories-path",
            str(repo_root / "standards_categories.yaml"),
            "--legacy-json",
            str(legacy_json.relative_to(repo_root)),
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
            "--log-level",
            "DEBUG",
            "--max-show",
            "5",
            "--index-artifacts-to-keep",
            "3",
            "--gap-artifacts-to-keep",
            "4",
        ]
    )

    assert result["status"] == "success"
    assert "generate" in calls and "gap" in calls
    gen_args = calls["generate"]
    gap_args = calls["gap"]
    assert "--repo-root" in gen_args and str(repo_root) in gen_args
    assert "--output-dir" in gen_args and str(repo_root / "index_out") in gen_args
    assert "--timestamp" in gen_args
    assert "--json" in gap_args and str(legacy_json) in gap_args
    assert result["gap"]["payload"]["summary"]["total_candidates"] == 0


def test_run_index_failure_short_circuits_gap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setenv("STANDARDS_GAP_USE_LEGACY", "1")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    gap_called = False

    def fake_loader(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str]], Any]:
        nonlocal gap_called
        if attribute == "main":
            def _main(argv: Sequence[str]) -> int:
                return 1

            return _main
        if attribute == "run":
            def _run(argv: Sequence[str]) -> dict[str, Any]:
                gap_called = True
                return {}

            return _run
        raise AssertionError(f"Unexpected attribute {attribute}")

    monkeypatch.setattr(module, "_load_callable", fake_loader)

    result = module.run(["--repo-root", str(repo_root)])

    assert result["status"] == "index_failed"
    assert result["gap"] is None or result["gap"].get("payload") is None
    assert gap_called is False


def test_run_gap_failure_reports_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.setenv("STANDARDS_GAP_USE_LEGACY", "1")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    def fake_loader(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str]], Any]:
        if attribute == "main":
            return lambda argv: 0
        if attribute == "run":
            def _run(argv: Sequence[str]) -> dict[str, Any]:
                raise RuntimeError("gap failure")

            return _run
        raise AssertionError(f"Unexpected attribute {attribute}")

    monkeypatch.setattr(module, "_load_callable", fake_loader)

    result = module.run(["--repo-root", str(repo_root)])

    assert result["status"] == "gap_failed"
    assert result["gap"]["exit_code"] == 2
    assert result["gap"]["error"] == "gap failure"


def test_run_skip_index_bypasses_generator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    called = {"generate": False, "gap": False}

    def fake_loader(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str]], Any]:
        if attribute == "main":
            def _main(argv: Sequence[str]) -> int:
                called["generate"] = True
                return 0

            return _main
        if attribute == "run":
            def _run(argv: Sequence[str]) -> dict[str, Any]:
                called["gap"] = True
                return {"summary": {"total_candidates": 1}}

            return _run
        raise AssertionError(f"Unexpected attribute {attribute}")

    monkeypatch.setattr(module, "_load_callable", fake_loader)

    result = module.run(["--repo-root", str(repo_root), "--skip-index"])

    assert result["status"] == "success"
    assert called["gap"] is True
    assert called["generate"] is False


def test_main_uses_status(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()

    monkeypatch.setattr(module, "run", lambda argv=None: {"status": "success"})
    assert module.main([]) == 0

    monkeypatch.setattr(
        module,
        "run",
        lambda argv=None: {"status": "index_failed", "index": {"exit_code": 3}, "gap": None},
    )
    assert module.main([]) == 3

    monkeypatch.setattr(
        module,
        "run",
        lambda argv=None: {"status": "gap_failed", "index": None, "gap": {"exit_code": 4}},
    )
    assert module.main([]) == 4

    monkeypatch.setattr(module, "run", lambda argv=None: {"status": "failed", "exit_code": 5})
    assert module.main([]) == 5

    monkeypatch.setattr(module, "run", lambda argv=None: {"status": "unknown"})
    assert module.main([]) == 1
