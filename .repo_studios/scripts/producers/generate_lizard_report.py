#!/usr/bin/env python3
"""Lizard Complexity Report generator with positional bundle artifacts.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/healthview/lizard_report/<YYYYMMDD-HHMM>/`
        - `manifest.json`
        - `summary.md`
        - `telemetry.json`

The script is tolerant: it always exits 0, encoding failures in the telemetry payload.
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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_TARGETS = ("agents", "api", "scripts")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports")
VIEWER_SLUG = "healthview"
TOPIC = "lizard_report"
DEFAULT_ARTIFACTS_TO_KEEP = 10
DEFAULT_LIZARD_EXTRA_ARGS = ("-Ejson", "-i", "-1")
VENDOR_DIR = Path(__file__).resolve().parents[2] / "vendor"
VENDOR_LIZARD_JSON_PATH = VENDOR_DIR / "lizard_ext" / "lizardjson.py"

REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARIES_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories
except ModuleNotFoundError:  # pragma: no cover - fallback for direct script execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries.database_integration import create_storage
    from libraries.prune_logs import prune_run_directories

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


@dataclass(frozen=True)
class Offender:
    path: str
    name: str
    cyclomatic_complexity: int
    length: int
    start_line: int | None = None
    end_line: int | None = None

    def to_payload(self, *, max_ccn: int, max_length: int, rank: int) -> dict[str, Any]:
        ccn_delta = max(self.cyclomatic_complexity - max_ccn, 0)
        length_delta = max(self.length - max_length, 0)
        payload: dict[str, Any] = {
            "rank": rank,
            "path": self.path,
            "name": self.name,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "length": self.length,
            "ccn_over_limit": ccn_delta,
            "length_over_limit": length_delta,
        }
        if self.start_line is not None:
            payload["start_line"] = self.start_line
        if self.end_line is not None:
            payload["end_line"] = self.end_line
        return payload


def _current_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return _current_utc()
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _timestamp_slug(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def _truncate_text(text: str, limit: int) -> tuple[str, bool]:
    if limit <= 0 or len(text) <= limit:
        return text, False
    return text[:limit] + "\n... (truncated)\n", True


def _ensure_lizard_json_extension() -> None:
    try:
        lizard_ext = importlib.import_module("lizard_ext")
    except ModuleNotFoundError:
        logging.warning("lizard_ext package not found; JSON extension unavailable")
        return

    module_file = getattr(lizard_ext, "__file__", None)
    if not module_file:
        logging.warning("lizard_ext module path unavailable; JSON extension unavailable")
        return

    module_path = Path(module_file).parent / "lizardjson.py"
    if module_path.exists():
        return

    if VENDOR_LIZARD_JSON_PATH.exists():
        source_text = VENDOR_LIZARD_JSON_PATH.read_text(encoding="utf-8")
    else:
        source_text = LIZARD_JSON_EXTENSION_SOURCE

    try:
        module_path.write_text(source_text, encoding="utf-8")
    except OSError as exc:
        logging.warning("Failed to install lizard JSON extension: %s", exc)


def _has_flag(args: Sequence[str], flag: str, long_flag: str | None = None) -> bool:
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


def _build_command(max_ccn: int, max_length: int, targets: Sequence[str], extra: Iterable[str]) -> list[str]:
    cmd: list[str] = [
        sys.executable,
        "-m",
        "lizard",
        "-C",
        str(max_ccn),
        "-L",
        str(max_length),
    ]
    cmd.extend(_apply_default_extra_args(extra))
    cmd.extend(str(target) for target in targets)
    return cmd


def _sanitize_command(cmd: Sequence[Any]) -> list[str]:
    sanitized: list[str] = []
    for part in cmd:
        text = str(part)
        if any(ch in text for ch in ("\r", "\n")):
            raise ValueError("Command arguments must not contain newline characters")
        sanitized.append(text)
    return sanitized


def _resolve_targets(repo_root: Path, requested: Sequence[str] | None) -> list[str]:
    candidates = list(requested) if requested else list(DEFAULT_TARGETS)
    resolved: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        if not raw:
            continue
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = (repo_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(repo_root)
        except ValueError:
            logging.warning("Skipping target outside repo root: %s", candidate)
            continue
        if not candidate.exists():
            continue
        path_str = str(candidate)
        if path_str not in seen:
            seen.add(path_str)
            resolved.append(path_str)
    return resolved


def _extract_file_path(entry: dict[str, Any]) -> str | None:
    for key in ("filename", "file_name", "file"):
        value = entry.get(key)
        if value:
            return str(value)
    return None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_optional_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _collect_offenders(modules: Sequence[dict[str, Any]], max_ccn: int, max_length: int) -> list[Offender]:
    offenders: list[Offender] = []
    for entry in modules:
        file_path = _extract_file_path(entry)
        if not file_path:
            continue
        for func in entry.get("function_list") or []:
            ccn = _as_int(func.get("cyclomatic_complexity"))
            length = _as_int(func.get("length", func.get("nloc")))
            if ccn <= max_ccn and length <= max_length:
                continue
            name = func.get("name") or func.get("long_name") or "<unnamed>"
            offenders.append(
                Offender(
                    path=file_path,
                    name=str(name),
                    cyclomatic_complexity=ccn,
                    length=length,
                    start_line=_as_optional_int(func.get("start_line")),
                    end_line=_as_optional_int(func.get("end_line")),
                )
            )
    return offenders


def _rank_offenders(offenders: Sequence[Offender], max_ccn: int, max_length: int) -> list[Offender]:
    def severity(off: Offender) -> tuple[float, float, float, float, str, str]:
        ccn_ratio = (off.cyclomatic_complexity / max_ccn) if max_ccn > 0 else float("inf")
        length_ratio = (off.length / max_length) if max_length > 0 else float("inf")
        ccn_over = max(off.cyclomatic_complexity - max_ccn, 0)
        length_over = max(off.length - max_length, 0)
        return (
            -max(ccn_ratio, length_ratio),
            -ccn_over,
            -length_over,
            -off.cyclomatic_complexity,
            off.path,
            off.name,
        )

    return sorted(offenders, key=severity)


def _format_metric(value: int, limit: int) -> str:
    if limit <= 0:
        return f"{value}"
    delta = value - limit
    if delta > 0:
        return f"{value} (Δ+{delta})"
    return str(value)


def _recommendation(off: Offender, max_ccn: int, max_length: int) -> str:
    over_ccn = off.cyclomatic_complexity > max_ccn
    over_length = off.length > max_length
    if over_ccn and over_length:
        return "Split into smaller functions and simplify branching."
    if over_ccn:
        return "Reduce branching or extract helpers to lower CCN."
    if over_length:
        return "Break the function into smaller units to shorten length."
    return "Review function for maintainability improvements."


def _format_location(off: Offender) -> str:
    if off.start_line is not None and off.start_line > 0:
        return f"{off.path}:{off.start_line}"
    return off.path


def _render_markdown(
    payload: dict[str, Any],
    offenders: Sequence[Offender],
    *,
    top_limit: int,
    max_ccn: int,
    max_length: int,
) -> str:
    lines = [
        "# Lizard Complexity Report",
        "",
        f"- generated_utc: {payload['generated_utc']}",
        f"- status: {payload['status']}",
        f"- targets: {' '.join(payload['targets']) if payload['targets'] else '(none)'}",
        f"- max cyclomatic complexity: {payload['max_ccn']}",
        f"- max function length: {payload['max_length']}",
        f"- offenders: {len(offenders)}",
        "",
    ]

    if offenders:
        lines.extend(
            [
                "## Top Offenders",
                "",
                "| Rank | Function | Location | CCN (Δ) | Length (Δ) | Recommendation |",
                "|---:|---|---|---:|---:|---|",
            ]
        )
        for index, offender in enumerate(offenders[:top_limit], start=1):
            ccn_display = _format_metric(offender.cyclomatic_complexity, max_ccn)
            length_display = _format_metric(offender.length, max_length)
            lines.append(
                "| {rank} | `{name}` | `{location}` | {ccn} | {length} | {recommendation} |".format(
                    rank=index,
                    name=offender.name,
                    location=_format_location(offender),
                    ccn=ccn_display,
                    length=length_display,
                    recommendation=_recommendation(offender, max_ccn, max_length),
                )
            )
        lines.append("")
        remaining = payload.get("issue_count", 0) - min(len(offenders), top_limit)
        if remaining > 0:
            lines.extend(
                [
                    f"Additional offenders not shown: {remaining} (see `telemetry.json` for full list).",
                    "",
                ]
            )
    else:
        lines.append("No functions exceeded the configured thresholds.")
        lines.append("")

    lines.extend(
        [
            "## How to Reproduce",
            "",
            "```bash",
            payload.get("command_str") or "(unavailable)",
            "```",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def _render_log(
    payload: dict[str, Any],
    offenders: Sequence[Offender],
    *,
    max_ccn: int,
    max_length: int,
    top_limit: int,
) -> str:
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
        lines.append(f"top_offender_limit={min(len(offenders), top_limit)}")
        for index, offender in enumerate(offenders[:top_limit], start=1):
            ccn_delta = max(offender.cyclomatic_complexity - max_ccn, 0)
            length_delta = max(offender.length - max_length, 0)
            location = _format_location(offender)
            lines.append(
                "top{rank}={location}::{name} ccn={ccn} delta_ccn={delta_ccn} length={length} delta_length={delta_length}".format(
                    rank=index,
                    location=location,
                    name=offender.name,
                    ccn=offender.cyclomatic_complexity,
                    delta_ccn=ccn_delta,
                    length=offender.length,
                    delta_length=length_delta,
                )
            )
        remaining = payload.get("issue_count", 0) - min(len(offenders), top_limit)
        if remaining > 0:
            lines.append(f"additional_offenders={remaining}")
    else:
        lines.append("offenders=(none)")
    return "\n".join(lines) + "\n"


def _format_raw_output(stdout: str, stderr: str | None = None) -> str:
    segments: list[str] = []
    if stdout:
        stripped = stdout.strip()
        if stripped:
            try:
                formatted = json.dumps(json.loads(stripped), indent=2)
            except json.JSONDecodeError:
                formatted = stdout
        else:
            formatted = stdout
        segments.append(formatted)
    if stderr:
        segments.append("\n[stderr]\n")
        segments.append(stderr)
    return "".join(segments)


def _compose_report(
    *,
    slug: str,
    generated_at: datetime,
    max_ccn: int,
    max_length: int,
    targets: Sequence[str],
    command: Sequence[str],
    command_display: str | None = None,
) -> dict[str, Any]:
    command_list = list(command)
    display = command_display if command_display is not None else (shlex.join(command_list) if command_list else "")
    return {
        "schema_version": 1,
        "run_timestamp": slug,
        "generated_utc": generated_at.isoformat(),
        "max_ccn": max_ccn,
        "max_length": max_length,
        "targets": list(targets),
        "command": command_list,
        "command_str": display,
        "status": "pending",
        "issue_count": 0,
        "files_scanned": 0,
        "offenders": [],
        "notes": None,
    }


def _build_manifest(*, report: dict[str, Any], repo_root: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    status = report.get("status")
    summary = {
        "status": status,
        "issue_count": report.get("issue_count", 0),
        "files_scanned": report.get("files_scanned", 0),
    }
    return {
        "schema_version": 1,
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC,
        "run_timestamp": inputs.get("run_timestamp"),
        "git_sha": None,
        "status": "ok" if status in {"ok", "issues", "no_targets"} else "failed",
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


def _append_note(payload: dict[str, Any], message: str) -> None:
    if not message:
        return
    existing = payload.get("notes")
    if existing:
        payload["notes"] = f"{existing}; {message}"
    else:
        payload["notes"] = message


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate lizard complexity artifacts")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        help="Directory for structured lizard reports",
    )
    parser.add_argument(
        "--output-base",
        dest="output_base",
        default=None,
        help="Backward-compatible alias for --output-dir",
    )
    parser.add_argument("--timestamp", default=None)
    parser.add_argument(
        "--max-ccn",
        type=int,
        default=int(os.getenv("LIZARD_MAX_CCN", "15")),
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=int(os.getenv("LIZARD_MAX_LENGTH", "80")),
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        default=None,
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


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    configure_logging(args.log_level)

    repo_root = Path(args.repo_root).expanduser().resolve()
    output_setting = args.output_dir or args.output_base or str(DEFAULT_OUTPUT_DIR)
    output_dir = Path(output_setting)
    if not output_dir.is_absolute():
        output_dir = (repo_root / output_dir).resolve()

    if output_dir.name == "lizard_reports":
        logging.warning(
            "Legacy --output-dir points at lizard_reports; treating %s as base output directory",
            output_dir.parent,
        )
        output_dir = output_dir.parent

    generated_at = _parse_timestamp(args.timestamp)
    run_timestamp = _timestamp_slug(generated_at)

    target_override: Sequence[str] | None = None
    if args.targets:
        target_override = args.targets
    else:
        env_targets = [item for item in os.getenv("LIZARD_TARGETS", "").split() if item]
        if env_targets:
            target_override = env_targets

    targets = _resolve_targets(repo_root, target_override)
    requested_display = list(target_override) if target_override is not None else list(DEFAULT_TARGETS)

    offenders_ranked: list[Offender] = []
    raw_text = ""
    raw_json_content: Any | None = None

    if not targets:
        payload = _compose_report(
            slug=run_timestamp,
            generated_at=generated_at,
            max_ccn=args.max_ccn,
            max_length=args.max_length,
            targets=targets,
            command=[],
            command_display="(skipped: no targets resolved)",
        )
        payload["status"] = "no_targets"
        payload["notes"] = f"No targets resolved from requested set: {', '.join(requested_display)}"
    else:
        raw_cmd = _build_command(args.max_ccn, args.max_length, targets, args.extra_args)
        try:
            command = _sanitize_command(raw_cmd)
        except ValueError as exc:
            logging.error("Unsafe lizard arguments rejected: %s", exc)
            payload = _compose_report(
                slug=run_timestamp,
                generated_at=generated_at,
                max_ccn=args.max_ccn,
                max_length=args.max_length,
                targets=targets,
                command=[],
                command_display="(aborted: unsafe argument detected)",
            )
            payload["status"] = "error"
            payload["notes"] = f"Unsafe command argument detected: {exc}"
        else:
            payload = _compose_report(
                slug=run_timestamp,
                generated_at=generated_at,
                max_ccn=args.max_ccn,
                max_length=args.max_length,
                targets=targets,
                command=command,
            )
            _ensure_lizard_json_extension()
            try:
                result = subprocess.run(command, capture_output=True, text=True)
            except Exception as exc:  # pragma: no cover - defensive fallback
                logging.exception("Failed to invoke lizard")
                raw_text = _format_raw_output("", "".join(traceback.format_exception(exc)))
                payload["status"] = "error"
                payload["notes"] = f"Failed to invoke lizard: {exc}"
            else:
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                raw_text = _format_raw_output(stdout, stderr)

                data: Any | None = None
                modules: list[dict[str, Any]] = []
                if stdout.strip():
                    try:
                        data = json.loads(stdout)
                    except json.JSONDecodeError as exc:
                        logging.error("Failed to parse lizard JSON output: %s", exc)
                        payload["status"] = "error"
                        payload["notes"] = f"Failed to parse lizard JSON output: {exc}"
                    else:
                        if isinstance(data, dict):
                            modules = [data]
                        elif isinstance(data, list):
                            modules = [entry for entry in data if isinstance(entry, dict)]
                        collected = _collect_offenders(modules, args.max_ccn, args.max_length)
                        offenders_ranked = _rank_offenders(collected, args.max_ccn, args.max_length)
                        payload["files_scanned"] = len(modules)
                        if payload.get("status") != "error":
                            payload["status"] = "issues" if offenders_ranked else "ok"
                        raw_json_content = data
                else:
                    payload["status"] = "ok"
                    payload["files_scanned"] = 0
                    raw_json_content = []

                if result.returncode != 0:
                    logging.error("Lizard exited with status %s", result.returncode)
                    _append_note(payload, f"Lizard exited with status {result.returncode}")
                    if payload["status"] != "error":
                        payload["status"] = "error"

    payload["offenders"] = [
        offender.to_payload(max_ccn=args.max_ccn, max_length=args.max_length, rank=index + 1)
        for index, offender in enumerate(offenders_ranked)
    ]
    payload["issue_count"] = len(offenders_ranked)

    top_offenders = offenders_ranked[:10]

    log_text = _render_log(
        payload,
        top_offenders,
        max_ccn=args.max_ccn,
        max_length=args.max_length,
        top_limit=10,
    )

    raw_text_truncated, raw_text_was_truncated = _truncate_text(raw_text, 200_000)
    raw_json_summary: dict[str, Any] | None = None
    if raw_json_content is not None:
        if isinstance(raw_json_content, list):
            raw_json_summary = {
                "type": "list",
                "entry_count": len(raw_json_content),
                "sample": raw_json_content[:5],
            }
        else:
            raw_json_summary = {
                "type": type(raw_json_content).__name__,
                "sample": raw_json_content,
            }

    report_payload: dict[str, Any] = {
        **payload,
        "raw": {
            "text": raw_text_truncated,
            "text_truncated": raw_text_was_truncated,
            "json_summary": raw_json_summary,
        },
        "log_text": log_text,
    }

    run_inputs: dict[str, Any] = {
        "run_timestamp": run_timestamp,
        "max_ccn": args.max_ccn,
        "max_length": args.max_length,
        "targets_requested": requested_display,
        "targets_resolved": targets,
        "extra_args": list(args.extra_args),
        "artifacts_to_keep": max(args.artifacts_to_keep, 1),
    }

    markdown = _render_markdown(
        payload,
        top_offenders,
        top_limit=10,
        max_ccn=args.max_ccn,
        max_length=args.max_length,
    )

    telemetry = {
        "schema_version": 1,
        "generated_utc": generated_at.isoformat(),
        "metrics": {
            "status": payload.get("status"),
            "issue_count": payload.get("issue_count", 0),
            "files_scanned": payload.get("files_scanned", 0),
            "targets_count": len(targets),
            "max_ccn": args.max_ccn,
            "max_length": args.max_length,
        },
        "payload": report_payload,
    }

    storage = create_storage(
        output_dir,
        VIEWER_SLUG,
        TOPIC,
        timestamp=run_timestamp,
    )
    bundle_dir = storage.file_storage.bundle_dir
    manifest = _build_manifest(report=payload, repo_root=repo_root, inputs=run_inputs)

    # DB_INTEGRATION_MARKER: write manifest.json (report_runs)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: write summary.md (report_summaries)
    storage.write_summary({"markdown": markdown}, format="markdown")
    # DB_INTEGRATION_MARKER: write telemetry.json + extracted metrics (test_metrics)
    storage.write_telemetry(telemetry)

    prune_run_directories(
        output_dir / VIEWER_SLUG / TOPIC,
        keep=max(args.artifacts_to_keep, 1),
        current_run=bundle_dir,
        logger=logging.getLogger(__name__),
    )
    logging.info("Lizard report written to %s", bundle_dir)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
