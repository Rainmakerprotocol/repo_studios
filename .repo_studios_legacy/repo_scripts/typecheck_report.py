#!/usr/bin/env python3
"""
Typecheck Report Producer

Runs mypy with repo conventions, writes timestamped artifacts under:
  .repo_studios/typecheck/<timestamp>/{report.json,report.md,raw.txt}

Behavior:
- Detect mypy via sys.executable -m mypy
- Default targets from [tool.mypy].files in pyproject.toml
- Overrides via env:
    TYPECHECK_TARGETS="path1 path2 ..."
    TYPECHECK_STRICT=1  (adds --strict)
    HEALTH_TYPECHECK_FAST=1 (kept for parity; can trim targets if desired)
- Always exits 0 (tolerant); encodes failure in JSON/MD status
"""

import argparse
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except Exception:  # pragma: no cover - py311+ expected in this repo
    tomllib = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
OUT_BASE_DEFAULT = ROOT / ".repo_studios" / "typecheck"


def _ts_default() -> str:
    return time.strftime("%Y-%m-%d_%H%M")


def _load_pyproject(repo_root: Path) -> dict:
    py = repo_root / "pyproject.toml"
    if not py.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(py.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_pyproject_targets(repo_root: Path) -> list[str]:
    data = _load_pyproject(repo_root)
    tool = data.get("tool", {}) if isinstance(data, dict) else {}
    mypy = tool.get("mypy", {}) if isinstance(tool, dict) else {}
    files = mypy.get("files", [])
    if isinstance(files, list):
        return [str(x) for x in files if isinstance(x, (str, bytes))]
    return []


def _env_bool(name: str) -> bool:
    v = os.getenv(name)
    return v is not None and v not in ("", "0", "false", "False")


@dataclass
class ErrorSample:
    path: str
    line: int
    code: str
    message: str


@dataclass
class ReportCtx:
    ts: str
    status: str
    mypy_version: str
    total_errors: int
    files_with_issues: int
    checked_paths: list[str]
    invocation: list[str]
    samples: list[ErrorSample]


def _parse_summary(stdout: str) -> tuple[int, int, bool]:
    """Return (total_errors, files_with_issues, success_boolean)."""
    m_ok = re.search(r"^Success: no issues found in (\d+) source files?", stdout, flags=re.M)
    if m_ok:
        return 0, 0, True
    total_errors = 0
    files_with_issues = 0
    m_err = re.search(r"^Found (\d+) errors? in (\d+) files?", stdout, flags=re.M)
    if m_err:
        try:
            total_errors = int(m_err.group(1))
            files_with_issues = int(m_err.group(2))
        except Exception:
            total_errors = 0
            files_with_issues = 0
    return total_errors, files_with_issues, False


def _parse_samples(stdout: str, limit: int = 50) -> list[ErrorSample]:
    err_re = re.compile(
        r"^(?P<path>[^:\n]+):(?P<line>\d+):(?:\d+:)?\s+error: (?P<msg>.*?)(?: \[(?P<code>[^\]]+)\])?$"
    )
    out: list[ErrorSample] = []
    for raw in stdout.splitlines():
        m = err_re.match(raw.strip())
        if not m:
            continue
        try:
            ln = int(m.group("line"))
        except Exception:
            ln = 1
        out.append(
            ErrorSample(
                path=m.group("path"),
                line=ln,
                code=m.group("code") or "",
                message=(m.group("msg") or "").strip(),
            )
        )
        if len(out) >= limit:
            break
    return out


def _write_json(out_dir: Path, payload: dict) -> None:
    import json

    (out_dir / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_md(out_dir: Path, ctx: ReportCtx) -> None:
    lines: list[str] = []
    lines.append(f"# Typecheck Report — {ctx.ts}\n")
    lines.append("")
    lines.append(f"- status: {ctx.status}")
    lines.append(f"- mypy: {ctx.mypy_version}")
    lines.append(f"- total errors: {ctx.total_errors}")
    lines.append(f"- files with issues: {ctx.files_with_issues}")
    if ctx.checked_paths:
        disp = " ".join(ctx.checked_paths[:8]) + (" …" if len(ctx.checked_paths) > 8 else "")
        lines.append(f"- checked paths: {disp}")
    lines.append("")
    lines.append("## Top Issues (up to 20)")
    shown = 0
    for s in ctx.samples:
        lines.append(
            f"- {s.path}:{s.line} — [{s.code}] {s.message}"
            if s.code
            else f"- {s.path}:{s.line} — {s.message}"
        )
        shown += 1
        if shown >= 20:
            break
    if shown == 0:
        lines.append("(none)")
    lines.append("")
    lines.append("## How to Reproduce")
    lines.append("- make typecheck")
    if ctx.invocation:
        # Quote simple args with spaces
        pretty = " ".join(a if " " not in a else f'"{a}"' for a in ctx.invocation)
        lines.append(f"- or run: {pretty}")

    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _discover_targets(repo_root: Path) -> list[str]:
    env_targets = os.getenv("TYPECHECK_TARGETS", "").strip()
    if env_targets:
        return [t for t in env_targets.split() if t]
    return _read_pyproject_targets(repo_root)


def _get_mypy_version(repo_root: Path) -> str:
    try:
        vproc = subprocess.run(
            [sys.executable, "-m", "mypy", "--version"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        return (vproc.stdout or vproc.stderr or "").strip() or "unknown"
    except Exception:
        return "unknown"


def _build_invocation(strict: bool, targets: list[str]) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--show-error-codes",
        "--no-color-output",
        "--hide-error-context",
    ]
    if strict:
        cmd.append("--strict")
    if targets:
        cmd.extend(targets)
    return cmd


def _run_mypy(repo_root: Path, invocation: list[str]) -> str:
    try:
        proc = subprocess.run(
            invocation, cwd=str(repo_root), capture_output=True, text=True, check=False
        )
        out = proc.stdout or ""
        if proc.stderr:
            out += "\n" + proc.stderr
        return out
    except FileNotFoundError as e:
        return f"[EXCEPTION] mypy not found: {e}"
    except Exception as e:
        return f"[EXCEPTION] {e!r}"


def _compute_status(total_errors: int, files_with_issues: int, success_flag: bool) -> str:
    if success_flag and total_errors == 0 and files_with_issues == 0:
        return "OK"
    return "ERROR"


def _emit_stdout_summary(out_dir: Path, ctx: ReportCtx) -> None:
    msg = (
        f"Typecheck: OK — 0 errors (out: {out_dir})"
        if ctx.status == "OK"
        else f"Typecheck: ERROR — {ctx.total_errors} errors in {ctx.files_with_issues} files (out: {out_dir})"
    )
    logging.info(msg)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Produce mypy typecheck artifacts under .repo_studios/typecheck/<ts>"
    )
    ap.add_argument("--repo-root", default=str(ROOT))
    ap.add_argument("--output-base", default=str(OUT_BASE_DEFAULT))
    ap.add_argument("--timestamp", default=_ts_default())
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    out_base = Path(args.output_base).resolve()
    ts = args.timestamp
    out_dir = out_base / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = _discover_targets(repo_root)
    strict = _env_bool("TYPECHECK_STRICT")
    fast = _env_bool("HEALTH_TYPECHECK_FAST")

    # Apply curated fast-mode filtering unless explicit override is set
    override_present = bool(os.getenv("TYPECHECK_TARGETS", "").strip())
    if fast and not override_present:
        allow_prefixes = [
            "api",
            "agents/core",
            "agents/interface/chainlit",
        ]

        def _is_allowed(path: str) -> bool:
            p = path.strip().strip("/")
            return any(p == pre or p.startswith(pre + "/") for pre in allow_prefixes)

        curated = [t for t in targets if _is_allowed(t)] if targets else []
        # Fallback to default curated set if pyproject didn't specify or all were filtered
        if not curated:
            curated = [p for p in allow_prefixes if (repo_root / p).exists()]
        targets = curated

    mypy_version = _get_mypy_version(repo_root)
    invocation = _build_invocation(strict, targets)
    stdout_combined = _run_mypy(repo_root, invocation)

    # Persist raw output
    (out_dir / "raw.txt").write_text(stdout_combined, encoding="utf-8")

    total_errors, files_with_issues, success_flag = _parse_summary(stdout_combined)
    samples = _parse_samples(stdout_combined, limit=50)
    if not success_flag and total_errors == 0:
        total_errors = len(samples)
        files_with_issues = len({s.path for s in samples})

    status = _compute_status(total_errors, files_with_issues, success_flag)

    payload = {
        "status": status,
        "mypy_version": mypy_version,
        "checked_paths": targets,
        "total_errors": int(total_errors),
        "files_with_issues": int(files_with_issues),
        "error_samples": [
            {"path": s.path, "line": s.line, "code": s.code, "message": s.message}
            for s in samples[:50]
        ],
        "invocation": invocation,
        "timestamp": ts,
    }
    _write_json(out_dir, payload)

    ctx = ReportCtx(
        ts=ts,
        status=status,
        mypy_version=mypy_version,
        total_errors=total_errors,
        files_with_issues=files_with_issues,
        checked_paths=targets,
        invocation=invocation,
        samples=samples,
    )
    _write_md(out_dir, ctx)
    _emit_stdout_summary(out_dir, ctx)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
