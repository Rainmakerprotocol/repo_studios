import argparse
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# === Configuration ===
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Default target (backward compatible): limit scope to storage cleanup
DEFAULT_TARGET = str(PROJECT_ROOT / "metrics_storage" / "storage")
CLEAN_LOG_DIR = PROJECT_ROOT / ".repo_studios" / "cleanup_logs"
CLEAN_LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = CLEAN_LOG_DIR / f"clean_{datetime.now().strftime('%Y-%m-%d_%H%M')}.txt"
RUFF_CONFIG = str(PROJECT_ROOT / ".repo_studios" / "ruff_clean.toml")
BACKUP = False  # Set True to copy original files before modifying

# Optional mode to run only a subset of checks (e.g., 'markdown')
RUN_MODE = os.getenv("BATCH_CLEAN_ONLY", "all").lower()

# Markdown lint configuration
MARKDOWNLINT_CONFIG = ".markdownlint.json"
MARKDOWN_GLOB = "**/*.md"


# === Commands Used (Ruff is SSOT; Black not used in repo) ===
def ruff_format_cmd(targets: list[str]) -> list[str]:
    return [
        "ruff",
        "format",
        *targets,
        "--config",
        RUFF_CONFIG,
    ]


def ruff_fix_cmd(targets: list[str]) -> list[str]:
    return [
        "ruff",
        "check",
        *targets,
        "--fix",
        "--config",
        RUFF_CONFIG,
    ]


MYPY = ["mypy", "agents/core/monitoring", "agents/interface/chainlit"]
PYTEST = ["pytest", "-q"]

# Prefer npx to avoid global install; fallback to markdownlint if available
MARKDOWNLINT_FIX = [
    "npx",
    "--yes",
    "markdownlint-cli@0.39.0",
    MARKDOWN_GLOB,
    "--fix",
    "--config",
    MARKDOWNLINT_CONFIG,
]
MARKDOWNLINT_CHECK = [
    "npx",
    "--yes",
    "markdownlint-cli@0.39.0",
    MARKDOWN_GLOB,
    "--config",
    MARKDOWNLINT_CONFIG,
]


# === Helpers ===
DRY_RUN = False


def run_command(cmd: list[str], label: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n--- Running: {label} ---\n")
        if DRY_RUN:
            log.write("[dry-run] " + " ".join(cmd) + "\n")
            result = None
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
            log.write(result.stdout)
            log.write(result.stderr)
        import logging

        logging.info(f"[✓] {label} {'(dry-run)' if DRY_RUN else 'complete'}")


def backup_files(targets: list[str]) -> None:
    import shutil

    for target in targets:
        if os.path.isfile(target):
            if target.endswith(".py"):
                shutil.copy2(target, target + ".bak")
            continue
        for root, _, files in os.walk(target):
            for file in files:
                if file.endswith(".py"):
                    src = os.path.join(root, file)
                    dst = os.path.join(root, file + ".bak")
                    shutil.copy2(src, dst)
    import logging

    logging.info("[✓] Backup of .py files complete")


def run_markdownlint() -> None:
    """Run markdownlint fix and check if tooling is available."""
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write("\n--- Running: Markdownlint (Markdown formatting/lint) ---\n")

    def _run(cmd: list[str], label: str) -> None:
        run_command(cmd, label)

    # Try npx first
    if shutil.which("npx"):
        _run(MARKDOWNLINT_FIX, "markdownlint --fix (via npx)")
        _run(MARKDOWNLINT_CHECK, "markdownlint check (via npx)")
        return

    # Fallback to globally installed markdownlint if present
    if shutil.which("markdownlint"):
        _run(
            [
                "markdownlint",
                MARKDOWN_GLOB,
                "--fix",
                "--config",
                MARKDOWNLINT_CONFIG,
            ],
            "markdownlint --fix (global)",
        )
        _run(
            [
                "markdownlint",
                MARKDOWN_GLOB,
                "--config",
                MARKDOWNLINT_CONFIG,
            ],
            "markdownlint check (global)",
        )
        return

    import logging as _logging

    _logging.info(
        "[i] Skipping markdownlint (npx/markdownlint not found). "
        "Install Node or markdownlint-cli to enable."
    )


def refresh_project_tree(
    md_file: Path,
    root_dir: Path,
    max_depth: int = 3,
    exclude: tuple[str, ...] = ("__pycache__", "z_FUTURE_IMPIMENTATIONS", "logs"),
) -> None:
    """Regenerate the folder tree block between markers in the given markdown file.

    The block is delimited by:
      <!-- tree:begin -->
      ```text
      ...
      ```
      <!-- tree:end -->

    Args:
      md_file: Markdown file path containing the markers.
      root_dir: Project root to scan.
      max_depth: Maximum directory depth to render.
      exclude: Directory names to exclude (top-level match).
    """

    def _is_excluded(path: Path) -> bool:
        parts = set(path.parts)
        return any(e in parts for e in exclude)

    def _children(d: Path) -> list[Path]:
        try:
            return sorted([p for p in d.iterdir() if not p.name.startswith(".")])
        except Exception:
            return []

    def _render_tree(dir_path: Path, depth: int, prefix: str = "") -> list[str]:
        if depth > max_depth:
            return []
        lines: list[str] = []
        if depth == 0:
            lines.append(f"{dir_path.name}/")
        entries = [p for p in _children(dir_path) if not _is_excluded(p)]
        dirs = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]
        # Limit root files to a small set for signal
        root_files = {
            "README.md",
            "pyproject.toml",
            "ruff.toml",
            "pytest.ini",
            "requirements-dev.txt",
        }
        if depth == 0 and files:
            for f in files:
                if f.name in root_files:
                    lines.append(f"├── {f.name}")
        # Render directories
        for i, d in enumerate(dirs):
            connector = "└──" if i == len(dirs) - 1 and depth > 0 else "├──"
            lines.append(f"{prefix}{connector} {d.name}/")
            child_prefix = prefix + ("    " if connector == "└──" else "│   ")
            lines.extend(_render_tree(d, depth + 1, child_prefix))
        return lines

    if not md_file.exists():
        import logging as _logging

        _logging.info(f"[i] Tree refresh skipped (missing): {md_file}")
        return

    text = md_file.read_text(encoding="utf-8")
    start = text.find("<!-- tree:begin -->")
    end = text.find("<!-- tree:end -->")
    if start == -1 or end == -1 or end < start:
        import logging as _logging

        _logging.info("[i] Tree markers not found; skipping refresh")
        return

    lines = _render_tree(root_dir, 0)
    body = "\n".join(lines) + "\n"
    # Include a timestamp so the block visibly updates each run
    stamp = datetime.now().strftime("%m/%d/%Y_%H:%M:%S")
    block = f"<!-- tree:begin -->\nUpdated: {stamp}\n```text\n{body}```\n<!-- tree:end -->"

    # Replace existing block, preserving surrounding content
    pattern = re.compile(
        r"<!-- tree:begin -->[\s\S]*?<!-- tree:end -->",
        flags=re.MULTILINE,
    )
    new_text = pattern.sub(block, text)
    if new_text != text:
        md_file.write_text(new_text, encoding="utf-8")
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write("\n--- Running: Refresh project tree block ---\n")
            log.write(f"Refreshed tree for: {root_dir} at {stamp}\n")
    else:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write("\n--- Running: Refresh project tree block ---\n")
            log.write("No changes in tree block.\n")


# === Main Cleanup Routine ===
if __name__ == "__main__":
    import logging

    # CLI: point-and-shoot targets and options
    parser = argparse.ArgumentParser(
        description=("Point-and-shoot repository cleaner (Ruff/Mypy/Pytest/Markdown)")
    )
    parser.add_argument(
        "-t",
        "--target",
        dest="targets",
        action="append",
        help="File or directory to clean (repeatable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands without executing them",
    )
    parser.add_argument(
        "--mode",
        choices=["all", "markdown"],
        default=os.getenv("BATCH_CLEAN_ONLY", RUN_MODE),
        help="Cleanup mode",
    )
    parser.add_argument("--backup", action="store_true", help="Backup .py files before modifying")
    parser.add_argument(
        "--refresh-only",
        action="store_true",
        help="Only refresh the project tree block and exit",
    )
    parser.add_argument(
        "--no-pytest",
        action="store_true",
        help="Skip running pytest as part of cleanup (useful for orchestrators that run tests separately)",
    )
    args = parser.parse_args()

    # Resolve targets: CLI > env > default
    env_targets = os.getenv("BATCH_CLEAN_TARGET_DIR") or os.getenv("BATCH_CLEAN_TARGETS")
    targets: list[str] = []
    if args.targets:
        targets = args.targets
    elif env_targets:
        targets = [t.strip() for t in env_targets.split(",") if t.strip()]
    else:
        targets = [DEFAULT_TARGET]

    # Normalize relative paths against PROJECT_ROOT and ensure existence
    norm_targets: list[str] = []
    for t in targets:
        p = Path(t)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        norm_targets.append(str(p))

    # Set globals from CLI
    DRY_RUN = bool(args.dry_run)
    mode = args.mode
    do_backup = bool(args.backup) or BACKUP

    logging.basicConfig(level=logging.INFO)
    logging.info("🚀 Batch Cleanup Started...")
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(
            "# 🧼 repo Cleanup Log\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Targets: {', '.join(norm_targets)}\n"
            f"Mode: {mode}{' (dry-run)' if DRY_RUN else ''}\n\n"
        )

    if do_backup:
        backup_files(norm_targets)

    # Refresh the project tree in standards doc before any other actions
    standards_doc = PROJECT_ROOT / ".repo_studios" / "repo_standards_project.md"
    refresh_project_tree(standards_doc, PROJECT_ROOT)

    # If requested, stop after tree refresh
    if args.refresh_only:
        logging.info("✅ Tree refresh complete. Exiting as requested (--refresh-only).")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n[i] Exited after tree refresh due to --refresh-only flag.\n")
        raise SystemExit(0)

    if mode == "markdown":
        run_markdownlint()
        logging.info(f"✅ Markdown-only cleanup complete. See {LOG_FILE} for details.")
    else:
        # Ruff on chosen targets
        run_command(ruff_format_cmd(norm_targets), "Ruff format (PEP8-aligned formatting)")
        run_command(ruff_fix_cmd(norm_targets), "Ruff check --fix")
        # Repo-wide (kept as-is)
        run_markdownlint()
        run_command(MYPY, "Mypy (type checking on gated packages)")
        if not args.no_pytest and os.getenv("BATCH_CLEAN_NO_PYTEST", "0") != "1":
            run_command(PYTEST, "Pytest (run tests)")
        else:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(
                    "\n[i] Skipping pytest as requested (--no-pytest or BATCH_CLEAN_NO_PYTEST=1).\n"
                )

    logging.info(f"✅ Cleanup complete. See {LOG_FILE} for details.")
