from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_CONSUMER_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "producers" / "generate_code_doc_churn_report.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
        env=merged_env,
    )


def _init_repo(path: Path) -> None:
    _git(["init"], cwd=path)
    _git(["config", "user.name", "Test User"], cwd=path)
    _git(["config", "user.email", "test@example.com"], cwd=path)


def _commit(path: Path, message: str, *, author_date: str | None = None) -> None:
    _git(["add", "-A"], cwd=path)
    env = None
    if author_date:
        env = {"GIT_AUTHOR_DATE": author_date, "GIT_COMMITTER_DATE": author_date}
    _git(["commit", "-m", message], cwd=path, env=env)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_doc_index_telemetry(repo_root: Path, payload: dict, *, timestamp: str = "20250101-0000") -> None:
    telemetry = {"payload": payload}
    telemetry_path = (
        repo_root
        / ".repo_studios"
        / "reports"
        / "producer_reports"
        / "healthview"
        / "doc_index"
        / timestamp
        / "telemetry.json"
    )
    _write_json(telemetry_path, telemetry)


def _minimal_doc_index(doc_paths: list[str]) -> dict:
    documents = []
    for doc_path in doc_paths:
        documents.append(
            {
                "folder": str(Path(doc_path).parent),
                "filename": doc_path,
                "owners": ["docs-team"],
                "modified_utc": "2025-01-01T00:00:00+00:00",
                "h1_headings": [],
                "h2_headings": [],
                "links": [],
                "description": None,
                "size_bytes": 0,
                "tags": [],
                "status": None,
                "frontmatter": None,
                "contains_placeholder": False,
            }
        )
    return {
        "schema_version": 1,
        "generated_utc": "2025-01-01T00:00:00+00:00",
        "repo_root": "repo",
        "summary": {},
        "metrics": {},
        "documents": documents,
    }


def test_churn_detects_missing_doc_updates(tmp_path):
    module = _load_module("generate_code_doc_churn_report", _CONSUMER_MODULE_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".repo_studios").mkdir()
    _init_repo(repo)

    (repo / "src").mkdir()
    (repo / "src" / "widget.py").write_text("print('hi')\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "src.md").write_text("# Src\n", encoding="utf-8")
    _commit(repo, "initial commit with docs", author_date="2024-01-01T00:00:00+00:00")

    # Modify code without touching docs
    (repo / "src" / "widget.py").write_text("print('hello')\n", encoding="utf-8")
    _commit(repo, "update widget")

    doc_index_payload = _minimal_doc_index(["docs/src.md"])
    _write_doc_index_telemetry(repo, doc_index_payload)

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        result = module.run(
            argv=[
                "--repo-root",
                str(repo),
                "--git-window",
                "30 days",
                "--output-dir",
                str(repo / ".repo_studios" / "reports" / "producer_reports"),
            ]
        )
    finally:
        os.chdir(cwd)

    summary = result["summary"]
    assert summary["modules_without_doc_updates"] == 1
    telemetry_path = Path(result["artifacts"]["telemetry.json"])
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    payload = telemetry["payload"]
    modules = payload["modules_missing_docs"]
    assert any(module_entry["module"] == "src" for module_entry in modules)


def test_churn_skips_when_docs_updated(tmp_path):
    module = _load_module("generate_code_doc_churn_report", _CONSUMER_MODULE_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".repo_studios").mkdir()
    _init_repo(repo)

    (repo / "lib").mkdir()
    (repo / "lib" / "core.py").write_text("print('core')\n", encoding="utf-8")
    _commit(repo, "initial core")

    (repo / "lib" / "core.py").write_text("print('core2')\n", encoding="utf-8")
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "lib.md").write_text("# Lib\n", encoding="utf-8")
    _commit(repo, "update core with docs")

    doc_index_payload = _minimal_doc_index(["docs/lib.md"])
    _write_doc_index_telemetry(repo, doc_index_payload)

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        result = module.run(
            argv=[
                "--repo-root",
                str(repo),
                "--git-window",
                "30 days",
                "--output-dir",
                str(repo / ".repo_studios" / "reports" / "producer_reports"),
            ]
        )
    finally:
        os.chdir(cwd)

    summary = result["summary"]
    assert summary["modules_without_doc_updates"] == 0


def test_churn_honors_allowlist(tmp_path):
    module = _load_module("generate_code_doc_churn_report", _CONSUMER_MODULE_PATH)

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".repo_studios").mkdir()
    _init_repo(repo)

    (repo / "service").mkdir()
    (repo / "service" / "api.py").write_text("print('api')\n", encoding="utf-8")
    _commit(repo, "initial api")

    (repo / "service" / "api.py").write_text("print('api2')\n", encoding="utf-8")
    _commit(repo, "update api")

    allowlist_path = repo / ".repo_studios" / "config" / "code_doc_churn_allowlist.txt"
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    allowlist_path.write_text("service\n", encoding="utf-8")

    cwd = os.getcwd()
    os.chdir(repo)
    try:
        result = module.run(
            argv=[
                "--repo-root",
                str(repo),
                "--git-window",
                "30 days",
                "--output-dir",
                str(repo / ".repo_studios" / "reports" / "producer_reports"),
                "--allowlist",
                str(allowlist_path),
            ]
        )
    finally:
        os.chdir(cwd)

    summary = result["summary"]
    assert summary["modules_without_doc_updates"] == 0