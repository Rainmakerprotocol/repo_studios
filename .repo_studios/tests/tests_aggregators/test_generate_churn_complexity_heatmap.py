from __future__ import annotations

import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


_AGGREGATOR_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "aggregators" / "generate_churn_complexity_heatmap.py"
)


def _load_module(name: str, path: Path):
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_consumer_bundle(
    root: Path,
    *,
    logs_dir: Path,
    junit_path: Path,
    generated: datetime,
) -> Path:
    run_dir = root / generated.strftime("%Y-%m-%d_%H%M")
    run_dir.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "schema_version": 1,
        "meta": {
            "generated_at": generated.isoformat(timespec="seconds"),
            "logs_dir": str(logs_dir),
            "junit": str(junit_path),
            "full_log": None,
        },
        "summary": {
            "failed": 1,
            "errors": 0,
        },
    }
    report_path = run_dir / "report.json"
    report_path.write_text(json.dumps(report_payload), encoding="utf-8")
    summary_payload = {
        "schema_version": 1,
        "generated_at": generated.isoformat(timespec="seconds"),
        "source": "producer",
        "producer_report": None,
        "logs_dir": str(logs_dir),
        "logs_source": None,
        "artifacts": {
            "report_json": str(report_path.resolve()),
            "report_md": str((run_dir / "report.md").resolve()),
        },
        "summary": report_payload.get("summary"),
    }
    summary_path = run_dir / "bundle_summary.json"
    summary_path.write_text(json.dumps(summary_payload), encoding="utf-8")
    return summary_path


def _write_metrics(path: Path) -> Path:
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "items": [
            {"file": "pkg/foo.py", "churn": 5, "complexity": 10},
            {"file": "pkg/bar.py", "churn": 2, "complexity": 3},
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_junit(path: Path, failures: dict[str, int]) -> Path:
    lines = ["<?xml version='1.0' encoding='utf-8'?>", "<testsuite>"]
    for file_path, count in failures.items():
        for index in range(count):
            lines.append("  <testcase classname='pkg.test_case' name='test_%d' file='%s'>" % (index, file_path))
            lines.append("    <failure message='boom'>trace</failure>")
            lines.append("  </testcase>")
    lines.append("</testsuite>")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_prefers_consumer_bundle(tmp_path):
    aggregator = _load_module("generate_churn_complexity_heatmap", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()
    (repo_root / "pkg").mkdir()
    (repo_root / "pkg" / "foo.py").write_text("print('foo')\n", encoding="utf-8")
    (repo_root / "pkg" / "bar.py").write_text("print('bar')\n", encoding="utf-8")

    logs_dir = repo_root / "logs"
    logs_dir.mkdir()
    junit_path = _write_junit(logs_dir / "junit_consumer.xml", {"pkg/foo.py": 2})

    summary_root = repo_root / "consumer_bundle"
    summary_path = _write_consumer_bundle(
        summary_root,
        logs_dir=logs_dir,
        junit_path=junit_path,
        generated=datetime(2025, 11, 24, 12, 0, tzinfo=UTC),
    )

    metrics_path = _write_metrics(repo_root / "metrics.json")
    output_base = repo_root / "aggregator_output"

    result = aggregator.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-base",
            str(output_base),
            "--test-log-summary",
            str(summary_path),
            "--metrics-source",
            str(metrics_path),
            "--logs-dir",
            str(logs_dir),
            "--artifacts-to-keep",
            "3",
        ]
    )

    assert result["mode"] == "consumer"
    heatmap_json = json.loads(Path(result["heatmap_json"]).read_text(encoding="utf-8"))
    assert heatmap_json["mode"] == "consumer"
    items = {item["file"]: item for item in heatmap_json["items"]}
    assert items["pkg/foo.py"]["failures"] == 2
    assert items["pkg/foo.py"]["score"] > items["pkg/bar.py"]["score"]
    assert Path(result["bundle_summary"]).exists()


def test_fallback_to_logs_when_summary_missing(tmp_path):
    aggregator = _load_module("generate_churn_complexity_heatmap", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()
    (repo_root / "pkg").mkdir()
    (repo_root / "pkg" / "foo.py").write_text("print('foo')\n", encoding="utf-8")

    logs_dir = repo_root / "logs"
    logs_dir.mkdir()
    _write_junit(logs_dir / "junit_fallback.xml", {"pkg/foo.py": 1})

    metrics_path = _write_metrics(repo_root / "metrics.json")
    output_base = repo_root / "aggregator_output"

    result = aggregator.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-base",
            str(output_base),
            "--test-log-summary",
            str(repo_root / "missing" / "bundle_summary.json"),
            "--metrics-source",
            str(metrics_path),
            "--logs-dir",
            str(logs_dir),
        ]
    )

    assert result["mode"] == "logs_fallback"
    assert any("Consumer bundle summary not found" in note for note in result["notes"])
    heatmap_json = json.loads(Path(result["heatmap_json"]).read_text(encoding="utf-8"))
    files = {item["file"]: item for item in heatmap_json["items"]}
    assert files["pkg/foo.py"]["failures"] == 1


def test_retention_prunes_old_runs(tmp_path):
    aggregator = _load_module("generate_churn_complexity_heatmap", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()
    (repo_root / "pkg").mkdir()
    (repo_root / "pkg" / "foo.py").write_text("print('foo')\n", encoding="utf-8")

    logs_dir = repo_root / "logs"
    logs_dir.mkdir()
    _write_junit(logs_dir / "junit.xml", {"pkg/foo.py": 1})
    metrics_path = _write_metrics(repo_root / "metrics.json")

    output_base = repo_root / "aggregator_output"
    output_base.mkdir()
    (output_base / "churn_complexity_heatmap-2025-11-20_000000").mkdir()
    (output_base / "churn_complexity_heatmap-2025-11-21_000000").mkdir()

    result = aggregator.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-base",
            str(output_base),
            "--metrics-source",
            str(metrics_path),
            "--logs-dir",
            str(logs_dir),
            "--artifacts-to-keep",
            "2",
        ]
    )

    remaining = [p for p in output_base.iterdir() if p.is_dir()]
    assert len(remaining) == 2
    pruned = {Path(p).name for p in result["pruned"]}
    assert "churn_complexity_heatmap-2025-11-20_000000" in pruned


def test_main_returns_nonzero_when_no_python_files(tmp_path):
    aggregator = _load_module("generate_churn_complexity_heatmap", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".repo_studios").mkdir()
    (repo_root / "logs").mkdir()

    exit_code = aggregator.main(
        [
            "--repo-root",
            str(repo_root),
            "--output-base",
            str(repo_root / "out"),
            "--logs-dir",
            str(repo_root / "logs"),
            "--test-log-summary",
            str(repo_root / "missing"),
            "--metrics-source",
            str(repo_root / "missing_metrics.json"),
        ]
    )

    assert exit_code == 1


def test_collect_git_churn_handles_oserror(tmp_path, monkeypatch):
    aggregator = _load_module("generate_churn_complexity_heatmap", _AGGREGATOR_PATH)

    def _boom(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(aggregator.subprocess, "run", _boom)
    logger = aggregator._configure_logging("INFO", False)

    churn = aggregator._collect_git_churn(tmp_path, 5, logger)
    assert not churn


def test_load_junit_failures_uses_classname_when_file_missing(tmp_path):
    aggregator = _load_module("generate_churn_complexity_heatmap", _AGGREGATOR_PATH)

    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    junit_path = repo_root / "junit.xml"
    junit_path.write_text(
        "\n".join(
            [
                "<?xml version='1.0' encoding='utf-8'?>",
                "<testsuite>",
                "  <testcase classname='pkg.tests.test_mod' name='test_0'>",
                "    <failure message='boom'>trace</failure>",
                "  </testcase>",
                "</testsuite>",
            ]
        ),
        encoding="utf-8",
    )

    logger = aggregator._configure_logging("INFO", False)
    failures = aggregator._load_junit_failures(junit_path, repo_root, logger)

    assert failures["pkg/tests/test_mod.py"] == 1
