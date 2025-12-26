#!/usr/bin/env python3
"""Generate a co-located function inventory for a repo folder."""

from __future__ import annotations

import argparse
import ast
import builtins
import hashlib
import json
import logging
import re
import sys
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "build",
    "dist",
    ".tox",
}
TEST_DIR_HINTS = {"tests", "test", "__tests__"}
TEST_DIR_PREFIXES = ("tests_",)
TEST_DIR_SUFFIXES = ("_tests",)
TEST_FILE_PREFIXES = ("test_",)
TEST_FILE_SUFFIXES = ("_test.py", "_tests.py")
PROJECT_NAMESPACE_HINTS = {"agents", "api", "mrp", "client_helpers", "scripts"}
BRANCH_NODE_TYPES = (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.Match)
DEFAULT_SCHEMA_VERSION = 2
STATIC_REPORTS_ROOT_RELATIVE = Path(".repo_studios/command_center/reports")
DEFAULT_REPORTS_ROOT_RELATIVE = STATIC_REPORTS_ROOT_RELATIVE / "index_scan"
STD_DECORATOR_NAMES = {"staticmethod", "classmethod", "property"}
STD_MODULE_PREFIXES = {"functools", "contextlib", "dataclasses", "abc", "typing", "inspect"}
DYNAMIC_EXEC_NAMES = {"exec", "eval", "execfile"}
DYNAMIC_IMPORT_NAMES = {"__import__", "import_module"}
ABSTRACT_BASE_HINTS = {"ABC", "ABCMeta", "Protocol", "ProtocolMeta"}
ABSTRACT_DECORATOR_SUFFIXES = {
    "abstractmethod",
    "abstractclassmethod",
    "abstractstaticmethod",
    "abstractproperty",
}
CODE_SMELL_LONG_FUNCTION_LINES = 80
CODE_SMELL_BRANCH_THRESHOLD = 6
CODE_SMELL_CALL_THRESHOLD = 15
CODE_SMELL_LONG_CLASS_LINES = 200
CODE_SMELL_METHOD_THRESHOLD = 12
CALLBACK_METHOD_ALWAYS = {
    "subscribe",
    "add_listener",
    "add_listeners",
    "add_handler",
    "add_handlers",
    "add_callback",
    "add_callbacks",
    "add_event_handler",
    "register_listener",
    "register_listeners",
    "register_handler",
    "register_handlers",
    "register_callback",
    "register_callbacks",
    "add_signal_handler",
    "register_signal_handler",
}
CALLBACK_METHOD_CONTEXTUAL = {
    "register",
    "connect",
    "listen",
    "on",
    "attach",
    "bind",
}
CALLBACK_METHOD_SUFFIXES = ("_listener", "_listeners", "_handler", "_handlers", "_callback", "_callbacks")
CALLBACK_CONTEXT_HINTS = (
    "bus",
    "dispatcher",
    "signal",
    "hook",
    "observer",
    "emitter",
    "event",
    "subscriber",
    "listener",
    "router",
    "webhook",
)
CALLBACK_TARGET_KEYWORDS = {
    "callback",
    "handler",
    "listener",
    "func",
    "function",
    "target",
    "receiver",
}
if hasattr(sys, "stdlib_module_names"):
    STDLIB_MODULE_NAMES = set(sys.stdlib_module_names)
else:  # pragma: no cover - fallback for older Python versions
    STDLIB_MODULE_NAMES = {
        "sys",
        "os",
        "math",
        "json",
        "pathlib",
        "typing",
        "collections",
        "itertools",
        "functools",
        "re",
    }

DEPENDENCY_SUMMARY_BUCKETS = ("internal", "standard_library", "third_party", "unknown")

DOCSTRING_WARNING_THRESHOLD = 80.0
DOCSTRING_FAILURE_THRESHOLD = 60.0
MAX_SCREENING_HISTORY_ENTRIES = 30

BUILTIN_FUNCTION_NAMES = {name for name, value in vars(builtins).items() if callable(value)}

_MATCH_NODE = (getattr(ast, "Match"),) if hasattr(ast, "Match") else tuple()

COMPLEXITY_NODE_TYPES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.IfExp,
    ast.With,
    ast.AsyncWith,
    *_MATCH_NODE,
)

LIBRARIES_ROOT = Path(__file__).resolve().parents[1]
REPO_STUDIOS_ROOT = LIBRARIES_ROOT.parents[2]

try:
    from libraries import resolve_repo_root, slugify_relative
except ModuleNotFoundError:  # pragma: no cover - fallback when run as script
    for candidate in (REPO_STUDIOS_ROOT, LIBRARIES_ROOT):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
    from libraries import resolve_repo_root, slugify_relative  # type: ignore  # noqa: E402


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


def _parameter_names(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    args = node.args
    names = [arg.arg for arg in args.posonlyargs + args.args]
    names.extend(arg.arg for arg in args.kwonlyargs)
    if args.vararg:
        names.append(args.vararg.arg)
    if args.kwarg:
        names.append(args.kwarg.arg)
    return [name for name in names if name not in {"self", "cls"}]


def _has_parameters_section(docstring: str) -> bool:
    return bool(
        re.search(r":param\b", docstring, re.IGNORECASE)
        or re.search(r"^\s*(Args?|Parameters?):", docstring, re.IGNORECASE | re.MULTILINE)
    )


def _has_returns_section(docstring: str) -> bool:
    return bool(
        re.search(r":return[s]?:", docstring, re.IGNORECASE)
        or re.search(r"^\s*Return[s]?:", docstring, re.IGNORECASE | re.MULTILINE)
    )


def _docstring_parameter_mentions(docstring: str, parameters: list[str]) -> tuple[list[str], list[str]]:
    lower_doc = docstring.lower()
    mentioned = sorted({name for name in parameters if name.lower() in lower_doc})
    missing = sorted(name for name in parameters if name not in mentioned)
    return mentioned, missing


def _function_code_smells(
    line_count: int | None,
    locals_summary: dict[str, int] | None,
    todo_tags: int,
) -> dict[str, bool]:
    summary = locals_summary or {}
    smells: dict[str, bool] = {}
    if line_count is not None and line_count > CODE_SMELL_LONG_FUNCTION_LINES:
        smells["long_function"] = True
    if summary.get("branches", 0) >= CODE_SMELL_BRANCH_THRESHOLD:
        smells["branching_heavy"] = True
    if summary.get("calls", 0) >= CODE_SMELL_CALL_THRESHOLD:
        smells["call_heavy"] = True
    if todo_tags > 0:
        smells["todo_comment"] = True
    return smells


def _class_code_smells(line_count: int | None, method_count: int) -> dict[str, bool]:
    smells: dict[str, bool] = {}
    if line_count is not None and line_count > CODE_SMELL_LONG_CLASS_LINES:
        smells["long_class"] = True
    if method_count >= CODE_SMELL_METHOD_THRESHOLD:
        smells["method_heavy"] = True
    return smells


def _cyclomatic_complexity(node: ast.AST) -> int:
    complexity = 1
    for inner in ast.walk(node):
        if isinstance(inner, COMPLEXITY_NODE_TYPES):
            complexity += 1
            if isinstance(inner, ast.Try):
                complexity += len(inner.handlers)
        elif isinstance(inner, ast.BoolOp):
            complexity += max(len(inner.values) - 1, 0)
        elif isinstance(inner, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            generators = getattr(inner, "generators", [])
            for comp in generators:
                complexity += 1
                complexity += len(getattr(comp, "ifs", []))
        elif isinstance(inner, ast.ExceptHandler):
            complexity += 1
    return complexity


def _normalize_callback_target(node: ast.AST) -> tuple[str | None, str | None]:
    if isinstance(node, ast.Name):
        return "name", node.id
    if isinstance(node, ast.Attribute):
        return "attribute", _safe_unparse(node)
    if isinstance(node, ast.Lambda):
        return "lambda", "<lambda>"
    if isinstance(node, ast.Call):
        return "call", _safe_unparse(node)
    if isinstance(node, ast.FunctionDef):  # pragma: no cover - uncommon inline definition
        return "function_def", getattr(node, "name", None)
    return None, None


def _select_callback_target(call: ast.Call) -> tuple[str | None, str | None, str | None]:
    for keyword in call.keywords or []:
        arg_name = keyword.arg or ""
        if arg_name.lower() in CALLBACK_TARGET_KEYWORDS:
            kind, value = _normalize_callback_target(keyword.value)
            if kind:
                return kind, value, arg_name
    for arg in call.args:
        if isinstance(arg, ast.Constant):
            continue
        kind, value = _normalize_callback_target(arg)
        if kind:
            return kind, value, "positional"
    return None, None, None


def _is_callback_callee(method_name: str | None, context_blob: str) -> bool:
    if not method_name:
        return False
    name = method_name.lower()
    if name in CALLBACK_METHOD_ALWAYS:
        return True
    if name in CALLBACK_METHOD_CONTEXTUAL:
        return any(hint in context_blob for hint in CALLBACK_CONTEXT_HINTS)
    if any(name.endswith(suffix) for suffix in CALLBACK_METHOD_SUFFIXES):
        return True
    if name.startswith("add_") and any(token in name for token in ("handler", "listener", "callback", "hook")):
        return True
    return False


def _callback_registration_info(call: ast.Call, import_alias_map: dict[str, str]) -> dict[str, Any] | None:
    func = call.func
    method_name: str | None = None
    root: str | None = None
    resolved: str | None = None
    module_path: str | None = None
    expression = _safe_unparse(func)
    if isinstance(func, ast.Attribute):
        method_name = func.attr
        root, resolved = _attribute_chain(func)
        if root and root in import_alias_map:
            module_path = import_alias_map[root]
    elif isinstance(func, ast.Name):
        method_name = func.id
    else:
        return None

    context_pieces = [part for part in (method_name, root, resolved, module_path) if part]
    context_blob = " ".join(part.lower() for part in context_pieces)
    if not _is_callback_callee(method_name, context_blob):
        return None

    target_kind, target_value, target_via = _select_callback_target(call)
    if not target_kind and not target_value:
        return None

    entry: dict[str, Any] = {
        "lineno": getattr(call, "lineno", None),
        "expression": expression,
        "method": method_name.lower() if method_name else None,
        "kind": "attribute" if isinstance(func, ast.Attribute) else "function",
        "root": root,
        "module": module_path,
        "target": target_value,
        "target_kind": target_kind,
        "target_via": target_via,
    }
    if resolved:
        entry["resolved"] = resolved
    return entry


def _docstring_quality(node: ast.AST, docstring: str | None) -> dict[str, Any]:
    parameters = sorted(_parameter_names(node))
    if not docstring or not docstring.strip():
        return {
            "exists": False,
            "line_count": 0,
            "nonempty_line_count": 0,
            "char_count": 0,
            "mentions_params": [],
            "missing_params": parameters,
            "has_parameters_section": False,
            "has_returns_section": False,
        }

    lines = docstring.splitlines()
    mentions, missing = _docstring_parameter_mentions(docstring, parameters)

    return {
        "exists": True,
        "line_count": len(lines),
        "nonempty_line_count": sum(1 for line in lines if line.strip()),
        "char_count": len(docstring),
        "mentions_params": mentions,
        "missing_params": missing,
        "has_parameters_section": _has_parameters_section(docstring),
        "has_returns_section": _has_returns_section(docstring),
    }


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


def _attribute_chain(node: ast.AST) -> tuple[str | None, str | None]:
    current = node
    parts: list[str] = []
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        root = current.id
    elif isinstance(current, ast.Call):  # pragma: no cover - uncommon decorator form
        return _attribute_chain(current.func)
    else:
        root = None
    if not parts:
        return root, root
    return root, ".".join(reversed(parts))


def _simplify_base_expression(value: str | None) -> str | None:
    if not value:
        return None
    trimmed = value.split("[", 1)[0]
    if " as " in trimmed:
        trimmed = trimmed.split(" as ", 1)[0]
    simplified = trimmed.split(".")[-1]
    return simplified or trimmed


def _decorator_base_name(resolved_path: str | None, root_name: str | None) -> str | None:
    if resolved_path:
        return resolved_path.split(".")[-1]
    return root_name


def _is_pytest_mark(resolved_path: str | None) -> bool:
    return bool(resolved_path and resolved_path.startswith("pytest.mark"))


def _is_click_command(module_path: str | None, resolved_path: str | None) -> bool:
    if module_path and module_path.startswith("click") and module_path.endswith(".command"):
        return True
    if resolved_path and resolved_path.endswith(".command"):
        return True
    return False


def _is_click_group(module_path: str | None, resolved_path: str | None) -> bool:
    if module_path and module_path.startswith("click") and module_path.endswith(".group"):
        return True
    if resolved_path and resolved_path.endswith(".group"):
        return True
    return False


def _is_project_decorator(
    base_name: str | None,
    defined_local_symbols: set[str],
    package_root: str | None,
    resolved_path: str | None,
) -> bool:
    if base_name and base_name in defined_local_symbols:
        return True
    if package_root and resolved_path and resolved_path.startswith(package_root):
        return True
    return False


def _is_globals_mutation(target: ast.expr) -> bool:
    if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Call):
        return _attribute_root(target.value.func) == "globals"
    return False


def _is_globals_setattr(call: ast.Call) -> bool:
    root = _attribute_root(call.func)
    if root != "setattr":
        return False
    if not call.args:
        return False
    first = call.args[0]
    if isinstance(first, ast.Call) and _attribute_root(first.func) == "globals":
        return True
    return False


def _detect_dynamic_code(tree: ast.AST) -> dict[str, Any]:
    flags = {
        "exec": False,
        "dynamic_import": False,
        "metaclass": False,
        "globals_mutation": False,
    }
    events: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            callee = _safe_unparse(node.func) or ""
            root = _attribute_root(node.func) or callee
            if root in DYNAMIC_EXEC_NAMES:
                flags["exec"] = True
                events.append({"kind": root, "lineno": getattr(node, "lineno", None), "detail": callee})
            elif root in DYNAMIC_IMPORT_NAMES or callee.endswith("import_module"):
                flags["dynamic_import"] = True
                events.append({"kind": "dynamic_import", "lineno": getattr(node, "lineno", None), "detail": callee})
            if _is_globals_setattr(node):
                flags["globals_mutation"] = True
                events.append({"kind": "globals_setattr", "lineno": getattr(node, "lineno", None), "detail": callee})
        elif isinstance(node, ast.ClassDef):
            for keyword in node.keywords or []:
                if keyword.arg == "metaclass":
                    flags["metaclass"] = True
                    events.append(
                        {
                            "kind": "metaclass",
                            "lineno": getattr(node, "lineno", None),
                            "detail": _safe_unparse(keyword.value),
                        }
                    )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if _is_globals_mutation(target):
                    flags["globals_mutation"] = True
                    events.append(
                        {
                            "kind": "globals_assign",
                            "lineno": getattr(target, "lineno", None),
                            "detail": _safe_unparse(target),
                        }
                    )
        elif isinstance(node, ast.AugAssign):
            if _is_globals_mutation(node.target):
                flags["globals_mutation"] = True
                events.append(
                    {
                        "kind": "globals_augassign",
                        "lineno": getattr(node.target, "lineno", None),
                        "detail": _safe_unparse(node.target),
                    }
                )

    return {"flags": flags, "events": events}


def _extract_literal_str_seq(node: ast.AST) -> tuple[list[str], bool]:
    symbols: list[str] = []
    dynamic = False
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                symbols.append(element.value)
            else:
                dynamic = True
    elif isinstance(node, ast.Constant) and isinstance(node.value, (list, tuple, set)):
        for element in node.value:
            if isinstance(element, str):
                symbols.append(element)
            else:
                dynamic = True
    else:
        dynamic = True
    return symbols, dynamic


def _extract_dunder_all(tree: ast.Module) -> dict[str, Any]:
    exports: dict[str, Any] = {
        "symbols": [],
        "dynamic": False,
        "lineno": None,
    }
    for node in tree.body:
        target_id = None
        value_node: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name) and t.id == "__all__"]
            if targets:
                target_id = "__all__"
                value_node = node.value
                exports["lineno"] = targets[0].lineno
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "__all__":
                target_id = "__all__"
                value_node = node.value
                exports["lineno"] = target.lineno
        elif isinstance(node, ast.AugAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "__all__":
                exports["dynamic"] = True
                exports.setdefault("lineno", target.lineno)
                continue
        if target_id != "__all__":
            continue
        if value_node is None:
            exports["dynamic"] = True
            continue
        symbols, dynamic = _extract_literal_str_seq(value_node)
        exports["symbols"] = symbols
        exports["dynamic"] = exports["dynamic"] or dynamic
    return exports


def _decorator_flags(module_path: str | None, resolved_path: str | None, base_name: str | None) -> dict[str, bool]:
    entries: list[tuple[str | None, bool]] = [
        (base_name, bool(base_name and base_name in STD_DECORATOR_NAMES)),
        ("pytest_mark", _is_pytest_mark(resolved_path)),
        ("click_command", _is_click_command(module_path, resolved_path)),
        ("click_group", _is_click_group(module_path, resolved_path)),
    ]
    keys = [flag for flag, condition in entries if flag and condition]
    if not keys:
        return {}
    return dict.fromkeys(sorted(keys), True)


def _classify_module_path(module_path: str | None, package_root: str | None) -> str | None:
    if not module_path:
        return None
    root_module = module_path.split(".")[0]
    if root_module in {"pytest", "click"}:
        return "framework"
    if root_module in STD_MODULE_PREFIXES:
        return "stdlib"
    if package_root and module_path.startswith(package_root):
        return "project"
    return None


def _decorator_classification(
    module_path: str | None,
    resolved_path: str | None,
    base_name: str | None,
    module_id: str,
    defined_local_symbols: set[str],
) -> str:
    package_root = module_id.split(".", 1)[0] if module_id else None
    if base_name in STD_DECORATOR_NAMES:
        return "stdlib"
    if _is_project_decorator(base_name, defined_local_symbols, package_root, resolved_path):
        return "project"
    classification = _classify_module_path(module_path, package_root)
    if classification:
        return classification
    return "unknown"


def _classify_decorator(
    module_path: str | None,
    resolved_path: str | None,
    root_name: str | None,
    module_id: str,
    defined_local_symbols: set[str],
) -> tuple[str, dict[str, bool]]:
    base_name = _decorator_base_name(resolved_path, root_name)
    flags = _decorator_flags(module_path, resolved_path, base_name)
    classification = _decorator_classification(
        module_path,
        resolved_path,
        base_name,
        module_id,
        defined_local_symbols,
    )
    return classification, flags


def _describe_decorator(
    node: ast.expr,
    import_alias_map: dict[str, str],
    module_id: str,
    defined_local_symbols: set[str],
) -> dict[str, Any]:
    expression = _safe_unparse(node)
    target = node.func if isinstance(node, ast.Call) else node
    root_name, resolved_path = _attribute_chain(target)
    module_path = import_alias_map.get(root_name) if root_name else None
    if not module_path and resolved_path:
        module_path = resolved_path
    classification, flags = _classify_decorator(
        module_path,
        resolved_path,
        root_name,
        module_id,
        defined_local_symbols,
    )
    return {
        "expression": expression,
        "root": root_name,
        "path": resolved_path,
        "module": module_path,
        "classification": classification,
        "flags": flags,
    }


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
            details.append(
                {
                    "kind": "import",
                    "module": None,
                    "names": names,
                    "lineno": node.lineno,
                    "level": 0,
                }
            )
        elif isinstance(node, ast.ImportFrom):
            names = []
            module = node.module or ""
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                exposed = alias.asname or alias.name
                alias_map[exposed] = full_name
                names.append({"name": alias.name, "asname": alias.asname})
            details.append(
                {
                    "kind": "from",
                    "module": module,
                    "names": names,
                    "lineno": node.lineno,
                    "level": getattr(node, "level", 0) or 0,
                }
            )
    return details, alias_map


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    target: Path
    target_relative: Path
    reports_root: Path


@dataclass(frozen=True)
class Options:
    schema_version: int
    log_level: str
    coverage_inputs: tuple[str, ...]


@dataclass
class CoverageInfo:
    path: Path
    executed: set[int]
    missing: set[int]
    contexts: dict[str, set[int]]


class CoverageIndex:
    def __init__(self) -> None:
        self._by_resolved: dict[str, CoverageInfo] = {}
        self._by_relative: dict[str, CoverageInfo] = {}

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return bool(self._by_resolved)

    def register(self, repo_root: Path, entry_path: str, data: dict[str, Any]) -> None:
        raw_path = Path(entry_path)
        resolved = raw_path if raw_path.is_absolute() else (repo_root / raw_path)
        resolved = resolved.resolve()

        info = self._by_resolved.get(resolved.as_posix())
        if info is None:
            info = CoverageInfo(path=resolved, executed=set(), missing=set(), contexts={})
            self._by_resolved[resolved.as_posix()] = info

        executed_lines = data.get("executed_lines") or []
        missing_lines = data.get("missing_lines") or []
        contexts_raw = data.get("contexts") or {}

        info.executed.update(int(line) for line in executed_lines)
        info.missing.update(int(line) for line in missing_lines)
        for context_name, lines in contexts_raw.items():
            bucket = info.contexts.setdefault(str(context_name), set())
            bucket.update(int(line) for line in lines)

        try:
            relative = resolved.relative_to(repo_root).as_posix()
            self._by_relative[relative] = info
        except ValueError:
            # Entry does not live under repo root; skip relative index.
            pass

    def get(self, absolute_path: Path, relative_path: Path | None = None) -> CoverageInfo | None:
        resolved_key = absolute_path.resolve().as_posix()
        info = self._by_resolved.get(resolved_key)
        if info is not None:
            return info
        if relative_path is not None:
            relative_key = relative_path.as_posix()
            info = self._by_relative.get(relative_key)
            if info is not None:
                return info
        return None


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_commandview_inventory",
        description=__doc__ or "",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "target",
        help="Directory to index. Relative paths resolve within the repo root.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root (auto-discovered via .repo_studios marker when omitted).",
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
            "Optional directory for centralized inventory copies inside "
            ".repo_studios/command_center/reports/. Defaults to the index_scan folder within that tree."
        ),
    )
    parser.add_argument(
        "--coverage-json",
        action="append",
        default=[],
        help="Optional coverage.py JSON report; provide multiple times to merge contexts.",
    )
    return parser.parse_args(argv)


_slugify_relative = slugify_relative


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    target_candidate = Path(args.target)
    target = target_candidate if target_candidate.is_absolute() else (repo_root / target_candidate)
    target = target.resolve()
    try:
        target.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Target path must reside within repo root: {target}") from exc
    target_relative = target.relative_to(repo_root)
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
    static_reports_root = (repo_root / STATIC_REPORTS_ROOT_RELATIVE).resolve()
    try:
        reports_root.relative_to(static_reports_root)
    except ValueError as exc:
        raise ValueError(
            "Reports root must reside under .repo_studios/command_center/reports for viewer discovery: "
            f"{reports_root}"
        ) from exc
    reports_root.mkdir(parents=True, exist_ok=True)
    return Paths(repo_root=repo_root, target=target, target_relative=target_relative, reports_root=reports_root)


def build_options(args: argparse.Namespace) -> Options:
    coverage_inputs = tuple(str(item) for item in (args.coverage_json or []))
    return Options(schema_version=int(args.schema_version), log_level=args.log_level, coverage_inputs=coverage_inputs)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper()), format="%(levelname)s %(message)s")


def load_coverage_reports(paths: Paths, coverage_inputs: tuple[str, ...]) -> tuple[CoverageIndex | None, list[str]]:
    if not coverage_inputs:
        return None, []
    index = CoverageIndex()
    loaded_sources: list[str] = []
    for raw in coverage_inputs:
        candidate = Path(raw)
        candidate = candidate if candidate.is_absolute() else (paths.repo_root / candidate)
        candidate = candidate.resolve()
        if not candidate.exists():
            logging.warning("Coverage file not found: %s", candidate)
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - defensive
            logging.warning("Failed to load coverage file %s: %s", candidate, exc)
            continue
        files_block = payload.get("files")
        if not isinstance(files_block, dict):
            logging.warning("Coverage file %s missing 'files' mapping", candidate)
            continue
        for entry_path, data in files_block.items():
            if isinstance(entry_path, str) and isinstance(data, dict):
                index.register(paths.repo_root, entry_path, data)
        try:
            loaded_sources.append(candidate.relative_to(paths.repo_root).as_posix())
        except ValueError:
            loaded_sources.append(candidate.as_posix())
    if not index:
        return None, loaded_sources
    return index, loaded_sources


def _run_git_command(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    command = ["git", "-C", str(repo_root), *args]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
    except OSError as exc:  # pragma: no cover - git missing
        logging.warning("Failed to execute git command %s: %s", " ".join(command), exc)
        return None
    if result.returncode != 0:
        logging.warning("Git command failed (exit %s): %s", result.returncode, result.stderr.strip())
        return None
    return result


def _collect_git_churn(repo_root: Path, repo_relative_path: Path) -> dict[str, Any] | None:
    if repo_relative_path.parts and repo_relative_path.parts[0] == "..":
        return None
    if repo_relative_path.as_posix() == ".":
        return None
    args = [
        "log",
        "--follow",
        "--numstat",
        "--date=iso",
        "--pretty=%ct\t%H",
        "--",
        repo_relative_path.as_posix(),
    ]
    result = _run_git_command(repo_root, args)
    if result is None:
        return None

    commit_count = 0
    additions = 0
    deletions = 0
    latest_hash: str | None = None
    latest_timestamp: int | None = None
    for line in result.stdout.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) == 2:
            commit_count += 1
            try:
                timestamp = int(parts[0])
            except ValueError:
                continue
            commit_hash = parts[1]
            if latest_timestamp is None or timestamp > latest_timestamp:
                latest_timestamp = timestamp
                latest_hash = commit_hash
            continue
        if len(parts) >= 3:
            add_raw, del_raw = parts[0], parts[1]
            try:
                additions += int(add_raw) if add_raw.isdigit() else 0
            except ValueError:  # pragma: no cover - improbable when isdigit
                pass
            try:
                deletions += int(del_raw) if del_raw.isdigit() else 0
            except ValueError:  # pragma: no cover - improbable when isdigit
                pass

    if commit_count == 0 and additions == 0 and deletions == 0:
        return None

    payload: dict[str, Any] = {
        "commit_count": commit_count,
        "additions": additions,
        "deletions": deletions,
    }
    if latest_hash and latest_timestamp is not None:
        payload["latest_commit"] = {
            "hash": latest_hash,
            "timestamp": datetime.fromtimestamp(latest_timestamp, timezone.utc).isoformat(),
        }
    payload["net_changes"] = additions - deletions
    return payload


def attach_git_churn(paths: Paths, files: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any] | None:
    summary = {
        "files_with_data": 0,
        "total_commits": 0,
        "total_additions": 0,
        "total_deletions": 0,
    }
    latest_overall: tuple[int, str] | None = None
    for entry in files:
        relative_path = entry.get("relative_path")
        if not relative_path:
            continue
        absolute = (paths.target / Path(relative_path)).resolve()
        try:
            repo_relative = absolute.relative_to(paths.repo_root)
        except ValueError:
            warnings.append(f"File {absolute} falls outside repo root; skipping git churn.")
            continue
        churn = _collect_git_churn(paths.repo_root, repo_relative)
        if churn is None:
            continue
        entry["git_churn"] = churn
        summary["files_with_data"] += 1
        summary["total_commits"] += int(churn.get("commit_count", 0))
        summary["total_additions"] += int(churn.get("additions", 0))
        summary["total_deletions"] += int(churn.get("deletions", 0))
        latest_payload = churn.get("latest_commit")
        if latest_payload and "timestamp" in latest_payload:
            try:
                ts = datetime.fromisoformat(latest_payload["timestamp"])
                epoch = int(ts.timestamp())
                if latest_overall is None or epoch > latest_overall[0]:
                    latest_overall = (epoch, latest_payload.get("hash", ""))
            except ValueError:
                continue
    if summary["files_with_data"] == 0:
        return None
    if latest_overall is not None:
        summary["latest_commit"] = {
            "hash": latest_overall[1],
            "timestamp": datetime.fromtimestamp(latest_overall[0], timezone.utc).isoformat(),
        }
    summary["net_changes"] = summary["total_additions"] - summary["total_deletions"]
    return summary


def _is_test_path(relative_parts: tuple[str, ...]) -> bool:
    if not relative_parts:
        return False
    directories = [part.lower() for part in relative_parts[:-1]]
    filename = relative_parts[-1].lower()
    directory_hit = any(
        part in TEST_DIR_HINTS
        or any(part.startswith(prefix) for prefix in TEST_DIR_PREFIXES)
        or any(part.endswith(suffix) for suffix in TEST_DIR_SUFFIXES)
        for part in directories
    )
    file_hit = filename.startswith(TEST_FILE_PREFIXES) or filename.endswith(TEST_FILE_SUFFIXES)
    return directory_hit or file_hit


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
        if _is_test_path(tuple(relative_parts)):
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
        "args": dict(annotations),
    }


def _annotation_quality(node: ast.AST, annotations: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {
            "parameters_total": 0,
            "parameters_annotated": 0,
            "coverage": None,
            "missing": [],
            "return_annotated": False,
        }

    args = node.args
    total = (
        len(args.posonlyargs)
        + len(args.args)
        + len(args.kwonlyargs)
        + int(args.vararg is not None)
        + int(args.kwarg is not None)
    )

    annotated_args = annotations.get("args", {})
    annotated_count = sum(1 for value in annotated_args.values() if value)
    coverage = annotated_count / total if total else None

    return {
        "parameters_total": total,
        "parameters_annotated": annotated_count,
        "coverage": coverage,
        "missing": sorted(name for name, value in annotated_args.items() if not value),
        "return_annotated": bool(annotations.get("return")),
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
    caller_context: dict[str, str],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, bool],
    list[dict[str, Any]],
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
    callback_registrations: list[dict[str, Any]] = []
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
            is_attribute = isinstance(inner.func, ast.Attribute)
            attr_root, attr_path = _attribute_chain(inner.func)
            root_name = attr_root or callee.split("(")[0]
            binding_root = None
            binding_expression = None
            if is_attribute:
                binding_expression = _safe_unparse(inner.func.value)
                binding_root = _attribute_root(inner.func.value)
            call_entry: dict[str, Any] = {
                "callee": callee,
                "lineno": inner.lineno,
                "caller": {
                    "module": caller_context.get("module_id"),
                    "qualified_name": caller_context.get("qualified_name"),
                    "symbol": caller_context.get("symbol"),
                    "lineno": inner.lineno,
                },
                "root": root_name,
                "is_attribute": is_attribute,
            }
            if attr_path and (is_attribute or (root_name and attr_path != root_name)):
                call_entry["attribute"] = attr_path
            if binding_root:
                call_entry["binding"] = binding_root
            if binding_expression and binding_expression != binding_root:
                call_entry["binding_expression"] = binding_expression
            if binding_root in {"self", "cls"}:
                call_entry["is_method_like"] = True
            calls.append(call_entry)
            if root_name in import_alias_map:
                uses_import.append(
                    {
                        "symbol": import_alias_map[root_name],
                        "via": root_name,
                        "lineno": inner.lineno,
                    }
                )
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
            callback_info = _callback_registration_info(inner, import_alias_map)
            if callback_info:
                callback_registrations.append(callback_info)
        if isinstance(inner, BRANCH_NODE_TYPES):
            locals_summary["branches"] += 1
        if isinstance(inner, ast.Global):
            used_globals.update(inner.names)
        if isinstance(inner, ast.Nonlocal):
            used_globals.update(inner.names)
        if isinstance(inner, ast.Name) and isinstance(inner.ctx, ast.Load):
            if inner.id in import_alias_map:
                uses_import.append(
                    {
                        "symbol": import_alias_map[inner.id],
                        "via": inner.id,
                        "lineno": inner.lineno,
                    }
                )
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
    callback_registrations = _dedupe(callback_registrations, ("expression", "target", "target_via", "lineno"))

    return (
        calls,
        uses_import,
        intra_file_refs,
        io_effects,
        logging_calls,
        callback_registrations,
        locals_summary,
        used_globals,
        todo_tags,
    )


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
    docstring_quality = _docstring_quality(node, docstring)
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

    (
        calls,
        uses_import,
        intra_file_refs,
        io_effects,
        logging_calls,
        callback_registrations,
        locals_summary,
        used_globals,
        todo_tags,
    ) = _collect_function_metrics(
        node,
        source,
        import_alias_map,
        defined_local_symbols,
        {
            "module_id": module_id,
            "qualified_name": qualified_name,
            "symbol": display_name,
        },
    )

    code_smells = _function_code_smells(line_count, locals_summary, todo_tags)

    raises = []
    for inner in ast.walk(node):
        if isinstance(inner, ast.Raise) and inner.exc is not None:
            expr = _safe_unparse(inner.exc)
            if expr:
                raises.append({"exception": expr, "lineno": inner.lineno})

    function_hash = hashlib.sha256(source_segment.encode("utf-8")).hexdigest() if source_segment else None

    args_structure = (
        _signature_structure(node.args) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else {}
    )
    annotations = _annotation_map(node)
    annotation_quality = _annotation_quality(node, annotations)
    decorator_nodes = list(getattr(node, "decorator_list", []))
    decorators = [value for value in (_safe_unparse(deco) for deco in decorator_nodes) if value]
    decorators_detailed = [
        _describe_decorator(deco, import_alias_map, module_id, defined_local_symbols) for deco in decorator_nodes
    ]
    cyclomatic_complexity = _cyclomatic_complexity(node)

    result = {
        "name": display_name,
        "qualified_name": qualified_name,
        "line": getattr(node, "lineno", 0),
        "type": "function",
        "is_async": is_async,
        "is_private": name.startswith("_"),
        "docstring": _docstring_summary(docstring),
        "docstring_quality": docstring_quality,
        "signature": signature_line,
        "line_count": line_count,
        "args": args_structure,
        "annotations": annotations,
        "annotation_quality": annotation_quality,
        "decorators": decorators,
        "decorators_detailed": decorators_detailed,
        "raises": raises,
        "returns_kind": _returns_kind(node),
        "locals_summary": locals_summary,
        "callback_registrations": callback_registrations,
        "code_smells": code_smells,
        "used_globals": sorted(used_globals),
        "hash": function_hash,
        "todo_tags": todo_tags,
        "first_stmt_kind": _first_stmt_kind(node),
        "cyclomatic_complexity": cyclomatic_complexity,
        "type_hint_coverage": annotation_quality.get("coverage"),
        "calls": calls,
        "uses_import": uses_import,
        "intra_file_refs": intra_file_refs,
        "io_effects": io_effects,
        "logging_calls": logging_calls,
    }
    if parent_class:
        result["parent_class"] = parent_class
    return result


def _extract_class(
    node: ast.ClassDef,
    source: str,
    module_id: str,
    relative_key: str,
    import_alias_map: dict[str, str],
    defined_local_symbols: set[str],
) -> dict[str, Any]:
    docstring = ast.get_docstring(node)
    docstring_quality = _docstring_quality(node, docstring)
    end_lineno = getattr(node, "end_lineno", None)
    line_count = None
    if end_lineno is not None:
        line_count = max(0, end_lineno - node.lineno + 1)
    bases = [value for value in (_safe_unparse(base) for base in node.bases) if value]
    decorator_nodes = list(node.decorator_list)
    decorators = [value for value in (_safe_unparse(deco) for deco in decorator_nodes) if value]
    decorators_detailed = [
        _describe_decorator(deco, import_alias_map, module_id, defined_local_symbols) for deco in decorator_nodes
    ]
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
    code_smells = _class_code_smells(line_count, len(methods))
    return {
        "name": node.name,
        "line": node.lineno,
        "docstring": _docstring_summary(docstring),
        "docstring_quality": docstring_quality,
        "methods": methods,
        "line_count": line_count,
        "bases": bases,
        "decorators": decorators,
        "decorators_detailed": decorators_detailed,
        "attributes": attributes,
        "code_smells": code_smells,
    }


def _is_abstract_method_entry(method_entry: dict[str, Any]) -> bool:
    decorators = method_entry.get("decorators_detailed", []) or []
    for decorator in decorators:
        expression = (decorator.get("expression") or "").split("(", 1)[0]
        fields = (
            decorator.get("root"),
            decorator.get("path"),
            decorator.get("module"),
            expression,
        )
        if any(field and any(field.endswith(suffix) for suffix in ABSTRACT_DECORATOR_SUFFIXES) for field in fields):
            return True
    return False


def _method_base_name(method_entry: dict[str, Any]) -> str:
    name = method_entry.get("name") or ""
    if not name:
        return ""
    return name.split(".")[-1]


def _build_method_index(classes: list[dict[str, Any]]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for class_entry in classes:
        method_names = {
            _method_base_name(method) for method in class_entry.get("methods", []) if _method_base_name(method)
        }
        index[class_entry.get("name", "")] = method_names
    return index


def _collect_overrides(
    class_entry: dict[str, Any],
    local_bases: list[str],
    method_index: dict[str, set[str]],
) -> list[dict[str, Any]]:
    overrides: list[dict[str, Any]] = []
    for method in class_entry.get("methods", []):
        method_name = _method_base_name(method)
        if not method_name:
            continue
        overriding = [base for base in local_bases if method_name in method_index.get(base, set())]
        if overriding:
            overrides.append(
                {
                    "name": method_name,
                    "qualified_name": method.get("qualified_name"),
                    "lineno": method.get("line"),
                    "overrides": overriding,
                }
            )
    return overrides


def _collect_abstract_methods(class_entry: dict[str, Any]) -> list[dict[str, Any]]:
    abstract_entries: list[dict[str, Any]] = []
    for method in class_entry.get("methods", []):
        if not _is_abstract_method_entry(method):
            continue
        method_name = _method_base_name(method)
        abstract_entries.append(
            {
                "name": method_name,
                "qualified_name": method.get("qualified_name"),
                "lineno": method.get("line"),
            }
        )
    return abstract_entries


def _normalize_base_names(base_exprs: list[str]) -> list[str]:
    names = [base for base in (_simplify_base_expression(expr) for expr in base_exprs) if base]
    return list(dict.fromkeys(names))


def _is_abstract_class(abstract_methods: list[dict[str, Any]], base_names: list[str]) -> bool:
    if abstract_methods:
        return True
    return any(base in ABSTRACT_BASE_HINTS for base in base_names)


def _dependency_category(target: str, package_root: str | None) -> str:
    if not target:
        return "unknown"
    if target.startswith("."):
        return "internal"
    normalized = target.split(".")[0]
    if normalized in PROJECT_NAMESPACE_HINTS:
        return "internal"
    if package_root and (normalized == package_root or target.startswith(f"{package_root}.")):
        return "internal"
    if normalized in STDLIB_MODULE_NAMES:
        return "standard_library"
    return "third_party"


def _resolve_import_target(kind: str, module: str | None, name: str) -> str:
    if kind == "import":
        return name
    module = module or ""
    return f"{module}.{name}" if module else name


def _collect_function_import_usage(
    functions: list[dict[str, Any]],
    classes: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    usage: dict[str, dict[str, Any]] = {}

    def _iter_entries() -> Iterable[dict[str, Any]]:
        yield from functions
        for cls in classes:
            yield from cls.get("methods", [])

    for func in _iter_entries():
        qualified = func.get("qualified_name") or func.get("name")
        for entry in func.get("uses_import", []):
            symbol = entry.get("symbol")
            if not symbol:
                continue
            info = usage.setdefault(symbol, {"functions": set(), "aliases": set()})
            if qualified:
                info["functions"].add(qualified)
            via = entry.get("via")
            if via:
                info["aliases"].add(via)
    normalized: dict[str, dict[str, Any]] = {}
    for symbol, info in usage.items():
        normalized[symbol] = {
            "functions": sorted(info["functions"]),
            "aliases": sorted(info["aliases"]),
        }
    return normalized


def _collect_unused_imports(import_graph: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unused: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for item in import_graph:
        kind = item.get("kind")
        module = item.get("module")
        lineno = item.get("lineno")
        for edge in item.get("edges", []) or []:
            if not edge.get("unused"):
                continue
            key = (
                kind,
                module,
                lineno,
                edge.get("target"),
                edge.get("imported_as"),
            )
            if key in seen:
                continue
            seen.add(key)
            unused.append(
                {
                    "target": edge.get("target"),
                    "imported_as": edge.get("imported_as"),
                    "kind": kind,
                    "module": module,
                    "lineno": lineno,
                }
            )
    return unused


def _build_call_graph(
    module_id: str,
    functions: list[dict[str, Any]],
    classes: list[dict[str, Any]],
    import_alias_map: dict[str, str],
) -> dict[str, Any]:
    package_root = module_id.split(".", 1)[0] if module_id else None
    module_basename = module_id.split(".")[-1] if module_id else None
    local_symbols: dict[str, str] = {}
    local_nodes: set[str] = set()
    class_methods: dict[str | None, dict[str, str]] = {}

    def _record_local(entry: dict[str, Any]) -> None:
        qualified = entry.get("qualified_name")
        name = entry.get("name")
        if qualified:
            local_nodes.add(qualified)
        if qualified and name:
            local_symbols[name] = qualified

    for function_entry in functions:
        _record_local(function_entry)

    for class_entry in classes:
        class_name = class_entry.get("name")
        method_lookup = class_methods.setdefault(class_name, {})
        for method_entry in class_entry.get("methods", []) or []:
            _record_local(method_entry)
            qualified = method_entry.get("qualified_name")
            display_name = method_entry.get("name")
            if not display_name:
                continue
            simple_name = display_name.split(".", 1)[-1]
            if qualified:
                method_lookup[simple_name] = qualified
            # ensure class-qualified lookup is available for expressions like Class.method
            if qualified and display_name not in local_symbols:
                local_symbols[display_name] = qualified

    edges: list[dict[str, Any]] = []
    summary_counter: Counter[str] = Counter()
    per_function: dict[str, Counter[str]] = {}

    def _iter_entries() -> Iterable[dict[str, Any]]:
        yield from functions
        for class_entry in classes:
            yield from class_entry.get("methods", []) or []

    for entry in _iter_entries():
        source = entry.get("qualified_name")
        if not source:
            continue
        for call in entry.get("calls", []) or []:
            resolution = _resolve_call_target(
                call,
                entry,
                module_id,
                module_basename,
                class_methods,
                local_symbols,
                import_alias_map,
                package_root,
            )
            target = resolution.pop("target", None)
            if target:
                local_nodes.add(target)
            edge: dict[str, Any] = {
                "source": source,
                "lineno": call.get("lineno"),
                "expression": call.get("callee"),
            }
            if call.get("attribute"):
                edge["attribute"] = call.get("attribute")
            if call.get("root"):
                edge["root"] = call.get("root")
            if call.get("binding"):
                edge["binding"] = call.get("binding")
            if call.get("binding_expression"):
                edge["binding_expression"] = call.get("binding_expression")
            if call.get("is_method_like"):
                edge["is_method_like"] = True
            if target:
                edge["target"] = target
            filtered_resolution = {k: v for k, v in resolution.items() if v is not None}
            if filtered_resolution:
                edge["resolution"] = filtered_resolution
            edges.append(edge)
            kind = filtered_resolution.get("kind", "unknown")
            summary_counter[kind] += 1
            per_function.setdefault(source, Counter())[kind] += 1

    edges.sort(key=lambda item: (item.get("source") or "", item.get("lineno") or 0, item.get("expression") or ""))

    by_function: dict[str, Any] = {}
    for source, counter in sorted(per_function.items()):
        by_function[source] = {
            "total": sum(counter.values()),
            "by_kind": dict(sorted(counter.items())),
        }

    external_modules = sorted(
        {
            resolution.get("module")
            for resolution in (edge.get("resolution") for edge in edges)
            if resolution and resolution.get("kind") == "imported" and resolution.get("module")
        }
    )

    call_graph: dict[str, Any] = {
        "edges": edges,
        "summary": {
            "total_edges": len(edges),
            "by_kind": dict(sorted(summary_counter.items())),
        },
    }
    if by_function:
        call_graph["by_function"] = by_function
    if local_nodes:
        call_graph["locals"] = sorted(local_nodes)
    if external_modules:
        call_graph["external_modules"] = external_modules
    return call_graph


def _identify_unreachable_functions(
    functions: list[dict[str, Any]],
    classes: list[dict[str, Any]],
    call_graph: dict[str, Any],
) -> list[dict[str, Any]]:
    defined_entries: dict[str, dict[str, Any]] = {}
    for entry in functions:
        qualified = entry.get("qualified_name")
        if qualified:
            defined_entries[qualified] = entry
    for class_entry in classes:
        for method in class_entry.get("methods", []) or []:
            qualified = method.get("qualified_name")
            if qualified:
                defined_entries[qualified] = method

    inbound: dict[str, int] = {name: 0 for name in defined_entries}
    for edge in call_graph.get("edges", []) or []:
        target = edge.get("target")
        if target in inbound:
            inbound[target] += 1

    unreachable: list[dict[str, Any]] = []
    for qualified, entry in defined_entries.items():
        if inbound.get(qualified, 0) > 0:
            continue
        kind = "method" if entry.get("parent_class") else (entry.get("type") or "function")
        unreachable.append(
            {
                "qualified_name": qualified,
                "name": entry.get("name"),
                "parent_class": entry.get("parent_class"),
                "kind": kind,
                "lineno": entry.get("line"),
            }
        )
    return unreachable


def _resolve_call_target(
    call: dict[str, Any],
    caller_entry: dict[str, Any],
    module_id: str,
    module_basename: str | None,
    class_methods: dict[str | None, dict[str, str]],
    local_symbols: dict[str, str],
    import_alias_map: dict[str, str],
    package_root: str | None,
) -> dict[str, Any]:
    resolution: dict[str, Any] = {
        "kind": "unknown",
        "module": None,
        "confidence": "low",
    }
    expression = call.get("callee") if isinstance(call.get("callee"), str) else None
    root = call.get("root") if isinstance(call.get("root"), str) else None
    if not root and expression:
        root = expression.split(".", 1)[0]
    attribute = call.get("attribute") if isinstance(call.get("attribute"), str) else None
    is_attribute = bool(call.get("is_attribute"))
    binding_root = call.get("binding") if isinstance(call.get("binding"), str) else None
    binding_expression = call.get("binding_expression") if isinstance(call.get("binding_expression"), str) else None
    attr_tail_parts: list[str] = []
    if is_attribute and attribute:
        parts = [part for part in attribute.split(".") if part]
        if parts:
            if root and parts[0] == root:
                attr_tail_parts = parts[1:]
            else:
                attr_tail_parts = parts
    caller_name = caller_entry.get("name") or ""
    caller_class = caller_entry.get("parent_class")
    if not caller_class and caller_name and "." in caller_name:
        caller_class = caller_name.split(".", 1)[0]

    def _finalize(
        target: str | None,
        kind: str,
        module: str | None,
        confidence: str = "high",
        detail: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolution.update(
            {
                "target": target,
                "kind": kind,
                "module": module,
                "confidence": confidence,
            }
        )
        if detail:
            resolution["detail"] = detail
        if extra:
            resolution.update(extra)
        return resolution

    if expression and expression in local_symbols:
        target = local_symbols[expression]
        return _finalize(target, "local_method" if "." in expression else "local_function", module_id)

    if root and not is_attribute and root in local_symbols:
        return _finalize(local_symbols[root], "local_function", module_id)

    if caller_class and (binding_root in {"self", "cls"} or call.get("is_method_like")) and attr_tail_parts:
        method_candidate = attr_tail_parts[0]
        target = class_methods.get(caller_class, {}).get(method_candidate)
        if target:
            detail: dict[str, Any] | None = None
            if len(attr_tail_parts) > 1:
                detail = {"attribute_tail": ".".join(attr_tail_parts[1:])}
            return _finalize(target, "local_method", module_id, "medium" if detail else "high", detail)

    if root and root in class_methods and attr_tail_parts:
        method_candidate = attr_tail_parts[0]
        target = class_methods[root].get(method_candidate)
        if target:
            detail = None
            if len(attr_tail_parts) > 1:
                detail = {"attribute_tail": ".".join(attr_tail_parts[1:])}
            return _finalize(target, "local_method", module_id, "medium" if detail else "high", detail)

    if module_basename and root == module_basename and attr_tail_parts:
        candidate = attr_tail_parts[0]
        if candidate in local_symbols:
            detail = None
            if len(attr_tail_parts) > 1:
                detail = {"attribute_tail": ".".join(attr_tail_parts[1:])}
            return _finalize(
                local_symbols[candidate],
                "local_function",
                module_id,
                "medium" if detail else "high",
                detail,
                {"via_module": module_basename},
            )
        if candidate in class_methods and len(attr_tail_parts) > 1:
            method_candidate = attr_tail_parts[1]
            target = class_methods[candidate].get(method_candidate)
            if target:
                detail = None
                if len(attr_tail_parts) > 2:
                    detail = {"attribute_tail": ".".join(attr_tail_parts[2:])}
                return _finalize(
                    target,
                    "local_method",
                    module_id,
                    "medium" if detail else "high",
                    detail,
                    {"via_module": module_basename},
                )

    if root and root in import_alias_map:
        resolved_module = import_alias_map[root]
        tail = ".".join(attr_tail_parts) if attr_tail_parts else ""
        resolved_symbol = f"{resolved_module}.{tail}" if tail else resolved_module
        module_head = resolved_module.split(".", 1)[0] if resolved_module else resolved_module
        detail = {"alias": root}
        if tail:
            detail["attribute_tail"] = tail
        return _finalize(
            resolved_symbol,
            "imported",
            module_head,
            "high",
            detail,
            {
                "module_path": resolved_module,
                "category": _dependency_category(resolved_module, package_root),
            },
        )

    if root and not is_attribute and root in BUILTIN_FUNCTION_NAMES:
        return _finalize(f"builtins.{root}", "builtin", "builtins")

    detail: dict[str, Any] = {}
    if binding_expression and binding_expression != binding_root:
        detail["binding_expression"] = binding_expression
    if attr_tail_parts:
        detail.setdefault("attribute_tail", ".".join(attr_tail_parts))
    if binding_root:
        detail.setdefault("binding", binding_root)
    if detail:
        resolution["detail"] = detail
    return resolution


def _collect_callback_registrations(
    functions: list[dict[str, Any]], classes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    def _append(source_entry: dict[str, Any]) -> None:
        qualified = source_entry.get("qualified_name") or source_entry.get("name")
        for item in source_entry.get("callback_registrations", []) or []:
            payload = dict(item)
            payload["function"] = qualified
            entries.append(payload)

    for func in functions:
        _append(func)
    for class_entry in classes:
        for method in class_entry.get("methods", []) or []:
            _append(method)

    return entries


def _summarize_code_smells(functions: list[dict[str, Any]], classes: list[dict[str, Any]]) -> dict[str, Any]:
    function_counter: Counter[str] = Counter()
    class_counter: Counter[str] = Counter()

    def _ingest(entry: dict[str, Any], sink: Counter[str]) -> None:
        for key, flagged in (entry.get("code_smells") or {}).items():
            if flagged:
                sink[key] += 1

    for func in functions:
        _ingest(func, function_counter)
    for class_entry in classes:
        _ingest(class_entry, class_counter)
        for method in class_entry.get("methods", []) or []:
            _ingest(method, function_counter)

    return {
        "functions": {key: function_counter[key] for key in sorted(function_counter)},
        "classes": {key: class_counter[key] for key in sorted(class_counter)},
    }


def _register_import(imports_flat: set[str], detail: dict[str, Any], alias_entry: dict[str, Any]) -> None:
    name = alias_entry["name"]
    exposed = alias_entry.get("asname") or name
    if detail["kind"] == "import":
        imports_flat.add(name)
        if exposed != name:
            imports_flat.add(exposed)
        return
    module_name = detail.get("module") or ""
    qualified = f"{module_name}.{name}" if module_name else name
    imports_flat.add(qualified)
    imports_flat.add(exposed)


def _collect_test_coverage_signals(imports_flat: set[str], module_id: str) -> dict[str, Any]:
    module_name = module_id.split(".")[-1] if module_id else ""
    prefixes = ["tests", "test", "pytest"]
    module_candidates = []
    if module_name:
        module_candidates.extend(
            [
                module_name,
                f"test_{module_name}",
                f"{module_name}_tests",
            ]
        )
        prefixes.extend(
            [
                f"tests.{module_name}",
                f"tests.test_{module_name}",
                f"tests.{module_name}_tests",
            ]
        )
    matching = sorted(
        {
            imp
            for imp in imports_flat
            if any(imp.startswith(prefix) for prefix in prefixes)
            or any(candidate in imp for candidate in module_candidates)
        }
    )
    return {
        "imports": matching,
        "has_matches": bool(matching),
    }


def _build_import_graph(
    imports_detailed: list[dict[str, Any]],
    usage_map: dict[str, dict[str, Any]],
    module_id: str,
) -> list[dict[str, Any]]:
    package_root = module_id.split(".", 1)[0] if module_id else None
    graph: list[dict[str, Any]] = []
    for detail in imports_detailed:
        edges: list[dict[str, Any]] = []
        for alias_entry in detail.get("names", []):
            target = _resolve_import_target(detail["kind"], detail.get("module"), alias_entry["name"])
            usage = usage_map.get(target)
            functions = usage["functions"] if usage else []
            aliases = usage["aliases"] if usage else []
            category = _dependency_category(target, package_root)
            edges.append(
                {
                    "target": target,
                    "imported_as": alias_entry.get("asname") or alias_entry["name"],
                    "functions": functions,
                    "via": aliases,
                    "unused": not functions,
                    "category": category,
                }
            )
        graph.append(
            {
                "kind": detail["kind"],
                "module": detail.get("module"),
                "lineno": detail.get("lineno"),
                "edges": edges,
            }
        )
    return graph


def _augment_class_relationships(classes: list[dict[str, Any]]) -> None:
    method_index = _build_method_index(classes)
    for class_entry in classes:
        base_exprs = class_entry.get("bases", []) or []
        simplified_bases = _normalize_base_names(base_exprs)
        local_bases = [base for base in simplified_bases if base in method_index]

        overrides = _collect_overrides(class_entry, local_bases, method_index)
        abstract_methods = _collect_abstract_methods(class_entry)
        class_entry["relationships"] = {
            "inherits_from": simplified_bases,
            "local_bases": local_bases,
            "overrides": overrides,
            "abstract_methods": abstract_methods,
            "is_abstract": _is_abstract_class(abstract_methods, simplified_bases),
        }


def _summarize_dependency_categories(graph: list[dict[str, Any]]) -> dict[str, Any]:
    modules_by_category: dict[str, set[str]] = {}
    for item in graph:
        for edge in item.get("edges", []):
            category = edge.get("category", "unknown")
            target = edge.get("target")
            if not target:
                continue
            modules_by_category.setdefault(category, set()).add(target)
    summary: dict[str, Any] = {}
    for bucket in DEPENDENCY_SUMMARY_BUCKETS:
        modules = sorted(modules_by_category.get(bucket, set()))
        summary[bucket] = {
            "count": len(modules),
            "modules": modules,
        }
    for category, modules in modules_by_category.items():
        if category in DEPENDENCY_SUMMARY_BUCKETS:
            continue
        summary[category] = {
            "count": len(modules),
            "modules": sorted(modules),
        }
    return summary


def analyze_python_file(
    path: Path,
    slice_root: Path,
    warnings: list[str],
    coverage: CoverageIndex | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any] | None:
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
        for item in detail["names"]:
            _register_import(imports_flat, detail, item)

    globals_block: list[dict[str, Any]] = []
    has_main_guard = False
    cli_parser = False
    defined_symbols: set[str] = set()
    exports_info = _extract_dunder_all(tree)
    dynamic_code = _detect_dynamic_code(tree)

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
                and any(isinstance(comp, ast.Constant) and comp.value == "__main__" for comp in test.comparators)
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

    _augment_class_relationships(classes)
    import_usage = _collect_function_import_usage(functions, classes)
    import_graph = _build_import_graph(imports_detailed, import_usage, module_id)
    dependency_summary = _summarize_dependency_categories(import_graph)
    module_callbacks = _collect_callback_registrations(functions, classes)
    code_smell_summary = _summarize_code_smells(functions, classes)
    coverage_signals = _collect_test_coverage_signals(imports_flat, module_id)
    call_graph = _build_call_graph(module_id, functions, classes, import_alias_map)
    unused_imports = _collect_unused_imports(import_graph)
    unreachable_functions = _identify_unreachable_functions(functions, classes, call_graph)

    defined_export_candidates: set[str] = set()
    defined_export_candidates.update(func["name"] for func in functions)
    for class_entry in classes:
        defined_export_candidates.add(class_entry["name"])
        for method_entry in class_entry.get("methods", []):
            defined_export_candidates.add(method_entry["name"].split(".")[-1])
    defined_export_candidates.update(glob["name"] for glob in globals_block)

    if exports_info["symbols"] and not exports_info["dynamic"]:
        exports_info["missing"] = [
            symbol for symbol in exports_info["symbols"] if symbol not in defined_export_candidates
        ]
    else:
        exports_info["missing"] = []

    result = {
        "path": str(path),
        "relative_path": relative.as_posix(),
        "module_id": module_id,
        "module_doc": _docstring_summary(ast.get_docstring(tree)),
        "line_count": line_count,
        "functions": functions,
        "classes": classes,
        "imports": sorted(imports_flat),
        "imports_detailed": imports_detailed,
        "import_graph": import_graph,
        "dependency_summary": dependency_summary,
        "call_graph": call_graph,
        "callback_registrations": module_callbacks,
        "code_smell_summary": code_smell_summary,
        "coverage_signals": coverage_signals,
        "globals": globals_block,
        "exports": exports_info,
        "entrypoints": {"has_main_guard": has_main_guard, "cli_parser": cli_parser},
        "dynamic_code": dynamic_code,
        "module_first_line": first_statement,
        "unused_imports": unused_imports,
        "unreachable_functions": unreachable_functions,
    }

    if coverage is not None:
        repo_base = repo_root or slice_root
        relative_repo: Path | None = None
        try:
            relative_repo = path.relative_to(repo_base)
        except ValueError:
            relative_repo = None
        info = coverage.get(path, relative_repo)
        if info is not None:
            executed_lines = sorted(info.executed)
            missing_lines = sorted(info.missing)
            executed_count = len(executed_lines)
            missing_count = len(missing_lines)
            tracked_count = executed_count + missing_count
            coverage_payload: dict[str, Any] = {
                "executed_lines": executed_lines,
                "missing_lines": missing_lines,
                "executed_count": executed_count,
                "missing_count": missing_count,
                "tracked_count": tracked_count,
            }
            if tracked_count:
                coverage_payload["line_rate"] = round(executed_count / tracked_count, 4)
            if info.contexts:
                coverage_payload["contexts"] = {name: sorted(lines) for name, lines in sorted(info.contexts.items())}
                coverage_payload["contexts_count"] = {
                    name: len(lines) for name, lines in coverage_payload["contexts"].items()
                }
            result["coverage"] = coverage_payload

    return result


def compose_inventory(
    paths: Paths,
    options: Options,
    files: list[dict[str, Any]],
    warnings: list[str],
    coverage_sources: list[str] | None = None,
    git_churn_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    if coverage_sources:
        metadata["coverage_sources"] = coverage_sources

    statistics = {
        "total_lines_of_code": total_lines,
        "files_by_type": dict(stats_counter),
        "private_functions": private_count,
        "public_functions": public_count,
        "async_functions": async_count,
    }

    coverage_files = 0
    coverage_executed = 0
    coverage_missing = 0
    for entry in files:
        coverage_block = entry.get("coverage")
        if not coverage_block:
            continue
        coverage_files += 1
        coverage_executed += int(coverage_block.get("executed_count", 0))
        coverage_missing += int(coverage_block.get("missing_count", 0))
    if coverage_sources or coverage_files:
        tracked = coverage_executed + coverage_missing
        coverage_summary: dict[str, Any] = {
            "sources": len(coverage_sources or []),
            "files_with_data": coverage_files,
            "executed_lines": coverage_executed,
            "missing_lines": coverage_missing,
            "tracked_lines": tracked,
        }
        if tracked:
            coverage_summary["line_rate"] = round(coverage_executed / tracked, 4)
        statistics["coverage"] = coverage_summary

    if git_churn_summary:
        statistics["git_churn"] = git_churn_summary

    payload = {
        "schema_version": options.schema_version,
        "metadata": metadata,
        "files": files,
        "statistics": statistics,
    }
    if warnings:
        payload["warnings"] = warnings
    return payload


def _entry_module_key(entry: dict[str, Any]) -> str:
    module_key = entry.get("module_id") or ""
    if module_key:
        return module_key
    relative = entry.get("relative_path") or ""
    if not relative:
        return ""
    return relative.replace("/", ".")


def _resolve_relative_import(module_id: str, module: str, level: int) -> str:
    if level <= 0:
        return module
    module_parts = [part for part in (module_id or "").split(".") if part]
    if level >= len(module_parts):
        base_parts: list[str] = []
    else:
        base_parts = module_parts[:-level]
    if module:
        base_parts.append(module)
    return ".".join(base_parts)


def _build_alias_resolution_map(
    imports_detailed: list[dict[str, Any]],
    module_id: str,
) -> dict[str, dict[str, Any]]:
    resolution: dict[str, dict[str, Any]] = {}
    for detail in imports_detailed:
        kind = detail.get("kind")
        module = detail.get("module") or ""
        level = int(detail.get("level", 0) or 0)
        for alias in detail.get("names", []) or []:
            alias_name = alias.get("name")
            if not alias_name or alias_name == "*":
                continue
            exposed = alias.get("asname") or alias_name
            if kind == "import":
                target_module = alias_name
                resolved_target = alias_name
            else:
                base_module = _resolve_relative_import(module_id, module, level)
                target_module = base_module if base_module else module
                if target_module:
                    resolved_target = f"{target_module}.{alias_name}"
                else:
                    resolved_target = alias_name
            resolution[exposed] = {
                "target": resolved_target,
                "module": target_module,
                "kind": kind,
            }
    return resolution


def _resolve_callee_path(
    callee: str,
    resolution_map: dict[str, dict[str, Any]],
) -> tuple[str | None, dict[str, Any] | None]:
    if not callee:
        return None, None
    best_alias: str | None = None
    for alias in resolution_map:
        if callee == alias or callee.startswith(f"{alias}."):
            if best_alias is None or len(alias) > len(best_alias):
                best_alias = alias
    if best_alias is None:
        return None, None
    info = resolution_map[best_alias]
    remainder = callee[len(best_alias) :]
    if remainder.startswith("."):
        remainder = remainder[1:]
    if remainder:
        resolved = f"{info['target']}.{remainder}" if info.get("target") else remainder
    else:
        resolved = info.get("target")
    return resolved, info


def _match_known_module(candidate: str | None, known_modules: set[str]) -> str | None:
    if not candidate:
        return None
    parts = [part for part in candidate.split(".") if part]
    for end in range(len(parts), 0, -1):
        attempt = ".".join(parts[:end])
        if attempt in known_modules:
            return attempt
    return None


def _iter_function_entries(files: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for entry in files:
        for function_entry in entry.get("functions", []) or []:
            yield function_entry
        for class_entry in entry.get("classes", []) or []:
            for method_entry in class_entry.get("methods", []) or []:
                yield method_entry


def _score_severity(score: float | None, warning_threshold: float, failure_threshold: float) -> str:
    if score is None:
        return "unknown"
    if score >= warning_threshold:
        return "ok"
    if score >= failure_threshold:
        return "warning"
    return "critical"


def _build_docstring_score_pack(files: list[dict[str, Any]]) -> dict[str, Any] | None:
    total_functions = 0
    documented_functions = 0
    params_sections = 0
    returns_sections = 0
    missing_param_mentions = 0

    for entry in _iter_function_entries(files):
        total_functions += 1
        quality = entry.get("docstring_quality") or {}
        if quality.get("exists"):
            documented_functions += 1
            if quality.get("has_parameters_section"):
                params_sections += 1
            if quality.get("has_returns_section"):
                returns_sections += 1
        missing_param_mentions += len(quality.get("missing_params") or [])

    if total_functions == 0:
        score = None
    else:
        score = documented_functions / total_functions * 100.0

    severity = _score_severity(score, DOCSTRING_WARNING_THRESHOLD, DOCSTRING_FAILURE_THRESHOLD)
    metrics = {
        "functions_total": total_functions,
        "functions_documented": documented_functions,
        "functions_missing": max(total_functions - documented_functions, 0),
        "docstrings_with_parameters_section": params_sections,
        "docstrings_with_returns_section": returns_sections,
        "missing_parameter_mentions": missing_param_mentions,
    }

    pack: dict[str, Any] = {
        "id": "docstring_coverage",
        "label": "Docstring Coverage",
        "description": "Percentage of functions and methods that include a docstring.",
        "unit": "percent",
        "severity": severity,
        "thresholds": {
            "warning": DOCSTRING_WARNING_THRESHOLD,
            "failure": DOCSTRING_FAILURE_THRESHOLD,
        },
        "metrics": metrics,
    }
    if score is not None:
        pack["score"] = round(score, 2)
        pack["coverage_ratio"] = documented_functions / total_functions if total_functions else 0.0
    else:
        pack["score"] = None
        pack["coverage_ratio"] = None
    return pack


def _build_screening_score_snapshot(payload: dict[str, Any]) -> dict[str, Any] | None:
    files = payload.get("files", [])
    packs: list[dict[str, Any]] = []
    docstring_pack = _build_docstring_score_pack(files)
    if docstring_pack:
        packs.append(docstring_pack)

    if not packs:
        return None

    timestamp = datetime.now(timezone.utc).isoformat()
    metadata = payload.get("metadata", {})
    context: dict[str, Any] = {}
    folder_name = metadata.get("folder_name")
    if folder_name:
        context["folder_name"] = folder_name
    generated_at = metadata.get("generated_at")
    if generated_at:
        context["inventory_generated_at"] = generated_at
    schema_version = metadata.get("schema_version")
    if schema_version is not None:
        context["inventory_schema_version"] = schema_version

    snapshot: dict[str, Any] = {
        "timestamp": timestamp,
        "packs": packs,
    }
    if context:
        snapshot["context"] = context
    snapshot["summary"] = {"total_packs": len(packs)}
    return snapshot


def _collect_screening_history(directories: Sequence[Path], source_name: str) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    seen_timestamps: set[str] = set()
    for directory in directories:
        if not directory.exists():
            continue
        existing_files = sorted(directory.glob(f"{source_name}_commandview_screening_*.json"))
        if not existing_files:
            continue
        latest_file = existing_files[-1]
        try:
            payload = json.loads(latest_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("Failed to load prior screening summary %s: %s", latest_file, exc)
            continue
        for entry in payload.get("score_history", []) or []:
            timestamp = entry.get("timestamp")
            if timestamp and timestamp not in seen_timestamps:
                history.append(entry)
                seen_timestamps.add(timestamp)
        snapshot = payload.get("score_snapshot")
        if snapshot:
            timestamp = snapshot.get("timestamp")
            if timestamp and timestamp not in seen_timestamps:
                history.append(snapshot)
                seen_timestamps.add(timestamp)
    history.sort(
        key=lambda entry: (
            entry.get("timestamp") or "",
            (entry.get("context") or {}).get("inventory_generated_at") or "",
        )
    )
    if len(history) > MAX_SCREENING_HISTORY_ENTRIES:
        history = history[-MAX_SCREENING_HISTORY_ENTRIES:]
    return history


def _apply_score_history(summary: dict[str, Any], history_seed: Sequence[dict[str, Any]]) -> dict[str, Any]:
    snapshot = summary.get("score_snapshot")
    merged = list(history_seed)
    if snapshot:
        merged.append(snapshot)
    merged.sort(
        key=lambda entry: (
            entry.get("timestamp") or "",
            (entry.get("context") or {}).get("inventory_generated_at") or "",
        )
    )
    if len(merged) > MAX_SCREENING_HISTORY_ENTRIES:
        merged = merged[-MAX_SCREENING_HISTORY_ENTRIES:]
    summary["score_history"] = merged
    if merged:
        summary["score_latest"] = merged[-1]
    return summary


def build_screening_summary(payload: dict[str, Any]) -> dict[str, Any]:
    files = payload.get("files", [])
    import_edges: set[tuple[str, str]] = set()
    call_edges: set[tuple[str, str]] = set()
    cross_module_edges: dict[tuple[str, str], dict[str, Any]] = {}
    nodes_meta: dict[str, dict[str, Any]] = {}
    known_modules: set[str] = {_entry_module_key(entry) for entry in files if _entry_module_key(entry)}

    for entry in files:
        module_key = _entry_module_key(entry)
        resolution_map = _build_alias_resolution_map(entry.get("imports_detailed", []), module_key)
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

        current_alias_map = resolution_map

        def _capture_function(
            function_entry: dict[str, Any],
            module_alias: str = module_key,
            alias_map: dict[str, Any] | None = None,
        ) -> None:
            resolution_lookup = alias_map or {}
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
                    resolved, info = _resolve_callee_path(callee, resolution_lookup)
                    target_module = _match_known_module(resolved, known_modules)
                    if not target_module and info and info.get("module") in known_modules:
                        target_module = info.get("module")
                    if resolved and target_module and module_alias and target_module != module_alias:
                        key = (module_alias, target_module)
                        edge = cross_module_edges.setdefault(
                            key,
                            {
                                "callers": set(),
                                "targets": set(),
                                "call_sites": set(),
                                "count": 0,
                            },
                        )
                        caller_name = call.get("caller", {}).get("qualified_name") or source
                        edge["callers"].add(caller_name)
                        edge["targets"].add(resolved)
                        lineno = call.get("lineno")
                        edge["call_sites"].add((caller_name, resolved, lineno))
                        edge["count"] += 1
            for ref in function_entry.get("intra_file_refs", []):
                callee = ref.get("callee_func")
                if callee:
                    target = f"{module_alias}::{callee}"
                    call_edges.add((source, target))

        for function_entry in entry.get("functions", []):
            _capture_function(function_entry, alias_map=current_alias_map)
        for class_entry in entry.get("classes", []):
            for method_entry in class_entry.get("methods", []):
                _capture_function(method_entry, alias_map=current_alias_map)

    imports_list = [list(edge) for edge in sorted(import_edges)]
    calls_list = [list(edge) for edge in sorted(call_edges)]
    cross_module_list: list[dict[str, Any]] = []
    for (source_module, target_module), data in sorted(cross_module_edges.items()):
        cross_module_list.append(
            {
                "source": source_module,
                "target": target_module,
                "call_count": data["count"],
                "callers": sorted(data["callers"]),
                "targets": sorted(data["targets"]),
                "call_sites": [
                    {
                        "caller": caller,
                        "target": target,
                        "lineno": lineno,
                    }
                    for caller, target, lineno in sorted(
                        data["call_sites"], key=lambda item: (item[0], item[1], item[2] or 0)
                    )
                ],
            }
        )

    summary: dict[str, Any] = {
        "graphs": {
            "imports": imports_list,
            "calls": calls_list,
            "cross_module_calls": cross_module_list,
        },
        "violations": {"cycles": False},
        "nodes": {"meta": nodes_meta},
    }
    score_snapshot = _build_screening_score_snapshot(payload)
    if score_snapshot:
        summary["score_snapshot"] = score_snapshot
    return summary


def _write_inventory_copy(directory: Path, source_name: str, payload: dict[str, Any]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    legacy_file = directory / f"{source_name}_index.json"
    if legacy_file.exists():
        legacy_file.unlink()
    for existing in directory.glob(f"{source_name}_index-*.json"):
        if existing.is_file():
            existing.unlink()
    for existing in directory.glob(f"{source_name}_commandview_*.json"):
        if existing.is_file() and "_screening_" not in existing.name:
            existing.unlink()
    date_token = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    output_file = directory / f"{source_name}_commandview_{date_token}.json"
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
    for existing in directory.glob(f"{source_name}_commandview_screening_*.json"):
        if existing.is_file():
            existing.unlink()
    date_token = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    output_file = directory / f"{source_name}_commandview_screening_{date_token}.json"
    temp_file = output_file.with_suffix(".screening.json.tmp")
    temp_file.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    temp_file.replace(output_file)
    return output_file


def write_inventory(paths: Paths, payload: dict[str, Any], summary: dict[str, Any]) -> Path:
    source_name = paths.target.name
    primary_dir = paths.target / f"{source_name}_index"
    reports_slug = _slugify_relative(paths.target_relative)
    secondary_dir = paths.reports_root / f"{reports_slug}_index"
    primary = _write_inventory_copy(primary_dir, source_name, payload)
    _write_inventory_copy(secondary_dir, source_name, payload)
    history_seed = _collect_screening_history((primary_dir, secondary_dir), source_name)
    summary = _apply_score_history(summary, history_seed)
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

    coverage_index, coverage_sources = load_coverage_reports(paths, options.coverage_inputs)

    warnings: list[str] = []
    collected: list[dict[str, Any]] = []
    for file_path in python_files:
        result = analyze_python_file(
            file_path,
            paths.target,
            warnings,
            coverage=coverage_index,
            repo_root=paths.repo_root,
        )
        if result:
            collected.append(result)

    if not collected:
        logging.error("All Python files failed to parse under %s", paths.target)
        return 1

    git_churn_summary = attach_git_churn(paths, collected, warnings)

    payload = compose_inventory(paths, options, collected, warnings, coverage_sources, git_churn_summary)
    summary = build_screening_summary(payload)
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
