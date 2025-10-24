"""Create hardlink with fallback to file copy for artifact versioning.

This module provides a safe way to create "latest" symlinks/hardlinks for
generated artifacts, with automatic fallback to file copying on systems
that don't support hardlinks or when crossing filesystem boundaries.

Usage:
    from .repo_studios.library.artifact_lifecycle.versioning import create_latest_link
    
    create_latest_link(
        source=Path("report-20251023.json"),
        destination=Path("latest-report.json")
    )

Part of: artifact_lifecycle/versioning/
Related: prune_old_runs.py
"""

from __future__ import annotations

from pathlib import Path


def create_latest_link(source: Path, destination: Path) -> None:
    """Create hardlink or copy to maintain 'latest' artifact reference.
    
    Attempts to create a hardlink from source to destination. If hardlinking
    fails (unsupported filesystem, cross-device link, permissions), falls back
    to copying the file contents.
    
    This pattern is commonly used to maintain a stable "latest" reference to
    timestamped artifact files without requiring symbolic links.
    
    Args:
        source: Path to source artifact file (must exist)
        destination: Path where latest link should be created
        
    Raises:
        FileNotFoundError: If source file does not exist
        PermissionError: If lacking write permissions to destination directory
        
    Example:
        >>> from pathlib import Path
        >>> create_latest_link(
        ...     source=Path("reports/report-20251023_120000.json"),
        ...     destination=Path("reports/latest_report.json")
        ... )
        # Creates hardlink or copy at destination
        
    Notes:
        - If destination exists, it is removed before creating link
        - Hardlinks are preferred (zero additional disk space)
        - File copy fallback ensures cross-platform compatibility
        - Both source and destination must be files (not directories)
    """
    if not source.exists():
        raise FileNotFoundError(f"Source file does not exist: {source}")
    
    if not source.is_file():
        raise ValueError(f"Source must be a file, not directory: {source}")
    
    # Remove existing destination if present
    if destination.exists():
        destination.unlink()
    
    # Attempt hardlink first (efficient)
    try:
        destination.hardlink_to(source)
    except OSError:
        # Fallback to copy (cross-device, unsupported fs, etc.)
        destination.write_bytes(source.read_bytes())


__all__ = ["create_latest_link"]
