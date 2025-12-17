from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_import_graph_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_import_graph_report", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_report_with_no_targets(tmp_path: Path) -> None:
    mod = _load_module()
    root = tmp_path / "workspace"
    root.mkdir()

    output_dir = root / ".repo_studios" / "reports" / "producer_reports"
    argv = [
        "--repo-root",
        str(root),
        "--output-dir",
        str(output_dir),
        "--timestamp",
        "2024-01-01T00:00:00+00:00",
        "--artifacts-to-keep",
        "3",
        "--log-level",
        "ERROR",
    ]

    exit_code = mod.main(argv)
    assert exit_code == 0

    run_dir = output_dir / "healthview" / "import_graph" / "20240101-0000"
    assert run_dir.is_dir()

    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "summary.md").is_file()
    assert (run_dir / "telemetry.json").is_file()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    report = telemetry["payload"]
    assert report["summary"]["status"] == "no_targets"
    assert report["summary"]["module_count"] == 0
    assert report["summary"]["edge_count"] == 0
    assert report["summary"]["cycle_count"] == 0
    assert report["owned_packages_resolved"] == []
    assert report["graph"] == {}

    assert not any(path.name.startswith("latest_") for path in output_dir.rglob("latest_*"))


def test_cycle_detection_and_pruning(tmp_path: Path) -> None:
    mod = _load_module()
    root = tmp_path / "repo"
    root.mkdir()

    _write(root / "agents" / "__init__.py", "")
    _write(root / "agents" / "foo.py", "import api\n")
    _write(root / "api" / "__init__.py", "")
    _write(root / "api" / "bar.py", "import agents\n")

    output_dir = root / ".repo_studios" / "reports" / "producer_reports"
    topic_dir = output_dir / "healthview" / "import_graph"
    topic_dir.mkdir(parents=True, exist_ok=True)

    stale_one = topic_dir / "20240101-0000"
    stale_one.mkdir()
    (stale_one / "telemetry.json").write_text("{}\n", encoding="utf-8")
    stale_two = topic_dir / "20240102-0000"
    stale_two.mkdir()
    (stale_two / "telemetry.json").write_text("{}\n", encoding="utf-8")

    argv = [
        "--repo-root",
        str(root),
        "--output-dir",
        str(output_dir),
        "--owned",
        "agents",
        "api",
        "--timestamp",
        "2024-02-03T00:00:00+00:00",
        "--artifacts-to-keep",
        "2",
        "--log-level",
        "ERROR",
    ]

    exit_code = mod.main(argv)
    assert exit_code == 0

    run_dir = topic_dir / "20240203-0000"
    assert run_dir.is_dir()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    data = telemetry["payload"]
    assert data["summary"]["status"] == "ok"
    assert data["summary"]["cycle_count"] >= 1
    cycles = {tuple(cycle) for cycle in data["cycles"]}
    assert ("agents", "api", "agents") in cycles

    graph_payload = data["graph"]
    assert graph_payload == {"agents": ["api"], "api": ["agents"]}

    remaining_dirs = {
        path.name for path in topic_dir.iterdir() if path.is_dir()
    }
    assert remaining_dirs == {
        "20240102-0000",
        "20240203-0000",
    }
