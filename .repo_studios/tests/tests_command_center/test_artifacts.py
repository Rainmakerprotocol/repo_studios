from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from command_center.scripts.libraries import artifacts


def test_copy_latest_artifact_falls_back_to_copy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source.txt"
    dest = tmp_path / "dest.txt"
    source.write_text("payload", encoding="utf-8")

    original_class = dest.__class__

    def raiser(self, other: Path) -> None:  # type: ignore[override]
        raise OSError("no hardlinks here")

    monkeypatch.setattr(original_class, "hardlink_to", raiser)

    artifacts.copy_latest_artifact(source, dest)

    assert dest.read_text(encoding="utf-8") == "payload"


def test_report_artifact_materialization(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    json_artifact = artifacts.ReportArtifact(filename="data.json", kind="json", content={"value": 1})
    json_path = json_artifact.materialize(run_dir)
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"value": 1}

    text_artifact = artifacts.ReportArtifact(filename="note.txt", kind="text", content="hello")
    text_path = text_artifact.materialize(run_dir)
    assert text_path.read_text(encoding="utf-8") == "hello"

    bytes_artifact = artifacts.ReportArtifact(filename="blob.bin", kind="bytes", content=b"bytes")
    bytes_path = bytes_artifact.materialize(run_dir)
    assert bytes_path.read_bytes() == b"bytes"

    copied_source = tmp_path / "source.bin"
    copied_source.write_text("copy", encoding="utf-8")
    copy_artifact = artifacts.ReportArtifact(filename="copied.txt", kind="copy", content=copied_source)
    copy_path = copy_artifact.materialize(run_dir)
    assert copy_path.read_text(encoding="utf-8") == "copy"

    def writer(target: Path) -> Path:
        custom = target / "writer.txt"
        custom.write_text("writer", encoding="utf-8")
        return custom

    writer_artifact = artifacts.ReportArtifact(filename="writer.txt", writer=writer)
    assert writer_artifact.materialize(run_dir).read_text(encoding="utf-8") == "writer"


def test_write_report_artifacts_prunes_history(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"

    # seed legacy runs, including a protected one
    keep_dir = output_dir / "dependency_hygiene-20240101_000000"
    keep_dir.mkdir(parents=True)
    (keep_dir / ".keep").write_text("", encoding="utf-8")
    obsolete = output_dir / "dependency_hygiene-20240102_000000"
    obsolete.mkdir(parents=True)

    timestamp = datetime(2025, 12, 1, 12, 0, tzinfo=timezone.utc)

    result = artifacts.write_report_artifacts(
        stem="dependency_hygiene",
        timestamp=timestamp,
        output_dir=output_dir,
        artifacts=[
            artifacts.ReportArtifact(filename="summary.md", kind="text", content="summary", pointer="latest_summary.md"),
        ],
        keep=1,
    )

    assert result.run_dir.exists()
    assert (output_dir / "latest_summary.md").exists()
    assert keep_dir.exists(), "protected directory should remain"
    assert not obsolete.exists(), "old run should be pruned"


def test_write_report_artifacts_hierarchical_layout(tmp_path: Path) -> None:
    output_dir = tmp_path / "reports"
    topic_dir = output_dir / "healthview" / "docs_health"
    old_run = topic_dir / "20250101-0000"
    old_run.mkdir(parents=True)
    (old_run / ".keep").write_text("", encoding="utf-8")
    stale_run = topic_dir / "20250102-0000"
    stale_run.mkdir(parents=True)

    timestamp = datetime(2025, 12, 1, 12, 30, tzinfo=timezone.utc)
    result = artifacts.write_report_artifacts(
        stem="docs_health",
        timestamp=timestamp,
        output_dir=output_dir,
        artifacts=[
            artifacts.ReportArtifact(filename="manifest.json", kind="json", content={"ok": True}),
        ],
        keep=1,
        viewer="healthview",
        topic="docs_health",
    )

    assert result.run_dir.parent == topic_dir
    remaining = sorted(child.name for child in topic_dir.iterdir())
    assert old_run.name in remaining  # protected by .keep
    assert "20250102-0000" not in remaining
