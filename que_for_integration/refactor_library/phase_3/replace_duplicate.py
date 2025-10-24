#!/usr/bin/env python3
"""Helper script to replace duplicate code with library imports.

This script assists with Phase 3 manual validation by:
1. Reading duplicate detection report
2. Finding occurrences of a specific duplicate group
3. Generating replacement instructions
4. Optionally performing the replacement (with backup)

Usage:
    # Dry run (show what would be replaced)
    python replace_duplicate.py --group-id dup_001 --dry-run
    
    # Actually perform replacement
    python replace_duplicate.py --group-id dup_001 --apply
    
    # With custom report
    python replace_duplicate.py \
        --report path/to/report.json \
        --group-id dup_001 \
        --apply
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


def load_report(report_path: Path) -> dict[str, Any]:
    """Load duplicate detection report."""
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")
    
    return json.loads(report_path.read_text(encoding="utf-8"))


def find_group(report: dict[str, Any], group_id: str) -> dict[str, Any] | None:
    """Find duplicate group by ID."""
    for group in report.get("duplicate_groups", []):
        if group["group_id"] == group_id:
            return group
    return None


def backup_file(filepath: Path, backup_dir: Path) -> Path:
    """Create backup of file before modification."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filepath.name}.{timestamp}.backup"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(filepath, backup_path)
    print(f"  ✅ Backup created: {backup_path}")
    return backup_path


def find_import_insertion_point(lines: list[str]) -> int:
    """Find appropriate line to insert import statement.
    
    Returns index after last import block, or after docstring.
    """
    in_docstring = False
    last_import_line = 0
    docstring_end = 0
    
    for idx, line in enumerate(lines):
        stripped = line.strip()
        
        # Track docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
            elif stripped.endswith('"""') or stripped.endswith("'''"):
                in_docstring = False
                docstring_end = idx + 1
        
        # Track imports
        if stripped.startswith(("import ", "from ")) and not in_docstring:
            last_import_line = idx + 1
    
    # Insert after imports, or after docstring if no imports
    return max(last_import_line, docstring_end)


def replace_function_with_import(
    filepath: Path,
    line_start: int,
    line_end: int,
    import_statement: str,
    dry_run: bool = True,
    backup_dir: Path | None = None,
) -> bool:
    """Replace function definition with import statement.
    
    Args:
        filepath: Path to file to modify
        line_start: Start line of function (1-indexed)
        line_end: End line of function (1-indexed)
        import_statement: Import statement to add
        dry_run: If True, only show changes without applying
        backup_dir: Directory for backups (if not dry_run)
        
    Returns:
        True if replacement successful
    """
    if not filepath.exists():
        print(f"  ❌ File not found: {filepath}")
        return False
    
    lines = filepath.read_text(encoding="utf-8").splitlines(keepends=True)
    
    # Validate line numbers
    if line_start < 1 or line_end > len(lines):
        print(f"  ❌ Invalid line range: {line_start}-{line_end} (file has {len(lines)} lines)")
        return False
    
    # Convert to 0-indexed
    start_idx = line_start - 1
    end_idx = line_end  # Inclusive end, so don't subtract 1
    
    if dry_run:
        print(f"\n📝 DRY RUN: {filepath}")
        print(f"  Would remove lines {line_start}-{line_end}:")
        for line in lines[start_idx:end_idx]:
            print(f"    - {line.rstrip()}")
        
        # Find where import would go
        import_line = find_import_insertion_point(lines)
        print(f"\n  Would add import at line {import_line + 1}:")
        print(f"    + {import_statement}")
        
        return True
    
    # Create backup
    if backup_dir:
        backup_file(filepath, backup_dir)
    
    # Remove function definition
    modified_lines = lines[:start_idx] + ["# Imported from library\n"] + lines[end_idx:]
    
    # Add import statement
    import_line = find_import_insertion_point(modified_lines)
    
    # Check if import already exists
    import_exists = any(import_statement in line for line in modified_lines)
    
    if not import_exists:
        # Add blank line before import if needed
        if import_line > 0 and modified_lines[import_line - 1].strip():
            modified_lines.insert(import_line, "\n")
            import_line += 1
        
        modified_lines.insert(import_line, f"{import_statement}\n")
    
    # Write modified content
    filepath.write_text("".join(modified_lines), encoding="utf-8")
    print(f"  ✅ Modified: {filepath}")
    
    return True


def process_group(
    group: dict[str, Any],
    repo_root: Path,
    dry_run: bool = True,
    backup_dir: Path | None = None,
) -> dict[str, Any]:
    """Process all occurrences in a duplicate group.
    
    Returns:
        Summary of replacements
    """
    group_id = group["group_id"]
    canonical_name = group["canonical_name"]
    occurrences = group["occurrences"]
    import_stmt = group["library_recommendation"]["import_statement"]
    
    print(f"\n{'='*60}")
    print(f"Processing: {group_id} - {canonical_name}")
    print(f"Occurrences: {len(occurrences)}")
    print(f"Import: {import_stmt}")
    print(f"{'='*60}")
    
    results = {
        "group_id": group_id,
        "total": len(occurrences),
        "successful": 0,
        "failed": 0,
        "files": [],
    }
    
    for occ in occurrences:
        filepath = repo_root / occ["file"]
        line_start = occ["line_start"]
        line_end = occ["line_end"]
        
        print(f"\n📄 {occ['file']} (lines {line_start}-{line_end})")
        
        success = replace_function_with_import(
            filepath=filepath,
            line_start=line_start,
            line_end=line_end,
            import_statement=import_stmt,
            dry_run=dry_run,
            backup_dir=backup_dir,
        )
        
        if success:
            results["successful"] += 1
            results["files"].append(str(filepath))
        else:
            results["failed"] += 1
    
    return results


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Replace duplicate code with library imports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Dry run (preview changes)
    python replace_duplicate.py --group-id dup_001 --dry-run
    
    # Apply changes
    python replace_duplicate.py --group-id dup_001 --apply
    
    # Custom report location
    python replace_duplicate.py \\
        --report .repo_studios/reports/duplicate_detection_reports/latest_report.json \\
        --group-id dup_001 \\
        --apply
        """,
    )
    
    parser.add_argument(
        "--report",
        type=Path,
        default=Path(".repo_studios/reports/duplicate_detection_reports/latest_report.json"),
        help="Path to duplicate detection report JSON",
    )
    parser.add_argument(
        "--group-id",
        required=True,
        help="Duplicate group ID to process (e.g., dup_001)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without applying",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply the changes (creates backups)",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path(".repo_studios/backups/phase3_replacements"),
        help="Directory for file backups",
    )
    
    args = parser.parse_args(argv)
    
    # Validation
    if not args.dry_run and not args.apply:
        print("❌ Error: Must specify either --dry-run or --apply")
        return 1
    
    if args.dry_run and args.apply:
        print("⚠️  Warning: Both --dry-run and --apply specified, using --dry-run")
        args.apply = False
    
    repo_root = args.repo_root.resolve()
    
    # Load report
    try:
        report = load_report(args.report)
    except FileNotFoundError as exc:
        print(f"❌ Error: {exc}")
        return 1
    
    # Find group
    group = find_group(report, args.group_id)
    if not group:
        print(f"❌ Error: Group ID '{args.group_id}' not found in report")
        print("\nAvailable groups:")
        for g in report.get("duplicate_groups", []):
            print(f"  - {g['group_id']}: {g['canonical_name']}")
        return 1
    
    # Process group
    backup_dir = args.backup_dir if args.apply else None
    results = process_group(
        group=group,
        repo_root=repo_root,
        dry_run=args.dry_run,
        backup_dir=backup_dir,
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total occurrences: {results['total']}")
    print(f"✅ Successful: {results['successful']}")
    print(f"❌ Failed: {results['failed']}")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes were applied")
        print("Run with --apply to perform actual replacements")
    else:
        print("\n✅ Changes applied successfully!")
        print(f"Backups saved to: {args.backup_dir}")
        print("\nNext steps:")
        print("  1. Review modified files")
        print("  2. Run targeted tests: pytest")
        print("  3. Run full suite: make studio-test-all")
        print("  4. If tests fail, restore from backups")
    
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
