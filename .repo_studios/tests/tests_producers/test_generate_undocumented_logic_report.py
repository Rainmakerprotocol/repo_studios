from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from textwrap import dedent

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_undocumented_logic_report.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_doc_index_telemetry(repo_root: Path, payload: dict, *, timestamp: str = "20250101-0000") -> None:
    telemetry_path = (
        repo_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "healthview"
        / "doc_index"
        / timestamp
        / "telemetry.json"
    )
    _write_json(telemetry_path, {"payload": payload})


def _minimal_doc_index(doc_path: str) -> dict:
    return {
        "schema_version": 1,
        "generated_utc": "2025-01-01T00:00:00+00:00",
        "repo_root": "repo",
        "summary": {},
        "metrics": {},
        "documents": [
            {
                "folder": str(Path(doc_path).parent),
                "filename": doc_path,
                "slug": Path(doc_path).stem.replace("_", "-"),
                "owners": ["docs"],
                "modified_utc": "2025-01-01T00:00:00+00:00",
            }
        ],
    }


def _minimal_anchor_inventory(doc_path: str) -> dict:
    return {
        "documents": [
            {
                "path": doc_path,
                "slug_counts": {"overview": 1},
            }
        ]
    }


def test_detects_missing_docstrings(tmp_path):
    module = _load_module("generate_undocumented_logic_report", _MODULE_PATH)

    repo = tmp_path / "repo"
    code_dir = repo / ".repo_studios" / "scripts" / "producers"
    code_dir.mkdir(parents=True)
    code_file = code_dir / "sample.py"
    code_file.write_text(
        dedent(
            '''
            """Module doc."""

            def documented():
                """Docstring."""
                return 1

            def missing():
                return 2

            class PublicClass:
                def method(self):
                    return 3

            class DocumentedClass:
                """Class doc."""

                def method(self):
                    """Method doc."""
                    return 4
            '''
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    doc_path = ".repo_studios/docs/automation/sample.md"
    _write_doc_index_telemetry(repo, _minimal_doc_index(doc_path))
    _write_json(
        repo
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "healthview"
        / "anchor_inventory"
        / "20250101-0000"
        / "telemetry.json",
        {
            "schema_version": 1,
            "viewer_slug": "healthview",
            "topic": "anchor_inventory",
            "run_timestamp": "20250101-0000",
            "generated_at": "2025-01-01T00:00:00+00:00",
            "status": "ok",
            "metrics": {},
            "payload": _minimal_anchor_inventory(doc_path),
        },
    )

    result = module.run(
        argv=[
            "--repo-root",
            str(repo),
            "--output-dir",
            str(repo / ".repo_studios" / "reports" / "producer_reports" / "undocumented_logic_reports"),
        ]
    )

    summary = result["summary"]
    assert summary["modules_with_findings"] == 1
    assert summary["entities_missing_docs"] == 3
    assert summary["docstring_coverage_percent"] == 50.0

    report_path = Path(result["artifacts"]["report.json"])
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    modules = payload["modules"]
    assert modules
    module_entry = modules[0]
    assert module_entry["module_path"] == ".repo_studios/scripts/producers/sample.py"
    findings = module_entry["findings"]
    assert len(findings) == 3
    qualified_names = {finding["qualified_name"] for finding in findings}
    assert f"{module_entry['module_name']}.missing" in qualified_names
    assert any(candidate["path"] == doc_path for candidate in module_entry["doc_candidates"])


def test_allowlist_skips_module(tmp_path):
    module = _load_module("generate_undocumented_logic_report_allow", _MODULE_PATH)

    repo = tmp_path / "repo"
    code_dir = repo / ".repo_studios" / "scripts"
    code_dir.mkdir(parents=True)
    code_file = code_dir / "skipme.py"
    code_file.write_text("def missing():\n    return 1\n", encoding="utf-8")

    allowlist_path = repo / ".repo_studios" / "config" / "undocumented_logic_allowlist.txt"
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    allowlist_path.write_text(
        ".repo_studios/scripts/skipme.py\n",
        encoding="utf-8",
    )

    result = module.run(
        argv=[
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist_path),
            "--output-dir",
            str(repo / ".repo_studios" / "reports" / "producer_reports" / "undocumented_logic_reports"),
        ]
    )

    summary = result["summary"]
    assert summary["modules_with_findings"] == 0
    assert summary["entities_missing_docs"] == 0


def test_handles_missing_metadata(tmp_path):
    module = _load_module("generate_undocumented_logic_report_missing", _MODULE_PATH)

    repo = tmp_path / "repo"
    code_dir = repo / ".repo_studios" / "scripts"
    code_dir.mkdir(parents=True)
    code_file = code_dir / "orphan.py"
    code_file.write_text("def missing():\n    return 1\n", encoding="utf-8")

    result = module.run(
        argv=[
            "--repo-root",
            str(repo),
            "--output-dir",
            str(repo / ".repo_studios" / "reports" / "producer_reports" / "undocumented_logic_reports"),
        ]
    )

    summary = result["summary"]
    assert summary["modules_with_findings"] == 1
    report_path = Path(result["artifacts"]["report.json"])
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    module_entry = payload["modules"][0]
    assert module_entry["doc_candidates"] == []
