from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "validate_import_boundaries.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_import_boundaries", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_graph(repo_root: Path, name: str, payload: dict[str, list[str]]) -> Path:
    graph_dir = repo_root / ".repo_studios" / "reports" / "producer_reports" / "healthview" / "import_graph" / name
    graph_dir.mkdir(parents=True, exist_ok=True)
    telemetry_path = graph_dir / "telemetry.json"
    telemetry_path.write_text(json.dumps({"payload": {"graph": payload}}), encoding="utf-8")
    return telemetry_path


def _set_fixed_datetime(monkeypatch, module, value):
    class _FixedDateTime(module.dt.datetime):
        @classmethod
        def now(cls, tz: module.dt.tzinfo | None = None):  # type: ignore[override]
            if tz is None:
                return value
            return value.astimezone(tz)

    monkeypatch.setattr(module.dt, "datetime", _FixedDateTime)


def test_emits_structured_artifacts_without_violations(tmp_path, monkeypatch):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_graph(repo_root, "20240101_000000", {"agents": [], "api": []})

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=mod.dt.timezone.utc),
    )

    payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "DEBUG",
        ]
    )

    assert payload["status"] == "ok"
    assert payload["summary"]["violation_count"] == 0

    output_dir = Path(payload["output_dir"])
    run_dir = output_dir / payload["run_id"]
    assert run_dir.exists()
    assert (run_dir / "report.json").exists()
    assert (run_dir / "report.md").exists()
    assert (run_dir / "log.txt").exists()
    assert (run_dir / "violations.json").exists()

    latest_dir = output_dir / "latest"
    assert (latest_dir / "latest_report.json").exists()
    assert (latest_dir / "latest_report.md").exists()
    assert (latest_dir / "latest_log.txt").exists()
    assert (latest_dir / "latest_violations.json").exists()


def test_detects_violations_and_honors_allowlist(tmp_path, monkeypatch):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    module_path = repo_root / "agents" / "module.py"
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(
        "from __future__ import annotations\nimport api\n",
        encoding="utf-8",
    )

    _write_graph(
        repo_root,
        "20240101_000000",
        {
            "agents": ["api"],
            "api": ["agents"],
        },
    )

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=mod.dt.timezone.utc),
    )

    payload_first = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "DEBUG",
        ]
    )

    assert payload_first["status"] == "violations"
    assert payload_first["summary"]["violation_count"] >= 1
    violation_files = {v["file"] for v in payload_first["violations"] if v.get("file")}
    assert "agents/module.py" in violation_files

    allowlist_path = repo_root / ".repo_studios" / "scripts" / "producers" / "import_rules_allowlist.json"
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    allowlist_path.write_text(
        json.dumps(
            {
                "edges": [
                    {"from": "agents", "to": "api"},
                    {"from": "api", "to": "agents"},
                ],
                "files": ["agents/module.py"],
            }
        ),
        encoding="utf-8",
    )

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 0, 1, tzinfo=mod.dt.timezone.utc),
    )
    payload_second = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--artifacts-to-keep",
            "1",
            "--log-level",
            "DEBUG",
        ]
    )

    assert payload_second["status"] == "ok"
    assert payload_second["summary"]["violation_count"] == 0

    output_dir = Path(payload_second["output_dir"])
    run_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith(mod.RUN_PREFIX)]
    assert len(run_dirs) == 1
    assert run_dirs[0].name == payload_second["run_id"]
