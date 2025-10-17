---
title: repo Standards — Monkey Patch Reduction
audience: [repo, Jarvis2, Developer]
role: [Standards, Operational-Doc]
owners: ["@docs-owners"]
status: active
version: 1.1.0
updated_at: 2025-09-28
tags: [monkey-patch, standards, testing, risk]
related_files:
  - ./repo_standards_project.md
  - ./repo_standards_python.md
  - ./repo_standards_markdown.md
  - ./repo_studios_clean.md
---

# Monkey Patch Reduction Standards

This document defines when monkey patches are acceptable, how to detect them,
and how to reduce or remove them safely.

## Scope

Covers Python-only monkey patches across the repository, including but not
limited to:

* builtins mutation (e.g., `builtins.open = ...`)
* sys.modules injection/rebinding (e.g., `sys.modules["x"] = ...`)
* import-time side effects (module-scope assignments to imported modules)
* global environment mutation at import-time (`os.environ[...] =` or
  `.update(...)`)
* attribute reassignment on third-party imports (e.g.,
  `requests.adapters.DEFAULT_POOLSIZE = ...`)
* bare `patch(...)` calls at module scope or unscoped decorators

## Principles

* Prefer dependency injection, adapters, and feature flags over monkey patches.
* Keep patches test-scoped (context managers/fixtures) and avoid module-scope
  runtime effects.
* Eliminate import-time side effects; perform configuration in startup hooks or
  guarded blocks.
* Treat builtins and sys.modules mutations as last-resort with explicit
  rationale and tests.

## Detection & Baseline

* Primary tool: `.repo_studios/scan_monkey_patches.py` (AST-first, optional regex fallback)
* Run via: `make scan-monkey-patches` or `make repo-insight`.
* Low-noise baseline: re-run with `--strict` to disable regex fallback and fail
  on parse errors.
* Review `.repo_studios/monkey_patch/trend_latest.md` for the compact
  recent scans table and latest-vs-previous deltas.

## Acceptable Uses (with guardrails)

* Test-local patches using `unittest.mock.patch` as context managers or
  function-scope fixtures.
* Temporary, flagged runtime overrides during migration, with:
  * Feature flag default-off
  * Clear TODO and expiry date
  * Unit tests validating fallback path
  * Entry in `docs/decisions.md` or an ADR

## Unacceptable/Risky Patterns (action required)

* builtins mutation at module scope
* sys.modules assignment/injection/rebinding
* import-time side effects changing third-party behavior
* os.environ mutations at import-time
* Module-scope or bare `patch(...)` in tests

## Refactoring Playbook

1) Identify high-risk patches using the scan summary by category and file.
2) Replace with one of:
   * Dependency injection (pass collaborators/functions as params)
   * Small adapter modules (e.g., `adapters/http.py`) that encapsulate behavior
   * Feature flags with explicit defaults and tests
   * Configuration hooks executed at startup (not import-time)
3) For tests:
   * Convert module-scope patches to `with patch(...):` per-test or to fixtures
     with `autouse=False`.
   * Prefer `monkeypatch.setenv`/`setattr` in pytest to restore after each
     test.
4) Add targeted tests covering the new seam/adapter; remove the patch.

## CI & Ratcheting

* Non-blocking: track totals and risky-category counts; flag increases in PR
  summary.
* Ratchet plan: reduce risky categories to zero first, then lower overall
  counts.
* Optional: introduce a soft gate that fails when risky categories increase vs
  previous scan.

## Quick Checklists

* New code:
  * [ ] No module-scope patches
  * [ ] No import-time env mutations
  * [ ] Tests use context-managed patches or fixtures

* Review/cleanup:
  * [ ] Replace builtins/sys.modules edits with DI/adapters
  * [ ] Move import-time behavior to startup paths
  * [ ] Add docs/rationale for any temporary flag-based override

## References

* Scanner: `.repo_studios/scan_monkey_patches.py`
* Trends: `.repo_studios/compare_monkey_patch_trends.py`
* CI usage: `docs/repo_insight_workflow.md`

## Anchor Health Cross-Link

When editing this standards file (adding or renaming H1/H2 headings), run `make anchor-health` and inspect `.repo_studios/anchor_health/anchor_report_latest.json` to avoid reintroducing duplicate slug clusters. Use disambiguating headings if adding new thematic sections (e.g., "Risk Categorization Matrix" instead of another generic "Overview"). See `repo_standards_markdown.md` for governance details.

## Agent Block (Planned)

<!-- agents:begin:agent_instructions -->
```yaml
agents:
  tasks:
    - id: monkey-scan
      title: Scan for monkey patches
      steps: [run_scanner, load_trend_report, categorize_risk]
      severity: warn
    - id: monkey-ratchet
      title: Enforce non-increase of risky categories
      steps: [compare_latest_vs_prev, assert_no_risky_increase]
      severity: warn
    - id: monkey-anchor-sanity
      title: Verify headings uniqueness post-edit
      steps: [run_anchor_health_optional, inspect_anchor_report_latest]
      severity: info
```
<!-- agents:end:agent_instructions -->
