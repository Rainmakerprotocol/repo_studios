from __future__ import annotations

import pytest

from tests.tests_command_center.monkey_patch import helpers

ORCHESTRATOR_PATH = helpers.COMMAND_CENTER_SCRIPTS / "orchestrators" / "run_monkey_patch_oversight.py"

orchestrator_module = helpers.load_optional_module(
    "run_monkey_patch_oversight",
    ORCHESTRATOR_PATH,
)

if orchestrator_module is None:
    pytest.skip("Monkey Patch Oversight orchestrator not yet implemented.", allow_module_level=True)


def test_orchestrator_exposes_run_entrypoint() -> None:
    """The orchestrator should expose a callable run helper so topic pipelines can import it."""

    assert hasattr(orchestrator_module, "run"), "run() entrypoint missing"
    assert callable(orchestrator_module.run), "run() must be callable"
    assert hasattr(orchestrator_module, "main"), "main() shim expected for CLI wiring"
