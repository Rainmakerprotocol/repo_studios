from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "command_center"
    / "scripts"
    / "orchestrators"
    / "run_dependency_import_hygiene.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("run_dependency_import_hygiene", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="hygiene_module")
def hygiene_module_fixture():
    return _load_module()


def test_run_emits_healthview_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hygiene_module) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    dependency_dir = tmp_path / "dependency"
    import_dir = tmp_path / "import"
    placeholder_dir = tmp_path / "placeholder"
    cleanup_dir = tmp_path / "cleanup"
    typecheck_dir = tmp_path / "typecheck"
    baselines_dir = tmp_path / "baselines"
    healthview_root = tmp_path / "healthview"

    timestamp = "2025-12-01T12:34:00+00:00"

    def fake_dependency(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = dependency_dir / f"{hygiene_module.DEPENDENCY_RUN_PREFIX}-{run_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_utc": options.run_timestamp.isoformat(),
            "summary": {
                "status": "failed",
                "issue_count": 2,
            },
        }
        (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        (run_dir / "report.md").write_text("# Dependency\n", encoding="utf-8")
        (run_dir / "log.txt").write_text("status=failed\n", encoding="utf-8")
        return hygiene_module.DependencyOutcome(
            run_dir=run_dir,
            report_json=run_dir / "report.json",
            report_md=run_dir / "report.md",
            log_path=run_dir / "log.txt",
            payload=payload,
            exit_code=1,
        )

    def fake_import(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = import_dir / f"{hygiene_module.IMPORT_GRAPH_RUN_PREFIX}-{run_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_utc": options.run_timestamp.isoformat(),
            "summary": {
                "status": "ok",
                "module_count": 10,
            },
        }
        (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        (run_dir / "graph.json").write_text(json.dumps({"a": ["b"]}), encoding="utf-8")
        (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
        return hygiene_module.ImportGraphOutcome(
            run_dir=run_dir,
            report_json=run_dir / "report.json",
            graph_path=run_dir / "graph.json",
            log_path=run_dir / "log.txt",
            payload=payload,
        )

    def fake_placeholder(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = placeholder_dir / f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}",
            "total_matches": 5,
        }
        (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        (run_dir / "matches.json").write_text(json.dumps([]), encoding="utf-8")
        (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
        return hygiene_module.PlaceholderOutcome(
            run_dir=run_dir,
            report_json=run_dir / "report.json",
            matches_json=run_dir / "matches.json",
            log_path=run_dir / "log.txt",
            payload=payload,
        )

    def fake_cleanup(paths, options):
        bundle_dir = cleanup_dir / f"run_batch_cleanup-{options.run_timestamp.strftime('%Y-%m-%d_%H%M%S')}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        summary_path = bundle_dir / "SUMMARY.md"
        summary_path.write_text("cleanup summary", encoding="utf-8")
        log_path = bundle_dir / "cleanup_log.txt"
        log_path.write_text("log", encoding="utf-8")
        bundle_summary = bundle_dir / "bundle_summary.json"
        bundle_summary.write_text(json.dumps({"status": "success"}), encoding="utf-8")
        return hygiene_module.BatchCleanupOutcome(
            bundle_dir=bundle_dir,
            summary_path=summary_path,
            log_path=log_path,
            bundle_summary=bundle_summary,
            status="success",
        )

    def fake_typecheck(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = typecheck_dir / f"{hygiene_module.TYPECHECK_RUN_PREFIX}-{run_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_utc": options.run_timestamp.isoformat(),
            "status": "error",
            "summary": {
                "error_count": 3,
                "files_with_issues": 2,
            },
        }
        (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        (run_dir / "report.md").write_text("# Typecheck\n", encoding="utf-8")
        (run_dir / "log.txt").write_text("status=error\n", encoding="utf-8")
        (run_dir / "raw.txt").write_text("raw", encoding="utf-8")
        return hygiene_module.TypecheckOutcome(
            run_dir=run_dir,
            report_json=run_dir / "report.json",
            report_md=run_dir / "report.md",
            log_path=run_dir / "log.txt",
            raw_output=run_dir / "raw.txt",
            payload=payload,
        )

    def fake_baselines(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        bundle_dir = baselines_dir / f"{hygiene_module.MYPY_BASELINES_RUN_PREFIX}-{run_slug}"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        summary_path = bundle_dir / "bundle_summary.json"
        summary_path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
        payload = {
            "status": "ok",
            "run_slug": options.run_timestamp.strftime("%Y%m%d_%H%M%S"),
            "artifacts": {"bundle_summary.json": str(summary_path)},
        }
        return hygiene_module.BaselineOutcome(
            run_dir=bundle_dir,
            summary_path=summary_path,
            status="ok",
            payload=payload,
        )

    monkeypatch.setattr(hygiene_module, "_dependency_report", fake_dependency)
    monkeypatch.setattr(hygiene_module, "_import_graph_report", fake_import)
    monkeypatch.setattr(hygiene_module, "_placeholder_scan", fake_placeholder)
    monkeypatch.setattr(hygiene_module, "_batch_cleanup", fake_cleanup)
    monkeypatch.setattr(hygiene_module, "_typecheck_report", fake_typecheck)
    monkeypatch.setattr(hygiene_module, "_refresh_baselines", fake_baselines)

    args = [
        "--repo-root",
        str(repo_root),
        "--dependency-output-dir",
        str(dependency_dir),
        "--import-graph-output-dir",
        str(import_dir),
        "--placeholder-output-dir",
        str(placeholder_dir),
        "--batch-cleanup-output-base",
        str(cleanup_dir),
        "--typecheck-output-dir",
        str(typecheck_dir),
        "--mypy-baselines-output-dir",
        str(baselines_dir),
        "--healthview-root",
        str(healthview_root),
        "--trigger-batch-cleanup",
        "--refresh-mypy-baselines",
        "--timestamp",
        timestamp,
        "--log-level",
        "ERROR",
    ]

    exit_code = hygiene_module.run(args)
    assert exit_code == 1  # cleanup marked success; dependency detected issues (pipeline failure)

    topic_dir = healthview_root / "healthview" / "dependency_import_hygiene"
    runs = sorted(child for child in topic_dir.iterdir() if child.is_dir())
    assert runs, "expected orchestrator run directory"
    run_folder = runs[0]
    manifest_path = run_folder / "manifest.json"
    summary_path = run_folder / "summary.md"
    telemetry_path = run_folder / "telemetry.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["topic"] == "dependency_import_hygiene"
    artifacts = manifest["artifacts"]
    assert artifacts["dependency_report"].endswith("report.json")
    assert artifacts["typecheck_report"].endswith("report.json")
    assert artifacts["mypy_baseline_summary"].endswith("bundle_summary.json")

    summary_text = summary_path.read_text(encoding="utf-8")
    assert "dependency_issue_count" in summary_text
    assert "mypy_baseline_status" in summary_text

    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    assert telemetry["topic"] == hygiene_module.TOPIC_SLUG
    assert any(step["status"] == "failed" for step in telemetry["steps"])


def test_run_respects_skip_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hygiene_module) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    dependency_dir = tmp_path / "dependency"
    placeholder_dir = tmp_path / "placeholder"
    healthview_root = tmp_path / "healthview"

    def fake_dependency(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = dependency_dir / f"{hygiene_module.DEPENDENCY_RUN_PREFIX}-{run_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_utc": options.run_timestamp.isoformat(),
            "summary": {
                "status": "ok",
                "issue_count": 0,
            },
        }
        (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        (run_dir / "report.md").write_text("# Dependency\n", encoding="utf-8")
        (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
        return hygiene_module.DependencyOutcome(
            run_dir=run_dir,
            report_json=run_dir / "report.json",
            report_md=run_dir / "report.md",
            log_path=run_dir / "log.txt",
            payload=payload,
            exit_code=0,
        )

    def fake_placeholder(paths, options):
        run_slug = options.run_timestamp.strftime("%Y%m%d_%H%M%S")
        run_dir = placeholder_dir / f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}"
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "run_id": f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}",
            "total_matches": 0,
        }
        (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
        (run_dir / "matches.json").write_text(json.dumps([]), encoding="utf-8")
        (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
        return hygiene_module.PlaceholderOutcome(
            run_dir=run_dir,
            report_json=run_dir / "report.json",
            matches_json=run_dir / "matches.json",
            log_path=run_dir / "log.txt",
            payload=payload,
        )

    monkeypatch.setattr(hygiene_module, "_dependency_report", fake_dependency)
    monkeypatch.setattr(hygiene_module, "_placeholder_scan", fake_placeholder)
    monkeypatch.setattr(
        hygiene_module,
        "_import_graph_report",
        lambda *args, **kwargs: pytest.fail("import graph should be skipped"),
    )
    monkeypatch.setattr(
        hygiene_module,
        "_batch_cleanup",
        lambda *args, **kwargs: pytest.fail("cleanup should be skipped"),
    )
    monkeypatch.setattr(
        hygiene_module,
        "_typecheck_report",
        lambda *args, **kwargs: pytest.fail("typecheck should be skipped"),
    )
    monkeypatch.setattr(
        hygiene_module,
        "_refresh_baselines",
        lambda *args, **kwargs: pytest.fail("baseline refresh should be skipped"),
    )

    args = [
        "--repo-root",
        str(repo_root),
        "--dependency-output-dir",
        str(dependency_dir),
        "--placeholder-output-dir",
        str(placeholder_dir),
        "--healthview-root",
        str(healthview_root),
        "--skip-import-graph",
        "--skip-typecheck",
        "--timestamp",
        "2025-12-01T01:00:00+00:00",
        "--log-level",
        "ERROR",
    ]

    exit_code = hygiene_module.run(args)
    assert exit_code == 0

    topic_dir = healthview_root / "healthview" / "dependency_import_hygiene"
    runs = sorted(child for child in topic_dir.iterdir() if child.is_dir())
    assert runs, "expected orchestrator run directory"
    summary_text = (runs[0] / "summary.md").read_text(encoding="utf-8")
    assert "import_graph_status: skipped" in summary_text
    assert "typecheck_status: skipped" in summary_text
