#!/usr/bin/env python3
"""
scan_monkey_patches.py — Enumerate monkey patches across a repo and export reports.

Usage (examples):
  - Basic scan from repository root (current dir) and write reports to default path:
      python .repo_studios/scan_monkey_patches.py

  - Specify repo root and include git blame metadata:
      python .repo_studios/scan_monkey_patches.py --repo-root . --with-git

  - Limit scan, customize project packages and exclusions:
      python .repo_studios/scan_monkey_patches.py \
        --repo-root . \
        --project-packages agents api jarvis2 \
        --exclude-dirs .git .venv venv node_modules build dist __pycache__

  - Run built-in self test:
      python .repo_studios/scan_monkey_patches.py --self-test --verbose

    - Strict mode (disable regex fallback; fail on parse errors):
            python .repo_studios/scan_monkey_patches.py --strict --with-git

Outputs (written to timestamped directory under `.repo_studios/reports/producer_reports/monkey_patch_scans/`):
    - report.json  — structured summary payload with counts, metadata, and configuration context
    - report.md    — human-readable summary with tables and recommended follow-up actions
    - log.txt      — key-value diagnostics for CI consumption
    - matches.json — full finding details
    - matches.tsv  — tab-separated export of all findings (only when matches exist)
    - latest/      — copies of the most recent artifacts for easy consumption

Exit codes:
  - 0 on success
  - 2 on self-test assertion failure
  - 1 on internal errors

Detection strategy:
  - First pass via Python AST for precise identification (avoids string/comment false positives).
  - Secondary regex pass to catch some edge patterns; de-duplicates by (file, line, category).
  - Heuristics classify by category and infer intent (best effort).

Limitations:
  - Heuristics may miss highly dynamic or obfuscated patterns.
  - Import-base resolution is best-effort (aliases resolved, but complex from-import chains may be simplified).
  - Regex fallback is intentionally conservative to avoid noise.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import logging
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
import shutil
from typing import Any

# Defaults (workspace-relative)
DEFAULT_OUTPUT_DIR = Path(".repo_studios/reports/producer_reports/monkey_patch_scans")
RUN_PREFIX = "monkey_patch_scan"
DEFAULT_ARTIFACTS_TO_KEEP = 10
SCHEMA_VERSION = 1
DEFAULT_EXCLUDES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    # Repo-specific heavy/noisy vendor trees
    ".founder_files",
    "external",
    "libraries",
    "z_FUTURE_IMPIMENTATIONS",
    "zzz_agent_repos",
}
DEFAULT_EXCLUDE_GLOBS: set[str] = {
    # Glob patterns (relative paths) to exclude entire subtrees
    "external/**",
    "libraries/**",
    ".founder_files/**",
    "**/zzz_agent_repos/**",
    "**/site-packages/**",
    # Repo-specific parse-noise: synthetic torch/vision/audio test harness file
    "scripts/test_torch_vision_audio.py",
    # Exclude third-party-like trees from counts per hygiene policy
    "src/vision/**",
    "src/audio/**",
}
DEFAULT_CONTEXT_LINES = 2
KNOWN_SINGLETON_BASES = {"logging", "warnings"}

CATEGORY_ATTRIBUTE_REASSIGNMENT = "attribute_reassignment_on_import"
CATEGORY_SETATTR = "setattr_on_import_or_class"
CATEGORY_SYS_MODULES = "sys_modules_assignment"
CATEGORY_BUILTINS = "builtins_mutation"
CATEGORY_IMPORT_TIME = "import_time_side_effect"
CATEGORY_TEST_PATCH_MISUSE = "test_patch_misuse"
CATEGORY_GLOBAL_ENV = "global_env_mutation"
CATEGORY_SINGLETON_REBIND = "singleton_rebind"
CATEGORY_OTHER = "other"

INTENT_MODULE_INJECTION = "module injection/aliasing"
INTENT_OVERRIDE_THIRD_PARTY = "override third-party behavior"
INTENT_NON_SCOPED_TEST_PATCH = "non-scoped test patch"
INTENT_GLOBAL_RUNTIME_CHANGE = "global runtime change"
INTENT_IMPORT_TIME_OVERRIDE = "import-time behavior override"
INTENT_UNSPECIFIED = "unspecified monkey patch"


@dataclass(frozen=True)
class Paths:
    repo_root: Path
    scan_root: Path
    output_dir: Path


@dataclass(frozen=True)
class ScanOptions:
    project_packages: set[str]
    exclude_dirs: set[str]
    exclude_globs: set[str]
    context_lines: int
    with_git: bool
    strict: bool
    artifacts_to_keep: int


@dataclass
class Finding:
    file: str
    line: int
    code: str
    category: str
    intent: str
    import_base: str | None
    is_test: bool
    is_module_scope: bool
    function: str | None
    class_name: str | None
    nearby_comment: str | None
    context: str | None
    git_author: str | None = None
    git_commit: str | None = None
    git_commit_date: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ImportResolver(ast.NodeVisitor):
    """Collect import aliases → modules and objects."""

    def __init__(self) -> None:
        self.alias_to_module: dict[str, str] = {}
        self.alias_is_from_object: dict[str, tuple[str, str]] = {}
        self.import_lines: set[int] = set()

    def visit_Import(self, node: ast.Import) -> Any:  # type: ignore[override]
        self.import_lines.add(getattr(node, "lineno", -1))
        for alias in node.names:
            mod = alias.name  # full module path
            asname = alias.asname or mod.split(".")[-1]
            self.alias_to_module[asname] = mod
        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:  # type: ignore[override]
        self.import_lines.add(getattr(node, "lineno", -1))
        module = node.module or ""
        for alias in node.names:
            asname = alias.asname or alias.name
            # map alias to full path module.object
            self.alias_to_module[asname] = f"{module}.{alias.name}" if module else alias.name
            self.alias_is_from_object[asname] = (module, alias.name)
        return self.generic_visit(node)


class ScopeTracker(ast.NodeVisitor):
    """Track current function/class scope while scanning."""

    def __init__(self) -> None:
        self.stack: list[tuple[str, str]] = []  # (type, name)

    def current(self) -> tuple[bool, str | None, str | None]:
        fn = None
        cl = None
        for t, n in reversed(self.stack):
            if t == "function" and fn is None:
                fn = n
            if t == "class" and cl is None:
                cl = n
        return (len(self.stack) == 0, fn, cl)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:  # type: ignore[override]
        self.stack.append(("function", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:  # type: ignore[override]
        self.stack.append(("function", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:  # type: ignore[override]
        self.stack.append(("class", node.name))
        self.generic_visit(node)
        self.stack.pop()


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def get_context(lines: list[str], lineno: int, n: int) -> str:
    i = max(1, lineno - n)
    j = min(len(lines), lineno + n)
    segment = lines[i - 1 : j]
    return "\n".join(f"{k + 1:>5}: {segment[k]}" for k in range(len(segment)))


def get_nearby_comment(lines: list[str], lineno: int, lookback: int = 5) -> str | None:
    start = max(0, lineno - 2 - lookback)
    window = lines[start : max(0, lineno - 1)]
    # collect contiguous trailing comments from the bottom
    collected: list[str] = []
    for line in reversed(window):
        s = line.strip()
        if s.startswith("#"):
            collected.append(s)
        elif s == "":
            # allow blank between comments
            collected.append(s)
        else:
            break
    collected.reverse()
    text = "\n".join(collected).strip()
    return text or None


def is_path_in_tests(repo_root: Path, file_path: Path) -> bool:
    try:
        rel = file_path.relative_to(repo_root)
        parts = rel.parts
        return "tests" in parts
    except Exception:
        return False


def top_level_packages_default(repo_root: Path) -> set[str]:
    pkgs: set[str] = set()
    for p in repo_root.iterdir():
        if not p.is_dir():
            continue
        if p.name.startswith("."):
            continue
        # Heuristic: folder with any .py files under it is a candidate
        try:
            for _ in p.rglob("*.py"):
                pkgs.add(p.name)
                break
        except Exception:
            continue
    # Always treat tests as owned for noise reduction
    pkgs.add("tests")
    return pkgs


def base_module_name(mod: str | None) -> str | None:
    if not mod:
        return None
    return mod.split(".")[0]


def dotted_name_from_attribute(attr: ast.AST) -> str | None:
    parts: list[str] = []
    cur: ast.AST | None = attr
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return ".".join(parts)
    return None


def is_alias_external(
    alias: str, resolver: ImportResolver, project_pkgs: set[str]
) -> tuple[bool, str | None]:
    # Determine the import base for an alias and whether it's external
    mod = resolver.alias_to_module.get(alias)
    if not mod:
        return False, None
    base = base_module_name(mod)
    return (base not in project_pkgs if base else False), base


def classify_intent(category: str, import_base: str | None, is_test: bool) -> str:
    if category == CATEGORY_SYS_MODULES:
        return INTENT_MODULE_INJECTION
    if category == CATEGORY_BUILTINS:
        return INTENT_GLOBAL_RUNTIME_CHANGE
    if category == CATEGORY_IMPORT_TIME:
        return INTENT_IMPORT_TIME_OVERRIDE
    if category == CATEGORY_TEST_PATCH_MISUSE and is_test:
        return INTENT_NON_SCOPED_TEST_PATCH
    if import_base and category in {
        CATEGORY_ATTRIBUTE_REASSIGNMENT,
        CATEGORY_SETATTR,
        CATEGORY_SINGLETON_REBIND,
    }:
        return INTENT_OVERRIDE_THIRD_PARTY
    return INTENT_UNSPECIFIED


def add_git_blame(
    repo_root: Path, file_path: Path, lineno: int
) -> tuple[str | None, str | None, str | None]:
    try:
        rel = file_path.relative_to(repo_root)
    except Exception:
        rel = file_path
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "blame",
                "-L",
                f"{lineno},{lineno}",
                "--line-porcelain",
                str(rel),
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode != 0:
            return None, None, None
        author = commit = date = None
        for line in proc.stdout.splitlines():
            if line.startswith("author "):
                author = line[len("author ") :].strip()
            elif re.match(r"^[0-9a-f]{7,40} ", line):
                commit = line.split()[0]
            elif line.startswith("author-time "):
                ts = int(line[len("author-time ") :].strip())
                # Use timezone-aware UTC datetime to avoid deprecation warnings
                date = dt.datetime.fromtimestamp(ts, tz=dt.UTC).isoformat()
        return author, commit, date
    except Exception:
        return None, None, None


class MonkeyPatchScanner(ast.NodeVisitor):
    def __init__(
        self,
        repo_root: Path,
        file_path: Path,
        lines: list[str],
        resolver: ImportResolver,
        project_pkgs: set[str],
        context_lines: int,
    ) -> None:
        self.repo_root = repo_root
        self.file_path = file_path
        self.lines = lines
        self.resolver = resolver
        self.project_pkgs = project_pkgs
        self.context_lines = context_lines
        self.scope = ScopeTracker()
        self.findings: list[Finding] = []

    # Delegate to ScopeTracker to know scope during traversal
    def generic_visit(self, node: ast.AST) -> Any:  # type: ignore[override]
        # Manually route into scope tracker for nested defs
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Push/pop handled by scope tracker methods; call them directly
            self.scope.visit(node)  # type: ignore[arg-type]
            return
        super().generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:  # type: ignore[override]
        self._handle_assignment(node, getattr(node, "lineno", -1))
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:  # type: ignore[override]
        self._handle_assignment(node, getattr(node, "lineno", -1))
        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:  # type: ignore[override]
        self._handle_assignment(node, getattr(node, "lineno", -1))
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:  # type: ignore[override]
        lineno = getattr(node, "lineno", -1)
        is_module_scope, fn_name, cl_name = self.scope.current()
        # setattr(...)
        if isinstance(node.func, ast.Name) and node.func.id == "setattr" and node.args:
            target = node.args[0]
            base_alias = None
            if isinstance(target, ast.Name):
                base_alias = target.id
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                base_alias = target.value.id
            external, base = (
                is_alias_external(base_alias or "", self.resolver, self.project_pkgs)
                if base_alias
                else (False, None)
            )
            category = CATEGORY_SETATTR
            if external:
                category = CATEGORY_SETATTR
            self._add_finding(
                lineno,
                category,
                base,
                is_module_scope,
                fn_name,
                cl_name,
            )
        # builtins.setattr(...)
        if isinstance(node.func, ast.Attribute):
            dotted = dotted_name_from_attribute(node.func)
            if dotted == "builtins.setattr":
                self._add_finding(
                    lineno,
                    CATEGORY_SETATTR,
                    "builtins",
                    is_module_scope,
                    fn_name,
                    cl_name,
                )
        # patch(...) at module scope not in with/dec — heuristic: any bare call at module level
        if is_module_scope and _is_patch_call(node, self.resolver):
            self._add_finding(
                lineno,
                CATEGORY_TEST_PATCH_MISUSE,
                "unittest",
                is_module_scope,
                fn_name,
                cl_name,
            )
        # os.environ.update(...), setdefault(...)
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Attribute):
            v = node.func.value
            if isinstance(v.value, ast.Name) and v.value.id == "os" and v.attr == "environ":
                if node.func.attr in {"update", "setdefault"}:
                    self._add_finding(
                        lineno,
                        CATEGORY_GLOBAL_ENV,
                        "os",
                        is_module_scope,
                        fn_name,
                        cl_name,
                    )
        return self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> Any:  # type: ignore[override]
        lineno = getattr(node, "lineno", -1)
        for target in node.targets:
            if isinstance(target, ast.Subscript) and _is_sys_modules(target):
                is_module_scope, fn_name, cl_name = self.scope.current()
                self._add_finding(
                    lineno,
                    CATEGORY_SYS_MODULES,
                    "sys",
                    is_module_scope,
                    fn_name,
                    cl_name,
                )
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:  # type: ignore[override]
        # Detect module-level decorator @patch(...)
        if self.scope.current()[0]:
            for dec in node.decorator_list:
                if _is_patch_decorator(dec, self.resolver):
                    lineno = getattr(dec, "lineno", getattr(node, "lineno", -1))
                    self._add_finding(
                        lineno,
                        CATEGORY_TEST_PATCH_MISUSE,
                        "unittest",
                        True,
                        node.name,
                        None,
                    )
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:  # type: ignore[override]
        if self.scope.current()[0]:
            for dec in node.decorator_list:
                if _is_patch_decorator(dec, self.resolver):
                    lineno = getattr(dec, "lineno", getattr(node, "lineno", -1))
                    self._add_finding(
                        lineno,
                        CATEGORY_TEST_PATCH_MISUSE,
                        "unittest",
                        True,
                        None,
                        node.name,
                    )
        return self.generic_visit(node)

    def _handle_assignment(self, node: ast.AST, lineno: int) -> None:
        is_module_scope, fn_name, cl_name = self.scope.current()
        targets: list[ast.AST] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif (isinstance(node, ast.AnnAssign) and node.target is not None) or isinstance(node, ast.AugAssign):
            targets = [node.target]
        for t in targets:
            # sys.modules[...]
            if isinstance(t, ast.Subscript) and _is_sys_modules(t):
                self._add_finding(
                    lineno, CATEGORY_SYS_MODULES, "sys", is_module_scope, fn_name, cl_name
                )
                continue
            # builtins.X = ...
            if (
                isinstance(t, ast.Attribute)
                and isinstance(t.value, ast.Name)
                and t.value.id == "builtins"
            ):
                self._add_finding(
                    lineno, CATEGORY_BUILTINS, "builtins", is_module_scope, fn_name, cl_name
                )
                continue
            # os.environ[...]
            if isinstance(t, ast.Subscript) and _is_os_environ(t):
                self._add_finding(
                    lineno, CATEGORY_GLOBAL_ENV, "os", is_module_scope, fn_name, cl_name
                )
                continue
            # logging.getLogger = ... or warnings.filterwarnings = ...
            if isinstance(t, ast.Attribute):
                dotted = dotted_name_from_attribute(t)
                if dotted:
                    base = dotted.split(".")[0]
                    if base in KNOWN_SINGLETON_BASES and "." in dotted:
                        self._add_finding(
                            lineno,
                            CATEGORY_SINGLETON_REBIND,
                            base,
                            is_module_scope,
                            fn_name,
                            cl_name,
                        )
                        continue
            # pkg.attr = ... where pkg alias imported (supports nested attribute like pkg.sub.x)
            if isinstance(t, ast.Attribute):
                base_alias: str | None = None
                if isinstance(t.value, ast.Name):
                    base_alias = t.value.id
                else:
                    dotted = dotted_name_from_attribute(t)
                    if dotted and "." in dotted:
                        base_alias = dotted.split(".", 1)[0]
                if base_alias:
                    external, base = is_alias_external(base_alias, self.resolver, self.project_pkgs)
                    if base:
                        # Always record attribute reassignment
                        self._add_finding(
                            lineno,
                            CATEGORY_ATTRIBUTE_REASSIGNMENT,
                            base,
                            is_module_scope,
                            fn_name,
                            cl_name,
                        )
                        # If near import at module scope, also record import-time side effect
                        if is_module_scope and _near_import(lineno, self.resolver.import_lines):
                            self._add_finding(
                                lineno,
                                CATEGORY_IMPORT_TIME,
                                base,
                                is_module_scope,
                                fn_name,
                                cl_name,
                            )
                        continue
            # assignment to imported object alias (from X import Y; Y = ...)
            if isinstance(t, ast.Name) and t.id in self.resolver.alias_to_module:
                base = base_module_name(self.resolver.alias_to_module.get(t.id))
                if base:
                    # Rebinding an imported symbol
                    self._add_finding(
                        lineno,
                        CATEGORY_ATTRIBUTE_REASSIGNMENT,
                        base,
                        is_module_scope,
                        fn_name,
                        cl_name,
                    )
                    continue

    def _add_finding(
        self,
        lineno: int,
        category: str,
        import_base: str | None,
        is_module_scope: bool,
        fn_name: str | None,
        cl_name: str | None,
    ) -> None:
        # Build fields
        code_line = self.lines[lineno - 1].rstrip() if 1 <= lineno <= len(self.lines) else ""
        context = get_context(self.lines, lineno, DEFAULT_CONTEXT_LINES)
        comment = get_nearby_comment(self.lines, lineno)
        is_test = is_path_in_tests(self.repo_root, self.file_path)
        intent = classify_intent(category, import_base, is_test)
        self.findings.append(
            Finding(
                file=str(self.file_path.relative_to(self.repo_root))
                if self.file_path.is_relative_to(self.repo_root)
                else str(self.file_path),
                line=lineno,
                code=code_line,
                category=category,
                intent=intent,
                import_base=import_base,
                is_test=is_test,
                is_module_scope=is_module_scope,
                function=fn_name,
                class_name=cl_name,
                nearby_comment=comment,
                context=context,
            )
        )


def _is_sys_modules(sub: ast.Subscript) -> bool:
    # sys.modules[...] pattern
    if isinstance(sub.value, ast.Attribute) and isinstance(sub.value.value, ast.Name):
        return sub.value.value.id == "sys" and sub.value.attr == "modules"
    return False


def _is_os_environ(sub: ast.Subscript) -> bool:
    if isinstance(sub.value, ast.Attribute) and isinstance(sub.value.value, ast.Name):
        return sub.value.value.id == "os" and sub.value.attr == "environ"
    return False


def _near_import(lineno: int, import_lines: set[int], window: int = 5) -> bool:
    return any(abs(lineno - li) <= window for li in import_lines)


def _is_patch_name(name: str, resolver: ImportResolver) -> bool:
    # Check if alias maps to unittest.mock.patch (best-effort)
    mapped = resolver.alias_to_module.get(name)
    if not mapped:
        return name == "patch"  # fallback if directly imported as patch
    return mapped.endswith(".patch") or mapped == "unittest.mock.patch"


def _is_patch_call(node: ast.Call, resolver: ImportResolver) -> bool:
    if isinstance(node.func, ast.Name):
        return _is_patch_name(node.func.id, resolver)
    if isinstance(node.func, ast.Attribute):
        dotted = dotted_name_from_attribute(node.func)
        return dotted is not None and dotted.endswith(".patch")
    return False


def _is_patch_decorator(dec: ast.AST, resolver: ImportResolver) -> bool:
    if isinstance(dec, ast.Call):
        return _is_patch_call(dec, resolver)
    if isinstance(dec, ast.Name):
        return _is_patch_name(dec.id, resolver)
    if isinstance(dec, ast.Attribute):
        dotted = dotted_name_from_attribute(dec)
        return dotted is not None and dotted.endswith(".patch")
    return False


def regex_fallback(lines: list[str]) -> list[tuple[int, str]]:
    """Return (lineno, category) pairs for simple regex patterns not caught by AST.
    Conservative to avoid noise.
    """
    results: list[tuple[int, str]] = []
    patterns = [
        (re.compile(r"sys\.modules\[[^\]]+\]\s*=\s*"), CATEGORY_SYS_MODULES),
        (re.compile(r"\bbuiltins\.[A-Za-z_]\w*\s*=\s*"), CATEGORY_BUILTINS),
        (re.compile(r"\bos\.environ\[[^\]]+\]\s*=\s*"), CATEGORY_GLOBAL_ENV),
        (re.compile(r"\bsetattr\s*\("), CATEGORY_SETATTR),
    ]
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        for rx, cat in patterns:
            if rx.search(s):
                results.append((i, cat))
                break
    return results


def scan_file(
    repo_root: Path,
    file_path: Path,
    project_pkgs: set[str],
    context_lines: int,
    strict: bool = False,
) -> list[Finding]:
    text_lines = read_lines(file_path)
    try:
        tree = ast.parse("\n".join(text_lines))
    except Exception:
        logging.debug("Failed to parse %s", file_path)
        if strict:
            raise
        return []

    # Collect imports (first pass)
    resolver = ImportResolver()
    resolver.visit(tree)

    # Main scan
    scanner = MonkeyPatchScanner(
        repo_root, file_path, text_lines, resolver, project_pkgs, context_lines
    )
    scanner.visit(tree)
    findings = scanner.findings

    # Regex fallback (disabled in strict mode)
    if not strict:
        fallback_hits = regex_fallback(text_lines)
        seen = {(f.line, f.category) for f in findings}
        for lineno, category in fallback_hits:
            if (lineno, category) in seen:
                continue
            # Add minimal fallback finding
            code_line = text_lines[lineno - 1].rstrip() if 1 <= lineno <= len(text_lines) else ""
            context = get_context(text_lines, lineno, context_lines)
            comment = get_nearby_comment(text_lines, lineno)
            is_module_scope = True  # unknown from regex; assume module level to surface
            is_test = is_path_in_tests(repo_root, file_path)
            findings.append(
                Finding(
                    file=str(file_path.relative_to(repo_root))
                    if file_path.is_relative_to(repo_root)
                    else str(file_path),
                    line=lineno,
                    code=code_line,
                    category=category,
                    intent=classify_intent(category, None, is_test),
                    import_base=None,
                    is_test=is_test,
                    is_module_scope=is_module_scope,
                    function=None,
                    class_name=None,
                    nearby_comment=comment,
                    context=context,
                )
            )
    return findings


def iter_python_files(
    scan_root: Path,
    repo_root: Path,
    exclude_dirs: set[str],
    exclude_globs: set[str] | None = None,
) -> Iterable[Path]:
    patterns = exclude_globs or set()
    for path in scan_root.rglob("*.py"):
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            rel = path.relative_to(scan_root)
        parts = set(rel.parts)
        if parts & exclude_dirs:
            continue
        # Glob exclusions matched against the relative path
        skip = False
        for pat in patterns:
            if rel.match(pat):
                skip = True
                break
        if skip:
            continue
        yield path


def augment_findings_with_git(
    findings: list[Finding], repo_root: Path, with_git: bool
) -> None:
    if not with_git:
        return
    for finding in findings:
        file_path = Path(finding.file)
        if not file_path.is_absolute():
            file_path = repo_root / file_path
        try:
            author, commit, date = add_git_blame(repo_root, file_path, finding.line)
        except Exception:
            author = commit = date = None
        finding.git_author = author
        finding.git_commit = commit
        finding.git_commit_date = date


def summarize_findings(
    findings: list[Finding], top_n: int = 10
) -> tuple[Counter[str], Counter[str], list[tuple[str, int]]]:
    by_category: Counter[str] = Counter(f.category for f in findings)
    by_import_base: Counter[str] = Counter(
        f.import_base for f in findings if f.import_base is not None
    )
    by_file_counter: Counter[str] = Counter(f.file for f in findings)
    top_files = sorted(by_file_counter.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    return by_category, by_import_base, top_files


def compose_payload(
    *,
    paths: Paths,
    options: ScanOptions,
    findings: list[Finding],
    timestamp: dt.datetime,
    files_scanned: int,
    parse_errors: int,
) -> dict[str, object]:
    by_category, by_import_base, top_files = summarize_findings(findings)
    files_with_findings = len({f.file for f in findings})
    status = "ok"
    if parse_errors:
        status = "warn" if not options.strict else "error"
    try:
        rel_scan_root = paths.scan_root.relative_to(paths.repo_root)
        scan_root_display = str(rel_scan_root) if rel_scan_root.parts else "."
    except ValueError:
        scan_root_display = str(paths.scan_root)

    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "timestamp": timestamp.isoformat(),
        "run_id": f"{RUN_PREFIX}-{timestamp.strftime('%Y%m%d_%H%M%S')}",
        "repo_root": str(paths.repo_root),
        "scan_root": scan_root_display,
        "project_packages": sorted(options.project_packages),
        "exclude_dirs": sorted(options.exclude_dirs),
        "exclude_globs": sorted(options.exclude_globs),
        "context_lines": options.context_lines,
        "with_git": options.with_git,
        "strict": options.strict,
        "files_scanned": files_scanned,
        "files_with_findings": files_with_findings,
        "total_findings": len(findings),
        "parse_errors": parse_errors,
        "summary": {
            "by_category": dict(sorted(by_category.items())),
            "by_import_base": dict(sorted(by_import_base.items())),
            "top_files": [
                {"path": path, "count": count} for path, count in top_files
            ],
        },
    }
    return payload


def render_markdown_report(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    by_category = summary.get("by_category", {}) if isinstance(summary, dict) else {}
    by_import_base = summary.get("by_import_base", {}) if isinstance(summary, dict) else {}
    top_files = summary.get("top_files", []) if isinstance(summary, dict) else []

    lines = [
        "# Monkey Patch Scan Report\n\n",
        f"- Status: `{payload.get('status', 'unknown')}`\n",
        f"- Timestamp: `{payload.get('timestamp', '')}`\n",
        f"- Scan Root: `{payload.get('scan_root', '.')}`\n",
        f"- Files Scanned: {payload.get('files_scanned', 0)}\n",
        f"- Files With Findings: {payload.get('files_with_findings', 0)}\n",
        f"- Total Findings: {payload.get('total_findings', 0)}\n",
        f"- Parse Errors: {payload.get('parse_errors', 0)}\n\n",
    ]

    if by_category:
        lines.append("## Findings by Category\n\n")
        lines.append("| Category | Count |\n| --- | ---: |\n")
        for category, count in sorted(by_category.items(), key=lambda item: item[0]):
            lines.append(f"| {category} | {count} |\n")
        lines.append("\n")

    if by_import_base:
        lines.append("## Patched Import Bases\n\n")
        lines.append("| Package | Count |\n| --- | ---: |\n")
        for name, count in sorted(by_import_base.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| {name} | {count} |\n")
        lines.append("\n")

    if top_files:
        lines.append("## Files With Highest Patch Counts\n\n")
        lines.append("| File | Count |\n| --- | ---: |\n")
        for entry in top_files:
            lines.append(f"| {entry['path']} | {entry['count']} |\n")
        lines.append("\n")

    lines.append("## Next Steps\n\n")
    lines.append("- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.\n")
    lines.append("- [ ] Replace module-scope patches with context-managed patches in tests.\n")
    lines.append("- [ ] Isolate import-time overrides behind flags or dependency injection.\n")
    lines.append("- [ ] Add targeted tests for any retained patches with clear rationale.\n")
    return "".join(lines)


def render_log(payload: dict[str, object]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    by_category = summary.get("by_category", {}) if isinstance(summary, dict) else {}
    entries = [
        f"status={payload.get('status', 'unknown')}",
        f"timestamp={payload.get('timestamp', '')}",
        f"scan_root={payload.get('scan_root', '.')}",
        f"files_scanned={payload.get('files_scanned', 0)}",
        f"files_with_findings={payload.get('files_with_findings', 0)}",
        f"total_findings={payload.get('total_findings', 0)}",
        f"parse_errors={payload.get('parse_errors', 0)}",
    ]
    for category, count in sorted(by_category.items(), key=lambda item: item[0]):
        entries.append(f"by_category_{category}={count}")
    return "\n".join(entries) + "\n"


def ensure_run_directory(base_dir: Path, run_id: str) -> Path:
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:
    latest_dir = output_dir / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "report.json": latest_dir / "latest_report.json",
        "report.md": latest_dir / "latest_report.md",
        "log.txt": latest_dir / "latest_log.txt",
        "matches.json": latest_dir / "latest_matches.json",
        "matches.tsv": latest_dir / "latest_matches.tsv",
    }
    for filename, target in mapping.items():
        source = run_dir / filename
        if source.exists():
            target.write_bytes(source.read_bytes())


def write_artifacts(
    *,
    run_dir: Path,
    payload: dict[str, object],
    findings: list[Finding],
    output_dir: Path,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "report.md").write_text(
        render_markdown_report(payload),
        encoding="utf-8",
    )
    (run_dir / "log.txt").write_text(render_log(payload), encoding="utf-8")
    matches = [finding.to_dict() for finding in findings]
    (run_dir / "matches.json").write_text(
        json.dumps(matches, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if findings:
        tsv_lines = [
            "file\tline\tcategory\timport_base\tintent\tis_test\tis_module_scope\tcode"
        ]
        for finding in findings:
            tsv_lines.append(
                "\t".join(
                    [
                        finding.file,
                        str(finding.line),
                        finding.category,
                        finding.import_base or "",
                        finding.intent,
                        "true" if finding.is_test else "false",
                        "true" if finding.is_module_scope else "false",
                        finding.code.replace("\t", " "),
                    ]
                )
            )
        (run_dir / "matches.tsv").write_text("\n".join(tsv_lines) + "\n", encoding="utf-8")
    _write_latest_artifacts(run_dir, output_dir)


def prune_history(base_dir: Path, keep: int) -> None:
    keep = max(keep, 1)
    if not base_dir.exists():
        return
    run_dirs = sorted(
        (path for path in base_dir.iterdir() if path.is_dir() and path.name.startswith(RUN_PREFIX)),
        key=lambda item: item.name,
    )
    excess = len(run_dirs) - keep
    for old_dir in run_dirs[: max(excess, 0)]:
        shutil.rmtree(old_dir, ignore_errors=True)


def scan_repository(paths: Paths, options: ScanOptions) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    parse_errors = 0
    files_scanned = 0
    for file in iter_python_files(
        paths.scan_root, paths.repo_root, options.exclude_dirs, options.exclude_globs
    ):
        try:
            if file.resolve() == Path(__file__).resolve():
                continue
        except Exception:
            # If resolving fails, keep scanning other files.
            logging.debug("Unable to resolve path %s", file)
        files_scanned += 1
        try:
            file_findings = scan_file(
                paths.repo_root,
                file,
                options.project_packages,
                options.context_lines,
                strict=options.strict,
            )
        except Exception:
            parse_errors += 1
            logging.exception("Parse error in %s", file)
            continue
        findings.extend(file_findings)
    return findings, parse_errors, files_scanned


def run_self_test(verbose: bool = False) -> int:
    import tempfile

    sample_files = {
        "a_modscope_assign.py": """
import requests
requests.adapters.DEFAULT_POOLSIZE = 1  # change pool size
""",
        "b_setattr.py": """
import requests
setattr(requests, "api", object())
""",
        "c_sysmodules.py": """
import sys
sys.modules["foo"] = object()
""",
        "d_builtins.py": """
import builtins
builtins.open = lambda *a, **k: None
""",
        "e_patch_misuse.py": """
from unittest.mock import patch
@patch("x.y.func")
def test_foo():
    pass
patch("x.y.func")  # not context-managed
""",
        "f_env_mut.py": """
import os
os.environ["SOME_KEY"] = "1"
os.environ.update({"A":"b"})
""",
        "g_singleton_rebind.py": """
import logging
logging.getLogger = lambda name=None: None
""",
        "h_from_import_attr.py": """
from somepkg import moduleX as mx
mx.feature_flag = True
""",
    }
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        for name, src in sample_files.items():
            (root / name).write_text(src, encoding="utf-8")
        # Prepare args and run scan within temp dir lifetime
        pkgs = {p.name for p in root.iterdir() if p.is_dir()}
        findings: list[Finding] = []
        for file in iter_python_files(root, root, set(DEFAULT_EXCLUDES), set()):
            findings.extend(scan_file(root, file, pkgs, DEFAULT_CONTEXT_LINES))
        # Expectations (at least one finding per category tested)
        cats = {f.category for f in findings}
        expected = {
            CATEGORY_ATTRIBUTE_REASSIGNMENT,
            CATEGORY_SETATTR,
            CATEGORY_SYS_MODULES,
            CATEGORY_BUILTINS,
            CATEGORY_TEST_PATCH_MISUSE,
            CATEGORY_GLOBAL_ENV,
            CATEGORY_SINGLETON_REBIND,
        }
        missing = expected - cats
        if missing:
            if verbose:
                logging.debug("[SELF-TEST] Missing categories: %s", sorted(missing))
            return 2
        if verbose:
            logging.debug(
                "[SELF-TEST] OK — %d findings across %d files", len(findings), len(sample_files)
            )
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan repository sources for monkey patches and emit structured artifacts."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root directory (defaults to three levels up from this script)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Directory to scan relative to the repo root (defaults to the repo root)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override for artifact output directory (defaults to producer_reports/monkey_patch_scans)",
    )
    parser.add_argument(
        "--project-packages",
        nargs="*",
        default=None,
        help="Space-separated list of owned packages (defaults to auto-detect)",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=None,
        help="Directory names to exclude from scanning (defaults to repo-standard list)",
    )
    parser.add_argument(
        "--exclude-globs",
        nargs="*",
        default=None,
        help="Glob patterns to exclude (e.g., external/** .founder_files/**)",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=DEFAULT_CONTEXT_LINES,
        help="Lines of context to capture around each finding",
    )
    parser.add_argument(
        "--with-git", action="store_true", help="Include git blame metadata where available"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat parse errors as fatal (after scanning)"
    )
    parser.add_argument(
        "--artifacts-to-keep",
        type=int,
        default=DEFAULT_ARTIFACTS_TO_KEEP,
        help="Number of historical run directories to retain (minimum 1)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--self-test", action="store_true", help="Run the built-in scanner self-test and exit"
    )
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[3]
    scan_root = (repo_root / args.root).resolve()
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
        output_dir = output_dir.resolve()
    else:
        output_dir = (repo_root / DEFAULT_OUTPUT_DIR).resolve()
    return Paths(repo_root=repo_root, scan_root=scan_root, output_dir=output_dir)


def run(argv: list[str] | None = None) -> dict[str, object]:
    args = parse_args(argv)
    configure_logging(args.log_level)

    if args.self_test:
        rc = run_self_test(verbose=args.log_level == "DEBUG")
        status = "self-test" if rc == 0 else "self-test-failed"
        return {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "exit_code": rc,
        }

    paths = build_paths(args)
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    project_packages = (
        set(args.project_packages)
        if args.project_packages
        else top_level_packages_default(paths.repo_root)
    )
    exclude_dirs = set(args.exclude_dirs) if args.exclude_dirs is not None else set(DEFAULT_EXCLUDES)
    exclude_globs = (
        set(args.exclude_globs) if args.exclude_globs is not None else set(DEFAULT_EXCLUDE_GLOBS)
    )
    options = ScanOptions(
        project_packages=project_packages,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        context_lines=int(args.context_lines),
        with_git=bool(args.with_git),
        strict=bool(args.strict),
        artifacts_to_keep=int(args.artifacts_to_keep),
    )

    logging.info("Scanning repo: %s", paths.repo_root)
    logging.info("Scan root: %s", paths.scan_root)
    logging.info("Output directory: %s", paths.output_dir)
    logging.info("Project packages: %s", ", ".join(sorted(options.project_packages)))

    findings, parse_errors, files_scanned = scan_repository(paths, options)
    augment_findings_with_git(findings, paths.repo_root, options.with_git)

    timestamp = dt.datetime.now(dt.timezone.utc)
    payload = compose_payload(
        paths=paths,
        options=options,
        findings=findings,
        timestamp=timestamp,
        files_scanned=files_scanned,
        parse_errors=parse_errors,
    )

    run_id = str(payload["run_id"])
    run_dir = ensure_run_directory(paths.output_dir, run_id)
    write_artifacts(run_dir=run_dir, payload=payload, findings=findings, output_dir=paths.output_dir)
    prune_history(paths.output_dir, options.artifacts_to_keep)

    logging.info("Done. Findings: %d", len(findings))
    if parse_errors:
        log_fn = logging.error if options.strict else logging.warning
        log_fn("%d file(s) failed to parse.", parse_errors)

    return payload


def main(argv: list[str] | None = None) -> int:
    payload = run(argv)
    status = payload.get("status")
    if status in {"self-test", "self-test-failed"}:
        return int(payload.get("exit_code", 0))
    if status == "error":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
