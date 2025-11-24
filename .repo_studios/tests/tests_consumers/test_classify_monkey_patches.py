from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_CONSUMER_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "consumers"
    / "classify_monkey_patches.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_structured_run(root: Path, name: str, matches: list[dict[str, object]], metadata: dict[str, object] | None = None) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "matches.json").write_text(json.dumps(matches), encoding="utf-8")
    if metadata is not None:
        (run_dir / "report.json").write_text(json.dumps(metadata), encoding="utf-8")
    return run_dir


def _write_legacy_run(root: Path, name: str, findings: list[dict[str, object]]) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    (run_dir / "report.json").write_text(json.dumps(findings), encoding="utf-8")
    return run_dir


def test_run_prefers_structured_matches(tmp_path):
    consumer = _load_module("classify_monkey_patches", _CONSUMER_PATH)

    base_dir = tmp_path / "structured"
    matches = [
        {
            "file": "src/example.py",
            "line": 10,
            "category": "sys_modules_assignment",
            "is_test": False,
            "is_module_scope": True,
            "import_base": "example",
        },
        {
            "file": "tests/test_example.py",
            "line": 5,
            "category": "global_env_mutation",
            "is_test": True,
            "is_module_scope": False,
            "import_base": "env",
        },
    ]
    meta = {"run_id": "scan-1", "total_findings": 2}
    run_dir = _write_structured_run(base_dir, "monkey_patch_scan-20251124_010101", matches, meta)

    result = consumer.run(["--base-dir", str(base_dir)])

    assert Path(result["scan_dir"]) == run_dir
    summary_path = run_dir / "RISK_SUMMARY.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["counts_by_risk"]["HIGH"] == 1
    assert summary["counts_by_risk"]["MODERATE"] == 1
    assert summary["run_metadata"]["run_id"] == "scan-1"
    md_text = (run_dir / "RISK_SUMMARY.md").read_text(encoding="utf-8")
    assert "Total Findings" in md_text
    assert "sys_modules_assignment" in md_text


def test_run_falls_back_to_legacy(tmp_path):
    consumer = _load_module("classify_monkey_patches", _CONSUMER_PATH)

    legacy_dir = tmp_path / "legacy"
    findings = [
        {
            "file": "src/legacy.py",
            "line": 3,
            "category": "attribute_reassignment_on_import",
            "is_test": False,
            "is_module_scope": True,
            "import_base": "legacy",
        }
    ]
    run_dir = _write_legacy_run(legacy_dir, "20250101_000000", findings)

    result = consumer.run(["--base-dir", str(legacy_dir)])

    assert Path(result["scan_dir"]) == run_dir
    summary = json.loads((run_dir / "RISK_SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["counts_by_risk"]["MODERATE"] == 1
    assert summary["run_metadata"] == {}