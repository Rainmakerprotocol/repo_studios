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

Outputs (written under `.repo_studios/reports/producer_reports/<viewer>/<topic>/<YYYYMMDD-HHMM>/`):
    - manifest.json  — run metadata + structured findings payload
    - summary.md     — human-readable synopsis with tables and recommended follow-up actions
    - telemetry.json — extracted metrics for time-series ingestion

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
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

LIBRARIES_ROOT = Path(__file__).resolve().parents[3] / ".repo_studios" / "command_center" / "scripts"

try:
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep
except ModuleNotFoundError:  # pragma: no cover - fallback when running standalone
    if str(LIBRARIES_ROOT) not in sys.path:
        sys.path.insert(0, str(LIBRARIES_ROOT))
    from libraries import (
        KeepSpec,
        PathSpec,
        OptionsConfig,
        PathsConfig,
        build_standard_options,
        build_standard_paths,
        prune_run_directories,
    )
    from libraries.database_integration import create_storage
    from libraries.report_paths import build_topic_path
    from libraries.retention_policy import get_keep

# Defaults (repo-root-relative)
# NOTE: Keep the producer default topic aligned with the Stage 5.1 orchestrator naming.
DEFAULT_OUTPUT_DIR = build_topic_path("producer", "monkey_patch_scans")
DEFAULT_KEEP = get_keep("scan_monkey_patches")
SCHEMA_VERSION = 1
TOPIC_SLUG = "monkey_patch_scans"
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
    """Resolved path configuration for monkey patch scanning.

    Attributes:
        repo_root: Repository root directory.
        scan_root: Directory to scan for Python files.
        output_dir: Directory for output artifacts.
    """

    repo_root: Path
    scan_root: Path
    output_dir: Path


@dataclass(frozen=True)
class Options:
    """Retention options for artifact management.

    Attributes:
        keep: Number of artifact bundles to retain.
    """

    keep: int


@dataclass(frozen=True)
class ScanOptions:
    """Configuration options for monkey patch scanning.

    Attributes:
        project_packages: Set of package names considered project-owned.
        exclude_dirs: Directory names to skip during traversal.
        exclude_globs: Glob patterns for files/directories to exclude.
        context_lines: Number of context lines to capture around findings.
        with_git: Whether to augment findings with git blame metadata.
        strict: Disable regex fallback; fail on parse errors.
        keep: Number of artifact bundles to retain.
    """

    project_packages: set[str]
    exclude_dirs: set[str]
    exclude_globs: set[str]
    context_lines: int
    with_git: bool
    strict: bool
    keep: int


@dataclass
class Finding:
    """Represents a detected monkey patch occurrence.

    Attributes:
        file: Relative file path where patch was found.
        line: Line number of the patch.
        code: Source code line containing the patch.
        category: Classification category of the patch.
        intent: Inferred intent of the patch.
        import_base: Base module being patched.
        is_test: Whether the patch is in test code.
        is_module_scope: Whether the patch is at module scope.
        function: Enclosing function name if any.
        class_name: Enclosing class name if any.
        nearby_comment: Comment near the patch for context.
        context: Surrounding source code lines.
        git_author: Git author of the patch line.
        git_commit: Git commit hash for the patch.
        git_commit_date: Date of the git commit.
    """

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
        """Convert finding to dictionary representation.

        Returns:
            Dictionary containing all finding attributes.
        """
        return asdict(self)


PATH_SPECS: dict[str, PathSpec] = {
    "scan_root": PathSpec(field="root", default=Path("."), within_repo=False),
    "output_dir": PathSpec(
        field="output_dir",
        default=DEFAULT_OUTPUT_DIR,
        ensure_dir=True,
        within_repo=True,
    ),
}


PATH_CONFIG = PathsConfig(
    dataclass_type=Paths,
    path_specs=PATH_SPECS,
    repo_root_depth=4,
)


OPTIONS_CONFIG = OptionsConfig(
    dataclass_type=Options,
    keep_specs={
        "keep": KeepSpec(field="keep", minimum=1),
    },
)


class ImportResolver(ast.NodeVisitor):
    """Collect import aliases → modules and objects.

    Attributes:
        alias_to_module: Mapping of import aliases to full module paths.
        alias_is_from_object: Mapping of aliases to (module, object) tuples.
        import_lines: Set of line numbers containing import statements.
    """

    def __init__(self) -> None:
        """Initialize empty alias and import line tracking."""
        self.alias_to_module: dict[str, str] = {}
        self.alias_is_from_object: dict[str, tuple[str, str]] = {}
        self.import_lines: set[int] = set()

    def visit_Import(self, node: ast.Import) -> Any:
        """Process import statements and record aliases.

        Args:
            node: AST Import node.

        Returns:
            Result of generic_visit for continued traversal.
        """
        self.import_lines.add(getattr(node, "lineno", -1))
        for alias in node.names:
            mod = alias.name  # full module path
            asname = alias.asname or mod.split(".")[-1]
            self.alias_to_module[asname] = mod
        return self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        """Process from-import statements and record aliases.

        Args:
            node: AST ImportFrom node.

        Returns:
            Result of generic_visit for continued traversal.
        """
        self.import_lines.add(getattr(node, "lineno", -1))
        module = node.module or ""
        for alias in node.names:
            asname = alias.asname or alias.name
            # map alias to full path module.object
            self.alias_to_module[asname] = f"{module}.{alias.name}" if module else alias.name
            self.alias_is_from_object[asname] = (module, alias.name)
        return self.generic_visit(node)


class ScopeTracker(ast.NodeVisitor):
    """Track current function/class scope while scanning.

    Attributes:
        stack: Stack of (type, name) tuples representing current scope.
    """

    def __init__(self) -> None:
        """Initialize empty scope stack."""
        self.stack: list[tuple[str, str]] = []  # (type, name)

    def current(self) -> tuple[bool, str | None, str | None]:
        """Return current scope information.

        Returns:
            Tuple of (is_module_scope, function_name, class_name).
        """
        fn = None
        cl = None
        for t, n in reversed(self.stack):
            if t == "function" and fn is None:
                fn = n
            if t == "class" and cl is None:
                cl = n
        return (len(self.stack) == 0, fn, cl)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        """Enter function scope and traverse children.

        Args:
            node: AST FunctionDef node.
        """
        self.stack.append(("function", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        """Enter async function scope and traverse children.

        Args:
            node: AST AsyncFunctionDef node.
        """
        self.stack.append(("function", node.name))
        self.generic_visit(node)
        self.stack.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        """Enter class scope and traverse children.

        Args:
            node: AST ClassDef node.
        """
        self.stack.append(("class", node.name))
        self.generic_visit(node)
        self.stack.pop()


def read_lines(path: Path) -> list[str]:
    """Read file contents and return as list of lines.

    Args:
        path: Path to file to read.

    Returns:
        List of lines, empty if reading fails.
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []


def get_context(lines: list[str], lineno: int, n: int) -> str:
    """Extract context lines around a given line number.

    Args:
        lines: Source file lines.
        lineno: Target line number (1-based).
        n: Number of context lines before and after.

    Returns:
        Formatted string with line numbers and content.
    """
    i = max(1, lineno - n)
    j = min(len(lines), lineno + n)
    segment = lines[i - 1 : j]
    return "\n".join(f"{k + 1:>5}: {segment[k]}" for k in range(len(segment)))


def get_nearby_comment(lines: list[str], lineno: int, lookback: int = 5) -> str | None:
    """Find comment lines preceding a given line.

    Args:
        lines: Source file lines.
        lineno: Target line number (1-based).
        lookback: Maximum lines to search backward.

    Returns:
        Contiguous comment text or None if not found.
    """
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
    """Check if file path is within a tests directory.

    Args:
        repo_root: Repository root for relative path computation.
        file_path: Path to check.

    Returns:
        True if path contains 'tests' component.
    """
    try:
        rel = file_path.relative_to(repo_root)
        parts = rel.parts
        return "tests" in parts
    except Exception:
        return False


def top_level_packages_default(repo_root: Path) -> set[str]:
    """Discover project packages by scanning repo root.

    Args:
        repo_root: Repository root directory.

    Returns:
        Set of package names found at top level.
    """
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
    """Extract top-level module name from dotted path.

    Args:
        mod: Dotted module path or None.

    Returns:
        First component of the path or None.
    """
    if not mod:
        return None
    return mod.split(".")[0]


def dotted_name_from_attribute(attr: ast.AST) -> str | None:
    """Build dotted name string from AST attribute chain.

    Args:
        attr: AST Attribute node.

    Returns:
        Dotted name string or None if not resolvable.
    """
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


def is_alias_external(alias: str, resolver: ImportResolver, project_pkgs: set[str]) -> tuple[bool, str | None]:
    """Determine if an alias refers to an external module.

    Args:
        alias: Import alias name.
        resolver: ImportResolver with alias mappings.
        project_pkgs: Set of project-owned package names.

    Returns:
        Tuple of (is_external, base_module_name).
    """
    # Determine the import base for an alias and whether it's external
    mod = resolver.alias_to_module.get(alias)
    if not mod:
        return False, None
    base = base_module_name(mod)
    return (base not in project_pkgs if base else False), base


def classify_intent(category: str, import_base: str | None, is_test: bool) -> str:
    """Infer intent of a monkey patch based on classification.

    Args:
        category: Patch category classification.
        import_base: Base module being patched.
        is_test: Whether patch is in test code.

    Returns:
        Intent string describing the patch purpose.
    """
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


def add_git_blame(repo_root: Path, file_path: Path, lineno: int) -> tuple[str | None, str | None, str | None]:
    """Retrieve git blame metadata for a specific line.

    Args:
        repo_root: Repository root for git commands.
        file_path: Path to file being blamed.
        lineno: Line number to blame.

    Returns:
        Tuple of (author, commit_hash, commit_date) or Nones on failure.
    """
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
    """AST visitor that detects monkey patch patterns.

    Attributes:
        repo_root: Repository root directory.
        file_path: Path to file being scanned.
        lines: Source lines of the file.
        resolver: ImportResolver with alias mappings.
        project_pkgs: Set of project-owned package names.
        context_lines: Number of context lines to capture.
        scope: ScopeTracker for current scope.
        findings: List of detected monkey patch findings.
    """

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
    def generic_visit(self, node: ast.AST) -> Any:
        # Manually route into scope tracker for nested defs
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Push/pop handled by scope tracker methods; call them directly
            self.scope.visit(node)
            return
        super().generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        self._handle_assignment(node, getattr(node, "lineno", -1))
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        self._handle_assignment(node, getattr(node, "lineno", -1))
        return self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:
        self._handle_assignment(node, getattr(node, "lineno", -1))
        return self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
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
                is_alias_external(base_alias or "", self.resolver, self.project_pkgs) if base_alias else (False, None)
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

    def visit_Delete(self, node: ast.Delete) -> Any:
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

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
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

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
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
                self._add_finding(lineno, CATEGORY_SYS_MODULES, "sys", is_module_scope, fn_name, cl_name)
                continue
            # builtins.X = ...
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "builtins":
                self._add_finding(lineno, CATEGORY_BUILTINS, "builtins", is_module_scope, fn_name, cl_name)
                continue
            # os.environ[...]
            if isinstance(t, ast.Subscript) and _is_os_environ(t):
                self._add_finding(lineno, CATEGORY_GLOBAL_ENV, "os", is_module_scope, fn_name, cl_name)
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
                    external, base_name = is_alias_external(base_alias, self.resolver, self.project_pkgs)
                    if base_name:
                        # Always record attribute reassignment
                        self._add_finding(
                            lineno,
                            CATEGORY_ATTRIBUTE_REASSIGNMENT,
                            base_name,
                            is_module_scope,
                            fn_name,
                            cl_name,
                        )
                        # If near import at module scope, also record import-time side effect
                        if is_module_scope and _near_import(lineno, self.resolver.import_lines):
                            self._add_finding(
                                lineno,
                                CATEGORY_IMPORT_TIME,
                                base_name,
                                is_module_scope,
                                fn_name,
                                cl_name,
                            )
                        continue
            # assignment to imported object alias (from X import Y; Y = ...)
            if isinstance(t, ast.Name) and t.id in self.resolver.alias_to_module:
                base_module = base_module_name(self.resolver.alias_to_module.get(t.id))
                if base_module:
                    # Rebinding an imported symbol
                    self._add_finding(
                        lineno,
                        CATEGORY_ATTRIBUTE_REASSIGNMENT,
                        base_module,
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
    """Check if subscript is sys.modules access.

    Args:
        sub: AST Subscript node.

    Returns:
        True if subscript is sys.modules[...].
    """
    # sys.modules[...] pattern
    if isinstance(sub.value, ast.Attribute) and isinstance(sub.value.value, ast.Name):
        return sub.value.value.id == "sys" and sub.value.attr == "modules"
    return False


def _is_os_environ(sub: ast.Subscript) -> bool:
    """Check if subscript is os.environ access.

    Args:
        sub: AST Subscript node.

    Returns:
        True if subscript is os.environ[...].
    """
    if isinstance(sub.value, ast.Attribute) and isinstance(sub.value.value, ast.Name):
        return sub.value.value.id == "os" and sub.value.attr == "environ"
    return False


def _near_import(lineno: int, import_lines: set[int], window: int = 5) -> bool:
    """Check if line number is near an import statement.

    Args:
        lineno: Line number to check.
        import_lines: Set of import line numbers.
        window: Proximity window size.

    Returns:
        True if lineno is within window of any import.
    """
    return any(abs(lineno - li) <= window for li in import_lines)


def _is_patch_name(name: str, resolver: ImportResolver) -> bool:
    """Check if name refers to unittest.mock.patch.

    Args:
        name: Name to check.
        resolver: ImportResolver with alias mappings.

    Returns:
        True if name resolves to patch function.
    """
    # Check if alias maps to unittest.mock.patch (best-effort)
    mapped = resolver.alias_to_module.get(name)
    if not mapped:
        return name == "patch"  # fallback if directly imported as patch
    return mapped.endswith(".patch") or mapped == "unittest.mock.patch"


def _is_patch_call(node: ast.Call, resolver: ImportResolver) -> bool:
    """Check if call is to unittest.mock.patch.

    Args:
        node: AST Call node.
        resolver: ImportResolver with alias mappings.

    Returns:
        True if call is to patch function.
    """
    if isinstance(node.func, ast.Name):
        return _is_patch_name(node.func.id, resolver)
    if isinstance(node.func, ast.Attribute):
        dotted = dotted_name_from_attribute(node.func)
        return dotted is not None and dotted.endswith(".patch")
    return False


def _is_patch_decorator(dec: ast.AST, resolver: ImportResolver) -> bool:
    """Check if decorator is unittest.mock.patch.

    Args:
        dec: AST decorator node.
        resolver: ImportResolver with alias mappings.

    Returns:
        True if decorator is patch.
    """
    if isinstance(dec, ast.Call):
        return _is_patch_call(dec, resolver)
    if isinstance(dec, ast.Name):
        return _is_patch_name(dec.id, resolver)
    if isinstance(dec, ast.Attribute):
        dotted = dotted_name_from_attribute(dec)
        return dotted is not None and dotted.endswith(".patch")
    return False


def regex_fallback(lines: list[str]) -> list[tuple[int, str]]:
    """Scan lines with regex for monkey patch patterns.

    Args:
        lines: Source file lines.

    Returns:
        List of (line_number, matched_code) tuples.
    """
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
    """Scan a single Python file for monkey patch patterns.

    Parse the file into an AST and scan for monkey patches using both
    AST-based detection and regex fallback patterns.

    Args:
        repo_root: Repository root path for relative path computation.
        file_path: Path to the Python file to scan.
        project_pkgs: Set of project package names for external detection.
        context_lines: Number of surrounding lines to capture.
        strict: If True, re-raise parse errors and skip regex fallback.

    Returns:
        List of Finding objects for detected monkey patches.
    """
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
    scanner = MonkeyPatchScanner(repo_root, file_path, text_lines, resolver, project_pkgs, context_lines)
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
    """Iterate over Python files in a directory tree.

    Recursively find all .py files under scan_root, filtering out
    excluded directories and glob patterns.

    Args:
        scan_root: Root directory to start scanning from.
        repo_root: Repository root for relative path computation.
        exclude_dirs: Directory names to skip (matched against path parts).
        exclude_globs: Glob patterns for paths to exclude.

    Yields:
        Path objects for each Python file found.
    """
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


def augment_findings_with_git(findings: list[Finding], repo_root: Path, with_git: bool) -> None:
    """Add git blame metadata to findings.

    Update each finding in place with author, commit hash, and date
    from git blame for the finding's line.

    Args:
        findings: List of Finding objects to augment.
        repo_root: Repository root for git operations.
        with_git: If False, skip git augmentation entirely.
    """
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
    """Compute summary statistics from findings.

    Aggregate findings by category and intent, and identify the most
    affected files.

    Args:
        findings: List of Finding objects to summarize.
        top_n: Number of top files to include in ranking.

    Returns:
        Tuple of (category counts, intent counts, top files with counts).
    """
    by_category: Counter[str] = Counter(f.category for f in findings)
    by_import_base: Counter[str] = Counter(f.import_base for f in findings if f.import_base is not None)
    by_file_counter: Counter[str] = Counter(f.file for f in findings)
    top_files = sorted(by_file_counter.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    return by_category, by_import_base, top_files


def summarize_findings_extended(findings: list[Finding], top_n: int = 10) -> dict[str, Any]:
    """Compute extended summary statistics for findings.

    In addition to the legacy summary (category/import-base/top-files), compute
    test vs non-test splits and module-scope counts to support better human
    triage while keeping the bundle machine-readable.

    Args:
        findings: List of Finding objects to summarize.
        top_n: Number of top files to include in each ranking.

    Returns:
        Dictionary with extended summary metrics.
    """
    total_findings = len(findings)
    test_findings = [f for f in findings if f.is_test]
    non_test_findings = [f for f in findings if not f.is_test]

    module_scope_findings = [f for f in findings if f.is_module_scope]
    module_scope_test = [f for f in module_scope_findings if f.is_test]
    module_scope_non_test = [f for f in module_scope_findings if not f.is_test]

    by_category_test: Counter[str] = Counter(f.category for f in test_findings)
    by_category_non_test: Counter[str] = Counter(f.category for f in non_test_findings)

    by_file_test: Counter[str] = Counter(f.file for f in test_findings)
    by_file_non_test: Counter[str] = Counter(f.file for f in non_test_findings)

    top_files_test = sorted(by_file_test.items(), key=lambda item: (-item[1], item[0]))[:top_n]
    top_files_non_test = sorted(by_file_non_test.items(), key=lambda item: (-item[1], item[0]))[:top_n]

    return {
        "total_findings_test": len(test_findings),
        "total_findings_non_test": len(non_test_findings),
        "module_scope_total": len(module_scope_findings),
        "module_scope_test": len(module_scope_test),
        "module_scope_non_test": len(module_scope_non_test),
        "by_category_test": dict(sorted(by_category_test.items())),
        "by_category_non_test": dict(sorted(by_category_non_test.items())),
        "top_files_test": [{"path": path, "count": count} for path, count in top_files_test],
        "top_files_non_test": [{"path": path, "count": count} for path, count in top_files_non_test],
        "_extended_schema_version": 1,
        "_extended_total_findings": total_findings,
    }


def _relativize(path: Path, repo_root: Path) -> str:
    """Convert path to POSIX string relative to repo root.

    Args:
        path: Path to relativize.
        repo_root: Repository root for relative path computation.

    Returns:
        POSIX-style relative path string, or absolute if not relative.
    """
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _resolve_run_timestamp(*, override: str | None, now: dt.datetime) -> str:
    """Resolve the run timestamp for artifact naming.

    Validate and return the override timestamp if provided, otherwise
    format the current datetime.

    Args:
        override: User-provided timestamp string or None.
        now: Current datetime for default timestamp.

    Returns:
        Timestamp string in YYYYMMDD-HHMM format.

    Raises:
        ValueError: If override is not in YYYYMMDD-HHMM format.
    """
    if override:
        candidate = override.strip()
        # Expected: YYYYMMDD-HHMM (13 chars)
        try:
            dt.datetime.strptime(candidate, "%Y%m%d-%H%M")
        except ValueError as exc:
            raise ValueError("--timestamp must be in YYYYMMDD-HHMM format (UTC)") from exc
        return candidate
    return now.strftime("%Y%m%d-%H%M")


def compose_manifest(
    *,
    paths: Paths,
    options: ScanOptions,
    findings: list[Finding],
    timestamp: dt.datetime,
    run_timestamp: str,
    generated_at: str,
    bundle_dir: Path,
    files_scanned: int,
    parse_errors: int,
    duration_ms: int,
) -> dict[str, object]:
    """Compose the manifest JSON for the scan bundle.

    Build a complete manifest dictionary with metadata, inputs,
    summary statistics, and all findings.

    Args:
        paths: Resolved path configuration.
        options: Scan options used for this run.
        findings: List of detected monkey patch findings.
        timestamp: Scan execution datetime.
        run_timestamp: Formatted timestamp for artifact naming.
        generated_at: ISO-format generation timestamp.
        bundle_dir: Output directory for the bundle.
        files_scanned: Total number of files processed.
        parse_errors: Count of files that failed to parse.
        duration_ms: Scan duration in milliseconds.

    Returns:
        Complete manifest dictionary ready for JSON serialization.
    """
    by_category, by_import_base, top_files = summarize_findings(findings)
    extended_summary = summarize_findings_extended(findings)
    files_with_findings = len({f.file for f in findings})
    status = "ok"
    if parse_errors:
        status = "warn" if not options.strict else "error"
    try:
        rel_scan_root = paths.scan_root.relative_to(paths.repo_root)
        scan_root_display = str(rel_scan_root) if rel_scan_root.parts else "."
    except ValueError:
        scan_root_display = str(paths.scan_root)

    manifest_path = bundle_dir / "manifest.json"
    summary_path = bundle_dir / "summary.md"
    telemetry_path = bundle_dir / "telemetry.json"

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "generated_at": generated_at,
        "status": status,
        "git_sha": None,
        "repo_root": str(paths.repo_root),
        "inputs": {
            "scan_root": scan_root_display,
            "project_packages": sorted(options.project_packages),
            "exclude_dirs": sorted(options.exclude_dirs),
            "exclude_globs": sorted(options.exclude_globs),
            "context_lines": options.context_lines,
            "with_git": options.with_git,
            "strict": options.strict,
            "keep": max(1, int(options.keep)),
            "timestamp": run_timestamp,
        },
        "catalog": [
            {"artifact": "manifest.json", "path": _relativize(manifest_path, paths.repo_root)},
            {"artifact": "summary.md", "path": _relativize(summary_path, paths.repo_root)},
            {"artifact": "telemetry.json", "path": _relativize(telemetry_path, paths.repo_root)},
        ],
        "provenance": {
            "script": "scan_monkey_patches.py",
            "trigger": "cli",
        },
        "payload": {
            "timestamp": timestamp.isoformat(),
            "scan_root": scan_root_display,
            "files_scanned": files_scanned,
            "files_with_findings": files_with_findings,
            "total_findings": len(findings),
            "parse_errors": parse_errors,
            "duration_ms": duration_ms,
            "summary": {
                "by_category": dict(sorted(by_category.items())),
                "by_import_base": dict(sorted(by_import_base.items())),
                "top_files": [{"path": path, "count": count} for path, count in top_files],
                **extended_summary,
            },
            "findings": [finding.to_dict() for finding in findings],
        },
    }
    return manifest


def compose_telemetry(
    *,
    manifest: dict[str, object],
    run_timestamp: str,
    generated_at: str,
) -> dict[str, object]:
    """Compose telemetry JSON from manifest data.

    Extract key metrics from the manifest for lightweight telemetry
    reporting.

    Args:
        manifest: Complete manifest dictionary from compose_manifest.
        run_timestamp: Formatted timestamp for artifact naming.
        generated_at: ISO-format generation timestamp.

    Returns:
        Telemetry dictionary with extracted metrics.
    """
    payload_obj = cast(dict[str, Any], manifest.get("payload")) if isinstance(manifest.get("payload"), dict) else {}
    summary = cast(dict[str, Any], payload_obj.get("summary")) if isinstance(payload_obj.get("summary"), dict) else {}
    by_category = cast(dict[str, Any], summary.get("by_category")) if isinstance(summary.get("by_category"), dict) else {}
    total_findings_test = int(summary.get("total_findings_test", 0) or 0)
    total_findings_non_test = int(summary.get("total_findings_non_test", 0) or 0)
    module_scope_non_test = int(summary.get("module_scope_non_test", 0) or 0)
    metrics: dict[str, object] = {
        "files_scanned": int(payload_obj.get("files_scanned", 0) or 0),
        "files_with_findings": int(payload_obj.get("files_with_findings", 0) or 0),
        "total_findings": int(payload_obj.get("total_findings", 0) or 0),
        "total_findings_test": total_findings_test,
        "total_findings_non_test": total_findings_non_test,
        "module_scope_non_test": module_scope_non_test,
        "parse_errors": int(payload_obj.get("parse_errors", 0) or 0),
        "duration_ms": int(payload_obj.get("duration_ms", 0) or 0),
        "findings_by_category": by_category,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "generated_at": generated_at,
        "status": manifest.get("status", "unknown") if isinstance(manifest, dict) else "unknown",
        "metrics": metrics,
        "inputs": manifest.get("inputs", {}) if isinstance(manifest.get("inputs"), dict) else {},
    }


def render_summary_markdown(manifest: dict[str, object]) -> str:
    """Render a markdown summary from the manifest.

    Generate a human-readable report with findings breakdown,
    top affected files, and recommended next steps.

    Args:
        manifest: Complete manifest dictionary from compose_manifest.

    Returns:
        Markdown-formatted summary string.
    """
    payload_obj = cast(dict[str, Any], manifest.get("payload")) if isinstance(manifest.get("payload"), dict) else {}
    summary = cast(dict[str, Any], payload_obj.get("summary")) if isinstance(payload_obj.get("summary"), dict) else {}
    by_category = cast(dict[str, Any], summary.get("by_category")) if isinstance(summary.get("by_category"), dict) else {}
    by_category_test = (
        cast(dict[str, Any], summary.get("by_category_test")) if isinstance(summary.get("by_category_test"), dict) else {}
    )
    by_category_non_test = (
        cast(dict[str, Any], summary.get("by_category_non_test"))
        if isinstance(summary.get("by_category_non_test"), dict)
        else {}
    )
    by_import_base = cast(dict[str, Any], summary.get("by_import_base")) if isinstance(summary.get("by_import_base"), dict) else {}
    top_files = cast(list[object], summary.get("top_files")) if isinstance(summary.get("top_files"), list) else []

    total_findings_test = int(summary.get("total_findings_test", 0) or 0)
    total_findings_non_test = int(summary.get("total_findings_non_test", 0) or 0)
    module_scope_non_test = int(summary.get("module_scope_non_test", 0) or 0)
    top_files_test = cast(list[object], summary.get("top_files_test")) if isinstance(summary.get("top_files_test"), list) else []
    top_files_non_test = (
        cast(list[object], summary.get("top_files_non_test")) if isinstance(summary.get("top_files_non_test"), list) else []
    )

    inputs_obj = cast(dict[str, Any], manifest.get("inputs")) if isinstance(manifest.get("inputs"), dict) else {}
    keep_value = inputs_obj.get("keep")

    def _display_path(value: str) -> str:
        return value.replace("\\", "/")

    def _escape_table_cell(value: str) -> str:
        sanitized = value.replace("\n", " ").replace("\r", " ")
        return sanitized.replace("|", "\\|")

    def _truncate_middle(value: str, max_len: int) -> str:
        if max_len <= 0:
            return ""

        text = _display_path(value)
        if len(text) <= max_len:
            return text

        if max_len < 10:
            return text[:max_len]

        left_len = (max_len - 1) // 2
        right_len = max_len - 1 - left_len
        return f"{text[:left_len]}…{text[-right_len:]}"

    def _format_path_for_table(value: str, max_len: int = 72) -> str:
        path = value.strip()
        if not path:
            return "-"
        return _escape_table_cell(_truncate_middle(path, max_len))

    lines = [
        "# Monkey Patch Scan Report\n\n",
        f"- Status: `{manifest.get('status', 'unknown')}`\n",
        f"- Run timestamp (UTC): `{manifest.get('run_timestamp', '')}`\n",
        f"- Scan Root: `{payload_obj.get('scan_root', '.')}`\n",
        f"- Files Scanned: {payload_obj.get('files_scanned', 0)}\n",
        f"- Files With Findings: {payload_obj.get('files_with_findings', 0)}\n",
        f"- Total Findings: {payload_obj.get('total_findings', 0)}\n",
        f"- Findings (non-test): {total_findings_non_test}\n",
        f"- Findings (tests): {total_findings_test}\n",
        f"- Module-scope findings (non-test): {module_scope_non_test}\n",
        f"- Parse Errors: {payload_obj.get('parse_errors', 0)}\n",
    ]

    if keep_value is not None:
        lines.append(f"- Retention (keep): {keep_value}\n")

    lines.append("\n")

    lines.append("## Artifacts\n\n")
    lines.append("- `manifest.json` (full findings + inputs)\n")
    lines.append("- `telemetry.json` (thin metrics for dashboards)\n")
    lines.append("- `summary.md` (this file)\n\n")

    lines.append("## Risk Highlights\n\n")
    lines.append("- Focus first on non-test module-scope findings and `sys_modules_assignment` outside tests.\n")
    lines.append("- Test-only patches are often acceptable when scoped and justified.\n\n")

    if by_category:
        lines.append("## Findings by Category\n\n")
        lines.append("| Category | Count |\n| --- | ---: |\n")
        for category, count in sorted(by_category.items(), key=lambda item: item[0]):
            lines.append(f"| {category} | {count} |\n")
        lines.append("\n")

    if by_category_non_test:
        lines.append("## Findings by Category (Non-Test)\n\n")
        lines.append("| Category | Count |\n| --- | ---: |\n")
        for category, count in sorted(by_category_non_test.items(), key=lambda item: item[0]):
            lines.append(f"| {category} | {count} |\n")
        lines.append("\n")

    if by_category_test:
        lines.append("## Findings by Category (Tests)\n\n")
        lines.append("| Category | Count |\n| --- | ---: |\n")
        for category, count in sorted(by_category_test.items(), key=lambda item: item[0]):
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
        lines.append("- Full file paths live in `manifest.json` under `payload.summary.top_files`.\n\n")
        lines.append("| File | Count |\n| --- | ---: |\n")
        for entry in top_files:
            if not isinstance(entry, dict):
                continue
            lines.append(f"| {_format_path_for_table(str(entry.get('path', '')))} | {entry.get('count', 0)} |\n")
        lines.append("\n")

    if top_files_non_test:
        lines.append("## Top Non-Test Files\n\n")
        lines.append("- Full file paths live in `manifest.json` under `payload.summary.top_files_non_test`.\n\n")
        lines.append("| File | Count |\n| --- | ---: |\n")
        for entry in top_files_non_test:
            if not isinstance(entry, dict):
                continue
            lines.append(f"| {_format_path_for_table(str(entry.get('path', '')))} | {entry.get('count', 0)} |\n")
        lines.append("\n")

    if top_files_test:
        lines.append("## Top Test Files\n\n")
        lines.append("- Full file paths live in `manifest.json` under `payload.summary.top_files_test`.\n\n")
        lines.append("| File | Count |\n| --- | ---: |\n")
        for entry in top_files_test:
            if not isinstance(entry, dict):
                continue
            lines.append(f"| {_format_path_for_table(str(entry.get('path', '')))} | {entry.get('count', 0)} |\n")
        lines.append("\n")

    lines.append("## Next Steps\n\n")
    lines.append("- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.\n")
    lines.append("- [ ] Replace module-scope patches with context-managed patches in tests.\n")
    lines.append("- [ ] Isolate import-time overrides behind flags or dependency injection.\n")
    lines.append("- [ ] Add targeted tests for any retained patches with clear rationale.\n")
    return "".join(lines)


def write_bundle(
    *,
    output_dir: Path,
    run_timestamp: str,
    manifest: dict[str, object],
    telemetry: dict[str, object],
    summary_markdown: str,
    keep: int,
    logger: logging.Logger,
) -> Path:
    """Write scan bundle artifacts to disk.

    Create the timestamped output directory and write manifest,
    telemetry, and summary files. Prune old run directories.

    Args:
        output_dir: Base output directory for bundles.
        run_timestamp: Formatted timestamp for directory naming.
        manifest: Complete manifest dictionary.
        telemetry: Telemetry dictionary for metrics.
        summary_markdown: Rendered markdown summary.
        keep: Number of run directories to retain.
        logger: Logger for pruning messages.

    Returns:
        Path to the created bundle directory.
    """
    storage = create_storage(output_dir, "", "", timestamp=run_timestamp)
    bundle_dir = output_dir / run_timestamp

    # DB_INTEGRATION_MARKER: Persist manifest bundle (report_runs + report_artifacts)
    storage.write_manifest(manifest)
    # DB_INTEGRATION_MARKER: Persist human-readable report summary (report_artifacts)
    storage.write_summary({"markdown": summary_markdown}, format="md")
    # DB_INTEGRATION_MARKER: Persist telemetry payload + extracted metrics (report_artifacts + test_metrics)
    storage.write_telemetry(telemetry)

    base_dir = output_dir
    prune_run_directories(
        base_dir,
        keep=max(1, keep),
        current_run=bundle_dir,
        logger=logger,
    )

    return bundle_dir


def scan_repository(paths: Paths, options: ScanOptions) -> tuple[list[Finding], int, int]:
    """Scan all Python files in the repository for monkey patches.

    Iterate over files, scan each one, and aggregate findings.
    Skip the scanner script itself to avoid self-detection.

    Args:
        paths: Resolved path configuration.
        options: Scan options controlling behavior.

    Returns:
        Tuple of (findings list, files scanned count, parse error count).
    """
    findings: list[Finding] = []
    parse_errors = 0
    files_scanned = 0
    for file in iter_python_files(paths.scan_root, paths.repo_root, options.exclude_dirs, options.exclude_globs):
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
    """Run internal self-test to validate scanner detection.

    Create temporary sample files covering major monkey patch
    categories and verify the scanner detects each one.

    Args:
        verbose: If True, log detailed self-test progress.

    Returns:
        Exit code: 0 on success, 2 if expected categories are missing.
    """
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
            logging.debug("[SELF-TEST] OK — %d findings across %d files", len(findings), len(sample_files))
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Configure the argument parser with all scanner options and
    parse the provided argument list.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Parsed namespace with all configuration options.
    """
    parser = argparse.ArgumentParser(
        description="Scan repository sources for monkey patches and emit structured artifacts."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Directory to scan relative to the repo root (defaults to the repo root)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Override for artifact output directory (defaults to .repo_studios/reports/producer_reports)",
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
    parser.add_argument("--with-git", action="store_true", help="Include git blame metadata where available")
    parser.add_argument("--strict", action="store_true", help="Treat parse errors as fatal (after scanning)")
    parser.add_argument(
        "--keep",
        "--artifacts-to-keep",
        dest="keep",
        type=int,
        default=DEFAULT_KEEP,
        help="Number of historical run directories to retain (minimum 1)",
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="Override run timestamp slug (UTC) in YYYYMMDD-HHMM format (used for deterministic testing)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity",
    )
    parser.add_argument("--self-test", action="store_true", help="Run the built-in scanner self-test and exit")
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    """Configure the logging subsystem.

    Set up basic logging with the specified verbosity level.

    Args:
        level: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def build_paths(args: argparse.Namespace) -> Paths:
    """Build resolved path configuration from CLI arguments.

    Use the standard path builder with the scanner's path configuration.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Resolved Paths dataclass with repo root, scan root, and output dir.
    """
    return cast(Paths, build_standard_paths(args, PATH_CONFIG, origin=Path(__file__)))


def run(argv: list[str] | None = None) -> dict[str, object]:
    """Execute the monkey patch scanner and produce artifacts.

    Parse arguments, run the scan, compose artifacts, and write
    the output bundle to disk.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Result dictionary with status, run timestamp, and findings count.
    """
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
        set(args.project_packages) if args.project_packages else top_level_packages_default(paths.repo_root)
    )
    exclude_dirs = set(args.exclude_dirs) if args.exclude_dirs is not None else set(DEFAULT_EXCLUDES)
    exclude_globs = set(args.exclude_globs) if args.exclude_globs is not None else set(DEFAULT_EXCLUDE_GLOBS)
    resolved_options = build_standard_options(args, OPTIONS_CONFIG)

    options = ScanOptions(
        project_packages=project_packages,
        exclude_dirs=exclude_dirs,
        exclude_globs=exclude_globs,
        context_lines=int(args.context_lines),
        with_git=bool(args.with_git),
        strict=bool(args.strict),
        keep=resolved_options.keep,
    )

    logger = logging.getLogger(__name__)

    logger.info("Scanning repo: %s", paths.repo_root)
    logger.info("Scan root: %s", paths.scan_root)
    logger.info("Output directory: %s", paths.output_dir)
    logger.info("Project packages: %s", ", ".join(sorted(options.project_packages)))

    started = time.perf_counter()
    findings, parse_errors, files_scanned = scan_repository(paths, options)
    augment_findings_with_git(findings, paths.repo_root, options.with_git)
    duration_ms = int((time.perf_counter() - started) * 1000)

    now = dt.datetime.now(dt.UTC)
    run_timestamp = _resolve_run_timestamp(override=args.timestamp, now=now)
    bundle_dir = paths.output_dir / run_timestamp
    generated_at = now.isoformat()

    manifest = compose_manifest(
        paths=paths,
        options=options,
        findings=findings,
        timestamp=now,
        run_timestamp=run_timestamp,
        generated_at=generated_at,
        bundle_dir=bundle_dir,
        files_scanned=files_scanned,
        parse_errors=parse_errors,
        duration_ms=duration_ms,
    )
    telemetry = compose_telemetry(manifest=manifest, run_timestamp=run_timestamp, generated_at=generated_at)
    summary_markdown = render_summary_markdown(manifest)

    run_dir = write_bundle(
        output_dir=paths.output_dir,
        run_timestamp=run_timestamp,
        manifest=manifest,
        telemetry=telemetry,
        summary_markdown=summary_markdown,
        keep=options.keep,
        logger=logger,
    )

    logger.info("Done. Findings: %d", len(findings))
    if parse_errors:
        log_fn = logger.error if options.strict else logger.warning
        log_fn("%d file(s) failed to parse.", parse_errors)

    total_findings = 0
    payload_obj = manifest.get("payload")
    if isinstance(payload_obj, dict):
        total_findings = int(payload_obj.get("total_findings", 0) or 0)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": manifest.get("status", "unknown"),
        "viewer": "healthview",
        "topic": TOPIC_SLUG,
        "run_timestamp": run_timestamp,
        "run_dir": str(run_dir),
        "total_findings": total_findings,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the monkey patch scanner.

    Run the scanner and return an appropriate exit code based
    on the result status.

    Args:
        argv: Command-line arguments or None for sys.argv.

    Returns:
        Exit code: 0 on success, 1 on error, or self-test result code.
    """
    payload: dict[str, object] = run(argv)
    status = payload.get("status")
    if status in {"self-test", "self-test-failed"}:
        exit_code = payload.get("exit_code", 0)
        if isinstance(exit_code, int):
            return exit_code
        if isinstance(exit_code, str) and exit_code.isdigit():
            return int(exit_code)
        return 0
    if status == "error":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
