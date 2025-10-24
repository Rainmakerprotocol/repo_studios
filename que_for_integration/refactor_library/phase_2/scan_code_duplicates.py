#!/usr/bin/env python3
"""Scan Python codebase for duplicate functions using AST analysis.

This tool detects exact and near-duplicate functions across a Python codebase,
generates AI-optimized JSON reports, and recommends library extraction paths
following the naming conventions in .repo_studios/naming_conventions.md.

Artifacts (default):
    - `.repo_studios/reports/duplicate_detection_reports/`
        - `duplicate_detection-<timestamp>/report.json`
        - `duplicate_detection-<timestamp>/summary.md`
        - `latest_report.(json|md)` symlinks

Exit codes:
    0 success (duplicates detected and reported)
    1 error (scanning failed)
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/duplicate_detection_reports")
RUN_PREFIX = "duplicate_detection"
DEFAULT_ARTIFACTS_TO_KEEP = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.85
DEFAULT_MIN_LINES = 3


@dataclass
class FunctionInfo:
    """Information about a function extracted from AST."""
    file: str
    line_start: int
    line_end: int
    function_name: str
    is_function: bool
    code_hash: str
    signature: str
    body_lines: list[str]
    ast_node: ast.FunctionDef | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary without AST node."""
        return {
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "function_name": self.function_name,
            "is_function": self.is_function,
            "code_hash": self.code_hash,
        }


@dataclass
class DuplicateGroup:
    """Group of duplicate function occurrences."""
    group_id: str
    signature_hash: str
    canonical_name: str
    purpose: str
    category: str
    occurrences: list[FunctionInfo]
    similarity_score: float
    duplicate_type: str
    library_recommendation: dict[str, Any]
    refactoring_action: dict[str, Any]
    impact_analysis: dict[str, Any]


class FunctionExtractor(ast.NodeVisitor):
    """Extract functions from Python AST."""
    
    def __init__(self, source_code: str, filepath: str, repo_root: Path):
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.filepath = filepath
        self.repo_root = repo_root
        self.functions: list[FunctionInfo] = []
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes."""
        # Skip nested functions (for now - may add later)
        if isinstance(node, ast.FunctionDef):
            self._extract_function(node)
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition nodes."""
        self._extract_function(node)
        self.generic_visit(node)
    
    def _extract_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Extract function information from AST node."""
        line_start = node.lineno
        line_end = node.end_lineno or line_start
        
        # Get function body lines
        body_lines = self.source_lines[line_start - 1:line_end]
        body_text = "\n".join(body_lines)
        
        # Generate hash of normalized body (ignore whitespace/comments)
        code_hash = self._compute_code_hash(body_text)
        
        # Generate signature
        args = [arg.arg for arg in node.args.args]
        signature = f"def {node.name}({', '.join(args)})"
        
        try:
            rel_path = Path(self.filepath).relative_to(self.repo_root)
        except ValueError:
            rel_path = Path(self.filepath)
        
        func_info = FunctionInfo(
            file=str(rel_path),
            line_start=line_start,
            line_end=line_end,
            function_name=node.name,
            is_function=True,
            code_hash=code_hash,
            signature=signature,
            body_lines=body_lines,
            ast_node=node,
        )
        
        self.functions.append(func_info)
    
    def _compute_code_hash(self, code: str) -> str:
        """Compute hash of code ignoring whitespace and comments."""
        # Normalize: remove comments, extra whitespace
        normalized = self._normalize_code(code)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison."""
        lines = []
        for line in code.splitlines():
            # Remove comments
            if "#" in line:
                line = line[:line.index("#")]
            # Strip whitespace
            line = line.strip()
            if line:
                lines.append(line)
        return "\n".join(lines)


def scan_python_files(directory: Path, ignore_patterns: list[str] | None = None) -> list[Path]:
    """Recursively find Python files."""
    ignore_patterns = ignore_patterns or ["test_*", "__pycache__", ".git", "venv"]
    python_files = []
    
    for py_file in directory.rglob("*.py"):
        # Check ignore patterns
        if any(pattern in str(py_file) for pattern in ignore_patterns):
            continue
        python_files.append(py_file)
    
    return sorted(python_files)


def extract_functions_from_file(filepath: Path, repo_root: Path) -> list[FunctionInfo]:
    """Extract all functions from a Python file."""
    try:
        source_code = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source_code, filename=str(filepath))
        
        extractor = FunctionExtractor(source_code, str(filepath), repo_root)
        extractor.visit(tree)
        
        return extractor.functions
    except SyntaxError as exc:
        logging.warning("Syntax error in %s: %s", filepath, exc)
        return []
    except Exception as exc:
        logging.warning("Failed to parse %s: %s", filepath, exc)
        return []


def compute_ast_similarity(func1: FunctionInfo, func2: FunctionInfo) -> float:
    """Compute similarity score between two functions using AST comparison."""
    if not func1.ast_node or not func2.ast_node:
        # Fallback to text similarity
        return _text_similarity(func1.body_lines, func2.body_lines)
    
    # Compare AST structure
    similarity = _ast_node_similarity(func1.ast_node, func2.ast_node)
    return similarity


def _ast_node_similarity(node1: ast.AST, node2: ast.AST) -> float:
    """Recursively compare AST nodes for structural similarity."""
    # Same node type is baseline
    if type(node1) != type(node2):
        return 0.0
    
    # For leaf nodes, compare values
    if isinstance(node1, ast.Constant):
        return 1.0 if node1.value == node2.value else 0.5
    
    if isinstance(node1, ast.Name):
        return 1.0 if node1.id == node2.id else 0.8  # Variable names less critical
    
    # For container nodes, compare children
    children1 = list(ast.iter_child_nodes(node1))
    children2 = list(ast.iter_child_nodes(node2))
    
    if not children1 and not children2:
        return 1.0
    
    if len(children1) != len(children2):
        # Different structure, but compute partial similarity
        max_len = max(len(children1), len(children2))
        if max_len == 0:
            return 1.0
        return min(len(children1), len(children2)) / max_len * 0.5
    
    # Compare child nodes recursively
    similarities = [
        _ast_node_similarity(c1, c2)
        for c1, c2 in zip(children1, children2)
    ]
    
    return sum(similarities) / len(similarities) if similarities else 0.0


def _text_similarity(lines1: list[str], lines2: list[str]) -> float:
    """Fallback text-based similarity."""
    text1 = "\n".join(lines1)
    text2 = "\n".join(lines2)
    
    # Simple character-level similarity
    if text1 == text2:
        return 1.0
    
    # Use difflib-style approach
    import difflib
    matcher = difflib.SequenceMatcher(None, text1, text2)
    return matcher.ratio()


def group_duplicates(
    functions: list[FunctionInfo],
    similarity_threshold: float,
    min_lines: int,
) -> list[list[FunctionInfo]]:
    """Group functions into duplicate clusters."""
    # First, group by exact hash
    hash_groups: dict[str, list[FunctionInfo]] = defaultdict(list)
    for func in functions:
        # Filter by minimum lines
        if len(func.body_lines) < min_lines:
            continue
        hash_groups[func.code_hash].append(func)
    
    # Exact duplicates (hash match)
    exact_groups = [group for group in hash_groups.values() if len(group) > 1]
    
    # Near duplicates (similarity scoring)
    remaining = [func for group in hash_groups.values() if len(group) == 1 for func in group]
    near_groups: list[list[FunctionInfo]] = []
    
    processed = set()
    for i, func1 in enumerate(remaining):
        if func1.code_hash in processed:
            continue
        
        cluster = [func1]
        for func2 in remaining[i + 1:]:
            if func2.code_hash in processed:
                continue
            
            similarity = compute_ast_similarity(func1, func2)
            if similarity >= similarity_threshold:
                cluster.append(func2)
                processed.add(func2.code_hash)
        
        if len(cluster) > 1:
            near_groups.append(cluster)
            processed.add(func1.code_hash)
    
    return exact_groups + near_groups


def infer_library_path(func_name: str, category: str) -> dict[str, Any]:
    """Infer recommended library path from function name and category."""
    # Mapping of keywords to library domains
    domain_keywords = {
        "filesystem": ["path", "file", "dir", "directory", "folder"],
        "artifact_lifecycle": ["artifact", "report", "output", "write", "prune", "link", "latest"],
        "time_handling": ["time", "timestamp", "date", "format", "parse"],
        "logging_setup": ["log", "logging", "configure"],
        "cli_patterns": ["arg", "argument", "cli", "parse"],
    }
    
    purpose_keywords = {
        "path_operations": ["path", "relative", "absolute", "resolve"],
        "directory_management": ["dir", "directory", "ensure", "create", "mkdir"],
        "versioning": ["version", "prune", "link", "latest", "old"],
        "structured_output": ["write", "output", "json", "markdown", "md", "log", "tsv"],
        "parsing": ["parse"],
        "formatting": ["format"],
        "configuration": ["config", "configure", "setup"],
        "common_args": ["arg"],
    }
    
    # Infer domain
    func_lower = func_name.lower()
    domain = "filesystem"  # Default
    for dom, keywords in domain_keywords.items():
        if any(kw in func_lower for kw in keywords):
            domain = dom
            break
    
    # Infer purpose
    purpose = "utilities"  # Default
    for purp, keywords in purpose_keywords.items():
        if any(kw in func_lower for kw in keywords):
            purpose = purp
            break
    
    # Special case handling
    if "prune" in func_lower and "run" in func_lower:
        domain = "artifact_lifecycle"
        purpose = "versioning"
    elif "copy" in func_lower and "latest" in func_lower:
        domain = "artifact_lifecycle"
        purpose = "versioning"
    elif "ensure" in func_lower and "dir" in func_lower:
        domain = "filesystem"
        purpose = "directory_management"
    elif "timestamp" in func_lower and "parse" in func_lower:
        domain = "time_handling"
        purpose = "parsing"
    elif "timestamp" in func_lower and "format" in func_lower:
        domain = "time_handling"
        purpose = "formatting"
    
    # Generate file name (clean up function name)
    clean_name = func_name.lstrip("_")
    target_file = f"{clean_name}.py"
    target_path = f"{domain}/{purpose}/{target_file}"
    
    return {
        "target_path": target_path,
        "function_signature": f"def {clean_name}(...) -> ...",
        "import_statement": f"from .repo_studios.library.{domain}.{purpose} import {clean_name}",
        "confidence": 0.85,  # Can be improved with ML
        "reasoning": [
            f"Function name contains '{domain}' domain keywords",
            f"Function purpose matches '{purpose}' pattern",
            f"Follows naming convention: verb_noun format",
        ],
    }


def generate_refactoring_action(
    group: list[FunctionInfo],
    library_path: str,
    group_id: str,
) -> dict[str, Any]:
    """Generate step-by-step refactoring instructions."""
    # Determine best source (first occurrence)
    best_source = group[0]
    
    # Check for variations
    has_variations = len(set(f.code_hash for f in group)) > 1
    
    steps = [
        {
            "step": 1,
            "action": "create_library_file",
            "target": f".repo_studios/library/{library_path}",
            "content_source": f"{best_source.file}:{best_source.line_start}-{best_source.line_end}",
        },
        {
            "step": 2,
            "action": "create_test_file",
            "target": f".repo_studios/tests/tests_library/test_{library_path.replace('/', '/test_')}",
            "test_strategy": "unit_test_with_fixtures",
        },
        {
            "step": 3,
            "action": "replace_occurrences",
            "replacements": [
                {
                    "file": func.file,
                    "line_range": [func.line_start, func.line_end],
                    "replace_with": "# Imported from library",
                    "add_import": f"from .repo_studios.library.{library_path.replace('/', '.').replace('.py', '')} import {func.function_name.lstrip('_')}",
                }
                for func in group
            ],
        },
        {
            "step": 4,
            "action": "run_targeted_tests",
            "test_files": [f"tests for {func.file}" for func in group],
            "success_criteria": "all_tests_green",
        },
        {
            "step": 5,
            "action": "validate_full_suite",
            "command": "make studio-test-all",
            "success_criteria": "no_new_failures",
        },
    ]
    
    strategy = "unify_and_extract" if has_variations else "extract_to_library_and_replace"
    
    return {
        "strategy": strategy,
        "priority": "high" if len(group) >= 3 else "medium",
        "estimated_effort": "low" if not has_variations else "medium",
        "risk_level": "low",
        "unification_required": has_variations,
        "steps": steps,
    }


def analyze_impact(group: list[FunctionInfo]) -> dict[str, Any]:
    """Analyze impact of refactoring this duplicate group."""
    total_lines = sum(len(f.body_lines) for f in group)
    saved_lines = total_lines - len(group[0].body_lines)  # Keep one copy
    
    files_affected = list(set(f.file for f in group))
    
    return {
        "lines_saved": saved_lines,
        "files_affected": len(files_affected),
        "downstream_dependencies": [],  # TODO: Add import analysis
        "breaking_change_risk": "none",
        "regression_risk": "low" if len(group) <= 3 else "medium",
    }


def build_duplicate_group(
    group: list[FunctionInfo],
    group_id: str,
    similarity_score: float,
) -> DuplicateGroup:
    """Build complete duplicate group with recommendations."""
    canonical_name = group[0].function_name.lstrip("_")
    category = "utility_function"  # Simplification
    
    # Infer purpose from function name
    purpose = canonical_name.replace("_", " ")
    
    lib_rec = infer_library_path(canonical_name, category)
    refactor = generate_refactoring_action(group, lib_rec["target_path"], group_id)
    impact = analyze_impact(group)
    
    duplicate_type = "exact_duplicate" if similarity_score == 1.0 else "near_duplicate_with_variations"
    
    return DuplicateGroup(
        group_id=group_id,
        signature_hash=group[0].code_hash,
        canonical_name=canonical_name,
        purpose=purpose,
        category=category,
        occurrences=group,
        similarity_score=similarity_score,
        duplicate_type=duplicate_type,
        library_recommendation=lib_rec,
        refactoring_action=refactor,
        impact_analysis=impact,
    )


def build_report(
    duplicate_groups: list[DuplicateGroup],
    scan_config: dict[str, Any],
    repo_root: Path,
    generated_ts: datetime,
) -> dict[str, Any]:
    """Build complete JSON report."""
    total_occurrences = sum(len(g.occurrences) for g in duplicate_groups)
    total_lines_duplicated = sum(g.impact_analysis["lines_saved"] for g in duplicate_groups)
    
    priority_breakdown = {"high": 0, "medium": 0, "low": 0}
    risk_breakdown = {"low": 0, "medium": 0, "high": 0}
    
    for group in duplicate_groups:
        priority = group.refactoring_action["priority"]
        risk = group.refactoring_action["risk_level"]
        priority_breakdown[priority] += 1
        risk_breakdown[risk] += 1
    
    # Group into execution phases
    phase1_groups = [g for g in duplicate_groups if g.refactoring_action["risk_level"] == "low" and not g.refactoring_action["unification_required"]]
    phase2_groups = [g for g in duplicate_groups if g.refactoring_action["unification_required"]]
    phase3_groups = [g for g in duplicate_groups if g not in phase1_groups and g not in phase2_groups]
    
    execution_order = [
        {
            "phase": 1,
            "name": "safe_extractions",
            "group_ids": [g.group_id for g in phase1_groups],
            "reasoning": "Zero variations, pure functions, low risk",
        },
        {
            "phase": 2,
            "name": "unification_required",
            "group_ids": [g.group_id for g in phase2_groups],
            "reasoning": "Need to reconcile inconsistent implementations",
        },
        {
            "phase": 3,
            "name": "complex_patterns",
            "group_ids": [g.group_id for g in phase3_groups],
            "reasoning": "Higher complexity or risk",
        },
    ]
    
    return {
        "schema_version": "1.0.0",
        "generated_utc": generated_ts.isoformat(),
        "repo_root": str(repo_root),
        "scan_scope": scan_config,
        "duplicate_detection_config": {
            "similarity_threshold": scan_config.get("similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD),
            "min_lines": scan_config.get("min_lines", DEFAULT_MIN_LINES),
            "ignore_patterns": scan_config.get("ignore_patterns", []),
        },
        "duplicate_groups": [
            {
                "group_id": g.group_id,
                "signature_hash": g.signature_hash,
                "canonical_name": g.canonical_name,
                "purpose": g.purpose,
                "category": g.category,
                "occurrences": [occ.to_dict() for occ in g.occurrences],
                "analysis": {
                    "similarity_score": g.similarity_score,
                    "type": g.duplicate_type,
                    "variations": [],  # TODO: Detail variations
                    "complexity": "low",
                    "dependencies": [],  # TODO: Extract from AST
                },
                "library_recommendation": g.library_recommendation,
                "refactoring_action": g.refactoring_action,
                "impact_analysis": g.impact_analysis,
            }
            for g in duplicate_groups
        ],
        "summary": {
            "total_duplicate_groups": len(duplicate_groups),
            "total_occurrences": total_occurrences,
            "total_lines_duplicated": total_lines_duplicated,
            "potential_lines_saved": total_lines_duplicated - len(duplicate_groups) * 10,  # Estimate
            "files_requiring_changes": len(set(occ.file for g in duplicate_groups for occ in g.occurrences)),
            "library_files_to_create": len(duplicate_groups),
            "test_files_to_create": len(duplicate_groups),
            "estimated_total_effort": "3-5 developer days",
            "priority_breakdown": priority_breakdown,
            "risk_breakdown": risk_breakdown,
        },
        "execution_order": execution_order,
        "ai_agent_instructions": {
            "workflow": "autonomous_refactoring_pipeline",
            "phases": [
                {
                    "phase": 1,
                    "name": "inspect_library",
                    "instruction": "For each duplicate_group, check if library_recommendation.target_path already exists.",
                },
                {
                    "phase": 2,
                    "name": "create_library_function",
                    "instruction": "Extract code from occurrence with highest confidence.",
                },
                {
                    "phase": 3,
                    "name": "create_tests",
                    "instruction": "Generate pytest test file with comprehensive coverage.",
                },
                {
                    "phase": 4,
                    "name": "replace_in_source_files",
                    "instruction": "Delete specified line_range, add import_statement.",
                },
                {
                    "phase": 5,
                    "name": "validate",
                    "instruction": "Run test_files in sequence. Rollback on failure.",
                },
                {
                    "phase": 6,
                    "name": "full_suite_validation",
                    "instruction": "Run full test suite. Report new failures.",
                },
            ],
        },
    }


def write_summary_markdown(report: dict[str, Any]) -> str:
    """Generate human-readable summary."""
    summary = report["summary"]
    lines = [
        "# Duplicate Code Detection Summary\n",
        f"Generated: {report['generated_utc']}\n",
        f"Repo Root: {report['repo_root']}\n",
        "\n## Overview\n",
        f"- **Duplicate Groups Found:** {summary['total_duplicate_groups']}",
        f"- **Total Occurrences:** {summary['total_occurrences']}",
        f"- **Lines Duplicated:** {summary['total_lines_duplicated']}",
        f"- **Potential Lines Saved:** {summary['potential_lines_saved']}",
        f"- **Files Affected:** {summary['files_requiring_changes']}",
        "\n## Priority Breakdown\n",
        f"- High: {summary['priority_breakdown']['high']}",
        f"- Medium: {summary['priority_breakdown']['medium']}",
        f"- Low: {summary['priority_breakdown']['low']}",
        "\n## Risk Breakdown\n",
        f"- Low Risk: {summary['risk_breakdown']['low']}",
        f"- Medium Risk: {summary['risk_breakdown']['medium']}",
        f"- High Risk: {summary['risk_breakdown']['high']}",
        "\n## Recommended Execution Order\n",
    ]
    
    for phase in report["execution_order"]:
        lines.append(f"\n### Phase {phase['phase']}: {phase['name']}")
        lines.append(f"- Groups: {len(phase['group_ids'])}")
        lines.append(f"- Reasoning: {phase['reasoning']}")
    
    lines.append("\n## Next Steps\n")
    lines.append("1. Review full report: `latest_report.json`")
    lines.append("2. Inspect Phase 1 groups (safe extractions)")
    lines.append("3. Run manual extraction for validation (Phase 3 of implementation plan)")
    lines.append("4. Proceed with automated refactoring (Phase 4 of implementation plan)")
    
    return "\n".join(lines) + "\n"


def write_artifacts(
    report: dict[str, Any],
    output_dir: Path,
    keep: int,
) -> Path:
    """Write report artifacts with pruning."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_ts = datetime.fromisoformat(report["generated_utc"])
    run_dir = output_dir / f"{RUN_PREFIX}-{generated_ts.strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Write JSON report
    json_path = run_dir / "report.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    
    # Write markdown summary
    md_path = run_dir / "summary.md"
    md_path.write_text(write_summary_markdown(report), encoding="utf-8")
    
    # Create latest links
    latest_pairs = [
        (json_path, output_dir / "latest_report.json"),
        (md_path, output_dir / "latest_summary.md"),
    ]
    
    for src, dest in latest_pairs:
        try:
            if dest.exists():
                dest.unlink()
            dest.hardlink_to(src)
        except OSError:
            dest.write_bytes(src.read_bytes())
    
    # Prune old runs
    prune_old_runs(output_dir, keep=keep, current_run=run_dir)
    
    return run_dir


def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:
    """Delete old run directories."""
    keep = max(keep, 1)
    if not output_dir.exists():
        return
    
    candidates = [
        path
        for path in output_dir.iterdir()
        if path.is_dir() and path.name.startswith(f"{RUN_PREFIX}-")
    ]
    candidates.sort(key=lambda p: p.name, reverse=True)
    
    for idx, path in enumerate(candidates):
        if idx < keep or path == current_run:
            continue
        for child in path.iterdir():
            if child.is_file():
                child.unlink(missing_ok=True)
        path.rmdir()


def configure_logging(level: str) -> None:
    """Configure logging."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=numeric_level, format="%(levelname)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scan Python codebase for duplicates using AST analysis")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--scan-dirs", nargs="+", type=Path, help="Directories to scan (relative to repo-root)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--similarity-threshold", type=float, default=DEFAULT_SIMILARITY_THRESHOLD, help="Similarity threshold (0-1)")
    parser.add_argument("--min-lines", type=int, default=DEFAULT_MIN_LINES, help="Minimum function lines")
    parser.add_argument("--artifacts-to-keep", type=int, default=DEFAULT_ARTIFACTS_TO_KEEP, help="Artifacts to retain")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args(argv)
    configure_logging(args.log_level)
    
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    
    # Determine scan directories
    scan_dirs = args.scan_dirs or [repo_root / ".repo_studios" / "scripts"]
    scan_dirs = [d if d.is_absolute() else repo_root / d for d in scan_dirs]
    
    logging.info("Scanning directories: %s", [str(d) for d in scan_dirs])
    
    # Scan Python files
    all_files = []
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            logging.warning("Scan directory does not exist: %s", scan_dir)
            continue
        all_files.extend(scan_python_files(scan_dir))
    
    logging.info("Found %d Python files", len(all_files))
    
    # Extract functions
    all_functions = []
    for filepath in all_files:
        funcs = extract_functions_from_file(filepath, repo_root)
        all_functions.extend(funcs)
    
    logging.info("Extracted %d functions", len(all_functions))
    
    # Group duplicates
    duplicate_groups_raw = group_duplicates(
        all_functions,
        similarity_threshold=args.similarity_threshold,
        min_lines=args.min_lines,
    )
    
    logging.info("Found %d duplicate groups", len(duplicate_groups_raw))
    
    # Build duplicate group objects
    duplicate_groups = [
        build_duplicate_group(group, f"dup_{idx:03d}", 1.0 if len(set(f.code_hash for f in group)) == 1 else 0.9)
        for idx, group in enumerate(duplicate_groups_raw, start=1)
    ]
    
    # Build report
    generated_ts = datetime.now(timezone.utc)
    scan_config = {
        "directories": [str(d.relative_to(repo_root)) for d in scan_dirs],
        "file_count": len(all_files),
        "total_lines_scanned": sum(len(f.body_lines) for f in all_functions),
        "similarity_threshold": args.similarity_threshold,
        "min_lines": args.min_lines,
    }
    
    report = build_report(duplicate_groups, scan_config, repo_root, generated_ts)
    
    # Write artifacts
    run_dir = write_artifacts(report, output_dir, keep=args.artifacts_to_keep)
    
    logging.info("Report written to: %s", run_dir)
    logging.info("Summary: %d duplicate groups, %d total occurrences", len(duplicate_groups), report["summary"]["total_occurrences"])
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
