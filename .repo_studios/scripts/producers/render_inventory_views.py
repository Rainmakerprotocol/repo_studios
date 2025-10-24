#!/usr/bin/env python3
"""Render structured inventory views and maintain legacy compatibility."""
from __future__ import annotations

import argparse
import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA_ROOT = Path(".repo_studios/inventory_schema")
DEFAULT_VIEWS_DIR = Path(".repo_studios/inventory_schema/views")
DEFAULT_REPORTS_ROOT = Path(".repo_studios/reports")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/render_inventory_views")
RUN_PREFIX = "render_inventory_views"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1
IGNORED_FILES = {"enums.yaml", "inventory_entry_template.yaml"}


@dataclass(frozen=True)
class ViewBundle:
    docs: List[Dict[str, Any]]
    scripts: List[Dict[str, Any]]
    tests: List[Dict[str, Any]]
    summary: Dict[str, Any]
    dashboard: Dict[str, Any]


def _current_time() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return _current_time()
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO timestamp '{raw}'") from exc


def _format_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d_%H%M%S")


def _sanitize_slug(slug: str) -> str:
    return slug.replace("/", "_").replace("\\", "_")


def _prepare_run_dir(output_dir: Path, slug: str) -> Path:
    run_dir = output_dir / f"{RUN_PREFIX}-{_sanitize_slug(slug)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    runs = [node for node in output_dir.iterdir() if node.is_dir() and node.name.startswith(f"{RUN_PREFIX}-")]
    runs.sort(key=lambda node: node.name, reverse=True)
    for index, node in enumerate(runs):
        if index < keep or node == current_run:
            continue
        for child in node.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
        node.rmdir()


def load_inventory(schema_root: Path, views_dir: Path) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for path in sorted(schema_root.glob("**/*.yaml")):
        if path.name in IGNORED_FILES:
            continue
        if views_dir in path.parents:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        except yaml.YAMLError as exc:
            logging.warning("Skipping %s due to YAML error: %s", path, exc)
            continue
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    entries.append(item)
    return entries


def docs_view(entries: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
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
    out: List[Dict[str, Any]] = []
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
    out: List[Dict[str, Any]] = []
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


def summary_view(entries: Iterable[Dict[str, Any]], *, generated_at: datetime) -> Dict[str, Any]:
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
    return {
        "generated_at": generated_at.isoformat(),
        "total": total,
        "by_asset_kind": dict(counters["asset_kind"]),
        "by_maturity": dict(counters["maturity"]),
        "by_status": dict(counters["status"]),
        "status_by_asset_kind": {kind: dict(counter) for kind, counter in status_by_kind.items()},
        "maturity_by_asset_kind": {kind: dict(counter) for kind, counter in maturity_by_kind.items()},
        "consumers": dict(consumer_counts),
        "top_tags": [{"tag": tag, "count": count} for tag, count in tag_counts.most_common()],
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


def build_views(entries: List[Dict[str, Any]], *, generated_at: datetime) -> ViewBundle:
    return ViewBundle(
        docs=docs_view(entries),
        scripts=scripts_view(entries),
        tests=tests_view(entries),
        summary=summary_view(entries, generated_at=generated_at),
        dashboard=summary_dashboard(entries),
    )


def write_yaml(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, default_flow_style=False, sort_keys=False)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def ensure_report_topics(reports_root: Path) -> Dict[str, Path]:
    topics = {
        "docs": reports_root / "docs" / "latest",
        "scripts": reports_root / "scripts" / "latest",
        "tests": reports_root / "tests" / "latest",
        "summary": reports_root / "summary" / "latest",
    }
    for path in topics.values():
        path.mkdir(parents=True, exist_ok=True)
    return topics


def _compute_redirect(repo_root: Path, destination: Path) -> str:
    base = repo_root / ".repo_studios"
    try:
        relative = destination.relative_to(base)
    except ValueError:
        relative = destination.relative_to(repo_root)
    return str(relative).replace("\\", "/")


def write_stub(path: Path, destination: Path, *, generated_at: datetime, repo_root: Path) -> None:
    redirect = _compute_redirect(repo_root, destination)
    payload: Any
    if path.suffix == ".json":
        payload = {"redirect": redirect, "generated_at": generated_at.isoformat()}
        write_json(path, payload)
    else:
        payload = [
            {
                "redirect": redirect,
                "generated_at": generated_at.isoformat(),
                "note": "View relocated under reports/<topic>/latest/.",
            }
        ]
        write_yaml(path, payload)


def _copy_latest(src: Path, dest: Path) -> None:
    try:
        if dest.exists():
            dest.unlink()
        dest.hardlink_to(src)
    except OSError:
        dest.write_bytes(src.read_bytes())


def update_latest_artifacts(run_dir: Path, output_dir: Path) -> None:
    mapping = {
        "latest_report.json": run_dir / "report.json",
        "latest_report.md": run_dir / "report.md",
        "latest_report.log": run_dir / "log.txt",
        "latest_raw.json": run_dir / "raw.json",
    }
    for filename, src in mapping.items():
        dest = output_dir / filename
        _copy_latest(src, dest)


def compose_report_payload(
    *,
    repo_root: Path,
    run_dir: Path,
    slug: str,
    generated_at: datetime,
    bundle: ViewBundle,
    schema_root: Path,
    views_dir: Path,
    reports_root: Path,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    summary = bundle.summary
    docs_count = len(bundle.docs)
    scripts_count = len(bundle.scripts)
    tests_count = len(bundle.tests)
    counts = {
        "total": summary.get("total", 0),
        "docs": docs_count,
        "scripts": scripts_count,
        "tests": tests_count,
    }
    report_payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "timestamp": slug,
        "generated_utc": generated_at.isoformat(),
        "repo_root": str(repo_root),
        "output_dir": str(run_dir),
        "inputs": {
            "schema_root": str(schema_root),
            "views_dir": str(views_dir),
            "reports_root": str(reports_root),
        },
        "counts": {
            "totals": counts,
            "by_asset_kind": summary.get("by_asset_kind", {}),
            "by_maturity": summary.get("by_maturity", {}),
            "by_status": summary.get("by_status", {}),
        },
        "top_tags": summary.get("top_tags", [])[:10],
        "top_consumers": sorted(bundle.summary.get("consumers", {}).items(), key=lambda item: item[1], reverse=True)[:10],
        "notes": [],
    }
    raw_payload = {
        **report_payload,
        "views": {
            "docs": bundle.docs,
            "scripts": bundle.scripts,
            "tests": bundle.tests,
        },
        "summary": bundle.summary,
        "dashboard": bundle.dashboard,
    }
    return report_payload, raw_payload


def render_markdown(report_payload: Dict[str, Any]) -> str:
    counts = report_payload.get("counts", {}).get("totals", {})
    lines = ["# Render Inventory Views\n\n"]
    lines.append(f"- generated_utc: {report_payload['generated_utc']}\n")
    lines.append(f"- status: {report_payload['status']}\n")
    lines.append(f"- output_dir: {report_payload['output_dir']}\n")
    lines.append("\n## Totals\n\n")
    lines.append("| Metric | Value |\n")
    lines.append("|---|---:|\n")
    lines.append(f"| entries | {counts.get('total', 0)} |\n")
    lines.append(f"| docs | {counts.get('docs', 0)} |\n")
    lines.append(f"| scripts | {counts.get('scripts', 0)} |\n")
    lines.append(f"| tests | {counts.get('tests', 0)} |\n")
    lines.append("\n## Top Tags\n\n")
    tags = report_payload.get("top_tags", [])
    if not tags:
        lines.append("(none)\n")
    else:
        for item in tags[:10]:
            lines.append(f"- {item['tag']}: {item['count']}\n")
    lines.append("\n## Leading Consumers\n\n")
    consumers = report_payload.get("top_consumers", [])
    if not consumers:
        lines.append("(none)\n")
    else:
        for name, count in consumers:
            lines.append(f"- {name}: {count}\n")
    return "".join(lines)


def render_log(report_payload: Dict[str, Any]) -> str:
    counts = report_payload.get("counts", {}).get("totals", {})
    return "\n".join(
        [
            f"status={report_payload['status']}",
            f"timestamp={report_payload['timestamp']}",
            f"total_entries={counts.get('total', 0)}",
            f"docs={counts.get('docs', 0)}",
            f"scripts={counts.get('scripts', 0)}",
            f"tests={counts.get('tests', 0)}",
        ]
    ) + "\n"


def write_run_artifacts(run_dir: Path, report_payload: Dict[str, Any], raw_payload: Dict[str, Any]) -> None:
    (run_dir / "report.json").write_text(json.dumps(report_payload, indent=2) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown(report_payload), encoding="utf-8")
    (run_dir / "log.txt").write_text(render_log(report_payload), encoding="utf-8")
    (run_dir / "raw.json").write_text(json.dumps(raw_payload, indent=2) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render inventory secondary views and emit structured artifacts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="Repository root used to resolve relative paths")
    parser.add_argument("--schema-root", default=str(DEFAULT_SCHEMA_ROOT), help="Path to inventory schema directory")
    parser.add_argument("--views-dir", default=str(DEFAULT_VIEWS_DIR), help="Legacy compatibility directory for views")
    parser.add_argument("--reports-root", default=str(DEFAULT_REPORTS_ROOT), help="Destination root for topic reports")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Destination for structured producer artifacts")
    parser.add_argument("--timestamp", help="ISO timestamp override for the run")
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="Number of historical runs to retain")
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity")
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(levelname)s: %(message)s")

    repo_root = Path(args.repo_root).resolve()
    schema_root = _resolve(repo_root, args.schema_root)
    views_dir = _ensure_dir(_resolve(repo_root, args.views_dir))
    reports_root = _ensure_dir(_resolve(repo_root, args.reports_root))
    output_dir = _ensure_dir(_resolve(repo_root, args.output_dir))

    generated_at = _parse_timestamp(args.timestamp)
    slug = _format_slug(generated_at)
    run_dir = _prepare_run_dir(output_dir, slug)

    entries = load_inventory(schema_root, views_dir)
    bundle = build_views(entries, generated_at=generated_at)

    report_payload, raw_payload = compose_report_payload(
        repo_root=repo_root,
        run_dir=run_dir,
        slug=slug,
        generated_at=generated_at,
        bundle=bundle,
        schema_root=schema_root,
        views_dir=views_dir,
        reports_root=reports_root,
    )

    write_run_artifacts(run_dir, report_payload, raw_payload)
    update_latest_artifacts(run_dir, output_dir)

    topic_paths = ensure_report_topics(reports_root)

    docs_path = topic_paths["docs"] / "docs_overview.yaml"
    scripts_path = topic_paths["scripts"] / "scripts_overview.yaml"
    tests_path = topic_paths["tests"] / "tests_overview.yaml"
    summary_path = topic_paths["summary"] / "summary.json"
    dashboard_path = topic_paths["summary"] / "dashboard.json"

    write_yaml(docs_path, bundle.docs)
    write_yaml(scripts_path, bundle.scripts)
    write_yaml(tests_path, bundle.tests)
    write_json(summary_path, bundle.summary)
    write_json(dashboard_path, bundle.dashboard)

    write_stub(views_dir / "docs_overview.yaml", docs_path, generated_at=generated_at, repo_root=repo_root)
    write_stub(views_dir / "scripts_overview.yaml", scripts_path, generated_at=generated_at, repo_root=repo_root)
    write_stub(views_dir / "tests_overview.yaml", tests_path, generated_at=generated_at, repo_root=repo_root)
    write_stub(views_dir / "summary.json", summary_path, generated_at=generated_at, repo_root=repo_root)

    prune_old_runs(output_dir, keep=args.artifacts_to_keep, current_run=run_dir)

    logging.info(
        "render_inventory_views status=%s total=%s docs=%s scripts=%s tests=%s",
        report_payload["status"],
        report_payload["counts"]["totals"]["total"],
        report_payload["counts"]["totals"]["docs"],
        report_payload["counts"]["totals"]["scripts"],
        report_payload["counts"]["totals"]["tests"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
