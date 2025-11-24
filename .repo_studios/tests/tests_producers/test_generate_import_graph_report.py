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

    output_dir = root / ".repo_studios" / "reports" / "producer_reports" / "import_graph_reports"
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

    run_dir = output_dir / "import_graph-20240101_000000"
    assert run_dir.is_dir()

    report_path = run_dir / "report.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["summary"]["status"] == "no_targets"
    assert data["summary"]["module_count"] == 0
    assert data["summary"]["edge_count"] == 0
    assert data["summary"]["cycle_count"] == 0
    assert data["owned_packages_resolved"] == []

    latest_graph = output_dir / "latest_graph.json"
    assert latest_graph.is_file()
    assert json.loads(latest_graph.read_text(encoding="utf-8")) == {}

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "status=no_targets" in log_text


def test_cycle_detection_and_pruning(tmp_path: Path) -> None:
    mod = _load_module()
    root = tmp_path / "repo"
    root.mkdir()

    _write(root / "agents" / "__init__.py", "")
    _write(root / "agents" / "foo.py", "import api\n")
    _write(root / "api" / "__init__.py", "")
    _write(root / "api" / "bar.py", "import agents\n")

    output_dir = root / ".repo_studios" / "reports" / "producer_reports" / "import_graph_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_one = output_dir / "import_graph-20240101_000000"
    stale_one.mkdir()
    (stale_one / "report.json").write_text("{}\n", encoding="utf-8")
    stale_two = output_dir / "import_graph-20240102_000000"
    stale_two.mkdir()
    (stale_two / "report.json").write_text("{}\n", encoding="utf-8")

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

    run_dir = output_dir / "import_graph-20240203_000000"
    assert run_dir.is_dir()

    report_path = run_dir / "report.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["summary"]["status"] == "ok"
    assert data["summary"]["cycle_count"] >= 1
    cycles = {tuple(cycle) for cycle in data["cycles"]}
    assert ("agents", "api", "agents") in cycles

    graph_payload = json.loads((run_dir / "graph.json").read_text(encoding="utf-8"))
    assert graph_payload == {"agents": ["api"], "api": ["agents"]}

    latest_graph = json.loads((output_dir / "latest_graph.json").read_text(encoding="utf-8"))
    assert latest_graph == graph_payload

    remaining_dirs = {
        path.name for path in output_dir.iterdir() if path.is_dir() and path.name.startswith("import_graph-")
    }
    assert remaining_dirs == {
        "import_graph-20240102_000000",
        "import_graph-20240203_000000",
    }

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "cycle_count=1" in log_text
