#!/usr/bin/env python3
"""Duplicate scanning utilities tailored for the Command Center workflow.

This module refactors the experimental ``scan_code_duplicates.py`` script into a
repo-aware tool that can be imported for unit tests and invoked via CLI. The
core responsibilities are:

* Discover functions across a target directory using AST inspection.
* Group exact and near-duplicate functions with similarity metrics.
* Merge scanner results with the producers companion analysis so teams obtain a
  unified duplicate matrix for prioritisation.
* Emit artifacts in the viewer/topic/timestamp hierarchy while mirroring the
    latest run into the producer index directory and pruning stale history.

The CLI entry point follows the same "run/main" pattern used throughout Repo
Studios scripts so that other tooling can shell out consistently.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util

import json
import logging
import sys
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

try:
    from libraries import (  # type: ignore  # noqa: E402
        ReportArtifact,
        WriteReportArtifactsResult,
        resolve_repo_root,
        slugify_relative,
        write_report_artifacts,
    )
except ModuleNotFoundError:  # pragma: no cover - CLI fallback
    SCRIPT_DIR = Path(__file__).resolve().parent
    SCRIPTS_ROOT = SCRIPT_DIR.parent
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))
    from libraries import (  # type: ignore  # noqa: E402
        ReportArtifact,
        WriteReportArtifactsResult,
        resolve_repo_root,
        slugify_relative,
        write_report_artifacts,
    )

DEFAULT_SIMILARITY_THRESHOLD = 0.85
DEFAULT_MIN_LINES = 3
DEFAULT_KEEP_RUNS = 3
DEFAULT_TARGET_RELATIVE = Path(".repo_studios/command_center/scripts/producers")
DEFAULT_OUTPUT_DIR = Path(".repo_studios/command_center/reports")

INVENTORY_SCRIPT_RELATIVE = Path(
    ".repo_studios/command_center/scripts/producers/generate_commandview_inventory.py"
)
ANALYSIS_SCRIPT_RELATIVE = Path(
    ".repo_studios/command_center/scripts/summarizers/generate_function_analysis.py"
)

DEFAULT_IGNORE_DIRS = {
    "__pycache__",
    ".git",
    ".repo_studios",
    "build",
    "dist",
    "node_modules",
    "venv",
}

VIEWER_SLUG = "commandview"
TOPIC_SLUG = "duplicate_scan"


@dataclass
class FunctionInfo:
    """Metadata captured for each discovered function."""

    file: str
    line_start: int
    line_end: int
    function_name: str
    is_function: bool
    code_hash: str
    signature: str
    body_lines: list[str]
    ast_node: ast.AST | None = None

    def to_occurrence(self) -> dict[str, Any]:
        line_count = max(self.line_end - self.line_start + 1, 0)
        sample_line = self.body_lines[0].strip() if self.body_lines else ""
        return {
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_count": line_count,
            "function_name": self.function_name,
            "signature": self.signature,
            "sample_line": sample_line,
        }


@dataclass(frozen=True)
class Paths:
    """Resolved filesystem locations used during a scan run."""

    repo_root: Path
    target: Path
    output_dir: Path
    target_slug: str
    source_name: str
    target_index_dir: Path


@dataclass(frozen=True)
class Options:
    """Runtime configuration flags for the duplicate scan."""

    similarity_threshold: float
    min_lines: int
    keep_runs: int
    analysis_path: Path | None
    log_level: str
    skip_upstream: bool

@dataclass
class DuplicateGroup:
    """Scanner-centric view of duplicates."""

    group_id: str
    canonical_name: str
    occurrences: list[FunctionInfo]
    similarity_score: float
    duplicate_type: str
    signature_hash: str

    def to_matrix_group(self) -> dict[str, Any]:
        """Serialise into the matrix-friendly structure."""
        return {
            "group_id": self.group_id,
            "canonical_name": self.canonical_name,
            "similarity_score": round(self.similarity_score, 4),
            "duplicate_type": self.duplicate_type,
            "signature_hash": self.signature_hash,
            "occurrences": [occ.to_occurrence() for occ in self.occurrences],
        }


@dataclass
class ScanResult:
    """Summary of the AST scan."""

    files_scanned: int
    functions_scanned: int
    duplicate_groups: list[DuplicateGroup]


@dataclass(frozen=True)
class RunArtifacts:
    """File locations emitted for a duplicate scan run."""

    slug: str
    viewer_matrix: Path
    viewer_summary: Path
    index_matrix: Path
    index_summary: Path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scan_duplicates",
        description="Scan a directory for duplicate Python functions and merge results with producers analysis.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--target",
        default=str(DEFAULT_TARGET_RELATIVE),
        help="Directory to scan for Python files. Relative paths resolve within the repo root.",
    )
    parser.add_argument(
        "--repo-root",
        help="Explicit repository root. Defaults to marker-based discovery (searches ancestors for .repo_studios).",
    )
    parser.add_argument(
        "--run-root",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Base reports directory for duplicate scan outputs (viewer/topic/timestamp layout).",
    )
    parser.add_argument(
        "--output-dir",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--keep-runs",
        type=int,
        default=DEFAULT_KEEP_RUNS,
        help="Number of timestamped run folders to retain (excluding pinned .keep folders).",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=DEFAULT_SIMILARITY_THRESHOLD,
        help="Minimum similarity score for near-duplicate grouping.",
    )
    parser.add_argument(
        "--min-lines",
        type=int,
        default=DEFAULT_MIN_LINES,
        help="Ignore functions shorter than this many lines when scanning.",
    )
    parser.add_argument(
        "--analysis-file",
        dest="analysis_file",
        help="Optional explicit path to an analysis JSON file to merge with scanner output.",
    )
    parser.add_argument(
        "--producers-analysis",
        dest="analysis_file",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity for the scan.",
    )
    parser.add_argument(
        "--skip-upstream",
        action="store_true",
        help="Skip running prerequisite inventory and analysis producers before scanning.",
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__).resolve())
    target = _resolve_within_repo(repo_root, Path(args.target))
    output_arg = getattr(args, "output_dir", None) or args.run_root
    output_dir = _resolve_within_repo(repo_root, Path(output_arg))
    if not target.exists() or not target.is_dir():
        raise FileNotFoundError(f"Target directory not found or not a directory: {target}")
    source_name = target.name
    target_slug = _slugify_relative(target.relative_to(repo_root))
    target_index_dir = target / f"{source_name}_index"
    output_dir.mkdir(parents=True, exist_ok=True)
    target_index_dir.mkdir(parents=True, exist_ok=True)
    return Paths(
        repo_root=repo_root,
        target=target,
        output_dir=output_dir,
        target_slug=target_slug,
        source_name=source_name,
        target_index_dir=target_index_dir,
    )


def build_options(args: argparse.Namespace) -> Options:
    analysis_path = Path(args.analysis_file).resolve() if args.analysis_file else None
    return Options(
        similarity_threshold=float(args.similarity_threshold),
        min_lines=int(args.min_lines),
        keep_runs=int(args.keep_runs),
        analysis_path=analysis_path,
        log_level=args.log_level,
        skip_upstream=bool(args.skip_upstream),
    )


def _resolve_script_path(repo_root: Path, relative: Path) -> Path:
    script_path = (repo_root / relative).resolve()
    if not script_path.exists():
        raise FileNotFoundError(f"Required script not found: {script_path}")
    return script_path


def _load_cli_module(script_path: Path, module_name: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:
    candidates = sorted(directory.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"No {label} artifacts matching '{pattern}' found in {directory}.")
    return candidates[-1]


def _run_inventory(paths: Paths, options: Options) -> Path:
    script_path = _resolve_script_path(paths.repo_root, INVENTORY_SCRIPT_RELATIVE)
    module_name = "command_center.producers.generate_commandview_inventory"
    module = _load_cli_module(script_path, module_name)
    run_fn = getattr(module, "run", None)
    if run_fn is None:
        raise RuntimeError(f"generate_commandview_inventory module at {script_path} does not expose a run() helper.")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        options.log_level,
        str(paths.target),
    ]
    exit_code = run_fn(argv)
    if exit_code != 0:
        raise RuntimeError(f"Function inventory generation failed with exit code {exit_code}.")
    index_dir = paths.target / f"{paths.source_name}_index"
    return _latest_artifact(index_dir, f"{paths.source_name}_commandview_[0-9]*.json", "inventory")


def _run_analysis(paths: Paths, options: Options, inventory_path: Path) -> Path:
    script_path = _resolve_script_path(paths.repo_root, ANALYSIS_SCRIPT_RELATIVE)
    module_name = "command_center.summarizers.generate_function_analysis"
    module = _load_cli_module(script_path, module_name)
    run_fn = getattr(module, "run", None)
    if run_fn is None:
        raise RuntimeError(f"generate_function_analysis module at {script_path} does not expose a run() helper.")
    argv = [
        "--repo-root",
        str(paths.repo_root),
        "--log-level",
        options.log_level,
        "--inventory-file",
        str(inventory_path),
        str(paths.target),
    ]
    exit_code = run_fn(argv)
    if exit_code != 0:
        raise RuntimeError(f"Function analysis generation failed with exit code {exit_code}.")
    index_dir = inventory_path.parent
    return _latest_artifact(index_dir, f"{paths.source_name}_analysis-*.json", "analysis")


def orchestrate_upstream(paths: Paths, options: Options) -> Path:
    logging.info("Running function inventory producer for %s", paths.source_name)
    inventory_path = _run_inventory(paths, options)
    logging.info("Running function analysis producer for %s", paths.source_name)
    analysis_path = _run_analysis(paths, options, inventory_path)
    return analysis_path


def _resolve_within_repo(repo_root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:  # pragma: no cover - defensive guardrail
        raise ValueError(f"Path must reside within the repo root: {resolved}") from exc
    return resolved


_slugify_relative = slugify_relative


def _to_repo_relative(path: Path, repo_root: Path) -> str:
    try:
        rel = path.relative_to(repo_root)
    except ValueError:  # pragma: no cover - defensive guardrail
        return str(path)
    return str(rel).replace("\\", "/")


class FunctionExtractor(ast.NodeVisitor):
    """Extract functions from Python source files."""

    def __init__(self, source_code: str, filepath: Path, repo_root: Path) -> None:
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.filepath = filepath
        self.repo_root = repo_root
        self.functions: list[FunctionInfo] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: D401 - docstring inherited
        self._extract_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: D401
        self._extract_function(node)
        self.generic_visit(node)

    def _extract_function(self, node: ast.AST) -> None:
        line_start = getattr(node, "lineno", 0)
        line_end = getattr(node, "end_lineno", line_start)
        body_lines = self.source_lines[line_start - 1 : line_end]
        code_hash = _compute_code_hash("\n".join(body_lines))
        signature = _build_signature(node)
        try:
            rel_path = self.filepath.relative_to(self.repo_root)
        except ValueError:
            rel_path = self.filepath
        info = FunctionInfo(
            file=str(rel_path).replace("\\", "/"),
            line_start=line_start,
            line_end=line_end,
            function_name=getattr(node, "name", "<anonymous>"),
            is_function=True,
            code_hash=code_hash,
            signature=signature,
            body_lines=body_lines,
            ast_node=node,
        )
        self.functions.append(info)


def _compute_code_hash(code: str) -> str:
    import hashlib

    normalized = _normalize_code(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def _normalize_code(code: str) -> str:
    lines: list[str] = []
    for raw in code.splitlines():
        stripped = raw.split("#", 1)[0].strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _build_signature(node: ast.AST) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        arg_names = [arg.arg for arg in getattr(node.args, "args", [])]
        return f"def {getattr(node, 'name', '<anonymous>')}({', '.join(arg_names)})"
    return "<unknown>"


def scan_python_files(directory: Path, ignore_patterns: Sequence[str] | None = None) -> list[Path]:
    ignore_dirs = set(ignore_patterns or DEFAULT_IGNORE_DIRS)
    results: list[Path] = []
    for path in directory.rglob("*.py"):
        try:
            relative_parts = path.relative_to(directory).parts
        except ValueError:
            continue
        if any(part in ignore_dirs or part.startswith(".") for part in relative_parts[:-1]):
            continue
        results.append(path)
    return sorted(results)


def extract_functions_from_file(filepath: Path, repo_root: Path) -> list[FunctionInfo]:
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except (OSError, SyntaxError) as exc:
        logging.debug("Skipping %s due to parse error: %s", filepath, exc)
        return []
    extractor = FunctionExtractor(source, filepath, repo_root)
    extractor.visit(tree)
    return extractor.functions


def compute_ast_similarity(left: FunctionInfo, right: FunctionInfo) -> float:
    if not left.ast_node or not right.ast_node:
        return _text_similarity(left.body_lines, right.body_lines)
    return _ast_node_similarity(left.ast_node, right.ast_node)


def _ast_node_similarity(node1: ast.AST, node2: ast.AST) -> float:
    if type(node1) is not type(node2):  # noqa: E721 - intentional strict type check
        return 0.0
    if isinstance(node1, ast.Constant):
        return 1.0 if getattr(node1, "value", None) == getattr(node2, "value", None) else 0.5
    if isinstance(node1, ast.Name):
        return 1.0 if getattr(node1, "id", None) == getattr(node2, "id", None) else 0.8
    children1 = list(ast.iter_child_nodes(node1))
    children2 = list(ast.iter_child_nodes(node2))
    if not children1 and not children2:
        return 1.0
    if len(children1) != len(children2):
        max_len = max(len(children1), len(children2))
        if max_len == 0:
            return 1.0
        return (min(len(children1), len(children2)) / max_len) * 0.5
    scores = [_ast_node_similarity(c1, c2) for c1, c2 in zip(children1, children2)]
    return sum(scores) / len(scores) if scores else 0.0


def _text_similarity(lines1: Sequence[str], lines2: Sequence[str]) -> float:
    import difflib

    text1 = "\n".join(lines1)
    text2 = "\n".join(lines2)
    if text1 == text2:
        return 1.0
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio()


def group_duplicates(
    functions: Sequence[FunctionInfo],
    *,
    similarity_threshold: float,
    min_lines: int,
) -> list[list[FunctionInfo]]:
    hash_groups: dict[str, list[FunctionInfo]] = defaultdict(list)
    for func in functions:
        if len(func.body_lines) < min_lines:
            continue
        hash_groups[func.code_hash].append(func)
    exact_groups = [group for group in hash_groups.values() if len(group) > 1]
    remaining = [func for group in hash_groups.values() if len(group) == 1 for func in group]
    near_groups: list[list[FunctionInfo]] = []
    consumed: set[int] = set()
    for idx, primary in enumerate(remaining):
        if idx in consumed:
            continue
        cluster = [primary]
        for jdx in range(idx + 1, len(remaining)):
            if jdx in consumed:
                continue
            candidate = remaining[jdx]
            score = compute_ast_similarity(primary, candidate)
            if score >= similarity_threshold:
                cluster.append(candidate)
                consumed.add(jdx)
        if len(cluster) > 1:
            near_groups.append(cluster)
            consumed.add(idx)
    return exact_groups + near_groups


def build_duplicate_groups(
    functions: Sequence[FunctionInfo],
    *,
    similarity_threshold: float,
    min_lines: int,
) -> list[DuplicateGroup]:
    raw_groups = group_duplicates(
        functions,
        similarity_threshold=similarity_threshold,
        min_lines=min_lines,
    )
    groups: list[DuplicateGroup] = []
    for index, members in enumerate(raw_groups, start=1):
        hashes = {member.code_hash for member in members}
        duplicate_type = "exact_duplicate" if len(hashes) == 1 else "near_duplicate_with_variations"
        canonical_name = _canonical_name(members)
        similarity_score = 1.0 if len(hashes) == 1 else _average_pairwise_similarity(members)
        groups.append(
            DuplicateGroup(
                group_id=f"dup_{index:03d}",
                canonical_name=canonical_name,
                occurrences=list(members),
                similarity_score=similarity_score,
                duplicate_type=duplicate_type,
                signature_hash=members[0].code_hash,
            )
        )
    return groups


def _canonical_name(members: Sequence[FunctionInfo]) -> str:
    names = [member.function_name.lstrip("_") for member in members]
    if not names:
        return "<unknown>"
    counter = Counter(name.lower() for name in names)
    return max(counter.items(), key=lambda item: (item[1], -len(item[0])))[0]


def _average_pairwise_similarity(members: Sequence[FunctionInfo]) -> float:
    scores: list[float] = []
    for left, right in _pairwise(members):
        scores.append(compute_ast_similarity(left, right))
    return sum(scores) / len(scores) if scores else 1.0


def _pairwise(items: Sequence[FunctionInfo]) -> Iterator[tuple[FunctionInfo, FunctionInfo]]:
    for idx in range(len(items)):
        for jdx in range(idx + 1, len(items)):
            yield items[idx], items[jdx]


def locate_analysis(paths: Paths, options: Options) -> Path:
    if options.analysis_path:
        if not options.analysis_path.exists():
            raise FileNotFoundError(f"Analysis file not found: {options.analysis_path}")
        return options.analysis_path
    pattern = f"{paths.source_name}_analysis-*.json"
    candidates = sorted(paths.target_index_dir.glob(pattern))
    if not candidates:
        raise FileNotFoundError(
            f"No analysis files matching '{pattern}' found in {paths.target_index_dir}."
            " Provide --analysis-file to supply a compatible dataset."
        )
    return candidates[-1]


def load_source_duplicates(analysis_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    findings = payload.get("findings", [])
    results: list[dict[str, Any]] = []
    for item in findings:
        details = item.get("details", {})
        metrics = item.get("metrics", {})
        instances = item.get("instances", [])
        entry = {
            "id": item.get("id"),
            "function_name": details.get("function_name"),
            "signature": details.get("signature"),
            "producer_duplicate_count": metrics.get("duplicate_count", len(instances)),
            "producer_instances": [
                {
                    "path": inst.get("path"),
                    "line": inst.get("line"),
                    "line_count": inst.get("line_count"),
                    "name": inst.get("name"),
                }
                for inst in instances
            ],
            "scanner_groups": [],
        }
        results.append(entry)
    return results


def merge_duplicates(
    producer_entries: list[dict[str, Any]],
    duplicate_groups: Sequence[DuplicateGroup],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    matrix: list[dict[str, Any]] = [dict(entry) for entry in producer_entries]
    name_to_entry: dict[str, dict[str, Any]] = {}
    for entry in matrix:
        key = _normalize_name(entry.get("function_name"))
        if key:
            name_to_entry[key] = entry
    matched_groups = 0
    for group in duplicate_groups:
        key = _normalize_name(group.canonical_name)
        if key and key in name_to_entry:
            name_to_entry[key].setdefault("scanner_groups", []).append(group.to_matrix_group())
            matched_groups += 1
        else:
            matrix.append(
                {
                    "id": f"scanner_only::{group.group_id}",
                    "function_name": group.canonical_name,
                    "signature": None,
                    "producer_duplicate_count": 0,
                    "producer_instances": [],
                    "scanner_groups": [group.to_matrix_group()],
                }
            )
    stats = {
        "producer_groups": len(producer_entries),
        "scanner_groups": len(duplicate_groups),
        "matched_groups": matched_groups,
        "scanner_only_groups": len(duplicate_groups) - matched_groups,
    }
    matrix.sort(key=lambda item: (-(item.get("producer_duplicate_count") or 0), item.get("function_name") or ""))
    return matrix, stats


def _normalize_name(name: str | None) -> str:
    return name.lstrip("_").lower() if name else ""


def _load_source_line(repo_root: Path, relative_path: str | None, line_number: int | None) -> str:
    if not relative_path or line_number is None or line_number <= 0:
        return ""
    path = Path(relative_path)
    if not path.is_absolute():
        path = (repo_root / path).resolve()
    try:
        contents = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    lines = contents.splitlines()
    if line_number > len(lines):
        return ""
    return lines[line_number - 1].strip()


def _extract_top_offenders(
    matrix: Sequence[dict[str, Any]],
    repo_root: Path,
    limit: int = 10,
) -> list[dict[str, Any]]:
    offenders: list[dict[str, Any]] = []
    for entry in matrix:
        producer_instances = entry.get("producer_instances", []) or []
        scanner_groups = entry.get("scanner_groups", []) or []
        occurrences: OrderedDict[tuple[str, int | None, int | None], dict[str, Any]] = OrderedDict()

        def record_occurrence(
            path: str,
            line_start: int | None,
            line_end: int | None,
            line_count: int | None,
            sample_line: str,
        ) -> None:
            key = (path, line_start, line_end)
            if key not in occurrences:
                occurrences[key] = {
                    "path": path,
                    "line_start": line_start,
                    "line_end": line_end,
                    "line_count": line_count,
                    "sample_line": sample_line,
                }
            else:
                existing = occurrences[key]
                if line_count is not None and (existing["line_count"] is None or line_count > existing["line_count"]):
                    existing["line_count"] = line_count
                if not existing["sample_line"] and sample_line:
                    existing["sample_line"] = sample_line

        for inst in producer_instances:
            path = inst.get("path")
            if not isinstance(path, str) or not path:
                continue
            line_start_raw = inst.get("line")
            line_start = int(line_start_raw) if isinstance(line_start_raw, int) and line_start_raw > 0 else None
            line_count_raw = inst.get("line_count")
            line_count = int(line_count_raw) if isinstance(line_count_raw, int) and line_count_raw > 0 else None
            line_end = None
            if line_start is not None and line_count is not None:
                line_end = line_start + line_count - 1
            sample_line = _load_source_line(repo_root, path, line_start)
            record_occurrence(path, line_start, line_end, line_count, sample_line)

        for group in scanner_groups:
            for occ in group.get("occurrences", []) or []:
                path = occ.get("file")
                if not isinstance(path, str) or not path:
                    continue
                line_start_raw = occ.get("line_start")
                line_end_raw = occ.get("line_end")
                line_start = int(line_start_raw) if isinstance(line_start_raw, int) else None
                line_end = int(line_end_raw) if isinstance(line_end_raw, int) else None
                line_count: int | None = None
                if line_start is not None and line_end is not None and line_end >= line_start:
                    line_count = line_end - line_start + 1
                sample_line = (occ.get("sample_line") or "").strip()
                if not sample_line:
                    sample_line = _load_source_line(repo_root, path, line_start)
                record_occurrence(path, line_start, line_end, line_count, sample_line)

        if not occurrences:
            continue

        offenders.append(
            {
                "function_name": entry.get("function_name") or "<unknown>",
                "occurrence_count": len(occurrences),
                "occurrences": list(occurrences.values()),
            }
        )

    offenders.sort(key=lambda item: (-item["occurrence_count"], item["function_name"]))
    return offenders[:limit]


def generate_summary(
    stats: dict[str, Any],
    scan_result: ScanResult,
    analysis_path: Path,
    paths: Paths,
    matrix: Sequence[dict[str, Any]],
) -> str:
    lines = ["# Duplicate Scan Summary", "", "## Overview", ""]
    lines.extend(
        [
            f"- Target directory: `{_to_repo_relative(paths.target, paths.repo_root)}`",
            f"- Python files scanned: {scan_result.files_scanned}",
            f"- Functions analysed: {scan_result.functions_scanned}",
            f"- Scanner groups detected: {stats['scanner_groups']}",
            f"- Producer groups referenced: {stats['producer_groups']}",
            f"- Scanner groups matched to producers: {stats['matched_groups']}",
            f"- Scanner-only groups: {stats['scanner_only_groups']}",
        ]
    )
    if not matrix:
        lines.append("- No duplicate groups detected during this scan.")
    lines.extend(["", "## Inputs", ""])
    rel_analysis = _to_repo_relative(analysis_path, paths.repo_root)
    lines.extend(
        [
            f"- Analysis dataset: `{rel_analysis}`",
            "- Run generated with scan_duplicates CLI",
        ]
    )
    lines.extend(["", "## Top Duplicate Offenders", ""])
    offenders = _extract_top_offenders(matrix, paths.repo_root)
    if not offenders:
        lines.append("- No notable duplicate offenders detected.")
    else:
        for index, offender in enumerate(offenders, start=1):
            lines.append(f"{index}. `{offender['function_name']}` — " f"{offender['occurrence_count']} duplicate(s)")
            for detail in offender["occurrences"]:
                path = detail["path"]
                line_start = detail.get("line_start")
                line_end = detail.get("line_end")
                if line_start is not None and line_end is not None:
                    location = f"{path}:{line_start}-{line_end}"
                elif line_start is not None:
                    location = f"{path}:{line_start}"
                else:
                    location = path
                line_count = detail.get("line_count")
                if isinstance(line_count, int) and line_count > 0:
                    line_count_text = f"{line_count} line(s)"
                else:
                    line_count_text = "n/a line count"
                sample_line = (detail.get("sample_line") or "sample unavailable").strip()
                sample_line = sample_line.replace("`", "\\`")
                lines.append(f"    - {location} ({line_count_text}): `{sample_line}`")
            lines.append("")
        if lines[-1] == "":
            lines.pop()
        lines.append("")
    lines.extend(
        [
            "## Next Steps",
            "",
            "- Review scanner-only groups to decide whether they warrant new producer tracking.",
            "- Prioritise groups with high duplicate counts or similarity for extraction.",
        ]
    )
    return "\n".join(lines) + "\n"


def scan_target(paths: Paths, options: Options) -> ScanResult:
    python_files = scan_python_files(paths.target)
    functions: list[FunctionInfo] = []
    for file_path in python_files:
        functions.extend(extract_functions_from_file(file_path, paths.repo_root))
    duplicate_groups = build_duplicate_groups(
        functions,
        similarity_threshold=options.similarity_threshold,
        min_lines=options.min_lines,
    )
    return ScanResult(
        files_scanned=len(python_files),
        functions_scanned=len(functions),
        duplicate_groups=duplicate_groups,
    )


def compose_payload(
    matrix: list[dict[str, Any]],
    stats: dict[str, Any],
    scan_result: ScanResult,
    paths: Paths,
    analysis_path: Path,
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "metadata": {
            "generated_at": generated_at,
            "target": _to_repo_relative(paths.target, paths.repo_root),
            "repo_root": str(paths.repo_root),
            "analysis_source": _to_repo_relative(analysis_path, paths.repo_root),
            "python_files_scanned": scan_result.files_scanned,
            "functions_scanned": scan_result.functions_scanned,
        },
        "stats": stats,
        "entries": matrix,
    }


def _write_index_artifacts(
    *,
    payload: dict[str, Any],
    summary: str,
    paths: Paths,
    slug: str,
) -> tuple[Path, Path]:
    matrix_name = f"{paths.source_name}_duplicate_matrix-{slug}.json"
    summary_name = f"{paths.source_name}_duplicate_summary-{slug}.md"
    paths.target_index_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = paths.target_index_dir / matrix_name
    summary_path = paths.target_index_dir / summary_name
    matrix_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(summary, encoding="utf-8")
    return matrix_path, summary_path


def _prune_index_artifacts(paths: Paths, *, keep: int) -> None:
    keep = max(keep, 1)
    pattern = f"{paths.source_name}_duplicate_matrix-*.json"
    matrix_files = sorted(paths.target_index_dir.glob(pattern), key=lambda item: item.name, reverse=True)
    for stale in matrix_files[keep:]:
        slug = stale.stem.replace(f"{paths.source_name}_duplicate_matrix-", "")
        summary_path = paths.target_index_dir / f"{paths.source_name}_duplicate_summary-{slug}.md"
        try:
            stale.unlink()
        except FileNotFoundError:
            pass
        if summary_path.exists():
            try:
                summary_path.unlink()
            except FileNotFoundError:
                pass


def write_outputs(
    payload: dict[str, Any],
    summary: str,
    paths: Paths,
    *,
    timestamp: datetime | None = None,
    keep: int = DEFAULT_KEEP_RUNS,
) -> RunArtifacts:
    moment = timestamp or datetime.now(timezone.utc)
    matrix_filename = f"{paths.source_name}_duplicate_matrix.json"
    summary_filename = f"{paths.source_name}_duplicate_summary.md"

    def _write_matrix(run_dir: Path) -> Path:
        target = run_dir / matrix_filename
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    def _write_summary(run_dir: Path) -> Path:
        target = run_dir / summary_filename
        target.write_text(summary, encoding="utf-8")
        return target

    report_result: WriteReportArtifactsResult = write_report_artifacts(
        stem=f"{paths.target_slug}_duplicate_scan",
        timestamp=moment,
        output_dir=paths.output_dir,
        artifacts=[
            ReportArtifact(filename=matrix_filename, writer=_write_matrix),
            ReportArtifact(filename=summary_filename, writer=_write_summary),
        ],
        keep=max(keep, 1),
        viewer=VIEWER_SLUG,
        topic=TOPIC_SLUG,
    )

    index_matrix, index_summary = _write_index_artifacts(
        payload=payload,
        summary=summary,
        paths=paths,
        slug=report_result.slug,
    )

    _prune_index_artifacts(paths=paths, keep=keep)

    return RunArtifacts(
        slug=report_result.slug,
        viewer_matrix=report_result.artifacts[matrix_filename],
        viewer_summary=report_result.artifacts[summary_filename],
        index_matrix=index_matrix,
        index_summary=index_summary,
    )

def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging(options.log_level)
    try:
        paths = build_paths(args)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("%s", exc)
        return 1
    if not options.skip_upstream and options.analysis_path is None:
        try:
            analysis_override = orchestrate_upstream(paths, options)
        except (FileNotFoundError, ImportError, RuntimeError) as exc:
            logging.error("%s", exc)
            return 1
        options = replace(options, analysis_path=analysis_override)
    try:
        analysis_path = locate_analysis(paths, options)
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 1
    scan_result = scan_target(paths, options)
    producer_entries = load_source_duplicates(analysis_path)
    matrix, stats = merge_duplicates(producer_entries, scan_result.duplicate_groups)
    payload = compose_payload(matrix, stats, scan_result, paths, analysis_path)
    summary = generate_summary(stats, scan_result, analysis_path, paths, matrix)
    artifacts = write_outputs(payload=payload, summary=summary, paths=paths, keep=options.keep_runs)
    logging.info(
        "Duplicate scan complete: files=%d functions=%d scanner_groups=%d producers=%d",
        scan_result.files_scanned,
        scan_result.functions_scanned,
        stats["scanner_groups"],
        stats["producer_groups"],
    )
    logging.debug(
        "Artifacts mirrored: slug=%s viewer_matrix=%s index_matrix=%s viewer_summary=%s index_summary=%s",
        artifacts.slug,
        artifacts.viewer_matrix,
        artifacts.index_matrix,
        artifacts.viewer_summary,
        artifacts.index_summary,
    )
    return 0


def main() -> None:  # pragma: no cover - thin wrapper for CLI usage
    raise SystemExit(run())


__all__ = [
    "FunctionExtractor",
    "FunctionInfo",
    "Paths",
    "Options",
    "RunArtifacts",
    "VIEWER_SLUG",
    "TOPIC_SLUG",
    "scan_python_files",
    "write_outputs",
    "compute_ast_similarity",
    "group_duplicates",
    "run",
    "main",
]
