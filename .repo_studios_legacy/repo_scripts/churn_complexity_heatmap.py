#!/usr/bin/env python3
"""
Churn × Complexity Risk Heatmap

Computes a simple per-file risk score by combining:
- Code churn: number of commits touching the file in the last N commits (window)
- Static complexity proxy: count of branches in AST (if/for/while/try/with + boolean ops)
- Optional failure density: number of failed tests referencing the file (from latest JUnit)

Outputs (under --output-base/<ts>/):
- heatmap.json
- heatmap.md
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    out, _ = proc.communicate()
    return proc.returncode, out


def _ensure_out(base: Path) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_dir = base / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _py_files(root: Path) -> list[Path]:
    ignores = {".venv", ".git", "__pycache__", "node_modules"}
    out: list[Path] = []
    for p in root.rglob("*.py"):
        if any(seg in ignores for seg in p.parts):
            continue
        out.append(p)
    return out


def _commit_churn(root: Path, window: int) -> Counter[str]:
    _, out = _run(
        ["git", "--no-pager", "log", f"-n{window}", "--name-only", "--pretty=format:"], cwd=root
    )
    files = [
        line.strip() for line in out.splitlines() if line.strip() and line.strip().endswith(".py")
    ]
    return Counter(files)


def _complexity_score(path: Path) -> int:
    import ast

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return 0
    count = 0
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.BoolOp,
        ast.IfExp,
        ast.Match,
    )
    for node in ast.walk(tree):
        if isinstance(node, branch_nodes):
            count += 1
    return count


def _junit_failures(junit: Path | None) -> Counter[str]:
    from defusedxml import ElementTree

    c: Counter[str] = Counter()
    if not junit:
        return c
    try:
        root = ElementTree.parse(junit).getroot()
    except Exception:
        return c
    for tc in root.iterfind(".//testcase"):
        if tc.find("failure") is not None or tc.find("error") is not None:
            file_attr = tc.get("file")
            classname = tc.get("classname")
            left = file_attr or (classname.replace(".", "/") + ".py" if classname else None)
            if left:
                c[left] += 1
    return c


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate churn × complexity heatmap")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--window", type=int, default=500, help="git log window (number of commits)")
    ap.add_argument("--output-base", default=".repo_studios/churn_complexity")
    ap.add_argument("--logs-dir", default=".repo_studios/pytest_logs")
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    out_base = Path(args.output_base)
    if not out_base.is_absolute():
        out_base = (root / out_base).resolve()
    out_dir = _ensure_out(out_base)

    # Latest JUnit for failure density
    logs_dir = root / args.logs_dir
    junit_candidates = sorted((p for p in logs_dir.glob("junit_*.xml")), key=lambda p: p.name)
    junit = junit_candidates[-1] if junit_candidates else None

    churn = _commit_churn(root, args.window)
    failures = _junit_failures(junit)

    results: list[dict[str, Any]] = []
    for py in _py_files(root):
        rel = str(py.relative_to(root))
        comp = _complexity_score(py)
        ch = churn[rel]
        fail = failures[rel]
        # Simple normalized score: log1p(churn)*log1p(complexity)*(1+fail)
        score = math.log1p(ch) * math.log1p(comp) * (1 + fail)
        results.append(
            {
                "file": rel,
                "churn": ch,
                "complexity": comp,
                "failures": fail,
                "score": round(score, 4),
            }
        )

    # Sort by score desc
    results.sort(key=lambda x: x["score"], reverse=True)

    # JSON
    (out_dir / "heatmap.json").write_text(
        json.dumps(
            {"generated_at": datetime.now().isoformat(), "window": args.window, "items": results},
            indent=2,
        ),
        encoding="utf-8",
    )

    # Markdown top 25
    md: list[str] = []
    md.append("# Churn × Complexity Heatmap\n")
    md.append(f"Generated: {datetime.now().isoformat()}\n")
    md.append(f"Window: last {args.window} commits\n")
    md.append("\n| File | Churn | Complexity | Failures | Score |\n|---|---:|---:|---:|---:|\n")
    for item in results[:25]:
        md.append(
            f"| {item['file']} | {item['churn']} | {item['complexity']} | {item['failures']} | {item['score']:.4f} |\n"
        )
    (out_dir / "heatmap.md").write_text("".join(md), encoding="utf-8")

    logging.info("Heatmap written to %s", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
