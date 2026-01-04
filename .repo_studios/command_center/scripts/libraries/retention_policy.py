"""Centralized retention policy loader for artifact pruning.

This module provides a single source of truth for artifact retention counts
across all pruning-enabled scripts. Configuration is read from:
  .repo_studios/config/retention_policy.yaml

Override precedence (highest to lowest):
  1. CLI argument passed directly to the script
  2. Environment variable: RETENTION_<script_key>=<count>
  3. Config file value
  4. Hardcoded fallback (DEFAULT_FALLBACK_KEEP = 5)

Usage:
    from libraries.retention_policy import get_keep, get_orchestrator_config

    # Get keep value for a specific script
    keep = get_keep("collect_test_log_reports")

    # Get all keeps for an orchestrator's scripts
    config = get_orchestrator_config("run_test_execution_telemetry")

CLI Validation:
    python -m .repo_studios.command_center.scripts.libraries.retention_policy --validate
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Hardcoded fallback if config is missing or script not found
DEFAULT_FALLBACK_KEEP = 5

# Environment variable prefix for overrides
ENV_PREFIX = "RETENTION_"

# Default config path relative to repo root
CONFIG_RELATIVE_PATH = ".repo_studios/config/retention_policy.yaml"


@dataclass(frozen=True)
class ScriptRetention:
    """Retention configuration for a single script."""

    key: str
    keep: int
    description: str
    source: str  # "config", "env", "fallback"


@dataclass(frozen=True)
class OrchestratorConfig:
    """Retention configuration for an orchestrator and its managed scripts."""

    name: str
    artifacts_to_keep: int
    scripts: dict[str, ScriptRetention]


def _find_repo_root() -> Path:
    """Locate the repository root by searching for .repo_studios directory."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if parent.name == ".repo_studios":
            continue
        if (parent / ".repo_studios").is_dir():
            return parent
        if (parent / ".git").is_dir():
            return parent
    # Fallback to cwd if detection fails
    return Path.cwd()


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML config file. Returns empty dict if file missing or invalid."""
    if not path.exists():
        logger.warning("Retention config not found: %s", path)
        return {}
    try:
        import yaml

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except ImportError:
        logger.error("PyYAML not installed; cannot load retention config")
        return {}
    except Exception as exc:
        logger.error("Failed to parse retention config %s: %s", path, exc)
        return {}


@lru_cache(maxsize=1)
def _get_config() -> dict[str, Any]:
    """Load and cache the retention policy config."""
    repo_root = _find_repo_root()
    config_path = repo_root / CONFIG_RELATIVE_PATH
    return _load_yaml(config_path)


def reload_config() -> None:
    """Clear cached config to force reload on next access."""
    _get_config.cache_clear()


def _get_env_override(script_key: str) -> int | None:
    """Check for environment variable override for a script key."""
    env_var = f"{ENV_PREFIX}{script_key}"
    value = os.environ.get(env_var)
    if value is not None:
        try:
            return max(1, int(value))
        except ValueError:
            logger.warning("Invalid %s value '%s'; ignoring", env_var, value)
    return None


def _find_script_in_config(script_key: str) -> tuple[int | None, str | None]:
    """Search config for a script key. Returns (keep, description) or (None, None)."""
    config = _get_config()

    # Check orchestrator scripts
    orchestrators = config.get("orchestrators", {})
    for _orch_name, orch_data in orchestrators.items():
        if not isinstance(orch_data, dict):
            continue
        scripts = orch_data.get("scripts", {})
        if script_key in scripts:
            script_data = scripts[script_key]
            if isinstance(script_data, dict):
                return script_data.get("keep"), script_data.get("description", "")
            if isinstance(script_data, int):
                return script_data, ""

    # Check standalone scripts
    standalone = config.get("standalone", {})
    if script_key in standalone:
        script_data = standalone[script_key]
        if isinstance(script_data, dict):
            return script_data.get("keep"), script_data.get("description", "")
        if isinstance(script_data, int):
            return script_data, ""

    return None, None


def get_keep(script_key: str) -> int:
    """Get the retention count for a script.

    Args:
        script_key: Script identifier (e.g., "collect_test_log_reports")

    Returns:
        Retention count with override precedence applied.
    """
    # Check environment override first
    env_override = _get_env_override(script_key)
    if env_override is not None:
        logger.debug("Using env override for %s: %d", script_key, env_override)
        return env_override

    # Check config file
    config_keep, _ = _find_script_in_config(script_key)
    if config_keep is not None:
        return max(1, config_keep)

    # Check global default in config
    config = _get_config()
    default_keep = config.get("default_keep", DEFAULT_FALLBACK_KEEP)

    logger.debug("Script %s not in config; using default %d", script_key, default_keep)
    return max(1, default_keep)


def get_script_retention(script_key: str) -> ScriptRetention:
    """Get full retention info for a script including source.

    Args:
        script_key: Script identifier

    Returns:
        ScriptRetention with keep value and source indicator.
    """
    # Check environment override
    env_override = _get_env_override(script_key)
    if env_override is not None:
        return ScriptRetention(
            key=script_key,
            keep=env_override,
            description="",
            source="env",
        )

    # Check config file
    config_keep, description = _find_script_in_config(script_key)
    if config_keep is not None:
        return ScriptRetention(
            key=script_key,
            keep=max(1, config_keep),
            description=description or "",
            source="config",
        )

    # Fallback
    config = _get_config()
    default_keep = config.get("default_keep", DEFAULT_FALLBACK_KEEP)
    return ScriptRetention(
        key=script_key,
        keep=max(1, default_keep),
        description="",
        source="fallback",
    )


def get_orchestrator_config(orchestrator_name: str) -> OrchestratorConfig | None:
    """Get retention configuration for an orchestrator and its scripts.

    Args:
        orchestrator_name: Orchestrator identifier (e.g., "run_test_execution_telemetry")

    Returns:
        OrchestratorConfig or None if orchestrator not found.
    """
    config = _get_config()
    orchestrators = config.get("orchestrators", {})

    if orchestrator_name not in orchestrators:
        return None

    orch_data = orchestrators[orchestrator_name]
    if not isinstance(orch_data, dict):
        return None

    # Build script retention map using the orchestrator-scoped values.
    #
    # NOTE: We intentionally do NOT call get_script_retention(script_key) here.
    # The same script key may appear under multiple orchestrators with different
    # keep values, and get_script_retention performs a global lookup.
    scripts: dict[str, ScriptRetention] = {}
    for script_key, script_data in orch_data.get("scripts", {}).items():
        env_override = _get_env_override(script_key)
        if env_override is not None:
            scripts[script_key] = ScriptRetention(
                key=script_key,
                keep=env_override,
                description="",
                source="env",
            )
            continue

        keep_value: int | None = None
        description = ""
        if isinstance(script_data, dict):
            raw_keep = script_data.get("keep")
            if raw_keep is not None:
                try:
                    keep_value = int(raw_keep)
                except (TypeError, ValueError):
                    keep_value = None
            raw_description = script_data.get("description")
            if raw_description is not None:
                description = str(raw_description)
        elif isinstance(script_data, int):
            keep_value = script_data

        if keep_value is None:
            keep_value = DEFAULT_FALLBACK_KEEP
            source = "fallback"
        else:
            source = "config"

        scripts[script_key] = ScriptRetention(
            key=script_key,
            keep=max(1, keep_value),
            description=description,
            source=source,
        )

    return OrchestratorConfig(
        name=orchestrator_name,
        artifacts_to_keep=max(1, int(orch_data.get("artifacts_to_keep", DEFAULT_FALLBACK_KEEP))),
        scripts=scripts,
    )


def list_all_scripts() -> list[ScriptRetention]:
    """List all scripts defined in the config with their retention info."""
    config = _get_config()
    results: list[ScriptRetention] = []

    # Orchestrator scripts
    for _orch_name, orch_data in config.get("orchestrators", {}).items():
        if not isinstance(orch_data, dict):
            continue
        for script_key in orch_data.get("scripts", {}):
            results.append(get_script_retention(script_key))

    # Standalone scripts
    for script_key in config.get("standalone", {}):
        results.append(get_script_retention(script_key))

    return results


def validate_config() -> tuple[bool, list[str]]:
    """Validate the retention policy config.

    Returns:
        (is_valid, list of error/warning messages)
    """
    messages: list[str] = []
    config = _get_config()

    if not config:
        messages.append("ERROR: Config file not found or empty")
        return False, messages

    # Check version
    version = config.get("version")
    if not version:
        messages.append("WARNING: No version specified in config")

    # Check default_keep
    default_keep = config.get("default_keep")
    if default_keep is None:
        messages.append("WARNING: No default_keep specified; using fallback=5")
    elif not isinstance(default_keep, int) or default_keep < 1:
        messages.append(f"ERROR: Invalid default_keep: {default_keep}")
        return False, messages

    # Validate orchestrators
    orchestrators = config.get("orchestrators", {})
    if not isinstance(orchestrators, dict):
        messages.append("ERROR: 'orchestrators' must be a dict")
        return False, messages

    script_keys_seen: set[str] = set()

    for orch_name, orch_data in orchestrators.items():
        if not isinstance(orch_data, dict):
            messages.append(f"ERROR: Orchestrator '{orch_name}' must be a dict")
            return False, messages

        orch_keep = orch_data.get("artifacts_to_keep")
        if orch_keep is not None and (not isinstance(orch_keep, int) or orch_keep < 1):
            messages.append(f"ERROR: Invalid artifacts_to_keep for {orch_name}: {orch_keep}")
            return False, messages

        scripts = orch_data.get("scripts", {})
        if not isinstance(scripts, dict):
            messages.append(f"ERROR: scripts in '{orch_name}' must be a dict")
            return False, messages

        for script_key, script_data in scripts.items():
            if script_key in script_keys_seen:
                messages.append(f"WARNING: Duplicate script key '{script_key}'")
            script_keys_seen.add(script_key)

            if isinstance(script_data, dict):
                keep = script_data.get("keep")
                if keep is not None and (not isinstance(keep, int) or keep < 1):
                    messages.append(f"ERROR: Invalid keep for {script_key}: {keep}")
                    return False, messages

    # Validate standalone
    standalone = config.get("standalone", {})
    if not isinstance(standalone, dict):
        messages.append("ERROR: 'standalone' must be a dict")
        return False, messages

    for script_key, script_data in standalone.items():
        if script_key in script_keys_seen:
            messages.append(f"WARNING: Duplicate script key '{script_key}' in standalone")
        script_keys_seen.add(script_key)

        if isinstance(script_data, dict):
            keep = script_data.get("keep")
            if keep is not None and (not isinstance(keep, int) or keep < 1):
                messages.append(f"ERROR: Invalid keep for {script_key}: {keep}")
                return False, messages

    messages.append(f"INFO: Found {len(script_keys_seen)} script entries")
    return True, messages


def _print_validation_report() -> int:
    """Print validation report and return exit code."""
    is_valid, messages = validate_config()

    print("=" * 60)
    print("Retention Policy Validation Report")
    print("=" * 60)

    for msg in messages:
        print(msg)

    print()
    if is_valid:
        print("✓ Config is valid")

        # Print summary
        scripts = list_all_scripts()
        print(f"\nTotal scripts configured: {len(scripts)}")

        # Group by source
        by_source: dict[str, int] = {}
        for s in scripts:
            by_source[s.source] = by_source.get(s.source, 0) + 1
        for source, count in sorted(by_source.items()):
            print(f"  {source}: {count}")

        return 0
    else:
        print("✗ Config has errors")
        return 1


def _print_list_report() -> int:
    """Print all configured scripts with their retention values."""
    scripts = list_all_scripts()

    print("=" * 60)
    print("Configured Scripts and Retention Values")
    print("=" * 60)
    print(f"{'Script':<45} {'Keep':>5} {'Source':<8}")
    print("-" * 60)

    for s in sorted(scripts, key=lambda x: x.key):
        print(f"{s.key:<45} {s.keep:>5} {s.source:<8}")

    print("-" * 60)
    print(f"Total: {len(scripts)} scripts")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for validation and listing."""
    parser = argparse.ArgumentParser(
        description="Retention policy validation and inspection",
        prog="retention_policy",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the retention policy config",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_scripts",
        help="List all configured scripts with retention values",
    )
    parser.add_argument(
        "--get",
        metavar="SCRIPT_KEY",
        help="Get retention value for a specific script",
    )
    parser.add_argument(
        "--orchestrator",
        metavar="NAME",
        help="Show config for a specific orchestrator",
    )

    args = parser.parse_args(argv)

    if args.validate:
        return _print_validation_report()

    if args.list_scripts:
        return _print_list_report()

    if args.get:
        retention = get_script_retention(args.get)
        print(f"{retention.key}: {retention.keep} (source: {retention.source})")
        if retention.description:
            print(f"  Description: {retention.description}")
        return 0

    if args.orchestrator:
        config = get_orchestrator_config(args.orchestrator)
        if config is None:
            print(f"Orchestrator '{args.orchestrator}' not found")
            return 1
        print(f"Orchestrator: {config.name}")
        print(f"  artifacts_to_keep: {config.artifacts_to_keep}")
        print(f"  scripts:")
        for key, ret in sorted(config.scripts.items()):
            print(f"    {key}: {ret.keep} ({ret.source})")
        return 0

    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
