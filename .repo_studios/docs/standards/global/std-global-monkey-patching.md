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

## Governance & Tracking

- Register every patch in `.repo_studios/inventory_schema/scripts_catalog.yaml` with `governance_flags: [monkey_patch]` and reference tickets.
- Maintain a ledger in `.repo_studios/agent_notes/monkey_patch_log_YYYY-MM-DD.txt` summarizing rationale, owner, and expiry plan.
- Review patches during quarterly maturity checkpoints; escalate stale entries to leadership.
- Capture roll-forward tasks in Jira or the equivalent tracking system.

---

## CI & Runtime Guards

- Add assertions in smoke tests ensuring patched modules import successfully.
- Install a health check that compares current monkey patch list against inventory, failing CI on drift.
- Use feature flags to disable patches dynamically in staging environments.
- Emit metrics (`monkey_patch.activations`) for each invocation to track blast radius.

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
