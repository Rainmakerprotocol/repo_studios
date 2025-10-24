"""Repo Studios Library - Composable Code Utilities

This package contains reusable functions extracted from duplicate code
across Repo Studios scripts. All modules follow strict naming conventions
for AI discoverability.

Structure:
    - filesystem/          File and directory operations
    - artifact_lifecycle/  Report generation and management
    - time_handling/       Timestamp parsing and formatting
    - logging_setup/       Logging configuration
    - cli_patterns/        Reusable CLI argument definitions

Usage:
    from .repo_studios.library.domain.purpose import function_name

Documentation:
    See: .repo_studios/library/README.md
    See: .repo_studios/naming_conventions.md

Status:
    Phase 1 Complete - Structure created
    Phase 2 Pending - Duplicate detection
    Phase 3 Pending - Manual extraction validation
"""

__version__ = "0.1.0"
__all__ = []

# Library is designed for explicit imports only
# Do NOT use: from .repo_studios.library import *
# DO use: from .repo_studios.library.domain.purpose import specific_function
