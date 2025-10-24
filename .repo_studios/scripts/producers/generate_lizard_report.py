#!/usr/bin/env python3
"""Lizard Complexity Report Generator.

Runs `python -m lizard` with repo conventions and emits timestamped artifacts under
`.repo_studios/reports/producer_reports/lizard_reports/<timestamp>/`:

- `report.json`: machine-readable summary (status, counts, offending functions)
- `report.md`: human summary with top offenders and reproduction hints
- `raw.json`: full JSON output from Lizard when available
- `raw.txt`: stdout/stderr when invocation fails
- `log.txt`: structured key/value summary for automation

The script is tolerant: it always exits 0, encoding failures in the JSON summary.
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import shlex
import subprocess
import sys
import traceback
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

DEFAULT_TARGETS = ("agents", "api", "scripts")
DEFAULT_OUTPUT_DIR = Path(
    ".repo_studios/reports/producer_reports/lizard_reports"
)
RUN_PREFIX = "lizard"
DEFAULT_ARTIFACTS_TO_KEEP = 10
DEFAULT_LIZARD_EXTRA_ARGS = ("-Ejson", "-i", "-1")
VENDOR_DIR = Path(__file__).resolve().parents[2] / "vendor"
VENDOR_LIZARD_JSON_PATH = VENDOR_DIR / "lizard_ext" / "lizardjson.py"
LIZARD_JSON_EXTENSION_SOURCE = '''"""JSON output extension for lizard (auto-installed)."""

from __future__ import annotations

import json
from typing import Iterable

from lizard import get_warnings


def _serialize_function(func):
    return {
        "name": getattr(func, "name", None),
        "long_name": getattr(func, "long_name", None),
        "cyclomatic_complexity": getattr(func, "cyclomatic_complexity", None),
        "token_count": getattr(func, "token_count", None),
        "parameter_count": getattr(func, "parameter_count", None),
        "length": getattr(func, "length", None),
        "nloc": getattr(func, "nloc", None),
        "start_line": getattr(func, "start_line", None),
        "end_line": getattr(func, "end_line", None),
        "file": getattr(func, "filename", None),
    }


def _serialize_module(module):
    return {
        "filename": getattr(module, "filename", None),
        "nloc": getattr(module, "nloc", None),
        "cyclomatic_complexity": getattr(module, "CCN", None),
        "token_count": getattr(module, "token_count", None),
        "function_list": [_serialize_function(func) for func in getattr(module, "function_list", [])],
    }


def print_json(result: Iterable, option, scheme, total_factory):
    modules = [module for module in result if module]
    print(json.dumps([_serialize_module(module) for module in modules], indent=2))
    warnings = list(get_warnings(modules, option))
    warning_count = len(warnings)
    if getattr(option, "number", -1) >= 0 and warning_count > option.number:
        return warning_count
    return warning_count


class LizardExtension:  # pragma: no cover - compatibility shim
    ordering_index = 10_000

    def set_args(self, parser):
        parser.set_defaults(printer=print_json)

    def __call__(self, tokens, reader):
        for token in tokens:
            yield token
'''


def _ensure_lizard_json_extension() -> None:
    try:
        lizard_ext = importlib.import_module("lizard_ext")
    except ModuleNotFoundError:
        logging.warning("lizard_ext package not found; JSON extension unavailable")
        return

    module_path = Path(lizard_ext.__file__).parent / "lizardjson.py"
    if module_path.exists():
        return

    source_text: str
    if VENDOR_LIZARD_JSON_PATH.exists():
        source_text = VENDOR_LIZARD_JSON_PATH.read_text(encoding="utf-8")
    else:
        source_text = LIZARD_JSON_EXTENSION_SOURCE

    try:
        module_path.write_text(source_text, encoding="utf-8")
    except OSError as exc:
        logging.warning("Failed to install lizard JSON extension: %s", exc)


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


def _format_run_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d_%H%M%S")


def _resolve_timestamp(raw: str | None) -> tuple[str, datetime]:
    if not raw:
        now = _current_utc()
        return _format_run_slug(now), now

    try:
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return _format_run_slug(parsed), parsed
    except ValueError:
        # Preserve provided slug but still capture current UTC for metadata.
        return raw, _current_utc()


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_slug(slug: str) -> str:
    sanitized = slug.replace(os.sep, "_")
    sanitized = sanitized.replace("/", "_")
    return sanitized


def _copy_latest(src: Path, dest: Path) -> None:
    try:
        if dest.exists():
            dest.unlink()
        dest.hardlink_to(src)
    except OSError:
        dest.write_bytes(src.read_bytes())


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    candidates.sort(key=lambda p: p.name, reverse=True)
    for index, path in enumerate(candidates):
        if index < keep or path == current_run:
            continue
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)  # type: ignore[attr-defined]
        path.rmdir()


def _prepare_run_dir(output_dir: Path, run_slug: str) -> Path:
    _ensure_directory(output_dir)
    safe_slug = _sanitize_slug(run_slug)
    run_dir = output_dir / f"{RUN_PREFIX}-{safe_slug}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


@dataclass
class Offender:
    path: str
    name: str
    complexity: int
    length: int


def _has_flag(args: list[str], flag: str, long_flag: str | None = None) -> bool:
    for item in args:
        if item == flag or (long_flag and item == long_flag):
            return True
        if item.startswith(flag) and item != flag:
            return True
        if long_flag and item.startswith(long_flag) and item != long_flag:
            return True
    return False


def _apply_default_extra_args(extra: Iterable[str]) -> list[str]:
    extra_list = [str(arg) for arg in extra if str(arg)]

    defaults: list[str] = []
    if not _has_flag(extra_list, "-Ejson"):
        defaults.append(DEFAULT_LIZARD_EXTRA_ARGS[0])

    if not (_has_flag(extra_list, "-i") or _has_flag(extra_list, "--ignore_warnings")):
        defaults.extend(DEFAULT_LIZARD_EXTRA_ARGS[1:])

    return defaults + extra_list


def _build_command(max_ccn: int, max_length: int, targets: Iterable[str], extra: Iterable[str]) -> list[str]:
    cmd: list[str] = [sys.executable, "-m", "lizard", "-C", str(max_ccn), "-L", str(max_length)]
    cmd.extend(_apply_default_extra_args(extra))
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


def _write_json(run_dir: Path, payload: dict) -> Path:
    path = run_dir / "report.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _write_md(run_dir: Path, payload: dict, offenders: list[Offender], *, max_rows: int = 25) -> Path:
    lines: list[str] = []
    lines.append("# Lizard Complexity Report\n\n")
    lines.append(f"- generated_utc: {payload['generated_utc']}\n")
    lines.append(f"- status: {payload['status']}\n")
    targets = " ".join(payload["targets"]) if payload["targets"] else "(none)"
    lines.append(f"- targets: {targets}\n")
    lines.append(f"- max cyclomatic complexity: {payload['max_ccn']}\n")
    lines.append(f"- max function length: {payload['max_length']}\n")
    lines.append(f"- offenders: {len(offenders)}\n\n")

    if offenders:
        lines.append("## Top Offenders\n\n")
        lines.append("| Function | File | CCN | Length |\n")
        lines.append("|---|---|---:|---:|\n")
        for off in offenders[:max_rows]:
            lines.append(
                f"| `{off.name}` | `{off.path}` | {off.complexity} | {off.length} |\n"
            )
        lines.append("\n")
    else:
        lines.append("No functions exceeded the configured thresholds.\n\n")

    lines.append("## How to Reproduce\n\n")
    lines.append("```bash\n")
    lines.append(f"{payload['command_str']}\n")
    lines.append("```\n")

    path = run_dir / "report.md"
    path.write_text("".join(lines), encoding="utf-8")
    return path


def _write_log(run_dir: Path, payload: dict, offenders: list[Offender]) -> Path:
    lines = [
        f"status={payload['status']}",
        f"issue_count={payload['issue_count']}",
        f"generated_utc={payload['generated_utc']}",
        f"targets={' '.join(payload['targets']) if payload['targets'] else '(none)'}",
        f"max_ccn={payload['max_ccn']}",
        f"max_length={payload['max_length']}",
        f"files_scanned={payload.get('files_scanned', 0)}",
    ]
    if payload.get("notes"):
        lines.append(f"notes={payload['notes']}")
    if offenders:
        lines.append("offenders:")
        for offender in offenders:
            lines.append(
                f"  {offender.path}::{offender.name} ccn={offender.complexity} length={offender.length}"
            )
    else:
        lines.append("offenders=(none)")

    path = run_dir / "log.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_artifacts(
    payload: dict,
    offenders: list[Offender],
    *,
    run_dir: Path,
    output_dir: Path,
    keep: int,
) -> None:
    _ensure_directory(output_dir)
    json_path = _write_json(run_dir, payload)
    md_path = _write_md(run_dir, payload, offenders)
    log_path = _write_log(run_dir, payload, offenders)

    latest_pairs: list[tuple[Path, Path]] = [
        (json_path, output_dir / "latest_report.json"),
        (md_path, output_dir / "latest_report.md"),
        (log_path, output_dir / "latest_report.log"),
    ]

    raw_json = run_dir / "raw.json"
    raw_txt = run_dir / "raw.txt"
    if raw_json.exists():
        latest_pairs.append((raw_json, output_dir / "latest_raw.json"))
    if raw_txt.exists():
        latest_pairs.append((raw_txt, output_dir / "latest_raw.txt"))

    for src, dest in latest_pairs:
        _copy_latest(src, dest)

    prune_old_runs(output_dir, keep=keep, current_run=run_dir)


def _write_raw(raw_path: Path, stdout: str, stderr: str | None = None) -> None:
    lines: list[str] = []
    if stdout:
        formatted_stdout = stdout
        stripped = stdout.strip()
        if stripped:
            try:
                formatted_stdout = json.dumps(json.loads(stripped), indent=2)
            except json.JSONDecodeError:
                formatted_stdout = stdout
        lines.append(formatted_stdout)
    if stderr:
        lines.append("\n[stderr]\n")
        lines.append(stderr)
    raw_path.write_text("".join(lines), encoding="utf-8")


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
    run_dir: Path,
    raw_json_path: Path,
    raw_txt_path: Path,
    targets: list[str],
    max_ccn: int,
    max_length: int,
    report_payload: dict,
    cmd: list[str],
) -> tuple[dict, list[Offender]]:
    offenders: list[Offender] = []

    if not targets:
        report_payload["status"] = "no_targets"
        report_payload["notes"] = "No targets resolved for lizard run"
        _write_raw(raw_txt_path, "", None)
        return report_payload, offenders

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001
        report_payload["notes"] = f"lizard invocation failed: {exc}"
        _write_raw(raw_txt_path, "", traceback.format_exc())
        return report_payload, offenders

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    if proc.returncode != 0:
        note = "lizard module not installed" if "No module named lizard" in stderr else f"lizard command failed (rc={proc.returncode})"
        report_payload["notes"] = note
        report_payload["status"] = "error"
        _write_raw(raw_txt_path, stdout, stderr)
        return report_payload, offenders

    if not stdout.strip():
        report_payload["notes"] = "lizard produced empty output"
        report_payload["status"] = "error"
        _write_raw(raw_txt_path, stdout, stderr)
        return report_payload, offenders

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError as exc:
        report_payload["notes"] = f"Failed to parse lizard JSON output: {exc}"
        report_payload["status"] = "error"
        _write_raw(raw_txt_path, stdout, stderr)
        return report_payload, offenders

    raw_json_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    _write_raw(raw_txt_path, stdout, stderr if stderr.strip() else None)

    offenders = _parse_offenders(parsed, max_ccn=max_ccn, max_length=max_length)
    report_payload.update(
        {
            "status": "ok" if not offenders else "issues",
            "issue_count": len(offenders),
            "files_scanned": len(parsed) if isinstance(parsed, list) else 0,
        }
    )
    report_payload["offenders"] = [
        {
            "path": offender.path,
            "name": offender.name,
            "cyclomatic_complexity": offender.complexity,
            "length": offender.length,
        }
        for offender in offenders
    ]

    return report_payload, offenders


def _compose_report_payload(
    run_slug: str,
    generated_at: datetime,
    args: argparse.Namespace,
    targets: list[str],
    cmd: list[str],
) -> dict:
    return {
        "schema_version": 1,
        "status": "error",
        "timestamp": run_slug,
        "generated_utc": generated_at.isoformat(),
        "max_ccn": args.max_ccn,
        "max_length": args.max_length,
        "targets": targets,
        "command": cmd,
        "command_str": shlex.join(cmd),
        "issue_count": 0,
        "files_scanned": 0,
        "offenders": [],
        "notes": "",
    }


def _handle_unsafe_arguments(
    run_dir: Path,
    output_dir: Path,
    run_slug: str,
    generated_at: datetime,
    args: argparse.Namespace,
    targets: list[str],
    raw_cmd: Iterable[str],
    exc: Exception,
    *,
    keep: int,
) -> int:
    report_payload = {
        "schema_version": 1,
        "status": "error",
        "timestamp": run_slug,
        "generated_utc": generated_at.isoformat(),
        "max_ccn": args.max_ccn,
        "max_length": args.max_length,
        "targets": targets,
        "command": list(raw_cmd),
        "command_str": "(aborted: unsafe argument detected)",
        "issue_count": 0,
        "files_scanned": 0,
        "offenders": [],
        "notes": f"Unsafe command argument detected: {exc}",
    }
    offenders: list[Offender] = []
    write_artifacts(
        report_payload,
        offenders,
        run_dir=run_dir,
        output_dir=output_dir,
        keep=keep,
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate lizard complexity artifacts")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for structured lizard reports",
    )
    parser.add_argument(
        "--output-base",
        dest="output_dir",
        help="Backward-compatible alias for --output-dir",
    )
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
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical runs to retain",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser


def _resolve_output_dir(output_value: str | None, repo_root: Path) -> Path:
    value = output_value or str(DEFAULT_OUTPUT_DIR)
    out_dir = Path(value)
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()
    return out_dir


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    configure_logging(args.log_level)

    repo_root = Path(args.repo_root).resolve()
    output_dir = _resolve_output_dir(args.output_dir, repo_root)
    run_slug, generated_at = _resolve_timestamp(args.timestamp)
    run_dir = _prepare_run_dir(output_dir, run_slug)

    raw_json_path = run_dir / "raw.json"
    raw_txt_path = run_dir / "raw.txt"

    _ensure_lizard_json_extension()

    targets = _select_targets(repo_root, args.targets)
    raw_cmd = _build_command(args.max_ccn, args.max_length, targets, args.extra_args)
    try:
        cmd = _sanitize_command(raw_cmd)
    except ValueError as exc:
        logging.error("Unsafe lizard arguments rejected: %s", exc)
        return _handle_unsafe_arguments(
            run_dir,
            output_dir,
            run_slug,
            generated_at,
            args,
            targets,
            raw_cmd,
            exc,
            keep=args.artifacts_to_keep,
        )

    report_payload = _compose_report_payload(run_slug, generated_at, args, targets, cmd)

    report_payload, offenders = _generate_report(
        run_dir,
        raw_json_path,
        raw_txt_path,
        targets,
        args.max_ccn,
        args.max_length,
        report_payload,
        cmd,
    )

    write_artifacts(
        report_payload,
        offenders,
        run_dir=run_dir,
        output_dir=output_dir,
        keep=args.artifacts_to_keep,
    )

    # Maintain legacy behavior: never fail the producer, even when offenders exist.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
