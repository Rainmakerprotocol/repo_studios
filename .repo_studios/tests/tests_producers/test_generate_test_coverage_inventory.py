from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_test_coverage_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_test_coverage_inventory", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_coverage_fixture(repo_root: Path, *, hits_for_uncovered: int = 0) -> Path:
    coverage_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "test_run_coverage"
    coverage_dir.mkdir(parents=True, exist_ok=True)
    coverage_xml = coverage_dir / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version=\"1.0\"?>
<coverage line-rate=\"0\" branch-rate=\"0\" version=\"1\">
  <sources>
    <source>{source}</source>
  </sources>
  <packages>
    <package name=\"src\" line-rate=\"0\" branch-rate=\"0\">
      <classes>
        <class name=\"alpha\" filename=\"src/alpha.py\" line-rate=\"0\" branch-rate=\"0\">
          <lines>
            <line number=\"2\" hits=\"1\"/>
            <line number=\"6\" hits=\"{hits}\"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""".format(source=repo_root.as_posix(), hits=hits_for_uncovered),
        encoding="utf-8",
    )
    return coverage_xml


def test_generates_structured_artifacts(tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    src_dir = repo_root / "src"
    src_dir.mkdir()
    module_path = src_dir / "alpha.py"
    module_path.write_text(
        "def covered():\n    return 1\n\n\ndef uncovered():\n    return 2\n",
        encoding="utf-8",
    )

    coverage_xml = _write_coverage_fixture(repo_root)

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "test_coverage_reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert summary["status"] == "ok"
    assert summary["total_files"] == 1
    assert summary["total_functions"] == 2
    assert summary["covered_functions"] == 1
    assert summary["overall_coverage_pct"] == pytest.approx(50.0)

    files = payload["files"]
    assert len(files) == 1
    file_entry = files[0]
    assert file_entry["path"].replace("\\", "/") == "src/alpha.py"
    assert file_entry["function_count"] == 2
    assert file_entry["functions_covered"] == 1
    assert file_entry["uncovered_functions"] == ["uncovered"]

    latest_json = output_dir / "latest_report.json"
    latest_md = output_dir / "latest_report.md"
    latest_csv = output_dir / "latest_report.csv"
    latest_log = output_dir / "latest_report.log"
    assert latest_json.is_file()
    assert latest_md.is_file()
    assert latest_csv.is_file()
    assert latest_log.is_file()

    markdown = latest_md.read_text(encoding="utf-8")
    assert "Test Coverage Inventory" in markdown
    assert "src/alpha.py" in markdown

    csv_lines = latest_csv.read_text(encoding="utf-8").strip().splitlines()
    assert csv_lines[0] == "path,function_count,functions_covered,coverage_pct,uncovered_functions"
    assert "src/alpha.py,2,1,50.00,uncovered" in csv_lines[1]


def test_threshold_enforcement_and_pruning(tmp_path: Path):
    mod = _load_module()

    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    src_dir = repo_root / "src"
    src_dir.mkdir()
    module_path = src_dir / "alpha.py"
    module_path.write_text(
        "def covered():\n    return 1\n\n\ndef uncovered():\n    return 2\n",
        encoding="utf-8",
    )

    coverage_xml = _write_coverage_fixture(repo_root)

    output_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "test_coverage_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_slugs = [
        f"{mod.RUN_PREFIX}-20240101_000000",
        f"{mod.RUN_PREFIX}-20240102_000000",
        f"{mod.RUN_PREFIX}-20240103_000000",
    ]
    for slug in stale_slugs:
        run_dir = output_dir / slug
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "report.json").write_text("{}\n", encoding="utf-8")

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-02-04T00:00:00+00:00",
            "--min-coverage",
            "90",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1

    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240204_000000"
    assert run_dir.is_dir()

    payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    summary = payload["summary"]
    assert summary["status"] == "threshold_failed"
    assert summary["files_below_threshold"] == ["src/alpha.py"]

    log_text = (output_dir / "latest_report.log").read_text(encoding="utf-8")
    assert "status=threshold_failed" in log_text
    assert "files_below_threshold=1" in log_text

    remaining = sorted(
        path.name for path in output_dir.iterdir() if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)
    )
    assert remaining == [
        f"{mod.RUN_PREFIX}-20240103_000000",
        f"{mod.RUN_PREFIX}-20240204_000000",
    ]
