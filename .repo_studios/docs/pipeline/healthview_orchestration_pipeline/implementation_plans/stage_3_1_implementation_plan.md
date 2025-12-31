---
title: Stage 3.1 Fault Diagnostics Overview — Implementation Plan
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
status: in-progress
version: 1.0.0
updated: 2025-12-31
tags:
  - implementation-plan
  - stage-3-1
  - fault-diagnostics
  - report-paths
related_files:
  - ../tier1_healthview_orchestration_pipeline.md
  - ../tier2_roster/tier2_fault_diagnostics_overview_roster.md
  - ../../../../scripts/producers/collect_faulthandler_reports.py
  - ../../../../scripts/consumers/generate_fault_artifacts.py
  - ../../../command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py
  - ../../../command_center/scripts/orchestrators/run_fault_diagnostics_overview.py
---

# Stage 3.1 Fault Diagnostics Overview — Implementation Plan

## Executive Summary

This plan documents the refactoring of Stage 3.1 scripts to align with the HOP (HealthView
Orchestration Pipeline) contract. The migration introduces `report_paths.py` for centralized path
management and ensures all docstrings follow PEP 287 reStructuredText format.

## Script Inventory (Stage 3.1)

| Script | Category | Location | Functions |
| ------ | -------- | -------- | --------- |
| `collect_faulthandler_reports.py` | Producer | `.repo_studios/scripts/producers/` | 19 functions |
| `generate_fault_artifacts.py` | Consumer | `.repo_studios/scripts/consumers/` | 19 functions |
| `summarize_fault_diagnostics_overview.py` | Summarizer | `.repo_studios/command_center/scripts/summarizers/` | 18 functions |
| `run_fault_diagnostics_overview.py` | Orchestrator | `.repo_studios/command_center/scripts/orchestrators/` | 15 functions |

---

## Phase 0: Prerequisite — Path Migration (✅ COMPLETED)

### 0.1 Import `build_topic_path` from `libraries.report_paths`

**Status:** ✅ Completed

All four scripts now import and use `build_topic_path`:

| Script | Import Statement | Constants Updated |
| ------ | ---------------- | ----------------- |
| `collect_faulthandler_reports.py` | `from libraries.report_paths import build_topic_path` | `DEFAULT_OUTPUT_DIR = build_topic_path("producer", TOPIC_SLUG)` |
| `generate_fault_artifacts.py` | `from libraries.report_paths import build_topic_path` | `DEFAULT_OUTPUT_DIR = build_topic_path("consumer", TOPIC_SLUG)` |
| `summarize_fault_diagnostics_overview.py` | `from libraries.report_paths import build_topic_path` | `DEFAULT_*_OUTPUT_DIR = build_topic_path(...)` for all three tiers |
| `run_fault_diagnostics_overview.py` | `from libraries.report_paths import build_topic_path, HEALTHVIEW_ROOT` | All `DEFAULT_*_OUTPUT` constants use `build_topic_path()` |

### 0.2 Remove Legacy Constants

**Status:** ✅ Completed

- Removed `VIEWER_SLUG` constants from all scripts
- Removed `DEFAULT_PRODUCER_CC`, `DEFAULT_CONSUMER_CC`, `DEFAULT_HEALTHVIEW_ROOT` from orchestrator
- Replaced undefined `VIEWER_SLUG` references with literal `"healthview"` in payload dictionaries

---

## Phase 1: Path & Constants Update

### 1.1 Validate HOP Output Paths

**Status:** ⏳ To Verify

Verify each script writes to the correct HOP path:

| Script | Expected Output Path |
| ------ | -------------------- |
| Producer | `.repo_studios/reports/healthview/producer_reports/faulthandler_reports/<YYYYMMDD-HHMM>/` |
| Consumer | `.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/` |
| Summarizer | `.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/` |
| Orchestrator | `.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/` |

**Verification Command:**

```bash
python -c "from libraries.report_paths import build_topic_path; print(build_topic_path('producer', 'faulthandler_reports'))"
```

### 1.2 Update Remaining Hardcoded Paths

**Status:** ⏳ Pending

Check for remaining hardcoded paths in:

- [ ] `collect_faulthandler_reports.py` line 49: `DEFAULT_RUNS_RELATIVE` still uses `command_center`
- [ ] `generate_fault_artifacts.py`: Verify `RAWVIEW_ROOT` and discovery paths
- [ ] `summarize_fault_diagnostics_overview.py`: Verify input discovery paths
- [ ] `run_fault_diagnostics_overview.py`: Verify all CLI argument defaults

### 1.3 Standardize Topic Slugs

**Status:** ⏳ Pending

Ensure consistent topic slug naming:

| Tier | Topic Slug | Notes |
| ---- | ---------- | ----- |
| Producer | `faulthandler_reports` | Matches `PRODUCER_TOPIC_SLUG` |
| Consumer | `fault_artifacts` | Matches `CONSUMER_TOPIC_SLUG` |
| Summarizer | `fault_diagnostics_overview` | Matches `TOPIC_SLUG` |
| Orchestrator | `fault_diagnostics_overview` | Matches `TOPIC_SLUG` |

---

## Phase 2: Discovery Logic Update

### 2.1 Timestamp-Based Discovery (No Pointer Files)

**Status:** ⏳ Pending

HOP contract requires timestamp-based discovery without `latest_*` pointer files.

**Scripts to Audit:**

- [ ] `collect_faulthandler_reports.py`: `_find_latest_run()` — verify uses directory sorting
- [ ] `generate_fault_artifacts.py`: `_find_latest_outdir()` — verify uses directory sorting
- [ ] `summarize_fault_diagnostics_overview.py`: Discovery of consumer bundles
- [ ] `run_fault_diagnostics_overview.py`: Discovery of upstream artifacts

**Expected Pattern:**

```python
def _find_latest_bundle(base: Path) -> Path | None:
    """Discover latest timestamped bundle via directory sorting.

    :param base: Parent directory containing timestamped subdirectories.
    :type base: Path
    :returns: Path to most recent bundle, or None if no valid bundles found.
    :rtype: Path | None

    .. note::
        Uses lexicographic sort on YYYYMMDD-HHMM format directories.
        No pointer files (``latest_*``) are used per HOP contract.
    """
    candidates = [d for d in base.iterdir() if d.is_dir() and HOP_TIMESTAMP_PATTERN.match(d.name)]
    if not candidates:
        return None
    return max(candidates, key=lambda d: d.name)
```

### 2.2 Input Path Resolution

**Status:** ⏳ Pending

Verify each script correctly resolves its input paths:

| Script | Input Source | Resolution Method |
| ------ | ------------ | ----------------- |
| Producer | Raw faulthandler runs | `_resolve_runs_base()` + `_find_latest_run()` |
| Consumer | Producer report + run dir | `_load_producer_report()` + `_discover_outdir()` |
| Summarizer | Consumer bundle | Timestamp-sorted directory scan |
| Orchestrator | Chains producer → consumer → summarizer | Dynamic import + payload threading |

---

## Phase 3: Output Artifacts Update

### 3.1 Base Package Compliance

**Status:** ⏳ Pending

Verify each script emits the HOP base package:

| Artifact | Producer | Consumer | Summarizer | Orchestrator |
| -------- | -------- | -------- | ---------- | ------------ |
| `manifest.json` | ✅ | ✅ | ✅ | ✅ |
| `summary.md` | ✅ | ✅ | ✅ | ✅ |
| `telemetry.json` | ✅ | ✅ | ✅ | ✅ |

### 3.2 Manifest Schema Compliance

**Status:** ⏳ Pending

Verify manifest payloads include required fields:

```python
{
    "schema_version": int,
    "viewer": "healthview",
    "topic": str,  # topic slug
    "generated_at": str,  # ISO 8601 timestamp
    "run_slug": str,  # YYYYMMDD-HHMM
    "metrics": dict,
    "artifacts": dict,  # relative paths to sibling artifacts
}
```

### 3.3 Retention Enforcement

**Status:** ⏳ Pending

Verify `prune_run_directories()` is called with correct arguments:

```python
# Pattern after migration:
prune_run_directories(
    output_dir,  # Full HOP path (not output_dir / viewer / topic)
    keep=artifacts_to_keep,
    logger=logger,
)
```

---

## Phase 4: Docstring Updates (PEP 287 reStructuredText)

### 4.1 Module Docstrings

**Status:** ⏳ Pending

All four scripts have module docstrings. Update to ensure:

- [x] Output Path Contract section with correct HOP path
- [x] Base Package section listing artifact trio
- [x] CLI Arguments section with parameter descriptions
- [ ] Cross-references using ``:doc:`` and ``:ref:`` roles

### 4.2 Function Docstrings — Producer (19 functions)

**File:** `collect_faulthandler_reports.py`

| Function | Status | Priority | Notes |
| -------- | ------ | -------- | ----- |
| `parse_args` | ⏳ | High | Add `:returns:` with Namespace fields |
| `build_paths` | ⏳ | High | Add `:param:`, `:returns:`, `:rtype:` |
| `build_options` | ⏳ | High | Add `:param:`, `:returns:`, `:rtype:` |
| `configure_logging` | ⏳ | Low | Simple setter |
| `_allow_legacy_runs` | ⏳ | Low | Internal helper |
| `_timestamp_slug` | ⏳ | Medium | Add `:param:`, `:returns:` |
| `_resolve_timestamp` | ⏳ | Medium | Add `:param:`, `:returns:`, `:raises:` |
| `_detect_trigger_type` | ⏳ | Low | Internal helper |
| `_detect_requested_by` | ⏳ | Low | Internal helper |
| `_detect_git_sha` | ⏳ | Medium | Add `:param:`, `:returns:` |
| `_resolve_runs_base` | ⏳ | High | Critical path resolution |
| `_find_latest_run` | ⏳ | High | Discovery logic |
| `_resolve_run_dir` | ⏳ | High | Critical path resolution |
| `_render_markdown` | ⏳ | Medium | Add `:param:`, `:returns:` |
| `build_manifest` | ⏳ | High | Public API |
| `build_telemetry` | ⏳ | High | Public API |
| `_validate_latest` | ⏳ | Medium | Validation helper |
| `run` | ⏳ | High | Primary entry point |
| `main` | ⏳ | Medium | CLI wrapper |

### 4.3 Function Docstrings — Consumer (19 functions)

**File:** `generate_fault_artifacts.py`

| Function | Status | Priority | Notes |
| -------- | ------ | -------- | ----- |
| `_timestamp_slug` | ⏳ | Low | Internal helper |
| `_allow_legacy_runs` | ⏳ | Low | Internal helper |
| `_resolve_runs_base` | ⏳ | Medium | Path resolution |
| `_resolve_runs_base_for_repo` | ⏳ | Medium | Path resolution |
| `_find_latest_outdir` | ⏳ | High | Discovery logic |
| `_discover_outdir` | ⏳ | High | Discovery logic |
| `_is_compatible_producer_report` | ⏳ | Medium | Validation |
| `_load_json` | ⏳ | Low | Utility |
| `_load_producer_report` | ⏳ | High | Critical loading |
| `_top_n_from_env` | ⏳ | Low | Env parsing |
| `_decode_signatures` | ⏳ | High | Data transformation |
| `_write_stacks_csv` | ⏳ | Medium | Output writing |
| `_write_summary` | ⏳ | Medium | Output writing |
| `_serialize_signatures` | ⏳ | Medium | Data transformation |
| `_write_consumer_bundle` | ⏳ | High | Primary output |
| `_prune_history` | ⏳ | Medium | Retention |
| `_parse_args` | ⏳ | High | CLI parsing |
| `run` | ⏳ | High | Primary entry point |
| `main` | ⏳ | Medium | CLI wrapper |

### 4.4 Function Docstrings — Summarizer (18 functions)

**File:** `summarize_fault_diagnostics_overview.py`

| Function | Status | Priority | Notes |
| -------- | ------ | -------- | ----- |
| `_parse_args` | ⏳ | High | CLI parsing |
| `_parse_timestamp` | ⏳ | Medium | Timestamp handling |
| `_resolve_optional_path` | ⏳ | Medium | Path resolution |
| `build_paths` | ⏳ | High | Path construction |
| `build_options` | ⏳ | High | Options construction |
| `configure_logging` | ⏳ | Low | Simple setter |
| `_load_json` | ⏳ | Low | Utility |
| `_normalize_relative` | ⏳ | Medium | Path normalization |
| `_ensure_path` | ⏳ | Medium | Path validation |
| `_find_previous_bundle` | ⏳ | High | Discovery for baseline |
| `_extract_metrics` | ⏳ | High | Data extraction |
| `_coerce_int` | ⏳ | Low | Type coercion |
| `_extract_severity` | ⏳ | Medium | Data extraction |
| `_collect_signature_ids` | ⏳ | Medium | Data extraction |
| `_extract_producer_repeat_offender` | ⏳ | Medium | Data extraction |
| `_build_markdown` | ⏳ | High | Summary generation |
| `run` | ⏳ | High | Primary entry point |
| `main` | ⏳ | Medium | CLI wrapper |

### 4.5 Function Docstrings — Orchestrator (15 functions)

**File:** `run_fault_diagnostics_overview.py`

| Function | Status | Priority | Notes |
| -------- | ------ | -------- | ----- |
| `parse_args` | ⏳ | High | CLI parsing |
| `_parse_timestamp` | ⏳ | Medium | Timestamp handling |
| `_resolve_path` | ⏳ | Medium | Path resolution |
| `build_paths` | ⏳ | High | Path construction |
| `build_options` | ⏳ | High | Options construction |
| `configure_logging` | ⏳ | Low | Simple setter |
| `_load_callable` | ⏳ | High | Dynamic import |
| `_relativize` | ⏳ | Medium | Path normalization |
| `_execute_producer` | ⏳ | High | Pipeline step |
| `_execute_consumer` | ⏳ | High | Pipeline step |
| `_execute_summarizer` | ⏳ | High | Pipeline step |
| `_register_scripts` | ⏳ | Medium | Catalog registration |
| `_summarize_steps` | ⏳ | Medium | Report generation |
| `run` | ⏳ | High | Primary entry point |
| `main` | ⏳ | Medium | CLI wrapper |

### 4.6 PEP 287 Docstring Template

Use this template for function docstrings:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """Short one-line summary.

    Longer description if needed, explaining the purpose and behavior
    of the function in more detail.

    :param param1: Description of first parameter.
    :type param1: Type1
    :param param2: Description of second parameter.
    :type param2: Type2
    :returns: Description of return value.
    :rtype: ReturnType
    :raises ExceptionType: When and why this exception is raised.

    .. note::
        Additional notes about usage or behavior.

    .. seealso::
        :func:`related_function` for related functionality.

    Example::

        >>> result = function_name(arg1, arg2)
        >>> print(result)
        expected_output
    """
```

---

## Phase 5: Test Updates

### 5.1 Existing Test Coverage

**Status:** ⏳ Pending Audit

Locate and audit existing tests:

| Script | Test File | Status |
| ------ | --------- | ------ |
| Producer | `tests/tests_producers/test_collect_faulthandler_reports.py` | ⏳ Locate |
| Consumer | `tests/tests_consumers/test_generate_fault_artifacts.py` | ⏳ Locate |
| Summarizer | `tests/tests_command_center/summarizers/test_summarize_fault_diagnostics_overview.py` | ⏳ Locate |
| Orchestrator | `tests/tests_command_center/orchestrators/test_run_fault_diagnostics_overview.py` | ⏳ Locate |

### 5.2 Test Cases to Add/Update

- [ ] Verify output paths match HOP contract
- [ ] Verify base package artifacts are emitted
- [ ] Verify no pointer files (`latest_*`) are created
- [ ] Verify timestamp-based discovery works correctly
- [ ] Verify retention pruning works with new path structure
- [ ] Verify manifest schema compliance

### 5.3 Integration Test

- [ ] End-to-end pipeline test: producer → consumer → summarizer → orchestrator
- [ ] Verify artifact threading between stages
- [ ] Verify telemetry aggregation

---

## Execution Order

1. **Phase 1.2** — Update remaining hardcoded paths
2. **Phase 1.3** — Validate topic slug consistency
3. **Phase 2.1** — Audit discovery logic for HOP compliance
4. **Phase 3.1–3.3** — Verify output artifacts and retention
5. **Phase 4** — Update all function docstrings (priority order)
6. **Phase 5** — Update tests

---

## Verification Checklist

- [ ] All scripts use `build_topic_path()` for output directories
- [ ] No `VIEWER_SLUG` constants remain (only literals where needed in payloads)
- [ ] No `latest_*` pointer files are created
- [ ] All output paths follow HOP structure
- [ ] All public functions have PEP 287 docstrings
- [ ] All tests pass with new path structure
- [ ] Tier-2 roster updated with evidence links

---

## Update Log

| Date | Author | Changes |
| ---- | ------ | ------- |
| 2025-12-31 | Agent | Initial plan created; Phase 0 marked complete |

