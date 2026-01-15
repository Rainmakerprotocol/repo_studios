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

    def _fake_loader(script_path: Path, module_name: str, attribute: str):
        if module_name == hygiene_module.DEPENDENCY_MODULE:
            def _fake_dependency_main(argv: list[str]) -> int:
                report_ts = argv[argv.index("--timestamp") + 1]
                # Match format used by orchestrator: %Y%m%d-%H%M
                ts_slug = datetime.fromisoformat(report_ts).strftime("%Y%m%d-%H%M")
                # HOP-compliant path: output_dir/timestamp (no viewer/topic)
                run_dir = dependency_dir / ts_slug
                run_dir.mkdir(parents=True, exist_ok=True)
                # telemetry.json with payload structure
                telemetry = {
                    "generated_utc": report_ts,
                    "payload": {
                        "summary": {
                            "status": "ok",
                            "issue_count": 2,
                        },
                    },
                }
                (run_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")
                (run_dir / "summary.md").write_text("# Dependency\n", encoding="utf-8")
                return 0

            return _fake_dependency_main

        if module_name == hygiene_module.IMPORT_GRAPH_MODULE:
            def _fake_import_main(argv: list[str]) -> int:
                report_ts = argv[argv.index("--timestamp") + 1]
                # Match format used by orchestrator: %Y%m%d-%H%M (no seconds)
                ts_slug = datetime.fromisoformat(report_ts).strftime("%Y%m%d-%H%M")
                # HOP-compliant path: output_dir/timestamp (no viewer/topic)
                run_dir = import_dir / ts_slug
                run_dir.mkdir(parents=True, exist_ok=True)
                # telemetry.json must have payload.summary.status for status extraction
                # and payload.graph for graph_path detection
                telemetry = {
                    "generated_utc": report_ts,
                    "payload": {
                        "summary": {
                            "status": "ok",
                            "module_count": 10,
                        },
                        "graph": {"a": ["b"]},
                    },
                }
                (run_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")
                (run_dir / "log.txt").write_text("status=ok\n", encoding="utf-8")
                return 0

            return _fake_import_main

        if module_name == hygiene_module.PLACEHOLDER_MODULE:
            def _fake_placeholder_run(argv: list[str]) -> dict[str, object]:
                ts_slug = run_dt.strftime("%Y%m%d-%H%M")
                run_dir = placeholder_dir / ts_slug
                run_dir.mkdir(parents=True, exist_ok=True)
                telemetry = {
                    "generated_utc": run_dt.isoformat(),
                    "payload": {
                        "summary": {
                            "status": "ok",
                            "issue_count": 5,
                        }
                    },
                }
                (run_dir / "manifest.json").write_text(
                    json.dumps({"topic": "code_placeholders", "status": "ok"}),
                    encoding="utf-8",
                )
                (run_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")
                (run_dir / "summary.md").write_text("# Placeholders\n", encoding="utf-8")
                return {
                    "run_id": ts_slug,
                }

            return _fake_placeholder_run

        if module_name == hygiene_module.TYPECHECK_MODULE:
            def _fake_typecheck_main(argv: list[str]) -> int:
                report_ts = argv[argv.index("--timestamp") + 1]
                # HOP-compliant: just YYYYMMDD-HHMM
                ts_slug = datetime.fromisoformat(report_ts).strftime("%Y%m%d-%H%M")
                run_dir = typecheck_dir / ts_slug
                run_dir.mkdir(parents=True, exist_ok=True)
                manifest = {
                    "generated_utc": report_ts,
                    "status": "ok",
                    "summary": {
                        "error_count": 0,
                        "files_with_issues": 0,
                    },
                }
                (run_dir / "telemetry.json").write_text(json.dumps({"payload": manifest}), encoding="utf-8")
                (run_dir / "summary.md").write_text("# Typecheck\n", encoding="utf-8")
                (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
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
    # Dependency report now uses telemetry.json as the report file
    assert artifacts["dependency_report"].endswith("telemetry.json")
    assert artifacts["typecheck_report"].endswith("telemetry.json")
    assert artifacts["mypy_baseline_summary"].endswith("bundle_summary.json")
    assert artifacts["placeholder_telemetry"].endswith("telemetry.json")
    assert artifacts["placeholder_summary"].endswith("summary.md")

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
                ts_slug = datetime.fromisoformat(argv[argv.index("--timestamp") + 1]).strftime("%Y%m%d-%H%M")
                run_dir = dependency_dir / ts_slug
                run_dir.mkdir(parents=True, exist_ok=True)
                report_ts = argv[argv.index("--timestamp") + 1]
                telemetry = {
                    "generated_utc": report_ts,
                    "payload": {
                        "summary": {
                            "status": "ok",
                            "issue_count": 0,
                        },
                    },
                }
                (run_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")
                (run_dir / "summary.md").write_text("# Dependency\n", encoding="utf-8")
                return 0

            return _dependency_main

        if module_name == hygiene_module.PLACEHOLDER_MODULE:
            def _placeholder_run(argv: list[str]) -> dict[str, object]:
                ts_slug = datetime(2025, 12, 1, 1, 0, tzinfo=timezone.utc).strftime("%Y%m%d-%H%M")
                run_dir = placeholder_dir / ts_slug
                run_dir.mkdir(parents=True, exist_ok=True)
                telemetry = {
                    "generated_utc": datetime(2025, 12, 1, 1, 0, tzinfo=timezone.utc).isoformat(),
                    "payload": {
                        "summary": {
                            "status": "ok",
                            "issue_count": 0,
                        }
                    },
                }
                (run_dir / "manifest.json").write_text(
                    json.dumps({"topic": "code_placeholders", "status": "ok"}),
                    encoding="utf-8",
                )
                (run_dir / "telemetry.json").write_text(json.dumps(telemetry), encoding="utf-8")
                (run_dir / "summary.md").write_text("# Placeholders\n", encoding="utf-8")
                return {"run_id": ts_slug}

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
    (repo_root / ".repo_studios").mkdir()
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
        orchestrator_output_dir=tmp_path / "healthview",
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
        typecheck_targets=(".repo_studios",),
        allow_missing_typecheck_targets=False,
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

    assert not (cleanup_base / "latest_cleanup_summary.json").exists()
    assert not (cleanup_base / "latest_cleanup_log.txt").exists()
    assert not (cleanup_base / "latest_bundle_summary.json").exists()
