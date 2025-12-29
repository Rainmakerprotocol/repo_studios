"""Run mypy and emit structured artifacts for the typecheck producer.

Artifacts (default):
    - `.repo_studios/reports/producer_reports/healthview/typecheck_report/<YYYYMMDD-HHMM>/`
        - `manifest.json`
        - `summary.md`
        - `telemetry.json`
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple, cast

try:  # pragma: no cover - Python 3.11+
    import tomllib
except Exception:  # pragma: no cover - fallback if unavailable
    tomllib = None  # type: ignore[assignment]


DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports")
RUN_PREFIX = "typecheck"  # legacy label; run directories now live under viewer/topic.
DEFAULT_ARTIFACTS_TO_KEEP = get_keep("generate_typecheck_report")
SCHEMA_VERSION = 1

VIEWER_SLUG = "healthview"
TOPIC_SLUG = "typecheck_report"

LIBRARIES_ROOT = DEFAULT_REPO_ROOT / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when executed directly
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
    from libraries.retention_policy import get_keep


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
    files_checked: int
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
    return moment.strftime("%Y%m%d-%H%M")


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


def _normalise_targets(targets: list[str]) -> list[str]:
    normalised: list[str] = []
    for entry in targets:
        token = entry.strip()
        if not token:
            continue
        normalised.append(token)
    return normalised


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


def _parse_checked_files(stdout: str) -> int | None:
    ok_match = re.search(r"^Success: no issues found in (\d+) source files?", stdout, flags=re.M)
    if ok_match:
        try:
            return int(ok_match.group(1))
        except Exception:  # pragma: no cover - defensive
            return None
    checked_match = re.search(r"\(checked (\d+) source files?\)", stdout)
    if checked_match:
        try:
            return int(checked_match.group(1))
        except Exception:  # pragma: no cover - defensive
            return None
    return None


def _should_exclude_relpath(relpath: Path) -> bool:
    parts = relpath.parts
    if not parts:
        return False
    first = parts[0]
    if first in {"legacy", ".venv"}:
        return True
    if first.startswith("tmp_"):
        return True
    if parts[0] == ".repo_studios" and len(parts) >= 2 and parts[1] == "reports":
        return True
    if relpath.name.startswith("tmp_"):
        return True
    return False


def _discover_all_python_files(repo_root: Path) -> list[str]:
    files: list[str] = []
    for candidate in repo_root.rglob("*.py"):
        try:
            rel = candidate.relative_to(repo_root)
        except Exception:  # pragma: no cover - defensive
            continue
        if _should_exclude_relpath(rel):
            continue
        files.append(rel.as_posix())
    files.sort()
    return files


def _chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
    if chunk_size <= 0:
        return [items]
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def _partition_all_targets(all_files: list[str]) -> list[tuple[str, list[str]]]:
    repo_files: list[str] = []
    studio_files: list[str] = []
    command_center_files: list[str] = []

    for path in all_files:
        if path.startswith(".repo_studios/command_center/"):
            command_center_files.append(path)
        elif path.startswith(".repo_studios/"):
            studio_files.append(path)
        else:
            repo_files.append(path)

    partitions: list[tuple[str, list[str]]] = []
    if repo_files:
        partitions.append(("repo", repo_files))
    if studio_files:
        partitions.append(("repo_studios", studio_files))
    if command_center_files:
        partitions.append(("command_center", command_center_files))
    return partitions


def _parse_samples(stdout: str, limit: int = 50) -> list[ErrorSample]:
    pattern = re.compile(r"^(?P<path>[^:\n]+):(?P<line>\d+):(?:\d+:)?\s+error: (?P<msg>.*?)(?: \[(?P<code>[^\]]+)\])?$")
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
    reports_root: Path,
    topic_dir: Path,
    bundle_dir: Path,
    status: str,
    stats: BuildStats,
    files_checked_by_partition: dict[str, int] | None = None,
) -> dict[str, Any]:
    summary = {
        "error_count": stats.error_count,
        "files_with_issues": stats.files_with_issues,
        "files_checked": stats.files_checked,
        "paths_checked": stats.paths_checked,
    }
    if files_checked_by_partition:
        summary["files_checked_by_partition"] = dict(files_checked_by_partition)
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
        "viewer_slug": VIEWER_SLUG,
        "topic": TOPIC_SLUG,
        "status": status,
        "run_timestamp": run_slug,
        "generated_utc": generated_at.isoformat(),
        "repo_root": str(repo_root),
        "reports_root": str(reports_root),
        "topic_dir": str(topic_dir),
        "bundle_dir": str(bundle_dir),
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
    lines.append(f"- bundle_dir: {payload.get('bundle_dir', '')}\n")
    lines.append("\n## Summary\n\n")
    lines.append("| Metric | Value |\n")
    lines.append("|---|---:|\n")
    lines.append(f"| error_count | {summary.get('error_count', 0)} |\n")
    lines.append(f"| files_with_issues | {summary.get('files_with_issues', 0)} |\n")
    lines.append(f"| files_checked | {summary.get('files_checked', 0)} |\n")
    partition_checked = summary.get("files_checked_by_partition")
    if isinstance(partition_checked, dict) and partition_checked:
        for label in sorted(partition_checked):
            try:
                value = int(partition_checked.get(label, 0) or 0)
            except Exception:
                value = 0
            safe_label = str(label).replace("-", "_")
            lines.append(f"| files_checked_{safe_label} | {value} |\n")
    lines.append(f"| paths_checked | {len(summary.get('paths_checked', []))} |\n")
    lines.append("\n## Sample Errors\n\n")
    samples = payload.get("error_samples", [])
    if not samples:
        lines.append("(none)\n")
    else:
        for sample in samples[:20]:
            code = sample.get("code")
            fragment = f"[{code}] " if code else ""
            lines.append(f"- {sample.get('path')}:{sample.get('line')} — {fragment}{sample.get('message')}\n")
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
    partition_checked = summary.get("files_checked_by_partition")
    extra_lines: list[str] = []
    if isinstance(partition_checked, dict) and partition_checked:
        for label in sorted(partition_checked):
            safe_label = str(label).replace("-", "_")
            try:
                value = int(partition_checked.get(label, 0) or 0)
            except Exception:
                value = 0
            extra_lines.append(f"files_checked_{safe_label}={value}")
    return (
        "\n".join(
            [
                f"status={payload['status']}",
                f"run_timestamp={payload.get('run_timestamp', '')}",
                f"error_count={summary.get('error_count', 0)}",
                f"files_with_issues={summary.get('files_with_issues', 0)}",
                f"files_checked={summary.get('files_checked', 0)}",
                *extra_lines,
                f"paths_checked={len(summary.get('paths_checked', []))}",
                f"mypy_version={payload.get('mypy_version', 'unknown')}",
            ]
        )
        + "\n"
    )


def _build_manifest(
    *,
    payload: dict[str, Any],
    strict: bool,
    fast: bool,
    return_code: int,
    raw_output: str,
    rendered_log: str,
) -> dict[str, Any]:
    manifest: dict[str, Any] = dict(payload)
    manifest.update(
        {
            "strict": strict,
            "fast_mode": fast,
            "return_code": return_code,
            "log": rendered_log,
            "raw_output": raw_output,
        }
    )
    return manifest


def _build_telemetry(
    *,
    payload: dict[str, Any],
    strict: bool,
    fast: bool,
    return_code: int,
) -> dict[str, Any]:
    summary = payload.get("summary", {})
    files_checked_by_partition = summary.get("files_checked_by_partition")
    extra_metrics: dict[str, int] = {}
    if isinstance(files_checked_by_partition, dict) and files_checked_by_partition:
        for label, value in files_checked_by_partition.items():
            safe_label = str(label).replace("-", "_")
            try:
                extra_metrics[f"files_checked_{safe_label}"] = int(value or 0)
            except Exception:
                extra_metrics[f"files_checked_{safe_label}"] = 0
    return {
        "viewer_slug": payload.get("viewer_slug"),
        "topic": payload.get("topic"),
        "run_timestamp": payload.get("run_timestamp"),
        "generated_utc": payload.get("generated_utc"),
        "metrics": {
            "status": payload.get("status"),
            "error_count": int(summary.get("error_count", 0) or 0),
            "files_with_issues": int(summary.get("files_with_issues", 0) or 0),
            "files_checked": int(summary.get("files_checked", 0) or 0),
            **extra_metrics,
            "paths_checked": len(summary.get("paths_checked", []) or []),
            "strict": bool(strict),
            "fast_mode": bool(fast),
            "return_code": int(return_code),
        },
        "payload": {
            "mypy_version": payload.get("mypy_version"),
            "invocation": payload.get("invocation"),
        },
    }


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run mypy and emit structured artifacts for typecheck monitoring",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", help="Repository root used to resolve paths")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Typecheck all discovered Python files in the repository (batched)",
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        help="Explicit mypy targets (overrides TYPECHECK_TARGETS and pyproject defaults)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where structured artifacts will be written",
    )
    parser.add_argument("--timestamp", help="ISO8601 timestamp to seed the run directory")
    parser.add_argument(
        "--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="Number of historical runs to retain"
    )
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity")
    return parser


class Paths(NamedTuple):
    repo_root: Path
    output_dir: Path


class Options(NamedTuple):
    artifacts_to_keep: int
    timestamp: str | None = None
    log_level: str = "INFO"


PATH_SPECS: dict[str, PathSpec] = {
    "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=False),
}


KEEP_SPECS: dict[str, KeepSpec] = {
    "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
}


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs=KEEP_SPECS,
)


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace) -> Options:
    base_options = cast(Options, build_standard_options(args, OPTIONS_CONFIG))
    return cast(
        Options,
        base_options._replace(
        timestamp=getattr(args, "timestamp", None),
        log_level=str(getattr(args, "log_level", "INFO")),
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    repo_root = paths.repo_root
    output_dir = paths.output_dir

    timestamp_arg = options.timestamp
    if timestamp_arg:
        try:
            generated_at = datetime.fromisoformat(timestamp_arg)
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=timezone.utc)
        except ValueError:
            generated_at = _current_utc()
    else:
        generated_at = _current_utc()

    run_slug = _format_slug(generated_at)
    topic_dir = output_dir / VIEWER_SLUG / TOPIC_SLUG

    explicit_targets: list[str] | None = None
    all_mode = bool(getattr(args, "all", False))
    if all_mode:
        explicit_targets = ["."]
    else:
        raw_targets = getattr(args, "targets", None)
        if isinstance(raw_targets, list):
            explicit_targets = [str(entry) for entry in raw_targets]

    if explicit_targets is not None:
        targets = _normalise_targets(explicit_targets)
    else:
        targets = _discover_targets(repo_root)
        targets = _normalise_targets(targets)
    strict = _env_bool("TYPECHECK_STRICT")
    fast = _env_bool("HEALTH_TYPECHECK_FAST")
    override_present = explicit_targets is not None or bool(os.getenv("TYPECHECK_TARGETS", "").strip())
    if fast and not override_present:
        targets = _filter_fast_targets(repo_root, targets)
    targets = _normalise_targets(list(dict.fromkeys(targets)))

    mypy_version = _get_mypy_version(repo_root)
    invocation = _build_invocation(strict, targets)
    if all_mode:
        base = _build_invocation(strict, [])
        invocation = base + ["<all python files (batched)>"]

    skipped_note = ""
    stdout_combined = ""
    return_code = 0
    total_errors = 0
    files_with_issues = 0
    files_checked = 0
    files_checked_by_partition: dict[str, int] = {}
    success_flag = True
    samples: list[ErrorSample] = []
    status = "skipped"

    if targets:
        if all_mode:
            all_files = _discover_all_python_files(repo_root)
            if not all_files:
                stdout_combined = "No Python files discovered for --all; skipping mypy execution.\n"
                skipped_note = "No Python files discovered for --all; skipping mypy execution."
                status = "skipped"
            else:
                aggregated_output: list[str] = []
                aggregated_samples: list[ErrorSample] = []
                aggregated_return_code = 0
                aggregated_success = True
                aggregated_errors = 0
                aggregated_files_with_issues = 0
                aggregated_files_checked = 0

                partitions = _partition_all_targets(all_files)
                chunk_size = 100
                for label, partition_files in partitions:
                    partition_checked = 0
                    chunks = _chunk_list(partition_files, chunk_size)
                    for index, batch in enumerate(chunks, start=1):
                        batch_invocation = _build_invocation(strict, batch)
                        batch_stdout, batch_rc = _run_mypy(repo_root, batch_invocation)
                        aggregated_return_code = max(aggregated_return_code, batch_rc)

                        aggregated_output.append(
                            f"--- {label} batch {index}/{len(chunks)} ({len(batch)} files) ---"
                        )
                        aggregated_output.append(batch_stdout.rstrip())

                        batch_errors, batch_files, batch_success = _parse_summary(batch_stdout)
                        batch_checked = _parse_checked_files(batch_stdout)
                        if batch_checked is not None:
                            aggregated_files_checked += batch_checked
                            partition_checked += batch_checked
                        else:
                            aggregated_files_checked += len(batch)
                            partition_checked += len(batch)

                        batch_samples = _parse_samples(batch_stdout)
                        if not batch_success and batch_errors == 0:
                            batch_errors = len(batch_samples)
                            batch_files = len({sample.path for sample in batch_samples})

                        aggregated_errors += batch_errors
                        aggregated_files_with_issues += batch_files
                        aggregated_samples.extend(batch_samples)

                        aggregated_success = aggregated_success and batch_success and batch_rc == 0

                    files_checked_by_partition[label] = partition_checked

                stdout_combined = "\n\n".join(aggregated_output) + "\n"
                if len(stdout_combined) > 200_000:
                    stdout_combined = stdout_combined[:200_000] + "\n[TRUNCATED] Raw output exceeded 200k chars.\n"

                return_code = aggregated_return_code
                success_flag = aggregated_success
                total_errors = aggregated_errors
                files_with_issues = aggregated_files_with_issues
                files_checked = aggregated_files_checked
                samples = aggregated_samples[:50]
                status = _compute_status(success_flag, total_errors, files_with_issues, return_code)
        else:
            stdout_combined, return_code = _run_mypy(repo_root, invocation)
            missing_target = "Missing target module" in stdout_combined
            if return_code != 0 and missing_target:
                skipped_note = "mypy reported missing target module; treating run as skipped."
            else:
                total_errors, files_with_issues, success_flag = _parse_summary(stdout_combined)
                checked = _parse_checked_files(stdout_combined)
                if checked is not None:
                    files_checked = checked
                samples = _parse_samples(stdout_combined)
                if not success_flag and total_errors == 0:
                    total_errors = len(samples)
                    files_with_issues = len({sample.path for sample in samples})
                status = _compute_status(success_flag, total_errors, files_with_issues, return_code)
    else:
        stdout_combined = "No typecheck targets discovered; skipping mypy execution.\n"
        skipped_note = "No typecheck targets discovered; skipping mypy execution."

    stats = BuildStats(
        status=status,
        error_count=total_errors,
        files_with_issues=files_with_issues,
        files_checked=files_checked,
        paths_checked=targets,
        invocation=invocation,
        mypy_version=mypy_version,
        samples=samples,
    )

    storage = create_storage(output_dir, VIEWER_SLUG, TOPIC_SLUG, timestamp=run_slug)
    bundle_dir = storage.file_storage.bundle_dir

    payload = _compose_payload(
        run_slug=run_slug,
        generated_at=generated_at,
        repo_root=repo_root,
        reports_root=output_dir,
        topic_dir=topic_dir,
        bundle_dir=bundle_dir,
        status=status,
        stats=stats,
        files_checked_by_partition=(files_checked_by_partition or None),
    )
    if skipped_note:
        payload["notes"] = skipped_note
    rendered_log = _render_log(payload)
    markdown = _render_markdown(payload)

    manifest = _build_manifest(
        payload=payload,
        strict=strict,
        fast=fast,
        return_code=return_code,
        raw_output=stdout_combined,
        rendered_log=rendered_log,
    )
    telemetry = _build_telemetry(payload=payload, strict=strict, fast=fast, return_code=return_code)

    # DB_INTEGRATION_MARKER: typecheck manifest write
    storage.write_manifest(manifest)

    # DB_INTEGRATION_MARKER: typecheck summary markdown write
    storage.write_summary({"markdown": markdown}, format="md")

    # DB_INTEGRATION_MARKER: typecheck telemetry write
    storage.write_telemetry(telemetry)

    prune_run_directories(
        topic_dir,
        keep=options.artifacts_to_keep,
        current_run=bundle_dir,
        logger=logging.getLogger(__name__),
    )

    logging.info(
        "Typecheck run_dir=%s status=%s errors=%d files=%d",
        bundle_dir,
        status,
        total_errors,
        files_with_issues,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
