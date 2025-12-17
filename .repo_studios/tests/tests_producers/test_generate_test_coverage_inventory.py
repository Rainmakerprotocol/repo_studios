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
    coverage_dir = repo_root / ".repo_studios" / "tests" / "fixtures" / "test_run_coverage"
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

    output_root = repo_root / ".repo_studios" / "reports" / "producer_reports"

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
            "--timestamp",
            "2024-01-01T00:00:00+00:00",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 0
    run_dir = output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG / "20240101-0000"
    assert run_dir.is_dir()

    bundle_files = sorted(path.name for path in run_dir.iterdir() if path.is_file())
    assert bundle_files == ["manifest.json", "summary.md", "telemetry.json"]

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["viewer_slug"] == mod.VIEWER_SLUG
    assert manifest["topic"] == mod.TOPIC_SLUG
    assert manifest["run_timestamp"] == "20240101-0000"
    assert manifest["status"] == "ok"
    assert "inputs" in manifest

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["viewer_slug"] == mod.VIEWER_SLUG
    assert telemetry["topic"] == mod.TOPIC_SLUG
    assert telemetry["run_timestamp"] == "20240101-0000"
    assert telemetry["status"] == "ok"

    payload = telemetry["payload"]
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

    markdown = (run_dir / "summary.md").read_text(encoding="utf-8")
    assert "Test Coverage Inventory" in markdown
    assert "src/alpha.py" in markdown

    assert not list((output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG).glob("latest_*"))


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

    output_root = repo_root / ".repo_studios" / "reports" / "producer_reports"
    base_dir = output_root / mod.VIEWER_SLUG / mod.TOPIC_SLUG
    base_dir.mkdir(parents=True, exist_ok=True)

    stale_slugs = ["20240101-0000", "20240102-0000", "20240103-0000"]
    for slug in stale_slugs:
        run_dir = base_dir / slug
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "telemetry.json").write_text("{}\n", encoding="utf-8")

    exit_code = mod.main(
        [
            "--repo-root",
            str(repo_root),
            "--coverage-xml",
            str(coverage_xml),
            "--output-dir",
            str(output_root),
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

    run_dir = base_dir / "20240204-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    payload = telemetry["payload"]
    summary = payload["summary"]
    assert summary["status"] == "threshold_failed"
    assert summary["files_below_threshold"] == ["src/alpha.py"]

    remaining = sorted(path.name for path in base_dir.iterdir() if path.is_dir())
    assert remaining == [
        "20240103-0000",
        "20240204-0000",
    ]

    assert not list(base_dir.glob("latest_*"))
