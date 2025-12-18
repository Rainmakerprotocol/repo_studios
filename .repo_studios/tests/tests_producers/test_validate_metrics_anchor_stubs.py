from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "validate_metrics_anchor_stubs.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_metrics_anchor_stubs", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _set_fixed_datetime(monkeypatch, module, value):
    class _FixedDateTime(module.dt.datetime):
        @classmethod
        def now(cls, tz: module.dt.tzinfo | None = None):  # type: ignore[override]
            if tz is None:
                return value
            return value.astimezone(tz)

    monkeypatch.setattr(module.dt, "datetime", _FixedDateTime)


def _write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_legacy_file(path: Path, anchors: list[str]) -> None:
    lines = [
        "# Metrics Orchestrator",
        "",
        "## Legacy Anchor Compatibility",
    ]
    for anchor in anchors:
        lines.append(f"### {anchor}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_structured_artifacts_without_missing(tmp_path, monkeypatch):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    _write_legacy_file(
        repo_root / "docs/api/metrics_orchestrator.md",
        anchors=["Sample Anchor"],
    )
    _write_markdown(
        repo_root / "docs/example.md",
        "[Metrics](metrics_orchestrator.md#sample-anchor)\n",
    )

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
    assert payload["summary"]["missing_count"] == 0
    assert payload["summary"]["anchors_referenced"] == 1

    output_dir = Path(payload["output_dir"])
    assert payload["viewer_slug"] == "healthview"
    assert payload["topic"] == "metrics_anchor_stub_validation"
    assert payload["run_timestamp"] == "20250101-1200"

    run_dir = output_dir / payload["viewer_slug"] / payload["topic"] / payload["run_timestamp"]
    assert (run_dir / "manifest.json").exists()
    assert (run_dir / "summary.md").exists()
    assert (run_dir / "telemetry.json").exists()

    telemetry = json.loads((run_dir / "telemetry.json").read_text(encoding="utf-8"))
    assert telemetry["payload"]["report"]["summary"]["files_checked"] >= 1


def test_detects_missing_and_honors_allowlist(tmp_path, monkeypatch):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    _write_legacy_file(
        repo_root / "docs/api/metrics_orchestrator.md",
        anchors=["Existing Anchor"],
    )
    _write_markdown(
        repo_root / "docs/usage.md",
        "[Missing](metrics_orchestrator.md#missing-anchor)\n",
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

    assert payload_first["status"] == "fail"
    assert payload_first["summary"]["missing_count"] == 1
    assert payload_first["missing"][0]["anchor"] == "missing-anchor"

    allowlist_path = repo_root / ".repo_studios/scripts/producers/metrics_anchor_allowlist.json"
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    allowlist_path.write_text(json.dumps({"anchors": ["missing-anchor"]}), encoding="utf-8")

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 1, 0, tzinfo=mod.dt.timezone.utc),
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
    assert payload_second["summary"]["missing_count"] == 0
    assert payload_second["summary"]["allowlisted_count"] == 1

    output_dir = Path(payload_second["output_dir"])
    topic_dir = output_dir / payload_second["viewer_slug"] / payload_second["topic"]
    run_dirs = [p for p in topic_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    assert run_dirs[0].name == payload_second["run_timestamp"]
