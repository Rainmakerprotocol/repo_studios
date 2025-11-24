#!/usr/bin/env python3
"""Import Graph Report generator with structured artifacts and pruning support."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/import_graph_reports")
RUN_PREFIX = "import_graph"
DEFAULT_ARTIFACTS_TO_KEEP = 10
OWNED_DEFAULT = {
    ".repo_studios",
    "legacy",
}

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import ReportArtifact, WriteReportArtifactsResult, write_report_artifacts
except ModuleNotFoundError:  # pragma: no cover - fallback for script execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import ReportArtifact, WriteReportArtifactsResult, write_report_artifacts


IMPORT_RE = re.compile(r"^(?:from\s+([\w\.]+)\s+import\s+|import\s+([\w\.]+))")


def iter_py_files(root: Path, owned: set[str]) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        rel = path.relative_to(root)
        if rel.parts and rel.parts[0] in owned:
            yield path


def parse_imports(path: Path) -> set[str]:
    imports: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = IMPORT_RE.match(line.strip())
            if not match:
                continue
            module = match.group(1) or match.group(2) or ""
            base = module.split(".")[0]
            if base:
                imports.add(base)
    except Exception:
        return imports
    return imports


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


def build_graph(root: Path, owned: set[str]) -> dict[str, set[str]]:
    raw_dependencies: dict[str, set[str]] = defaultdict(set)
    modules: set[str] = set()

    for py_file in iter_py_files(root, owned):
        try:
            rel = py_file.relative_to(root)
        except Exception:
            continue
        source = _module_identifier(rel)
        if not source:
            continue
        modules.add(source)
        raw_dependencies[source].update(parse_imports(py_file))

    alias_map: dict[str, set[str]] = defaultdict(set)
    for module_id in modules:
        for alias in _alias_candidates(module_id):
            alias_map[alias].add(module_id)

    graph: dict[str, set[str]] = {module_id: set() for module_id in modules}
    for module_id, imports in raw_dependencies.items():
        for dep in imports:
            for target in alias_map.get(dep, ()):
                if target != module_id:
                    graph[module_id].add(target)
    return graph


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
    owned_requested: Sequence[str],
    graph: dict[str, set[str]],
    fan_in: dict[str, int],
    fan_out: dict[str, int],
    cycles: list[list[str]],
    generated_ts: datetime,
) -> dict[str, Any]:
    graph_serialized = _serialize_graph(graph)
    all_nodes = set(graph_serialized.keys())
    for neighbors in graph_serialized.values():
        all_nodes.update(neighbors)
    edge_count = sum(len(neighbors) for neighbors in graph_serialized.values())
    owned_requested_set = {pkg for pkg in owned_requested}
    resolved_packages = sorted(pkg for pkg in owned_requested_set if (repo_root / pkg).exists())
    missing_packages = sorted(pkg for pkg in owned_requested_set if pkg not in resolved_packages)
    status = "ok" if resolved_packages else "no_targets"
    summary = {
        "status": status,
        "module_count": len(all_nodes),
        "edge_count": edge_count,
        "cycle_count": len(cycles),
    }
    top_fan_in = [
        {"module": name, "count": count}
        for name, count in sorted(fan_in.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    top_fan_out = [
        {"module": name, "count": count}
        for name, count in sorted(fan_out.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    isolated_modules = sorted(name for name in all_nodes if fan_in.get(name, 0) == 0 and fan_out.get(name, 0) == 0)
    return {
        "schema_version": 1,
        "generated_utc": generated_ts.isoformat(),
        "repo_root": str(repo_root),
        "owned_packages_requested": sorted(owned_requested_set),
        "owned_packages_resolved": resolved_packages,
        "missing_owned_packages": missing_packages,
        "summary": summary,
        "top_fan_in": top_fan_in,
        "top_fan_out": top_fan_out,
        "cycles": cycles,
        "isolated_modules": isolated_modules,
        "graph": graph_serialized,
    }


def write_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    owned_requested = report.get("owned_packages_requested", [])
    owned_resolved = report.get("owned_packages_resolved", [])
    missing = report.get("missing_owned_packages", [])
    lines = [
        "# Import Graph Report",
        "",
        f"Generated (UTC): {report['generated_utc']}",
        f"Repo Root: {report['repo_root']}",
        "",
        "## Summary",
        "",
        f"- status: {summary['status']}",
        f"- module count: {summary['module_count']}",
        f"- edge count: {summary['edge_count']}",
        f"- cycle count: {summary['cycle_count']}",
        f"- owned packages requested: {', '.join(owned_requested) if owned_requested else '(none)'}",
        f"- owned packages resolved: {', '.join(owned_resolved) if owned_resolved else '(none)'}",
        f"- missing owned packages: {', '.join(missing) if missing else '(none)'}",
    ]
    isolated = report.get("isolated_modules", [])
    lines.append(f"- isolated modules: {', '.join(isolated) if isolated else '(none)'}")
    lines.extend(["", "## Top Fan-In", ""])
    if report.get("top_fan_in"):
        for entry in report["top_fan_in"]:
            lines.append(f"- {entry['module']}: {entry['count']}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Top Fan-Out", ""])
    if report.get("top_fan_out"):
        for entry in report["top_fan_out"]:
            lines.append(f"- {entry['module']}: {entry['count']}")
    else:
        lines.append("- (none)")
    lines.extend(["", "## Cycles", ""])
    if report.get("cycles"):
        for cycle in report["cycles"]:
            lines.append(f"- {' -> '.join(cycle)}")
    else:
        lines.append("- (none)")
    graph_path = report.get("graph_path")
    if graph_path:
        lines.extend(["", f"Graph JSON: `{graph_path}`"])
    return "\n".join(lines) + "\n"


def write_log(report: dict[str, Any]) -> str:
    lines = [
        f"status={report['summary']['status']}",
        f"module_count={report['summary']['module_count']}",
        f"edge_count={report['summary']['edge_count']}",
        f"cycle_count={report['summary']['cycle_count']}",
    ]
    for entry in report.get("top_fan_in", []):
        lines.append(f"top_fan_in[{entry['module']}]={entry['count']}")
    for entry in report.get("top_fan_out", []):
        lines.append(f"top_fan_out[{entry['module']}]={entry['count']}")
    if report.get("cycles"):
        for cycle in report["cycles"]:
            lines.append(f"cycle={'->'.join(cycle)}")
    if report.get("isolated_modules"):
        lines.append("isolated_modules=" + ",".join(report["isolated_modules"]))
    missing = report.get("missing_owned_packages")
    if missing:
        lines.append("missing_owned_packages=" + ",".join(missing))
    return "\n".join(lines) + "\n"


def write_import_graph_artifacts(
    *,
    report: dict[str, Any],
    output_dir: Path,
    timestamp: datetime,
    keep: int,
) -> WriteReportArtifactsResult:
    serialized_graph = report["graph"]

    def _write_graph(run_dir: Path) -> Path:
        path = run_dir / "graph.json"
        path.write_text(
            json.dumps(serialized_graph, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        report["graph_path"] = str(path)
        report["run_directory"] = str(run_dir)
        return path

    return write_report_artifacts(
        stem=RUN_PREFIX,
        timestamp=timestamp,
        output_dir=output_dir,
        keep=keep,
        artifacts=[
            ReportArtifact(
                filename="graph.json",
                pointer="latest_graph.json",
                writer=_write_graph,
            ),
            ReportArtifact(
                filename="report.json",
                kind="json",
                content=lambda: dict(report),
                pointer="latest_report.json",
            ),
            ReportArtifact(
                filename="report.md",
                kind="text",
                content=lambda: write_markdown(report),
                pointer="latest_report.md",
            ),
            ReportArtifact(
                filename="log.txt",
                kind="text",
                content=lambda: write_log(report),
                pointer="latest_report.log",
            ),
        ],
    )


def configure_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric, format="%(levelname)s: %(message)s")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate import graph report")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory to write structured artifacts",
    )
    parser.add_argument(
        "--owned",
        nargs="+",
        help="Owned top-level packages to include (defaults applied if omitted)",
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

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()

    owned = set(args.owned) if args.owned else set(OWNED_DEFAULT)
    owned.add(".repo_studios")

    generated_ts = _parse_timestamp(args.timestamp)
    graph = build_graph(repo_root, owned)
    fan_in, fan_out = fan_metrics(graph)
    cycles = find_cycles(graph)

    report = build_report(
        repo_root=repo_root,
        owned_requested=sorted(owned),
        graph=graph,
        fan_in=fan_in,
        fan_out=fan_out,
        cycles=cycles,
        generated_ts=generated_ts,
    )

    result = write_import_graph_artifacts(
        report=report,
        output_dir=output_dir,
        timestamp=generated_ts,
        keep=args.artifacts_to_keep,
    )
    logging.info("Import graph report written to %s", result.run_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
