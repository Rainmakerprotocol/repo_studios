#!/usr/bin/env python3
"""
Best-effort: dump all Python thread stacks once to stderr if faulthandler is enabled.
Exits 0 regardless of outcome to avoid masking original CI failures.
Cross-platform: no signals used; imports stdlib only.
"""

from __future__ import annotations

import sys
from contextlib import suppress


def main() -> int:
    with suppress(Exception):
        import faulthandler  # type: ignore

        # If not enabled yet, enable with default destination. We intentionally
        # avoid passing a file handle so that, when the bootstrap configured a
        # custom writer (e.g., stacks.log), faulthandler continues to use it.
        try:
            if getattr(faulthandler, "is_enabled", lambda: False)():
                pass
            else:
                with suppress(Exception):
                    faulthandler.enable(all_threads=True)
        except Exception:
            pass
        # One-time dump (no explicit file to honor configured writer)
        with suppress(Exception):
            faulthandler.dump_traceback(all_threads=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
