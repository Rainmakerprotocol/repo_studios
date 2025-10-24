from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "producers"
    / "scan_code_placeholders.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "scan_code_placeholders", _MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_structured_artifacts(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
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
            "--artifacts-to-keep",
            "5",
        ]
    )

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "code_placeholder_scans"
    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("placeholder_scan-")]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]

    report_path = run_dir / "report.json"
    matches_path = run_dir / "matches.json"
    assert report_path.exists()
    assert matches_path.exists()

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["total_matches"] == 2
    assert payload["summary"]["by_pattern"] == {"FIXME": 1, "TODO": 1}

    matches = json.loads(matches_path.read_text(encoding="utf-8"))
    assert {entry["pattern"] for entry in matches} == {"TODO", "FIXME"}

    latest_dir = output_dir / "latest"
    assert (latest_dir / "latest_report.json").exists()
    assert (latest_dir / "latest_matches.json").exists()


def test_pruning_and_allowlist(tmp_path: Path) -> None:
    mod = _load_module()
    repo_root = tmp_path / "workspace"
    scan_root = repo_root / "src"
    scan_root.mkdir(parents=True, exist_ok=True)

    target_file = scan_root / "sample.py"
    target_file.write_text("# NOTE: keep track\n", encoding="utf-8")

    allowlist = repo_root / "allowlist.txt"
    allowlist.write_text("src/sample.py:1\n", encoding="utf-8")

    for _ in range(2):
        mod.run(
            [
                "--repo-root",
                str(repo_root),
                "--root",
                "src",
                "--artifacts-to-keep",
                "1",
                "--allowlist-file",
                str(allowlist.relative_to(repo_root)),
            ]
        )

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "code_placeholder_scans"
    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("placeholder_scan-")]
    assert len(run_dirs) == 1

    payload = json.loads((run_dirs[0] / "report.json").read_text(encoding="utf-8"))
    assert payload["total_matches"] == 0
    assert payload["allowlist_size"] == 1