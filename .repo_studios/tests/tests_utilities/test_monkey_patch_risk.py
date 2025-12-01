from __future__ import annotations

from tests.tests_command_center.monkey_patch.helpers import load_monkey_patch_risk_module


def _signals(module, **overrides):
    return module.FindingSignals(
        category=overrides.get("category", ""),
        is_test=overrides.get("is_test", False),
        is_module_scope=overrides.get("is_module_scope", False),
    )


def test_classify_high_risk_non_test_module_scope() -> None:
    module = load_monkey_patch_risk_module()
    signals = _signals(module, category="global_env_mutation", is_test=False, is_module_scope=True)

    result = module.classify_monkey_patch(signals)

    assert result == "HIGH"


def test_classify_moderate_for_tests_and_attribute_reassignment() -> None:
    module = load_monkey_patch_risk_module()
    signals = _signals(module, category="attribute_reassignment_on_import", is_test=False)

    result = module.classify_monkey_patch(signals)

    assert result == "MODERATE"


def test_classify_safe_for_test_attribute_reassignment() -> None:
    module = load_monkey_patch_risk_module()
    signals = _signals(module, category="attribute_reassignment_on_import", is_test=True)

    result = module.classify_monkey_patch(signals)

    assert result == "SAFE"


def test_classify_moderate_for_test_patch_misuse() -> None:
    module = load_monkey_patch_risk_module()
    signals = _signals(module, category="test_patch_misuse")

    result = module.classify_monkey_patch(signals)

    assert result == "MODERATE"


def test_classify_default_safe() -> None:
    module = load_monkey_patch_risk_module()
    signals = _signals(module, category="other_case")

    result = module.classify_monkey_patch(signals)

    assert result == "SAFE"
