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

Outputs (written to timestamped directory):
  - report.json  — rich per-finding JSON objects with fields described below
  - report.csv   — selected columns for quick triage
  - SUMMARY.md   — counts by category, top externals, files with most patches

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
import csv
import datetime as dt
import json
import logging
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Defaults (workspace-relative)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_BASE = ROOT / ".repo_studios" / "monkey_patch"
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
    repo_root: Path, exclude_dirs: set[str], exclude_globs: set[str] | None = None
) -> Iterable[Path]:
    patterns = exclude_globs or set()
    for path in repo_root.rglob("*.py"):
        rel = path.relative_to(repo_root)
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


def write_reports(
    findings: list[Finding],
    output_dir: Path,
    with_git: bool,
    repo_root: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Optionally augment with git blame
    if with_git:
        for f in findings:
            try:
                author, commit, date = add_git_blame(repo_root, (repo_root / f.file), f.line)
            except Exception:
                author = commit = date = None
            f.git_author = author
            f.git_commit = commit
            f.git_commit_date = date

    # JSON
    json_path = output_dir / "report.json"
    with json_path.open("w", encoding="utf-8") as jf:
        json.dump([asdict(f) for f in findings], jf, indent=2, ensure_ascii=False)

    # CSV (selected columns)
    csv_path = output_dir / "report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(
            [
                "file",
                "line",
                "category",
                "import_base",
                "is_test",
                "is_module_scope",
                "intent",
                "code",
            ]
        )
        for f in findings:
            writer.writerow(
                [
                    f.file,
                    f.line,
                    f.category,
                    f.import_base or "",
                    f.is_test,
                    f.is_module_scope,
                    f.intent,
                    f.code,
                ]
            )

    # SUMMARY.md
    summary_path = output_dir / "SUMMARY.md"
    by_category: dict[str, int] = {}
    by_import_base: dict[str, int] = {}
    by_file: dict[str, int] = {}
    for f in findings:
        by_category[f.category] = by_category.get(f.category, 0) + 1
        if f.import_base:
            by_import_base[f.import_base] = by_import_base.get(f.import_base, 0) + 1
        by_file[f.file] = by_file.get(f.file, 0) + 1

    def top_n(d: dict[str, int], n: int = 10) -> list[tuple[str, int]]:
        return sorted(d.items(), key=lambda x: (-x[1], x[0]))[:n]

    lines: list[str] = []
    lines.append("# Monkey Patch Scan Summary\n")
    lines.append(f"Date: {dt.datetime.now().isoformat()}\n")
    lines.append("\n## Totals by Category\n")
    for cat, cnt in sorted(by_category.items()):
        lines.append(f"- {cat}: {cnt}")
    lines.append("\n## Top Externals Patched\n")
    for name, cnt in top_n(by_import_base):
        lines.append(f"- {name}: {cnt}")
    lines.append("\n## Files with Highest Patch Count\n")
    for name, cnt in top_n(by_file):
        lines.append(f"- {name}: {cnt}")

    # Grouped by package table
    if by_import_base:
        lines.append("\n## Patches Grouped by Package\n")
        lines.append("| Package | Count |\n|---|---:|")
        for name, cnt in sorted(by_import_base.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| {name} | {cnt} |")

    # Next steps checklist
    lines.append("\n## Next Steps\n")
    lines.append(
        "- [ ] Review global mutations (builtins, os.environ) and confine to startup phases."
    )
    lines.append("- [ ] Replace module-scope patches with context-managed patches in tests.")
    lines.append("- [ ] Isolate import-time overrides behind flags or dependency injection.")
    lines.append("- [ ] Add targeted tests for any retained patches with clear rationale.")

    with summary_path.open("w", encoding="utf-8") as sf:
        sf.write("\n".join(lines) + "\n")


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
        for file in iter_python_files(root, DEFAULT_EXCLUDES):
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan repo for monkey patches and export reports.")
    parser.add_argument("--repo-root", type=str, default=".", help="Repository root directory")
    parser.add_argument(
        "--output-dir", type=str, default=str(DEFAULT_OUTPUT_BASE), help="Base output directory"
    )
    parser.add_argument(
        "--project-packages",
        nargs="*",
        help="Space-separated list of owned packages (defaults to auto-detect)",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=list(DEFAULT_EXCLUDES),
        help="Directories to exclude (names only)",
    )
    parser.add_argument(
        "--exclude-globs",
        nargs="*",
        default=list(DEFAULT_EXCLUDE_GLOBS),
        help="Glob patterns to exclude (e.g., external/** .founder_files/**)",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=DEFAULT_CONTEXT_LINES,
        help="Lines of context around findings",
    )
    parser.add_argument(
        "--with-git", action="store_true", help="Include git blame metadata if available"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Disable regex fallback and fail on parse errors"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--self-test", action="store_true", help="Run internal self-test and exit")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="[%(levelname)s] %(message)s"
    )

    if args.self_test:
        rc = run_self_test(verbose=args.verbose)
        return rc

    try:
        repo_root = Path(args.repo_root).resolve()
        out_base = (
            Path(args.output_dir)
            if Path(args.output_dir).is_absolute()
            else (repo_root / args.output_dir)
        ).resolve()
        exclude_dirs = set(args.exclude_dirs)
        exclude_globs = set(args.exclude_globs)
        context_lines = int(args.context_lines)
        if args.project_packages:
            project_pkgs = set(args.project_packages)
        else:
            project_pkgs = top_level_packages_default(repo_root)

        timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
        out_dir = out_base / timestamp
        logging.info("Scanning repo: %s", repo_root)
        logging.info("Output directory: %s", out_dir)
        logging.info("Project packages: %s", ", ".join(sorted(project_pkgs)))

        all_findings: list[Finding] = []
        parse_errors = 0
        for file in iter_python_files(repo_root, exclude_dirs, exclude_globs):
            # Skip our own script and generated outputs
            try:
                if Path(file).resolve() == Path(__file__).resolve():
                    continue
            except Exception:
                pass
            try:
                fds = scan_file(repo_root, file, project_pkgs, context_lines, strict=args.strict)
            except Exception:
                parse_errors += 1
                logging.exception("Parse error in %s", file)
                continue
            all_findings.extend(fds)

        write_reports(all_findings, out_dir, args.with_git, repo_root)
        logging.info("Done. Findings: %d", len(all_findings))
        if args.strict and parse_errors:
            logging.error("Strict mode: %d file(s) failed to parse.", parse_errors)
            return 1
        return 0
    except Exception as e:
        logging.exception("Fatal error during scan: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
