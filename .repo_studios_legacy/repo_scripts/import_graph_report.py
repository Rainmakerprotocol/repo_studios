#!/usr/bin/env python3
"""
Import Graph Report — Builds a module import graph and surfaces cycles and hotspots.

Scans Python files under owned packages, parses imports, and emits:
 - .repo_studios/import_graph/<ts>/graph.json — adjacency list
 - .repo_studios/import_graph/<ts>/report.md — cycles, fan-in/fan-out top-N

No network; static analysis from source files only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

OWNED_DEFAULT = {
    "agents",
    "api",
    "client_helpers",
    "jarvis2",
    "metrics_storage",
    "mrp",
    "scripts",
    "src",
    "tests",
}


def iter_py_files(root: Path, owned: set[str]) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in owned:
            yield p


IMPORT_RE = re.compile(r"^(?:from\s+([\w\.]+)\s+import\s+|import\s+([\w\.]+))")


def parse_imports(path: Path) -> set[str]:
    out: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = IMPORT_RE.match(line.strip())
            if not m:
                continue
            mod = m.group(1) or m.group(2) or ""
            base = mod.split(".")[0]
            if base:
                out.add(base)
    except Exception:
        pass
    return out


def build_graph(root: Path, owned: set[str]) -> dict[str, set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for f in iter_py_files(root, owned):
        try:
            rel = f.relative_to(root)
            src = rel.parts[0]
        except Exception:
            continue
        for dep in parse_imports(f):
            if dep in owned:
                graph[src].add(dep)
    return graph


def fan_metrics(graph: dict[str, set[str]]):
    fan_out = {n: len(neigh) for n, neigh in graph.items()}
    fan_in = defaultdict(int)
    for _n, neigh in graph.items():
        for d in neigh:
            fan_in[d] += 1
    return fan_in, fan_out


def find_cycles(graph: dict[str, set[str]]):
    cycles: list[list[str]] = []
    nodes = list(graph.keys())
    for start in nodes:
        stack = [(start, [start])]
        seen = set()
        while stack:
            cur, path = stack.pop()
            for nxt in graph.get(cur, ()):
                if nxt == start and len(path) > 1:
                    cycles.append(path + [start])
                elif (cur, nxt) not in seen and nxt in graph:
                    seen.add((cur, nxt))
                    if nxt not in path:  # avoid trivial backtracking
                        stack.append((nxt, path + [nxt]))
    # Normalize cycles by rotation to start with lexicographically smallest node
    norm: list[list[str]] = []
    seen_sig = set()
    for c in cycles:
        body = c[:-1]
        k = min(range(len(body)), key=lambda i: body[i])
        rot = body[k:] + body[:k]
        sig = tuple(rot)
        if sig not in seen_sig:
            seen_sig.add(sig)
            norm.append(rot + [rot[0]])
    return norm


def main() -> int:
    ap = argparse.ArgumentParser(description="Import graph cycles and hotspot report")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--owned", nargs="*", default=sorted(OWNED_DEFAULT))
    ap.add_argument("--output-base", default=".repo_studios/import_graph")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    owned = set(args.owned)
    out_base = Path(args.output_base)
    if not out_base.is_absolute():
        out_base = (root / out_base).resolve()
    out = out_base / dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    out.mkdir(parents=True, exist_ok=True)

    graph = build_graph(root, owned)
    fan_in, fan_out = fan_metrics(graph)
    cycles = find_cycles(graph)

    # Write graph
    (out / "graph.json").write_text(
        json.dumps({k: sorted(v) for k, v in graph.items()}, indent=2), encoding="utf-8"
    )

    # Write report
    def top_n(d: dict[str, int], n: int = 10):
        return sorted(d.items(), key=lambda x: (-x[1], x[0]))[:n]

    lines: list[str] = []
    lines.append("# Import Graph Report\n")
    lines.append(f"Date: {dt.datetime.now().isoformat()}\n")
    lines.append("\n## Hotspots\n")
    lines.append("\n### Top fan-in (modules most depended on)\n")
    for name, cnt in top_n(fan_in):
        lines.append(f"- {name}: {cnt}")
    lines.append("\n### Top fan-out (modules with many dependencies)\n")
    for name, cnt in top_n(fan_out):
        lines.append(f"- {name}: {cnt}")
    lines.append("\n## Cycles\n")
    if not cycles:
        lines.append("- None detected")
    else:
        for cyc in cycles:
            lines.append("- " + " -> ".join(cyc))
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
