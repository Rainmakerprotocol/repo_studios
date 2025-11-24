#!/usr/bin/env python3
"""Generate selector.json for the Command Center viewer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from command_center.viewer.refresh import refresh_selector_payload
except ModuleNotFoundError:  # pragma: no cover - path fix only for direct script execution
    script_path = Path(__file__).resolve()
    package_root = script_path.parents[2]
    if str(package_root) not in sys.path:
        sys.path.append(str(package_root))
    from command_center.viewer.refresh import refresh_selector_payload


def generate_selector_json(
    repo_root: Path | None = None,
    output_path: Path | None = None,
) -> None:
    """
    Generate selector.json file for the viewer.

    Args:
        repo_root: Path to repository root (default: auto-detect)
        output_path: Where to write selector.json (default: reports/selector.json)
    """
    if repo_root is None:
        # Auto-detect repo root from this script's location
        # viewer/generate_selector.py -> viewer -> command_center -> .repo_studios -> repo_root
        repo_root = Path(__file__).parent.parent.parent.parent

    if output_path is None:
        # Default: write to reports directory
        output_path = repo_root / ".repo_studios" / "command_center" / "reports" / "selector.json"

    print(f"Generating selector data from: {repo_root}")

    # Use the refresh module to build selector payload
    payload = refresh_selector_payload(repo_root)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write selector.json
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    entry_count = len(payload.get("entries", []))
    print(f"✓ Generated selector.json with {entry_count} artifact groups")
    print(f"✓ Written to: {output_path}")

    # Also print summary
    for entry in payload.get("entries", []):
        slug = entry.get("slug", "unknown")
        option_count = len(entry.get("options", []))
        print(f"  - {slug}: {option_count} artifact(s)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate selector.json for Command Center viewer")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Path to repository root (default: auto-detect)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for selector.json (default: reports/selector.json)",
    )

    args = parser.parse_args()
    generate_selector_json(repo_root=args.repo_root, output_path=args.output)
