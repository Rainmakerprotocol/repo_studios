from __future__ import annotations

from pathlib import Path

from command_center.scripts.libraries.build_commandview_selector import (
    build_commandview_selector,
    build_commandview_selector_payload,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_commandview_selector_filters_static_commandview_files(tmp_path: Path) -> None:
    repo_root = tmp_path
    static_root = repo_root / ".repo_studios" / "command_center" / "reports" / "index_scan" / "alpha_index"
    commandview_file = static_root / "alpha_commandview_20251106-1014.json"
    screening_file = static_root / "alpha_commandview_screening_20251106-1014.json"
    dynamic_root = repo_root / "alpha_index"
    dynamic_file = dynamic_root / "alpha_commandview_20251105-0930.json"

    _write(commandview_file, "{}")
    _write(screening_file, "{}")
    _write(dynamic_file, "{}")

    records = build_commandview_selector(repo_root)
    assert len(records) == 1
    record = records[0]
    assert record.slug == "alpha"
    assert record.timestamp == "20251106-1014"
    assert record.category == "index_scan"
    assert record.relative_path == "index_scan/alpha_index/alpha_commandview_20251106-1014.json"
    assert record.absolute_path.endswith("alpha_commandview_20251106-1014.json")
    assert record.timestamp_iso.endswith("+00:00")
    assert "alpha" in record.display_name
    assert "2025-11-06" in record.display_name

    payload = build_commandview_selector_payload(repo_root)
    assert payload == [record.to_payload()]


def test_build_commandview_selector_orders_by_slug_and_timestamp(tmp_path: Path) -> None:
    repo_root = tmp_path
    alpha_dir = repo_root / ".repo_studios" / "command_center" / "reports" / "index_scan" / "alpha_index"
    beta_dir = repo_root / ".repo_studios" / "command_center" / "reports" / "index_scan" / "beta_index"

    _write(alpha_dir / "alpha_commandview_20251105-0830.json", "{}")
    _write(alpha_dir / "alpha_commandview_20251106-0900.json", "{}")
    _write(beta_dir / "beta_commandview_20251104-1000.json", "{}")

    records = build_commandview_selector(repo_root)
    assert [record.slug for record in records] == ["alpha", "alpha", "beta"]
    alpha_records = [record for record in records if record.slug == "alpha"]
    assert [record.timestamp for record in alpha_records] == ["20251106-0900", "20251105-0830"]


def test_build_commandview_selector_handles_missing_reports_root(tmp_path: Path) -> None:
    repo_root = tmp_path
    records = build_commandview_selector(repo_root)
    assert records == []
    assert build_commandview_selector_payload(repo_root) == []
