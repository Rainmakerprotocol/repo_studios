from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from pathlib import Path
from dataclasses import dataclass

import pytest

SCRIPTS_ROOT = (
    Path(__file__).resolve().parents[4]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)


def _load_libraries():
    try:
        return importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - fallback mirrors existing tests
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("libraries")


libraries = _load_libraries()
PathSpec = libraries.PathSpec
KeepSpec = libraries.KeepSpec
build_keep_counts = libraries.build_keep_counts
build_paths = libraries.build_paths
resolve_path = libraries.resolve_path
resolve_repo_root = libraries.resolve_repo_root
PathsConfig = libraries.PathsConfig
OptionsConfig = libraries.OptionsConfig
build_standard_paths = libraries.build_standard_paths
build_standard_options = libraries.build_standard_options


def test_resolve_repo_root_explicit(tmp_path: Path) -> None:
    explicit_root = tmp_path / "explicit"
    explicit_root.mkdir()
    result = resolve_repo_root(str(explicit_root))
    assert result == explicit_root.resolve()


def test_resolve_repo_root_fallback(tmp_path: Path) -> None:
    origin = tmp_path / ".repo_studios" / "scripts" / "producers" / "tool.py"
    origin.parent.mkdir(parents=True)
    origin.write_text("", encoding="utf-8")
    result = resolve_repo_root(None, fallback_depth=4, origin=origin)
    assert result == tmp_path.resolve()


def test_resolve_path_relative_default_creates_directory(tmp_path: Path) -> None:
    repo_root = tmp_path
    resolved = resolve_path(
        None,
        repo_root=repo_root,
        default=Path("reports/output"),
        ensure_dir=True,
    )
    expected = (repo_root / "reports" / "output").resolve()
    assert resolved == expected
    assert resolved.is_dir()


def test_resolve_path_rejects_outside_repo(tmp_path: Path) -> None:
    repo_root = tmp_path
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    with pytest.raises(ValueError):
        resolve_path(str(outside), repo_root=repo_root, default=Path("unused"))


def test_build_paths_uses_specs(tmp_path: Path) -> None:
    repo_root = tmp_path
    config = {
        "reports_root": PathSpec(field="reports_root", default=Path("reports"), ensure_dir=True),
        "output_dir": PathSpec(
            field="output_dir", default=Path("fallback"), ensure_dir=True, within_repo=False
        ),
    }
    custom_output = tmp_path / "custom-output"
    args = SimpleNamespace(reports_root=None, output_dir=str(custom_output))
    result = build_paths(config, args=args, repo_root=repo_root)
    assert result["reports_root"] == (repo_root / "reports").resolve()
    assert (repo_root / "reports").is_dir()
    assert result["output_dir"] == custom_output.resolve()
    assert custom_output.is_dir()


def test_build_keep_counts_respects_env(monkeypatch: pytest.MonkeyPatch) -> None:
    config = {
        "artifacts": KeepSpec(field="artifacts", minimum=2, env_override="FORCE_KEEP", env_truthy=frozenset({"yes"})),
    }
    args = SimpleNamespace(artifacts="5")
    result = build_keep_counts(config, args=args)
    assert result["artifacts"] == 5
    monkeypatch.setenv("FORCE_KEEP", "yes")
    args_override = SimpleNamespace(artifacts=None)
    result_override = build_keep_counts(config, args=args_override)
    assert result_override["artifacts"] == 2
    monkeypatch.delenv("FORCE_KEEP", raising=False)


@dataclass(frozen=True)
class SamplePaths:
    repo_root: Path
    reports_root: Path
    output_dir: Path


@dataclass(frozen=True)
class SampleOptions:
    artifacts: int


def test_build_standard_paths_wraps_builders(tmp_path: Path) -> None:
    origin = tmp_path / ".repo_studios" / "command_center" / "scripts" / "producer.py"
    origin.parent.mkdir(parents=True)
    origin.write_text("", encoding="utf-8")
    config = PathsConfig(
        dataclass_type=SamplePaths,
        path_specs={
            "reports_root": PathSpec(field="reports_root", default=Path("reports"), ensure_dir=True),
            "output_dir": PathSpec(
                field="output_dir",
                default=Path("fallback"),
                ensure_dir=True,
                within_repo=False,
            ),
        },
        repo_root_depth=4,
    )
    custom_output = tmp_path / "custom-output"
    args = SimpleNamespace(repo_root=None, reports_root=None, output_dir=str(custom_output))
    result = build_standard_paths(args, config, origin=origin)
    assert isinstance(result, SamplePaths)
    assert result.repo_root == tmp_path.resolve()
    assert result.reports_root == (tmp_path / "reports").resolve()
    assert result.output_dir == custom_output.resolve()
    assert result.output_dir.is_dir()


def test_build_standard_options_wraps_keep_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    config = OptionsConfig(
        dataclass_type=SampleOptions,
        keep_specs={
            "artifacts": KeepSpec(field="artifacts", minimum=1, env_override="FORCE_KEEP", env_truthy=frozenset({"true"})),
        },
    )
    args = SimpleNamespace(artifacts="3")
    result = build_standard_options(args, config)
    assert isinstance(result, SampleOptions)
    assert result.artifacts == 3
    monkeypatch.setenv("FORCE_KEEP", "true")
    override_args = SimpleNamespace(artifacts=None)
    override_result = build_standard_options(override_args, config)
    assert override_result.artifacts == 1
    monkeypatch.delenv("FORCE_KEEP", raising=False)
