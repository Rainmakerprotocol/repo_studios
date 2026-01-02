#!/usr/bin/env python3
"""Import Graph Report generator with positional bundle artifacts.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/healthview/import_graph/<YYYYMMDD-HHMM>/`
        - `manifest.json`
        - `summary.md`
        - `telemetry.json`

Enhanced features:
    - File/line provenance tracking for cycle diagnosis
    - --scan-all flag to scan entire repo (not just owned packages)
    - --exclude flag to skip directories (default: .venv, __pycache__, .git, node_modules)
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

from libraries.cli import resolve_path, resolve_repo_root

TOPIC_SLUG = "import_graph"
DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_import_graph_report")
OWNED_DEFAULT = {
    ".repo_studios",
    "legacy",
}

DEFAULT_EXCLUDE = {
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
    "site-packages",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
}


@dataclass
class ImportEdge:
    """Represents a single import statement with file/line provenance."""

    source_file: Path
    line_number: int
    import_statement: str
    target_module: str


IMPORT_RE = re.compile(r"^(?:from\s+([\w\.]+)\s+import\s+|import\s+([\w\.]+))")


def iter_py_files(
    root: Path,
    owned: set[str] | None,
    exclude: set[str] | None = None,
) -> Iterable[Path]:
    """Iterate over Python files in the repository.

    Args:
        root: Repository root path.
        owned: Set of top-level directories to scan. If None, scan all.
        exclude: Set of directory names to skip (e.g., .venv, __pycache__).

    Yields:
        Path objects for each .py file found.
    """
    exclude_set = exclude if exclude is not None else DEFAULT_EXCLUDE
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        # Skip excluded directories
        if any(part in exclude_set for part in rel.parts):
            continue
        # If owned is None (scan-all mode), yield all non-excluded files
        if owned is None:
            yield path
        elif rel.parts and rel.parts[0] in owned:
            yield path


def parse_imports(path: Path) -> list[ImportEdge]:
    """Parse import statements from a Python file with line provenance.

    Args:
        path: Path to the Python file.

    Returns:
        List of ImportEdge objects with file, line, statement, and target module.
    """
    edges: list[ImportEdge] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            match = IMPORT_RE.match(stripped)
            if not match:
                continue
            module = match.group(1) or match.group(2) or ""
            base = module.split(".")[0]
            if base:
                edges.append(
                    ImportEdge(
                        source_file=path,
                        line_number=line_num,
                        import_statement=stripped,
                        target_module=base,
                    )
                )
    except Exception:
        return edges
    return edges


def parse_imports_simple(path: Path) -> set[str]:
    """Parse import statements and return just the module names (legacy compatibility)."""
    return {edge.target_module for edge in parse_imports(path)}


def _module_identifier(rel: Path) -> str:
    parts = rel.parts
    if not parts:
        return ""
    if len(parts) >= 2 and parts[1].endswith(".py"):
        return parts[0]
    head = parts[0]
    if head in {".repo_studios", "legacy"} and len(parts) >= 2:
        return "/".join(parts[:2])
    return head


def _alias_candidates(module_id: str) -> set[str]:
    module_id = module_id.replace("\\", "/")
    parts = module_id.split("/")
    aliases: set[str] = {module_id}
    if parts:
        first = parts[0].lstrip(".")
        if first:
            aliases.add(first)
        aliases.add(parts[-1])
        aliases.add(module_id.replace("/", "."))
    return {alias for alias in aliases if alias}


@dataclass
class GraphResult:
    """Result of building the import graph with provenance tracking."""

    graph: dict[str, set[str]]
    edge_provenance: dict[tuple[str, str], list[dict[str, Any]]]
    files_scanned: int


def build_graph(
    root: Path,
    owned: set[str] | None,
    exclude: set[str] | None = None,
) -> GraphResult:
    """Build import graph with edge provenance tracking.

    Args:
        root: Repository root path.
        owned: Set of top-level directories to scan. If None, scan all.
        exclude: Set of directory names to skip.

    Returns:
        GraphResult with graph, edge provenance, and file count.
    """
    raw_dependencies: dict[str, list[ImportEdge]] = defaultdict(list)
    modules: set[str] = set()
    files_scanned = 0

    for py_file in iter_py_files(root, owned, exclude):
        files_scanned += 1
        try:
            rel = py_file.relative_to(root)
        except Exception:
            continue
        source = _module_identifier(rel)
        if not source:
            continue
        modules.add(source)
        raw_dependencies[source].extend(parse_imports(py_file))

    alias_map: dict[str, set[str]] = defaultdict(set)
    for module_id in modules:
        for alias in _alias_candidates(module_id):
            alias_map[alias].add(module_id)

    graph: dict[str, set[str]] = {module_id: set() for module_id in modules}
    edge_provenance: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for module_id, import_edges in raw_dependencies.items():
        for edge in import_edges:
            for target in alias_map.get(edge.target_module, ()):
                if target != module_id:
                    graph[module_id].add(target)
                    # Store provenance for this edge
                    edge_key = (module_id, target)
                    edge_provenance[edge_key].append({
                        "file": str(edge.source_file.relative_to(root)),
                        "line": edge.line_number,
                        "statement": edge.import_statement,
                    })

    return GraphResult(
        graph=graph,
        edge_provenance=dict(edge_provenance),
        files_scanned=files_scanned,
    )


def fan_metrics(graph: dict[str, set[str]]) -> tuple[dict[str, int], dict[str, int]]:
    fan_out = {name: len(neighbors) for name, neighbors in graph.items()}
    fan_in: dict[str, int] = defaultdict(int)
    for _, neighbors in graph.items():
        for dep in neighbors:
            fan_in[dep] += 1
    return fan_in, fan_out


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    nodes = list(graph.keys())
    for start in nodes:
        stack: list[tuple[str, list[str]]] = [(start, [start])]
        seen_edges: set[tuple[str, str]] = set()
        while stack:
            current, path = stack.pop()
            for neighbor in graph.get(current, ()):  # pragma: no branch - simple loop
                if neighbor == start and len(path) > 1:
                    cycles.append(path + [start])
                    continue
                if (current, neighbor) in seen_edges:
                    continue
                seen_edges.add((current, neighbor))
                if neighbor not in path and neighbor in graph:
                    stack.append((neighbor, path + [neighbor]))
    normalized: list[list[str]] = []
    signatures: set[tuple[str, ...]] = set()
    for cycle in cycles:
        body = cycle[:-1]
        if not body:
            continue
        pivot = min(range(len(body)), key=lambda idx: body[idx])
        rotated = body[pivot:] + body[:pivot]
        signature = tuple(rotated)
        if signature in signatures:
            continue
        signatures.add(signature)
        normalized.append(rotated + [rotated[0]])
    return normalized


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _serialize_graph(graph: dict[str, set[str]]) -> dict[str, list[str]]:
    return {name: sorted(neighbors) for name, neighbors in sorted(graph.items())}


def build_report(
    *,
    repo_root: Path,
    owned_requested: Sequence[str] | None,
    graph: dict[str, set[str]],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    cycles: list[list[str]],
    edge_provenance: dict[tuple[str, str], list[dict[str, Any]]],
    files_scanned: int,
    generated_ts: datetime,
    scan_all: bool = False,
) -> dict[str, Any]:
    """Build the report payload with provenance tracking.

    Args:
        repo_root: Repository root path.
        owned_requested: Packages requested (None if scan-all mode).
        graph: Module dependency graph.
        fan_in: Fan-in metrics per module.
        fan_out: Fan-out metrics per module.
        cycles: Detected import cycles.
        edge_provenance: File/line provenance for each edge.
        files_scanned: Total number of Python files scanned.
        generated_ts: Report generation timestamp.
        scan_all: Whether scan-all mode was used.

    Returns:
        Report dictionary with all metrics and provenance.
    """
    graph_serialized = _serialize_graph(graph)
    all_nodes = set(graph_serialized.keys())
    for neighbors in graph_serialized.values():
        all_nodes.update(neighbors)
    edge_count = sum(len(neighbors) for neighbors in graph_serialized.values())

    if owned_requested is None:
        owned_requested_set: set[str] = set()
        resolved_packages: list[str] = []
        missing_packages: list[str] = []
    else:
        owned_requested_set = {pkg for pkg in owned_requested}
        resolved_packages = sorted(
            pkg for pkg in owned_requested_set if (repo_root / pkg).exists()
        )
        missing_packages = sorted(
            pkg for pkg in owned_requested_set if pkg not in resolved_packages
        )

    status = "ok" if scan_all or resolved_packages else "no_targets"
    summary = {
        "status": status,
        "module_count": len(all_nodes),
        "edge_count": edge_count,
        "cycle_count": len(cycles),
        "files_scanned": files_scanned,
    }
    top_fan_in = [
        {"module": name, "count": count}
        for name, count in sorted(fan_in.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    top_fan_out = [
        {"module": name, "count": count}
        for name, count in sorted(fan_out.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    isolated_modules = sorted(
        name for name in all_nodes if fan_in.get(name, 0) == 0 and fan_out.get(name, 0) == 0
    )

    # Build cycle provenance - attach file/line info to each cycle edge
    cycle_provenance: list[dict[str, Any]] = []
    for cycle in cycles:
        cycle_edges: list[dict[str, Any]] = []
        for i in range(len(cycle) - 1):
            edge_key = (cycle[i], cycle[i + 1])
            edge_files = edge_provenance.get(edge_key, [])
            cycle_edges.append({
                "from": cycle[i],
                "to": cycle[i + 1],
                "locations": edge_files[:5],  # Limit to first 5 for readability
            })
        cycle_provenance.append({
            "cycle": cycle,
            "edges": cycle_edges,
        })

    # Serialize edge provenance with string keys for JSON
    edge_provenance_serialized: dict[str, list[dict[str, Any]]] = {
        f"{src} -> {dst}": locations
        for (src, dst), locations in sorted(edge_provenance.items())
    }

    return {
        "schema_version": 2,  # Bumped for provenance addition
        "generated_utc": generated_ts.isoformat(),
        "repo_root": str(repo_root),
        "scan_all": scan_all,
        "owned_packages_requested": sorted(owned_requested_set) if owned_requested_set else None,
        "owned_packages_resolved": resolved_packages if resolved_packages else None,
        "missing_owned_packages": missing_packages if missing_packages else None,
        "summary": summary,
        "top_fan_in": top_fan_in,
        "top_fan_out": top_fan_out,
        "cycles": cycles,
        "cycle_provenance": cycle_provenance,
        "isolated_modules": isolated_modules,
        "graph": graph_serialized,
        "edge_provenance": edge_provenance_serialized,
    }


def _build_manifest(*, report: dict[str, Any], repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    status = summary.get("status") if isinstance(summary, dict) else None
    return {
        "schema_version": 1,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": inputs.get("run_timestamp"),
        "git_sha": None,
        "status": "ok" if status in {"ok", "no_targets"} else "failed",
        "catalog": [
            {"artifact": "manifest.json", "kind": "json"},
            {"artifact": "summary.md", "kind": "markdown"},
            {"artifact": "telemetry.json", "kind": "json"},
        ],
        "inputs": {
            "repo_root": str(repo_root),
            **inputs,
        },
        "provenance": {
            "trigger_type": "manual",
        },
        "summary": summary,
    }


def write_markdown(report: dict[str, Any]) -> str:
    """Generate markdown summary with cycle provenance for diagnostics."""
    summary = report["summary"]
    scan_all = report.get("scan_all", False)
    owned_requested = report.get("owned_packages_requested") or []
    owned_resolved = report.get("owned_packages_resolved") or []
    missing = report.get("missing_owned_packages") or []
    files_scanned = summary.get("files_scanned", 0)

    lines = [
        "# Import Graph Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Repo Root: {report['repo_root']}",
        "",
        "## Summary",
        "",
        f"- Status: {summary['status']}",
        f"- Files scanned: {files_scanned}",
        f"- Module count: {summary['module_count']}",
        f"- Edge count: {summary['edge_count']}",
        f"- Cycle count: {summary['cycle_count']}",
    ]

    if scan_all:
        lines.append("- Scan mode: all (entire repository)")
    else:
        lines.append(
            f"- Owned packages requested: {', '.join(owned_requested) if owned_requested else '(none)'}"
        )
        lines.append(
            f"- Owned packages resolved: {', '.join(owned_resolved) if owned_resolved else '(none)'}"
        )
        lines.append(
            f"- Missing owned packages: {', '.join(missing) if missing else '(none)'}"
        )

    isolated = report.get("isolated_modules", [])
    if isolated:
        lines.append("- Isolated modules:")
        for mod in isolated:
            lines.append(f"  - {mod}")
    else:
        lines.append("- Isolated modules: (none)")

    lines.extend(["", "## Top Fan-In (Modules Most Depended On)", ""])
    if report.get("top_fan_in"):
        for entry in report["top_fan_in"]:
            lines.append(f"- {entry['module']}: {entry['count']}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Top Fan-Out (Modules With Many Dependencies)", ""])
    if report.get("top_fan_out"):
        for entry in report["top_fan_out"]:
            lines.append(f"- {entry['module']}: {entry['count']}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Cycles Detected", ""])
    cycle_provenance = report.get("cycle_provenance", [])
    if cycle_provenance:
        for i, cycle_info in enumerate(cycle_provenance[:10], start=1):
            cycle = cycle_info.get("cycle", [])
            lines.append(f"### Cycle {i}: {' → '.join(cycle)}")
            lines.append("")
            edges = cycle_info.get("edges", [])
            for edge in edges:
                lines.append(f"**{edge['from']} → {edge['to']}:**")
                locations = edge.get("locations", [])
                if locations:
                    for loc in locations[:3]:  # Show first 3 locations per edge
                        lines.append(f"- `{loc['file']}` line {loc['line']}: `{loc['statement']}`")
                else:
                    lines.append("- (no location data)")
                lines.append("")
    elif report.get("cycles"):
        # Fallback if no provenance (shouldn't happen with new code)
        for cycle in report["cycles"][:10]:
            lines.append(f"- {' → '.join(cycle)}")
    else:
        lines.append("No import cycles detected. ✓")

    return "\n".join(lines) + "\n"


def configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric, format="%(levelname)s: %(message)s")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate import graph report with cycle provenance tracking"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (auto-discovered via .repo_studios marker when omitted)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Base directory for generated report bundles",
    )
    parser.add_argument(
        "--owned",
        nargs="+",
        help="Owned top-level packages to include (defaults applied if omitted)",
    )
    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan entire repository (ignore --owned filter)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=list(DEFAULT_EXCLUDE),
        help=f"Directory names to exclude (default: {', '.join(sorted(DEFAULT_EXCLUDE))})",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical runs to retain",
    )
    parser.add_argument(
        "--timestamp",
        help="Optional ISO timestamp for deterministic run directory naming",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    output_dir = resolve_path(
        str(args.output_dir),
        repo_root=repo_root,
        default=DEFAULT_OUTPUT_DIR,
        ensure_dir=True,
    )

    exclude_set = set(args.exclude)

    # Determine scan mode
    if args.scan_all:
        owned: set[str] | None = None
        logging.info("Scan mode: all (scanning entire repository)")
    else:
        owned = set(args.owned) if args.owned else set(OWNED_DEFAULT)
        owned.add(".repo_studios")
        logging.info("Scan mode: owned packages (%s)", ", ".join(sorted(owned)))

    generated_ts = _parse_timestamp(args.timestamp)
    timestamp = generated_ts.strftime("%Y%m%d-%H%M")

    # Build graph with provenance tracking
    graph_result = build_graph(repo_root, owned, exclude_set)
    logging.info("Scanned %d Python files", graph_result.files_scanned)

    fan_in, fan_out = fan_metrics(graph_result.graph)
    cycles = find_cycles(graph_result.graph)

    if cycles:
        logging.warning("Detected %d import cycle(s)", len(cycles))

    report = build_report(
        repo_root=repo_root,
        owned_requested=sorted(owned) if owned else None,
        graph=graph_result.graph,
        fan_in=fan_in,
        fan_out=fan_out,
        cycles=cycles,
        edge_provenance=graph_result.edge_provenance,
        files_scanned=graph_result.files_scanned,
        generated_ts=generated_ts,
        scan_all=args.scan_all,
    )

    inputs = {
        "run_timestamp": timestamp,
        "scan_all": args.scan_all,
        "owned_packages_requested": sorted(owned) if owned else None,
        "exclude_patterns": sorted(exclude_set),
        "artifacts_to_keep": args.artifacts_to_keep,
    }

    manifest = _build_manifest(report=report, repo_root=repo_root, inputs=inputs)
    telemetry: dict[str, Any] = {
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": timestamp,
        "generated_utc": report.get("generated_utc"),
        "metrics": {
            "status": report.get("summary", {}).get("status"),
            "files_scanned": report.get("summary", {}).get("files_scanned"),
            "module_count": report.get("summary", {}).get("module_count"),
            "edge_count": report.get("summary", {}).get("edge_count"),
            "cycle_count": report.get("summary", {}).get("cycle_count"),
            "scan_all": args.scan_all,
            "owned_packages_requested": report.get("owned_packages_requested"),
            "owned_packages_resolved": report.get("owned_packages_resolved"),
        },
        "payload": report,
    }

    storage = create_storage(
        output_dir=output_dir,
        viewer_slug="",
        topic="",
        timestamp=timestamp,
    )

    markdown = write_markdown(report)

    # DB_INTEGRATION_MARKER: write manifest.json (report_runs)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: write summary.md (report_summaries)
    storage.write_summary({"markdown": markdown}, format="markdown")
    # DB_INTEGRATION_MARKER: write telemetry.json + extracted metrics (test_metrics)
    storage.write_telemetry(telemetry)

    run_dir = storage.file_storage.bundle_dir
    topic_dir = run_dir.parent
    prune_run_directories(
        topic_dir,
        keep=args.artifacts_to_keep,
        current_run=run_dir,
        logger=logging.getLogger(__name__),
    )
    logging.info("Import graph report written to %s", run_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
