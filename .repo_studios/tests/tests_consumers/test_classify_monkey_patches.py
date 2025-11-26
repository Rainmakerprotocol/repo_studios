from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

_CONSUMER_PATH = Path(__file__).resolve().parents[2] / "scripts" / "consumers" / "classify_monkey_patches.py"


def _load_module(name: str, path: Path):
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_structured_run(
    root: Path,
    name: str,
    matches: list[dict[str, object]],
    metadata: dict[str, object] | None = None,
) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "matches.json").write_text(json.dumps(matches), encoding="utf-8")
    if metadata is not None:
        (run_dir / "report.json").write_text(json.dumps(metadata), encoding="utf-8")
    return run_dir


def _write_legacy_run(root: Path, name: str, findings: list[dict[str, object]]) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(findings), encoding="utf-8")
    return run_dir


@pytest.mark.parametrize(
    "category,is_test,is_module_scope,expected",
    [
        ("sys_modules_assignment", False, True, "HIGH"),
        ("sys_modules_assignment", True, True, "MODERATE"),
        ("import_time_side_effect", False, False, "HIGH"),
        ("builtins_mutation", True, False, "MODERATE"),
        ("singleton_rebind", False, False, "HIGH"),
        ("global_env_mutation", False, True, "HIGH"),
        ("global_env_mutation", True, False, "MODERATE"),
        ("attribute_reassignment_on_import", False, False, "MODERATE"),
        ("attribute_reassignment_on_import", True, False, "SAFE"),
        ("setattr_on_import_or_class", False, False, "MODERATE"),
        ("test_patch_misuse", True, True, "MODERATE"),
        ("other", False, False, "SAFE"),
    ],
)
def test_classify_matrix(category, is_test, is_module_scope, expected):
    consumer = _load_module("classify_monkey_patches", _CONSUMER_PATH)
    finding = consumer.Finding(
        file="src/example.py",
        line=1,
        category=category,
        is_test=is_test,
        is_module_scope=is_module_scope,
        import_base=None,
    )
    assert consumer.classify(finding) == expected


def test_run_prefers_structured_matches(tmp_path):
    consumer = _load_module("classify_monkey_patches", _CONSUMER_PATH)

    base_dir = tmp_path / "structured"
    output_base = tmp_path / "consumer"
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

    result = consumer.run(
        [
            "--base-dir",
            str(base_dir),
            "--output-base",
            str(output_base),
        ]
    )

    assert Path(result["scan_dir"]) == run_dir.resolve()
    assert result["source"] == "structured"

    bundle_dir = Path(result["bundle_dir"])
    assert bundle_dir.parent == output_base.resolve()
    summary = json.loads((bundle_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["counts_by_risk"]["HIGH"] == 1
    assert summary["counts_by_risk"]["MODERATE"] == 1
    assert summary["run_metadata"]["run_id"] == "scan-1"

    bundle_summary = json.loads(Path(result["bundle_summary"]).read_text(encoding="utf-8"))
    assert bundle_summary["source"] == "structured"
    assert bundle_summary["artifacts"]["summary_json"].endswith("summary.json")

    md_text = (bundle_dir / "SUMMARY.md").read_text(encoding="utf-8")
    assert "Total Findings" in md_text
    assert "sys_modules_assignment" in md_text

    # Legacy copies remain for compatibility
    legacy_summary = json.loads((run_dir / "RISK_SUMMARY.json").read_text(encoding="utf-8"))
    assert legacy_summary["counts_by_risk"]["HIGH"] == 1


def test_run_falls_back_to_legacy(tmp_path):
    consumer = _load_module("classify_monkey_patches", _CONSUMER_PATH)

    legacy_dir = tmp_path / "legacy"
    output_base = tmp_path / "consumer"
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

    result = consumer.run(
        [
            "--base-dir",
            str(legacy_dir),
            "--output-base",
            str(output_base),
        ]
    )

    assert Path(result["scan_dir"]) == run_dir.resolve()
    assert result["source"] == "legacy"
    summary = json.loads((Path(result["bundle_dir"]) / "summary.json").read_text(encoding="utf-8"))
    assert summary["counts_by_risk"]["MODERATE"] == 1
    assert summary["run_metadata"] == {}


def test_retention_prunes_old_runs(tmp_path):
    consumer = _load_module("classify_monkey_patches", _CONSUMER_PATH)

    base_dir = tmp_path / "structured"
    output_base = tmp_path / "consumer"
    matches = [
        {
            "file": "src/example.py",
            "line": 1,
            "category": "sys_modules_assignment",
            "is_test": False,
            "is_module_scope": True,
        }
    ]

    timestamps = [
        datetime(2025, 11, 24, 0, 0, tzinfo=UTC),
        datetime(2025, 11, 24, 0, 1, tzinfo=UTC),
        datetime(2025, 11, 24, 0, 2, tzinfo=UTC),
    ]
    original_now = consumer._utcnow

    def fake_now():
        return timestamps.pop(0)

    consumer._utcnow = fake_now
    try:
        results = []
        for idx in range(3):
            run_dir = _write_structured_run(
                base_dir,
                f"monkey_patch_scan-20251124_0{idx}0000",
                matches,
                {"run": idx},
            )
            results.append(
                consumer.run(
                    [
                        "--scan-dir",
                        str(run_dir),
                        "--output-base",
                        str(output_base),
                        "--artifacts-to-keep",
                        "2",
                    ]
                )
            )

        bundle_dirs = sorted(p for p in output_base.iterdir() if p.is_dir())
        assert len(bundle_dirs) == 2
        first_bundle = Path(results[0]["bundle_dir"])
        assert not first_bundle.exists()
        pruned_paths = {Path(p) for p in results[-1]["pruned"]}
        assert first_bundle in pruned_paths
    finally:
        consumer._utcnow = original_now
