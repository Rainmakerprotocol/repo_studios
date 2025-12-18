from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "producers" / "verify_docs_integrity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_docs_integrity", MODULE_PATH)
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


def _render_json_block(module, payload: dict[str, object]) -> str:
    bare = dict(payload)
    digest = module._compute_hash_for_json_block(bare)
    enriched = dict(bare)
    enriched["content_hash"] = digest
    return json.dumps(enriched, indent=2, sort_keys=True)


def _write_doc(module, path: Path, block: dict[str, object]) -> None:
    body = [
        "# Docs Integrity Handbook",
        "",
        "This handbook is used for integrity verification tests.",
        "",
        "```json",
        _render_json_block(module, block),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def _write_index(module, path: Path, documents: list[dict[str, object]]) -> None:
    index_block = {"documents": documents}
    block_text = _render_json_block(module, index_block)
    table_lines = module._build_index_table_lines(documents)
    lines = [
        "# Repo Studios Documentation Index",
        "",
        "```json",
        block_text,
        "```",
        "",
        module.INDEX_TABLE_BEGIN,
        "",
        "\n".join(table_lines),
        "",
        module.INDEX_TABLE_END,
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def test_clean_run_generates_artifacts(tmp_path, monkeypatch):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    docs_dir = repo_root / "docs/standards/global"

    _write_doc(
        mod,
        docs_dir / "std-docs-integrity-handbook.md",
        {"doc_id": "docs_integrity_handbook", "revision": 1},
    )

    documents = [
        {
            "category": "global",
            "doc_id": "docs_integrity_handbook",
            "path": "docs/standards/global/std-docs-integrity-handbook.md",
            "stability": "stable",
            "json_block": True,
        }
    ]

    _write_index(
        mod,
        repo_root / "docs/standards/docs_index.md",
        documents,
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
            "--output-dir",
            str(repo_root / "artifacts"),
            "--artifacts-to-keep",
            "2",
            "--log-level",
            "DEBUG",
        ]
    )

    assert payload["status"] == "ok"
    assert payload["exit_code"] == 0
    assert payload["summary"]["documents_processed"] == 1
    assert payload["summary"]["json_blocks_checked"] == 2
    assert payload["summary"]["mismatched_blocks"] == 0

    output_root = repo_root / "artifacts"
    expected_run_timestamp = "20250101-1200"
    expected_run_dir = (
        output_root / "healthview" / "docs_integrity_validation" / expected_run_timestamp
    )

    assert payload["run_timestamp"] == expected_run_timestamp
    assert Path(payload["run_dir"]) == expected_run_dir

    assert (expected_run_dir / "manifest.json").exists()
    assert (expected_run_dir / "summary.md").exists()
    assert (expected_run_dir / "telemetry.json").exists()
    assert not (expected_run_dir / "report.json").exists()
    assert not (output_root / "latest").exists()

    manifest = json.loads(
        (expected_run_dir / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["viewer_slug"] == "healthview"
    assert manifest["topic"] == "docs_integrity_validation"
    assert manifest["run_timestamp"] == expected_run_timestamp

    telemetry = json.loads(
        (expected_run_dir / "telemetry.json").read_text(encoding="utf-8")
    )
    assert telemetry["status"] == "ok"
    assert telemetry["metrics"]["documents_processed"] == 1


def test_detects_mismatches_and_updates(tmp_path, monkeypatch):
    mod = _load_module()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    docs_dir = repo_root / "docs/standards/global"

    # Intentionally omit content_hash so the first run reports a mismatch
    doc_body = [
        "# Docs Integrity Handbook",
        "",
        "```json",
        json.dumps({"doc_id": "docs_integrity_handbook", "revision": 1}, indent=2, sort_keys=True),
        "```",
        "",
    ]
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "std-docs-integrity-handbook.md").write_text("\n".join(doc_body), encoding="utf-8")

    documents = [
        {
            "category": "global",
            "doc_id": "docs_integrity_handbook",
            "path": "docs/standards/global/std-docs-integrity-handbook.md",
            "stability": "stable",
            "json_block": True,
        }
    ]

    # Index starts with placeholder hash to force mismatch
    index_lines = [
        "# Repo Studios Documentation Index",
        "",
        "```json",
        json.dumps(
            {
                "documents": documents,
                "content_hash": "placeholder",
            },
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        mod.INDEX_TABLE_BEGIN,
        "",
        "| Category | Doc ID | File | Summary | JSON | Stability |",
        "|----------|--------|------|---------|------|-----------|",
        "| Global | docs_integrity_handbook | standards/global/std-docs-integrity-handbook.md | docs_integrity_handbo | yes | stable |",
        "",
        mod.INDEX_TABLE_END,
        "",
    ]
    index_path = repo_root / "docs/standards/docs_index.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(index_lines), encoding="utf-8")

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=mod.dt.timezone.utc),
    )

    first_payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(repo_root / "artifacts"),
            "--log-level",
            "INFO",
        ]
    )

    assert first_payload["status"] == "mismatches"
    assert first_payload["exit_code"] == 1
    assert first_payload["summary"]["mismatched_blocks"] >= 1

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 1, 0, tzinfo=mod.dt.timezone.utc),
    )

    second_payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(repo_root / "artifacts"),
            "--log-level",
            "INFO",
            "--update",
        ]
    )

    assert second_payload["status"] == "updated"
    assert second_payload["exit_code"] == 0

    _set_fixed_datetime(
        monkeypatch,
        mod,
        mod.dt.datetime(2025, 1, 1, 12, 2, 0, tzinfo=mod.dt.timezone.utc),
    )

    final_payload = mod.run(
        [
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(repo_root / "artifacts"),
            "--log-level",
            "INFO",
        ]
    )

    assert final_payload["status"] == "ok"
    assert final_payload["summary"]["mismatched_blocks"] == 0
