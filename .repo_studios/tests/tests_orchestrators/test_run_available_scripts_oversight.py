"""Unit tests for run_available_scripts_oversight orchestrator."""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPO_ROOT / ".repo_studios" / "command_center" / "scripts"
ORCHESTRATOR_PATH = SCRIPTS_ROOT / "orchestrators" / "run_available_scripts_oversight.py"


def _load_module(module_path: Path, module_name: str) -> ModuleType:
    """Dynamically load a module from file path."""
    # Ensure libraries are importable
    if str(SCRIPTS_ROOT) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_ROOT))

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Load the orchestrator module
mod = _load_module(ORCHESTRATOR_PATH, "run_available_scripts_oversight")

# Import specific names
CONSUMER_CONFIGS = mod.CONSUMER_CONFIGS
PRODUCER_CONFIGS = mod.PRODUCER_CONFIGS
ScriptConfig = mod.ScriptConfig
StepOutcome = mod.StepOutcome
build_options = mod.build_options
build_paths = mod.build_paths
parse_args = mod.parse_args
run = mod.run


class TestParseArgs:
    """Test argument parsing."""

    def test_default_values(self) -> None:
        """Verify default argument values."""
        args = parse_args([])
        assert args.repo_root is None
        assert args.log_level == "INFO"
        assert args.artifacts_to_keep == 3
        assert args.skip_producers is False
        assert args.skip_consumers is False

    def test_skip_flags(self) -> None:
        """Verify skip flags are parsed correctly."""
        args = parse_args(["--skip-producers", "--skip-consumers"])
        assert args.skip_producers is True
        assert args.skip_consumers is True

    def test_log_level(self) -> None:
        """Verify log level is parsed correctly."""
        args = parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"


class TestScriptConfig:
    """Test ScriptConfig dataclass."""

    def test_default_values(self) -> None:
        """Verify default ScriptConfig values."""
        config = ScriptConfig(name="test", path="test.py")
        assert config.supports_artifacts_to_keep is True
        assert config.supports_output_dir is True
        assert config.uses_argv_kwarg is False
        assert config.custom_args is None

    def test_producer_configs_exist(self) -> None:
        """Verify producer configs are defined."""
        assert len(PRODUCER_CONFIGS) > 0
        for config in PRODUCER_CONFIGS:
            assert config.name
            assert config.path

    def test_consumer_configs_exist(self) -> None:
        """Verify consumer configs are defined."""
        assert len(CONSUMER_CONFIGS) > 0
        for config in CONSUMER_CONFIGS:
            assert config.name
            assert config.path


class TestRun:
    """Test the main run function."""

    def test_run_with_all_skipped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test run with both producers and consumers skipped."""
        output_dir = tmp_path / "orchestrator"
        output_dir.mkdir(parents=True)

        # Create a minimal .repo_studios marker
        marker = tmp_path / ".repo_studios"
        marker.mkdir()

        result = run(
            [
                "--repo-root",
                str(tmp_path),
                "--orchestrator-output-dir",
                str(output_dir),
                "--skip-producers",
                "--skip-consumers",
            ]
        )

        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert result["exit_code"] == 0
        assert "run_dir" in result
        assert "manifest_path" in result
        assert "summary_path" in result
        assert "telemetry_path" in result

    def test_run_returns_payload_dict(self, tmp_path: Path) -> None:
        """Verify run() returns a well-formed payload dict."""
        output_dir = tmp_path / "orchestrator"
        output_dir.mkdir(parents=True)

        # Create a minimal .repo_studios marker
        marker = tmp_path / ".repo_studios"
        marker.mkdir()

        result = run(
            [
                "--repo-root",
                str(tmp_path),
                "--orchestrator-output-dir",
                str(output_dir),
                "--skip-producers",
                "--skip-consumers",
            ]
        )

        # Verify payload structure
        assert "status" in result
        assert "exit_code" in result
        assert "run_dir" in result
        assert "slug" in result
        assert "producer_count" in result
        assert "consumer_count" in result

        # Verify artifacts exist
        run_dir = Path(result["run_dir"])
        assert run_dir.exists()
        assert (run_dir / "manifest.json").exists()
        assert (run_dir / "summary.md").exists()
        assert (run_dir / "telemetry.json").exists()

    def test_manifest_structure(self, tmp_path: Path) -> None:
        """Verify manifest.json has expected structure."""
        output_dir = tmp_path / "orchestrator"
        output_dir.mkdir(parents=True)

        marker = tmp_path / ".repo_studios"
        marker.mkdir()

        result = run(
            [
                "--repo-root",
                str(tmp_path),
                "--orchestrator-output-dir",
                str(output_dir),
                "--skip-producers",
                "--skip-consumers",
            ]
        )

        manifest_path = Path(result["manifest_path"])
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        assert "schema_version" in manifest
        assert "viewer" in manifest
        assert "topic" in manifest
        assert "run_slug" in manifest
        assert "generated_at" in manifest
        assert "artifacts" in manifest
        assert "catalog" in manifest

        assert manifest["viewer"] == "healthview"
        assert manifest["topic"] == "available_scripts_oversight"


class TestStepOutcome:
    """Test StepOutcome dataclass."""

    def test_fields(self) -> None:
        """Verify StepOutcome fields."""
        outcome = StepOutcome(
            script_name="test",
            payload={"status": "ok"},
            status="ok",
            detail="test detail",
            exit_code=0,
            run_dir=Path("/tmp/test"),
        )
        assert outcome.script_name == "test"
        assert outcome.status == "ok"
        assert outcome.exit_code == 0
