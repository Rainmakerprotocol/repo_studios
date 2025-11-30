#!/usr/bin/env python3
"""Generate automation dry-run artifacts (manifest, metrics, inputs, README)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

AUTOMATION_SCRIPT_RELATIVE = Path(".repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py")
DEFAULT_POST_RUN_MATRIX = Path("que_for_integration/refactor_library/phase_4/POST_RUN_TEST_MATRIX.md")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    output_dir: Path
    post_run_matrix: Path


@dataclass(frozen=True)
class Options:
    log_level: str
    keep: int | None


def _load_cli_module(script_path: Path, module_name: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_run_function(script_path: Path):
    if not script_path.exists():
        raise FileNotFoundError(f"Required script not found: {script_path}")
    module = _load_cli_module(script_path, "command_center.aggregators.generate_automation_manifest")
    run_fn = getattr(module, "run", None)
    if not callable(run_fn):  # pragma: no cover - defensive
        raise RuntimeError("generate_automation_manifest module does not expose run()")
    return module, run_fn


def _resolve_within_repo(repo_root: Path, candidate: str) -> Path:
    raw = Path(candidate)
    resolved = raw if raw.is_absolute() else repo_root / raw
    resolved = resolved.resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Path must reside within the repo root: {resolved}") from exc
    return resolved


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root (defaults to script ancestor)")
    parser.add_argument("--output-dir", help="Directory for automation run artifacts")
    parser.add_argument("--keep", type=int, help="Number of historical runs to retain (overrides manifest default)")
    parser.add_argument("--timestamp", help="ISO8601 timestamp for run directory naming (UTC if absent)")
    parser.add_argument("--run-id", required=True, help="Unique identifier for the automation run")
    parser.add_argument("--baseline-sha", required=True, help="Git commit SHA used as the automation baseline")
    parser.add_argument(
        "--target",
        dest="targets",
        action="append",
        required=True,
        help="Slugged target processed during the run (repeatable)",
    )
    parser.add_argument("--lines-touched", type=int, required=True, help="Total lines changed during the run")
    parser.add_argument("--files-changed", type=int, required=True, help="Count of files modified")
    parser.add_argument(
        "--duplicate-groups-resolved", type=int, required=True, help="Number of duplicate groups addressed"
    )
    parser.add_argument("--runtime-seconds", type=float, required=True, help="Wall-clock execution time for the run")
    parser.add_argument("--files-file", required=True, help="Path to JSON describing updated/skipped/conflicted files")
    parser.add_argument("--tests-file", required=True, help="Path to JSON describing executed test suites")
    parser.add_argument("--notes", default="", help="Optional operator notes to include in the manifest")
    parser.add_argument("--operator", help="Operator responsible for the run")
    parser.add_argument("--dry-run", action="store_true", help="Flag indicating the run emitted artifacts only")
    parser.add_argument("--guardrail-config", help="Path to guardrail configuration YAML to snapshot in the manifest")
    parser.add_argument(
        "--guardrail-override", action="store_true", help="Indicate whether guardrail override was used"
    )
    parser.add_argument("--manifest-schema-version", default="1.0", help="Schema version to embed in manifest")
    parser.add_argument("--metrics-schema-version", default="1.0", help="Schema version to embed in metrics summary")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument("--post-run-matrix", help="Path to post-run test matrix markdown file")
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    output_dir = _resolve_within_repo(
        repo_root, args.output_dir or ".repo_studios/command_center/reports"
    )
    matrix_candidate = args.post_run_matrix or str(DEFAULT_POST_RUN_MATRIX)
    post_run_matrix = _resolve_within_repo(repo_root, matrix_candidate)
    return Paths(repo_root=repo_root, output_dir=output_dir, post_run_matrix=post_run_matrix)


def build_options(args: argparse.Namespace) -> Options:
    keep = args.keep if args.keep is not None else None
    return Options(log_level=args.log_level, keep=keep)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s: %(message)s")


def _copy_input(src: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


def _write_readme(
    run_dir: Path,
    *,
    manifest_path: Path,
    metrics_path: Path,
    run_id: str,
    baseline_sha: str,
    dry_run: bool,
    notes: str,
    operator: str | None,
    inputs_dir: Path,
    post_run_required: Sequence[tuple[str, str]],
    post_run_conditional: Sequence[tuple[str, str]],
    matrix_reference: Path | None,
) -> Path:
    readme_path = run_dir / "README.md"
    lines = [
        "# Automation Dry-Run Bundle",
        "",
        f"- run_id: `{run_id}`",
        f"- baseline_sha: `{baseline_sha}`",
        f"- dry_run: `{str(dry_run).lower()}`",
        f"- manifest: `{manifest_path.relative_to(run_dir)}`",
        f"- metrics_summary: `{metrics_path.relative_to(run_dir)}`",
        f"- inputs: `{inputs_dir.relative_to(run_dir)}`",
    ]
    if operator:
        lines.append(f"- operator: `{operator}`")
    if notes:
        lines.extend(["", "## Notes", notes.strip()])
    if post_run_required or post_run_conditional:
        lines.extend(["", "## Post-Run Test Commands", ""])
        if post_run_required:
            lines.append("**Required suites:**")
            for label, command in post_run_required:
                lines.append(f"- {label}: `{command}`")
            lines.append("")
        if post_run_conditional:
            lines.append("**Conditional suites:**")
            for label, command in post_run_conditional:
                lines.append(f"- {label}: `{command}`")
            lines.append("")
        if matrix_reference:
            lines.append(f"Matrix reference: `{matrix_reference}`")
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


def _slug_from_timestamp(moment: datetime) -> str:
    normalized = moment.astimezone(timezone.utc)
    return normalized.strftime("%Y%m%d-%H%M")


def _trim_table_header(rows: Sequence[str]) -> Sequence[str]:
    if len(rows) >= 2 and rows[0].strip().startswith("|") and "---" in rows[1]:
        return rows[2:]
    return rows


def _parse_table_rows(rows: Iterable[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for row in rows:
        normalized = row.strip()
        if not normalized or normalized.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in normalized.strip("|").split("|")]
        if len(cells) < 2:
            continue
        label = cells[0]
        command = cells[1]
        if not label or not command:
            continue
        if command.startswith("`") and command.endswith("`"):
            command = command[1:-1]
        parsed.append((label, command))
    return parsed


def _load_post_run_matrix(matrix_path: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    if not matrix_path.exists():
        return [], []
    lines = matrix_path.read_text(encoding="utf-8").splitlines()
    required_rows: list[str] = []
    conditional_rows: list[str] = []
    current: list[str] | None = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            lower = stripped.lower()
            if lower.startswith("## required suites"):
                current = required_rows
            elif lower.startswith("## conditional suites"):
                current = conditional_rows
            else:
                current = None
            continue
        if current is None:
            continue
        if not stripped:
            current = None
            continue
        if stripped.startswith("|"):
            current.append(stripped)
            continue
        current = None

    required = _parse_table_rows(_trim_table_header(required_rows))
    conditional = _parse_table_rows(_trim_table_header(conditional_rows))
    return required, conditional


def _build_post_run_snapshot(
    required: Sequence[tuple[str, str]],
    conditional: Sequence[tuple[str, str]],
    matrix_reference: Path | None,
) -> dict[str, object] | None:
    if not required and not conditional and matrix_reference is None:
        return None
    snapshot: dict[str, object] = {}
    if matrix_reference is not None:
        snapshot["matrix_reference"] = matrix_reference.as_posix()
    if required:
        snapshot["required"] = [{"label": label, "command": command} for label, command in required]
    if conditional:
        snapshot["conditional"] = [{"condition": label, "command": command} for label, command in conditional]
    return snapshot


def _update_json_file(path: Path, mutator) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logging.warning("Expected JSON artifact missing: %s", path)
        return
    except json.JSONDecodeError as exc:  # pragma: no cover - safety net
        logging.error("Unable to parse JSON artifact %s: %s", path, exc)
        return

    changed = mutator(payload)
    if changed:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _embed_post_run_tests(
    manifest_path: Path,
    metrics_path: Path,
    snapshot: dict[str, object],
) -> None:
    def mutate_manifest(data: dict[str, object]) -> bool:
        changed = False
        if data.get("post_run_tests") != snapshot:
            data["post_run_tests"] = json.loads(json.dumps(snapshot))
            changed = True
        metrics_section = data.get("metrics_summary")
        if isinstance(metrics_section, dict):
            if metrics_section.get("post_run_tests") != snapshot:
                metrics_section["post_run_tests"] = json.loads(json.dumps(snapshot))
                changed = True
        return changed

    def mutate_metrics(data: dict[str, object]) -> bool:
        if data.get("post_run_tests") == snapshot:
            return False
        data["post_run_tests"] = json.loads(json.dumps(snapshot))
        return True

    _update_json_file(manifest_path, mutate_manifest)
    _update_json_file(metrics_path, mutate_metrics)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging(options.log_level)

    try:
        paths = build_paths(args)
    except ValueError as exc:
        logging.error("%s", exc)
        return 1

    files_file = _resolve_within_repo(paths.repo_root, args.files_file)
    tests_file = _resolve_within_repo(paths.repo_root, args.tests_file)
    guardrail_config = None
    if args.guardrail_config:
        guardrail_config = _resolve_within_repo(paths.repo_root, args.guardrail_config)

    timestamp = _parse_timestamp(args.timestamp)
    timestamp_iso = timestamp.isoformat()

    script_path = (paths.repo_root / AUTOMATION_SCRIPT_RELATIVE).resolve()
    try:
        module, run_fn = _load_run_function(script_path)
    except (FileNotFoundError, ImportError, RuntimeError) as exc:
        logging.error("%s", exc)
        return 1

    manifest_args: list[str] = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.output_dir),
        "--tests-file",
        str(tests_file),
        "--files-file",
        str(files_file),
        "--run-id",
        args.run_id,
        "--baseline-sha",
        args.baseline_sha,
        "--timestamp",
        timestamp_iso,
        "--lines-touched",
        str(args.lines_touched),
        "--files-changed",
        str(args.files_changed),
        "--duplicate-groups-resolved",
        str(args.duplicate_groups_resolved),
        "--runtime-seconds",
        str(args.runtime_seconds),
        "--notes",
        args.notes,
        "--log-level",
        options.log_level,
        "--manifest-schema-version",
        args.manifest_schema_version,
        "--metrics-schema-version",
        args.metrics_schema_version,
    ]
    if options.keep is not None:
        manifest_args.extend(["--keep", str(options.keep)])
    if args.operator:
        manifest_args.extend(["--operator", args.operator])
    if args.dry_run:
        manifest_args.append("--dry-run")
    if guardrail_config:
        manifest_args.extend(["--guardrail-config", str(guardrail_config)])
    if args.guardrail_override:
        manifest_args.append("--guardrail-override")
    for target in args.targets:
        manifest_args.extend(["--target", target])

    exit_code = int(run_fn(manifest_args))
    if exit_code != 0:
        logging.error("generate_automation_manifest failed with exit code %d", exit_code)
        return exit_code

    slug = _slug_from_timestamp(timestamp)
    viewer = getattr(module, "VIEWER_SLUG", "commandview")
    topic = getattr(module, "TOPIC_SLUG", module.RUN_STEM)
    run_dir = paths.output_dir / viewer / topic / slug
    if not run_dir.exists():
        logging.error("Expected automation run directory not found: %s", run_dir)
        return 1

    manifest_path = run_dir / module.MANIFEST_FILENAME
    metrics_path = run_dir / module.METRICS_FILENAME
    if not manifest_path.exists() or not metrics_path.exists():
        logging.error("Automation manifest or metrics summary missing in %s", run_dir)
        return 1

    required_post_run, conditional_post_run = _load_post_run_matrix(paths.post_run_matrix)

    inputs_dir = run_dir / "inputs"
    copied_files = {
        "files": _copy_input(files_file, inputs_dir),
        "tests": _copy_input(tests_file, inputs_dir),
    }
    if guardrail_config:
        copied_files["guardrail"] = _copy_input(guardrail_config, inputs_dir)
    matrix_copy: Path | None = None
    if paths.post_run_matrix.exists():
        matrix_copy = _copy_input(paths.post_run_matrix, inputs_dir)
        copied_files["post_run_matrix"] = matrix_copy

    matrix_relative: Path | None = None
    if matrix_copy:
        matrix_relative = matrix_copy.relative_to(run_dir)

    post_run_snapshot = _build_post_run_snapshot(
        required_post_run,
        conditional_post_run,
        matrix_relative,
    )
    if post_run_snapshot:
        _embed_post_run_tests(manifest_path, metrics_path, post_run_snapshot)

    readme_path = _write_readme(
        run_dir,
        manifest_path=manifest_path,
        metrics_path=metrics_path,
        run_id=args.run_id,
        baseline_sha=args.baseline_sha,
        dry_run=bool(args.dry_run),
        notes=args.notes,
        operator=args.operator,
        inputs_dir=inputs_dir,
        post_run_required=required_post_run,
        post_run_conditional=conditional_post_run,
        matrix_reference=matrix_relative,
    )

    logging.info("Automation dry-run bundle created at %s", run_dir)
    logging.info("Manifest: %s", manifest_path)
    logging.info("Metrics summary: %s", metrics_path)
    logging.debug("Inputs copied: %s", copied_files)
    logging.debug("README: %s", readme_path)
    if required_post_run or conditional_post_run:
        logging.debug("Post-run required suites: %s", required_post_run)
        logging.debug("Post-run conditional suites: %s", conditional_post_run)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))


__all__ = [
    "run",
    "main",
    "parse_args",
    "build_paths",
    "build_options",
]
