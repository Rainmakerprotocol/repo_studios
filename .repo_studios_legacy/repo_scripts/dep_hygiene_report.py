#!/usr/bin/env python3
"""
Dependency Hygiene Report — Offline checks for pinning, duplicates, and VCS/local refs.

Outputs timestamped artifacts under .repo_studios/dep_health/<ts>/:
 - report.json — machine-readable issues
 - report.md   — human summary with counts and tables

No network calls; purely static analysis of requirements*.txt and pyproject.toml.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore


REQ_PATTERNS = (
    "requirements.txt",
    "requirements-dev.txt",
    "requirements/*.txt",
)


@dataclass
class Issue:
    kind: str
    file: str
    line: int
    spec: str


def _iter_req_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pat in REQ_PATTERNS:
        files.extend(root.glob(pat))
    return [p for p in files if p.exists()]


def _parse_requirements_file(path: Path) -> tuple[list[Issue], dict[str, list[str]]]:
    issues: list[Issue] = []
    seen: dict[str, list[str]] = {}
    for i, raw in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
    ):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement")):
            continue
        if line.startswith(("-e ", "--editable")):
            issues.append(Issue("editable_install", str(path), i, raw))
            continue
        if re.match(r"^(git\+|hg\+|svn\+|bzr\+)", line):
            issues.append(Issue("vcs_ref", str(path), i, raw))
        if re.match(r"^\./|^\.\.|^/", line):
            issues.append(Issue("local_path", str(path), i, raw))

        # Split on version specifiers
        name = re.split(r"[<>=!~]", line)[0].strip()
        if name:
            seen.setdefault(name.lower(), []).append(line)
        # Pinning check: prefer '==' exact pins
        if "==" not in line:
            issues.append(Issue("unpinned", str(path), i, raw))
    # Duplicates
    for pkg, specs in seen.items():
        if len(specs) > 1:
            issues.append(Issue("duplicate", str(path), 0, f"{pkg}: {specs}"))
    return issues, seen


def _parse_pyproject(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    if tomllib is None:
        return issues
    data = tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    # PEP 621 dependencies
    deps = data.get("project", {}).get("dependencies", []) or data.get("tool", {}).get(
        "poetry", {}
    ).get("dependencies", {})
    if isinstance(deps, dict):
        items = [(k, str(v)) for k, v in deps.items() if k != "python"]
    else:
        items = [(d, d) for d in deps]
    for raw_name, spec in items:
        # Consider spec pinned if contains '==' or is an exact version string
        pinned = "==" in spec or re.fullmatch(r"\d+\.\d+(\.\d+)?", spec) is not None
        if not pinned:
            issues.append(Issue("unpinned", str(path), 0, f"{raw_name} {spec}"))
        if re.match(r"^(git\+|hg\+|svn\+|bzr\+)", spec):
            issues.append(Issue("vcs_ref", str(path), 0, f"{raw_name} {spec}"))
    return issues


def _write_outputs(out_dir: Path, issues: list[Issue]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # JSON
    (out_dir / "report.json").write_text(
        json.dumps([asdict(i) for i in issues], indent=2), encoding="utf-8"
    )
    # Markdown
    counts: dict[str, int] = {}
    for i in issues:
        counts[i.kind] = counts.get(i.kind, 0) + 1
    lines: list[str] = []
    lines.append("# Dependency Hygiene Report\n")
    lines.append(f"Date: {dt.datetime.now().isoformat()}\n")
    lines.append("\n## Summary\n")
    if issues:
        for k, v in sorted(counts.items()):
            lines.append(f"- {k}: {v}")
    else:
        lines.append("- No issues detected.")
    lines.append("\n## Findings\n")
    for i in issues:
        loc = f"{i.file}:{i.line}" if i.line else i.file
        lines.append(f"- [{i.kind}] {loc} — {i.spec}")
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dependency hygiene report (offline)")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-base", default=".repo_studios/dep_health")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    out_base = (Path(args.output_base) if Path(args.output_base).is_absolute() else (root / args.output_base)).resolve()
    out = out_base / dt.datetime.now().strftime("%Y-%m-%d_%H%M")

    all_issues: list[Issue] = []
    # requirements files
    for rf in _iter_req_files(root):
        issues, _ = _parse_requirements_file(rf)
        all_issues.extend(issues)
    # pyproject
    pyproj = root / "pyproject.toml"
    if pyproj.exists():
        all_issues.extend(_parse_pyproject(pyproj))

    _write_outputs(out, all_issues)
    logging.info("Dependency hygiene report written to: %s", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
