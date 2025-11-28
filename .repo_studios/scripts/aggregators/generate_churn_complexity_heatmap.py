#!/usr/bin/env python3
"""Generate a churn × complexity heatmap with provenance and retention."""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import shutil
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_REPO_ROOT = Path(".")
DEFAULT_OUTPUT_BASE = Path(".repo_studios/reports/aggregator_reports/churn_complexity_heatmap")
DEFAULT_TEST_LOG_SUMMARY = Path(
    ".repo_studios/reports/consumer_reports/test_log_health_reports/latest/bundle_summary.json"
)
DEFAULT_LOGS_DIR = Path(".repo_studios/reports/orchestrator_logs/pytest_log_capture_logs")
LEGACY_LOGS_DIR = Path(".repo_studios/pytest_logs")
DEFAULT_METRICS_SOURCE: Path | None = None
DEFAULT_WINDOW = 500
DEFAULT_ARTIFACTS_TO_KEEP = 10

RUN_PREFIX = "churn_complexity_heatmap-"
HEATMAP_JSON = "heatmap.json"
HEATMAP_MD = "heatmap.md"
BUNDLE_SUMMARY = "bundle_summary.json"

PY_EXT = ".py"


@dataclass(frozen=True)
class MetricRecord:
    file: str
    churn: int
    complexity: int
    failures: int


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate churn, complexity, and failure density into a trend heatmap"
    )
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    parser.add_argument("--output-base", type=Path, default=DEFAULT_OUTPUT_BASE)
    parser.add_argument("--test-log-summary", type=Path, default=DEFAULT_TEST_LOG_SUMMARY)
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS_DIR)
    parser.add_argument("--metrics-source", type=Path, default=DEFAULT_METRICS_SOURCE)
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args(argv)


def _resolve_path(base: Path, candidate: Path) -> Path:
    return candidate if candidate.is_absolute() else (base / candidate).resolve()


def _configure_logging(level: str, verbose: bool) -> logging.Logger:
    resolved = logging.DEBUG if verbose else getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=resolved, format="[%(levelname)s] %(message)s", force=True)
    return logging.getLogger("generate_churn_complexity_heatmap")


def _ensure_run_dir(base: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H%M%S")
    run_dir = base / f"{RUN_PREFIX}{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _discover_summary_path(candidate: Path, logger: logging.Logger) -> Path | None:
    if candidate.exists() and candidate.is_file():
        return candidate
    if candidate.exists() and candidate.is_dir():
        potential = candidate / BUNDLE_SUMMARY
        if potential.exists():
            return potential
    base = candidate.parent if candidate.suffix else candidate
    if not base.exists():
        logger.debug("Test log summary base %s does not exist", base)
        return None
    run_dirs = sorted(
        [child for child in base.iterdir() if child.is_dir()],
        key=lambda path: path.name,
        reverse=True,
    )
    for run_dir in run_dirs:
        summary = run_dir / BUNDLE_SUMMARY
        if summary.exists():
            return summary
    return None


def _read_json(path: Path, logger: logging.Logger) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Failed to load JSON from %s: %s", path, exc)
        return None
    return payload if isinstance(payload, dict) else None


def _load_metrics_from_source(path: Path, logger: logging.Logger) -> list[MetricRecord]:
    payload = _read_json(path, logger)
    if not payload:
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        logger.warning("Metrics source %s missing 'items' list", path)
        return []
    records: list[MetricRecord] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        file = entry.get("file")
        if not isinstance(file, str):
            continue
        churn = int(entry.get("churn", 0))
        complexity = int(entry.get("complexity", 0))
        failures = int(entry.get("failures", 0))
        records.append(MetricRecord(file=file, churn=churn, complexity=complexity, failures=failures))
    return records


def _scan_python_files(root: Path) -> Iterable[Path]:
    ignores = {".git", ".venv", "__pycache__", "node_modules"}
    for path in root.rglob("*.py"):
        if any(part in ignores for part in path.parts):
            continue
        yield path


def _collect_git_churn(root: Path, window: int, logger: logging.Logger) -> Counter[str]:
    cmd = ["git", "--no-pager", "log", f"-n{window}", "--name-only", "--pretty=format:"]
    try:
        result = subprocess.run(
            cmd,
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        logger.warning("Git command failed for churn collection: %s", exc)
        return Counter()
    if result.returncode != 0:
        logger.warning("Git churn command returned %s: %s", result.returncode, result.stderr.strip())
        return Counter()
    files = [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(PY_EXT)]
    counter: Counter[str] = Counter()
    for entry in files:
        counter[entry.replace("\\", "/")] += 1
    return counter


def _complexity_score(path: Path) -> int:
    import ast

    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return 0
    count = 0
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.BoolOp,
        ast.IfExp,
        ast.Match,
    )
    for node in ast.walk(tree):
        if isinstance(node, branch_nodes):
            count += 1
    return count


def _prepare_metrics(
    *,
    repo_root: Path,
    metrics_source: Path | None,
    window: int,
    logger: logging.Logger,
) -> tuple[list[MetricRecord], list[str]]:
    notes: list[str] = []
    if metrics_source is not None and metrics_source.exists():
        metrics = _load_metrics_from_source(metrics_source, logger)
        if metrics:
            notes.append(f"Metrics preloaded from {metrics_source}")
            return metrics, notes
        notes.append(f"Metrics source {metrics_source} was empty; recomputing from repo")

    churn = _collect_git_churn(repo_root, window, logger)
    metrics: list[MetricRecord] = []
    for path in _scan_python_files(repo_root):
        rel = path.relative_to(repo_root).as_posix()
        metrics.append(
            MetricRecord(
                file=rel,
                churn=churn.get(rel, 0),
                complexity=_complexity_score(path),
                failures=0,
            )
        )
    return metrics, notes


def _normalize_relative(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _load_junit_failures(path: Path | None, repo_root: Path, logger: logging.Logger) -> Counter[str]:
    if path is None or not path.exists():
        return Counter()
    try:
        from defusedxml import ElementTree
    except ImportError:
        import xml.etree.ElementTree as ElementTree  # type: ignore

        logger.debug("defusedxml unavailable; falling back to xml.etree.ElementTree for junit parse")
    try:
        root = ElementTree.parse(path).getroot()
    except Exception as exc:
        logger.warning("Failed to parse junit report %s: %s", path, exc)
        return Counter()
    counter: Counter[str] = Counter()
    for testcase in root.iterfind(".//testcase"):
        has_failure = testcase.find("failure") is not None or testcase.find("error") is not None
        if not has_failure:
            continue
        file_attr = testcase.get("file")
        classname = testcase.get("classname")
        detected = None
        if file_attr:
            raw_path = Path(file_attr)
            detected = raw_path if raw_path.is_absolute() else (repo_root / raw_path)
        elif classname:
            detected = repo_root / (classname.replace(".", "/") + PY_EXT)
        if detected is None:
            continue
        rel = _normalize_relative(detected, repo_root)
        counter[rel] += 1
    return counter


def _discover_junit_from_summary(
    summary: dict[str, Any] | None,
    report: dict[str, Any] | None,
    logger: logging.Logger,
) -> Path | None:
    _ = summary  # preserved for future metadata expansion
    if report:
        meta = report.get("meta")
        if isinstance(meta, dict):
            junit = meta.get("junit")
            if isinstance(junit, str):
                junit_path = Path(junit)
                if junit_path.exists():
                    return junit_path
    return None


def _load_consumer_bundle(
    summary_path: Path | None,
    logger: logging.Logger,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    notes: list[str] = []
    if summary_path is None:
        return None, None, notes
    summary = _read_json(summary_path, logger)
    if summary is None:
        notes.append(f"Unable to parse consumer bundle summary at {summary_path}")
        return None, None, notes
    artifacts = summary.get("artifacts", {})
    report_path_str = artifacts.get("report_json") if isinstance(artifacts, dict) else None
    report_path = Path(report_path_str) if isinstance(report_path_str, str) else None
    report = None
    if report_path and report_path.exists():
        report = _read_json(report_path, logger)
    else:
        notes.append("Consumer bundle summary missing accessible report_json; failure counts may degrade")
    return summary, report, notes


def _discover_logs_junit(logs_dir: Path) -> Path | None:
    if not logs_dir.exists():
        return None
    junit_candidates = sorted(
        [path for path in logs_dir.rglob("junit_*.xml") if path.is_file()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return junit_candidates[0] if junit_candidates else None


def _allow_legacy_logs() -> bool:
    flag = os.environ.get("CHURN_HEATMAP_ALLOW_LEGACY", "1").strip().lower()
    return flag not in {"0", "false", "no", "off"}


def _choose_logs_dir(repo_root: Path, candidate: Path, logger: logging.Logger) -> tuple[Path, Path | None]:
    junit = _discover_logs_junit(candidate)
    if junit is not None or not _allow_legacy_logs():
        return candidate, junit

    legacy = _resolve_path(repo_root, LEGACY_LOGS_DIR)
    legacy_junit = _discover_logs_junit(legacy)
    if legacy_junit is not None:
        logger.info(
            "JUnit artifacts not found under %s; falling back to legacy logs at %s",
            candidate,
            legacy,
        )
        return legacy, legacy_junit

    return candidate, junit


def _git_head(repo_root: Path, logger: logging.Logger) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        logger.debug("Unable to resolve git HEAD: %s", exc)
        return None
    if result.returncode != 0:
        logger.debug("git rev-parse returned %s: %s", result.returncode, result.stderr.strip())
        return None
    return result.stdout.strip()


def _annotate_failures(
    metrics: list[MetricRecord],
    failures: Counter[str],
) -> list[MetricRecord]:
    annotated: list[MetricRecord] = []
    for record in metrics:
        annotated.append(
            MetricRecord(
                file=record.file,
                churn=record.churn,
                complexity=record.complexity,
                failures=record.failures if record.failures else failures.get(record.file, 0),
            )
        )
    return annotated


def _score_metrics(metrics: list[MetricRecord]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for record in metrics:
        churn = max(record.churn, 0)
        complexity = max(record.complexity, 0)
        failures = max(record.failures, 0)
        score = math.log1p(churn) * math.log1p(complexity) * (1 + failures)
        scored.append(
            {
                "file": record.file,
                "churn": churn,
                "complexity": complexity,
                "failures": failures,
                "score": round(score, 4),
            }
        )
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored


def _render_markdown(
    *,
    generated_at: datetime,
    repo_root: Path,
    window: int,
    git_sha: str | None,
    mode: str,
    records: list[dict[str, Any]],
    notes: list[str],
    sources: dict[str, str | None],
) -> str:
    lines: list[str] = ["# Churn × Complexity Heatmap", ""]
    lines.append(f"Generated (UTC): {generated_at.isoformat(timespec='seconds')}")
    lines.append(f"Repo Root: `{repo_root}`")
    lines.append(f"Window: last {window} commits")
    if git_sha:
        lines.append(f"Git HEAD: `{git_sha}`")
    lines.append(f"Mode: {mode}")
    lines.append("")
    if notes:
        lines.append("## Notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append("## Top Files")
    lines.append("")
    if records:
        lines.append("| File | Churn | Complexity | Failures | Score |")
        lines.append("|---|---:|---:|---:|---:|")
        top = records[:25]
        for row in top:
            lines.append(
                f"| {row['file']} | {row['churn']} | {row['complexity']} | {row['failures']} | {row['score']:.4f} |"
            )
        if len(records) > 25:
            lines.append("")
            lines.append(f"Showing top 25 of {len(records)} files")
    else:
        lines.append("No metrics available.")
    lines.append("")
    lines.append("## Source References")
    lines.append("")
    for label, value in sources.items():
        if value:
            lines.append(f"- {label}: `{value}`")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _update_latest(base: Path, run_dir: Path) -> None:
    mapping = {
        HEATMAP_JSON: base / f"latest_{HEATMAP_JSON}",
        HEATMAP_MD: base / f"latest_{HEATMAP_MD}",
        BUNDLE_SUMMARY: base / f"latest_{BUNDLE_SUMMARY}",
    }
    for name, dest in mapping.items():
        src = run_dir / name
        if not src.exists():
            continue
        try:
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            dest.hardlink_to(src)
        except Exception:
            dest.write_bytes(src.read_bytes())


def _prune_history(base: Path, current: Path, keep: int) -> list[Path]:
    keep = max(int(keep), 1)
    if not base.exists():
        return []
    runs = sorted(
        [path for path in base.iterdir() if path.is_dir() and path.name.startswith(RUN_PREFIX) and path != current],
        key=lambda path: path.name,
        reverse=True,
    )
    stale = runs[keep - 1 :]
    for path in stale:
        try:
            shutil.rmtree(path, ignore_errors=False)
        except Exception:
            continue
    return stale


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parse_args(argv)
    logger = _configure_logging(args.log_level, args.verbose)

    repo_root = _resolve_path(Path.cwd(), args.repo_root)
    output_base = _resolve_path(repo_root, args.output_base)
    logs_dir = _resolve_path(repo_root, args.logs_dir)
    primary_logs_dir = logs_dir
    metrics_source = args.metrics_source
    if metrics_source is not None and not metrics_source.is_absolute():
        metrics_source = (repo_root / metrics_source).resolve()
    summary_candidate = args.test_log_summary
    if not summary_candidate.is_absolute():
        summary_candidate = (repo_root / summary_candidate).resolve()

    output_base.mkdir(parents=True, exist_ok=True)

    metrics, metric_notes = _prepare_metrics(
        repo_root=repo_root,
        metrics_source=metrics_source,
        window=args.window,
        logger=logger,
    )
    if not metrics:
        raise FileNotFoundError("No Python metrics available for churn × complexity analysis.")

    summary_path = _discover_summary_path(summary_candidate, logger)
    notes = list(metric_notes)
    if summary_path is None:
        notes.append(f"Consumer bundle summary not found near {summary_candidate}")
    summary_payload, report_payload, bundle_notes = _load_consumer_bundle(summary_path, logger)
    notes += bundle_notes

    junit_path = _discover_junit_from_summary(summary_payload, report_payload, logger)
    mode = "consumer"
    if junit_path is None:
        logs_dir, junit_candidate = _choose_logs_dir(repo_root, logs_dir, logger)
        junit_path = junit_candidate
        if junit_path is None:
            notes.append("JUnit artifact not found; failure density defaults to zero")
            mode = "logs_fallback"
        else:
            notes.append(f"Consumer summary unavailable; JUnit inferred from logs at {junit_path}")
            if logs_dir != primary_logs_dir:
                notes.append(f"Pytest logs sourced from legacy directory {logs_dir}")
            mode = "logs_fallback"

    failures = _load_junit_failures(junit_path, repo_root, logger)
    metrics = _annotate_failures(metrics, failures)
    scored = _score_metrics(metrics)

    generated_at = datetime.now(UTC)
    git_sha = _git_head(repo_root, logger)

    run_dir = _ensure_run_dir(output_base)
    heatmap_json_path = run_dir / HEATMAP_JSON
    heatmap_md_path = run_dir / HEATMAP_MD
    bundle_summary_path = run_dir / BUNDLE_SUMMARY

    inputs = {
        "metrics_source": str(metrics_source) if metrics_source else None,
        "test_log_summary": str(summary_path) if summary_path else None,
        "logs_dir": str(logs_dir),
        "junit": str(junit_path) if junit_path else None,
    }

    json_payload = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "repo_root": str(repo_root),
        "window": int(args.window),
        "git_sha": git_sha,
        "mode": mode,
        "notes": notes,
        "inputs": inputs,
        "items": scored,
    }
    _write_json(heatmap_json_path, json_payload)

    markdown = _render_markdown(
        generated_at=generated_at,
        repo_root=repo_root,
        window=args.window,
        git_sha=git_sha,
        mode=mode,
        records=scored,
        notes=notes,
        sources=inputs,
    )
    heatmap_md_path.write_text(markdown, encoding="utf-8")

    bundle_summary = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "mode": mode,
        "repo_root": str(repo_root),
        "window": int(args.window),
        "git_sha": git_sha,
        "inputs": inputs,
        "artifacts": {
            "heatmap_json": str(heatmap_json_path.resolve()),
            "heatmap_md": str(heatmap_md_path.resolve()),
        },
        "notes": notes,
        "summary_source": str(summary_path) if summary_path else None,
    }
    _write_json(bundle_summary_path, bundle_summary)

    _update_latest(output_base, run_dir)
    pruned = _prune_history(output_base, run_dir, args.artifacts_to_keep)

    logger.info(
        "Heatmap bundle written to %s (mode=%s, files=%d, pruned=%d)",
        run_dir,
        mode,
        len(scored),
        len(pruned),
    )

    return {
        "mode": mode,
        "output_dir": str(run_dir.resolve()),
        "heatmap_json": str(heatmap_json_path.resolve()),
        "heatmap_markdown": str(heatmap_md_path.resolve()),
        "bundle_summary": str(bundle_summary_path.resolve()),
        "notes": notes,
        "pruned": [str(path.resolve()) for path in pruned],
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        run(argv)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
