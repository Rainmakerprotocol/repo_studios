from __future__ import annotations

import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_ROOT = (
    Path(__file__).resolve().parents[4]
    / ".repo_studios"
    / "command_center"
    / "scripts"
)


def _load_libraries():
    try:
        return importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - test fallback for path issues
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("libraries")


libraries = _load_libraries()
copy_latest_artifact = libraries.copy_latest_artifact
ReportArtifact = libraries.ReportArtifact
write_report_artifacts = libraries.write_report_artifacts


def test_copy_latest_artifact_creates_link(tmp_path: Path) -> None:
    src = tmp_path / "source.json"
    dest = tmp_path / "dest.json"
    content = "{\"value\": 1}"
    src.write_text(content, encoding="utf-8")

    copy_latest_artifact(src, dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == content


def test_copy_latest_artifact_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    src = tmp_path / "source.json"
    dest = tmp_path / "dest.json"
    src.write_text("payload", encoding="utf-8")
    dest.write_text("stale", encoding="utf-8")

    def _raise_oserror(self: Path, target: Path) -> None:  # pragma: no cover - exercised via test
        raise OSError("link not permitted")

    monkeypatch.setattr(Path, "hardlink_to", _raise_oserror, raising=False)

    copy_latest_artifact(src, dest)

    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "payload"


def test_write_report_artifacts_basic_flow(tmp_path: Path) -> None:
    timestamp = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    artifacts = [
        ReportArtifact(
            filename="report.json",
            kind="json",
            content={"status": "ok"},
            pointer="latest_report.json",
        ),
        ReportArtifact(
            filename="report.md",
            kind="text",
            content="# Demo\n",
            pointer="latest_report.md",
        ),
        ReportArtifact(
            filename="log.txt",
            kind="text",
            content="status=ok\n",
            pointer="latest_report.log",
        ),
    ]

    result = write_report_artifacts(
        stem="demo",
        timestamp=timestamp,
        output_dir=tmp_path,
        artifacts=artifacts,
        keep=2,
    )

    run_dir = tmp_path / "demo-20240101_000000"
    assert result.run_dir == run_dir
    assert run_dir.is_dir()

    payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert payload == {"status": "ok"}
    assert (run_dir / "report.md").read_text(encoding="utf-8") == "# Demo\n"
    assert (run_dir / "log.txt").read_text(encoding="utf-8") == "status=ok\n"

    assert (tmp_path / "latest_report.json").is_file()
    assert (tmp_path / "latest_report.md").is_file()
    assert (tmp_path / "latest_report.log").is_file()

    # Ensure pruning removes older siblings beyond keep count
    stale = tmp_path / "demo-20200101_000000"
    stale.mkdir(parents=True, exist_ok=True)
    write_report_artifacts(
        stem="demo",
        timestamp=datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc),
        output_dir=tmp_path,
        artifacts=artifacts,
        keep=2,
    )
    remaining_dirs = {
        node.name
        for node in tmp_path.iterdir()
        if node.is_dir() and node.name.startswith("demo-")
    }
    assert remaining_dirs == {"demo-20240101_000000", "demo-20240102_000000"}


def test_write_report_artifacts_with_writer_and_callable_content(tmp_path: Path) -> None:
    timestamp = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
    report_payload: dict[str, Any] = {"status": "pending"}
    graph_edges = {"app": ["util"]}

    def _graph_writer(run_dir: Path) -> Path:
        path = run_dir / "graph.json"
        path.write_text(
            json.dumps(graph_edges, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        report_payload["graph_path"] = str(path)
        report_payload["run_directory"] = str(run_dir)
        report_payload["status"] = "ok"
        return path

    artifacts = [
        ReportArtifact(
            filename="graph.json",
            pointer="latest_graph.json",
            writer=_graph_writer,
        ),
        ReportArtifact(
            filename="report.json",
            kind="json",
            content=lambda: report_payload,
            pointer="latest_report.json",
        ),
        ReportArtifact(
            filename="report.md",
            kind="text",
            content=lambda: "# Summary\n",
        ),
    ]

    result = write_report_artifacts(
        stem="imports",
        timestamp=timestamp,
        output_dir=tmp_path,
        artifacts=artifacts,
        keep=1,
    )

    run_dir = result.run_dir
    assert json.loads((run_dir / "graph.json").read_text(encoding="utf-8")) == graph_edges
    payload = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert payload["graph_path"].endswith("graph.json")
    assert payload["run_directory"] == str(run_dir)
    assert payload["status"] == "ok"
