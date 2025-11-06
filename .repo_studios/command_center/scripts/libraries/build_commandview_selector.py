"""Selector helpers for CommandView inventory discovery."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

STATIC_REPORTS_ROOT_RELATIVE = Path(".repo_studios/command_center/reports")
_COMMANDVIEW_PATTERN = re.compile(r"^(?P<slug>.+)_commandview_(?P<stamp>\d{8}-\d{4})\.json$")


@dataclass(frozen=True)
class SelectorRecord:
    """Describes a single CommandView artifact for viewer selection."""

    slug: str
    timestamp: str
    timestamp_iso: str
    display_name: str
    category: str
    relative_path: str
    absolute_path: str
    _sort_key: datetime = field(repr=False, compare=False)

    def to_payload(self) -> dict[str, str]:
        """Convert the record into a JSON-friendly payload."""

        return {
            "slug": self.slug,
            "timestamp": self.timestamp,
            "timestamp_iso": self.timestamp_iso,
            "display_name": self.display_name,
            "category": self.category,
            "relative_path": self.relative_path,
            "absolute_path": self.absolute_path,
        }


def _resolve_static_root(repo_root: Path) -> Path:
    repo_root = repo_root.resolve()
    static_root = (repo_root / STATIC_REPORTS_ROOT_RELATIVE).resolve()
    return static_root


def build_commandview_selector(repo_root: Path) -> list[SelectorRecord]:
    """Discover CommandView inventory artifacts under the static reports tree."""

    static_root = _resolve_static_root(repo_root)
    if not static_root.exists():
        return []

    records: list[SelectorRecord] = []
    for candidate in static_root.rglob("*.json"):
        name = candidate.name
        if "_screening_" in name:
            continue
        match = _COMMANDVIEW_PATTERN.match(name)
        if match is None:
            continue
        slug = match.group("slug")
        stamp = match.group("stamp")
        stamp_dt = datetime.strptime(stamp, "%Y%m%d-%H%M").replace(tzinfo=timezone.utc)
        relative_path = candidate.relative_to(static_root).as_posix()
        category = relative_path.split("/", 1)[0]
        display_name = f"{slug} ({stamp_dt.strftime('%Y-%m-%d %H:%M UTC')})"
        records.append(
            SelectorRecord(
                slug=slug,
                timestamp=stamp,
                timestamp_iso=stamp_dt.isoformat(),
                display_name=display_name,
                category=category,
                relative_path=relative_path,
                absolute_path=str(candidate.resolve()),
                _sort_key=stamp_dt,
            )
        )

    records.sort(key=lambda item: item._sort_key, reverse=True)
    records.sort(key=lambda item: item.slug)
    return records


def build_commandview_selector_payload(repo_root: Path) -> list[dict[str, str]]:
    """Return selector payload entries ready for JSON serialisation."""

    return [record.to_payload() for record in build_commandview_selector(repo_root)]


def dump_commandview_selector(repo_root: Path) -> str:
    """Serialise the selector payload as pretty-printed JSON."""

    payload = build_commandview_selector_payload(repo_root)
    return json.dumps(payload, indent=2, sort_keys=True)


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point printing the selector payload to stdout."""

    args = list(argv or [])
    repo_root = Path(args[0]).resolve() if args else Path.cwd()
    print(dump_commandview_selector(repo_root))
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    raise SystemExit(main())
