# Stage 7.1 Implementation Plan: Full Diagnostic Suite

> **Purpose:** Temporary implementation tracking document for Stage 7.1 HOP migration.
> Delete after migration complete.

## ✅ STAGE 7.1 COMPLETE

**Completed:** 2025-12-31
**Tests:** 3/3 passing

The meta-orchestrator has been migrated to HOP-compliant output paths using `build_topic_path()`.

---

## Overview

Stage 7.1 is the meta-orchestrator that chains all topic orchestrators (Stages 1.1–6.1)
sequentially via `orchestrate_full_diagnostic.py`.

**Target Contract (HOP):**

- Output root: `.repo_studios/reports/healthview/<tier_class>_reports/<topic>/<YYYYMMDD-HHMM>/`
- Base package: `manifest.json`, `summary.md`, `telemetry.json`
- No pointer files (`latest_*`, `current_*`)

---

## Script Inventory

| Script | Location | Functions | Test File(s) |
|--------|----------|-----------|--------------|
| `orchestrate_full_diagnostic.py` | `.repo_studios/command_center/scripts/orchestrators/` | ~20 | `test_orchestrate_full_diagnostic.py` |

**Total: 1 script, ~20 functions, 1 test file**

---

## Current State Analysis

### Current Output Root

```
DEFAULT_REPORTS_ROOT = Path(".repo_studios/command_center/reports")
```

The meta-orchestrator writes to:
- `.repo_studios/command_center/reports/healthview/full_diagnostic/<YYYYMMDD-HHMM>/`

### Current Artifact Contract

```python
report_artifacts = write_report_artifacts(
    stem=META_TOPIC,
    timestamp=options.run_timestamp,
    output_dir=paths.reports_root,
    artifacts=[...],
    keep=options.artifacts_to_keep,
    viewer=META_VIEWER,      # "healthview"
    topic=META_TOPIC,        # "full_diagnostic"
)
```

### HOP Target

```python
DEFAULT_REPORTS_ROOT = build_topic_path("orchestrator", "full_diagnostic")
# → .repo_studios/reports/healthview/orchestrator_reports/full_diagnostic/

report_artifacts = write_report_artifacts(
    stem=META_TOPIC,
    timestamp=options.run_timestamp,
    output_dir=paths.reports_root,
    artifacts=[...],
    keep=options.artifacts_to_keep,
    viewer="",   # Empty - path already contains viewer
    topic="",    # Empty - path already contains topic
)
```

---

## Implementation Phases

### Phase 1: Path & Constants Migration

**Status:** ✅ COMPLETE

| Change | Current | Target |
|--------|---------|--------|
| Import | N/A | Added `from libraries.report_paths import build_topic_path` |
| `DEFAULT_REPORTS_ROOT` | `Path(".repo_studios/command_center/reports")` | `build_topic_path("orchestrator", "full_diagnostic")` |
| `write_report_artifacts` | `viewer=META_VIEWER, topic=META_TOPIC` | `viewer="", topic=""` |

### Phase 2: Artifact Path Resolution

**Status:** ✅ COMPLETE

Updated `_build_topic_record` function:
- Removed `reports_root` parameter (no longer needed)
- Changed artifact path construction to use `build_topic_path("orchestrator", topic_slug) / run_slug`
- This aligns with how topic orchestrators now write their artifacts

### Phase 3: Test Updates

**Status:** ✅ COMPLETE

Updated test expectations for HOP paths:

| Test File | Expected Changes |
|-----------|------------------|
| `test_orchestrate_full_diagnostic.py` | Path assertions for manifest location |

---

## Verification Checklist

- [x] `orchestrate_full_diagnostic.py` uses `build_topic_path()` for defaults
- [x] No `latest_*` pointer files written or read
- [x] Base package artifacts present in all bundles
- [x] All tests pass - **3/3 passed**
- [ ] Mypy clean (deferred)
- [ ] PEP 287 docstrings (deferred)

---

## Evidence Links

**Scripts:**

- [orchestrate_full_diagnostic.py](../../../../command_center/scripts/orchestrators/orchestrate_full_diagnostic.py)

**Tests:**

- [test_orchestrate_full_diagnostic.py](../../../../tests/tests_command_center/orchestrators/test_orchestrate_full_diagnostic.py)

**Tier-2 Roster:**

- [tier2_full_suite_overview_roster.md](../tier2_roster/tier2_full_suite_overview_roster.md)
