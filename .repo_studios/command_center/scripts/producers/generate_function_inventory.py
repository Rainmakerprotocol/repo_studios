#!/usr/bin/env python3
"""Generate a co-located function inventory for a repo folder."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import logging
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SKIP_DIRS = {"__pycache__", ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "build", "dist", ".tox"}
BRANCH_NODE_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)
DEFAULT_SCHEMA_VERSION = 2
DEFAULT_REPORTS_ROOT_RELATIVE = Path(".repo_studios/command_center/reports/index_scan")


def _safe_unparse(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:  # pragma: no cover - fallback path
        return None


def _relative_module_id(relative_path: Path, root_name: str | None = None) -> str:
    without_suffix = relative_path.with_suffix("")
    parts = list(without_suffix.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        parts = []
    if root_name:
        parts = [root_name] + parts
    if not parts:
        return ""
    return ".".join(parts)


def _docstring_summary(value: str | None) -> str | None:
    if not value:
        return None
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def _classify_global_value(node: ast.AST | None) -> str:
    if node is None:
        return "other"
    if isinstance(node, ast.Call):
        return "call"
    if isinstance(node, ast.Constant):
        return "const"
    if isinstance(node, (ast.Dict, ast.List, ast.Set, ast.Tuple)):
        return "config"
    return "other"


def _attribute_root(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, ast.Attribute):
        if isinstance(current.value, ast.Name):
            return current.value.id
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return None


def _extract_imports_detailed(tree: ast.AST) -> tuple[list[dict[str, Any]], dict[str, str]]:
    details: list[dict[str, Any]] = []
    alias_map: dict[str, str] = {}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.Import):
            names: list[dict[str, Any]] = []
            for alias in node.names:
                exposed = alias.asname or alias.name
                alias_map[exposed] = alias.name
                names.append({"name": alias.name, "asname": alias.asname})
            details.append({
                "kind": "import",
                "module": None,
                "names": names,
                "lineno": node.lineno,
            })
        elif isinstance(node, ast.ImportFrom):
            names = []
            module = node.module or ""
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                exposed = alias.asname or alias.name
                alias_map[exposed] = full_name
                names.append({"name": alias.name, "asname": alias.asname})
            details.append({
                "kind": "from",
                "module": module,
                "names": names,
                "lineno": node.lineno,
            })
    return details, alias_map


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path
    reports_root: Path


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
    parser.add_argument(
        "--reports-root",
        help=(
            "Optional directory for centralized inventory copies. "
            "Defaults to .repo_studios/command_center/reports/index_scan within the repo root."
        ),
    )
    return parser.parse_args(argv)


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[4]
    target_candidate = Path(args.target)
    target = target_candidate if target_candidate.is_absolute() else (repo_root / target_candidate)
    target = target.resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Target path must reside within repo root: {target}") from exc
    if args.reports_root:
        reports_candidate = Path(args.reports_root)
        reports_root = reports_candidate if reports_candidate.is_absolute() else repo_root / reports_candidate
    else:
        reports_root = repo_root / DEFAULT_REPORTS_ROOT_RELATIVE
    reports_root = reports_root.resolve()
    try:
        reports_root.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Reports root must reside within repo root: {reports_root}") from exc
    reports_root.mkdir(parents=True, exist_ok=True)
    return Paths(repo_root=repo_root, target=target, reports_root=reports_root)


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
    return _docstring_summary(value)


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


def _signature_structure(arguments: ast.arguments) -> dict[str, Any]:
    def _names(nodes: list[ast.arg]) -> list[str]:
        return [node.arg for node in nodes]

    return {
        "positional": _names(arguments.posonlyargs + arguments.args),
        "kwonly": _names(arguments.kwonlyargs),
        "vararg": arguments.vararg.arg if arguments.vararg else None,
        "kwvararg": arguments.kwarg.arg if arguments.kwarg else None,
    }


def _annotation_map(node: ast.AST) -> dict[str, Any]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {"return": None, "args": {}}
    annotations: dict[str, str | None] = {}
    for arg in list(node.args.posonlyargs) + list(node.args.args):
        annotations[arg.arg] = _safe_unparse(arg.annotation)
    for arg in node.args.kwonlyargs:
        annotations[arg.arg] = _safe_unparse(arg.annotation)
    if node.args.vararg:
        annotations[node.args.vararg.arg] = _safe_unparse(node.args.vararg.annotation)
    if node.args.kwarg:
        annotations[node.args.kwarg.arg] = _safe_unparse(node.args.kwarg.annotation)
    return {
        "return": _safe_unparse(node.returns),
        "args": {name: value for name, value in annotations.items()},
    }


def _returns_kind(node: ast.AST) -> str:
    is_async = isinstance(node, ast.AsyncFunctionDef)
    has_yield = any(isinstance(item, (ast.Yield, ast.YieldFrom)) for item in ast.walk(node))
    if is_async:
        return "async"
    if has_yield:
        return "generator"
    for item in ast.walk(node):
        if isinstance(item, ast.Return) and item.value is not None:
            return "value"
    return "none"


def _first_stmt_kind(node: ast.AST) -> str | None:
    body = getattr(node, "body", None)
    if not body:
        return None
    return body[0].__class__.__name__.lower()


def _collect_function_metrics(
    node: ast.AST,
    source: str,
    import_alias_map: dict[str, str],
    defined_local_symbols: set[str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, bool],
    list[dict[str, Any]],
    dict[str, int],
    set[str],
    int,
]:
    calls: list[dict[str, Any]] = []
    uses_import: list[dict[str, Any]] = []
    intra_file_refs: list[dict[str, Any]] = []
    io_effects = {"reads": False, "writes": False, "env": False, "network": False}
    logging_calls: list[dict[str, Any]] = []
    locals_summary = {"assign": 0, "calls": 0, "branches": 0}
    used_globals: set[str] = set()
    todo_tags = 0

    todo_pattern = re.compile(r"\b(?:TODO|FIXME)\b", re.IGNORECASE)

    for inner in ast.walk(node):
        if isinstance(inner, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            locals_summary["assign"] += 1
        if isinstance(inner, ast.Call):
            locals_summary["calls"] += 1
            callee = _safe_unparse(inner.func) or "<unknown>"
            calls.append({"callee": callee, "lineno": inner.lineno})
            root_name = _attribute_root(inner.func) or callee.split("(")[0]
            if root_name in import_alias_map:
                uses_import.append({
                    "symbol": import_alias_map[root_name],
                    "via": root_name,
                    "lineno": inner.lineno,
                })
            if callee in defined_local_symbols:
                intra_file_refs.append({"callee_func": callee, "lineno": inner.lineno})

            # I/O detection heuristics
            if callee == "open" or callee.endswith(".open"):
                mode_arg = None
                if len(inner.args) >= 2:
                    mode_arg = inner.args[1]
                elif any(isinstance(kw, ast.keyword) and kw.arg == "mode" for kw in inner.keywords):
                    kw = next(kw for kw in inner.keywords if kw.arg == "mode")
                    mode_arg = kw.value
                mode_value = None
                if isinstance(mode_arg, ast.Constant) and isinstance(mode_arg.value, str):
                    mode_value = mode_arg.value
                if mode_value is None:
                    io_effects["reads"] = True
                else:
                    if any(flag in mode_value for flag in ("r", "+")):
                        io_effects["reads"] = True
                    if any(flag in mode_value for flag in ("w", "a", "x", "+")):
                        io_effects["writes"] = True
            root = _attribute_root(inner.func)
            attr = inner.func.attr if isinstance(inner.func, ast.Attribute) else None
            if root == "os" and attr in {"getenv"}:
                io_effects["env"] = True
            if root == "os" and isinstance(inner.func, ast.Attribute) and inner.func.attr == "environ":
                io_effects["env"] = True
            if root in {"requests", "urllib", "http", "socket"}:
                io_effects["network"] = True
            if root == "logging" and attr in {"debug", "info", "warning", "error", "critical", "exception"}:
                logging_calls.append({"level": attr.lower(), "lineno": inner.lineno})
        if isinstance(inner, BRANCH_NODE_TYPES):
            locals_summary["branches"] += 1
        if isinstance(inner, ast.Global):
            used_globals.update(inner.names)
        if isinstance(inner, ast.Nonlocal):
            used_globals.update(inner.names)
        if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
            if inner.id in import_alias_map:
                uses_import.append({
                    "symbol": import_alias_map[inner.id],
                    "via": inner.id,
                    "lineno": inner.lineno,
                })
        if isinstance(inner, ast.Attribute):
            root = _attribute_root(inner)
            if root == "os" and inner.attr == "environ":
                io_effects["env"] = True

    source_segment = ast.get_source_segment(source, node) or ""
    todo_tags = len(todo_pattern.findall(source_segment))

    def _dedupe(entries: list[dict[str, Any]], key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        results: list[dict[str, Any]] = []
        for item in entries:
            key = tuple(item.get(field) for field in key_fields)
            if key in seen:
                continue
            seen.add(key)
            results.append(item)
        return results

    uses_import = _dedupe(uses_import, ("symbol", "via", "lineno"))
    intra_file_refs = _dedupe(intra_file_refs, ("callee_func", "lineno"))

    return calls, uses_import, intra_file_refs, io_effects, logging_calls, locals_summary, used_globals, todo_tags


def _extract_function(
    node: ast.AST,
    source: str,
    module_id: str,
    relative_key: str,
    import_alias_map: dict[str, str],
    defined_local_symbols: set[str],
    parent_class: str | None = None,
) -> dict[str, Any]:
    docstring = ast.get_docstring(node)
    is_async = isinstance(node, ast.AsyncFunctionDef)
    name = getattr(node, "name", "<unknown>")
    source_segment = ast.get_source_segment(source, node) or ""
    signature_line: str | None = None
    if source_segment:
        first_line = source_segment.splitlines()[0].strip()
        signature_line = first_line or None
    end_lineno = getattr(node, "end_lineno", None)
    line_count = None
    if end_lineno is not None and getattr(node, "lineno", None) is not None:
        line_count = max(0, end_lineno - node.lineno + 1)
    qualified_name_prefix = module_id or relative_key
    if parent_class:
        qualified_name = f"{qualified_name_prefix}::{parent_class}.{name}"
        display_name = f"{parent_class}.{name}"
    else:
        qualified_name = f"{qualified_name_prefix}::{name}"
        display_name = name

    calls, uses_import, intra_file_refs, io_effects, logging_calls, locals_summary, used_globals, todo_tags = _collect_function_metrics(
        node,
        source,
        import_alias_map,
        defined_local_symbols,
    )

    raises = []
    for inner in ast.walk(node):
        if isinstance(inner, ast.Raise) and inner.exc is not None:
            expr = _safe_unparse(inner.exc)
            if expr:
                raises.append({"exception": expr, "lineno": inner.lineno})

    function_hash = hashlib.sha1(source_segment.encode("utf-8")).hexdigest() if source_segment else None

    args_structure = _signature_structure(node.args) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else {}
    annotations = _annotation_map(node)
    decorators = [value for value in (_safe_unparse(deco) for deco in getattr(node, "decorator_list", [])) if value]

    return {
        "name": display_name,
        "qualified_name": qualified_name,
        "line": getattr(node, "lineno", 0),
        "type": "function",
        "is_async": is_async,
        "is_private": name.startswith("_"),
        "docstring": _docstring_summary(docstring),
        "signature": signature_line,
        "line_count": line_count,
        "args": args_structure,
        "annotations": annotations,
        "decorators": decorators,
        "raises": raises,
        "returns_kind": _returns_kind(node),
        "locals_summary": locals_summary,
        "used_globals": sorted(used_globals),
        "hash": function_hash,
        "todo_tags": todo_tags,
        "first_stmt_kind": _first_stmt_kind(node),
        "calls": calls,
        "uses_import": uses_import,
        "intra_file_refs": intra_file_refs,
        "io_effects": io_effects,
        "logging_calls": logging_calls,
    }


def _extract_class(
    node: ast.ClassDef,
    source: str,
    module_id: str,
    relative_key: str,
    import_alias_map: dict[str, str],
    defined_local_symbols: set[str],
) -> dict[str, Any]:
    docstring = ast.get_docstring(node)
    end_lineno = getattr(node, "end_lineno", None)
    line_count = None
    if end_lineno is not None:
        line_count = max(0, end_lineno - node.lineno + 1)
    bases = [value for value in (_safe_unparse(base) for base in node.bases) if value]
    decorators = [value for value in (_safe_unparse(deco) for deco in node.decorator_list) if value]
    attributes: list[dict[str, Any]] = []
    methods: list[dict[str, Any]] = []
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(
                _extract_function(
                    child,
                    source,
                    module_id,
                    relative_key,
                    import_alias_map,
                    defined_local_symbols,
                    parent_class=node.name,
                )
            )
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(child, ast.Assign):
                targets = [t for t in child.targets if isinstance(t, ast.Name)]
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
                targets = [child.target]
            for target in targets:
                attributes.append({"name": target.id, "lineno": target.lineno})
    return {
        "name": node.name,
        "line": node.lineno,
        "docstring": _docstring_summary(docstring),
        "methods": methods,
        "line_count": line_count,
        "bases": bases,
        "decorators": decorators,
        "attributes": attributes,
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
    relative = path.relative_to(slice_root)
    module_id = _relative_module_id(relative, slice_root.name)
    relative_key = relative.with_suffix("").as_posix()

    imports_detailed, import_alias_map = _extract_imports_detailed(tree)
    imports_flat: set[str] = set()
    for detail in imports_detailed:
        if detail["kind"] == "import":
            for item in detail["names"]:
                imports_flat.add(item["name"])
        else:
            module_name = detail["module"] or ""
            for item in detail["names"]:
                imports_flat.add(f"{module_name}.{item['name']}" if module_name else item["name"])

    globals_block: list[dict[str, Any]] = []
    has_main_guard = False
    cli_parser = False
    defined_symbols: set[str] = set()

    # First pass to collect definition names
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_symbols.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_symbols.add(f"{node.name}.{child.name}")

    # Second pass for globals and entrypoints
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value_node = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
            targets: list[ast.Name] = []
            if isinstance(node, ast.Assign):
                targets = [t for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target]
            for target in targets:
                globals_block.append(
                    {
                        "name": target.id,
                        "value_kind": _classify_global_value(value_node),
                        "lineno": target.lineno,
                    }
                )
        if isinstance(node, ast.If):
            test = node.test
            if (
                isinstance(test, ast.Compare)
                and len(test.ops) == 1
                and isinstance(test.ops[0], ast.Eq)
                and isinstance(test.left, ast.Name)
                and test.left.id == "__name__"
                and any(
                    isinstance(comp, ast.Constant) and comp.value == "__main__"
                    for comp in test.comparators
                )
            ):
                has_main_guard = True

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = _safe_unparse(node.func) or ""
            if "ArgumentParser" in callee or (
                isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument"
            ):
                cli_parser = True

    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(
                _extract_function(
                    node,
                    text,
                    module_id,
                    relative_key,
                    import_alias_map,
                    defined_symbols,
                )
            )
        elif isinstance(node, ast.ClassDef):
            classes.append(
                _extract_class(
                    node,
                    text,
                    module_id,
                    relative_key,
                    import_alias_map,
                    defined_symbols,
                )
            )

    return {
        "path": str(path),
        "relative_path": relative.as_posix(),
        "module_id": module_id,
        "module_doc": _docstring_summary(ast.get_docstring(tree)),
        "line_count": line_count,
        "functions": functions,
        "classes": classes,
        "imports": sorted(imports_flat),
        "imports_detailed": imports_detailed,
        "globals": globals_block,
        "entrypoints": {"has_main_guard": has_main_guard, "cli_parser": cli_parser},
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


def build_screening_summary(files: list[dict[str, Any]]) -> dict[str, Any]:
    import_edges: set[tuple[str, str]] = set()
    call_edges: set[tuple[str, str]] = set()
    nodes_meta: dict[str, dict[str, Any]] = {}

    for entry in files:
        module_key = entry.get("module_id") or entry.get("relative_path", "").replace("/", ".")
        imports_detailed = entry.get("imports_detailed", [])
        for detail in imports_detailed:
            if detail.get("kind") == "import":
                for item in detail.get("names", []):
                    target = item.get("name")
                    if target:
                        import_edges.add((module_key, target))
            elif detail.get("kind") == "from":
                base = detail.get("module") or ""
                for item in detail.get("names", []):
                    name = item.get("name")
                    if name:
                        target = f"{base}.{name}" if base else name
                        import_edges.add((module_key, target))

        def _capture_function(function_entry: dict[str, Any]) -> None:
            source = function_entry.get("qualified_name")
            if not source:
                return
            nodes_meta[source] = {
                "hash": function_entry.get("hash"),
                "io_effects": function_entry.get("io_effects", {}),
            }
            for call in function_entry.get("calls", []):
                callee = call.get("callee")
                if callee:
                    call_edges.add((source, callee))
            for ref in function_entry.get("intra_file_refs", []):
                callee = ref.get("callee_func")
                if callee:
                    target = f"{module_key}::{callee}"
                    call_edges.add((source, target))

        for function_entry in entry.get("functions", []):
            _capture_function(function_entry)
        for class_entry in entry.get("classes", []):
            for method_entry in class_entry.get("methods", []):
                _capture_function(method_entry)

    imports_list = [list(edge) for edge in sorted(import_edges)]
    calls_list = [list(edge) for edge in sorted(call_edges)]

    return {
        "graphs": {
            "imports": imports_list,
            "calls": calls_list,
        },
        "violations": {"cycles": False},
        "nodes": {"meta": nodes_meta},
    }


def _write_inventory_copy(directory: Path, source_name: str, payload: dict[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    legacy_file = directory / f"{source_name}_index.json"
    if legacy_file.exists():
        legacy_file.unlink()
    for existing in directory.glob(f"{source_name}_index-*.json"):
        if existing.is_file():
            existing.unlink()
    date_suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = directory / f"{source_name}_index-{date_suffix}.json"
    temp_file = output_file.with_suffix(".json.tmp")
    temp_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(output_file)
    latest_pointer = directory / "latest.json"
    if latest_pointer.exists():
        latest_pointer.unlink()
    return output_file


def _write_screening_copy(directory: Path, source_name: str, summary: dict[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for existing in directory.glob(f"{source_name}_screening-*.json"):
        if existing.is_file():
            existing.unlink()
    date_suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = directory / f"{source_name}_screening-{date_suffix}.json"
    temp_file = output_file.with_suffix(".screening.json.tmp")
    temp_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(output_file)
    return output_file


def write_inventory(paths: Paths, payload: dict[str, Any], summary: dict[str, Any]) -> Path:
    source_name = paths.target.name
    primary_dir = paths.target / f"{source_name}_index"
    secondary_dir = paths.reports_root / f"{source_name}_index"
    primary = _write_inventory_copy(primary_dir, source_name, payload)
    _write_inventory_copy(secondary_dir, source_name, payload)
    _write_screening_copy(primary_dir, source_name, summary)
    _write_screening_copy(secondary_dir, source_name, summary)
    return primary


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
    summary = build_screening_summary(payload["files"])
    output_file = write_inventory(paths, payload, summary)
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
