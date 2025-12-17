from __future__ import annotations

import json
from pathlib import Path

from libraries import (
    build_commandview_selector,
    build_commandview_selector_payload,
    dump_commandview_selector,
)


def test_build_commandview_selector_discovers_artifacts(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    static_root = repo_root / ".repo_studios" / "command_center" / "reports" / "commandview"
    topic_dir = static_root / "docs" / "20251201"
    topic_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = topic_dir / "docs_health_commandview_20251201-1234.json"
    manifest_path.write_text(
        json.dumps(
            {
                "metadata": {
                    "folder_path": ".repo_studios/command_center/reports/docs_health/docs_health-20251201_123400"
                }
            }
        ),
        encoding="utf-8",
    )

    outside_path = static_root / "docs" / "docs_health_commandview_20251201-1200.json"
    outside_path.write_text(
        json.dumps({"metadata": {"folder_path": str(tmp_path / "external")}}),
        encoding="utf-8",
    )

    malformed = static_root / "docs" / "invalid.json"
    malformed.write_text("not json", encoding="utf-8")

    records = build_commandview_selector(repo_root)
    assert len(records) == 2
    assert any(record.target_repo_relative for record in records)
    assert any(record.target_repo_relative is None for record in records)

    payloads = build_commandview_selector_payload(repo_root)
    categories = {payload["category"] for payload in payloads}
    assert "commandview" in categories
    assert any(entry["relative_path"].endswith(".json") for entry in payloads)

    dumped = dump_commandview_selector(repo_root)
    assert "docs_health_commandview" in dumped
