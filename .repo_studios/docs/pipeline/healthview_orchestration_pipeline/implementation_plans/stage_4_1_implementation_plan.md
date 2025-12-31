# Stage 4.1 Implementation Plan: Dependency & Import Hygiene

> **Purpose:** Temporary implementation tracking document for Stage 4.1 HOP migration.
> Delete after migration complete.

## Overview

Stage 4.1 chains a 6-script pipeline (5 producers/utilities + 1 orchestrator) for dependency
hygiene, import graph analysis, placeholder tracking, typecheck compliance, and mypy baseline
refresh.

**Target Contract (HOP):**

- Output root: `.repo_studios/reports/healthview/<tier_class>_reports/<topic>/<YYYYMMDD-HHMM>/`
- Base package: `manifest.json`, `summary.md`, `telemetry.json`
- No pointer files (`latest_*`, `current_*`)

---

## Script Inventory

| Script | Location | Functions | Test File |
|--------|----------|-----------|-----------|
| `generate_dependency_hygiene_report.py` | `.repo_studios/scripts/producers/` | 13 | `test_generate_dependency_hygiene_report.py` |
| `generate_import_graph_report.py` | `.repo_studios/scripts/producers/` | 14 | `test_generate_import_graph_report.py` |
| `scan_code_placeholders.py` | `.repo_studios/scripts/producers/` | 23 | `test_scan_code_placeholders.py` |
| `generate_typecheck_report.py` | `.repo_studios/scripts/producers/` | 31 | `test_generate_typecheck_report.py` |
| `refresh_mypy_baselines.py` | `.repo_studios/scripts/utilities/` | 19 | `test_refresh_mypy_baselines.py` |
| `run_dependency_import_hygiene.py` | `.repo_studios/command_center/scripts/orchestrators/` | 31 | `test_run_dependency_import_hygiene.py` |

**Total: 6 scripts, ~131 functions, 6 test files**

---

## Implementation Phases

### Phase 0: Path Migration Assessment

**Status:** ✅ COMPLETE

Migration summary:

| Script | Status | Test Results |
|--------|--------|--------------|
| `generate_dependency_hygiene_report.py` | ✅ HOP-compliant | 2/2 passing |
| `generate_import_graph_report.py` | ✅ HOP-compliant | 2/2 passing |
| `scan_code_placeholders.py` | ✅ HOP-compliant | 5/5 passing |
| `generate_typecheck_report.py` | ✅ HOP-compliant | 4/4 passing |
| `refresh_mypy_baselines.py` | ⏭️ Skipped (rawview, not healthview) | N/A |
| `run_dependency_import_hygiene.py` | ✅ HOP-compliant | 3/3 passing |

**Total Tests: 16/16 passing**

**Key Observations:**
- All producers use manual path construction with `VIEWER_SLUG` and `TOPIC` constants
- `refresh_mypy_baselines.py` writes to `rawview` not `healthview`
- Orchestrator uses `DEFAULT_HEALTHVIEW_ROOT` with manual assembly
- Some scripts still reference `latest_*` pointer logic (`copy_latest_artifact`, `_update_cleanup_latest`)

### Phase 1: Path & Constants Migration

Update default output paths to use HOP-compliant `build_topic_path()`:

| Script | Current Default | Target Default |
|--------|-----------------|----------------|
| `generate_dependency_hygiene_report.py` | `Path(".repo_studios/reports/producer_reports")` | `build_topic_path("producer", "dependency_hygiene")` |
| `generate_import_graph_report.py` | `Path(".repo_studios/reports/producer_reports")` | `build_topic_path("producer", "import_graph")` |
| `scan_code_placeholders.py` | `Path(".repo_studios/reports/producer_reports")` | `build_topic_path("producer", "code_placeholders")` |
| `generate_typecheck_report.py` | `Path(".repo_studios/reports/producer_reports")` | `build_topic_path("producer", "typecheck_report")` |
| `refresh_mypy_baselines.py` | `Path(".repo_studios/command_center/reports/rawview/mypy_baselines")` | `build_topic_path("utility", "mypy_baselines")` |
| `run_dependency_import_hygiene.py` | Multiple hardcoded paths | `build_topic_path("orchestrator", "dependency_import_hygiene")` |

**Required Changes:**
1. Import `build_topic_path` from `libraries.report_paths`
2. Replace `DEFAULT_OUTPUT_DIR` with `build_topic_path()` calls
3. Remove redundant `VIEWER_SLUG` constants (viewer is implicit in HOP path)
4. Update `TOPIC` / `TOPIC_SLUG` to be the topic slug only (not full path component)

### Phase 2: Discovery Logic

Remove any `latest_*` pointer file dependencies:

- [ ] `_update_cleanup_latest()` in orchestrator (line ~597) - remove or convert to timestamp discovery
- [ ] `copy_latest_artifact` import in `refresh_mypy_baselines.py` - remove if writing pointers
- [ ] Any `latest_*.json` reads in discovery functions
- [ ] `_prune_cleanup_history()` - verify uses timestamp-based retention only

### Phase 3: Output Artifacts

Ensure base package compliance:

- [ ] `manifest.json` with `viewer: "healthview"`, `topic: "<topic_slug>"`
- [ ] `summary.md` human-readable digest
- [ ] `telemetry.json` machine-readable metrics

### Phase 4: Test Updates

Update test expectations for HOP paths and manifest fields:

| Test File | Expected Changes |
|-----------|------------------|
| `test_generate_dependency_hygiene_report.py` | Path expectations, manifest fields |
| `test_generate_import_graph_report.py` | Path expectations, manifest fields |
| `test_scan_code_placeholders.py` | Path expectations, manifest fields |
| `test_generate_typecheck_report.py` | Path expectations, manifest fields |
| `test_refresh_mypy_baselines.py` | Path expectations, remove latest_* assertions |
| `test_run_dependency_import_hygiene.py` | Path expectations, manifest fields |

### Phase 5: Docstring Updates

Add PEP 287 reStructuredText docstrings to all functions:

**Template:**
```python
def function_name(param: Type) -> ReturnType:
    """Brief description.

    :param param: Parameter description.
    :type param: Type
    :returns: Return description.
    :rtype: ReturnType
    :raises ExceptionType: When raised.

    .. note::
        Additional notes.
    """
```

---

## Verification Checklist

- [ ] All 6 scripts use `build_topic_path()` for defaults
- [ ] No `latest_*` pointer files written or read
- [ ] Base package artifacts present in all bundles
- [ ] All tests pass (`pytest` on 6 test files)
- [ ] Mypy clean (`--ignore-missing-imports` on all 6 scripts)
- [ ] PEP 287 docstrings on all ~131 functions

---

## Evidence Links

**Scripts:**

- [generate_dependency_hygiene_report.py](../../../../scripts/producers/generate_dependency_hygiene_report.py)
- [generate_import_graph_report.py](../../../../scripts/producers/generate_import_graph_report.py)
- [scan_code_placeholders.py](../../../../scripts/producers/scan_code_placeholders.py)
- [generate_typecheck_report.py](../../../../scripts/producers/generate_typecheck_report.py)
- [refresh_mypy_baselines.py](../../../../scripts/utilities/refresh_mypy_baselines.py)
- [run_dependency_import_hygiene.py](../../../../command_center/scripts/orchestrators/run_dependency_import_hygiene.py)

**Tests:**

- [test_generate_dependency_hygiene_report.py](../../../../tests/tests_producers/test_generate_dependency_hygiene_report.py)
- [test_generate_import_graph_report.py](../../../../tests/tests_producers/test_generate_import_graph_report.py)
- [test_scan_code_placeholders.py](../../../../tests/tests_producers/test_scan_code_placeholders.py)
- [test_generate_typecheck_report.py](../../../../tests/tests_producers/test_generate_typecheck_report.py)
- [test_refresh_mypy_baselines.py](../../../../tests/tests_utilities/test_refresh_mypy_baselines.py)
- [test_run_dependency_import_hygiene.py](../../../../tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py)

---

## Progress Log

| Date | Phase | Status | Notes |
|------|-------|--------|-------|
| 2024-12-31 | Plan Created | ✅ | Initial inventory complete |
| 2024-12-31 | Phase 0 Assessment | ✅ | All 6 scripts need migration |
| 2024-12-31 | Phase 1 Path Migration | ✅ | 5 scripts migrated to build_topic_path(), refresh_mypy_baselines.py skipped (rawview) |
| 2024-12-31 | Phase 2 Discovery Logic | ✅ | create_storage pattern updated to use empty strings for viewer_slug/topic |
| 2024-12-31 | Phase 3 Output Artifacts | ✅ | All manifests use viewer: "healthview" instead of viewer_slug |
| 2024-12-31 | Phase 4 Test Updates | ✅ | 16/16 tests passing |
| 2024-12-31 | Stage 4.1 COMPLETE | ✅ | Ready for docstring phase |
| 2024-12-31 | Phase 1 | 🔄 | In progress - path migration |
