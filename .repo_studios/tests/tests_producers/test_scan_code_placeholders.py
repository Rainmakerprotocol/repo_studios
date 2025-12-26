from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "scan_code_placeholders.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("scan_code_placeholders", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_structured_artifacts(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)
    scan_root = repo_root / "src"
    scan_root.mkdir(parents=True, exist_ok=True)

    (scan_root / "one.py").write_text(
        """# TODO: polish this function\nprint('hello')\n""",
        encoding="utf-8",
    )
    (scan_root / "two.md").write_text(
        """<!-- FIXME: update docs -->\nBody text\n""",
        encoding="utf-8",
    )

    mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            "src",
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
            "--artifacts-to-keep",
            "5",
        ]
    )

    topic_dir = (
        repo_root / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "code_placeholders"
    )
    run_dir = topic_dir / "20250101-0000"
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "telemetry.json").exists()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    summary = telemetry["summary"]
    assert summary["total_matches"] == 2
    assert summary["summary"]["by_pattern"] == {"FIXME": 1, "TODO": 1}


def test_pruning_and_allowlist(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)
    scan_root = repo_root / "src"
    scan_root.mkdir(parents=True, exist_ok=True)

    target_file = scan_root / "sample.py"
    target_file.write_text("# NOTE: keep track\n", encoding="utf-8")

    allowlist = repo_root / "allowlist.txt"
    allowlist.write_text("src/sample.py:1\n", encoding="utf-8")

    timestamps = ["2025-01-01T00:00:00+00:00", "2025-01-01T00:01:00+00:00"]
    for timestamp in timestamps:
        mod.run(
            [
                "--repo-root",
                str(repo_root),
                "--root",
                "src",
                "--timestamp",
                timestamp,
                "--artifacts-to-keep",
                "1",
                "--allowlist-file",
                str(allowlist.relative_to(repo_root)),
            ]
        )

    topic_dir = (
        repo_root / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "code_placeholders"
    )
    run_dirs = [p for p in topic_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1

    telemetry = json.loads((run_dirs[0] / "telemetry.json").read_text(encoding="utf-8"))
    summary = telemetry["summary"]
    assert summary["total_matches"] == 0
    assert summary["allowlist_size"] == 1


def test_default_exclusions_skip_virtualenv(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)

    (repo_root / "real.py").write_text("# TODO: implement feature\n", encoding="utf-8")
    env_file = repo_root / ".venv" / "lib" / "package.py"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("# FIXME: should be ignored\n", encoding="utf-8")

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            ".",
            "--include-ext",
            ".py",
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
        ]
    )

    assert payload["total_matches"] == 1
    assert payload["default_exclusions_applied"] is True
    assert set(payload["exclude_prefixes"]) == {".venv/", "node_modules/"}
    assert payload["exclude_segments"] == ["site-packages"]

    topic_dir = (
        repo_root / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "code_placeholders"
    )
    run_dir = topic_dir / "20250101-0000"
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    sample = manifest.get("matches_sample", [])
    assert {entry["path"] for entry in sample} == {"real.py"}


def test_exclude_prefix_flag_disables_defaults(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)

    env_file = repo_root / ".venv" / "lib" / "module.py"
    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("# NOTE: now included\n", encoding="utf-8")

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            ".",
            "--include-ext",
            ".py",
            "--exclude-prefix",
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
        ]
    )

    assert payload["default_exclusions_applied"] is False
    assert payload["exclude_prefixes"] == []
    assert payload["exclude_segments"] == []
    assert payload["total_matches"] == 1


def test_ignores_title_case_tokens(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    repo_root.mkdir(parents=True, exist_ok=True)
    (repo_root / ".repo_studios").mkdir(parents=True, exist_ok=True)

    (repo_root / "doc.md").write_text("# Review heading\n", encoding="utf-8")
    (repo_root / "code.py").write_text("# TODO: follow up\n", encoding="utf-8")

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--root",
            ".",
            "--include-ext",
            ".md",
            ".py",
            "--timestamp",
            "2025-01-01T00:00:00+00:00",
        ]
    )

    assert payload["total_matches"] == 1
    topic_dir = (
        repo_root / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "code_placeholders"
    )
    run_dir = topic_dir / "20250101-0000"
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    sample = manifest.get("matches_sample", [])
    assert {entry["path"] for entry in sample} == {"code.py"}
