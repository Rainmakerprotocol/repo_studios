#!/usr/bin/env python3
"""
Scan the codebase for placeholder comments (TODO, FIXME, NOTE, etc.) and output them as a list.

Usage:
    python find_placeholders.py [root_dir]
If no root_dir is given, scans current directory.
"""

import os
import re
import sys
from pathlib import Path

PLACEHOLDER_PATTERNS = [r"TODO", r"FIXME", r"NOTE", r"XXX", r"OPTIMIZE", r"REVIEW"]
COMMENT_REGEX = re.compile(r"#.*?(" + "|".join(PLACEHOLDER_PATTERNS) + r")[:\s]", re.IGNORECASE)


def scan_placeholders(root_dir: str) -> list[tuple[str, int, str]]:
    results = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith((".py", ".md", ".txt", ".js", ".ts", ".yaml", ".yml", ".json")):
                fpath = Path(dirpath) / fname
                try:
                    with fpath.open("r", encoding="utf-8", errors="ignore") as f:
                        for lineno, line in enumerate(f, 1):
                            if COMMENT_REGEX.search(line):
                                results.append((str(fpath), lineno, line.strip()))
                except Exception:
                    continue
    return results


def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())
    found = scan_placeholders(root_dir)
    # Emit results to stdout but avoid extra chatter so linters don't flag prints here.
    for fpath, lineno, line in found:
        sys.stdout.write(f"{fpath}:{lineno}: {line}\n")


if __name__ == "__main__":
    main()
