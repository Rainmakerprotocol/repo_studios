#!/usr/bin/env python3
"""Shared monkey patch risk classification helpers.

Aligned with ``docs/standards/global/std-global-monkey-patching.md`` so
consumers/aggregators emit consistent severity tiers for scanner findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["HIGH", "MODERATE", "SAFE"]


@dataclass(frozen=True)
class FindingSignals:
    """Signals required to classify a monkey patch finding."""

    category: str
    is_test: bool
    is_module_scope: bool


HIGH_RISK_CATEGORIES = {
    "sys_modules_assignment",
    "import_time_side_effect",
    "builtins_mutation",
    "singleton_rebind",
}

MODERATE_RISK_CATEGORIES = {
  "attribute_reassignment_on_import",
  "setattr_on_import_or_class",
}

GLOBAL_ENV_MUTATION = "global_env_mutation"


def classify_monkey_patch(signals: FindingSignals) -> RiskLevel:
    """Return the HIGH/MODERATE/SAFE bucket for a scan finding.

    Rules mirror the governance standard:
    * Global runtime changes (sys.modules, builtins, singletons, import-time side effects)
      are HIGH unless they are test-contained overrides.
    * Module-scope global env mutations land in HIGH; test-contained or function-scoped
      mutations downgrade to MODERATE to signal pending cleanup.
    * Import-time attribute reassignment and setattr-style overrides are MODERATE when they
      ship with production code and SAFE when isolated to tests.
    * Test patch misuse and similar hygiene gaps are MODERATE so they remain visible but do
      not block remediation queues reserved for HIGH findings.
    * Everything else is treated as SAFE; downstream tooling still records totals for trend
      monitoring.
    """

    category = (signals.category or "").strip()
    is_test = bool(signals.is_test)
    is_module_scope = bool(signals.is_module_scope)

    if category == GLOBAL_ENV_MUTATION:
        if not is_test and is_module_scope:
            return "HIGH"
        return "MODERATE"

    if category in HIGH_RISK_CATEGORIES:
        return "MODERATE" if is_test else "HIGH"

    if category in MODERATE_RISK_CATEGORIES:
      return "MODERATE" if not is_test else "SAFE"

    if category == "test_patch_misuse":
      return "MODERATE"

    # Default fallback: treat remaining categories as SAFE but keep them in reports.
    return "SAFE"
