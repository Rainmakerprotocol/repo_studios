#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import time
import traceback
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TARGET_REL = Path("metrics_storage") / "storage"
DEFAULT_OUTPUT_BASE = Path(".repo_studios/reports/orchestrator_runs/run_batch_cleanup")
DEFAULT_ARTIFACTS_TO_KEEP = 5

RUFF_CONFIG = PROJECT_ROOT / ".repo_studios" / "ruff_clean.toml"
PROJECT_TREE_DOC_REL = Path(".repo_studios/docs/project_tree_overview.md")
MARKDOWNLINT_CONFIG = ".markdownlint.json"
MARKDOWN_GLOB = "**/*.md"
MYPY_TARGETS = ["mypy", "agents/core/monitoring", "agents/interface/chainlit"]
PYTEST_CMD = ["pytest", "-q"]


def ruff_format_cmd(targets: Sequence[Path]) -> list[str]:
    return ["ruff", "format", *[str(t) for t in targets], "--config", str(RUFF_CONFIG)]


def ruff_fix_cmd(targets: Sequence[Path]) -> list[str]:
    return ["ruff", "check", *[str(t) for t in targets], "--fix", "--config", str(RUFF_CONFIG)]


@dataclass
class CleanupOptions:
    targets: list[Path]
    mode: str
    dry_run: bool
    backup: bool
    refresh_only: bool
    skip_pytest: bool
    output_base: Path
    artifacts_to_keep: int
    log_level: str


@dataclass
class CommandResult:
    label: str
    command: list[str]
    status: str
    returncode: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    skipped_reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "command": self.command,
            "status": self.status,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "skipped_reason": self.skipped_reason,
        }


CommandExecutor = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orchestrate Ruff/Mypy/Pytest/Markdown cleanup with structured outputs"
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="targets",
        action="append",
        help="File or directory to clean (repeatable)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan commands without executing")
    parser.add_argument(
        "--mode",
        choices=["all", "markdown"],
        default=os.getenv("BATCH_CLEAN_ONLY", "all").lower(),
        help="Cleanup scope",
    )
    parser.add_argument("--backup", action="store_true", help="Backup .py files before modifying")
    parser.add_argument("--refresh-only", action="store_true", help="Just refresh the standards tree block")
    parser.add_argument("--no-pytest", action="store_true", help="Skip pytest even in all mode")
    parser.add_argument(
        "--output-base",
        help="Override output directory for structured bundles",
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of run bundles to retain",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity")
    parser.add_argument("--verbose", action="store_true", help="Shortcut for --log-level DEBUG")
    return parser.parse_args(argv)


def _resolve_targets(raw_targets: list[str] | None) -> list[Path]:
    env_targets = os.getenv("BATCH_CLEAN_TARGET_DIR") or os.getenv("BATCH_CLEAN_TARGETS")
    if raw_targets:
        candidates = raw_targets
    elif env_targets:
        candidates = [t.strip() for t in env_targets.split(",") if t.strip()]
    else:
        candidates = [str(DEFAULT_TARGET_REL)]
    resolved: list[Path] = []
    for candidate in candidates:
        path = Path(candidate)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        resolved.append(path)
    return resolved


def _resolve_output_base(base_arg: str | None) -> Path:
    base = Path(base_arg) if base_arg else DEFAULT_OUTPUT_BASE
    if not base.is_absolute():
        base = (PROJECT_ROOT / base).resolve()
    return base


def _prepare_options(args: argparse.Namespace) -> CleanupOptions:
    targets = _resolve_targets(args.targets)
    output_base = _resolve_output_base(args.output_base)
    skip_pytest_flag = args.no_pytest or os.getenv("BATCH_CLEAN_NO_PYTEST", "0") == "1"
    artifacts_to_keep = max(int(args.artifacts_to_keep or DEFAULT_ARTIFACTS_TO_KEEP), 1)
    log_level = "DEBUG" if args.verbose else str(args.log_level)
    return CleanupOptions(
        targets=targets,
        mode=str(args.mode or "all"),
        dry_run=bool(args.dry_run),
        backup=bool(args.backup),
        refresh_only=bool(args.refresh_only),
        skip_pytest=skip_pytest_flag,
        output_base=output_base,
        artifacts_to_keep=artifacts_to_keep,
        log_level=log_level,
    )


def _run_subprocess(cmd: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )


def _record_skip(label: str, reason: str, command: list[str] | None = None) -> CommandResult:
    return CommandResult(
        label=label,
        command=command or [],
        status="skipped",
        returncode=None,
        stdout="",
        stderr="",
        duration_seconds=0.0,
        skipped_reason=reason,
    )


def _execute_command(
    cmd: list[str],
    label: str,
    *,
    options: CleanupOptions,
    log_handle,
    executor: CommandExecutor,
) -> CommandResult:
    if options.dry_run:
        log_handle.write(f"\n--- {label} ---\n[dry-run] {' '.join(cmd)}\n")
        return _record_skip(label, "dry-run", cmd)
    start = time.monotonic()
    log_handle.write(f"\n--- {label} ---\n$ {' '.join(cmd)}\n")
    completed = executor(cmd)
    duration = time.monotonic() - start
    log_handle.write(completed.stdout)
    if completed.stderr:
        log_handle.write(completed.stderr)
    status = "success" if completed.returncode == 0 else "failed"
    if status == "failed":
        log_handle.write(f"[!] {label} exited with {completed.returncode}\n")
    return CommandResult(
        label=label,
        command=list(cmd),
        status=status,
        returncode=int(completed.returncode),
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=duration,
    )


def _run_markdownlint(
    *,
    options: CleanupOptions,
    log_handle,
    executor: CommandExecutor,
) -> tuple[list[CommandResult], str | None]:
    results: list[CommandResult] = []
    note: str | None = None
    if options.dry_run:
        result = _record_skip("markdownlint", "dry-run", [])
        log_handle.write("\n--- Markdownlint ---\n[dry-run]\n")
        return [result], note
    log_handle.write("\n--- Markdownlint ---\n")
    config_path = PROJECT_ROOT / MARKDOWNLINT_CONFIG
    if not config_path.exists():
        skip = _record_skip("markdownlint", "config missing", [])
        log_handle.write(f"Config not found at {config_path}; markdownlint skipped.\n")
        note = "markdownlint skipped (config missing)"
        return [skip], note
    npx_binary = shutil.which("npx.cmd") or shutil.which("npx.exe") or shutil.which("npx")
    if npx_binary:
        fix_cmd = [
            npx_binary,
            "--yes",
            "markdownlint-cli@0.39.0",
            MARKDOWN_GLOB,
            "--fix",
            "--config",
            str(config_path),
        ]
        check_cmd = [
            npx_binary,
            "--yes",
            "markdownlint-cli@0.39.0",
            MARKDOWN_GLOB,
            "--config",
            str(config_path),
        ]
        results.append(
            _execute_command(
                fix_cmd, "markdownlint --fix (npx)", options=options, log_handle=log_handle, executor=executor
            )
        )
        if results[-1].status == "failed":
            return results, note
        results.append(
            _execute_command(
                check_cmd, "markdownlint check (npx)", options=options, log_handle=log_handle, executor=executor
            )
        )
        return results, note
    markdownlint_binary = (
        shutil.which("markdownlint.cmd") or shutil.which("markdownlint.exe") or shutil.which("markdownlint")
    )
    if markdownlint_binary:
        fix_cmd = [
            markdownlint_binary,
            MARKDOWN_GLOB,
            "--fix",
            "--config",
            str(config_path),
        ]
        check_cmd = [
            markdownlint_binary,
            MARKDOWN_GLOB,
            "--config",
            str(config_path),
        ]
        results.append(
            _execute_command(fix_cmd, "markdownlint --fix", options=options, log_handle=log_handle, executor=executor)
        )
        if results[-1].status == "failed":
            return results, note
        results.append(
            _execute_command(check_cmd, "markdownlint check", options=options, log_handle=log_handle, executor=executor)
        )
        return results, note
    skip = _record_skip("markdownlint", "Tooling not available", [])
    log_handle.write("Tooling unavailable; markdownlint skipped.\n")
    note = "markdownlint skipped (tooling unavailable)"
    return [skip], note


def _refresh_project_tree(log_handle, root_dir: Path) -> dict[str, object]:
    doc_path = (root_dir / PROJECT_TREE_DOC_REL).resolve()
    metadata = {
        "markdown_path": str(doc_path.resolve()),
        "root": str(root_dir.resolve()),
        "updated": False,
        "found_markers": False,
    }
    if not doc_path.exists():
        log_handle.write(f"\n--- Refresh project tree ---\nMissing file: {doc_path}\n")
        return metadata

    text = doc_path.read_text(encoding="utf-8")
    start = text.find("<!-- tree:begin -->")
    end = text.find("<!-- tree:end -->")
    if start == -1 or end == -1 or end < start:
        log_handle.write("\n--- Refresh project tree ---\nMarkers not found; skipping refresh.\n")
        metadata["found_markers"] = False
        return metadata
    metadata["found_markers"] = True

    def _children(path: Path) -> list[Path]:
        try:
            entries = list(path.iterdir())
        except Exception:
            return []

        allowed: list[Path] = []
        for candidate in entries:
            if candidate.name.startswith(".") and candidate.name != ".repo_studios":
                continue
            allowed.append(candidate)
        return sorted(allowed)

    def _is_excluded(path: Path) -> bool:
        excluded = {"__pycache__", "z_FUTURE_IMPIMENTATIONS", "logs"}
        return any(part in excluded for part in path.parts)

    def _render_tree(current: Path, depth: int, prefix: str = "") -> list[str]:
        if depth > 3:
            return []
        lines: list[str] = []
        if depth == 0:
            lines.append(f"{current.name}/")
        entries = [p for p in _children(current) if not _is_excluded(p)]
        dirs = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]
        root_files = {
            "README.md",
            "pyproject.toml",
            "ruff.toml",
            "pytest.ini",
            "requirements-dev.txt",
        }
        if depth == 0:
            for file in files:
                if file.name in root_files:
                    lines.append(f"├── {file.name}")
        for index, directory in enumerate(dirs):
            connector = "└──" if index == len(dirs) - 1 and depth > 0 else "├──"
            lines.append(f"{prefix}{connector} {directory.name}/")
            child_prefix = prefix + ("    " if connector == "└──" else "│   ")
            lines.extend(_render_tree(directory, depth + 1, child_prefix))
        return lines

    lines = _render_tree(root_dir, 0)
    stamp = datetime.now(UTC).strftime("%m/%d/%Y_%H:%M:%S")
    body = "\n".join(lines) + "\n"
    block = "<!-- tree:begin -->\n" f"Updated: {stamp}\n\n" "```text\n" f"{body}```\n" "<!-- tree:end -->"
    from re import MULTILINE, compile as re_compile

    pattern = re_compile(r"<!-- tree:begin -->[\s\S]*?<!-- tree:end -->", flags=MULTILINE)
    new_text = pattern.sub(block, text)
    log_handle.write("\n--- Refresh project tree ---\n")
    if new_text != text:
        doc_path.write_text(new_text, encoding="utf-8")
        metadata["updated"] = True
        metadata["timestamp"] = stamp
        log_handle.write(f"Updated tree block at {stamp}.\n")
    else:
        metadata["timestamp"] = stamp
        log_handle.write("No changes in tree block.\n")
    return metadata


def _backup_files(targets: Sequence[Path], log_handle) -> list[str]:
    copied: list[str] = []
    for target in targets:
        if target.is_file() and target.suffix == ".py":
            backup_path = target.with_suffix(target.suffix + ".bak")
            shutil.copy2(target, backup_path)
            copied.append(str(backup_path))
            continue
        if target.is_dir():
            for path in target.rglob("*.py"):
                backup_path = path.with_suffix(path.suffix + ".bak")
                shutil.copy2(path, backup_path)
                copied.append(str(backup_path))
    if copied:
        log_handle.write("\n--- Backup ---\n")
        for entry in copied:
            log_handle.write(f"Created backup: {entry}\n")
    return copied


def _classify_targets(targets: Sequence[Path]) -> tuple[list[Path], list[Path]]:
    existing: list[Path] = []
    missing: list[Path] = []
    for target in targets:
        if target.exists():
            existing.append(target)
        else:
            missing.append(target)
    return existing, missing


def _execute_cleanup(
    *,
    options: CleanupOptions,
    log_handle,
    executor: CommandExecutor,
) -> tuple[list[CommandResult], list[str], bool]:
    steps: list[CommandResult] = []
    notes: list[str] = []
    failed = False
    targets = options.targets
    if options.mode == "markdown":
        lint_results, lint_note = _run_markdownlint(options=options, log_handle=log_handle, executor=executor)
        steps.extend(lint_results)
        if lint_note:
            notes.append(lint_note)
        notes.append("mode=markdown; Ruff, mypy, and pytest skipped")
        return steps, notes, failed

    ruff_format = _execute_command(
        ruff_format_cmd(targets),
        "Ruff format",
        options=options,
        log_handle=log_handle,
        executor=executor,
    )
    steps.append(ruff_format)
    if ruff_format.status == "failed":
        return steps, notes, True

    ruff_fix = _execute_command(
        ruff_fix_cmd(targets),
        "Ruff check --fix",
        options=options,
        log_handle=log_handle,
        executor=executor,
    )
    steps.append(ruff_fix)
    if ruff_fix.status == "failed":
        return steps, notes, True

    lint_results, lint_note = _run_markdownlint(options=options, log_handle=log_handle, executor=executor)
    steps.extend(lint_results)
    if lint_note:
        notes.append(lint_note)
    if steps[-1].status == "failed":
        return steps, notes, True

    mypy_result = _execute_command(
        MYPY_TARGETS,
        "Mypy",
        options=options,
        log_handle=log_handle,
        executor=executor,
    )
    steps.append(mypy_result)
    if mypy_result.status == "failed":
        return steps, notes, True

    if options.skip_pytest:
        skip_note = "pytest skipped (--no-pytest or BATCH_CLEAN_NO_PYTEST=1)"
        steps.append(_record_skip("Pytest", skip_note, PYTEST_CMD))
        notes.append(skip_note)
        return steps, notes, failed

    pytest_result = _execute_command(
        PYTEST_CMD,
        "Pytest",
        options=options,
        log_handle=log_handle,
        executor=executor,
    )
    steps.append(pytest_result)
    if pytest_result.status == "failed":
        return steps, notes, True
    return steps, notes, failed


def _write_summary(
    *,
    bundle_dir: Path,
    options: CleanupOptions,
    steps: list[CommandResult],
    tree_refresh: dict[str, object],
    backups: list[str],
    notes: list[str],
    status: str,
    exception: str | None,
) -> Path:
    summary_path = bundle_dir / "cleanup_summary.json"
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": status,
        "options": {
            "targets": [str(t) for t in options.targets],
            "mode": options.mode,
            "dry_run": options.dry_run,
            "backup": options.backup,
            "refresh_only": options.refresh_only,
            "skip_pytest": options.skip_pytest,
            "artifacts_to_keep": options.artifacts_to_keep,
        },
        "steps": [step.to_dict() for step in steps],
        "tree_refresh": tree_refresh,
        "backups": backups,
        "notes": notes,
        "exception": exception,
    }
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return summary_path


def _write_bundle_summary(
    *,
    bundle_dir: Path,
    summary_path: Path,
    log_path: Path,
    status: str,
) -> Path:
    bundle_summary_path = bundle_dir / "bundle_summary.json"
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": status,
        "bundle_dir": str(bundle_dir.resolve()),
        "artifacts": {
            "cleanup_summary": str(summary_path.resolve()),
            "cleanup_log": str(log_path.resolve()),
        },
    }
    bundle_summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return bundle_summary_path


def _update_latest(bundle_dir: Path, output_base: Path) -> None:
    latest_map = {
        "cleanup_summary.json": output_base / "latest_cleanup_summary.json",
        "cleanup_log.txt": output_base / "latest_cleanup_log.txt",
        "bundle_summary.json": output_base / "latest_bundle_summary.json",
    }
    for name, destination in latest_map.items():
        src = bundle_dir / name
        try:
            if destination.exists() or destination.is_symlink():
                destination.unlink()
            destination.hardlink_to(src)
        except Exception:
            destination.write_bytes(src.read_bytes())


def _prune_history(output_base: Path, current_dir: Path, keep: int) -> list[str]:
    if not output_base.exists():
        return []
    bundles = sorted(
        [path for path in output_base.iterdir() if path.is_dir() and path.name.startswith("run_batch_cleanup-")],
        key=lambda p: p.name,
        reverse=True,
    )
    pruned: list[str] = []
    for old_dir in bundles[keep:]:
        if old_dir == current_dir:
            continue
        shutil.rmtree(old_dir, ignore_errors=True)
        pruned.append(str(old_dir.resolve()))
    return pruned


def run(argv: Sequence[str] | None = None, *, executor: CommandExecutor | None = None) -> dict[str, object]:
    args = _parse_args(argv)
    options = _prepare_options(args)
    log_level = getattr(logging, options.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s", force=True)

    executor_fn = executor or _run_subprocess
    options.output_base.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC)
    bundle_dir = options.output_base / f"run_batch_cleanup-{timestamp.strftime('%Y-%m-%d_%H%M%S')}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    log_path = bundle_dir / "cleanup_log.txt"

    steps: list[CommandResult] = []
    notes: list[str] = []
    backups: list[str] = []
    tree_refresh: dict[str, object] | None = None
    exception_message: str | None = None
    status = "success"

    with log_path.open("w", encoding="utf-8") as log_handle:
        existing_targets, missing_targets = _classify_targets(options.targets)
        fallback_used = False
        if existing_targets:
            options.targets = existing_targets
        else:
            fallback_used = True
            options.targets = [PROJECT_ROOT]

        log_handle.write(
            "# 🧼 repo cleanup log\n"
            f"Timestamp: {timestamp.isoformat()}\n"
            f"Targets: {', '.join(str(t) for t in options.targets)}\n"
            f"Mode: {options.mode}{' (dry-run)' if options.dry_run else ''}\n"
        )
        if missing_targets or fallback_used:
            log_handle.write("\n--- Target verification ---\n")
            if missing_targets:
                for target in missing_targets:
                    log_handle.write(f"Missing target: {target}\n")
            if fallback_used:
                log_handle.write("No requested targets existed; defaulted to project root.\n")
                notes.append("Requested cleanup targets missing; defaulted to project root")
            elif missing_targets:
                log_handle.write("Proceeding with existing targets only.\n")
                notes.append("Missing cleanup targets skipped: " + ", ".join(str(target) for target in missing_targets))
        try:
            tree_refresh = _refresh_project_tree(log_handle, PROJECT_ROOT)
            if options.backup:
                backups = _backup_files(options.targets, log_handle)
            if options.refresh_only:
                notes.append("refresh-only flag set; skipping remaining commands")
            else:
                steps, step_notes, failed = _execute_cleanup(
                    options=options,
                    log_handle=log_handle,
                    executor=executor_fn,
                )
                notes.extend(step_notes)
                if failed:
                    status = "failed"
                if options.dry_run:
                    notes.append("dry-run mode executed; no changes applied")
        except Exception as exc:  # pragma: no cover - defensive logging
            status = "error"
            exception_message = f"{exc.__class__.__name__}: {exc}"
            log_handle.write("\n[!] Unhandled exception during cleanup:\n")
            traceback.print_exc(file=log_handle)
        log_handle.write(f"\nStatus: {status}\n")

    if tree_refresh is None:
        tree_refresh = {}

    if options.refresh_only and status != "error":
        status = "success"

    summary_path = _write_summary(
        bundle_dir=bundle_dir,
        options=options,
        steps=steps,
        tree_refresh=tree_refresh,
        backups=backups,
        notes=notes,
        status=status,
        exception=exception_message,
    )
    bundle_summary_path = _write_bundle_summary(
        bundle_dir=bundle_dir,
        summary_path=summary_path,
        log_path=log_path,
        status=status,
    )
    _update_latest(bundle_dir, options.output_base)
    pruned = _prune_history(options.output_base, bundle_dir, options.artifacts_to_keep)

    result = {
        "status": status,
        "bundle_dir": str(bundle_dir.resolve()),
        "summary_path": str(summary_path.resolve()),
        "log_path": str(log_path.resolve()),
        "bundle_summary": str(bundle_summary_path.resolve()),
        "pruned": pruned,
    }

    if exception_message:
        raise RuntimeError(exception_message)

    return result


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(argv)
    except Exception as exc:  # pragma: no cover - CLI guard
        logging.exception("Batch cleanup failed: %s", exc)
        return 1
    status = result.get("status", "success")
    import sys

    sys.stdout.write(json.dumps({"status": status, **result}) + "\n")
    return 0 if status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
