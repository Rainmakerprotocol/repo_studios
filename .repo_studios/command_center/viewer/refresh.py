from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from command_center.scripts.libraries.build_commandview_selector import (
    SelectorRecord,
    build_commandview_selector,
)


@dataclass(frozen=True)
class SelectorOption:
    """Represents a single selectable CommandView artifact."""

    slug: str
    timestamp: str
    label: str
    relative_path: str
    absolute_path: str
    category: str
    timestamp_iso: str
    target_repo_relative: Optional[str]
    target_path: Optional[str]


@dataclass(frozen=True)
class ViewerSelectorEntry:
    """Group of CommandView artifacts for a given slug."""

    slug: str
    options: Tuple[SelectorOption, ...]


@dataclass(frozen=True)
class ViewerSelectorState:
    """Top-level state returned to the viewer during refresh."""

    generated_at: str
    entries: Tuple[ViewerSelectorEntry, ...]


@dataclass(frozen=True)
class ViewerRefreshResult:
    """Outcome of a refresh run alongside the resolved active context."""

    state: ViewerSelectorState
    active_entry: Optional[ViewerSelectorEntry]
    active_option: Optional[SelectorOption]


def _build_option(record: SelectorRecord) -> SelectorOption:
    return SelectorOption(
        slug=record.slug,
        timestamp=record.timestamp,
        label=record.display_name,
        relative_path=record.relative_path,
        absolute_path=record.absolute_path,
        category=record.category,
        timestamp_iso=record.timestamp_iso,
        target_repo_relative=record.target_repo_relative,
        target_path=record.target_path,
    )


def _group_records(records: Iterable[SelectorRecord]) -> Dict[str, List[SelectorOption]]:
    buckets: Dict[str, List[SelectorOption]] = {}
    for record in records:
        option = _build_option(record)
        bucket = buckets.setdefault(option.slug, [])
        # Deduplicate by relative path so we do not surface duplicates when
        # refresh is triggered repeatedly in rapid succession.
        if any(existing.relative_path == option.relative_path for existing in bucket):
            continue
        bucket.append(option)
    for options in buckets.values():
        options.sort(key=lambda opt: opt.timestamp, reverse=True)
    return buckets


def refresh_selector_state(repo_root: Path) -> ViewerSelectorState:
    """Build the viewer selector state from static CommandView artifacts."""

    records = build_commandview_selector(repo_root)
    buckets = _group_records(records)
    entries = tuple(
        ViewerSelectorEntry(slug=slug, options=tuple(options))
        for slug, options in sorted(buckets.items())
    )
    generated_at = datetime.now(timezone.utc).isoformat()
    return ViewerSelectorState(generated_at=generated_at, entries=entries)


def refresh_selector_payload(repo_root: Path) -> dict:
    """Return a dictionary describing the selector state."""

    state = refresh_selector_state(repo_root)
    return {
        "generated_at": state.generated_at,
        "entries": [
            {
                "slug": entry.slug,
                "options": [
                    {
                        "slug": option.slug,
                        "timestamp": option.timestamp,
                        "label": option.label,
                        "relative_path": option.relative_path,
                        "absolute_path": option.absolute_path,
                        "category": option.category,
                        "timestamp_iso": option.timestamp_iso,
                        "target_repo_relative": option.target_repo_relative,
                        "target_path": option.target_path,
                    }
                    for option in entry.options
                ],
            }
            for entry in state.entries
        ],
    }


def refresh_selector_state_json(repo_root: Path) -> str:
    """Dump the selector state payload as formatted JSON."""

    payload = refresh_selector_payload(repo_root)
    return json.dumps(payload, indent=2, sort_keys=True)


def refresh_selector_with_context(
    repo_root: Path,
    *,
    active_relative_path: str | None = None,
    active_slug: str | None = None,
) -> ViewerRefreshResult:
    """Refresh selector state and attempt to preserve the active selection."""

    state = refresh_selector_state(repo_root)
    active_entry: Optional[ViewerSelectorEntry] = None
    active_option: Optional[SelectorOption] = None

    if active_relative_path:
        for entry in state.entries:
            for option in entry.options:
                if option.relative_path == active_relative_path:
                    active_entry = entry
                    active_option = option
                    break
            if active_option is not None:
                break

    if active_option is None and active_slug:
        for entry in state.entries:
            if entry.slug == active_slug and entry.options:
                active_entry = entry
                active_option = entry.options[0]
                break

    if active_option is None and state.entries:
        fallback_entry = state.entries[0]
        fallback_option = fallback_entry.options[0] if fallback_entry.options else None
        active_entry = fallback_entry if fallback_option else None
        active_option = fallback_option

    return ViewerRefreshResult(state=state, active_entry=active_entry, active_option=active_option)


__all__ = [
    "SelectorOption",
    "ViewerSelectorEntry",
    "ViewerSelectorState",
    "ViewerRefreshResult",
    "refresh_selector_payload",
    "refresh_selector_state",
    "refresh_selector_state_json",
    "refresh_selector_with_context",
]
