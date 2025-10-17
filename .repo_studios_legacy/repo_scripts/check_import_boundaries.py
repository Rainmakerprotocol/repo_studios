#!/usr/bin/env python3
"""
Import Boundaries & Cycle Checker

Purpose
  - Enforce directional boundaries between layers
  - Detect cycles at a coarse (top-level) package granularity
  - Support a transitional allowlist for edges and file-level exceptions

Assumptions
  - The import graph JSON exists at .repo_studios/import_graph/<ts>/graph.json
    as written by import_graph_report.py. Its shape is a dict: {module: [imports...]}
  - We enforce these defaults (can be extended later):
      • Forbid agents → api imports (static cross-layer) in source files
      • Forbid agents/core → agents/interface imports (inversion within agents)
      • Detect top-level cycles, notably api ⇄ agents
  - Tests are exempt; scripts are currently exempt; allowlist can waive violations.

Exit code
  - 0 on success (no violations beyond allowlist)
  - 1 on violations not covered by allowlist

Usage
  python .repo_studios/check_import_boundaries.py [--repo-root .]

Env
  STRICT=1 can be used by CI to treat warnings as errors in the future.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GRAPH_DIR = HERE / "import_graph"
ALLOWLIST_PATH = HERE / "import_rules_allowlist.json"


@dataclass
class Violation:
    kind: str  # "cycle" | "edge" | "static-import"
    detail: str
    file: str | None = None


def _latest_graph_json() -> Path | None:
    if not GRAPH_DIR.exists():
        return None
    # Pick the lexicographically latest timestamp dir
    dirs = [p for p in GRAPH_DIR.iterdir() if p.is_dir()]
    if not dirs:
        return None
    latest = sorted(dirs)[-1]
    cand = latest / "graph.json"
    return cand if cand.exists() else None


def _load_graph(path: Path) -> dict[str, list[str]]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _load_allowlist(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"edges": [], "files": []}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {"edges": [], "files": []}


def _is_test_file(p: Path) -> bool:
    r = str(p)
    return "/tests/" in r or r.endswith("/tests")


def _scan_static_imports(repo_root: Path) -> list[Violation]:
    """Scan for disallowed static imports by path and content patterns.

    Rules:
    - agents/** importing api/* (forbidden): look for 'from api' or 'import api' tokens.
    - agents/core/** importing agents/interface/** (forbidden):
        'from agents.interface' or 'import agents.interface'
    - api/** importing agents/interface/** (discouraged):
        'from agents.interface' or 'import agents.interface' (tests excluded).
    Tests are exempt. Non-.py files ignored. Vendor or external dirs can be ignored via a simple skip.
    """
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
        # prune skip dirs
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fp = Path(dirpath) / fn
            if _is_test_file(fp):
                continue
            rel = fp.relative_to(repo_root).as_posix()
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            # Rule: agents → api forbidden
            if rel.startswith("agents/"):
                if "\nfrom api " in text or "\nimport api" in text:
                    violations.append(
                        Violation(
                            kind="static-import",
                            detail="agents -> api",
                            file=rel,
                        )
                    )
            # Rule: agents/core → agents/interface forbidden
            if rel.startswith("agents/core/"):
                if "\nfrom agents.interface" in text or "\nimport agents.interface" in text:
                    violations.append(
                        Violation(
                            kind="static-import",
                            detail="agents/core -> agents/interface",
                            file=rel,
                        )
                    )
            # Rule: api → agents/interface discouraged (enforceable when STRICT=1 later)
            if rel.startswith("api/"):
                if "\nfrom agents.interface" in text or "\nimport agents.interface" in text:
                    violations.append(
                        Violation(
                            kind="static-import",
                            detail="api -> agents/interface",
                            file=rel,
                        )
                    )
    return violations


def _detect_cycles(
    graph: dict[str, list[str]], *, agents_to_api_forbidden_found: bool
) -> list[Violation]:
    # Coarse cycles on top-level namespaces present in graph keys
    v: list[Violation] = []
    # Specific: api ⇄ agents
    if "api" in graph and "agents" in graph:
        api_edges = set(graph.get("api", []))
        ag_edges = set(graph.get("agents", []))
        # Only consider a cycle a violation when the disallowed direction
        # (agents -> api) is present in source files; api -> agents by itself
        # is permitted by layering and should not be flagged.
        if agents_to_api_forbidden_found and "agents" in api_edges and "api" in ag_edges:
            v.append(Violation(kind="cycle", detail="api <-> agents"))
    return v


def _edge_violation_edges(
    graph: dict[str, list[str]], *, agents_to_api_forbidden_found: bool
) -> list[Violation]:
    # Forbid agents -> api edge (top-level)
    v: list[Violation] = []
    if agents_to_api_forbidden_found and "agents" in graph:
        if "api" in set(graph.get("agents", [])):
            v.append(Violation(kind="edge", detail="agents -> api"))
    # Intra-agents inversion is best caught by static file scan; keep here for parity later
    return v


def _apply_allowlist(violations: list[Violation], allow: dict[str, Any]) -> list[Violation]:
    allowed_edges = {(e.get("from"), e.get("to")) for e in allow.get("edges", [])}
    allowed_files = set(allow.get("files", []))
    out: list[Violation] = []
    for v in violations:
        if v.kind in {"edge", "cycle"}:
            # cycles are allowed only if both directed edges are allowlisted
            if v.kind == "edge":
                parts = v.detail.split("->")
                if len(parts) == 2:
                    src = parts[0].strip()
                    dst = parts[1].strip()
                    if (src, dst) in allowed_edges:
                        continue
            if v.kind == "cycle":
                if ("api", "agents") in allowed_edges and ("agents", "api") in allowed_edges:
                    continue
        if v.kind == "static-import" and v.file:
            if v.file in allowed_files:
                continue
        out.append(v)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=str(ROOT))
    args = ap.parse_args()
    repo_root = Path(args.repo_root).resolve()

    graph_path = _latest_graph_json()
    graph = _load_graph(graph_path) if graph_path else {}
    allow = _load_allowlist(ALLOWLIST_PATH)

    # First run static scan (source only, tests excluded)
    static_violations = _scan_static_imports(repo_root)
    agents_to_api_forbidden_found = any(
        v.kind == "static-import" and v.detail == "agents -> api" for v in static_violations
    )

    violations: list[Violation] = []
    violations += _detect_cycles(graph, agents_to_api_forbidden_found=agents_to_api_forbidden_found)
    violations += _edge_violation_edges(
        graph, agents_to_api_forbidden_found=agents_to_api_forbidden_found
    )
    violations += static_violations

    remaining = _apply_allowlist(violations, allow)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if not remaining:
        logging.info("[check-imports] OK — no violations (beyond allowlist)")
        return 0

    logging.error("[check-imports] Violations detected:")
    for v in remaining:
        loc = f" ({v.file})" if v.file else ""
        logging.error(f"  - {v.kind}: {v.detail}{loc}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
