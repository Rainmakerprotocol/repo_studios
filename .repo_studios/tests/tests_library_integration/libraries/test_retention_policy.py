"""Unit tests for retention_policy.py loader module."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

# Add the libraries path to enable imports
_SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "command_center" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from libraries.retention_policy import (
    DEFAULT_FALLBACK_KEEP,
    ENV_PREFIX,
    OrchestratorConfig,
    ScriptRetention,
    _find_repo_root,
    get_keep,
    get_orchestrator_config,
    get_script_retention,
    list_all_scripts,
    main,
    reload_config,
    validate_config,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the config cache before and after each test."""
    reload_config()
    yield
    reload_config()


class TestGetKeep:
    """Tests for get_keep function."""

    def test_returns_int(self) -> None:
        """get_keep always returns an integer."""
        result = get_keep("collect_test_log_reports")
        assert isinstance(result, int)

    def test_returns_positive(self) -> None:
        """get_keep always returns at least 1."""
        result = get_keep("nonexistent_script_xyz")
        assert result >= 1

    def test_known_script_returns_config_value(self) -> None:
        """Known scripts return their configured value."""
        # collect_test_log_reports is configured with keep: 5
        result = get_keep("collect_test_log_reports")
        assert result == 5

    def test_unknown_script_returns_default(self) -> None:
        """Unknown scripts return the default_keep value."""
        result = get_keep("completely_unknown_script_12345")
        assert result == 5  # default_keep in config is 5

    def test_env_override_takes_precedence(self) -> None:
        """Environment variable override takes precedence over config."""
        env_var = f"{ENV_PREFIX}collect_test_log_reports"
        with patch.dict(os.environ, {env_var: "42"}):
            reload_config()  # Force re-evaluation
            result = get_keep("collect_test_log_reports")
            assert result == 42

    def test_env_override_minimum_is_1(self) -> None:
        """Environment override values below 1 are clamped to 1."""
        env_var = f"{ENV_PREFIX}test_script"
        with patch.dict(os.environ, {env_var: "0"}):
            reload_config()
            result = get_keep("test_script")
            assert result >= 1

    def test_invalid_env_value_ignored(self) -> None:
        """Invalid environment variable values are ignored."""
        env_var = f"{ENV_PREFIX}collect_test_log_reports"
        with patch.dict(os.environ, {env_var: "not_a_number"}):
            reload_config()
            result = get_keep("collect_test_log_reports")
            # Should fall back to config value, not crash
            assert isinstance(result, int)


class TestGetScriptRetention:
    """Tests for get_script_retention function."""

    def test_returns_dataclass(self) -> None:
        """get_script_retention returns a ScriptRetention dataclass."""
        result = get_script_retention("collect_test_log_reports")
        assert isinstance(result, ScriptRetention)

    def test_includes_key(self) -> None:
        """Result includes the requested script key."""
        result = get_script_retention("scan_monkey_patches")
        assert result.key == "scan_monkey_patches"

    def test_includes_source(self) -> None:
        """Result indicates the source of the value."""
        result = get_script_retention("collect_test_log_reports")
        assert result.source in ("config", "env", "fallback")

    def test_config_source_for_known_script(self) -> None:
        """Known scripts report 'config' as source."""
        result = get_script_retention("collect_test_log_reports")
        assert result.source == "config"

    def test_fallback_source_for_unknown_script(self) -> None:
        """Unknown scripts report 'fallback' as source."""
        result = get_script_retention("completely_unknown_xyz")
        assert result.source == "fallback"

    def test_env_source_when_overridden(self) -> None:
        """Environment-overridden scripts report 'env' as source."""
        env_var = f"{ENV_PREFIX}test_script"
        with patch.dict(os.environ, {env_var: "7"}):
            reload_config()
            result = get_script_retention("test_script")
            assert result.source == "env"
            assert result.keep == 7


class TestGetOrchestratorConfig:
    """Tests for get_orchestrator_config function."""

    def test_known_orchestrator_returns_config(self) -> None:
        """Known orchestrators return an OrchestratorConfig."""
        result = get_orchestrator_config("run_test_execution_telemetry")
        assert isinstance(result, OrchestratorConfig)

    def test_unknown_orchestrator_returns_none(self) -> None:
        """Unknown orchestrators return None."""
        result = get_orchestrator_config("nonexistent_orchestrator")
        assert result is None

    def test_orchestrator_has_name(self) -> None:
        """Orchestrator config includes the name."""
        result = get_orchestrator_config("run_test_execution_telemetry")
        assert result is not None
        assert result.name == "run_test_execution_telemetry"

    def test_orchestrator_has_artifacts_to_keep(self) -> None:
        """Orchestrator config includes artifacts_to_keep."""
        result = get_orchestrator_config("run_test_execution_telemetry")
        assert result is not None
        assert isinstance(result.artifacts_to_keep, int)
        assert result.artifacts_to_keep >= 1

    def test_orchestrator_has_scripts(self) -> None:
        """Orchestrator config includes managed scripts."""
        result = get_orchestrator_config("run_test_execution_telemetry")
        assert result is not None
        assert isinstance(result.scripts, dict)
        assert len(result.scripts) > 0

    def test_orchestrator_scripts_are_retention_objects(self) -> None:
        """Orchestrator script values are ScriptRetention objects."""
        result = get_orchestrator_config("run_test_execution_telemetry")
        assert result is not None
        for script in result.scripts.values():
            assert isinstance(script, ScriptRetention)


class TestListAllScripts:
    """Tests for list_all_scripts function."""

    def test_returns_list(self) -> None:
        """list_all_scripts returns a list."""
        result = list_all_scripts()
        assert isinstance(result, list)

    def test_list_not_empty(self) -> None:
        """list_all_scripts returns non-empty list from real config."""
        result = list_all_scripts()
        assert len(result) > 0

    def test_list_contains_retention_objects(self) -> None:
        """list_all_scripts returns ScriptRetention objects."""
        result = list_all_scripts()
        for item in result:
            assert isinstance(item, ScriptRetention)

    def test_includes_known_scripts(self) -> None:
        """list_all_scripts includes scripts from config."""
        result = list_all_scripts()
        keys = {s.key for s in result}
        assert "collect_test_log_reports" in keys
        assert "scan_monkey_patches" in keys


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_returns_tuple(self) -> None:
        """validate_config returns (bool, list)."""
        is_valid, messages = validate_config()
        assert isinstance(is_valid, bool)
        assert isinstance(messages, list)

    def test_real_config_is_valid(self) -> None:
        """The actual retention_policy.yaml should be valid."""
        is_valid, messages = validate_config()
        # Print messages for debugging if validation fails
        if not is_valid:
            for msg in messages:
                print(msg)
        assert is_valid, f"Config validation failed: {messages}"

    def test_messages_are_strings(self) -> None:
        """Validation messages are strings."""
        _, messages = validate_config()
        for msg in messages:
            assert isinstance(msg, str)


class TestReloadConfig:
    """Tests for reload_config function."""

    def test_clears_cache(self) -> None:
        """reload_config clears the config cache."""
        # First call to load config
        get_keep("collect_test_log_reports")

        # Reload should not raise
        reload_config()

        # Should be able to load again
        result = get_keep("collect_test_log_reports")
        assert isinstance(result, int)


class TestFindRepoRoot:
    """Tests for _find_repo_root function."""

    def test_finds_repo_root(self) -> None:
        """_find_repo_root returns a valid path."""
        result = _find_repo_root()
        assert isinstance(result, Path)
        assert result.exists()

    def test_repo_root_contains_repo_studios(self) -> None:
        """Found repo root contains .repo_studios directory."""
        result = _find_repo_root()
        assert (result / ".repo_studios").is_dir()


class TestCLI:
    """Tests for CLI entry point."""

    def test_validate_flag(self) -> None:
        """--validate runs without error."""
        exit_code = main(["--validate"])
        assert exit_code == 0

    def test_list_flag(self) -> None:
        """--list runs without error."""
        exit_code = main(["--list"])
        assert exit_code == 0

    def test_get_known_script(self) -> None:
        """--get for known script returns 0."""
        exit_code = main(["--get", "collect_test_log_reports"])
        assert exit_code == 0

    def test_get_unknown_script(self) -> None:
        """--get for unknown script still returns 0 (fallback)."""
        exit_code = main(["--get", "nonexistent_script"])
        assert exit_code == 0

    def test_orchestrator_known(self) -> None:
        """--orchestrator for known orchestrator returns 0."""
        exit_code = main(["--orchestrator", "run_test_execution_telemetry"])
        assert exit_code == 0

    def test_orchestrator_unknown(self) -> None:
        """--orchestrator for unknown orchestrator returns 1."""
        exit_code = main(["--orchestrator", "nonexistent_orchestrator"])
        assert exit_code == 1

    def test_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No arguments shows help and returns 0."""
        exit_code = main([])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "--validate" in captured.out


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_script_key(self) -> None:
        """Empty script key returns default."""
        result = get_keep("")
        assert result >= 1

    def test_special_characters_in_key(self) -> None:
        """Script key with special characters doesn't crash."""
        result = get_keep("script-with-dashes_and_underscores")
        assert result >= 1

    def test_negative_env_value(self) -> None:
        """Negative env override value is clamped to 1."""
        env_var = f"{ENV_PREFIX}test_script"
        with patch.dict(os.environ, {env_var: "-5"}):
            reload_config()
            result = get_keep("test_script")
            assert result >= 1
