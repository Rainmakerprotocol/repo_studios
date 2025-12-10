#!/usr/bin/env python3
"""Topic orchestrator for dependency and import hygiene.

Publishes Healthview bundles to
`.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<timestamp>/` and replaces
`scripts/orchestrators/run_batch_cleanup.py` together with the manually sequenced hygiene producers.
It runs dependency hygiene, import graph, placeholder scan, batch cleanup dry run, typecheck, and
optional mypy baseline refresh steps before mirroring artifacts. Typical runs take seven to eleven
minutes in CI, with linting and mypy dominating when baseline refresh is enabled.
"""

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
from typing import Any, Iterable, Sequence

from command_center.scripts.libraries import (
    CatalogRegistry,
    KeepSpec,
    OptionsConfig,
    PathSpec,
    PathsConfig,
    ReportArtifact,
    TopicContext,
    TopicStep,
    build_pipeline_telemetry,
    build_standard_options,
    build_standard_paths,
    build_topic_pipeline,
    measure_artifact_directory,
    step_failed,
    step_skipped,
    step_success,
    write_report_artifacts,
)

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "dependency-import-hygiene"
HEALTHVIEW_TOPIC = "dependency_import_hygiene"
VIEWER_SLUG = "healthview"
SCHEMA_VERSION = 1

DEPENDENCY_SCRIPT = Path(".repo_studios/scripts/producers/generate_dependency_hygiene_report.py")
IMPORT_GRAPH_SCRIPT = Path(".repo_studios/scripts/producers/generate_import_graph_report.py")
PLACEHOLDER_SCRIPT = Path(".repo_studios/scripts/producers/scan_code_placeholders.py")
TYPECHECK_SCRIPT = Path(".repo_studios/scripts/producers/generate_typecheck_report.py")
REFRESH_BASELINES_SCRIPT = Path(".repo_studios/scripts/utilities/refresh_mypy_baselines.py")

DEPENDENCY_MODULE = "scripts.producers.generate_dependency_hygiene_report"
IMPORT_GRAPH_MODULE = "scripts.producers.generate_import_graph_report"
PLACEHOLDER_MODULE = "scripts.producers.scan_code_placeholders"
TYPECHECK_MODULE = "scripts.producers.generate_typecheck_report"
REFRESH_BASELINES_MODULE = "scripts.utilities.refresh_mypy_baselines"

DEFAULT_DEPENDENCY_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/dependency_hygiene_reports")
DEFAULT_IMPORT_GRAPH_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/import_graph_reports")
DEFAULT_PLACEHOLDER_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/code_placeholder_scans")
DEFAULT_PLACEHOLDER_ALLOWLIST = Path(".repo_studios/config/placeholder_allowlist.txt")
DEFAULT_BATCH_CLEANUP_OUTPUT_BASE = Path(".repo_studios/reports/orchestrator_runs/run_batch_cleanup")
DEFAULT_TYPECHECK_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/typecheck_reports")
DEFAULT_MYPY_BASELINES_OUTPUT_DIR = Path(".repo_studios/reports/orchestrator_runs/mypy_baselines")
DEFAULT_HEALTHVIEW_ROOT = Path(".repo_studios/command_center/reports")

DEPENDENCY_RUN_PREFIX = "dependency_hygiene"
IMPORT_GRAPH_RUN_PREFIX = "import_graph"
PLACEHOLDER_RUN_PREFIX = "placeholder_scan"
TYPECHECK_RUN_PREFIX = "typecheck"
MYPY_BASELINES_RUN_PREFIX = "mypy_baselines"


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    dependency_output_dir: Path
    import_graph_output_dir: Path
    placeholder_output_dir: Path
    placeholder_allowlist: Path
    batch_cleanup_output_base: Path
    typecheck_output_dir: Path
    mypy_baselines_output_dir: Path
    healthview_root: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "dependency_output_dir": PathSpec(
            field="dependency_output_dir", default=DEFAULT_DEPENDENCY_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "import_graph_output_dir": PathSpec(
            field="import_graph_output_dir", default=DEFAULT_IMPORT_GRAPH_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "placeholder_output_dir": PathSpec(
            field="placeholder_output_dir", default=DEFAULT_PLACEHOLDER_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "placeholder_allowlist": PathSpec(
            field="placeholder_allowlist", default=DEFAULT_PLACEHOLDER_ALLOWLIST, ensure_dir=False, within_repo=False
        ),
        "batch_cleanup_output_base": PathSpec(
            field="batch_cleanup_output_base", default=DEFAULT_BATCH_CLEANUP_OUTPUT_BASE, ensure_dir=True, within_repo=False
        ),
        "typecheck_output_dir": PathSpec(
            field="typecheck_output_dir", default=DEFAULT_TYPECHECK_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "mypy_baselines_output_dir": PathSpec(
            field="mypy_baselines_output_dir",
            default=DEFAULT_MYPY_BASELINES_OUTPUT_DIR,
            ensure_dir=True,
            within_repo=False,
        ),
        "healthview_root": PathSpec(
            field="healthview_root", default=DEFAULT_HEALTHVIEW_ROOT, ensure_dir=True, within_repo=False
        ),
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepParameters:
    artifacts_to_keep: int
    dependency_keep: int
    import_graph_keep: int
    placeholder_keep: int
    cleanup_keep: int
    typecheck_keep: int
    baseline_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepParameters,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "dependency_keep": KeepSpec(field="dependency_artifacts_to_keep", minimum=1),
        "import_graph_keep": KeepSpec(field="import_graph_artifacts_to_keep", minimum=1),
        "placeholder_keep": KeepSpec(field="placeholder_artifacts_to_keep", minimum=1),
        "cleanup_keep": KeepSpec(field="cleanup_artifacts_to_keep", minimum=1),
        "typecheck_keep": KeepSpec(field="typecheck_artifacts_to_keep", minimum=1),
        "baseline_keep": KeepSpec(field="baseline_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int
    dependency_keep: int
    import_graph_keep: int
    placeholder_keep: int
    cleanup_keep: int
    typecheck_keep: int
    baseline_keep: int
    run_timestamp: datetime
    skip_import_graph: bool
    skip_typecheck: bool
    trigger_batch_cleanup: bool
    refresh_mypy_baselines: bool
    dependency_patterns: tuple[str, ...]
    dependency_skip_pyproject: bool
    import_owned: tuple[str, ...]
    placeholder_extensions: tuple[str, ...]
    placeholder_patterns: tuple[str, ...]
    placeholder_exclude_prefixes: tuple[str, ...] | None


@dataclass(frozen=True)
class DependencyOutcome:
    run_dir: Path | None
    report_json: Path | None
    report_md: Path | None
    log_path: Path | None
    payload: dict[str, Any] | None
    exit_code: int


@dataclass(frozen=True)
class ImportGraphOutcome:
    run_dir: Path | None
    report_json: Path | None
    graph_path: Path | None
    log_path: Path | None
    payload: dict[str, Any] | None


@dataclass(frozen=True)
class PlaceholderOutcome:
    run_dir: Path | None
    report_json: Path | None
    matches_json: Path | None
    log_path: Path | None
    payload: dict[str, Any] | None


@dataclass(frozen=True)
class BatchCleanupOutcome:
    bundle_dir: Path | None
    summary_path: Path | None
    log_path: Path | None
    bundle_summary: Path | None
    status: str | None


@dataclass(frozen=True)
class TypecheckOutcome:
    run_dir: Path | None
    report_json: Path | None
    report_md: Path | None
    log_path: Path | None
    raw_output: Path | None
    payload: dict[str, Any] | None


@dataclass(frozen=True)
class BaselineOutcome:
    run_dir: Path | None
    summary_path: Path | None
    status: str | None
    payload: dict[str, Any] | None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--dependency-output-dir", default=str(DEFAULT_DEPENDENCY_OUTPUT_DIR))
    parser.add_argument("--import-graph-output-dir", default=str(DEFAULT_IMPORT_GRAPH_OUTPUT_DIR))
    parser.add_argument("--placeholder-output-dir", default=str(DEFAULT_PLACEHOLDER_OUTPUT_DIR))
    parser.add_argument("--placeholder-allowlist", default=str(DEFAULT_PLACEHOLDER_ALLOWLIST))
    parser.add_argument("--batch-cleanup-output-base", default=str(DEFAULT_BATCH_CLEANUP_OUTPUT_BASE))
    parser.add_argument("--typecheck-output-dir", default=str(DEFAULT_TYPECHECK_OUTPUT_DIR))
    parser.add_argument("--mypy-baselines-output-dir", default=str(DEFAULT_MYPY_BASELINES_OUTPUT_DIR))
    parser.add_argument("--healthview-root", default=str(DEFAULT_HEALTHVIEW_ROOT))
    parser.add_argument("--dependency-artifacts-to-keep", type=int, default=10)
    parser.add_argument("--import-graph-artifacts-to-keep", type=int, default=10)
    parser.add_argument("--placeholder-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--cleanup-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--typecheck-artifacts-to-keep", type=int, default=10)
    parser.add_argument("--baseline-artifacts-to-keep", type=int, default=5)
    parser.add_argument("--artifacts-to-keep", type=int, default=3, help="Retention budget for orchestrator runs")
    parser.add_argument(
        "--dependency-requirements-pattern",
        action="append",
        dest="dependency_patterns",
        help="Glob pattern(s) forwarded to the dependency hygiene producer",
    )
    parser.add_argument(
        "--dependency-skip-pyproject",
        action="store_true",
        help="Skip scanning pyproject.toml in the dependency hygiene producer",
    )
    parser.add_argument(
        "--import-owned",
        nargs="+",
        default=None,
        help="Owned packages forwarded to the import graph producer",
    )
    parser.add_argument(
        "--placeholder-include-ext",
        nargs="+",
        default=None,
        help="File extensions forwarded to the placeholder scanner",
    )
    parser.add_argument(
        "--placeholder-pattern",
        nargs="+",
        default=None,
        help="Placeholder tokens forwarded to the placeholder scanner",
    )
    parser.add_argument(
        "--placeholder-exclude-prefix",
        nargs="+",
        default=None,
        help="Prefixes forwarded to the placeholder scanner",
    )
    parser.add_argument("--skip-import-graph", action="store_true", help="Skip the import graph producer")
    parser.add_argument("--skip-typecheck", action="store_true", help="Skip the typecheck producer")
    parser.add_argument(
        "--trigger-batch-cleanup",
        action="store_true",
        help="Execute run_batch_cleanup in dry-run mode and capture the bundle",
    )
    parser.add_argument(
        "--refresh-mypy-baselines",
        action="store_true",
        help="Invoke the mypy baseline refresher after the typecheck step",
    )
    parser.add_argument("--timestamp", help="ISO8601 timestamp forwarded to producers where supported")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    return parser.parse_args(argv)


def _parse_timestamp(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:  # pragma: no cover - defensive timestamp parsing
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_paths(args: argparse.Namespace) -> Paths:
    return build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__))


def _normalize_sequence(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return tuple()
    return tuple(dict.fromkeys(str(value) for value in values if str(value)))


def build_options(args: argparse.Namespace) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    run_timestamp = _parse_timestamp(getattr(args, "timestamp", None))
    dependency_patterns = _normalize_sequence(getattr(args, "dependency_patterns", None))
    import_owned = _normalize_sequence(getattr(args, "import_owned", None))
    placeholder_extensions = _normalize_sequence(getattr(args, "placeholder_include_ext", None))
    placeholder_patterns = _normalize_sequence(getattr(args, "placeholder_pattern", None))
    placeholder_exclude = _normalize_sequence(getattr(args, "placeholder_exclude_prefix", None))
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        dependency_keep=keep_values.dependency_keep,
        import_graph_keep=keep_values.import_graph_keep,
        placeholder_keep=keep_values.placeholder_keep,
        cleanup_keep=keep_values.cleanup_keep,
        typecheck_keep=keep_values.typecheck_keep,
        baseline_keep=keep_values.baseline_keep,
        run_timestamp=run_timestamp,
        skip_import_graph=bool(args.skip_import_graph),
        skip_typecheck=bool(args.skip_typecheck),
        trigger_batch_cleanup=bool(args.trigger_batch_cleanup),
        refresh_mypy_baselines=bool(args.refresh_mypy_baselines),
        dependency_patterns=dependency_patterns,
        dependency_skip_pyproject=bool(args.dependency_skip_pyproject),
        import_owned=import_owned,
        placeholder_extensions=placeholder_extensions,
        placeholder_patterns=placeholder_patterns,
        placeholder_exclude_prefixes=placeholder_exclude if placeholder_exclude else None,
    )


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s %(message)s")


def _load_callable(script_path: Path, module_name: str, attribute: str):
    script_path = script_path.resolve()
    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load module from {script_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
    func = getattr(module, attribute, None)
    if not callable(func):
        raise AttributeError(f"Module {module_name} missing callable {attribute}()")
    return func


def _invoke_main(func, argv: Sequence[str]) -> int:
    try:
        result = func(list(argv))
    except SystemExit as exc:  # pragma: no cover - defensive guard for argparse exits
        code = exc.code
        if isinstance(code, int):
            return code
        return 1
    if isinstance(result, int):
        return result
    try:
        return int(result)
    except (TypeError, ValueError):  # pragma: no cover - defensive coercion
        return 0


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _relativize(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _timestamp_to_slug(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


def _iso_to_run_dir(prefix: str, output_dir: Path, raw: str | None, *, separator: str = "_") -> Path | None:
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    slug = parsed.strftime(f"%Y%m%d{separator}%H%M%S")
    candidate = output_dir / f"{prefix}-{slug}"
    return candidate.resolve() if candidate.exists() else None


def _dependency_report(paths: Paths, options: Options) -> DependencyOutcome:
    LOGGER.info("Running dependency hygiene producer")
    main_callable = _load_callable(paths.repo_root / DEPENDENCY_SCRIPT, DEPENDENCY_MODULE, "main")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.dependency_output_dir),
        "--artifacts-to-keep",
        str(options.dependency_keep),
        "--log-level",
        options.log_level,
    ]
    if options.dependency_patterns:
        for pattern in options.dependency_patterns:
            argv.extend(["--requirements-pattern", pattern])
    if options.dependency_skip_pyproject:
        argv.append("--skip-pyproject")
    argv.extend(["--timestamp", options.run_timestamp.isoformat()])
    exit_code = _invoke_main(main_callable, argv)
    latest_report = paths.dependency_output_dir / "latest_report.json"
    payload = _read_json(latest_report)
    generated = payload.get("generated_utc") if isinstance(payload, dict) else None
    run_dir = _iso_to_run_dir(DEPENDENCY_RUN_PREFIX, paths.dependency_output_dir, generated)
    report_json = run_dir / "report.json" if run_dir and (run_dir / "report.json").exists() else None
    report_md = run_dir / "report.md" if run_dir and (run_dir / "report.md").exists() else None
    log_path = run_dir / "log.txt" if run_dir and (run_dir / "log.txt").exists() else None
    return DependencyOutcome(
        run_dir=run_dir,
        report_json=report_json,
        report_md=report_md,
        log_path=log_path,
        payload=payload,
        exit_code=exit_code,
    )


def _import_graph_report(paths: Paths, options: Options) -> ImportGraphOutcome:
    LOGGER.info("Running import graph producer")
    main_callable = _load_callable(paths.repo_root / IMPORT_GRAPH_SCRIPT, IMPORT_GRAPH_MODULE, "main")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.import_graph_output_dir),
        "--artifacts-to-keep",
        str(options.import_graph_keep),
        "--log-level",
        options.log_level,
        "--timestamp",
        options.run_timestamp.isoformat(),
    ]
    if options.import_owned:
        argv.extend(["--owned", *options.import_owned])
    _invoke_main(main_callable, argv)
    latest_report = paths.import_graph_output_dir / "latest_report.json"
    payload = _read_json(latest_report)
    generated = payload.get("generated_utc") if isinstance(payload, dict) else None
    run_dir = _iso_to_run_dir(IMPORT_GRAPH_RUN_PREFIX, paths.import_graph_output_dir, generated)
    report_json = run_dir / "report.json" if run_dir and (run_dir / "report.json").exists() else None
    graph_path = run_dir / "graph.json" if run_dir and (run_dir / "graph.json").exists() else None
    log_path = run_dir / "log.txt" if run_dir and (run_dir / "log.txt").exists() else None
    return ImportGraphOutcome(
        run_dir=run_dir,
        report_json=report_json,
        graph_path=graph_path,
        log_path=log_path,
        payload=payload,
    )


def _placeholder_scan(paths: Paths, options: Options) -> PlaceholderOutcome:
    LOGGER.info("Running placeholder scan producer")
    run_callable = _load_callable(paths.repo_root / PLACEHOLDER_SCRIPT, PLACEHOLDER_MODULE, "run")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.placeholder_output_dir),
        "--allowlist-file",
        str(paths.placeholder_allowlist),
        "--artifacts-to-keep",
        str(options.placeholder_keep),
        "--log-level",
        options.log_level,
    ]
    if options.placeholder_extensions:
        argv.extend(["--include-ext", *options.placeholder_extensions])
    if options.placeholder_patterns:
        argv.extend(["--patterns", *options.placeholder_patterns])
    if options.placeholder_exclude_prefixes:
        argv.extend(["--exclude-prefix", *options.placeholder_exclude_prefixes])
    payload = run_callable(argv)
    run_dir = None
    if isinstance(payload, dict):
        run_id = payload.get("run_id")
        if isinstance(run_id, str):
            candidate = paths.placeholder_output_dir / run_id
            if candidate.exists():
                run_dir = candidate.resolve()
    report_json = run_dir / "report.json" if run_dir and (run_dir / "report.json").exists() else None
    matches_json = run_dir / "matches.json" if run_dir and (run_dir / "matches.json").exists() else None
    log_path = run_dir / "log.txt" if run_dir and (run_dir / "log.txt").exists() else None
    return PlaceholderOutcome(
        run_dir=run_dir,
        report_json=report_json,
        matches_json=matches_json,
        log_path=log_path,
        payload=payload if isinstance(payload, dict) else None,
    )


def _cleanup_step_commands(repo_root: Path) -> list[tuple[str, list[str]]]:
    resolved_root = repo_root.resolve()
    ruff_config = resolved_root / ".repo_studios" / "ruff_clean.toml"
    markdown_config = resolved_root / ".markdownlint.json"
    return [
        ("Ruff format", ["ruff", "format", str(resolved_root), "--config", str(ruff_config)]),
        (
            "Ruff check --fix",
            ["ruff", "check", str(resolved_root), "--fix", "--config", str(ruff_config)],
        ),
        (
            "markdownlint --fix (npx)",
            [
                "npx",
                "--yes",
                "markdownlint-cli@0.39.0",
                "**/*.md",
                "--fix",
                "--config",
                str(markdown_config),
            ],
        ),
        (
            "markdownlint check (npx)",
            [
                "npx",
                "--yes",
                "markdownlint-cli@0.39.0",
                "**/*.md",
                "--config",
                str(markdown_config),
            ],
        ),
        ("Mypy", ["mypy"]),
        ("Pytest", ["pytest", "-q"]),
    ]


def _update_cleanup_latest(bundle_dir: Path, output_base: Path) -> None:
    mapping = {
        "cleanup_summary.json": output_base / "latest_cleanup_summary.json",
        "cleanup_log.txt": output_base / "latest_cleanup_log.txt",
        "bundle_summary.json": output_base / "latest_bundle_summary.json",
    }
    for source_name, destination in mapping.items():
        source_path = bundle_dir / source_name
        if not source_path.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            if destination.exists() or destination.is_symlink():
                destination.unlink()
            destination.hardlink_to(source_path)
        except Exception:
            shutil.copy2(source_path, destination)


def _prune_cleanup_history(output_base: Path, current_dir: Path, keep: int) -> list[str]:
    if keep <= 0 or not output_base.exists():
        return []
    bundles = sorted(
        [path for path in output_base.iterdir() if path.is_dir() and path.name.startswith("run_batch_cleanup-")],
        key=lambda candidate: candidate.name,
        reverse=True,
    )
    pruned: list[str] = []
    for obsolete in bundles[keep:]:
        if obsolete == current_dir:
            continue
        shutil.rmtree(obsolete, ignore_errors=True)
        pruned.append(str(obsolete.resolve()))
    return pruned


def _batch_cleanup(paths: Paths, options: Options) -> BatchCleanupOutcome:
    LOGGER.info("Recording batch cleanup dry-run plan")
    timestamp = options.run_timestamp.astimezone(timezone.utc)
    slug = timestamp.strftime("%Y-%m-%d_%H%M%S")
    bundle_dir = paths.batch_cleanup_output_base / f"run_batch_cleanup-{slug}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    commands = _cleanup_step_commands(paths.repo_root)
    log_lines = [
        "# 🧼 dependency cleanup dry-run",
        f"Timestamp: {timestamp.isoformat()}",
        f"Repo root: {paths.repo_root.resolve()}",
        "",
        "Legacy run_batch_cleanup shim removed; commands recorded for operator reference only.",
        "",
        "## Planned steps",
    ]
    for label, command in commands:
        log_lines.append(f"- {label}: {' '.join(command)}")
    log_path = bundle_dir / "cleanup_log.txt"
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    steps_payload = [
        {
            "label": label,
            "command": command,
            "status": "skipped",
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "duration_seconds": 0.0,
            "skipped_reason": "dry-run planning; legacy shim retired",
        }
        for label, command in commands
    ]

    tree_markdown = paths.repo_root / ".repo_studios" / "docs" / "project_tree_overview.md"
    tree_refresh = {
        "markdown_path": str(tree_markdown.resolve() if tree_markdown.exists() else tree_markdown),
        "root": str(paths.repo_root.resolve()),
        "updated": False,
        "found_markers": tree_markdown.exists(),
        "timestamp": timestamp.strftime("%m/%d/%Y_%H:%M:%S"),
    }

    summary_payload = {
        "schema_version": 1,
        "generated_at": timestamp.isoformat(),
        "status": "success",
        "options": {
            "targets": [str(paths.repo_root.resolve())],
            "mode": "all",
            "dry_run": True,
            "backup": False,
            "refresh_only": False,
            "skip_pytest": True,
            "artifacts_to_keep": options.cleanup_keep,
        },
        "steps": steps_payload,
        "tree_refresh": tree_refresh,
        "backups": [],
        "notes": [
            "dry-run mode executed; no cleanup commands were invoked",
            "legacy batch cleanup shim removed; dependency/import hygiene orchestrator now emits plan",
        ],
        "exception": None,
    }
    summary_path = bundle_dir / "cleanup_summary.json"
    summary_path.write_text(json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8")

    bundle_summary_payload = {
        "schema_version": 1,
        "generated_at": timestamp.isoformat(),
        "status": "success",
        "bundle_dir": str(bundle_dir.resolve()),
        "artifacts": {
            "cleanup_summary": str(summary_path.resolve()),
            "cleanup_log": str(log_path.resolve()),
        },
    }
    bundle_summary_path = bundle_dir / "bundle_summary.json"
    bundle_summary_path.write_text(json.dumps(bundle_summary_payload, indent=2) + "\n", encoding="utf-8")

    _update_cleanup_latest(bundle_dir, paths.batch_cleanup_output_base)
    _prune_cleanup_history(paths.batch_cleanup_output_base, bundle_dir, options.cleanup_keep)

    return BatchCleanupOutcome(
        bundle_dir=bundle_dir,
        summary_path=summary_path,
        log_path=log_path,
        bundle_summary=bundle_summary_path,
        status="success",
    )


def _typecheck_report(paths: Paths, options: Options) -> TypecheckOutcome:
    LOGGER.info("Running typecheck producer")
    main_callable = _load_callable(paths.repo_root / TYPECHECK_SCRIPT, TYPECHECK_MODULE, "main")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.typecheck_output_dir),
        "--artifacts-to-keep",
        str(options.typecheck_keep),
        "--log-level",
        options.log_level,
        "--timestamp",
        options.run_timestamp.isoformat(),
    ]
    _invoke_main(main_callable, argv)
    latest_report = paths.typecheck_output_dir / "latest_report.json"
    payload = _read_json(latest_report)
    timestamp = payload.get("generated_utc") if isinstance(payload, dict) else None
    run_dir = _iso_to_run_dir(TYPECHECK_RUN_PREFIX, paths.typecheck_output_dir, timestamp)
    report_json = run_dir / "report.json" if run_dir and (run_dir / "report.json").exists() else None
    report_md = run_dir / "report.md" if run_dir and (run_dir / "report.md").exists() else None
    log_path = run_dir / "log.txt" if run_dir and (run_dir / "log.txt").exists() else None
    raw_output = run_dir / "raw.txt" if run_dir and (run_dir / "raw.txt").exists() else None
    return TypecheckOutcome(
        run_dir=run_dir,
        report_json=report_json,
        report_md=report_md,
        log_path=log_path,
        raw_output=raw_output,
        payload=payload,
    )


def _refresh_baselines(paths: Paths, options: Options) -> BaselineOutcome:
    LOGGER.info("Refreshing mypy baselines")
    run_callable = _load_callable(paths.repo_root / REFRESH_BASELINES_SCRIPT, REFRESH_BASELINES_MODULE, "run")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.mypy_baselines_output_dir),
        "--artifacts-to-keep",
        str(options.baseline_keep),
        "--log-level",
        options.log_level,
        "--timestamp",
        options.run_timestamp.isoformat(),
    ]
    payload = run_callable(argv)
    run_dir = None
    if isinstance(payload, dict):
        run_slug = payload.get("run_slug")
        if isinstance(run_slug, str):
            candidate = paths.mypy_baselines_output_dir / f"{MYPY_BASELINES_RUN_PREFIX}-{run_slug.replace('-', '_')}"
            if candidate.exists():
                run_dir = candidate.resolve()
    summary_path = None
    if isinstance(payload, dict):
        artifacts = payload.get("artifacts")
        if isinstance(artifacts, dict):
            candidate = artifacts.get("bundle_summary.json")
            if candidate:
                path = Path(candidate)
                if not path.is_absolute():
                    path = (paths.mypy_baselines_output_dir / path).resolve()
                summary_path = path if path.exists() else None
    status = payload.get("status") if isinstance(payload, dict) else None
    return BaselineOutcome(
        run_dir=run_dir,
        summary_path=summary_path,
        status=str(status) if isinstance(status, str) else None,
        payload=payload if isinstance(payload, dict) else None,
    )


def _register_scripts(registry: CatalogRegistry) -> None:
    registry.register(
        script_path=str(Path(".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py")),
        topic=TOPIC_SLUG,
        role="orchestrator",
    )
    registry.register(script_path=str(DEPENDENCY_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(IMPORT_GRAPH_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(PLACEHOLDER_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(TYPECHECK_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(REFRESH_BASELINES_SCRIPT), topic=TOPIC_SLUG, role="utility")


def _summarize_markdown(
    *,
    slug: str,
    telemetry_success: bool,
    dependency: DependencyOutcome,
    import_graph: ImportGraphOutcome | None,
    placeholder: PlaceholderOutcome,
    cleanup: BatchCleanupOutcome | None,
    typecheck: TypecheckOutcome | None,
    baselines: BaselineOutcome | None,
    step_reports: Iterable[tuple[str, str, str | None]],
) -> str:
    dependency_summary = dependency.payload.get("summary") if dependency.payload else {}
    dep_status = dependency_summary.get("status") if isinstance(dependency_summary, dict) else None
    dep_issue_count = dependency_summary.get("issue_count") if isinstance(dependency_summary, dict) else None

    import_summary = import_graph.payload.get("summary") if import_graph and import_graph.payload else {}
    import_status = import_summary.get("status") if isinstance(import_summary, dict) else None

    placeholder_total = None
    if placeholder.payload:
        placeholder_total = placeholder.payload.get("total_matches")

    typecheck_status = None
    typecheck_errors = None
    if typecheck and isinstance(typecheck.payload, dict):
        typecheck_status = typecheck.payload.get("status")
        summary = typecheck.payload.get("summary")
        if isinstance(summary, dict):
            typecheck_errors = summary.get("error_count")

    baseline_status = baselines.status if baselines else None

    lines: list[str] = []
    lines.append("# Dependency & Import Hygiene Summary")
    lines.append("")
    lines.append(f"- run_slug: `{slug}`")
    lines.append(f"- pipeline_status: {'success' if telemetry_success else 'failed'}")
    lines.append(f"- dependency_status: {dep_status or 'unknown'}")
    lines.append(f"- dependency_issue_count: {dep_issue_count if dep_issue_count is not None else 'unknown'}")
    if import_graph:
        lines.append(f"- import_graph_status: {import_status or 'unknown'}")
    else:
        lines.append("- import_graph_status: skipped")
    lines.append(f"- placeholder_matches: {placeholder_total if placeholder_total is not None else 'unknown'}")
    if cleanup:
        lines.append(f"- batch_cleanup_status: {cleanup.status or 'unknown'}")
    else:
        lines.append("- batch_cleanup_status: skipped")
    if typecheck:
        lines.append(f"- typecheck_status: {typecheck_status or 'unknown'}")
        lines.append(f"- typecheck_error_count: {typecheck_errors if typecheck_errors is not None else 'unknown'}")
    else:
        lines.append("- typecheck_status: skipped")
        lines.append("- typecheck_error_count: skipped")
    if baselines:
        lines.append(f"- mypy_baseline_status: {baseline_status or 'unknown'}")
    else:
        lines.append("- mypy_baseline_status: not requested")
    lines.append("")
    lines.append("## Step Outcomes")
    lines.append("")
    for name, status, detail in step_reports:
        lines.append(f"- {name}: {status}")
        if detail:
            lines.append(f"  - detail: {detail}")
    lines.append("")
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    paths = build_paths(args)
    options = build_options(args)
    configure_logging(options.log_level)

    registry = CatalogRegistry()
    _register_scripts(registry)

    context = TopicContext(paths=paths, options=options, metadata={})

    dependency_holder: dict[str, DependencyOutcome] = {}
    import_holder: dict[str, ImportGraphOutcome | None] = {"value": None}
    placeholder_holder: dict[str, PlaceholderOutcome] = {}
    cleanup_holder: dict[str, BatchCleanupOutcome | None] = {"value": None}
    typecheck_holder: dict[str, TypecheckOutcome | None] = {"value": None}
    baseline_holder: dict[str, BaselineOutcome | None] = {"value": None}

    def dependency_step(ctx: TopicContext):
        outcome = _dependency_report(paths, options)
        dependency_holder["value"] = outcome
        ctx.add_metadata("dependency", outcome.payload)
        summary = outcome.payload.get("summary") if outcome.payload else {}
        issues = summary.get("issue_count") if isinstance(summary, dict) else None
        detail = "dependency hygiene completed"
        if isinstance(summary, dict) and summary.get("status") == "failed":
            detail = f"issues detected ({issues if issues is not None else 'unknown'} findings)"
        payload = summary if isinstance(summary, dict) else None
        if outcome.exit_code not in (0, 1) or payload is None:
            return step_failed(detail="dependency producer failed", payload=payload)
        if outcome.exit_code == 1:
            return step_failed(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    def import_step(ctx: TopicContext):
        if options.skip_import_graph:
            return step_skipped(detail="import graph step skipped via flag")
        outcome = _import_graph_report(paths, options)
        import_holder["value"] = outcome
        ctx.add_metadata("import_graph", outcome.payload)
        summary = outcome.payload.get("summary") if outcome.payload else {}
        status = summary.get("status") if isinstance(summary, dict) else None
        detail = f"status {status}" if status else "import graph completed"
        payload = summary if isinstance(summary, dict) else None
        if payload is None:
            return step_failed(detail="import graph payload missing", payload=None)
        if status not in {"ok", "no_targets"}:
            return step_failed(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    def placeholder_step(ctx: TopicContext):
        outcome = _placeholder_scan(paths, options)
        placeholder_holder["value"] = outcome
        ctx.add_metadata("placeholder", outcome.payload)
        total = outcome.payload.get("total_matches") if outcome.payload else None
        detail = f"total matches {total}" if total is not None else "placeholder scan complete"
        if outcome.payload is None:
            return step_failed(detail="placeholder payload missing", payload=None)
        return step_success(detail=detail, payload=outcome.payload)

    def cleanup_step(ctx: TopicContext):
        if not options.trigger_batch_cleanup:
            return step_skipped(detail="batch cleanup skipped via flag")
        outcome = _batch_cleanup(paths, options)
        cleanup_holder["value"] = outcome
        payload = {
            "status": outcome.status,
            "bundle_dir": str(outcome.bundle_dir) if outcome.bundle_dir else None,
        }
        detail = f"status {outcome.status}" if outcome.status else "cleanup executed"
        if outcome.status and outcome.status.lower() not in {"success", "ok"}:
            return step_failed(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    def typecheck_step(ctx: TopicContext):
        if options.skip_typecheck:
            return step_skipped(detail="typecheck skipped via flag")
        outcome = _typecheck_report(paths, options)
        typecheck_holder["value"] = outcome
        ctx.add_metadata("typecheck", outcome.payload)
        status = outcome.payload.get("status") if outcome.payload else None
        summary = outcome.payload.get("summary") if outcome.payload else None
        notes = outcome.payload.get("notes") if outcome.payload else None
        detail = f"status {status}" if status else "typecheck completed"
        if status == "skipped" and isinstance(notes, str) and notes:
            detail = notes
        payload = {
            "status": status,
            "summary": summary,
        } if isinstance(summary, dict) else {"status": status}
        if notes:
            payload["notes"] = notes
        if status == "skipped":
            return step_skipped(detail=detail, payload=payload)
        if status not in {"ok"}:
            return step_failed(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    def baselines_step(ctx: TopicContext):
        if not options.refresh_mypy_baselines:
            return step_skipped(detail="baseline refresh not requested")
        outcome = _refresh_baselines(paths, options)
        baseline_holder["value"] = outcome
        ctx.add_metadata("mypy_baselines", outcome.payload)
        detail = f"status {outcome.status}" if outcome.status else "baseline refresh completed"
        payload = outcome.payload if isinstance(outcome.payload, dict) else None
        if outcome.status and outcome.status.lower() not in {"ok", "success"}:
            return step_failed(detail=detail, payload=payload)
        return step_success(detail=detail, payload=payload)

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="dependency", runner=dependency_step),
            TopicStep(name="import_graph", runner=import_step),
            TopicStep(name="placeholders", runner=placeholder_step),
            TopicStep(name="cleanup", runner=cleanup_step, continue_on_failure=False),
            TopicStep(name="typecheck", runner=typecheck_step),
            TopicStep(name="refresh_baselines", runner=baselines_step),
        ],
        stop_on_failure=False,
    )

    result = pipeline.run(context)
    failed_steps = [step for step in result.steps if step.status == "failed"]
    if failed_steps:
        LOGGER.error("Pipeline encountered failures")
    dependency_outcome = dependency_holder.get("value")
    if dependency_outcome is None:
        raise RuntimeError("Dependency step did not produce an outcome")
    import_outcome = import_holder.get("value")
    placeholder_outcome = placeholder_holder.get("value")
    if placeholder_outcome is None:
        raise RuntimeError("Placeholder step did not produce an outcome")
    cleanup_outcome = cleanup_holder.get("value")
    typecheck_outcome = typecheck_holder.get("value")
    baselines_outcome = baseline_holder.get("value")

    run_slug = _timestamp_to_slug(options.run_timestamp)
    telemetry = build_pipeline_telemetry(result, viewer=VIEWER_SLUG, topic=TOPIC_SLUG, run_slug=run_slug)
    completed_at = datetime.now(timezone.utc)
    telemetry_payload = telemetry.as_dict()

    artifacts_section: dict[str, Any] = {
        "dependency_report": _relativize(dependency_outcome.report_json, paths.repo_root),
        "dependency_markdown": _relativize(dependency_outcome.report_md, paths.repo_root),
        "dependency_log": _relativize(dependency_outcome.log_path, paths.repo_root),
        "placeholder_report": _relativize(placeholder_outcome.report_json, paths.repo_root),
        "placeholder_matches": _relativize(placeholder_outcome.matches_json, paths.repo_root),
        "placeholder_log": _relativize(placeholder_outcome.log_path, paths.repo_root),
    }
    if import_outcome:
        artifacts_section["import_graph_report"] = _relativize(import_outcome.report_json, paths.repo_root)
        artifacts_section["import_graph_graph"] = _relativize(import_outcome.graph_path, paths.repo_root)
        artifacts_section["import_graph_log"] = _relativize(import_outcome.log_path, paths.repo_root)
    if cleanup_outcome:
        artifacts_section["batch_cleanup_summary"] = _relativize(cleanup_outcome.summary_path, paths.repo_root)
        artifacts_section["batch_cleanup_log"] = _relativize(cleanup_outcome.log_path, paths.repo_root)
        artifacts_section["batch_cleanup_bundle"] = _relativize(cleanup_outcome.bundle_dir, paths.repo_root)
        artifacts_section["batch_cleanup_bundle_summary"] = _relativize(cleanup_outcome.bundle_summary, paths.repo_root)
    if typecheck_outcome:
        artifacts_section["typecheck_report"] = _relativize(typecheck_outcome.report_json, paths.repo_root)
        artifacts_section["typecheck_markdown"] = _relativize(typecheck_outcome.report_md, paths.repo_root)
        artifacts_section["typecheck_log"] = _relativize(typecheck_outcome.log_path, paths.repo_root)
        artifacts_section["typecheck_raw"] = _relativize(typecheck_outcome.raw_output, paths.repo_root)
    if baselines_outcome:
        artifacts_section["mypy_baseline_summary"] = _relativize(baselines_outcome.summary_path, paths.repo_root)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "dependency_patterns": list(options.dependency_patterns),
            "dependency_skip_pyproject": options.dependency_skip_pyproject,
            "import_owned": list(options.import_owned),
            "placeholder_allowlist": _relativize(paths.placeholder_allowlist, paths.repo_root),
            "placeholder_extensions": list(options.placeholder_extensions),
            "placeholder_patterns": list(options.placeholder_patterns),
            "placeholder_exclude_prefixes": list(options.placeholder_exclude_prefixes or ()),
            "skip_import_graph": options.skip_import_graph,
            "skip_typecheck": options.skip_typecheck,
            "trigger_batch_cleanup": options.trigger_batch_cleanup,
            "refresh_mypy_baselines": options.refresh_mypy_baselines,
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
    }

    summary_content = _summarize_markdown(
        slug=run_slug,
        telemetry_success=telemetry.success,
        dependency=dependency_outcome,
        import_graph=import_outcome,
        placeholder=placeholder_outcome,
        cleanup=cleanup_outcome,
        typecheck=typecheck_outcome,
        baselines=baselines_outcome,
        step_reports=[(step.name, step.status, step.detail) for step in result.steps],
    )

    artifacts = [
        ReportArtifact(filename="manifest.json", kind="json", content=lambda: manifest),
        ReportArtifact(filename="summary.md", kind="text", content=lambda: summary_content),
        ReportArtifact(filename="telemetry.json", kind="json", content=lambda: telemetry_payload),
    ]
    result_artifacts = write_report_artifacts(
        stem=HEALTHVIEW_TOPIC,
        timestamp=options.run_timestamp,
        output_dir=paths.healthview_root,
        artifacts=artifacts,
        keep=options.artifacts_to_keep,
        viewer=VIEWER_SLUG,
        topic=HEALTHVIEW_TOPIC,
    )

    artifact_metrics = measure_artifact_directory(result_artifacts.run_dir)
    metrics_section = telemetry_payload.setdefault("metrics", {})
    metrics_section.update(artifact_metrics.as_dict())
    manifest["telemetry"] = telemetry_payload
    manifest["metrics"] = dict(metrics_section)

    manifest_path = result_artifacts.artifacts["manifest.json"]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    telemetry_path = result_artifacts.artifacts["telemetry.json"]
    telemetry_path.write_text(json.dumps(telemetry_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    LOGGER.info("Dependency & Import Hygiene orchestrator complete (slug=%s)", run_slug)
    return 0 if telemetry.success else 1


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))
