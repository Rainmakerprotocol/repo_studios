from __future__ import annotations

import json
import sys
import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_dependency_hygiene_report.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_dependency_hygiene_report", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_reports_written_without_issues(tmp_path):
    mod = _load_module()
    root = tmp_path / "workspace"
    root.mkdir()

    _write(
        root / "requirements.txt",
        "requests==2.31.0\n\n# comment\n",
    )
    _write(
        root / "requirements-dev.txt",
        "pytest==8.4.2\n",
    )
    _write(
        root / "pyproject.toml",
        """
[project]
dependencies = [
    "rich==13.7.1",
    "typer==0.12.3"
]
        """.strip()
        + "\n",
    )

    output_dir = root / ".repo_studios" / "reports" / "producer_reports" / "dependency_hygiene_reports"

    exit_code = mod.main(
        [
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
    )

    assert exit_code == 0
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240101_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "passed"
    assert report["summary"]["issue_count"] == 0
    assert report["summary"]["requirements_scanned"] == 2
    assert report["summary"]["pyproject_scanned"] is True
    assert report["requirements_files"] == [
        "requirements-dev.txt",
        "requirements.txt",
    ]

    markdown = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "# Dependency Hygiene Report" in markdown
    assert "- (none)" in markdown

    log_text = (run_dir / "log.txt").read_text(encoding="utf-8")
    assert "status=passed" in log_text

    assert (output_dir / "latest_report.json").is_file()
    assert (output_dir / "latest_report.md").is_file()
    assert (output_dir / "latest_report.log").is_file()


def test_threshold_breach_and_pruning(tmp_path):
    mod = _load_module()
    root = tmp_path / "project"
    root.mkdir()

    output_dir = root / ".repo_studios" / "reports" / "producer_reports" / "dependency_hygiene_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    stale_names = [
        f"{mod.RUN_PREFIX}-20240101_000000",
        f"{mod.RUN_PREFIX}-20240115_000000",
    ]
    for name in stale_names:
        stale_dir = output_dir / name
        stale_dir.mkdir()
        (stale_dir / "report.json").write_text("{}\n", encoding="utf-8")

    _write(
        root / "requirements" / "extra.txt",
        "django>=4.2\nrequests==2.31.0\ndjango>=4.2\n",
    )
    _write(
        root / "requirements-dev.txt",
        "pytest\n",
    )
    _write(
        root / "pyproject.toml",
        """
[tool.poetry]
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "0.110"
        """.strip()
        + "\n",
    )

    exit_code = mod.main(
        [
            "--repo-root",
            str(root),
            "--output-dir",
            str(output_dir),
            "--timestamp",
            "2024-02-03T00:00:00+00:00",
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "ERROR",
        ]
    )

    assert exit_code == 1
    run_dir = output_dir / f"{mod.RUN_PREFIX}-20240203_000000"
    assert run_dir.is_dir()

    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report["summary"]["status"] == "failed"
    assert report["summary"]["issue_count"] >= 1
    kinds = {issue["kind"] for issue in report["issues"]}
    assert "duplicate" in kinds
    assert "unpinned" in kinds

    run_dirs = {path.name for path in output_dir.iterdir() if path.is_dir() and path.name.startswith(mod.RUN_PREFIX)}
    assert run_dirs == {
        f"{mod.RUN_PREFIX}-20240115_000000",
        f"{mod.RUN_PREFIX}-20240203_000000",
    }

    log_text = (output_dir / "latest_report.log").read_text(encoding="utf-8")
    assert "failure_reason=dependency hygiene issues detected" in log_text
