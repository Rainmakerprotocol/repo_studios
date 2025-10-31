# `build_paths` / `build_options` Extraction Brief

**Status:** Ready for implementation (2025-10-30)

This brief captures the concrete plan for centralising the duplicated `build_paths` and `build_options` helpers into the shared `libraries` staging package.

---

## Objectives

1. Provide a single, configurable path/option resolver that mirrors existing script semantics while honouring Repo Studios naming conventions.
2. Reduce duplication across producers and orchestrators ahead of the Phase 3 promotion into the canonical `.repo_studios/library/` tree.
3. Preserve backwards compatibility for callers during the migration by keeping legacy function names as thin wrappers.

---

## Core Deliverables

| Deliverable | Description | Owner |
| --- | --- | --- |
| `libraries/cli_paths.py` (staged module) | Exports `PathsConfig`, `OptionsConfig`, `build_standard_paths`, and `build_standard_options` helpers backed by reusable resolvers (`resolve_repo_root`, `resolve_path`, `normalize_keep_count`). | Agent |
| Wrapper updates | Each producer now imports from `libraries` and exposes its historical `build_paths`/`build_options` names by delegating to the shared helper. | Agent |
| Integration tests | Add parameterised coverage in `tests/tests_library_integration/libraries/test_cli_paths.py` to assert repo-root resolution, relative/absolute overrides, and keep-count normalisation. | Agent |
| Producer regressions | Update targeted producer tests (starting with `validate_metrics_anchor_stubs`) to assert parity with legacy behaviour. | Agent |

---

## Pilot Scope

- **Primary pilot:** `producers/validate_metrics_anchor_stubs.py`
  - Retains existing `Paths` dataclass structure and CLI surface area.
  - Exercises required/optional path resolution, repo-root overrides, and keep-count handling.
- **Secondary follow-on:** `producers/analyze_test_hardening.py` and `producers/scan_monkey_patches.py`
  - Validate optional flag handling and environment-driven overrides (`STRICT`, custom glob paths).

Pilot success criteria:

1. No behavioural drift in command-line defaults or resolved output directories (validated via unit + producer tests).
2. CLI help output remains unchanged (spot-check `--help`).
3. Duplicate matrix entry for `build_paths`/`build_options` decreases across migrated scripts.

---

## Test Strategy

1. **Library integration tests** (`tests/tests_library_integration/libraries/test_cli_paths.py`)
   - Repo-root detection (explicit flag, implicit default).
   - Relative vs. absolute overrides.
   - Optional path handling (`ensure_exists` guard).
   - Keep-count normalisation with minimum clamp.
2. **Producer regression tests**
   - Re-run targeted suites (`pytest tests/tests_producers/test_validate_metrics_anchor_stubs.py`, etc.).
   - Add assertions around resolved path outputs when feasible (e.g., using fixture overrides).
3. **Smoke validation**
   - Execute the affected producers manually with `--repo-root .` and custom overrides to confirm CLI surfaces remain stable on Windows.

---

## Migration Sequence

1. Implement shared helper module under `libraries` and export through `libraries/__init__.py`.
2. Update pilot producer (`validate_metrics_anchor_stubs.py`) to import the helper, delegating through existing `build_paths`/`build_options` wrappers.
3. Run library + producer tests; document results in the run-folder summary.
4. Repeat for subsequent producers, batching similar scripts to minimise churn.
5. Refresh duplicate matrix after each batch to confirm reductions.

---

## Documentation & Reporting

- Update `.repo_studios/command_center/README.md` once the first migration lands, noting the availability of the shared CLI helper.
- Record progress and test results in the active alignment checklist (Phase 3 section) and in the run-folder summary for each extraction session.
- Capture any deviations or script-specific overrides in this brief for future reference.

---

## Open Questions

1. Should keep-count normalisation respect script-specific maxima/minima beyond the shared default of 1? (Proposed: accept optional `minimum` argument per config.)
2. Do we need a convenience helper for multi-output producers (JSON + Markdown + log directories) beyond the standard `output_dir` field? (Proposed: handle case-by-case during migration.)

Document updates as decisions are made during implementation.
