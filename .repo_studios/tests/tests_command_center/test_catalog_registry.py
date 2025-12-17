from __future__ import annotations

import pytest

from libraries import CatalogEntry, CatalogRegistry


def test_catalog_registry_register_and_lookup() -> None:
    registry = CatalogRegistry()
    entry = registry.register(script_path=".repo_studios/scripts/producers/example.py", topic="test", role="producer")

    assert registry.get(".repo_studios/scripts/producers/example.py") == entry
    assert registry.entries_for_topic("test") == [entry]
    assert registry.topics() == {"test"}
    assert registry.roles() == {"producer"}


def test_catalog_registry_prevents_conflicting_registration() -> None:
    registry = CatalogRegistry()
    registry.register(script_path="script.py", topic="one", role="producer")

    with pytest.raises(ValueError):
        registry.register(script_path="script.py", topic="two", role="consumer")


def test_catalog_registry_extend() -> None:
    registry = CatalogRegistry()
    registry.extend(
        [
            CatalogEntry(script_path="a.py", topic="alpha", role="producer"),
            CatalogEntry(script_path="b.py", topic="beta", role="consumer"),
        ]
    )

    entries = registry.all_entries()
    assert len(entries) == 2
    assert {entry.topic for entry in entries} == {"alpha", "beta"}
