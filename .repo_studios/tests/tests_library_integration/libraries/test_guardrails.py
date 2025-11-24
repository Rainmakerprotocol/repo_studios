from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

SCRIPTS_ROOT = Path(__file__).resolve().parents[4] / ".repo_studios" / "command_center" / "scripts"


def _load_libraries():
    try:
        return importlib.import_module("libraries")
    except ModuleNotFoundError:  # pragma: no cover - mirrors existing tests
        if str(SCRIPTS_ROOT) not in sys.path:
            sys.path.insert(0, str(SCRIPTS_ROOT))
        return importlib.import_module("libraries")


libraries = _load_libraries()
load_guardrail_config = libraries.load_guardrail_config
enforce_run_size_limit = libraries.enforce_run_size_limit
GuardrailConfigError = libraries.GuardrailConfigError
GuardrailViolationError = libraries.GuardrailViolationError


def _write_config(tmp_path: Path, *, max_files: int = 3) -> Path:
    allowed_targets = tmp_path / "allowed_targets.yaml"
    allowed_targets.write_text("targets: []\n", encoding="utf-8")
    config_path = tmp_path / "automation_config.yaml"
    config_path.write_text(
        """
metadata:
  updated: "2025-10-31"
allow_list:
  source: allowed_targets.yaml
constraints:
  max_files_per_run: {max_files}
  max_groups_per_run: 2
  require_lock_check: true
  allow_override_flag: allow-custom
""".format(max_files=max_files),
        encoding="utf-8",
    )
    return config_path


def test_load_guardrail_config_normalizes_paths(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    config = load_guardrail_config(config_path)
    assert config.config_path == config_path.resolve()
    assert config.allow_list_source == (tmp_path / "allowed_targets.yaml").resolve()
    assert config.constraints.max_files_per_run == 3
    assert config.constraints.max_groups_per_run == 2
    assert config.constraints.require_lock_check is True
    assert config.constraints.allow_override_flag == "allow-custom"
    assert config.metadata["updated"] == "2025-10-31"


def test_enforce_run_size_limit_raises_when_over_limit(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, max_files=2)
    config = load_guardrail_config(config_path)
    candidates = [tmp_path / f"file_{index}.py" for index in range(3)]
    with pytest.raises(GuardrailViolationError) as excinfo:
        enforce_run_size_limit(candidates, config)
    assert "exceeding the configured guardrail limit of 2" in str(excinfo.value)


def test_enforce_run_size_limit_allows_override(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, max_files=1)
    config = load_guardrail_config(config_path)
    candidates = [tmp_path / "first.py", tmp_path / "second.py"]
    limit, count = enforce_run_size_limit(candidates, config, override=True)
    assert limit == 1
    assert count == 2


def test_load_guardrail_config_requires_max_files(tmp_path: Path) -> None:
    allowed_targets = tmp_path / "allowed_targets.yaml"
    allowed_targets.write_text("targets: []\n", encoding="utf-8")
    config_path = tmp_path / "automation_config.yaml"
    config_path.write_text(
        """
allow_list:
  source: allowed_targets.yaml
constraints:
  require_lock_check: false
""",
        encoding="utf-8",
    )
    with pytest.raises(GuardrailConfigError):
        load_guardrail_config(config_path)
