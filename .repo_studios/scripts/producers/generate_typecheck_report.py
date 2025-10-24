"""Run mypy and emit structured artifacts for the typecheck producer."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover - Python 3.11+
    import tomllib
except Exception:  # pragma: no cover - fallback if unavailable
    tomllib = None  # type: ignore[assignment]


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/typecheck_reports")
RUN_PREFIX = "typecheck"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1


@dataclass
class ErrorSample:
    path: str
    line: int
    code: str
    message: str


@dataclass
class BuildStats:
    status: str
    error_count: int
    files_with_issues: int
    paths_checked: list[str]
    invocation: list[str]
    mypy_version: str
    samples: list[ErrorSample]


def _current_utc() -> datetime:
    try:
        return datetime.now(datetime.UTC)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - python <3.11 fallback
        return datetime.now(timezone.utc)


def _format_slug(moment: datetime) -> str:
    return moment.strftime("%Y%m%d_%H%M%S")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_slug(slug: str) -> str:
    safe = slug.replace("/", "_").replace("\\", "_")
    if os.sep not in {"/", "\\"}:
        safe = safe.replace(os.sep, "_")
    return safe


def _prepare_run_dir(output_dir: Path, run_slug: str) -> Path:
    run_dir = output_dir / f"{RUN_PREFIX}-{_sanitize_slug(run_slug)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    runs = [child for child in output_dir.iterdir() if child.is_dir() and child.name.startswith(f"{RUN_PREFIX}-")]
    runs.sort(key=lambda node: node.name, reverse=True)
    for index, node in enumerate(runs):
        if index < keep or node == current_run:
            continue
        for item in node.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)
        node.rmdir()


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _load_pyproject(repo_root: Path) -> dict[str, Any]:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover - defensive
        return {}


def _read_pyproject_targets(repo_root: Path) -> list[str]:
    data = _load_pyproject(repo_root)
    tool = data.get("tool", {}) if isinstance(data, dict) else {}
    mypy_cfg = tool.get("mypy") if isinstance(tool, dict) else None
    if isinstance(mypy_cfg, dict):
        files = mypy_cfg.get("files", [])
        if isinstance(files, list):
            return [str(entry) for entry in files if isinstance(entry, (str, bytes))]
    return []


def _env_bool(name: str) -> bool:
    raw = os.getenv(name)
    return raw is not None and raw.lower() not in {"", "0", "false"}


def _discover_targets(repo_root: Path) -> list[str]:
    override = os.getenv("TYPECHECK_TARGETS", "").strip()
    if override:
        return [value for value in override.split() if value]
    return _read_pyproject_targets(repo_root)


def _allow_fast_targets(repo_root: Path) -> list[str]:
    defaults = ["api", "agents/core", "agents/interface/chainlit"]
    return [path for path in defaults if (repo_root / path).exists()]


def _filter_fast_targets(repo_root: Path, targets: list[str]) -> list[str]:
    allow_prefixes = ["api", "agents/core", "agents/interface/chainlit"]

    def _allowed(entry: str) -> bool:
        normalized = entry.strip().strip("/")
        return any(normalized == prefix or normalized.startswith(prefix + "/") for prefix in allow_prefixes)

    curated = [t for t in targets if _allowed(t)]
    return curated or _allow_fast_targets(repo_root)


def _get_mypy_version(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "mypy", "--version"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        return (proc.stdout or proc.stderr or "unknown").strip() or "unknown"
    except Exception:  # pragma: no cover - defensive
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


def _run_mypy(repo_root: Path, invocation: list[str]) -> tuple[str, int]:
    try:
        proc = subprocess.run(
            invocation,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout or ""
        if proc.stderr:
            stdout += "\n" + proc.stderr
        return stdout, proc.returncode
    except FileNotFoundError as exc:
        message = f"[EXCEPTION] mypy not found: {exc}"
        return message, 127
    except Exception as exc:  # pragma: no cover - defensive
        return f"[EXCEPTION] {exc!r}", 1


def _parse_summary(stdout: str) -> tuple[int, int, bool]:
    ok_match = re.search(r"^Success: no issues found in (\d+) source files?", stdout, flags=re.M)
    if ok_match:
        return 0, 0, True
    total_errors = 0
    files_with_issues = 0
    error_match = re.search(r"^Found (\d+) errors? in (\d+) files?", stdout, flags=re.M)
    if error_match:
        try:
            total_errors = int(error_match.group(1))
            files_with_issues = int(error_match.group(2))
        except Exception:  # pragma: no cover - defensive
            total_errors = 0
            files_with_issues = 0
    return total_errors, files_with_issues, False


def _parse_samples(stdout: str, limit: int = 50) -> list[ErrorSample]:
    pattern = re.compile(
        r"^(?P<path>[^:\n]+):(?P<line>\d+):(?:\d+:)?\s+error: (?P<msg>.*?)(?: \[(?P<code>[^\]]+)\])?$"
    )
    samples: list[ErrorSample] = []
    for line in stdout.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        try:
            lineno = int(match.group("line"))
        except Exception:
            lineno = 1
        samples.append(
            ErrorSample(
                path=match.group("path"),
                line=lineno,
                code=match.group("code") or "",
                message=(match.group("msg") or "").strip(),
            )
        )
        if len(samples) >= limit:
            break
    return samples


def _compute_status(success: bool, total_errors: int, files_with_issues: int, return_code: int) -> str:
    if return_code == 0 and success and total_errors == 0 and files_with_issues == 0:
        return "ok"
    if return_code == 127:
        return "missing_tool"
    return "error"


def _compose_payload(
    *,
    run_slug: str,
    generated_at: datetime,
    repo_root: Path,
    run_dir: Path,
    status: str,
    stats: BuildStats,
) -> dict[str, Any]:
    summary = {
        "error_count": stats.error_count,
        "files_with_issues": stats.files_with_issues,
        "paths_checked": stats.paths_checked,
    }
    samples = [
        {
            "path": sample.path,
            "line": sample.line,
            "code": sample.code,
            "message": sample.message,
        }
        for sample in stats.samples
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "timestamp": run_slug,
        "generated_utc": generated_at.isoformat(),
        "repo_root": str(repo_root),
        "output_dir": str(run_dir.parent),
        "invocation": stats.invocation,
        "mypy_version": stats.mypy_version,
        "summary": summary,
        "error_samples": samples,
        "notes": "",
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    lines: list[str] = []
    lines.append("# Typecheck Report\n\n")
    lines.append(f"- generated_utc: {payload['generated_utc']}\n")
    lines.append(f"- status: {payload['status']}\n")
    lines.append(f"- mypy_version: {payload.get('mypy_version', 'unknown')}\n")
    lines.append(f"- output_dir: {payload['output_dir']}\n")
    lines.append("\n## Summary\n\n")
    lines.append("| Metric | Value |\n")
    lines.append("|---|---:|\n")
    lines.append(f"| error_count | {summary.get('error_count', 0)} |\n")
    lines.append(f"| files_with_issues | {summary.get('files_with_issues', 0)} |\n")
    lines.append(f"| paths_checked | {len(summary.get('paths_checked', []))} |\n")
    lines.append("\n## Sample Errors\n\n")
    samples = payload.get("error_samples", [])
    if not samples:
        lines.append("(none)\n")
    else:
        for sample in samples[:20]:
            code = sample.get("code")
            fragment = f"[{code}] " if code else ""
            lines.append(
                f"- {sample.get('path')}:{sample.get('line')} — {fragment}{sample.get('message')}\n"
            )
    lines.append("\n## Invocation\n\n")
    command = payload.get("invocation", [])
    if command:
        pretty = " ".join(part if " " not in part else f'"{part}"' for part in command)
        lines.append(f"`{pretty}`\n")
    else:
        lines.append("(unknown)\n")
    return "".join(lines)


def _render_log(payload: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    return "\n".join(
        [
            f"status={payload['status']}",
            f"timestamp={payload['timestamp']}",
            f"error_count={summary.get('error_count', 0)}",
            f"files_with_issues={summary.get('files_with_issues', 0)}",
            f"paths_checked={len(summary.get('paths_checked', []))}",
            f"mypy_version={payload.get('mypy_version', 'unknown')}",
        ]
    ) + "\n"


def _write_artifacts(
    *,
    run_dir: Path,
    payload: dict[str, Any],
    stdout_combined: str,
) -> tuple[Path, Path, Path, Path]:
    report_json = run_dir / "report.json"
    report_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    report_md = run_dir / "report.md"
    report_md.write_text(_render_markdown(payload), encoding="utf-8")

    log_txt = run_dir / "log.txt"
    log_txt.write_text(_render_log(payload), encoding="utf-8")

    raw_txt = run_dir / "raw.txt"
    raw_txt.write_text(stdout_combined, encoding="utf-8")

    return report_json, report_md, log_txt, raw_txt


def _copy_latest(src: Path, dest: Path) -> None:
    try:
        if dest.exists():
            dest.unlink()
        dest.hardlink_to(src)
    except OSError:
        dest.write_bytes(src.read_bytes())


def _update_latest(paths: list[tuple[Path, Path]]) -> None:
    for src, dest in paths:
        _copy_latest(src, dest)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run mypy and emit structured artifacts for typecheck monitoring",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT), help="Repository root used to resolve paths")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where structured artifacts will be written",
    )
    parser.add_argument("--timestamp", help="ISO8601 timestamp to seed the run directory")
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="Number of historical runs to retain")
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.log_level)

    repo_root = Path(args.repo_root).resolve()
    output_dir = _ensure_dir(_resolve_path(repo_root, args.output_dir))

    if args.timestamp:
        try:
            generated_at = datetime.fromisoformat(args.timestamp)
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=timezone.utc)
        except ValueError:
            generated_at = _current_utc()
    else:
        generated_at = _current_utc()

    run_slug = _format_slug(generated_at)
    run_dir = _prepare_run_dir(output_dir, run_slug)

    targets = _discover_targets(repo_root)
    strict = _env_bool("TYPECHECK_STRICT")
    fast = _env_bool("HEALTH_TYPECHECK_FAST")
    override_present = bool(os.getenv("TYPECHECK_TARGETS", "").strip())
    if fast and not override_present:
        targets = _filter_fast_targets(repo_root, targets)

    mypy_version = _get_mypy_version(repo_root)
    invocation = _build_invocation(strict, targets)
    stdout_combined, return_code = _run_mypy(repo_root, invocation)

    total_errors, files_with_issues, success_flag = _parse_summary(stdout_combined)
    samples = _parse_samples(stdout_combined)
    if not success_flag and total_errors == 0:
        total_errors = len(samples)
        files_with_issues = len({sample.path for sample in samples})

    status = _compute_status(success_flag, total_errors, files_with_issues, return_code)

    stats = BuildStats(
        status=status,
        error_count=total_errors,
        files_with_issues=files_with_issues,
        paths_checked=targets,
        invocation=invocation,
        mypy_version=mypy_version,
        samples=samples,
    )

    payload = _compose_payload(
        run_slug=run_slug,
        generated_at=generated_at,
        repo_root=repo_root,
        run_dir=run_dir,
        status=status,
        stats=stats,
    )

    report_json, report_md, log_txt, raw_txt = _write_artifacts(
        run_dir=run_dir,
        payload=payload,
        stdout_combined=stdout_combined,
    )

    latest_mappings = [
        (report_json, output_dir / "latest_report.json"),
        (report_md, output_dir / "latest_report.md"),
        (log_txt, output_dir / "latest_report.log"),
        (raw_txt, output_dir / "latest_raw.txt"),
    ]
    _update_latest(latest_mappings)

    prune_old_runs(output_dir, keep=args.artifacts_to_keep, current_run=run_dir)

    logging.info(
        "Typecheck status=%s errors=%d files=%d", status, total_errors, files_with_issues
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
