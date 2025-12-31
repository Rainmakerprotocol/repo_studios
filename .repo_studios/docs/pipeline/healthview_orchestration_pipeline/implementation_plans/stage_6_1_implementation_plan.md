# Stage 6.1 Implementation Plan: Standards Integrity

> **Purpose:** Temporary implementation tracking document for Stage 6.1 HOP migration.
> Delete after migration complete.

## ✅ STAGE 6.1 COMPLETE

**Completed:** 2025-01-XX
**Tests:** 19/19 passing

All 6 scripts migrated to HOP-compliant output paths using `build_topic_path()`.

---

## Overview

Stage 6.1 chains a 6-script pipeline (1 orchestrator, 4 producers, 1 summarizer) for standards
index generation, gap analysis, diff tracking, prompt seeding, and consolidated overview reporting.

**Target Contract (HOP):**

- Output root: `.repo_studios/reports/healthview/<tier_class>_reports/<topic>/<YYYYMMDD-HHMM>/`
- Base package: `manifest.json`, `summary.md`, `telemetry.json`
- No pointer files (`latest_*`, `current_*`)

---

## Script Inventory

| Script | Location | Functions | Test File(s) |
|--------|----------|-----------|--------------|
| `run_standards_integrity.py` | `.repo_studios/command_center/scripts/orchestrators/` | ~24 | `test_run_standards_integrity.py`, `test_run_standards_integrity_helpers.py` |
| `generate_standards_index.py` | `.repo_studios/scripts/producers/` | ~26 | `test_generate_standards_index.py` |
| `analyze_standards_index_gaps.py` | `.repo_studios/scripts/producers/` | 1 | `test_analyze_standards_index_gaps.py` |
| `diff_standards_index.py` | `.repo_studios/scripts/producers/` | ~22 | `test_diff_standards_index.py` |
| `seed_standards_prompts.py` | `.repo_studios/scripts/producers/` | 19 | `test_seed_standards_prompts.py` |
| `summarize_standards.py` | `.repo_studios/scripts/summarizers/` | 14 | `test_summarize_standards.py` |

**Total: 6 scripts, ~106 functions, 7 test files**

---

## Implementation Phases

### Phase 0: Path Migration Assessment

**Status:** ✅ COMPLETE

Review each script for current path patterns:

| Script | Current Output Root | HOP Target |
|--------|---------------------|------------|
| `run_standards_integrity.py` | `.repo_studios/command_center/reports/healthview/standards_integrity/<ts>` | `healthview/orchestrator_reports/standards_integrity/<ts>` |
| `generate_standards_index.py` | `.repo_studios/reports/producer_reports/rawview/standards_index/<ts>` | `healthview/producer_reports/standards_index/<ts>` |
| `analyze_standards_index_gaps.py` | `.repo_studios/command_center/reports/commandview/standards_index_gaps/<ts>` | `healthview/producer_reports/standards_index_gaps/<ts>` |
| `diff_standards_index.py` | `.repo_studios/command_center/reports/rawview/standards_index_diff/<ts>` | `healthview/producer_reports/standards_index_diff/<ts>` |
| `seed_standards_prompts.py` | `.repo_studios/reports/producer_reports/standards_prompt_seeds/<run_id>` | `healthview/producer_reports/standards_prompt_seeds/<ts>` |
| `summarize_standards.py` | `.repo_studios/command_center/reports/healthview/standards_overview/<ts>` | `healthview/summarizer_reports/standards_overview/<ts>` |

**Key Observations:**
- Scripts use mixed viewer slugs (`rawview`, `commandview`, `healthview`)
- `seed_standards_prompts.py` writes `latest_*` pointer files and uses different run ID format
- `analyze_standards_index_gaps.py` is a thin wrapper that imports from command_center
- Different timestamp formats across the chain

### Phase 1: Path & Constants Migration

Update default output paths to use HOP-compliant `build_topic_path()`:

| Script | Current Default | Target Default |
|--------|-----------------|----------------|
| `run_standards_integrity.py` | Hardcoded paths | `build_topic_path("orchestrator", "standards_integrity")` |
| `generate_standards_index.py` | `Path(".repo_studios/reports/producer_reports")` | `build_topic_path("producer", "standards_index")` |
| `analyze_standards_index_gaps.py` | (wrapper) | `build_topic_path("producer", "standards_index_gaps")` |
| `diff_standards_index.py` | Hardcoded path | `build_topic_path("producer", "standards_index_diff")` |
| `seed_standards_prompts.py` | Hardcoded path | `build_topic_path("producer", "standards_prompt_seeds")` |
| `summarize_standards.py` | Hardcoded path | `build_topic_path("summarizer", "standards_overview")` |

**Required Changes:**
1. Import `build_topic_path` from `libraries.report_paths`
2. Replace `DEFAULT_OUTPUT_DIR` with `build_topic_path()` calls
3. Remove redundant `VIEWER_SLUG` constants
4. Change `viewer_slug` → `viewer` in manifest/telemetry

### Phase 2: Discovery Logic

**Status:** ✅ COMPLETE

Removed `latest_*` pointer file dependencies:

- [x] `_write_latest_artifacts()` in `seed_standards_prompts.py` - removed function and call
- [x] Any `latest_*.json` / `latest_*.yaml` reads in discovery functions - none found requiring changes
- [x] Timestamp format standardized to `YYYYMMDD-HHMM`

### Phase 3: Output Artifacts

**Status:** ✅ COMPLETE

Base package compliance verified:

- [x] `manifest.json` with `viewer: "healthview"`, `topic: "<topic_slug>"`
- [x] `summary.md` human-readable digest
- [x] `telemetry.json` machine-readable metrics
- [x] No pointer file artifacts

### Phase 4: Test Updates

**Status:** ✅ COMPLETE

Updated test expectations for HOP paths and manifest fields:

| Test File | Expected Changes |
|-----------|------------------|
| `test_run_standards_integrity.py` | Path expectations, manifest fields |
| `test_run_standards_integrity_helpers.py` | Path expectations |
| `test_generate_standards_index.py` | Path expectations, manifest fields |
| `test_analyze_standards_index_gaps.py` | Path expectations |
| `test_diff_standards_index.py` | Path expectations, manifest fields |
| `test_seed_standards_prompts.py` | Path expectations, remove latest_* assertions |
| `test_summarize_standards.py` | Path expectations, manifest fields |

### Phase 5: Docstring Updates

Add PEP 287 reStructuredText docstrings to all functions (deferred to later phase).

---

## Verification Checklist

- [x] All 6 scripts use `build_topic_path()` for defaults
- [x] No `latest_*` pointer files written or read
- [x] Base package artifacts present in all bundles
- [x] All tests pass (`pytest` on 7 test files) - **19/19 passed**
- [ ] Mypy clean (`--ignore-missing-imports` on all 6 scripts) - deferred
- [ ] PEP 287 docstrings on all ~106 functions - deferred

---

## Evidence Links

**Scripts:**

- [run_standards_integrity.py](../../../../command_center/scripts/orchestrators/run_standards_integrity.py)
- [generate_standards_index.py](../../../../scripts/producers/generate_standards_index.py)
- [analyze_standards_index_gaps.py](../../../../scripts/producers/analyze_standards_index_gaps.py)
- [diff_standards_index.py](../../../../scripts/producers/diff_standards_index.py)
- [seed_standards_prompts.py](../../../../scripts/producers/seed_standards_prompts.py)
- [summarize_standards.py](../../../../scripts/summarizers/summarize_standards.py)

**Tests:**

- [test_run_standards_integrity.py](../../../../tests/tests_command_center/standards_integrity/test_run_standards_integrity.py)
- [test_run_standards_integrity_helpers.py](../../../../tests/tests_command_center/standards_integrity/test_run_standards_integrity_helpers.py)
- [test_generate_standards_index.py](../../../../tests/tests_producers/test_generate_standards_index.py)
- [test_analyze_standards_index_gaps.py](../../../../tests/tests_producers/test_analyze_standards_index_gaps.py)
- [test_diff_standards_index.py](../../../../tests/tests_producers/test_diff_standards_index.py)
- [test_seed_standards_prompts.py](../../../../tests/tests_producers/test_seed_standards_prompts.py)
- [test_summarize_standards.py](../../../../tests/tests_summarizers/test_summarize_standards.py)

**Tier-2 Roster:**

- [tier2_standards_integrity_roster.md](../tier2_roster/tier2_standards_integrity_roster.md)
