from __future__ import annotations

import json
from datetime import datetime as real_datetime, timezone as real_timezone
from pathlib import Path

import pytest

from command_center.scripts.libraries.build_commandview_selector import SelectorRecord
from command_center.viewer import refresh as viewer_refresh


def _make_record(
    slug: str,
    stamp: str,
    relative_path: str,
    category: str,
    absolute_root: Path,
) -> SelectorRecord:
    stamp_dt = real_datetime.strptime(stamp, "%Y%m%d-%H%M").replace(tzinfo=real_timezone.utc)
    return SelectorRecord(
        slug=slug,
        timestamp=stamp,
        timestamp_iso=stamp_dt.isoformat(),
        display_name=f"{slug} ({stamp_dt.strftime('%Y-%m-%d %H:%M UTC')})",
        category=category,
        relative_path=relative_path,
        absolute_path=str((absolute_root / relative_path).resolve()),
        _sort_key=stamp_dt,
    )


class _FixedDateTime(real_datetime):
    """Deterministic datetime helper for viewer refresh tests."""

    @classmethod
    def now(cls, tz: real_timezone | None = None):  # type: ignore[override]
        tzinfo = tz or real_timezone.utc
        return real_datetime(2025, 1, 3, 14, 15, 16, tzinfo=tzinfo)


@pytest.fixture(autouse=True)
def _fixed_now(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(viewer_refresh, "datetime", _FixedDateTime)


def test_refresh_selector_state_groups_and_deduplicates(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    records = [
        _make_record(
            slug="alpha",
            stamp="20240102-1310",
            relative_path="alpha/alpha_commandview_20240102-1310.json",
            category="alpha",
            absolute_root=tmp_path,
        ),
        _make_record(
            slug="alpha",
            stamp="20240101-1310",
            relative_path="alpha/alpha_commandview_20240101-1310.json",
            category="alpha",
            absolute_root=tmp_path,
        ),
        _make_record(
            slug="alpha",
            stamp="20240101-1310",
            relative_path="alpha/alpha_commandview_20240101-1310.json",
            category="alpha",
            absolute_root=tmp_path,
        ),
        _make_record(
            slug="beta",
            stamp="20231231-2359",
            relative_path="beta/beta_commandview_20231231-2359.json",
            category="beta",
            absolute_root=tmp_path,
        ),
    ]
    monkeypatch.setattr(viewer_refresh, "build_commandview_selector", lambda _: records)

    state = viewer_refresh.refresh_selector_state(tmp_path)

    assert state.generated_at == "2025-01-03T14:15:16+00:00"
    assert [entry.slug for entry in state.entries] == ["alpha", "beta"]

    alpha_entry = state.entries[0]
    assert len(alpha_entry.options) == 2
    assert [option.timestamp for option in alpha_entry.options] == [
        "20240102-1310",
        "20240101-1310",
    ]

    beta_entry = state.entries[1]
    assert len(beta_entry.options) == 1
    assert beta_entry.options[0].relative_path == "beta/beta_commandview_20231231-2359.json"


def test_refresh_selector_state_json_reuses_state_timestamp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(viewer_refresh, "build_commandview_selector", lambda _: [])

    payload = json.loads(viewer_refresh.refresh_selector_state_json(tmp_path))

    assert payload["generated_at"] == "2025-01-03T14:15:16+00:00"
    assert payload["entries"] == []


def test_refresh_selector_with_context_preserves_relative_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    records = [
        _make_record(
            slug="alpha",
            stamp="20240102-1310",
            relative_path="alpha/alpha_commandview_20240102-1310.json",
            category="alpha",
            absolute_root=tmp_path,
        ),
        _make_record(
            slug="beta",
            stamp="20231231-2359",
            relative_path="beta/beta_commandview_20231231-2359.json",
            category="beta",
            absolute_root=tmp_path,
        ),
    ]
    monkeypatch.setattr(viewer_refresh, "build_commandview_selector", lambda _: records)

    result = viewer_refresh.refresh_selector_with_context(
        tmp_path, active_relative_path="beta/beta_commandview_20231231-2359.json"
    )

    assert result.active_option is not None
    assert result.active_option.relative_path == "beta/beta_commandview_20231231-2359.json"
    assert result.active_entry is not None
    assert result.active_entry.slug == "beta"


def test_refresh_selector_with_context_falls_back_to_slug(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    records = [
        _make_record(
            slug="alpha",
            stamp="20240102-1310",
            relative_path="alpha/alpha_commandview_20240102-1310.json",
            category="alpha",
            absolute_root=tmp_path,
        ),
        _make_record(
            slug="beta",
            stamp="20231231-2359",
            relative_path="beta/beta_commandview_20231231-2359.json",
            category="beta",
            absolute_root=tmp_path,
        ),
    ]
    monkeypatch.setattr(viewer_refresh, "build_commandview_selector", lambda _: records)

    result = viewer_refresh.refresh_selector_with_context(
        tmp_path,
        active_relative_path="gamma/missing.json",
        active_slug="alpha",
    )

    assert result.active_option is not None
    assert result.active_option.slug == "alpha"
    assert result.active_option.relative_path == "alpha/alpha_commandview_20240102-1310.json"