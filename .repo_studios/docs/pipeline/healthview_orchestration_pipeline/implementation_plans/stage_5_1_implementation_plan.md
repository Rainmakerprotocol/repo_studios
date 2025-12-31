# Stage 5.1 Implementation Plan: Monkey Patch Oversight

> **Purpose:** Temporary implementation tracking document for Stage 5.1 HOP migration.
> Delete after migration complete.

## Overview

Stage 5.1 chains a 6-script pipeline (1 orchestrator, 1 producer, 1 consumer, 1 aggregator,
1 summarizer, 1 utility) for monkey patch scanning, risk classification, trend analysis,
and consolidated oversight reporting.

**Target Contract (HOP):**

- Output root: `.repo_studios/reports/healthview/<tier_class>_reports/<topic>/<YYYYMMDD-HHMM>/`
- Base package: `manifest.json`, `summary.md`, `telemetry.json`
- No pointer files (`latest_*`, `current_*`)

---

## Script Inventory

| Script | Location | Functions | Test File |
|--------|----------|-----------|-----------|
| `run_monkey_patch_oversight.py` | `.repo_studios/command_center/scripts/orchestrators/` | 20 | `test_run_monkey_patch_oversight.py` |
| `scan_monkey_patches.py` | `.repo_studios/scripts/producers/` | 55 | `test_scan_monkey_patches.py` |
| `classify_monkey_patches.py` | `.repo_studios/scripts/consumers/` | 17 | `test_classify_monkey_patches.py` |
| `analyze_monkey_patch_trends.py` | `.repo_studios/scripts/aggregators/` | 15 | `test_analyze_monkey_patch_trends.py` |
| `summarize_monkey_patch_overview.py` | `.repo_studios/command_center/scripts/summarizers/` | 16 | (none found) |
| `monkey_patch_risk.py` | `.repo_studios/scripts/utilities/` | 1 | `test_monkey_patch_risk.py` |

**Total: 6 scripts, ~124 functions, 5 test files**

---

## Implementation Phases

### Phase 0: Path Migration Assessment

**Status:** ✅ COMPLETE

Migration summary:

| Script | Status | Test Results |
|--------|--------|--------------|
| `run_monkey_patch_oversight.py` | ✅ HOP-compliant | 1/1 passing |
| `scan_monkey_patches.py` | ✅ HOP-compliant | 6/6 passing |
| `classify_monkey_patches.py` | ✅ HOP-compliant | 15/15 passing |
| `analyze_monkey_patch_trends.py` | ✅ HOP-compliant | 3/3 passing |
| `summarize_monkey_patch_overview.py` | ✅ HOP-compliant | (no test file) |
| `monkey_patch_risk.py` | ✅ N/A (pure utility) | 5/5 passing |

**Total Tests: 30/30 passing**

**Key Changes Applied:**
- Added `build_topic_path` import to all scripts
- Updated `DEFAULT_OUTPUT_DIR` / `DEFAULT_OUTPUT_BASE` / `DEFAULT_HEALTHVIEW_ROOT` to use `build_topic_path()`
- Changed `VIEWER_SLUG` from `"commandview"` to `"healthview"` where applicable
- Removed `_update_latest()` pointer file creation in consumer and aggregator
- Updated `create_storage()` calls to use empty strings for viewer/topic
- Updated manifest/telemetry `viewer_slug` → `viewer` fields
- Updated test assertions to match HOP-compliant paths

Review each script for current path patterns:

| Script | Current Pattern | HOP Target |
|--------|-----------------|------------|
| `run_monkey_patch_oversight.py` | `commandview/monkey_patch_oversight/<ts>` | `healthview/orchestrator_reports/monkey_patch_oversight/<ts>` |
| `scan_monkey_patches.py` | `<output_dir>/healthview/monkey_patches/<ts>` | `healthview/producer_reports/monkey_patches/<ts>` |
| `classify_monkey_patches.py` | `consumer_reports/monkey_patch_risk/<ts>` | `healthview/consumer_reports/monkey_patch_risk/<ts>` |
| `analyze_monkey_patch_trends.py` | `aggregator_reports/monkey_patch_trends/<ts>` | `healthview/aggregator_reports/monkey_patch_trends/<ts>` |
| `summarize_monkey_patch_overview.py` | `summarizer_reports/monkey_patch_overview/<ts>` | `healthview/summarizer_reports/monkey_patch_overview/<ts>` |
| `monkey_patch_risk.py` | (utility - no output) | N/A |

**Key Observations:**
- Producer already uses `healthview/` prefix but needs `build_topic_path()` integration
- Consumer/aggregator use legacy `<tier>_reports/` without `healthview/` prefix
- Summarizer uses legacy `summarizer_reports/` without `healthview/` prefix
- Consumer writes `latest_*` pointer files that need removal
- Aggregator writes `latest_*` pointer files that need removal
- `monkey_patch_risk.py` is a pure utility with no I/O (1 function only)

### Phase 1: Path & Constants Migration

Update default output paths to use HOP-compliant `build_topic_path()`:

| Script | Current Default | Target Default |
|--------|-----------------|----------------|
| `run_monkey_patch_oversight.py` | Multiple hardcoded paths | `build_topic_path("orchestrator", "monkey_patch_oversight")` |
| `scan_monkey_patches.py` | `Path(".repo_studios/reports/producer_reports")` | `build_topic_path("producer", "monkey_patches")` |
| `classify_monkey_patches.py` | `Path(".repo_studios/reports/consumer_reports")` | `build_topic_path("consumer", "monkey_patch_risk")` |
| `analyze_monkey_patch_trends.py` | `Path(".repo_studios/reports/aggregator_reports")` | `build_topic_path("aggregator", "monkey_patch_trends")` |
| `summarize_monkey_patch_overview.py` | `Path(".repo_studios/reports/summarizer_reports")` | `build_topic_path("summarizer", "monkey_patch_overview")` |
| `monkey_patch_risk.py` | N/A | N/A (no path changes needed) |

**Required Changes:**
1. Import `build_topic_path` from `libraries.report_paths`
2. Replace `DEFAULT_OUTPUT_DIR` with `build_topic_path()` calls
3. Remove redundant `VIEWER_SLUG` constants (viewer is implicit in HOP path)
4. Update `TOPIC` / `TOPIC_SLUG` to be the topic slug only

### Phase 2: Discovery Logic

Remove `latest_*` pointer file dependencies:

- [ ] `_update_latest()` in `classify_monkey_patches.py` - remove or convert to timestamp discovery
- [ ] `_update_latest()` in `analyze_monkey_patch_trends.py` - remove or convert to timestamp discovery
- [ ] `_latest_pointer()` / `_latest_run_artifact()` in summarizer - convert to timestamp-based discovery
- [ ] Any `latest_*.json` reads in discovery functions

### Phase 3: Output Artifacts

Ensure base package compliance:

- [ ] `manifest.json` with `viewer: "healthview"`, `topic: "<topic_slug>"`
- [ ] `summary.md` human-readable digest
- [ ] `telemetry.json` machine-readable metrics
- [ ] No pointer file artifacts (remove `latest_summary.json`, etc.)

### Phase 4: Test Updates

Update test expectations for HOP paths and manifest fields:

| Test File | Expected Changes |
|-----------|------------------|
| `test_run_monkey_patch_oversight.py` | Path expectations, manifest fields |
| `test_scan_monkey_patches.py` | Path expectations, manifest fields |
| `test_classify_monkey_patches.py` | Path expectations, remove latest_* assertions |
| `test_analyze_monkey_patch_trends.py` | Path expectations, remove latest_* assertions |
| (summarizer - no test file) | Create new test or skip |
| `test_monkey_patch_risk.py` | No changes (pure utility) |

### Phase 5: Docstring Updates

Add PEP 287 reStructuredText docstrings to all functions (deferred to later phase).

---

## Verification Checklist

- [ ] All 6 scripts use `build_topic_path()` for defaults (5 scripts + 1 utility N/A)
- [ ] No `latest_*` pointer files written or read
- [ ] Base package artifacts present in all bundles
- [ ] All tests pass (`pytest` on 5 test files)
- [ ] Mypy clean (`--ignore-missing-imports` on all 6 scripts)
- [ ] PEP 287 docstrings on all ~124 functions (deferred)

---

## Evidence Links

**Scripts:**

- [run_monkey_patch_oversight.py](../../../../command_center/scripts/orchestrators/run_monkey_patch_oversight.py)
- [scan_monkey_patches.py](../../../../scripts/producers/scan_monkey_patches.py)
- [classify_monkey_patches.py](../../../../scripts/consumers/classify_monkey_patches.py)
- [analyze_monkey_patch_trends.py](../../../../scripts/aggregators/analyze_monkey_patch_trends.py)
- [summarize_monkey_patch_overview.py](../../../../command_center/scripts/summarizers/summarize_monkey_patch_overview.py)
- [monkey_patch_risk.py](../../../../scripts/utilities/monkey_patch_risk.py)

**Tests:**

- [test_run_monkey_patch_oversight.py](../../../../tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py)
- [test_scan_monkey_patches.py](../../../../tests/tests_producers/test_scan_monkey_patches.py)
- [test_classify_monkey_patches.py](../../../../tests/tests_consumers/test_classify_monkey_patches.py)
- [test_analyze_monkey_patch_trends.py](../../../../tests/tests_aggregators/test_analyze_monkey_patch_trends.py)
- [test_monkey_patch_risk.py](../../../../tests/tests_utilities/test_monkey_patch_risk.py)

**Tier-2 Roster:**

- [tier2_monkey_patch_oversight_roster.md](../tier2_roster/tier2_monkey_patch_oversight_roster.md)
