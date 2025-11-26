from __future__ import annotations

import importlib.util
import json
import sys
import uuid
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / ".repo_studios" / "scripts" / "orchestrators" / "run_fault_pipeline.py"


def _load_module() -> ModuleType:
    module_name = f"run_fault_pipeline_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _sample_stacks() -> str:
    return (
        "Current thread 0x0001:\n"
        '  File "/svc/worker.py", line 8, in work\n'
        "\n"
        "Thread 0x0002:\n"
        '  File "/svc/helper.py", line 3, in assist\n'
    )


def _prepare_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    run_dir = repo_root / ".repo_studios" / "faulthandler" / "2025-01-01_000000"
    run_dir.mkdir(parents=True)
    (run_dir / "stacks.log").write_text(_sample_stacks(), encoding="utf-8")
    return repo_root


def test_run_fault_pipeline_executes_producer_and_consumer(tmp_path: Path) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()

    result = module.run(["--repo-root", str(repo_root), "--log-level", "INFO"])

    assert result["status"] == "success"
    summary_path = Path(result["summary_path"])
    bundle_summary_path = Path(result["bundle_summary_path"])
    log_path = Path(result["log_path"])
    assert summary_path.exists()
    assert bundle_summary_path.exists()
    assert log_path.exists()

    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["status"] == "success"
    assert payload["producer"]["status"] == "success"
    assert payload["consumer"]["status"] == "success"
    assert payload["severity_buckets"]["repeat_offender"] >= 0

    mirror_dir = repo_root / ".repo_studios" / "command_center" / "reports" / "fault_pipeline_orchestrator"
    assert any(node.is_dir() for node in mirror_dir.iterdir())
    latest_summary = mirror_dir / "latest_summary.json"
    assert latest_summary.exists()


def test_run_fault_pipeline_can_skip_producer_with_reuse(tmp_path: Path) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()

    first = module.run(["--repo-root", str(repo_root), "--log-level", "INFO"])
    assert first["status"] == "success"

    second = module.run(
        [
            "--repo-root",
            str(repo_root),
            "--skip-producer",
            "--log-level",
            "INFO",
            "--reuse-report",
            first["producer"]["report_path"],
        ]
    )

    assert second["status"] == "success"
    payload = json.loads(Path(second["summary_path"]).read_text(encoding="utf-8"))
    producer_step = next(step for step in payload["steps"] if step["name"] == "collect_faulthandler_reports")
    assert producer_step["status"] == "skipped"
    consumer_step = next(step for step in payload["steps"] if step["name"] == "generate_fault_artifacts")
    assert consumer_step["status"] == "success"


def test_run_fault_pipeline_prunes_history(tmp_path: Path) -> None:
    repo_root = _prepare_repo(tmp_path)
    module = _load_module()

    output_dir = repo_root / ".repo_studios" / "reports" / "orchestrator_runs" / "fault_pipeline"
    for slug in ("20240101_000000", "20240102_000000", "20240103_000000"):
        bundle = output_dir / f"fault_pipeline-{slug}"
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "summary.json").write_text("{}\n", encoding="utf-8")
        (bundle / "SUMMARY.md").write_text("placeholder\n", encoding="utf-8")
        (bundle / "bundle_summary.json").write_text("{}\n", encoding="utf-8")
        (bundle / "pipeline.log").write_text("log\n", encoding="utf-8")

    result = module.run([
        "--repo-root",
        str(repo_root),
        "--artifacts-to-keep",
        "2",
        "--log-level",
        "INFO",
    ])

    assert result["status"] == "success"
    remaining = [node for node in output_dir.iterdir() if node.is_dir()]
    assert len(remaining) == 2
