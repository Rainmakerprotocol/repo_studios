# Stage 11.1 Implementation Plan — Available Scripts (Holding Area)

**Status:** ALL PHASES COMPLETE  
**Created:** 2025-12-31  
**Updated:** 2025-12-31  
**Tier-2 Source:** [tier2_available_scripts_roster.md](../tier2_roster/tier2_available_scripts_roster.md)

---

## Purpose

Stage 11.1 is a **holding area** for scripts that are available to HealthView but **not yet wired into any orchestrator chain** (Stages 1.1–7). This plan tracks HOP migration work needed to make these scripts promotion-ready.

**Key difference from Stages 1.1–7.1:** These scripts are NOT part of active orchestration. HOP migration here prepares them for **future promotion** into orchestrators.

---

## Scripts Inventory (12 total)

| ID | Script | Category | Current Output Root | Migration Priority | Classification |
|----|--------|----------|---------------------|-------------------|----------------|
| ASR-001 | `generate_anchor_health_report.py` | consumer | `.repo_studios/reports/consumer_reports/anchor_health_reports/` | HIGH | Candidate for Stage 2.2 |
| ASR-002 | `configure_faulthandler_runtime.py` | utility | `.repo_studios/command_center/reports/rawview/fault_diagnostics_runs/` | LOW | Import-time bootstrap |
| ASR-003 | `dump_faulthandler_snapshot.py` | utility | `.repo_studios/command_center/reports/rawview/fault_snapshots/` | MEDIUM | Candidate for Stage 3.2 |
| ASR-004 | `fault_run_analysis.py` | utility | None (library) | NONE | Library module |
| ASR-005 | `validate_import_boundaries.py` | producer | `.repo_studios/reports/producer_reports/import_boundary_reports/` | HIGH | Candidate for Stage 4.2 |
| ASR-006 | `extract_standards_rules.py` | producer | TBD | MEDIUM | Candidate for Stage 6.2 |
| ASR-007 | `check_inventory_health.py` | producer | TBD | LOW | Questionable |
| ASR-008 | `validate_inventory.py` | producer | TBD | LOW | Questionable |
| ASR-009 | `summarize_health_suite.py` | summarizer | TBD | LOW | Legacy candidate |
| ASR-010 | `render_inventory_views.py` | producer | TBD | NONE | Out-of-scope |
| ASR-011 | `generate_lizard_report.py` | producer | TBD | NONE | Out-of-scope |
| ASR-013 | `test_log_analysis.py` | library | None | NONE | Library module |

---

## Migration Scope

### Scripts Requiring HOP Migration (Priority Order)

#### Phase 1: HIGH Priority (Report-Emitting Candidates)

1. **ASR-001: generate_anchor_health_report.py**
   - Path: `.repo_studios/scripts/consumers/generate_anchor_health_report.py`
   - Current: `.repo_studios/reports/consumer_reports/anchor_health_reports/anchor_health-YYYY-MM-DD_HHMM/`
   - Target: `.repo_studios/reports/healthview/consumer_reports/anchor_health/<YYYYMMDD-HHMM>/`
   - Issues: Emits `latest_*` pointer files, non-standard artifact names
   - Migration: Add `build_topic_path`, update output root, remove pointer file creation

2. **ASR-005: validate_import_boundaries.py**
   - Path: `.repo_studios/scripts/producers/validate_import_boundaries.py`
   - Current: `.repo_studios/reports/producer_reports/import_boundary_reports/<run_id>/`
   - Target: `.repo_studios/reports/healthview/producer_reports/import_boundary/<YYYYMMDD-HHMM>/`
   - Issues: Creates `latest/` subdirectory mirror (pointer-ban violation)
   - Migration: Add `build_topic_path`, update output root, remove `latest/` mirror

#### Phase 2: MEDIUM Priority — COMPLETE

3. **ASR-003: dump_faulthandler_snapshot.py** ✅
   - Path: `.repo_studios/scripts/utilities/dump_faulthandler_snapshot.py`
   - Current: `.repo_studios/command_center/reports/rawview/fault_snapshots/<YYYY-MM-DD_HHMMSS>/`
   - Target: `.repo_studios/reports/healthview/rawview_reports/fault_snapshot/<YYYY-MM-DD_HHMMSS>/`
   - Changes: Added `build_topic_path("rawview", TOPIC_SLUG)`, normalized `manifest.json` (lowercase)
   - Tests: **3/3 PASSED**

4. **ASR-006: extract_standards_rules.py** ⏭️ SKIPPED
   - Path: `.repo_studios/scripts/producers/extract_standards_rules.py`
   - Status: **Library module** — no file output, no HOP migration needed
   - Migration: N/A — exports `extract_rules()` function only

#### Phase 3: LOW Priority — COMPLETE

5. **ASR-002: configure_faulthandler_runtime.py** ✅
   - Path: `.repo_studios/scripts/utilities/configure_faulthandler_runtime.py`
   - Changes: Added `build_topic_path("rawview", TOPIC_SLUG)` for HOP-compliant output
   - Tests: **3/3 PASSED**

6. **ASR-007: check_inventory_health.py** ⏭️ ALREADY COMPLIANT
   - Path: `.repo_studios/scripts/producers/check_inventory_health.py`
   - Status: Already uses HOP-compliant path (`healthview/inventory_health`)
   - No pointer files created

7. **ASR-008: validate_inventory.py** ✅
   - Path: `.repo_studios/scripts/producers/validate_inventory.py`
   - Changes: Added `build_topic_path`, removed `update_latest_artifacts()` function
   - Tests: **1/1 PASSED**

8. **ASR-009: summarize_health_suite.py** ⏭️ DEFERRED
   - Path: `.repo_studios/scripts/summarizers/summarize_health_suite.py`
   - Status: Reads legacy pointer paths from upstream scripts; does not create new pointers
   - Migration: Deferred — will be addressed when upstream scripts migrate

#### No Migration Required

- **ASR-004: fault_run_analysis.py** — Library module (no file output)
- **ASR-006: extract_standards_rules.py** — Library module (no file output)
- **ASR-010: render_inventory_views.py** — Out-of-scope for HealthView
- **ASR-011: generate_lizard_report.py** — Out-of-scope for HealthView
- **ASR-013: test_log_analysis.py** — Library module (no file output)

---

## Phase 1 Implementation Details

### ASR-001: generate_anchor_health_report.py

**Current State (from Tier-2 roster):**
- Entry: `main(argv) -> run(argv)`
- Flags: `--inventory-report`, `--output-dir`, `--artifacts-to-keep`, `--log-level`
- Outputs:
  - Run directory: `anchor_health-YYYY-MM-DD_HHMM/`
  - Artifacts: `summary.json`, `SUMMARY.md`, `bundle_summary.json`, `anchor_report.json`, etc.
  - Pointer files: `latest_summary.json`, `latest_SUMMARY.md`, `anchor_report_latest.json`, etc.
- Retention: `prune_run_directories(keep=N, stem_prefix=anchor_health-)`

**Migration Steps:**
- [x] Add `from libraries.report_paths import build_topic_path`
- [x] Update DEFAULT_OUTPUT_ROOT to use `build_topic_path("consumer", "anchor_health")`
- [x] Remove pointer file creation (`latest_*`, `*_latest.*`)
- [x] Update `create_storage` / `write_report_artifacts` calls with `viewer=""`, `topic=""`
- [x] Verify pruning still works with HOP paths
- [x] Run tests and verify — **3/3 PASSED**

### ASR-005: validate_import_boundaries.py

**Current State (from Tier-2 roster):**
- Entry: `main(argv) -> run(argv)`
- Flags: `--repo-root`, `--graph-path`, `--output-dir`, `--allowlist-path`, `--artifacts-to-keep`, `--strict`, `--log-level`
- Outputs:
  - Run directory: `import_boundary_check-YYYYMMDD_HHMMSS/`
  - Artifacts: `report.json`, `report.md`, `log.txt`, `violations.json`
  - Pointer subtree: `latest/latest_report.json`, `latest/latest_report.md`, etc.
- Retention: `prune_run_directories(keep=N, stem_prefix=import_boundary_check)`

**Migration Steps:**
- [x] Add `from libraries.report_paths import build_topic_path`
- [x] Update DEFAULT_OUTPUT_ROOT to use `build_topic_path("producer", "import_boundary")`
- [x] Remove `latest/` subdirectory mirror creation
- [x] Update `create_storage` / `write_report_artifacts` calls with `viewer=""`, `topic=""`
- [x] Verify pruning still works with HOP paths
- [x] Run tests and verify — **2/2 PASSED**

---

## Tests

| Script | Test File | Status |
|--------|-----------|--------|
| generate_anchor_health_report.py | `tests/tests_consumers/test_generate_anchor_health_report.py` | ✅ 3/3 PASSED |
| validate_import_boundaries.py | `tests/tests_producers/test_validate_import_boundaries.py` | ✅ 2/2 PASSED |
| dump_faulthandler_snapshot.py | `tests/tests_utilities/test_dump_faulthandler_snapshot.py` | ✅ 3/3 PASSED |
| configure_faulthandler_runtime.py | `tests/tests_utilities/test_configure_faulthandler_runtime.py` | ✅ 3/3 PASSED |
| validate_inventory.py | `tests/tests_producers/test_validate_inventory.py` | ✅ 1/1 PASSED |
| check_inventory_health.py | N/A (already HOP-compliant) | ⏭️ SKIPPED |
| extract_standards_rules.py | N/A (library module) | ⏭️ SKIPPED |
| summarize_health_suite.py | N/A (deferred) | ⏭️ DEFERRED |

---

## Verification Checklist

After each script migration:
- [x] `build_topic_path` import added
- [x] Default output root uses HOP path
- [x] No pointer files created (`latest_*`, `*_latest.*`)
- [x] No `latest/` subdirectory mirrors
- [x] `write_report_artifacts` / `create_storage` uses empty strings for viewer/topic
- [x] Pruning mechanism works with new paths
- [x] Tests pass

---

## Update Log

| Date | Change | Tests |
|------|--------|-------|
| 2025-12-31 | Initial plan created from Tier-2 roster analysis | N/A |
| 2025-12-31 | Phase 1 complete: ASR-001, ASR-005 migrated to HOP | 5/5 PASSED |
| 2025-12-31 | Phase 2 complete: ASR-003 migrated, ASR-006 skipped (library) | 8/8 PASSED |
| 2025-12-31 | Phase 3 complete: ASR-002, ASR-008 migrated; ASR-007 already compliant; ASR-009 deferred | 12/12 PASSED |
