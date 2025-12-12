#!/usr/bin/env python3
"""
Generate tier3_scripts_index.yaml from individual tier3_*.yaml files.

Scans .repo_studios/docs/pipeline/ for tier3_*.yaml files, validates structure,
and aggregates into a single index for fast agent tool discovery.

Usage:
    python generate_tier3_index.py --repo-root . --validate
    python generate_tier3_index.py --output custom_index.yaml
"""

import argparse
import logging
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# Script version for tracking in output
GENERATOR_VERSION = "1.0.0"

# Expected tier3 YAML structure (required top-level keys)
REQUIRED_TIER3_KEYS = ["tool", "invocation", "parameters", "outputs", "behavior", "metadata"]

# Valid categories
VALID_CATEGORIES = ["producer", "consumer", "aggregator", "orchestrator", "summarizer", "utility"]

# Valid statuses
VALID_STATUSES = ["template", "draft", "active", "deprecated"]


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure logging with specified level."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(levelname)s: %(message)s",
        force=True  # Override any existing config
    )
    return logging.getLogger(__name__)


def find_tier3_files(pipeline_dir: Path, log: logging.Logger) -> List[Path]:
    """
    Find all tier3_*.yaml files in pipeline directory (non-recursive).
    
    Args:
        pipeline_dir: Path to .repo_studios/docs/pipeline/
        log: Logger instance
    
    Returns:
        List of Path objects for tier3 YAML files
    """
    pattern = "tier3_*.yaml"
    tier3_files = sorted(pipeline_dir.glob(pattern))
    
    # Filter out files in subdirectories
    tier3_files = [f for f in tier3_files if f.parent == pipeline_dir]
    
    log.info(f"Found {len(tier3_files)} tier3 YAML files matching '{pattern}'")
    return tier3_files


def validate_tier3_yaml(
    yaml_path: Path,
    data: Dict[str, Any],
    log: logging.Logger
) -> List[str]:
    """
    Validate tier3 YAML structure and return list of errors.
    
    Args:
        yaml_path: Path to YAML file (for error messages)
        data: Parsed YAML data
        log: Logger instance
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    filename = yaml_path.name
    
    # Check required top-level keys
    for key in REQUIRED_TIER3_KEYS:
        if key not in data:
            errors.append(f"Missing required section: {key}")
    
    # Validate tool section
    if "tool" in data:
        tool = data["tool"]
        if not isinstance(tool, dict):
            errors.append("'tool' must be a dictionary")
        else:
            if "id" not in tool:
                errors.append("'tool.id' is required")
            if "name" not in tool:
                errors.append("'tool.name' is required")
            if "description" not in tool:
                errors.append("'tool.description' is required")
    
    # Validate metadata section
    if "metadata" in data:
        meta = data["metadata"]
        if not isinstance(meta, dict):
            errors.append("'metadata' must be a dictionary")
        else:
            # Check category
            if "category" in meta:
                if meta["category"] not in VALID_CATEGORIES:
                    errors.append(
                        f"'metadata.category' must be one of {VALID_CATEGORIES}, "
                        f"got '{meta['category']}'"
                    )
            else:
                errors.append("'metadata.category' is required")
            
            # Check status
            if "status" in meta:
                if meta["status"] not in VALID_STATUSES:
                    errors.append(
                        f"'metadata.status' must be one of {VALID_STATUSES}, "
                        f"got '{meta['status']}'"
                    )
            else:
                errors.append("'metadata.status' is required")
    
    if errors:
        log.warning(f"{filename}: Found {len(errors)} validation error(s)")
    
    return errors


def load_tier3_yaml(
    yaml_path: Path,
    validate: bool,
    log: logging.Logger
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Load and optionally validate a tier3 YAML file.
    
    Args:
        yaml_path: Path to YAML file
        validate: Whether to run validation
        log: Logger instance
    
    Returns:
        Tuple of (parsed_data, errors). Data is None if load fails.
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict):
            return None, [f"YAML root must be a dictionary, got {type(data).__name__}"]
        
        errors = []
        if validate:
            errors = validate_tier3_yaml(yaml_path, data, log)
        
        return data, errors
    
    except yaml.YAMLError as e:
        log.error(f"{yaml_path.name}: YAML parse error: {e}")
        return None, [f"YAML parse error: {e}"]
    except Exception as e:
        log.error(f"{yaml_path.name}: Failed to load: {e}")
        return None, [f"Load error: {e}"]


def create_index_entry(
    yaml_path: Path,
    data: Dict[str, Any],
    pipeline_dir: Path
) -> Dict[str, Any]:
    """
    Create lightweight index entry from tier3 YAML data.
    
    Args:
        yaml_path: Path to YAML file
        data: Parsed YAML data
        pipeline_dir: Path to pipeline directory (for relative paths)
    
    Returns:
        Dictionary with index entry fields
    """
    tool = data.get("tool", {})
    invocation = data.get("invocation", {})
    metadata = data.get("metadata", {})
    
    # Relative path to tier3 file from pipeline dir
    tier3_file = yaml_path.relative_to(pipeline_dir)
    
    return {
        "script_id": tool.get("id", "unknown"),
        "name": tool.get("name", "Unknown Tool"),
        "category": metadata.get("category", "unknown"),
        "tier3_file": str(tier3_file),
        "script_path": invocation.get("script_path", "unknown"),
        "summary": tool.get("description", "No description"),
        "keywords": tool.get("keywords", []),
        "status": metadata.get("status", "unknown"),
        "entry_point": invocation.get("entry_function", "unknown"),
        "importable": invocation.get("importable", False)
    }


def generate_index(
    tier3_files: List[Path],
    pipeline_dir: Path,
    validate: bool,
    log: logging.Logger
) -> Dict[str, Any]:
    """
    Generate complete tier3_scripts_index from individual YAML files.
    
    Args:
        tier3_files: List of tier3 YAML file paths
        pipeline_dir: Path to pipeline directory
        validate: Whether to validate YAMLs
        log: Logger instance
    
    Returns:
        Complete index dictionary
    """
    scripts = []
    validation_errors = {}
    missing_data = []
    category_counts = Counter()
    status_counts = Counter()
    
    log.info("Processing tier3 YAML files...")
    
    for yaml_path in tier3_files:
        log.debug(f"Processing {yaml_path.name}")
        
        data, errors = load_tier3_yaml(yaml_path, validate, log)
        
        if data is None:
            missing_data.append(str(yaml_path.relative_to(pipeline_dir)))
            validation_errors[yaml_path.name] = errors
            continue
        
        if errors:
            validation_errors[yaml_path.name] = errors
        
        # Create index entry
        entry = create_index_entry(yaml_path, data, pipeline_dir)
        scripts.append(entry)
        
        # Update statistics
        category_counts[entry["category"]] += 1
        status_counts[entry["status"]] += 1
    
    # Build category indices
    by_category = {}
    for category in VALID_CATEGORIES:
        by_category[category] = [
            s["script_id"] for s in scripts if s["category"] == category
        ]
    
    # Build index structure
    index = {
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "repository": {
            "name": "repo_studios",
            "root": str(pipeline_dir.parent.parent.parent),  # Up to repo root
            "branch": "main"
        },
        "statistics": {
            "total_scripts": len(scripts),
            "categories": dict(category_counts),
            "status": dict(status_counts)
        },
        "scripts": scripts,
        "by_category": by_category
    }
    
    # Add validation report if errors found
    if validation_errors or missing_data:
        index["validation"] = {}
        
        if missing_data:
            index["validation"]["failed_to_load"] = missing_data
        
        if validation_errors:
            index["validation"]["validation_errors"] = [
                {
                    "tier3_file": filename,
                    "errors": errors
                }
                for filename, errors in validation_errors.items()
            ]
    
    log.info(f"Generated index with {len(scripts)} scripts")
    if validation_errors:
        log.warning(f"Found validation errors in {len(validation_errors)} file(s)")
    
    return index


def write_index(index: Dict[str, Any], output_path: Path, log: logging.Logger) -> None:
    """
    Write index to YAML file.
    
    Args:
        index: Index dictionary
        output_path: Path to output file
        log: Logger instance
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            index,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=100
        )
    
    log.info(f"✓ Wrote index to {output_path}")


def run(argv: List[str]) -> int:
    """
    Main entry point for script.
    
    Args:
        argv: Command-line arguments (excluding script name)
    
    Returns:
        Exit code (0 = success, non-zero = error)
    """
    parser = argparse.ArgumentParser(
        description="Generate tier3_scripts_index.yaml from tier3_*.yaml files"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root directory (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: tier3_index/outputs/tier3_scripts_index.yaml)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate tier3 YAML structure"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args(argv)
    log = setup_logging(args.log_level)
    
    # Resolve paths
    repo_root = args.repo_root.resolve()
    pipeline_dir = repo_root / ".repo_studios" / "docs" / "pipeline"
    
    if not pipeline_dir.exists():
        log.error(f"Pipeline directory not found: {pipeline_dir}")
        return 1
    
    # Determine output path
    if args.output:
        output_path = args.output.resolve()
    else:
        output_path = pipeline_dir / "tier3_index" / "outputs" / "tier3_scripts_index.yaml"
    
    log.info(f"Scanning for tier3 YAML files in: {pipeline_dir}")
    
    # Find tier3 files
    tier3_files = find_tier3_files(pipeline_dir, log)
    
    if not tier3_files:
        log.warning("No tier3_*.yaml files found")
        # Still generate empty index
        index = {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator_version": GENERATOR_VERSION,
            "statistics": {"total_scripts": 0},
            "scripts": []
        }
    else:
        # Generate index
        index = generate_index(tier3_files, pipeline_dir, args.validate, log)
    
    # Write output
    write_index(index, output_path, log)
    
    # Report summary
    stats = index.get("statistics", {})
    log.info(f"Summary: {stats.get('total_scripts', 0)} scripts indexed")
    
    if "validation" in index:
        validation = index["validation"]
        if "validation_errors" in validation:
            error_count = len(validation["validation_errors"])
            log.warning(f"⚠ {error_count} file(s) have validation errors")
            return 1  # Exit with error if validation issues found
    
    return 0


def main() -> int:
    """CLI entry point."""
    return run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
