#!/usr/bin/env python3
"""Generate a co-located function inventory for a repo folder."""
from __future__ import annotations

import argparse
import ast
import json
import logging
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SKIP_DIRS = {"__pycache__", ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "build", "dist", ".tox"}
DEFAULT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path


@dataclass(frozen=True)
class Options:
    schema_version: int
    log_level: str


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_function_inventory",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "target",
        help="Directory to index. Relative paths resolve within the repo root.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repository root. Defaults to script's grandparent directory.",
    )
    parser.add_argument(
        "--schema-version",
        type=int,
        default=DEFAULT_SCHEMA_VERSION,
        help="Schema version to stamp in the JSON payload.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[3]
    target_candidate = Path(args.target)
    target = target_candidate if target_candidate.is_absolute() else (repo_root / target_candidate)
    target = target.resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Target path must reside within repo root: {target}") from exc
    return Paths(repo_root=repo_root, target=target)


def build_options(args: argparse.Namespace) -> Options:
    return Options(schema_version=int(args.schema_version), log_level=args.log_level)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def discover_python_files(target: Path) -> list[Path]:
    results: list[Path] = []
    for path in target.rglob("*.py"):
        try:
            relative_parts = path.relative_to(target).parts
        except ValueError:
            # Should not happen, but skip anything outside the target slice.
            continue
        if any(part in SKIP_DIRS for part in relative_parts[:-1]):
            continue
        if any(part.startswith(".") for part in relative_parts[:-1]):
            continue
        results.append(path)
    results.sort()
    return results


def _docstring_first_line(value: str | None) -> str | None:
    if not value:
        return None
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _extract_imports(tree: ast.AST) -> list[str]:
    items: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                items.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                items.add(f"{module}.{alias.name}" if module else alias.name)
    return sorted(items)


def _extract_first_statement_line(tree: ast.Module, source: str) -> str | None:
    first_class: str | None = None
    first_other: str | None = None
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            # skip module docstring or other literal expressions
            if isinstance(node.value.value, str):
                continue
        segment = ast.get_source_segment(source, node) if source else None
        line: str | None = None
        if segment:
            first_line = segment.splitlines()[0].strip()
            if first_line:
                line = first_line
        if line is None:
            line_no = getattr(node, "lineno", None)
            if line_no is not None:
                lines = source.splitlines()
                if 1 <= line_no <= len(lines):
                    candidate = lines[line_no - 1].strip()
                    if candidate:
                        line = candidate
        if not line:
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return line
        if isinstance(node, ast.ClassDef) and first_class is None:
            first_class = line
            continue
        if first_other is None:
            first_other = line
    return first_class or first_other


def _extract_function(node: ast.AST, source: str) -> dict[str, Any]:
    docstring = ast.get_docstring(node)
    is_async = isinstance(node, ast.AsyncFunctionDef)
    name = getattr(node, "name", "<unknown>")
    source_segment = ast.get_source_segment(source, node) if source else None
    signature: str | None = None
    if source_segment:
        first_line = source_segment.splitlines()[0].strip()
        signature = first_line or None
    end_lineno = getattr(node, "end_lineno", None)
    line_count = None
    if end_lineno is not None and getattr(node, "lineno", None) is not None:
        line_count = max(0, end_lineno - node.lineno + 1)
    return {
        "name": name,
        "line": getattr(node, "lineno", 0),
        "type": "function",
        "is_async": is_async,
        "is_private": name.startswith("_"),
        "docstring": _docstring_first_line(docstring),
        "signature": signature,
        "line_count": line_count,
    }


def _extract_class(node: ast.ClassDef, source: str) -> dict[str, Any]:
    docstring = ast.get_docstring(node)
    end_lineno = getattr(node, "end_lineno", None)
    line_count = None
    if end_lineno is not None:
        line_count = max(0, end_lineno - node.lineno + 1)
    methods: list[dict[str, Any]] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_function(child, source))
    return {
        "name": node.name,
        "line": node.lineno,
        "docstring": _docstring_first_line(docstring),
        "methods": methods,
        "line_count": line_count,
    }


def analyze_python_file(path: Path, slice_root: Path, warnings: list[str]) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(f"Failed to read {path}: {exc}")
        logging.warning("Failed to read %s: %s", path, exc)
        return None

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        message = f"Syntax error in {path}: {exc.msg} (line {exc.lineno})"
        warnings.append(message)
        logging.warning(message)
        return None
    except Exception as exc:  # pragma: no cover - defensive
        warnings.append(f"Unexpected error parsing {path}: {exc}")
        logging.exception("Unexpected error parsing %s", path)
        return None

    line_count = len(text.splitlines())
    first_statement = _extract_first_statement_line(tree, text)
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_function(node, text))
        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node, text))
    imports = _extract_imports(tree)
    relative = path.relative_to(slice_root)
    return {
        "path": str(path),
        "relative_path": relative.as_posix(),
        "line_count": line_count,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "module_first_line": first_statement,
    }


def compose_inventory(paths: Paths, options: Options, files: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    total_functions = 0
    total_classes = 0
    stats_counter = Counter()
    private_count = 0
    public_count = 0
    async_count = 0

    for entry in files:
        func_count = len(entry["functions"])
        class_count = len(entry["classes"])
        total_functions += func_count
        total_classes += class_count
        stats_counter[".py"] += 1
        for func in entry["functions"]:
            if func.get("is_private"):
                private_count += 1
            else:
                public_count += 1
            if func.get("is_async"):
                async_count += 1
        for cls in entry["classes"]:
            stats_counter[".py"] += 0  # keep extension key present
            for method in cls.get("methods", []):
                total_functions += 1
                if method.get("is_private"):
                    private_count += 1
                else:
                    public_count += 1
                if method.get("is_async"):
                    async_count += 1

    total_lines = sum(entry["line_count"] for entry in files)

    metadata = {
        "schema_version": options.schema_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "folder_path": str(paths.target),
        "folder_name": paths.target.name,
        "total_files": len(files),
        "total_functions": total_functions,
        "total_classes": total_classes,
        "scan_depth": "recursive",
    }

    statistics = {
        "total_lines_of_code": total_lines,
        "files_by_type": dict(stats_counter),
        "private_functions": private_count,
        "public_functions": public_count,
        "async_functions": async_count,
    }

    payload = {
        "metadata": metadata,
        "files": files,
        "statistics": statistics,
    }
    if warnings:
        payload["warnings"] = warnings
    return payload


def write_inventory(paths: Paths, payload: dict[str, Any]) -> Path:
    target_dir = paths.target
    output_dir = target_dir / f"{target_dir.name}_index"
    output_dir.mkdir(parents=True, exist_ok=True)
    legacy_file = output_dir / f"{target_dir.name}_index.json"
    if legacy_file.exists():
        legacy_file.unlink()
    for existing in output_dir.glob(f"{target_dir.name}_index-*.json"):
        if existing.is_file():
            existing.unlink()
    date_suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = output_dir / f"{target_dir.name}_index-{date_suffix}.json"
    temp_file = output_file.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(output_file)
    latest_pointer = output_dir / "latest.json"
    latest_temp = latest_pointer.with_name(f"{latest_pointer.name}.tmp")
    latest_temp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    latest_temp.replace(latest_pointer)
    return output_file


def run(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    options = build_options(args)
    configure_logging(options.log_level)

    try:
        paths = build_paths(args)
    except ValueError as exc:
        logging.error("%s", exc)
        return 1

    if not paths.target.exists():
        logging.error("Target does not exist: %s", paths.target)
        return 1
    if not paths.target.is_dir():
        logging.error("Target is not a directory: %s", paths.target)
        return 1

    python_files = discover_python_files(paths.target)
    if not python_files:
        logging.error("No Python files found under %s", paths.target)
        return 1

    warnings: list[str] = []
    collected: list[dict[str, Any]] = []
    for file_path in python_files:
        result = analyze_python_file(file_path, paths.target, warnings)
        if result:
            collected.append(result)

    if not collected:
        logging.error("All Python files failed to parse under %s", paths.target)
        return 1

    payload = compose_inventory(paths, options, collected, warnings)
    output_file = write_inventory(paths, payload)
    logging.info(
        "Inventory generated: path=%s files=%d functions=%d classes=%d warnings=%d",
        output_file,
        payload["metadata"]["total_files"],
        payload["metadata"]["total_functions"],
        payload["metadata"]["total_classes"],
        len(warnings),
    )
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
