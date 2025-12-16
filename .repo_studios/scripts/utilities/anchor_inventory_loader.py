"""Utilities for locating and loading anchor inventory outputs.

The anchor inventory producer has migrated to the canonical positional bundle layout:

    <producer_reports>/<viewer_slug>/<topic>/<YYYYMMDD-HHMM>/
        - manifest.json
        - summary.md
        - telemetry.json

The inventory payload is stored in `telemetry.json` under the `payload` key.

This module provides compatibility loading for legacy outputs that used
`anchor_inventory_reports/<run>/report.json` plus `latest_report.json` pointers.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any


CANONICAL_VIEWER_SLUG = "healthview"
CANONICAL_TOPIC = "anchor_inventory"
DEFAULT_CANONICAL_TOPIC_DIR = Path(
    ".repo_studios/reports/producer_reports"  # base
) / CANONICAL_VIEWER_SLUG / CANONICAL_TOPIC

LEGACY_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/anchor_inventory_reports")
LEGACY_LATEST_REPORT = LEGACY_OUTPUT_DIR / "latest_report.json"

_BUNDLE_SLUG_RE = re.compile(r"^\d{8}-\d{4}$")


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _select_latest_canonical_bundle(topic_dir: Path) -> Path | None:
    if not topic_dir.exists():
        return None

    candidates: list[Path] = []
    for child in topic_dir.iterdir():
        if not child.is_dir():
            continue
        if not _BUNDLE_SLUG_RE.match(child.name):
            continue
        if (child / "telemetry.json").exists():
            candidates.append(child)

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.name, reverse=True)
    return candidates[0]


def _unwrap_telemetry_payload(document: dict[str, Any]) -> dict[str, Any] | None:
    payload = document.get("payload")
    if isinstance(payload, dict):
        return payload
    return None


def load_anchor_inventory(
    source: Path | None = None,
    *,
    logger: logging.Logger | None = None,
) -> tuple[dict[str, Any] | None, Path | None]:
    """Load the anchor inventory payload.

    Args:
        source: Optional explicit input path.
            - If a directory:
                - If it contains `telemetry.json`, loads that bundle.
                - Otherwise treats it as the canonical topic dir and selects the latest bundle.
            - If a file:
                - If it is `telemetry.json`, returns its `payload`.
                - Otherwise assumes it is a legacy `report.json`-shaped payload.
            - If omitted:
                - Prefer canonical topic dir latest bundle.
                - Fallback to legacy latest pointer and historical run scanning.
        logger: Optional logger for debug messages.

    Returns:
        (payload, source_path) where payload matches the historical `report.json` schema.
    """

    log = logger or logging.getLogger(__name__)

    candidates: list[Path] = []

    if source is not None:
        candidates.append(source)
    else:
        candidates.append(DEFAULT_CANONICAL_TOPIC_DIR)
        candidates.append(LEGACY_LATEST_REPORT)
        candidates.append(LEGACY_OUTPUT_DIR)

    for candidate in candidates:
        path = candidate
        if path.is_dir():
            telemetry_path = path / "telemetry.json"
            if telemetry_path.exists():
                telemetry = _load_json(telemetry_path)
                if telemetry is None:
                    continue
                payload = _unwrap_telemetry_payload(telemetry)
                if payload is not None:
                    return payload, telemetry_path
                log.debug("telemetry.json missing payload; returning document")
                return telemetry, telemetry_path

            latest_bundle = _select_latest_canonical_bundle(path)
            if latest_bundle is not None:
                telemetry = _load_json(latest_bundle / "telemetry.json")
                if telemetry is None:
                    continue
                payload = _unwrap_telemetry_payload(telemetry)
                if payload is not None:
                    return payload, latest_bundle / "telemetry.json"
                return telemetry, latest_bundle / "telemetry.json"

            # Legacy run directory scan
            if path.exists() and path.name.endswith("anchor_inventory_reports"):
                runs = sorted(
                    (child for child in path.iterdir() if child.is_dir() and child.name.startswith("anchor_inventory-")),
                    key=lambda p: p.name,
                    reverse=True,
                )
                for run_dir in runs:
                    report_path = run_dir / "report.json"
                    payload = _load_json(report_path)
                    if payload is not None:
                        return payload, report_path

            continue

        # File candidate
        if not path.exists():
            continue
        doc = _load_json(path)
        if doc is None:
            continue

        if path.name == "telemetry.json":
            payload = _unwrap_telemetry_payload(doc)
            if payload is not None:
                return payload, path

        return doc, path

    return None, None
