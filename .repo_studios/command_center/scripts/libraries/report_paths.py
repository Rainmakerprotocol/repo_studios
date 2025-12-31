"""Canonical HealthView report path registry.

This module provides the single source of truth for HOP-compliant output locations.
All scripts should import from here rather than hardcoding paths.

HOP Path Structure::

    /reports/healthview/<class>_reports/<topic>/<YYYYMMDD-HHMM>/
       ↑         ↑              ↑           ↑           ↑
     slug1    slug2          slug3       slug4       slug5

Slug Hierarchy:
    - slug1: ``reports`` - The reports root
    - slug2: ``healthview`` - The viewer namespace
    - slug3: ``<class>_reports`` - The tier class (producer, consumer, etc.)
    - slug4: ``<topic>`` - The specific topic (anchor_inventory, fault_artifacts, etc.)
    - slug5: ``<YYYYMMDD-HHMM>`` - The timestamp slug

Usage::

    from libraries.report_paths import (
        PRODUCER_REPORTS,
        AGGREGATOR_REPORTS,
        get_class_root,
        build_topic_path,
    )

    # Direct constant usage
    output_dir = PRODUCER_REPORTS  # Path(".repo_studios/reports/healthview/producer_reports")

    # Dynamic lookup by tier class
    output_dir = get_class_root("producer")

    # Build full topic path
    topic_dir = build_topic_path("producer", "anchor_inventory")
    # Result: Path(".repo_studios/reports/healthview/producer_reports/anchor_inventory")

    # Auto-infer from script location
    output_dir = get_default_output_dir(__file__)
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

# ─────────────────────────────────────────────────────────────────────────────
# Base Structure
# ─────────────────────────────────────────────────────────────────────────────

REPO_STUDIOS_ROOT = Path(".repo_studios")
"""Root directory for Repo Studios artifacts."""

REPORTS_ROOT = REPO_STUDIOS_ROOT / "reports"
"""Root directory for all reports (slug1)."""

HEALTHVIEW_ROOT = REPORTS_ROOT / "healthview"
"""Root directory for HealthView reports (slug2)."""

# ─────────────────────────────────────────────────────────────────────────────
# Tier Class Roots (slug3)
# ─────────────────────────────────────────────────────────────────────────────

AGGREGATOR_REPORTS = HEALTHVIEW_ROOT / "aggregator_reports"
"""Output directory for aggregator scripts."""

CONSUMER_REPORTS = HEALTHVIEW_ROOT / "consumer_reports"
"""Output directory for consumer scripts."""

ORCHESTRATOR_REPORTS = HEALTHVIEW_ROOT / "orchestrator_reports"
"""Output directory for orchestrator scripts."""

PRODUCER_REPORTS = HEALTHVIEW_ROOT / "producer_reports"
"""Output directory for producer scripts."""

RAWVIEW = HEALTHVIEW_ROOT / "rawview"
"""Output directory for raw/unprocessed artifacts."""

SUMMARIZER_REPORTS = HEALTHVIEW_ROOT / "summarizer_reports"
"""Output directory for summarizer scripts."""

# ─────────────────────────────────────────────────────────────────────────────
# Type Definitions
# ─────────────────────────────────────────────────────────────────────────────

TierClass = Literal["aggregator", "consumer", "orchestrator", "producer", "rawview", "summarizer"]
"""Valid tier class identifiers for HealthView scripts."""

_CLASS_MAPPING: dict[TierClass, Path] = {
    "aggregator": AGGREGATOR_REPORTS,
    "consumer": CONSUMER_REPORTS,
    "orchestrator": ORCHESTRATOR_REPORTS,
    "producer": PRODUCER_REPORTS,
    "rawview": RAWVIEW,
    "summarizer": SUMMARIZER_REPORTS,
}

# ─────────────────────────────────────────────────────────────────────────────
# Validation Constants
# ─────────────────────────────────────────────────────────────────────────────

VALID_TIER_CLASSES: frozenset[TierClass] = frozenset(_CLASS_MAPPING.keys())
"""Immutable set of valid tier class names."""

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def get_class_root(tier_class: TierClass) -> Path:
    """Return canonical output directory for a script tier class.

    :param tier_class: One of aggregator, consumer, orchestrator, producer, rawview, summarizer.
    :type tier_class: TierClass
    :returns: Relative path to the class root directory.
    :rtype: Path
    :raises ValueError: If tier_class is not recognized.

    Example::

        >>> get_class_root("producer")
        PosixPath('.repo_studios/reports/healthview/producer_reports')
        >>> get_class_root("aggregator")
        PosixPath('.repo_studios/reports/healthview/aggregator_reports')
    """
    if tier_class not in _CLASS_MAPPING:
        valid = ", ".join(sorted(_CLASS_MAPPING.keys()))
        raise ValueError(f"Unknown tier class: {tier_class!r}. Valid: {valid}")
    return _CLASS_MAPPING[tier_class]


def build_topic_path(tier_class: TierClass, topic: str) -> Path:
    """Build path for a specific topic within a tier class.

    :param tier_class: One of aggregator, consumer, orchestrator, producer, rawview, summarizer.
    :type tier_class: TierClass
    :param topic: The topic slug (e.g., "anchor_inventory", "fault_artifacts").
    :type topic: str
    :returns: Relative path to the topic directory.
    :rtype: Path
    :raises ValueError: If tier_class is not recognized or topic is empty.

    Example::

        >>> build_topic_path("producer", "anchor_inventory")
        PosixPath('.repo_studios/reports/healthview/producer_reports/anchor_inventory')
        >>> build_topic_path("consumer", "fault_artifacts")
        PosixPath('.repo_studios/reports/healthview/consumer_reports/fault_artifacts')
    """
    if not topic or not isinstance(topic, str):
        raise ValueError(f"Topic must be a non-empty string, got: {topic!r}")
    return get_class_root(tier_class) / topic


def build_absolute_topic_path(repo_root: Path, tier_class: TierClass, topic: str) -> Path:
    """Build absolute path for a topic given a repo root.

    :param repo_root: Absolute path to the repository root.
    :type repo_root: Path
    :param tier_class: One of aggregator, consumer, orchestrator, producer, rawview, summarizer.
    :type tier_class: TierClass
    :param topic: The topic slug.
    :type topic: str
    :returns: Absolute path to the topic directory.
    :rtype: Path

    Example::

        >>> build_absolute_topic_path(Path("/home/user/repo"), "producer", "anchor_inventory")
        PosixPath('/home/user/repo/.repo_studios/reports/healthview/producer_reports/anchor_inventory')
    """
    return repo_root / build_topic_path(tier_class, topic)


def infer_class_from_script(script_path: str | Path) -> TierClass | None:
    """Infer the tier class from a script's file path.

    Examines the script path for known directory patterns to determine
    which tier class the script belongs to.

    :param script_path: Path to the script file.
    :type script_path: str | Path
    :returns: Inferred tier class or None if not determinable.
    :rtype: TierClass | None

    Example::

        >>> infer_class_from_script("scripts/producers/generate_anchor_inventory.py")
        'producer'
        >>> infer_class_from_script("scripts/aggregators/aggregate_docs_health.py")
        'aggregator'
        >>> infer_class_from_script("some/unknown/path.py")
        None
    """
    path_str = str(script_path).replace("\\", "/").lower()

    # Check for plural folder names (scripts/producers/, scripts/consumers/, etc.)
    if "/producers/" in path_str:
        return "producer"
    if "/consumers/" in path_str:
        return "consumer"
    if "/aggregators/" in path_str:
        return "aggregator"
    if "/summarizers/" in path_str:
        return "summarizer"
    if "/orchestrators/" in path_str:
        return "orchestrator"
    if "/rawview/" in path_str:
        return "rawview"

    return None


def get_default_output_dir(script_path: str | Path) -> Path:
    """Get the default output directory for a script based on its location.

    This function infers the tier class from the script's path and returns
    the corresponding HOP-compliant output directory.

    :param script_path: Path to the script file.
    :type script_path: str | Path
    :returns: HOP-compliant output directory path.
    :rtype: Path
    :raises ValueError: If tier class cannot be inferred from the script path.

    Example::

        >>> get_default_output_dir("scripts/producers/generate_anchor_inventory.py")
        PosixPath('.repo_studios/reports/healthview/producer_reports')
        >>> get_default_output_dir("scripts/aggregators/aggregate_docs_health.py")
        PosixPath('.repo_studios/reports/healthview/aggregator_reports')
    """
    tier_class = infer_class_from_script(script_path)
    if tier_class is None:
        raise ValueError(f"Cannot infer tier class from script path: {script_path}")
    return get_class_root(tier_class)


def validate_output_path(path: Path) -> bool:
    """Check if a path follows HOP structure.

    Validates that the path contains the required HealthView structure
    with a recognized tier class folder.

    :param path: Path to validate.
    :type path: Path
    :returns: True if path follows HOP structure, False otherwise.
    :rtype: bool

    Example::

        >>> validate_output_path(Path(".repo_studios/reports/healthview/producer_reports/topic"))
        True
        >>> validate_output_path(Path(".repo_studios/reports/healthview/topic"))
        False
        >>> validate_output_path(Path("/some/random/path"))
        False
    """
    parts = path.parts
    if "healthview" not in parts:
        return False

    tier_folders = {
        "aggregator_reports",
        "consumer_reports",
        "orchestrator_reports",
        "producer_reports",
        "rawview",
        "summarizer_reports",
    }
    return any(folder in parts for folder in tier_folders)


def get_all_class_roots() -> dict[TierClass, Path]:
    """Return a copy of all tier class root paths.

    :returns: Dictionary mapping tier class names to their root paths.
    :rtype: dict[TierClass, Path]

    Example::

        >>> roots = get_all_class_roots()
        >>> roots["producer"]
        PosixPath('.repo_studios/reports/healthview/producer_reports')
    """
    return dict(_CLASS_MAPPING)


# ─────────────────────────────────────────────────────────────────────────────
# Module Exports
# ─────────────────────────────────────────────────────────────────────────────

__all__ = [
    # Constants
    "REPO_STUDIOS_ROOT",
    "REPORTS_ROOT",
    "HEALTHVIEW_ROOT",
    "AGGREGATOR_REPORTS",
    "CONSUMER_REPORTS",
    "ORCHESTRATOR_REPORTS",
    "PRODUCER_REPORTS",
    "RAWVIEW",
    "SUMMARIZER_REPORTS",
    "VALID_TIER_CLASSES",
    # Types
    "TierClass",
    # Functions
    "get_class_root",
    "build_topic_path",
    "build_absolute_topic_path",
    "infer_class_from_script",
    "get_default_output_dir",
    "validate_output_path",
    "get_all_class_roots",
]
