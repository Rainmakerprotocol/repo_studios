---
title: Global Monkey Patching Standard
status: draft
version: 2025-12-07
last_updated: 2025-12-07
owner: repo_studios_ai
tags:
	- testing
	- python
	- monkey-patching
---

<!-- markdownlint-disable MD013 -->

# Global Monkey Patching Standard

This standard defines when Repo Studios permits monkey patching and the safeguards required to limit
unexpected side effects in production and test environments.

## Builtin Constraints

- Avoid patching Python builtins (`len`, `open`, `list`, etc.) outside of tightly scoped, clearly documented tests.
- When a patch is unavoidable, wrap it in fixtures or context managers that guarantee timely teardown.
- Record rationale and risk mitigation steps in the pull request description so future contributors understand the trade-offs.

## Usage Guidelines

- Prefer dependency injection, protocol adapters, or feature flags before reaching for monkey patches; treat
	patches as a last resort for legacy surface areas.
- Scope patches to the minimal module or class required and ensure downstream imports do not accidentally
	inherit the modification.
- Validate that patches do not alter monitoring, metrics emission, or logging contracts used by other
	services.

## Testing Requirements

- Provide regression tests that fail without the patch to prove necessity and prevent accidental removal.
- Use `pytest` fixtures to apply patches; avoid global state changes in module import time.
- Ensure teardown phases restore original objects even when tests error; include `addfinalizer` hooks for
	nested fixtures.

## Operational Controls

- Never ship monkey patches in production code paths without explicit sign-off from the service owner.
- Document any runtime patching (for example hotfix scripts) in the service runbook along with rollback
	steps and monitoring signals to watch.
- Audit existing patches quarterly and replace them with first-class interfaces when feasible.

<!-- markdownlint-enable MD013 -->
