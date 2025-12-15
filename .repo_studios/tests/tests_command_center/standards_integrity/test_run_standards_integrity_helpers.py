from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def test_relativize_returns_relative_posix(tmp_path):
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    artifact = repo_root / "out" / "summary.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")

    assert orchestrator._relativize(artifact, repo_root) == "out/summary.json"


def test_parse_timestamp_defaults_to_utc_and_handles_naive():
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    now = orchestrator._parse_timestamp(None)
    assert now.tzinfo is not None

    parsed = orchestrator._parse_timestamp("2024-01-01T00:00:00")
    assert parsed == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_resolve_optional_path_handles_relative(tmp_path):
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    resolved = orchestrator._resolve_optional_path(repo_root, "out/manifest.json")
    assert resolved == (repo_root / "out" / "manifest.json").resolve()


def test_read_json_returns_none_for_invalid_json(tmp_path):
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    bad = tmp_path / "bad.json"
    bad.write_text("not-json", encoding="utf-8")
    assert orchestrator._read_json(bad) is None


def test_invoke_main_coerces_return_values():
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    def returns_string(argv):
        assert argv == ["--flag"]
        return "2"

    assert orchestrator._invoke_main(returns_string, ["--flag"]) == 2

    def returns_uncoercible(argv):
        return None

    assert orchestrator._invoke_main(returns_uncoercible, []) == 0


def test_load_callable_reuses_cached_module(tmp_path):
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    module_path = tmp_path / "toy_module.py"
    module_path.write_text(
        "def main(argv):\n    return 0\n",
        encoding="utf-8",
    )

    func_first = orchestrator._load_callable(module_path, "toy_module_for_test", "main")
    func_second = orchestrator._load_callable(module_path, "toy_module_for_test", "main")
    assert func_first is func_second


def test_load_callable_raises_for_missing_callable(tmp_path):
    from command_center.scripts.orchestrators import run_standards_integrity as orchestrator

    module_path = tmp_path / "toy_bad_module.py"
    module_path.write_text("X = 1\n", encoding="utf-8")

    try:
        orchestrator._load_callable(module_path, "toy_bad_module_for_test", "main")
    except AttributeError as exc:
        assert "missing callable" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected missing callable to raise")
