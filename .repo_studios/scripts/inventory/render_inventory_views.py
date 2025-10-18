#!/usr/bin/env python3
"""Generate secondary inventory views for Repo Studios."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "inventory_schema"
VIEWS_DIR = SCHEMA_ROOT / "views"
REPORTS_ROOT = ROOT / "reports"
IGNORED_FILES = {"enums.yaml", "inventory_entry_template.yaml"}


def load_inventory(schema_root: Path) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for path in sorted(schema_root.glob("**/*.yaml")):
        if path.name in IGNORED_FILES:
            continue
        if VIEWS_DIR in path.parents:
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    entries.append(item)
    return entries


def ensure_views_dir() -> None:
    VIEWS_DIR.mkdir(parents=True, exist_ok=True)


def docs_view(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for record in entries:
        if record.get("asset_kind") != "document":
            continue
        out.append(
            {
                "id": record.get("id"),
                "name": record.get("name"),
                "path": record.get("path"),
                "maturity": record.get("maturity"),
                "status": record.get("status"),
                "consumers": record.get("consumers", []),
                "tags": record.get("tags", []),
                "artifact_type": record.get("artifact_type"),
            }
        )
    return out


def scripts_view(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for record in entries:
        if record.get("asset_kind") != "script":
            continue
        out.append(
            {
                "id": record.get("id"),
                "name": record.get("name"),
                "path": record.get("path"),
                "roles": record.get("roles", []),
                "maturity": record.get("maturity"),
                "status": record.get("status"),
                "tags": record.get("tags", []),
                "related_assets": record.get("related_assets", []),
                "artifact_type": record.get("artifact_type"),
            }
        )
    return out


def tests_view(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for record in entries:
        if record.get("asset_kind") != "test":
            continue
        out.append(
            {
                "id": record.get("id"),
                "name": record.get("name"),
                "path": record.get("path"),
                "status": record.get("status"),
                "related_assets": record.get("related_assets", []),
                "artifact_type": record.get("artifact_type"),
            }
        )
    return out


def summary_view(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    counters: Dict[str, Counter] = defaultdict(Counter)
    total = 0
    status_by_kind: Dict[str, Counter] = defaultdict(Counter)
    maturity_by_kind: Dict[str, Counter] = defaultdict(Counter)
    consumer_counts: Counter = Counter()
    tag_counts: Counter = Counter()
    for record in entries:
        total += 1
        counters["asset_kind"][record.get("asset_kind", "unknown")] += 1
        counters["maturity"][record.get("maturity", "unknown")] += 1
        counters["status"][record.get("status", "unknown")] += 1
        asset_kind = record.get("asset_kind", "unknown")
        status = record.get("status", "unknown")
        maturity = record.get("maturity", "unknown")
        status_by_kind[asset_kind][status] += 1
        maturity_by_kind[asset_kind][maturity] += 1
        for consumer in record.get("consumers", []):
            consumer_counts[consumer] += 1
        for tag in record.get("tags", []):
            tag_counts[tag] += 1
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at": generated_at,
        "total": total,
        "by_asset_kind": dict(counters["asset_kind"]),
        "by_maturity": dict(counters["maturity"]),
        "by_status": dict(counters["status"]),
        "status_by_asset_kind": {kind: dict(counter) for kind, counter in status_by_kind.items()},
        "maturity_by_asset_kind": {kind: dict(counter) for kind, counter in maturity_by_kind.items()},
        "consumers": dict(consumer_counts),
        "top_tags": [
            {"tag": tag, "count": count}
            for tag, count in tag_counts.most_common()
        ],
    }


def summary_dashboard(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    maturity_totals: Dict[str, Counter] = defaultdict(Counter)
    role_counts: Counter = Counter()
    artifact_types: Counter = Counter()
    for record in entries:
        maturity = record.get("maturity", "unknown")
        asset_kind = record.get("asset_kind", "unknown")
        maturity_totals[asset_kind][maturity] += 1
        for role in record.get("roles", []):
            role_counts[role] += 1
        artifact_types[record.get("artifact_type", "unknown")] += 1

    return {
        "maturity_totals_by_asset_kind": {kind: dict(counter) for kind, counter in maturity_totals.items()},
        "roles": dict(role_counts),
        "artifact_types": dict(artifact_types),
    }


def write_yaml(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, default_flow_style=False, sort_keys=False)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_report_topics(reports_root: Path) -> Dict[str, Path]:
    """Ensure topic folders under reports/ and return mapping to latest paths."""
    topics = {
        "docs": reports_root / "docs" / "latest",
        "scripts": reports_root / "scripts" / "latest",
        "tests": reports_root / "tests" / "latest",
        "summary": reports_root / "summary" / "latest",
    }
    for path in topics.values():
        path.mkdir(parents=True, exist_ok=True)
    return topics


def write_stub(path: Path, destination: Path) -> None:
    """Write a compatibility stub pointing to the new report location."""
    generated_at = datetime.now(timezone.utc).isoformat()
    relative = destination.relative_to(ROOT)
    if path.suffix == ".json":
        write_json(path, {"redirect": str(relative), "generated_at": generated_at})
    else:
        write_yaml(
            path,
            [
                {
                    "redirect": str(relative),
                    "generated_at": generated_at,
                    "note": "View relocated under reports/<topic>/latest/.",
                }
            ],
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Render inventory secondary views")
    parser.add_argument("--schema-root", default=str(SCHEMA_ROOT), help="Path to inventory schema directory")
    parser.add_argument("--views-dir", default=str(VIEWS_DIR), help="Compatibility directory for legacy views")
    parser.add_argument("--reports-root", default=str(REPORTS_ROOT), help="Destination root for topic reports")
    args = parser.parse_args()

    schema_root = Path(args.schema_root).resolve()
    views_dir = Path(args.views_dir).resolve()
    reports_root = Path(args.reports_root).resolve()

    entries = load_inventory(schema_root)
    views_dir.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)
    topic_paths = ensure_report_topics(reports_root)

    docs_path = topic_paths["docs"] / "docs_overview.yaml"
    write_yaml(docs_path, docs_view(entries))
    write_stub(views_dir / "docs_overview.yaml", docs_path)

    scripts_path = topic_paths["scripts"] / "scripts_overview.yaml"
    write_yaml(scripts_path, scripts_view(entries))
    write_stub(views_dir / "scripts_overview.yaml", scripts_path)

    tests_path = topic_paths["tests"] / "tests_overview.yaml"
    write_yaml(tests_path, tests_view(entries))
    write_stub(views_dir / "tests_overview.yaml", tests_path)

    summary_path = topic_paths["summary"] / "summary.json"
    summary_data = summary_view(entries)
    write_json(summary_path, summary_data)
    dashboard_path = topic_paths["summary"] / "dashboard.json"
    write_json(dashboard_path, summary_dashboard(entries))
    write_stub(views_dir / "summary.json", summary_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
