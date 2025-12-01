"""Catalog registry helpers for mapping scripts to topic orchestrators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

RoleName = Literal["producer", "consumer", "aggregator", "orchestrator", "summarizer", "utility"]


@dataclass(frozen=True)
class CatalogEntry:
    """Represents a single script-to-topic association."""

    script_path: str
    topic: str
    role: RoleName


class CatalogRegistry:
    """In-memory registry that records script coverage by topic."""

    def __init__(self) -> None:
        self._entries: dict[str, CatalogEntry] = {}

    def register(self, *, script_path: str, topic: str, role: RoleName) -> CatalogEntry:
        normalised_path = script_path.replace("\\", "/")
        key = normalised_path.lower()
        entry = CatalogEntry(script_path=normalised_path, topic=topic, role=role)
        if key in self._entries and self._entries[key] != entry:
            raise ValueError(f"Script already registered with different metadata: {script_path}")
        self._entries[key] = entry
        return entry

    def get(self, script_path: str) -> CatalogEntry | None:
        return self._entries.get(script_path.replace("\\", "/").lower())

    def entries_for_topic(self, topic: str) -> list[CatalogEntry]:
        return [entry for entry in self._entries.values() if entry.topic == topic]

    def topics(self) -> set[str]:
        return {entry.topic for entry in self._entries.values()}

    def roles(self) -> set[RoleName]:
        return {entry.role for entry in self._entries.values()}

    def all_entries(self) -> list[CatalogEntry]:
        return sorted(self._entries.values(), key=lambda entry: (entry.topic, entry.role, entry.script_path))

    def extend(self, entries: Iterable[CatalogEntry]) -> None:
        for entry in entries:
            self.register(script_path=entry.script_path, topic=entry.topic, role=entry.role)
