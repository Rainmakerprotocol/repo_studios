#!/usr/bin/env python3
"""Lizard Complexity Report Generator.

Runs `python -m lizard` with repo conventions and emits timestamped artifacts under
`.repo_studios/lizard/<timestamp>/`:

- `report.json`: machine-readable summary (status, counts, offending functions)
- `report.md`: human summary with top offenders and reproduction hints
- `raw.json`: full JSON output from Lizard when available
- `raw.txt`: stdout/stderr when invocation fails

The script is tolerant: it always exits 0, encoding failures in the JSON summary.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import time
import traceback
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = ("agents", "api", "scripts")
OUT_BASE_DEFAULT = ROOT / ".repo_studios" / "lizard"


def _ts_default() -> str:
    return time.strftime("%Y-%m-%d_%H%M")


def _ensure_out_dir(base: Path, ts: str) -> Path:
    out_dir = base / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


@dataclass
class Offender:
    path: str
    name: str
    complexity: int
    length: int


def _env_bool(name: str) -> bool:
    value = os.getenv(name)
    return value is not None and value not in ("", "0", "false", "False")


def _build_command(max_ccn: int, max_length: int, targets: Iterable[str], extra: Iterable[str]) -> list[str]:
    cmd: list[str] = [sys.executable, "-m", "lizard", "-C", str(max_ccn), "-L", str(max_length)]
    cmd.extend(extra)
    cmd.extend(targets)
    return cmd


def _select_targets(repo_root: Path, provided: Iterable[str]) -> list[str]:
    targets = [t for t in provided if t]
    if targets:
        return [str((repo_root / t).resolve()) if not Path(t).is_absolute() else str(Path(t)) for t in targets]
    resolved: list[str] = []
    for rel in DEFAULT_TARGETS:
        path = repo_root / rel
        if path.exists():
            resolved.append(str(path.resolve()))
    return resolved


def _build_offender(file_path: str, func: dict, *, max_ccn: int, max_length: int) -> Offender | None:
    ccn = _as_int(func.get("cyclomatic_complexity", 0))
    length = _as_int(func.get("length", 0))
    if ccn <= max_ccn and length <= max_length:
        return None

    name = func.get("name") or func.get("long_name") or "<unnamed>"
    return Offender(
        path=file_path,
        name=str(name),
        complexity=ccn,
        length=length,
    )


def _extract_file_path(entry: dict) -> str | None:
    for key in ("filename", "file_name", "file"):
        value = entry.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _parse_offenders(payload: list[dict], *, max_ccn: int, max_length: int) -> list[Offender]:
    offenders: list[Offender] = []
    for entry in payload:
        file_path = _extract_file_path(entry)
        if not file_path:
            continue
        for func in entry.get("function_list", []):
            offender = _build_offender(file_path, func, max_ccn=max_ccn, max_length=max_length)
            if offender:
                offenders.append(offender)
    return offenders


def _write_json(out_dir: Path, payload: dict) -> None:
    (out_dir / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_md(out_dir: Path, payload: dict, offenders: list[Offender], *, max_rows: int = 25) -> None:
    lines: list[str] = []
    lines.append(f"# Lizard Complexity Report — {payload['timestamp']}\n\n")
    lines.append(f"- status: {payload['status']}")
    lines.append(f"- targets: {' '.join(payload['targets']) if payload['targets'] else '(none)'}")
    lines.append(f"- max cyclomatic complexity: {payload['max_ccn']}")
    lines.append(f"- max function length: {payload['max_length']}")
    lines.append(f"- offenders: {len(offenders)}\n")

    if offenders:
        lines.append("## Top Offenders\n")
        lines.append("| Function | File | CCN | Length |\n|---|---|---:|---:|\n")
        for off in offenders[:max_rows]:
            lines.append(
                f"| `{off.name}` | `{off.path}` | {off.complexity} | {off.length} |\n"
            )
        lines.append("\n")
    else:
        lines.append("No functions exceeded the configured thresholds.\n\n")

    lines.append("## How to Reproduce\n")
    lines.append("```bash")
    lines.append(payload["command_str"])
    lines.append("``" "\n")

    (out_dir / "report.md").write_text("".join(lines), encoding="utf-8")


def _write_raw(out_dir: Path, stdout: str, stderr: str | None = None) -> None:
    lines: list[str] = []
    if stdout:
        lines.append(stdout)
    if stderr:
        lines.append("\n[stderr]\n")
        lines.append(stderr)
    (out_dir / "raw.txt").write_text("".join(lines), encoding="utf-8")


def _sanitize_command(cmd: Iterable[str]) -> list[str]:
    sanitized: list[str] = []
    for part in cmd:
        if not isinstance(part, str):
            part = str(part)
        if any(ch in part for ch in ("\r", "\n")):
            raise ValueError("Command arguments must not contain newline characters")
        sanitized.append(part)
    return sanitized


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _generate_report(
    out_dir: Path,
    raw_json_path: Path,
    targets: list[str],
    max_ccn: int,
    max_length: int,
    report_payload: dict,
    cmd: list[str],
) -> tuple[dict, list[Offender]]:
    offenders: list[Offender] = []

    if not targets:
        report_payload["notes"] = "No targets resolved for lizard run"
        _write_raw(out_dir, "", None)
        return report_payload, offenders

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        report_payload["notes"] = f"lizard invocation failed: {exc}"
        _write_raw(out_dir, "", traceback.format_exc())
        return report_payload, offenders

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    if proc.returncode != 0:
        note = "lizard module not installed" if "No module named lizard" in stderr else f"lizard command failed (rc={proc.returncode})"
        report_payload["notes"] = note
        _write_raw(out_dir, stdout, stderr)
        return report_payload, offenders

    if not stdout.strip():
        report_payload["notes"] = "lizard produced empty output"
        _write_raw(out_dir, stdout, stderr)
        return report_payload, offenders

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        report_payload["notes"] = f"Failed to parse lizard JSON output: {exc}"
        _write_raw(out_dir, stdout, stderr)
        return report_payload, offenders

    raw_json_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")

    offenders = _parse_offenders(parsed, max_ccn=max_ccn, max_length=max_length)
    report_payload.update(
        {
            "status": "ok" if not offenders else "issues",
            "issue_count": len(offenders),
            "files_scanned": len(parsed) if isinstance(parsed, list) else 0,
        }
    )

    if stderr.strip():
        _write_raw(out_dir, stdout, stderr)

    return report_payload, offenders


def _compose_report_payload(
    timestamp: str,
    args: argparse.Namespace,
    targets: list[str],
    cmd: list[str],
) -> dict:
    return {
        "status": "error",
        "timestamp": timestamp,
        "max_ccn": args.max_ccn,
        "max_length": args.max_length,
        "targets": targets,
        "command": cmd,
        "command_str": shlex.join(cmd),
        "issue_count": 0,
        "notes": "",
    }


def _handle_unsafe_arguments(
    out_dir: Path,
    timestamp: str,
    args: argparse.Namespace,
    targets: list[str],
    raw_cmd: Iterable[str],
    exc: Exception,
) -> int:
    report_payload = {
        "status": "error",
        "timestamp": timestamp,
        "max_ccn": args.max_ccn,
        "max_length": args.max_length,
        "targets": targets,
        "command": list(raw_cmd),
        "command_str": "(aborted: unsafe argument detected)",
        "issue_count": 0,
        "notes": f"Unsafe command argument detected: {exc}",
    }
    offenders: list[Offender] = []
    _write_json(out_dir, report_payload)
    _write_md(out_dir, report_payload, offenders)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate lizard complexity artifacts")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-base", default=str(OUT_BASE_DEFAULT))
    parser.add_argument("--timestamp", default=None)
    parser.add_argument("--max-ccn", type=int, default=int(os.getenv("LIZARD_MAX_CCN", "15")))
    parser.add_argument("--max-length", type=int, default=int(os.getenv("LIZARD_MAX_LENGTH", "80")))
    parser.add_argument(
        "--targets",
        nargs="*",
        default=os.getenv("LIZARD_TARGETS", "").split(),
        help="Override default target directories",
    )
    parser.add_argument(
        "--extra-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Additional arguments passed verbatim to lizard before targets",
    )
    return parser


def _resolve_output_base(args: argparse.Namespace, repo_root: Path) -> Path:
    out_base = Path(args.output_base)
    if not out_base.is_absolute():
        out_base = (repo_root / out_base).resolve()
    return out_base


def main() -> int:
    args = _build_parser().parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_base = _resolve_output_base(args, repo_root)
    ts = args.timestamp or _ts_default()
    out_dir = _ensure_out_dir(out_base, ts)

    targets = _select_targets(repo_root, args.targets)
    raw_cmd = _build_command(args.max_ccn, args.max_length, targets, args.extra_args)
    try:
        cmd = _sanitize_command(raw_cmd)
    except ValueError as exc:
        logging.error("Unsafe lizard arguments rejected: %s", exc)
        return _handle_unsafe_arguments(out_dir, ts, args, targets, raw_cmd, exc)

    raw_json_path = out_dir / "raw.json"
    report_payload = _compose_report_payload(ts, args, targets, cmd)

    report_payload, offenders = _generate_report(
        out_dir,
        raw_json_path,
        targets,
        args.max_ccn,
        args.max_length,
        report_payload,
        cmd,
    )

    _write_json(out_dir, report_payload)
    _write_md(out_dir, report_payload, offenders)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
