#!/usr/bin/env python3
"""Structured import boundary checker with artifacts and pruning."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

DEFAULT_RELATIVE_GRAPH_DIR = Path(".repo_studios/reports/producer_reports/import_graph_reports")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/import_boundary_reports")
DEFAULT_ALLOWLIST = Path(".repo_studios/scripts/producers/import_rules_allowlist.json")
RUN_PREFIX = "import_boundary_check"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback when running standalone
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
    )


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    allowlist_path: Path
    graph_dir: Path | None = None


@dataclass(frozen=True)
class Options:
    artifacts_to_keep: int
    graph_path: Path | None = None
    strict: bool = False


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "output_dir": PathSpec(
            field="output_dir",
            default=DEFAULT_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=False,
        ),
        "allowlist_path": PathSpec(
            field="allowlist_path",
            default=DEFAULT_ALLOWLIST,
            within_repo=False,
        ),
    },
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
    },
)


@dataclass
class Violation:
    kind: str  # "cycle" | "edge" | "static-import"
    detail: str
    file: str | None = None


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="validate_import_boundaries",
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root (defaults to project root)")
    parser.add_argument(
        "--graph-path",
        help="Override path to import graph JSON; defaults to latest run under import_graph_reports",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for structured artifacts (defaults to producer_reports/import_boundary_reports)",
    )
    parser.add_argument(
        "--allowlist-path",
        help="Path to JSON allowlist file (defaults to import_rules_allowlist.json next to the script)",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical run directories to retain",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Reserved for future enforcement of discouraged edges",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    paths = build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))
    repo_root = paths.repo_root
    graph_dir = (repo_root / DEFAULT_RELATIVE_GRAPH_DIR).resolve()
    if getattr(args, "graph_path", None):
        graph_candidate = Path(args.graph_path)
        if not graph_candidate.is_absolute():
            graph_candidate = (repo_root / graph_candidate).resolve()
        else:
            graph_candidate = graph_candidate.resolve()
        graph_dir = graph_candidate.parent
    return replace(paths, graph_dir=graph_dir)


def build_options(args: argparse.Namespace, paths: Paths) -> Options:
    graph_path = None
    if args.graph_path:
        graph_path = Path(args.graph_path)
        if not graph_path.is_absolute():
            graph_path = (paths.repo_root / graph_path).resolve()
    strict = bool(args.strict or os.getenv("STRICT") in {"1", "true", "TRUE"})
    base_options = build_standard_options(args, OPTIONS_CONFIG)
    return replace(base_options, graph_path=graph_path, strict=strict)


def _latest_graph_json(graph_dir: Path) -> Path | None:
    if not graph_dir.exists():
        return None
    dirs = [p for p in graph_dir.iterdir() if p.is_dir()]
    if not dirs:
        return None
    latest = sorted(dirs)[-1]
    candidate = latest / "graph.json"
    return candidate if candidate.exists() else None


def _load_graph(path: Path | None) -> dict[str, list[str]]:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_allowlist(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"edges": [], "files": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"edges": [], "files": []}


def _is_test_file(path: Path) -> bool:
    text = path.as_posix()
    return "/tests/" in text or text.endswith("/tests")


def _scan_static_imports(repo_root: Path) -> list[Violation]:
    violations: list[Violation] = []
    skip_dirs = {
        ".venv",
        "venv",
        "node_modules",
        "external",
        "libraries",
        "voice_profile",
        "zzz_agent_repos",
        "z_Files to upload",
        "z_FUTURE_IMPIMENTATIONS",
        "__pycache__",
        ".repo_studios",
        "backups",
    }
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            file_path = Path(dirpath) / filename
            if _is_test_file(file_path):
                continue
            rel_path = file_path.relative_to(repo_root).as_posix()
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if rel_path.startswith("agents/"):
                if "\nfrom api " in text or "\nimport api" in text:
                    violations.append(Violation(kind="static-import", detail="agents -> api", file=rel_path))
            if rel_path.startswith("agents/core/"):
                if "\nfrom agents.interface" in text or "\nimport agents.interface" in text:
                    violations.append(
                        Violation(
                            kind="static-import",
                            detail="agents/core -> agents/interface",
                            file=rel_path,
                        )
                    )
            if rel_path.startswith("api/"):
                if "\nfrom agents.interface" in text or "\nimport agents.interface" in text:
                    violations.append(
                        Violation(
                            kind="static-import",
                            detail="api -> agents/interface",
                            file=rel_path,
                        )
                    )
    return violations


def _detect_cycles(graph: dict[str, list[str]], *, agents_to_api_forbidden_found: bool) -> list[Violation]:
    violations: list[Violation] = []
    if "api" in graph and "agents" in graph:
        api_edges = set(graph.get("api", []))
        agent_edges = set(graph.get("agents", []))
        if agents_to_api_forbidden_found and "agents" in api_edges and "api" in agent_edges:
            violations.append(Violation(kind="cycle", detail="api <-> agents"))
    return violations


def _edge_violations(graph: dict[str, list[str]], *, agents_to_api_forbidden_found: bool) -> list[Violation]:
    violations: list[Violation] = []
    if agents_to_api_forbidden_found and "agents" in graph:
        if "api" in set(graph.get("agents", [])):
            violations.append(Violation(kind="edge", detail="agents -> api"))
    return violations


def _apply_allowlist(violations: list[Violation], allowlist: dict[str, Any]) -> list[Violation]:
    allowed_edges = {(edge.get("from"), edge.get("to")) for edge in allowlist.get("edges", [])}
    allowed_files = set(allowlist.get("files", []))
    remaining: list[Violation] = []
    for violation in violations:
        if violation.kind == "edge":
            parts = [part.strip() for part in violation.detail.split("->")]
            if len(parts) == 2 and (parts[0], parts[1]) in allowed_edges:
                continue
        if violation.kind == "cycle":
            if ("api", "agents") in allowed_edges and ("agents", "api") in allowed_edges:
                continue
        if violation.kind == "static-import" and violation.file in allowed_files:
            continue
        remaining.append(violation)
    return remaining


def _summarize(violations: list[Violation]) -> dict[str, Any]:
    counts = Counter(v.kind for v in violations)
    return {
        "violation_count": len(violations),
        "violations_by_kind": dict(sorted(counts.items())),
    }


def render_markdown_report(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    violations = payload.get("violations", [])
    lines = [
        "# Import Boundary Report\n\n",
        f"- Status: `{payload.get('status', 'unknown')}`\n",
        f"- Timestamp: `{payload.get('timestamp', '')}`\n",
        f"- Repo Root: `{payload.get('repo_root', '')}`\n",
        f"- Graph Path: `{payload.get('graph_path') or 'auto-detected'}`\n",
        f"- Allowlist: `{payload.get('allowlist_path', '')}`\n",
        f"- Violations: {summary.get('violation_count', 0)}\n",
    ]

    counts = summary.get("violations_by_kind", {})
    if counts:
        lines.append("\n## Violations by Kind\n\n")
        lines.append("| Kind | Count |\n| --- | ---: |\n")
        for kind, count in sorted(counts.items()):
            lines.append(f"| {kind} | {count} |\n")

    if violations:
        lines.append("\n## Violation Details\n\n")
        lines.append("| Kind | Detail | File |\n| --- | --- | --- |\n")
        for violation in violations:
            file_display = violation.get("file") or "—"
            lines.append(f"| {violation.get('kind')} | {violation.get('detail')} | {file_display} |\n")

    lines.append(
        "\n## Next Steps\n\n"
        "- [ ] Address unallowlisted edges or update the allowlist with justification.\n"
        "- [ ] Re-run `validate_import_boundaries.py` after remediation to confirm clean state.\n"
        "- [ ] Capture decisions in the architecture log if allowlist entries are required long-term.\n"
    )
    return "".join(lines)


def render_log(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    counts = summary.get("violations_by_kind", {})
    entries = [
        f"status={payload.get('status', 'unknown')}",
        f"timestamp={payload.get('timestamp', '')}",
        f"violations={summary.get('violation_count', 0)}",
    ]
    for kind, count in sorted(counts.items()):
        entries.append(f"violations_{kind}={count}")
    if payload.get("graph_path"):
        entries.append(f"graph_path={payload['graph_path']}")
    entries.append(f"allowlist_path={payload.get('allowlist_path', '')}")
    return "\n".join(entries) + "\n"


def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:
    latest_dir = output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "report.json": latest_dir / "latest_report.json",
        "report.md": latest_dir / "latest_report.md",
        "log.txt": latest_dir / "latest_log.txt",
        "violations.json": latest_dir / "latest_violations.json",
    }
    for source, target in mapping.items():
        src_path = run_dir / source
        if src_path.exists():
            target.write_bytes(src_path.read_bytes())


def write_artifacts(
    *,
    run_dir: Path,
    output_dir: Path,
    payload: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown_report(payload), encoding="utf-8")
    (run_dir / "log.txt").write_text(render_log(payload), encoding="utf-8")
    (run_dir / "violations.json").write_text(
        json.dumps(payload.get("violations", []), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_latest_artifacts(run_dir, output_dir)


def prune_history(base_dir: Path, keep: int) -> None:
    if not base_dir.exists():
        return
    run_dirs = sorted(
        [p for p in base_dir.iterdir() if p.is_dir() and p.name.startswith(RUN_PREFIX)],
        key=lambda p: p.name,
    )
    excess = len(run_dirs) - keep
    if excess <= 0:
        return
    for directory in run_dirs[:excess]:
        for child in sorted(directory.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if child.is_file():
                child.unlink(missing_ok=True)
            elif child.is_dir():
                child.rmdir()
        directory.rmdir()


def compose_payload(
    *,
    paths: Paths,
    options: Options,
    graph_path: Path | None,
    violations: list[Violation],
    timestamp: dt.datetime,
) -> dict[str, Any]:
    run_id = f"{RUN_PREFIX}-{timestamp.strftime('%Y%m%d_%H%M%S')}"
    summary = _summarize(violations)
    status = "ok" if summary["violation_count"] == 0 else "violations"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "timestamp": timestamp.isoformat(),
        "run_id": run_id,
        "repo_root": str(paths.repo_root),
        "output_dir": str(paths.output_dir),
        "graph_path": str(graph_path) if graph_path else None,
        "allowlist_path": str(paths.allowlist_path),
        "options": {
            "strict": options.strict,
            "artifacts_to_keep": options.artifacts_to_keep,
        },
        "summary": summary,
        "violations": [{"kind": v.kind, "detail": v.detail, "file": v.file} for v in violations],
    }
    return payload


def run(argv: list[str] | None = None) -> dict[str, Any]:
    args = parse_args(argv)
    configure_logging(args.log_level)
    paths = build_paths(args)
    options = build_options(args, paths)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Repo root: %s", paths.repo_root)
    logging.info("Output directory: %s", paths.output_dir)

    graph_path = options.graph_path or _latest_graph_json(paths.graph_dir)
    if graph_path:
        logging.info("Graph path: %s", graph_path)
    else:
        logging.warning("No import graph found; cycle detection limited to static scan results")

    graph = _load_graph(graph_path)
    allowlist = _load_allowlist(paths.allowlist_path)
    static_violations = _scan_static_imports(paths.repo_root)
    agents_to_api_forbidden_found = any(
        v.kind == "static-import" and v.detail == "agents -> api" for v in static_violations
    )
    violations = []
    violations.extend(_detect_cycles(graph, agents_to_api_forbidden_found=agents_to_api_forbidden_found))
    violations.extend(_edge_violations(graph, agents_to_api_forbidden_found=agents_to_api_forbidden_found))
    violations.extend(static_violations)
    remaining = _apply_allowlist(violations, allowlist)

    timestamp = dt.datetime.now(dt.timezone.utc)
    payload = compose_payload(
        paths=paths,
        options=options,
        graph_path=graph_path,
        violations=remaining,
        timestamp=timestamp,
    )

    run_dir = paths.output_dir / payload["run_id"]
    write_artifacts(run_dir=run_dir, output_dir=paths.output_dir, payload=payload)
    prune_history(paths.output_dir, options.artifacts_to_keep)

    if payload["summary"]["violation_count"] == 0:
        logging.info("[check-imports] OK — no violations (beyond allowlist)")
    else:
        logging.error("[check-imports] Violations detected (%s)", payload["summary"]["violation_count"])
        for violation in payload["violations"]:
            loc = f" ({violation['file']})" if violation.get("file") else ""
            logging.error("  - %s: %s%s", violation["kind"], violation["detail"], loc)

    return payload


def main(argv: list[str] | None = None) -> int:
    payload = run(argv)
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
