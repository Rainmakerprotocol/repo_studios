---
title: Repo Studios Monkey Patch Governance
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
  - repo_studios_team@rainmakerprotocol.dev
status: approved
version: 1.1.0
updated: 2025-10-18
summary: >-
  Guardrails for introducing, auditing, and retiring monkey patches within Repo Studios projects.
tags:
  - monkey_patch
  - standards
legacy_source: .repo_studios_legacy/repo_docs/copilot_standards_monkey_patch.md
---

# Repo Studios Monkey Patch Governance

Audience: Repo Studios automation | Human developers | CI pipelines

Monkey patches are last-resort tools. Use this standard to minimize risk, track exceptions, and maintain escape hatches for automation.

---

## Scope

- Python monkey patches across the workspace, including third-party modules, builtins, and `sys.modules` entries.
- Import-time side effects that mutate global environment variables, adapters, or shared singletons.
- Module-scope usage of `unittest.mock.patch` (or equivalents) without context management.
- Configuration or bootstrap scripts that dynamically alter library behavior at runtime.

> JavaScript or Chainlit UI overrides live in their respective standards; treat those separately.

---

## Principles

- Prefer dependency injection, adapters, feature flags, or upstream fixes over monkey patches.
- Keep patches test-scoped whenever possible and ensure teardown restores prior state.
- Eliminate import-time mutations; move configuration into startup hooks or fixtures.
- Treat builtins and `sys.modules` mutations as emergency-only with explicit rollback plans and tests.

---

## Detection & Baseline

- Primary scanner: `.repo_studios/scan_monkey_patches.py` (AST-first with optional regex fallback).
- Run via `make scan-monkey-patches` or the broader `make repo-insight` suite.
- Use `--strict` to disable regex fallback and fail on parse errors for high signal.
- Review `.repo_studios/monkey_patch/trend_latest.md` for category deltas relative to prior runs.
- Track baseline counts in the docs inventory; ratchet by risky category before reducing overall totals.

---

## Approved Use Cases

- Temporary shims while upstream fixes are in flight and tracked via issue or ADR.
- Instrumentation hooks that cannot be achieved through public extension points.
- Critical hotfixes required to unblock CI or production with documented rollback steps.

If the change can be delivered through configuration, inheritance, or a fork, do not monkey patch.

---

## Authoring Requirements

1. Create a dedicated module under `monkey_patches/` with descriptive filenames (`requests_timeout_patch.py`).
2. Include a module docstring explaining scope, upstream reference, and removal criteria.
3. Add structured logging when the patch activates so telemetry captures usage.
4. Guard imports with `try/except` and fail loudly when target symbols shift.
5. Provide unit tests validating patched behavior and ensuring the original failure would recur without the patch.

```python
"""requests_timeout_patch: enforce sane defaults until upstream bug 12345 lands."""

from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)

_ORIGINAL_TIMEOUT = requests.sessions.Session.request


def _patched_request(self, method, url, **kwargs):
    if "timeout" not in kwargs:
        kwargs["timeout"] = 10
        logger.warning("monkey_patch_timeout", extra={"target": url})
    return _ORIGINAL_TIMEOUT(self, method, url, **kwargs)

requests.sessions.Session.request = _patched_request
```

---

## Refactoring Playbook

1. Identify risky patches using scanner output grouped by category and file.
2. Replace patches with dependency injection, narrow adapter modules, feature flags (default off), or startup configuration hooks.
3. For tests, convert module-scope patches to context managers or fixtures (`autouse=False`) or rely on pytest's `monkeypatch` helpers.
4. Add regression tests validating new seams; remove the patch once upstream fixes land.

---

## Governance & Tracking

- Register every patch in `.repo_studios/inventory_schema/scripts_catalog.yaml` with `governance_flags: [monkey_patch]` and reference tickets.
- Maintain a ledger in `.repo_studios/agent_notes/monkey_patch_log_YYYY-MM-DD.txt` summarizing rationale, owner, and expiry plan.
- Review patches during quarterly maturity checkpoints; escalate stale entries to leadership.
- Capture roll-forward tasks in Jira or the equivalent tracking system.

---

## CI, Ratcheting & Runtime Guards

- Add assertions in smoke tests ensuring patched modules import successfully.
- Install a health check that compares the current patch inventory to the docs catalog, failing CI on drift.
- Block merges when risky category counts increase relative to baseline and track them in governance ledgers.
- Emit metrics (`monkey_patch.activations`) for each invocation and capture structured logs with patch identifiers.
- Gate temporary overrides behind feature flags so staging/canary environments can disable them dynamically.

---

## Removal Process

1. Validate the upstream fix in a feature branch without the patch.
2. Remove the patch module and associated tests.
3. Update inventory and agent notes, linking the closing ticket.
4. Run `make studio-check-inventory-health` and the full QA suite before merging.

---

## Anti-Patterns

- Modifying third-party internals without documenting version constraints.
- Mutating global state outside a dedicated module.
- Introducing patches without regression tests or telemetry.
- Leaving patches without an expiry issue or ADR entry.

---

## Quick Checklists

### When introducing a patch

- [ ] Scoped module under `monkey_patches/` with docstring rationale and expiry plan.
- [ ] Feature flag default-off with ticket/ADR reference.
- [ ] Tests cover patched and unpatched paths.
- [ ] Telemetry emits activation logs/metrics.

### When reviewing existing patches

- [ ] Replace builtins/`sys.modules` edits with DI or adapters where feasible.
- [ ] Move import-time behavior to startup code or fixtures.
- [ ] Update inventory, cleanup logs, and ADRs with current status.
- [ ] Run scanner in strict mode plus `make anchor-health` prior to merge.

---

## References

- Scanner: `.repo_studios/scan_monkey_patches.py`
- Trends: `.repo_studios/compare_monkey_patch_trends.py`
- CI usage guidance: `docs/repo_insight_workflow.md`

---

## Anchor Health Reminder

When editing headings, run `make anchor-health` and confirm `.repo_studios/anchor_health/anchor_report_latest.json` has no duplicate slug regressions.

---

## Agent Block (Machine-Readable)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: monkey-patch-audit
      title: Audit monkey patch compliance
      steps:
        - ensure-inventory-entry: true
        - ensure-tests-cover: true
        - ensure-telemetry: {metrics: monkey_patch.activations, logger: true}
        - ensure-expiry-plan: true
```
<!-- agents:end:agent_instructions -->
