#!/usr/bin/env python3
"""List all DB_INTEGRATION_MARKER locations for tracking integration progress.

DB_INTEGRATION_MARKER: This utility helps track which scripts have been
instrumented with database integration stubs.

Usage:
    python list_db_markers.py [--output markers.csv] [--format csv|json|md]
    
Output formats:
    - CSV: Easy import into spreadsheets for project tracking
    - JSON: Machine-readable for automation
    - Markdown: Human-readable checklist format
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from libraries.cli import resolve_repo_root  # noqa: E402

logger = logging.getLogger(__name__)


@dataclass
class DBMarker:
    """Single DB_INTEGRATION_MARKER occurrence."""
    file_path: str
    line_number: int
    marker_text: str
    context: str  # Surrounding code for understanding
    marker_type: str  # code, comment, docstring


@dataclass
class ScriptStatus:
    """Integration status for a single script."""
    script_path: str
    tier: str  # producer, consumer, aggregator, orchestrator, summarizer, utility
    marker_count: int
    has_import: bool
    has_storage_init: bool
    has_writes: bool
    markers: list[DBMarker]


def find_markers_in_file(file_path: Path, repo_root: Path) -> list[DBMarker]:
    """Find all DB_INTEGRATION_MARKER occurrences in a file."""
    markers = []
    
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return markers
    
    # Pattern to match DB_INTEGRATION_MARKER with optional colon and description
    pattern = re.compile(r"DB_INTEGRATION_MARKER:?\s*(.*)")
    
    # Get relative path safely
    try:
        rel_path = str(file_path.relative_to(repo_root))
    except ValueError:
        rel_path = str(file_path)
    
    for i, line in enumerate(lines, start=1):
        match = pattern.search(line)
        if match:
            description = match.group(1).strip()
            
            # Determine marker type
            if '"""' in line or "'''" in line:
                marker_type = "docstring"
            elif line.strip().startswith("#"):
                marker_type = "comment"
            else:
                marker_type = "code"
            
            # Get context (3 lines before and after)
            start_idx = max(0, i - 4)
            end_idx = min(len(lines), i + 3)
            context = "\n".join(lines[start_idx:end_idx])
            
            markers.append(DBMarker(
                file_path=rel_path,
                line_number=i,
                marker_text=description or "(no description)",
                context=context,
                marker_type=marker_type,
            ))
    
    return markers


def analyze_script_status(file_path: Path, markers: list[DBMarker], repo_root: Path) -> ScriptStatus:
    """Analyze a script's integration status based on markers and code patterns."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        content = ""
    
    # Determine tier from path
    tier = "unknown"
    path_str = str(file_path).replace("\\", "/")
    if "/producers/" in path_str:
        tier = "producer"
    elif "/consumers/" in path_str:
        tier = "consumer"
    elif "/aggregators/" in path_str:
        tier = "aggregator"
    elif "/orchestrators/" in path_str:
        tier = "orchestrator"
    elif "/summarizers/" in path_str:
        tier = "summarizer"
    elif "/utilities/" in path_str or "/libraries/" in path_str:
        tier = "utility"
    
    # Check for integration milestones
    has_import = (
        "from command_center.scripts.libraries.database_integration import" in content
        or "from libraries.database_integration import" in content
        or "import database_integration" in content
    )
    has_storage_init = "create_storage(" in content or \
                       "DualWriteStorage(" in content
    has_writes = "storage.write_" in content
    
    # Get relative path safely
    try:
        relative_path = str(file_path.relative_to(repo_root))
    except ValueError:
        relative_path = str(file_path)
    
    return ScriptStatus(
        script_path=relative_path,
        tier=tier,
        marker_count=len(markers),
        has_import=has_import,
        has_storage_init=has_storage_init,
        has_writes=has_writes,
        markers=markers,
    )


def scan_repository(root: Path) -> dict[str, ScriptStatus]:
    """Scan repository for all Python files with DB markers."""
    script_status = {}
    
    # Focus on command center scripts
    search_dirs = [
        root / ".repo_studios" / "command_center" / "scripts",
        root / ".repo_studios" / "scripts",
    ]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for py_file in search_dir.rglob("*.py"):
            # Skip __pycache__ and test files
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue
            
            markers = find_markers_in_file(py_file, root)
            
            # Only include files with markers or potential integration candidates
            if markers or py_file.name.endswith((".py",)):
                status = analyze_script_status(py_file, markers, root)
                try:
                    script_status[str(py_file.relative_to(root))] = status
                except ValueError:
                    # Path not under root, use absolute path
                    script_status[str(py_file)] = status
    
    return script_status


def format_csv(statuses: dict[str, ScriptStatus], output_path: Path) -> None:
    """Output status as CSV for spreadsheet tracking."""
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Script Path",
            "Tier",
            "Marker Count",
            "Has Import",
            "Has Storage Init",
            "Has Writes",
            "Integration Status",
            "Sample Marker",
        ])
        
        for script_path, status in sorted(statuses.items()):
            if status.marker_count == 0:
                continue  # Skip files without markers for CSV
            
            # Determine overall status
            if status.has_import and status.has_storage_init and status.has_writes:
                integration_status = "Complete"
            elif status.has_import:
                integration_status = "In Progress"
            elif status.marker_count > 0:
                integration_status = "Documented"
            else:
                integration_status = "Not Started"
            
            sample_marker = status.markers[0].marker_text if status.markers else ""
            
            writer.writerow([
                status.script_path,
                status.tier,
                status.marker_count,
                status.has_import,
                status.has_storage_init,
                status.has_writes,
                integration_status,
                sample_marker[:100],  # Truncate
            ])
    

    logger.info(f"CSV report written to {output_path}")


def format_json(statuses: dict[str, ScriptStatus], output_path: Path) -> None:
    """Output status as JSON for automation."""
    output_data = {
        "summary": {
            "total_scripts": len(statuses),
            "scripts_with_markers": sum(1 for s in statuses.values() if s.marker_count > 0),
            "complete_integrations": sum(
                1 for s in statuses.values()
                if s.has_import and s.has_storage_init and s.has_writes
            ),
            "in_progress": sum(1 for s in statuses.values() if s.has_import),
        },
        "scripts": {
            path: {
                "tier": status.tier,
                "marker_count": status.marker_count,
                "has_import": status.has_import,
                "has_storage_init": status.has_storage_init,
                "has_writes": status.has_writes,
                "markers": [
                    {
                        "line": m.line_number,
                        "text": m.marker_text,
                        "type": m.marker_type,
                    }
                    for m in status.markers
                ],
            }
            for path, status in statuses.items()
            if status.marker_count > 0
        },
    }
    
    output_path.write_text(json.dumps(output_data, indent=2), encoding="utf-8")
    logger.info(f"JSON report written to {output_path}")


def format_markdown(statuses: dict[str, ScriptStatus], output_path: Path) -> None:
    """Output status as Markdown checklist."""
    lines = [
        "# Database Integration Status",
        "",
        "**DB_INTEGRATION_MARKER scan results**",
        "",
        f"**Total scripts scanned:** {len(statuses)}",
        f"**Scripts with markers:** {sum(1 for s in statuses.values() if s.marker_count > 0)}",
        "",
    ]
    
    # Group by tier
    by_tier: dict[str, list[ScriptStatus]] = defaultdict(list)
    for status in statuses.values():
        if status.marker_count > 0:  # Only include marked scripts
            by_tier[status.tier].append(status)
    
    for tier in ["producer", "consumer", "aggregator", "orchestrator", "summarizer", "utility"]:
        scripts = by_tier.get(tier, [])
        if not scripts:
            continue
        
        lines.append(f"## {tier.capitalize()} Scripts")
        lines.append("")
        
        for status in sorted(scripts, key=lambda s: s.script_path):
            # Determine checkbox state
            if status.has_import and status.has_storage_init and status.has_writes:
                checkbox = "[x]"
            elif status.has_import:
                checkbox = "[~]"  # In progress
            else:
                checkbox = "[ ]"
            
            lines.append(f"{checkbox} **{Path(status.script_path).name}**")
            lines.append(f"   - Path: `{status.script_path}`")
            lines.append(f"   - Markers: {status.marker_count}")
            lines.append(f"   - Import: {'✓' if status.has_import else '✗'}")
            lines.append(f"   - Storage init: {'✓' if status.has_storage_init else '✗'}")
            lines.append(f"   - Write calls: {'✓' if status.has_writes else '✗'}")
            
            # Show first marker
            if status.markers:
                first_marker = status.markers[0]
                lines.append(f"   - First marker (L{first_marker.line_number}): {first_marker.marker_text}")
            
            lines.append("")
    
    # Summary checklist
    lines.extend([
        "## Integration Checklist",
        "",
        "Legend:",
        "- `[ ]` Not started (markers only)",
        "- `[~]` In progress (import added)",
        "- `[x]` Complete (import + storage + writes)",
        "",
    ])
    
    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Markdown report written to {output_path}")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="List all DB_INTEGRATION_MARKER locations in the repository"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout for md, markers.csv for csv, markers.json for json)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "md"],
        default="md",
        help="Output format (default: md)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "Repository root. If omitted, auto-discovers by scanning parents for the '.repo_studios' marker "
            "directory (origin: this script)."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    
    args = parser.parse_args(argv)

    repo_root = resolve_repo_root(args.repo_root, origin=Path(__file__))
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s: %(message)s",
    )
    
    # Default output paths
    if args.output is None:
        if args.format == "csv":
            args.output = Path("db_integration_markers.csv")
        elif args.format == "json":
            args.output = Path("db_integration_markers.json")
        else:  # md
            args.output = Path("db_integration_status.md")

    if not args.output.is_absolute():
        args.output = (repo_root / args.output).resolve()
    
    logger.info(f"Scanning repository at {repo_root}")
    statuses = scan_repository(repo_root)
    
    logger.info(f"Found {len(statuses)} scripts")
    logger.info(
        f"Scripts with markers: {sum(1 for s in statuses.values() if s.marker_count > 0)}"
    )
    
    # Format output
    if args.format == "csv":
        format_csv(statuses, args.output)
    elif args.format == "json":
        format_json(statuses, args.output)
    else:  # md
        format_markdown(statuses, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
