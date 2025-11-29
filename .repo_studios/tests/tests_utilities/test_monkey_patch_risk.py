from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "utilities" / "monkey_patch_risk.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("monkey_patch_risk", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _signals(module, **overrides):
    return module.FindingSignals(
        category=overrides.get("category", ""),
        is_test=overrides.get("is_test", False),
        is_module_scope=overrides.get("is_module_scope", False),
    )


def test_classify_high_risk_non_test_module_scope() -> None:
    module = _load_module()
    signals = _signals(module, category="global_env_mutation", is_test=False, is_module_scope=True)

    result = module.classify_monkey_patch(signals)

    assert result == "HIGH"


def test_classify_moderate_for_tests_and_attribute_reassignment() -> None:
    module = _load_module()
    signals = _signals(module, category="attribute_reassignment_on_import", is_test=False)

    result = module.classify_monkey_patch(signals)

    assert result == "MODERATE"


def test_classify_safe_for_test_attribute_reassignment() -> None:
    module = _load_module()
    signals = _signals(module, category="attribute_reassignment_on_import", is_test=True)

    result = module.classify_monkey_patch(signals)

    assert result == "SAFE"


def test_classify_moderate_for_test_patch_misuse() -> None:
    module = _load_module()
    signals = _signals(module, category="test_patch_misuse")

    result = module.classify_monkey_patch(signals)

    assert result == "MODERATE"


def test_classify_default_safe() -> None:
    module = _load_module()
    signals = _signals(module, category="other_case")

    result = module.classify_monkey_patch(signals)

    assert result == "SAFE"
