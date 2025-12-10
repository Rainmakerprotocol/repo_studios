from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
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

    allowlist = tmp_path / "placeholder_allowlist.txt"
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("", encoding="utf-8")

    timestamp = "2025-12-01T12:34:00+00:00"
    run_dt = datetime.fromisoformat(timestamp)
    run_slug = run_dt.strftime("%Y%m%d_%H%M%S")

    def _fake_loader(script_path: Path, module_name: str, attribute: str):
        if module_name == hygiene_module.DEPENDENCY_MODULE:
            def _fake_dependency_main(argv: list[str]) -> int:
                report_ts = argv[argv.index("--timestamp") + 1]
                slug = datetime.fromisoformat(report_ts).strftime("%Y%m%d_%H%M%S")
                run_dir = dependency_dir / f"{hygiene_module.DEPENDENCY_RUN_PREFIX}-{slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "generated_utc": report_ts,
                    "summary": {
                        "status": "ok",
                        "issue_count": 2,
                    },
                }
                (dependency_dir / "latest_report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.md").write_text("# Dependency\n", encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                return 0

            return _fake_dependency_main

        if module_name == hygiene_module.IMPORT_GRAPH_MODULE:
            def _fake_import_main(argv: list[str]) -> int:
                report_ts = argv[argv.index("--timestamp") + 1]
                slug = datetime.fromisoformat(report_ts).strftime("%Y%m%d_%H%M%S")
                run_dir = import_dir / f"{hygiene_module.IMPORT_GRAPH_RUN_PREFIX}-{slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "generated_utc": report_ts,
                    "summary": {
                        "status": "ok",
                        "module_count": 10,
                    },
                }
                (import_dir / "latest_report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "graph.json").write_text(json.dumps({"a": ["b"]}), encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                return 0

            return _fake_import_main

        if module_name == hygiene_module.PLACEHOLDER_MODULE:
            def _fake_placeholder_run(argv: list[str]) -> dict[str, object]:
                run_dir = placeholder_dir / f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "run_id": f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}",
                    "total_matches": 5,
                }
                (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "matches.json").write_text(json.dumps([]), encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                return payload

            return _fake_placeholder_run

        if module_name == hygiene_module.TYPECHECK_MODULE:
            def _fake_typecheck_main(argv: list[str]) -> int:
                report_ts = argv[argv.index("--timestamp") + 1]
                slug = datetime.fromisoformat(report_ts).strftime("%Y%m%d_%H%M%S")
                run_dir = typecheck_dir / f"{hygiene_module.TYPECHECK_RUN_PREFIX}-{slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "generated_utc": report_ts,
                    "status": "ok",
                    "summary": {
                        "error_count": 0,
                        "files_with_issues": 0,
                    },
                }
                (typecheck_dir / "latest_report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.md").write_text("# Typecheck\n", encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                (run_dir / "raw.txt").write_text("raw", encoding="utf-8")
                return 0

            return _fake_typecheck_main

        if module_name == hygiene_module.REFRESH_BASELINES_MODULE:
            def _fake_refresh_run(argv: list[str]) -> dict[str, object]:
                slug = run_dt.strftime("%Y%m%d-%H%M%S")
                run_dir = baselines_dir / f"{hygiene_module.MYPY_BASELINES_RUN_PREFIX}-{slug.replace('-', '_')}"
                run_dir.mkdir(parents=True, exist_ok=True)
                summary_path = run_dir / "bundle_summary.json"
                summary_path.write_text(json.dumps({"status": "ok"}), encoding="utf-8")
                return {
                    "status": "ok",
                    "run_slug": slug,
                    "artifacts": {"bundle_summary.json": str(summary_path)},
                }

            return _fake_refresh_run

        raise AssertionError(f"Unexpected module request: {module_name}")

    monkeypatch.setattr(hygiene_module, "_load_callable", _fake_loader)

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
        "--placeholder-allowlist",
        str(allowlist),
        "--dependency-requirements-pattern",
        "requirements/base.txt",
        "--dependency-requirements-pattern",
        "requirements/dev.txt",
        "--dependency-skip-pyproject",
        "--import-owned",
        "package.one",
        "package.two",
        "--placeholder-include-ext",
        ".py",
        ".md",
        "--placeholder-pattern",
        "TODO",
        "FIXME",
        "--placeholder-exclude-prefix",
        "docs/",
        "--trigger-batch-cleanup",
        "--refresh-mypy-baselines",
        "--timestamp",
        timestamp,
        "--log-level",
        "ERROR",
    ]

    exit_code = hygiene_module.run(args)
    assert exit_code == 0

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
    assert any(step["status"] == "success" for step in telemetry["steps"])


def test_run_respects_skip_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hygiene_module) -> None:
    repo_root = Path(__file__).resolve().parents[4]

    dependency_dir = tmp_path / "dependency"
    placeholder_dir = tmp_path / "placeholder"
    healthview_root = tmp_path / "healthview"
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("", encoding="utf-8")

    def _fake_loader(script_path: Path, module_name: str, attribute: str):
        if module_name == hygiene_module.DEPENDENCY_MODULE:
            def _dependency_main(argv: list[str]) -> int:
                run_slug = datetime.fromisoformat(argv[argv.index("--timestamp") + 1]).strftime("%Y%m%d_%H%M%S")
                run_dir = dependency_dir / f"{hygiene_module.DEPENDENCY_RUN_PREFIX}-{run_slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "generated_utc": argv[argv.index("--timestamp") + 1],
                    "summary": {
                        "status": "ok",
                        "issue_count": 0,
                    },
                }
                (dependency_dir / "latest_report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "report.md").write_text("# Dependency\n", encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                return 0

            return _dependency_main

        if module_name == hygiene_module.PLACEHOLDER_MODULE:
            def _placeholder_run(argv: list[str]) -> dict[str, object]:
                run_slug = datetime(2025, 12, 1, 1, 0, tzinfo=timezone.utc).strftime("%Y%m%d_%H%M%S")
                run_dir = placeholder_dir / f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}"
                run_dir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "run_id": f"{hygiene_module.PLACEHOLDER_RUN_PREFIX}-{run_slug}",
                    "total_matches": 0,
                }
                (run_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")
                (run_dir / "matches.json").write_text(json.dumps([]), encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                return payload

            return _placeholder_run

        raise AssertionError(f"Unexpected module request: {module_name}")

    monkeypatch.setattr(hygiene_module, "_load_callable", _fake_loader)

    args = [
        "--repo-root",
        str(repo_root),
        "--dependency-output-dir",
        str(dependency_dir),
        "--placeholder-output-dir",
        str(placeholder_dir),
        "--healthview-root",
        str(healthview_root),
        "--placeholder-allowlist",
        str(allowlist),
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


def test_batch_cleanup_plan_writes_bundle(tmp_path: Path, hygiene_module) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    tree_doc = repo_root / ".repo_studios" / "docs"
    tree_doc.mkdir(parents=True, exist_ok=True)
    (tree_doc / "project_tree_overview.md").write_text("", encoding="utf-8")

    cleanup_base = repo_root / "cleanup_runs"
    paths = hygiene_module.Paths(
        repo_root=repo_root,
        dependency_output_dir=tmp_path / "dependency",
        import_graph_output_dir=tmp_path / "import",
        placeholder_output_dir=tmp_path / "placeholder",
        placeholder_allowlist=repo_root / ".repo_studios" / "config" / "placeholder_allowlist.txt",
        batch_cleanup_output_base=cleanup_base,
        typecheck_output_dir=tmp_path / "typecheck",
        mypy_baselines_output_dir=tmp_path / "baselines",
        healthview_root=tmp_path / "healthview",
    )

    options = hygiene_module.Options(
        log_level="INFO",
        artifacts_to_keep=3,
        dependency_keep=3,
        import_graph_keep=3,
        placeholder_keep=3,
        cleanup_keep=2,
        typecheck_keep=3,
        baseline_keep=3,
        run_timestamp=datetime(2025, 12, 1, 12, 30, tzinfo=timezone.utc),
        skip_import_graph=False,
        skip_typecheck=False,
        trigger_batch_cleanup=True,
        refresh_mypy_baselines=False,
        dependency_patterns=(),
        dependency_skip_pyproject=False,
        import_owned=(),
        placeholder_extensions=(),
        placeholder_patterns=(),
        placeholder_exclude_prefixes=None,
    )

    outcome = hygiene_module._batch_cleanup(paths, options)

    assert outcome.status == "success"
    assert outcome.bundle_dir and outcome.bundle_dir.exists()
    assert outcome.summary_path and outcome.summary_path.exists()
    summary_payload = json.loads(outcome.summary_path.read_text(encoding="utf-8"))
    assert summary_payload["status"] == "success"
    assert summary_payload["options"]["dry_run"] is True
    assert summary_payload["steps"]
    assert all(step["status"] == "skipped" for step in summary_payload["steps"])

    latest_summary = cleanup_base / "latest_cleanup_summary.json"
    assert latest_summary.exists()
