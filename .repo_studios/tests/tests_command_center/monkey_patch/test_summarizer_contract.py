from __future__ import annotations

import pytest

from tests.tests_command_center.monkey_patch import helpers

SUMMARIZER_PATH = helpers.COMMAND_CENTER_SCRIPTS / "summarizers" / "summarize_monkey_patch_overview.py"

summarizer_module = helpers.load_optional_module(
    "summarize_monkey_patch_overview",
    SUMMARIZER_PATH,
)

if summarizer_module is None:
    pytest.skip("Monkey Patch overview summarizer not yet implemented.", allow_module_level=True)


def test_summarizer_exposes_run_entrypoint() -> None:
    assert hasattr(summarizer_module, "run"), "run() entrypoint missing"
    assert callable(summarizer_module.run)


def test_summarizer_declares_expected_slugs() -> None:
    assert getattr(summarizer_module, "VIEWER_SLUG", None) == "healthview"
    assert getattr(summarizer_module, "TOPIC_SLUG", None) == "monkey_patch_overview"
