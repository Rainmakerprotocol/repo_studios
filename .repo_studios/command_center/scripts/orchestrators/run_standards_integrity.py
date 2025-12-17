#!/usr/bin/env python3
"""Topic orchestrator for standards integrity.

Publishes consolidated manifest, summary, and telemetry files to
`.repo_studios/command_center/reports/healthview/standards_integrity/<timestamp>/` and supersedes both
`scripts/orchestrators/run_standards_gap_suite.py` and
`scripts/orchestrators/run_standards_index_cli.py`. The pipeline regenerates the standards index,
performs gap analysis and diffing, seeds prompt packs, and invokes the summarizer so Healthview and
CommandView stay aligned. Runtime typically lands between five and eight minutes, with diff scopes
and prompt generation driving the upper bound.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence, cast

from command_center.scripts.libraries import (
    CatalogRegistry,
    GuardrailViolationError,
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
    enforce_report_naming,
    measure_artifact_directory,
    step_failed,
    step_skipped,
    step_success,
    write_report_artifacts,
)

LOGGER = logging.getLogger(__name__)

TOPIC_SLUG = "standards-integrity"
HEALTHVIEW_TOPIC = "standards_integrity"
VIEWER_SLUG = "healthview"
SCHEMA_VERSION = 1

GENERATE_SCRIPT = Path(".repo_studios/scripts/producers/generate_standards_index.py")
GAP_SCRIPT = Path(".repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py")
DIFF_SCRIPT = Path(".repo_studios/scripts/producers/diff_standards_index.py")
PROMPT_SCRIPT = Path(".repo_studios/scripts/producers/seed_standards_prompts.py")
SUMMARY_SCRIPT = Path(".repo_studios/scripts/summarizers/summarize_standards.py")

GENERATE_MODULE = "scripts.producers.generate_standards_index"
GAP_MODULE = "command_center.scripts.producers.analyze_standards_index_gaps"
DIFF_MODULE = "scripts.producers.diff_standards_index"
PROMPT_MODULE = "scripts.producers.seed_standards_prompts"
SUMMARY_MODULE = "scripts.summarizers.summarize_standards"

DEFAULT_INDEX_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports")
DEFAULT_INDEX_PATH = Path(".repo_studios/scripts/repo_standards_index.yaml")
DEFAULT_CATEGORIES_PATH = Path(".repo_studios/scripts/.repo_studios/standards_categories.yaml")
DEFAULT_GAP_OUTPUT_DIR = Path(".repo_studios/command_center/reports")
DEFAULT_DIFF_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_index_diff_reports")
DEFAULT_PROMPT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/standards_prompt_seeds")
DEFAULT_PENDING_PATH = Path(".repo_studios/scripts/repo_standards_pending.yaml")
DEFAULT_HEALTHVIEW_ROOT = Path(".repo_studios/command_center/reports")

INDEX_VIEWER_SLUG = "rawview"
INDEX_TOPIC_SLUG = "standards_index"
DIFF_RUN_PREFIX = "standards_index_diff-"
PROMPT_RUN_PREFIX = "standards_prompt_seed-"


def _format_run_slug(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y%m%d-%H%M")


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    index_output_dir: Path
    index_latest_path: Path
    categories_path: Path
    gap_output_dir: Path
    diff_output_dir: Path
    prompt_output_dir: Path
    pending_path: Path
    healthview_root: Path


PATHS_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs={
        "index_output_dir": PathSpec(
            field="index_output_dir", default=DEFAULT_INDEX_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "index_latest_path": PathSpec(field="index_path", default=DEFAULT_INDEX_PATH, within_repo=False),
        "categories_path": PathSpec(field="categories_path", default=DEFAULT_CATEGORIES_PATH, within_repo=False),
        "gap_output_dir": PathSpec(
            field="gap_output_dir", default=DEFAULT_GAP_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "diff_output_dir": PathSpec(
            field="diff_output_dir", default=DEFAULT_DIFF_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "prompt_output_dir": PathSpec(
            field="prompt_output_dir", default=DEFAULT_PROMPT_OUTPUT_DIR, ensure_dir=True, within_repo=False
        ),
        "pending_path": PathSpec(field="pending_path", default=DEFAULT_PENDING_PATH, within_repo=False),
        "healthview_root": PathSpec(
            field="healthview_root", default=DEFAULT_HEALTHVIEW_ROOT, ensure_dir=True, within_repo=False
        ),
    },
    repo_root_depth=4,
)


@dataclass(frozen=True)
class KeepParameters:
    artifacts_to_keep: int
    index_keep: int
    gap_keep: int
    diff_keep: int
    prompt_keep: int


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=KeepParameters,
    keep_specs={
        "artifacts_to_keep": KeepSpec(field="artifacts_to_keep", minimum=1),
        "index_keep": KeepSpec(field="index_artifacts_to_keep", minimum=1),
        "gap_keep": KeepSpec(field="gap_artifacts_to_keep", minimum=1),
        "diff_keep": KeepSpec(field="diff_artifacts_to_keep", minimum=1),
        "prompt_keep": KeepSpec(field="prompt_artifacts_to_keep", minimum=1),
    },
)


@dataclass(frozen=True)
class Options:
    log_level: str
    artifacts_to_keep: int
    index_keep: int
    gap_keep: int
    diff_keep: int
    prompt_keep: int
    gap_max_show: int
    diff_old_index: Path | None
    diff_fail_on: str
    prompt_include_warn: bool
    prompt_formats: tuple[str, ...] | None
    run_timestamp: datetime


@dataclass(frozen=True)
class IndexOutcome:
    run_dir: Path | None
    report_path: Path | None
    payload: dict[str, Any] | None
    index_path: Path | None


@dataclass(frozen=True)
class GapOutcome:
    run_dir: Path | None
    manifest_path: Path | None
    summary_md_path: Path | None
    telemetry_path: Path | None
    payload: dict[str, Any] | None


@dataclass(frozen=True)
class DiffOutcome:
    run_dir: Path | None
    report_path: Path | None
    payload: dict[str, Any] | None
    exit_code: int | None


@dataclass(frozen=True)
class PromptOutcome:
    run_dir: Path | None
    payload: dict[str, Any] | None


@dataclass(frozen=True)
class SummaryOutcome:
    exit_code: int | None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--repo-root", help="Repository root override")
    parser.add_argument("--index-output-dir", default=str(DEFAULT_INDEX_OUTPUT_DIR))
    parser.add_argument("--index-path", default=str(DEFAULT_INDEX_PATH))
    parser.add_argument("--categories-path", default=str(DEFAULT_CATEGORIES_PATH))
    parser.add_argument("--gap-output-dir", default=str(DEFAULT_GAP_OUTPUT_DIR))
    parser.add_argument("--diff-output-dir", default=str(DEFAULT_DIFF_OUTPUT_DIR))
    parser.add_argument("--prompt-output-dir", default=str(DEFAULT_PROMPT_OUTPUT_DIR))
    parser.add_argument("--pending-path", default=str(DEFAULT_PENDING_PATH))
    parser.add_argument("--healthview-root", default=str(DEFAULT_HEALTHVIEW_ROOT))
    parser.add_argument("--diff-old-index", help="Baseline index YAML for diff step")
    parser.add_argument("--diff-fail-on", default="any", help="Fail policy forwarded to diff script")
    parser.add_argument("--gap-max-show", type=int, default=8, help="Maximum gap candidates to log per source")
    parser.add_argument("--prompt-include-warn", action="store_true", help="Include warn severity rules in seed")
    parser.add_argument(
        "--prompt-formats",
        nargs="+",
        choices=("text", "yaml", "json"),
        help="Artifact formats to materialize for the prompt seed",
    )
    parser.add_argument("--artifacts-to-keep", type=int, default=3, help="Retention budget for topic artifacts")
    parser.add_argument(
        "--index-artifacts-to-keep", type=int, default=5, help="Retention budget for standards index runs"
    )
    parser.add_argument(
        "--gap-artifacts-to-keep", type=int, default=5, help="Retention budget for gap analysis runs"
    )
    parser.add_argument(
        "--diff-artifacts-to-keep", type=int, default=10, help="Retention budget for diff runs"
    )
    parser.add_argument(
        "--prompt-artifacts-to-keep", type=int, default=5, help="Retention budget for prompt seed runs"
    )
    parser.add_argument("--timestamp", help="ISO8601 timestamp for delegated scripts")
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
    except ValueError as exc:  # pragma: no cover - defensive parsing
        raise SystemExit(f"Invalid --timestamp value: {raw}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def build_paths(args: argparse.Namespace) -> Paths:
    return cast(Paths, build_standard_paths(args, PATHS_CONFIG, origin=Path(__file__)))


def build_options(args: argparse.Namespace, *, paths: Paths) -> Options:
    keep_values = build_standard_options(args, OPTIONS_CONFIG)
    diff_old_index = _resolve_optional_path(paths.repo_root, getattr(args, "diff_old_index", None))
    prompt_formats = None
    if args.prompt_formats:
        prompt_formats = tuple(dict.fromkeys(args.prompt_formats))
    return Options(
        log_level=str(args.log_level),
        artifacts_to_keep=keep_values.artifacts_to_keep,
        index_keep=keep_values.index_keep,
        gap_keep=keep_values.gap_keep,
        diff_keep=keep_values.diff_keep,
        prompt_keep=keep_values.prompt_keep,
        gap_max_show=max(1, int(args.gap_max_show)),
        diff_old_index=diff_old_index,
        diff_fail_on=str(args.diff_fail_on),
        prompt_include_warn=bool(args.prompt_include_warn),
        prompt_formats=prompt_formats,
        run_timestamp=_parse_timestamp(getattr(args, "timestamp", None)),
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


def _execute_index(paths: Paths, options: Options) -> IndexOutcome:
    LOGGER.info("Generating standards index")
    main_callable = _load_callable(paths.repo_root / GENERATE_SCRIPT, GENERATE_MODULE, "main")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.index_output_dir),
        "--index-path",
        str(paths.index_latest_path),
        "--artifacts-to-keep",
        str(options.index_keep),
        "--log-level",
        options.log_level,
    ]
    if options.run_timestamp:
        argv.extend(["--timestamp", options.run_timestamp.isoformat()])
    exit_code = _invoke_main(main_callable, argv)
    if exit_code != 0:
        raise RuntimeError(f"generate_standards_index exit code {exit_code}")

    run_slug = _format_run_slug(options.run_timestamp)
    candidate_dir = paths.index_output_dir / INDEX_VIEWER_SLUG / INDEX_TOPIC_SLUG / run_slug
    telemetry_path = candidate_dir / "telemetry.json"
    payload = _read_json(telemetry_path)
    if payload is None:
        raise RuntimeError("standards index telemetry missing after run")

    index_path = paths.index_latest_path if paths.index_latest_path.exists() else None
    return IndexOutcome(run_dir=candidate_dir, report_path=telemetry_path, payload=payload, index_path=index_path)


def _execute_gap(paths: Paths, options: Options) -> GapOutcome:
    LOGGER.info("Analyzing standards index gaps")
    run_callable = _load_callable(paths.repo_root / GAP_SCRIPT, GAP_MODULE, "run")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.gap_output_dir),
        "--index-path",
        str(paths.index_latest_path),
        "--categories-path",
        str(paths.categories_path),
        "--artifacts-to-keep",
        str(options.gap_keep),
        "--log-level",
        options.log_level,
        "--max",
        str(options.gap_max_show),
    ]
    if options.run_timestamp:
        argv.extend(["--timestamp", options.run_timestamp.isoformat()])
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("analyze_standards_index_gaps returned unexpected payload")
    run_dir = Path(payload.get("run_dir", "")).resolve() if payload.get("run_dir") else None
    if run_dir and not run_dir.exists():
        run_dir = None

    manifest_path = Path(payload.get("manifest_json", "")).resolve() if payload.get("manifest_json") else None
    if manifest_path and not manifest_path.exists():
        manifest_path = None
    summary_md_path = Path(payload.get("summary_md", "")).resolve() if payload.get("summary_md") else None
    if summary_md_path and not summary_md_path.exists():
        summary_md_path = None
    telemetry_path = Path(payload.get("telemetry_json", "")).resolve() if payload.get("telemetry_json") else None
    if telemetry_path and not telemetry_path.exists():
        telemetry_path = None
    return GapOutcome(
        run_dir=run_dir,
        manifest_path=manifest_path,
        summary_md_path=summary_md_path,
        telemetry_path=telemetry_path,
        payload=payload,
    )


def _execute_diff(paths: Paths, options: Options, index_outcome: IndexOutcome) -> DiffOutcome:
    if options.diff_old_index is None:
        return DiffOutcome(run_dir=None, report_path=None, payload=None, exit_code=None)
    if index_outcome.index_path is None or not index_outcome.index_path.exists():
        raise RuntimeError("standards index pointer missing for diff step")
    if not options.diff_old_index.exists():
        raise RuntimeError(f"Baseline index not found: {options.diff_old_index}")

    LOGGER.info("Diffing standards index against baseline")
    main_callable = _load_callable(paths.repo_root / DIFF_SCRIPT, DIFF_MODULE, "main")
    argv = [
        str(options.diff_old_index),
        str(index_outcome.index_path),
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.diff_output_dir),
        "--artifacts-to-keep",
        str(options.diff_keep),
        "--log-level",
        options.log_level,
        "--fail-on",
        options.diff_fail_on,
    ]
    if options.run_timestamp:
        argv.extend(["--timestamp", options.run_timestamp.isoformat()])
    exit_code = _invoke_main(main_callable, argv)

    latest_report = paths.diff_output_dir / "latest_report.json"
    payload = _read_json(latest_report)
    run_dir = None
    report_path = None
    if payload is not None:
        slug = str(payload.get("timestamp") or "")
        candidate = paths.diff_output_dir / f"{DIFF_RUN_PREFIX}{slug}" if slug else None
        if candidate and candidate.exists():
            run_dir = candidate
            report_candidate = candidate / "report.json"
            if report_candidate.exists():
                report_path = report_candidate
    return DiffOutcome(run_dir=run_dir, report_path=report_path, payload=payload, exit_code=exit_code)


def _execute_prompts(paths: Paths, options: Options) -> PromptOutcome:
    LOGGER.info("Seeding standards prompt bundles")
    run_callable = _load_callable(paths.repo_root / PROMPT_SCRIPT, PROMPT_MODULE, "run")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--output-dir",
        str(paths.prompt_output_dir),
        "--index-path",
        str(paths.index_latest_path),
        "--artifacts-to-keep",
        str(options.prompt_keep),
        "--log-level",
        options.log_level,
    ]
    if options.prompt_include_warn:
        argv.append("--include-warn")
    if options.prompt_formats:
        argv.append("--artifact-formats")
        argv.extend(options.prompt_formats)
    payload = run_callable(argv)
    if not isinstance(payload, dict):
        raise RuntimeError("seed_standards_prompts returned unexpected payload")
    run_id = payload.get("run_id")
    run_dir = None
    if isinstance(run_id, str) and run_id:
        candidate = paths.prompt_output_dir / run_id
        if candidate.exists():
            run_dir = candidate
    return PromptOutcome(run_dir=run_dir, payload=payload)


def _execute_summary(paths: Paths, *, index_outcome: IndexOutcome) -> SummaryOutcome:
    if index_outcome.index_path is None or not index_outcome.index_path.exists():
        raise RuntimeError("standards index pointer missing for summary step")
    summarize_callable = _load_callable(paths.repo_root / SUMMARY_SCRIPT, SUMMARY_MODULE, "summarize")
    exit_code = summarize_callable("summary", index_outcome.index_path, paths.pending_path)
    return SummaryOutcome(exit_code=exit_code if isinstance(exit_code, int) else 0)


def _register_scripts(registry: CatalogRegistry) -> None:
    registry.register(
        script_path=str(Path(".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py")),
        topic=TOPIC_SLUG,
        role="orchestrator",
    )
    registry.register(script_path=str(GENERATE_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(GAP_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(DIFF_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(PROMPT_SCRIPT), topic=TOPIC_SLUG, role="producer")
    registry.register(script_path=str(SUMMARY_SCRIPT), topic=TOPIC_SLUG, role="summarizer")


def _summarize_markdown(
    *,
    slug: str,
    telemetry_success: bool,
    index_outcome: IndexOutcome,
    gap_outcome: GapOutcome | None,
    diff_outcome: DiffOutcome | None,
    prompt_outcome: PromptOutcome | None,
    summary_outcome: SummaryOutcome | None,
    step_reports: Iterable[tuple[str, str, str | None]],
) -> str:
    lines: list[str] = []
    lines.append("# Standards Integrity Summary")
    lines.append("")
    lines.append(f"- run_slug: `{slug}`")
    lines.append(f"- pipeline_status: {'success' if telemetry_success else 'failed'}")

    index_payload = index_outcome.payload if isinstance(index_outcome.payload, dict) else {}
    index_status = index_payload.get("status")
    raw_index_summary = index_payload.get("summary")
    index_summary: dict[str, Any] = raw_index_summary if isinstance(raw_index_summary, dict) else {}
    lines.append(f"- index_status: {index_status or 'unknown'}")
    lines.append(f"- index_rule_count: {index_summary.get('rule_count', 'unknown')}")
    if index_payload.get("integrity_hash"):
        lines.append(f"- index_integrity_hash: `{index_payload['integrity_hash']}`")

    gap_payload = gap_outcome.payload if gap_outcome and isinstance(gap_outcome.payload, dict) else {}
    raw_gap_summary = gap_payload.get("summary")
    gap_summary: dict[str, Any] = raw_gap_summary if isinstance(raw_gap_summary, dict) else {}
    lines.append(f"- gap_total_candidates: {gap_summary.get('total_candidates', 'unknown')}")
    lines.append(f"- gap_sources_with_candidates: {gap_summary.get('sources_with_candidates', 'unknown')}")

    if diff_outcome is None:
        lines.append("- diff_exit_code: skipped")
        lines.append("- diff_status: skipped")
        lines.append("- diff_change_count: skipped")
    else:
        diff_payload = diff_outcome.payload if isinstance(diff_outcome.payload, dict) else {}
        diff_status = diff_payload.get("status") if diff_payload else None
        diff_change_count = diff_payload.get("change_count") if diff_payload else None
        exit_code = diff_outcome.exit_code
        lines.append(f"- diff_exit_code: {exit_code if exit_code is not None else 'skipped'}")
        status_value = diff_status or ("skipped" if exit_code is None else "unknown")
        lines.append(f"- diff_status: {status_value}")
        change_value = diff_change_count if diff_change_count is not None else ("skipped" if exit_code is None else "unknown")
        lines.append(f"- diff_change_count: {change_value}")

    prompt_payload = prompt_outcome.payload if prompt_outcome and isinstance(prompt_outcome.payload, dict) else {}
    raw_prompt_summary = prompt_payload.get("summary")
    prompt_summary: dict[str, Any] = raw_prompt_summary if isinstance(raw_prompt_summary, dict) else {}
    lines.append(f"- prompt_total_rules: {prompt_summary.get('total_rules', 'unknown')}")
    lines.append(f"- prompt_category_count: {prompt_summary.get('category_count', 'unknown')}")

    summary_code = summary_outcome.exit_code if summary_outcome else None
    lines.append(f"- summarize_exit_code: {summary_code if summary_code is not None else 'skipped'}")
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
    options = build_options(args, paths=paths)
    configure_logging(options.log_level)

    registry = CatalogRegistry()
    _register_scripts(registry)

    context = TopicContext(paths=paths, options=options, metadata={})

    index_holder: dict[str, IndexOutcome] = {}
    gap_holder: dict[str, GapOutcome] = {}
    diff_holder: dict[str, DiffOutcome] = {}
    prompt_holder: dict[str, PromptOutcome] = {}
    summary_holder: dict[str, SummaryOutcome] = {}

    def index_step(ctx: TopicContext):
        try:
            outcome = _execute_index(paths, options)
        except RuntimeError as exc:
            return step_failed(detail=str(exc))
        index_holder["value"] = outcome
        ctx.add_metadata("index", outcome)
        payload = outcome.payload if isinstance(outcome.payload, dict) else {}
        raw_summary = payload.get("summary")
        summary: dict[str, Any] = raw_summary if isinstance(raw_summary, dict) else {}
        detail_bits: list[str] = []
        if payload.get("status"):
            detail_bits.append(f"status={payload['status']}")
        rules = summary.get("rule_count")
        if isinstance(rules, int):
            detail_bits.append(f"rules={rules}")
        detail = ", ".join(detail_bits) if detail_bits else "index generated"
        step_payload = {
            "status": payload.get("status"),
            "rule_count": rules,
            "integrity_hash": payload.get("integrity_hash"),
        }
        return step_success(detail=detail, payload=step_payload)

    def gap_step(ctx: TopicContext):
        try:
            outcome = _execute_gap(paths, options)
        except RuntimeError as exc:
            return step_failed(detail=str(exc))
        gap_holder["value"] = outcome
        ctx.add_metadata("gap", outcome)
        payload = outcome.payload if isinstance(outcome.payload, dict) else {}
        raw_summary = payload.get("summary")
        summary: dict[str, Any] = raw_summary if isinstance(raw_summary, dict) else {}
        candidates = summary.get("total_candidates")
        detail = f"candidates={candidates}" if candidates is not None else "analysis completed"
        step_payload = {
            "total_candidates": candidates,
            "sources_with_candidates": summary.get("sources_with_candidates"),
        }
        return step_success(detail=detail, payload=step_payload)

    def diff_step(ctx: TopicContext):
        if options.diff_old_index is None:
            return step_skipped(detail="diff-old-index not provided")
        index_outcome = index_holder.get("value")
        if index_outcome is None:
            return step_failed(detail="index outcome missing")
        try:
            outcome = _execute_diff(paths, options, index_outcome)
        except RuntimeError as exc:
            return step_failed(detail=str(exc))
        diff_holder["value"] = outcome
        ctx.add_metadata("diff", outcome)
        payload = outcome.payload if isinstance(outcome.payload, dict) else {}
        change_count = payload.get("change_count")
        detail = f"changes={change_count}" if change_count is not None else "diff completed"
        step_payload = {
            "status": payload.get("status"),
            "change_count": change_count,
            "should_fail": payload.get("should_fail"),
        }
        if outcome.exit_code and outcome.exit_code != 0:
            return step_failed(detail=detail, payload=step_payload)
        return step_success(detail=detail, payload=step_payload)

    def prompt_step(ctx: TopicContext):
        index_outcome = index_holder.get("value")
        if index_outcome is None or index_outcome.index_path is None:
            return step_failed(detail="standards index missing for prompt seed")
        try:
            outcome = _execute_prompts(paths, options)
        except RuntimeError as exc:
            return step_failed(detail=str(exc))
        prompt_holder["value"] = outcome
        ctx.add_metadata("prompt", outcome)
        payload = outcome.payload if isinstance(outcome.payload, dict) else {}
        raw_summary = payload.get("summary")
        summary: dict[str, Any] = raw_summary if isinstance(raw_summary, dict) else {}
        total_rules = summary.get("total_rules")
        detail = f"rules={total_rules}" if total_rules is not None else "prompt seed generated"
        step_payload = {
            "run_id": payload.get("run_id"),
            "total_rules": total_rules,
            "category_count": summary.get("category_count"),
        }
        status = payload.get("status")
        if status and status != "ok":
            return step_failed(detail=detail, payload=step_payload)
        return step_success(detail=detail, payload=step_payload)

    def summary_step(ctx: TopicContext):
        index_outcome = index_holder.get("value")
        if index_outcome is None:
            return step_skipped(detail="index outcome missing")
        if index_outcome.index_path is None or not index_outcome.index_path.exists():
            return step_skipped(detail="standards index not available for summary")
        try:
            outcome = _execute_summary(paths, index_outcome=index_outcome)
        except RuntimeError as exc:
            return step_failed(detail=str(exc))
        summary_holder["value"] = outcome
        ctx.add_metadata("summary", outcome)
        if outcome.exit_code and outcome.exit_code != 0:
            return step_failed(detail=f"summarizer exit {outcome.exit_code}")
        return step_success(detail="summarizer completed")

    pipeline = build_topic_pipeline(
        steps=[
            TopicStep(name="index", runner=index_step),
            TopicStep(name="gap", runner=gap_step),
            TopicStep(name="diff", runner=diff_step),
            TopicStep(name="prompts", runner=prompt_step),
            TopicStep(name="summary", runner=summary_step, continue_on_failure=False),
        ]
    )

    result = pipeline.run(context)
    try:
        result.raise_for_failure()
    except RuntimeError as exc:
        LOGGER.error("Pipeline failed: %s", exc)
        return 1

    index_outcome = index_holder.get("value") or IndexOutcome(
        run_dir=None, report_path=None, payload=None, index_path=paths.index_latest_path if paths.index_latest_path.exists() else None
    )
    gap_outcome = gap_holder.get("value") or GapOutcome(
        run_dir=None,
        manifest_path=None,
        summary_md_path=None,
        telemetry_path=None,
        payload=None,
    )
    diff_outcome = diff_holder.get("value") or DiffOutcome(run_dir=None, report_path=None, payload=None, exit_code=None)
    prompt_outcome = prompt_holder.get("value") or PromptOutcome(run_dir=None, payload=None)
    summary_outcome = summary_holder.get("value") or SummaryOutcome(exit_code=None)

    run_slug = options.run_timestamp.strftime("%Y%m%d-%H%M")
    telemetry = build_pipeline_telemetry(result, viewer=VIEWER_SLUG, topic=TOPIC_SLUG, run_slug=run_slug)
    completed_at = datetime.now(timezone.utc)
    telemetry_payload = telemetry.as_dict()

    artifacts_section: dict[str, Any] = {
        "index_run": _relativize(index_outcome.run_dir, paths.repo_root),
        "index_report": _relativize(index_outcome.report_path, paths.repo_root),
        "gap_run": _relativize(gap_outcome.run_dir, paths.repo_root),
        "gap_manifest": _relativize(gap_outcome.manifest_path, paths.repo_root),
        "gap_summary_md": _relativize(gap_outcome.summary_md_path, paths.repo_root),
        "gap_telemetry": _relativize(gap_outcome.telemetry_path, paths.repo_root),
        "diff_run": _relativize(diff_outcome.run_dir, paths.repo_root),
        "diff_report": _relativize(diff_outcome.report_path, paths.repo_root),
        "prompt_run": _relativize(prompt_outcome.run_dir, paths.repo_root),
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "viewer": VIEWER_SLUG,
        "topic": HEALTHVIEW_TOPIC,
        "run_slug": run_slug,
        "generated_at": completed_at.isoformat(),
        "telemetry": telemetry_payload,
        "artifacts": artifacts_section,
        "inputs": {
            "index_path": _relativize(paths.index_latest_path, paths.repo_root),
            "categories_path": _relativize(paths.categories_path, paths.repo_root),
            "diff_old_index": _relativize(options.diff_old_index, paths.repo_root),
            "pending_path": _relativize(paths.pending_path, paths.repo_root),
        },
        "catalog": [entry.__dict__ for entry in registry.all_entries()],
    }

    summary_content = _summarize_markdown(
        slug=run_slug,
        telemetry_success=telemetry.success,
        index_outcome=index_outcome,
        gap_outcome=gap_outcome,
        diff_outcome=diff_outcome,
        prompt_outcome=prompt_outcome,
        summary_outcome=summary_outcome,
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

    try:
        enforce_report_naming(
            reports_root=paths.healthview_root,
            run_dir=result_artifacts.run_dir,
            viewer=VIEWER_SLUG,
            topic=HEALTHVIEW_TOPIC,
            artifact_roles=("manifest.json", "summary.md", "summary.json", "telemetry.json"),
        )
    except GuardrailViolationError as exc:
        LOGGER.error("Report naming audit failed: %s", exc)
        return 1

    LOGGER.info("Standards Integrity orchestrator complete (slug=%s)", run_slug)
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    raise SystemExit(run(argv))


__all__ = ["run", "main", "parse_args", "build_paths", "build_options"]


if __name__ == "__main__":
    main()
