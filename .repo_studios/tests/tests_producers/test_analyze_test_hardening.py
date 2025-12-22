"""Tests for analyze_test_hardening producer."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "analyze_test_hardening.py"
MODULE_NAME = "repo_studios_test.analyze_test_hardening"


@pytest.fixture(scope="module")
def analyzer_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert loader is not None
    sys.modules[spec.name] = module
    loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(spec.name, None)


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "tests").mkdir()
    return tmp_path


def write_test_file(repo_root: Path, relative: str, content: str) -> Path:
    path = repo_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def run_analyzer(module, repo_root: Path, output_dir: Path) -> dict:
    try:
        output_arg = output_dir.relative_to(repo_root)
    except ValueError:
        output_arg = output_dir
    payload = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_arg),
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "DEBUG",
            "--timestamp",
            "2025-12-15T19:30:00+00:00",
        ]
    )
    return payload


def test_detects_missing_assertions_and_long_test(analyzer_module, repo_root: Path) -> None:
    lines = [
        "import requests",
        "",
        "def test_big_block():",
        "    value = 0",
    ]
    # Generate enough body lines to trigger long_test and debug_code findings.
    lines.extend(f"    print({idx})" for idx in range(60))
    lines.append("    return value")
    write_test_file(repo_root, "tests/test_big.py", "\n".join(lines) + "\n")
    output_dir = repo_root / ".repo_studios/reports/healthview"
    payload = run_analyzer(analyzer_module, repo_root, output_dir)
    assert payload["summary"]["total_files"] == 1
    issues = payload["results"][0]["issues"]
    categories = {issue["category"] for issue in issues}
    assert {"missing_mocks", "long_test", "no_assertions", "debug_code"}.issubset(categories)


def test_clean_file_marked_ok(analyzer_module, repo_root: Path) -> None:
    content = """
import pytest

def test_addition_given_when_then():
    assert 1 + 1 == 2
"""
    write_test_file(repo_root, "tests/test_clean.py", content)
    output_dir = repo_root / ".repo_studios/reports/healthview"
    payload = run_analyzer(analyzer_module, repo_root, output_dir)
    assert payload["summary"]["total_issues"] == 0
    assert payload["status"] == "ok"


def test_artifacts_written(analyzer_module, repo_root: Path) -> None:
    content = """
import time

def test_sleep():
    time.sleep(1)
    assert True
"""
    output_dir = repo_root / ".repo_studios/reports/healthview"
    write_test_file(repo_root, "tests/test_sleep.py", content)
    payload = run_analyzer(analyzer_module, repo_root, output_dir)
    assert payload["summary"]["total_files"] == 1
    bundle_dir = Path(payload["output_dir"])
    assert (bundle_dir / "manifest.json").exists()
    assert (bundle_dir / "summary.md").exists()
    assert (bundle_dir / "telemetry.json").exists()
    telemetry = json.loads((bundle_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["metrics"]["total_files"] == 1
