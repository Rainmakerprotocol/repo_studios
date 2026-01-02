#!/usr/bin/env python3
"""Refresh mypy baselines and emit structured artifacts."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Sequence

import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports/rawview/mypy_baselines")
RUN_STEM = "mypy_baselines"
SCHEMA_VERSION = 1

LIBRARIES_ROOT = PROJECT_ROOT / ".repo_studios" / "command_center" / "scripts"

try:  # pragma: no cover - preferred import when executed via orchestrators
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        copy_latest_artifact,
        write_report_artifacts,
    )
    from libraries.retention_policy import get_keep  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (  # type: ignore
        KeepSpec,
        OptionsConfig,
        PathSpec,
        PathsConfig,
        ReportArtifact,
        build_standard_options,
        build_standard_paths,
        copy_latest_artifact,
        write_report_artifacts,
    )
    from libraries.retention_policy import get_keep  # type: ignore

DEFAULT_ARTIFACTS_TO_KEEP = get_keep("refresh_mypy_baselines")


@dataclass(frozen=True)
class TargetSpec:
    label: str
    mypy_arg: str
    filename: str


DEFAULT_TARGETS: tuple[TargetSpec, ...] = (
    TargetSpec(label="agents_full", mypy_arg="agents", filename="mypy_agents_full.txt"),
    TargetSpec(label="monitoring_full", mypy_arg="agents/core/monitoring", filename="mypy_monitoring_full.txt"),
)


class Paths(NamedTuple):
    repo_root: Path
    output_dir: Path


class Options(NamedTuple):
    artifacts_to_keep: int
    append_timestamp: bool
    log_level: str
    timestamp: str | None
    targets: tuple[TargetSpec, ...]


PATH_SPECS: dict[str, PathSpec] = {
    "output_dir": PathSpec(field="output_dir", default=DEFAULT_OUTPUT_DIR, ensure_dir=True, within_repo=True),
}


KEEP_SPECS: dict[str, KeepSpec] = {
    "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
}


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)


class _KeepOptions(NamedTuple):
    artifacts_to_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=_KeepOptions,
    keep_specs=KEEP_SPECS,
)


class TargetOutcome(NamedTuple):
    spec: TargetSpec
    command: list[str]
    output: str
    exit_code: int
    duration_seconds: float

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


def _utc_now() -> datetime:
    try:
        return datetime.now(datetime.UTC)  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - Python <3.11
        return datetime.now(timezone.utc)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return _utc_now()
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - defensive validation
        raise SystemExit(f"Invalid --timestamp value: {raw!r}") from exc
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _parse_target_override(raw: str) -> TargetSpec:
    if "=" not in raw:
        raise SystemExit("--target must be formatted as label=path[:filename]")
    label, remainder = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise SystemExit("--target label cannot be empty")
    if ":" in remainder:
        mypy_arg, filename = remainder.split(":", 1)
    else:
        mypy_arg = remainder
        filename = f"mypy_{label}.txt"
    mypy_arg = mypy_arg.strip()
    filename = filename.strip() or f"mypy_{label}.txt"
    if not mypy_arg:
        raise SystemExit("--target requires a mypy path after '='")
    return TargetSpec(label=label, mypy_arg=mypy_arg, filename=filename)


def _parse_targets(raw_values: Iterable[str] | None) -> tuple[TargetSpec, ...]:
    if not raw_values:
        return DEFAULT_TARGETS
    parsed = tuple(_parse_target_override(value.strip()) for value in raw_values if value.strip())
    if not parsed:
        return DEFAULT_TARGETS
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh mypy baselines and emit structured artifacts",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root used to resolve paths. If omitted, auto-discovers by scanning parents for the "
            "'.repo_studios' marker directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where baseline bundles will be written",
    )
    parser.add_argument(
        "--target",
        action="append",
        help="Override target definition (label=path[:filename])",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical runs to retain",
    )
    parser.add_argument("--timestamp", help="ISO-8601 timestamp for the run; defaults to current UTC time")
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity for stdout")
    parser.add_argument(
        "--append-timestamp",
        dest="append_timestamp",
        action="store_true",
        help="Append '# Refreshed: <timestamp>' to baseline files",
    )
    parser.add_argument(
        "--no-append-timestamp",
        dest="append_timestamp",
        action="store_false",
        help="Do not append timestamp markers to baseline files",
    )
    parser.set_defaults(append_timestamp=True)
    return parser


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATH_CONFIG, origin=Path(__file__))


def build_options(args: argparse.Namespace) -> Options:
    base_keep = build_standard_options(args, OPTIONS_CONFIG)
    artifacts_to_keep = getattr(base_keep, "artifacts_to_keep", DEFAULT_ARTIFACTS_TO_KEEP)
    targets = _parse_targets(getattr(args, "target", None))
    append_timestamp = bool(getattr(args, "append_timestamp", True))
    log_level = str(getattr(args, "log_level", "INFO"))
    timestamp = getattr(args, "timestamp", None)
    return Options(
        artifacts_to_keep=int(artifacts_to_keep),
        append_timestamp=append_timestamp,
        log_level=log_level,
        timestamp=timestamp,
        targets=targets,
    )


def _build_invocation(target: TargetSpec) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--hide-error-context",
        "--no-error-summary",
    ]
    cmd.append(target.mypy_arg)
    return cmd


def _invoke_mypy(repo_root: Path, command: Sequence[str]) -> tuple[str, int]:
    try:
        proc = subprocess.run(  # type: ignore[name-defined]
            list(command),
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if stderr:
            stdout = stdout + ("\n" if stdout else "") + stderr
        return stdout, int(proc.returncode)
    except FileNotFoundError as exc:  # pragma: no cover - defensive
        return f"[mypy-baseline] mypy not found: {exc}", 127
    except Exception as exc:  # pragma: no cover - defensive
        return f"[mypy-baseline] unexpected error: {exc!r}", 1


def _run_target(target: TargetSpec, repo_root: Path) -> TargetOutcome:
    command = _build_invocation(target)
    start = time.monotonic()
    output, exit_code = _invoke_mypy(repo_root, command)
    duration = time.monotonic() - start
    return TargetOutcome(spec=target, command=list(command), output=output, exit_code=exit_code, duration_seconds=duration)


def _summary_status(outcomes: Sequence[TargetOutcome]) -> str:
    return "ok" if all(outcome.succeeded for outcome in outcomes) else "error"


def _render_markdown(summary: dict[str, Any], outcomes: Sequence[TargetOutcome]) -> str:
    lines: list[str] = []
    lines.append("# mypy Baseline Refresh\n\n")
    lines.append(f"- generated_utc: {summary['generated_utc']}\n")
    lines.append(f"- status: {summary['status']}\n")
    lines.append(f"- repo_root: {summary['repo_root']}\n")
    lines.append("\n## Targets\n\n")
    lines.append("| Label | Mypy Path | Exit Code | Duration (s) | Latest Pointer |\n")
    lines.append("| --- | --- | ---: | ---: | --- |\n")
    for outcome in outcomes:
        targets_meta = summary["targets_meta"]  # type: ignore[index]
        pointer = targets_meta[outcome.spec.label]["latest_pointer"]
        lines.append(
            f"| {outcome.spec.label} | {outcome.spec.mypy_arg} | {outcome.exit_code} | "
            f"{outcome.duration_seconds:.2f} | {pointer or '(none)'} |\n"
        )
    return "".join(lines)


def _build_summary(
    *,
    outcomes: Sequence[TargetOutcome],
    generated_at: datetime,
    repo_root: Path,
    run_slug: str,
    append_timestamp: bool,
    output_dir: Path,
) -> dict[str, Any]:
    meta: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        pointer_name = f"latest_{outcome.spec.filename}"
        pointer_path = output_dir / pointer_name
        meta[outcome.spec.label] = {
            "filename": outcome.spec.filename,
            "command": outcome.command,
            "exit_code": outcome.exit_code,
            "duration_seconds": round(outcome.duration_seconds, 3),
            "latest_pointer": str(pointer_path) if pointer_path.exists() else None,
            "append_timestamp": append_timestamp,
        }
    status = _summary_status(outcomes)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "run_slug": run_slug,
        "generated_utc": generated_at.isoformat(),
        "repo_root": str(repo_root),
        "append_timestamp": append_timestamp,
        "targets_meta": meta,
    }


def _build_status_payload(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": summary["status"],
        "generated_utc": summary["generated_utc"],
        "run_slug": summary["run_slug"],
        "targets": [
            {
                "label": label,
                "filename": data["filename"],
                "exit_code": data["exit_code"],
                "latest_pointer": data["latest_pointer"],
            }
            for label, data in summary["targets_meta"].items()  # type: ignore[union-attr]
        ],
    }


def _build_artifacts(
    *,
    outcomes: Sequence[TargetOutcome],
    summary: dict[str, Any],
    status_payload: dict[str, Any],
    append_timestamp: bool,
    generated_at: datetime,
) -> list[ReportArtifact]:
    timestamp_marker = f"\n# Refreshed: {generated_at.strftime('%Y-%m-%d_%H%M%S')}\n" if append_timestamp else ""
    artifacts: list[ReportArtifact] = [
        ReportArtifact(filename="bundle_summary.json", kind="json", content=lambda: summary, pointer="latest_bundle_summary.json"),
        ReportArtifact(filename="status.json", kind="json", content=lambda: status_payload, pointer="latest_status.json"),
        ReportArtifact(
            filename="SUMMARY.md",
            kind="text",
            content=lambda: _render_markdown(summary, outcomes),
            pointer="latest_SUMMARY.md",
        ),
    ]
    for outcome in outcomes:
        content = outcome.output + timestamp_marker if outcome.output else timestamp_marker
        artifacts.append(
            ReportArtifact(
                filename=outcome.spec.filename,
                kind="text",
                content=content,
            )
        )
        if not outcome.succeeded:
            err_name = f"{Path(outcome.spec.filename).stem}_error.txt"
            artifacts.append(
                ReportArtifact(
                    filename=err_name,
                    kind="text",
                    content=content or f"mypy failed for {outcome.spec.label}\n",
                )
            )
    return artifacts


def _update_latest_pointers(
    *,
    outcomes: Sequence[TargetOutcome],
    artifact_result,
    output_dir: Path,
) -> None:
    for outcome in outcomes:
        if not outcome.succeeded:
            continue
        src = artifact_result.artifacts.get(outcome.spec.filename)
        if not src:
            continue
        pointer = output_dir / f"latest_{outcome.spec.filename}"
        copy_latest_artifact(src, pointer)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)

    log_level = getattr(logging, options.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(message)s", force=True)

    generated_at = _parse_timestamp(options.timestamp)
    run_slug = generated_at.strftime("%Y%m%d_%H%M%S")

    logging.info("[mypy-baseline] repo_root=%s", paths.repo_root)
    logging.info("[mypy-baseline] output_dir=%s", paths.output_dir)

    outcomes: list[TargetOutcome] = []
    for spec in options.targets:
        logging.info("[mypy-baseline] running %s -> %s", spec.mypy_arg, spec.filename)
        outcome = _run_target(spec, paths.repo_root)
        outcomes.append(outcome)
        logging.log(logging.DEBUG if outcome.succeeded else logging.WARNING, "[mypy-baseline] exit=%s", outcome.exit_code)

    summary = _build_summary(
        outcomes=outcomes,
        generated_at=generated_at,
        repo_root=paths.repo_root,
        run_slug=run_slug,
        append_timestamp=options.append_timestamp,
        output_dir=paths.output_dir,
    )
    status_payload = _build_status_payload(summary)

    artifacts = _build_artifacts(
        outcomes=outcomes,
        summary=summary,
        status_payload=status_payload,
        append_timestamp=options.append_timestamp,
        generated_at=generated_at,
    )

    result = write_report_artifacts(
        stem=RUN_STEM,
        timestamp=generated_at,
        output_dir=paths.output_dir,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
    )

    _update_latest_pointers(outcomes=outcomes, artifact_result=result, output_dir=paths.output_dir)

    targets_meta = summary["targets_meta"]  # type: ignore[index]
    for outcome in outcomes:
        pointer = paths.output_dir / f"latest_{outcome.spec.filename}"
        targets_meta[outcome.spec.label]["latest_pointer"] = str(pointer) if pointer.exists() else None

    summary["run_dir"] = str(result.run_dir)
    summary["artifacts"] = {name: str(path) for name, path in result.artifacts.items()}
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    run(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
