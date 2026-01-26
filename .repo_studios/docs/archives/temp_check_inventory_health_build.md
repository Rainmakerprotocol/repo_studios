---
title: "Script Build Template — check_inventory_health.py"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - build-template
  - phase-4-artifact
status: archived
version: 1.0.0
updated_at: 2026-01-25
tags:
  - stage-12
  - producer
  - phase-4
  - ASR-007
related_files:
  - .repo_studios/scripts/producers/check_inventory_health.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_available_scripts_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/implementation_plans/stage12_template_development_plan.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build Template — check_inventory_health.py

> **Purpose:** Working document for Phase 4 per-script processing of ASR-007.
>
> **Record ID:** ASR-007
> **Status:** `archived` (completed)
> **Created:** 2026-01-25
> **Completed:** 2026-01-25

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `check_inventory_health.py` |
| **Path** | `.repo_studios/scripts/producers/check_inventory_health.py` |
| **Tier Class** | Producer |
| **Lines** | 499 |
| **Record ID** | ASR-007 |
| **Planned Stage** | Questionable (command_center CI vs HealthView) |

### 1.1 Purpose

Validates repository inventory health against thresholds and baselines.
Emits structured artifacts (manifest, summary, telemetry) via database integration storage.

### 1.2 Current Capabilities

- Loads summary JSON from inventory producer output
- Compares against baseline and threshold configurations
- Detects threshold breaches (status limits, minimum assets, consumer requirements)
- Emits HOP base package via `create_storage()` abstraction
- Implements retention pruning via `prune_run_directories()`

---

## 2. Current State Analysis

### 2.1 CLI Interface

```text
usage: check_inventory_health [-h] [--repo-root REPO_ROOT]
                              [--summary SUMMARY] [--baseline BASELINE]
                              [--thresholds THRESHOLDS] [--output-dir OUTPUT_DIR]
                              [--artifacts-to-keep ARTIFACTS_TO_KEEP]
                              [--timestamp TIMESTAMP] [--log-level LOG_LEVEL]
```

### 2.2 Entry Points

| Entry | Signature | Returns |
|-------|-----------|---------|
| `main(argv)` | `list[str] \| None` → `int` | Exit code (0=ok, 1=breach, 2=missing input) |
| `run(argv)` | **MISSING** | — |

### 2.3 Current Output Contract

**Output root:** `.repo_studios/command_center/reports/healthview/inventory_health/<YYYYMMDD-HHMM>/`

**Artifacts (via storage abstraction):**

| Artifact | Format | Description |
|----------|--------|-------------|
| `manifest.json` | JSON | Schema version, status, inputs, viewer/topic slugs |
| `summary.md` | Markdown | Human-readable health report |
| `telemetry.json` | JSON | Execution metrics, issues, deltas |

### 2.4 HOP Compliance Assessment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Uses `build_topic_path()` | ⚠️ | Uses `create_storage()` with viewer/topic slugs |
| Uses `prune_run_directories()` | ✅ | Line 476 |
| Timestamp format `YYYYMMDD-HHMM` | ✅ | `_timestamp_slug()` function |
| No `latest_*` pointers | ✅ | No pointer files created |
| `run(argv)` entry point | ❌ | Only `main(argv)` exists |
| Returns payload dict | ❌ | Returns exit code only |
| Uses library CLI builders | ✅ | Uses `PathsConfig`, `OptionsConfig`, etc. |
| Retention from config | ✅ | `get_keep("check_inventory_health")` |

### 2.5 Gap Analysis

| Gap | Severity | Notes |
|-----|----------|-------|
| No `run(argv)` entry point | Medium | Orchestrators expect `run(argv)` returning payload |
| Output root under `command_center/reports/` | Low | May be intentional for CI usage |
| Already emits base package | ✅ | manifest.json, summary.md, telemetry.json |

---

## 3. Build Plan

### 3.1 Required Modifications

| # | Modification | Priority | Effort |
|---|--------------|----------|--------|
| 1 | Add `run(argv)` wrapper returning payload dict | High | Low |
| 2 | Extract payload from storage writes | Medium | Low |
| 3 | (Optional) Update docstring for HOP compliance | Low | Low |

### 3.2 Decision: Minimal Alignment

**Recommendation:** Add `run(argv)` wrapper only

**Rationale:**
- Script already emits HOP base package correctly
- Storage abstraction handles artifact writing
- Only missing piece is `run(argv)` entry for orchestrator chaining
- Output root location is intentional for CI context

---

## 4. Alteration Locations

### 4.1 Add run(argv) function (after main)

**Location:** Before `if __name__ == "__main__"` (around line 495)

**New code:**

```python
def run(argv: list[str] | None = None) -> dict[str, Any]:
    """Orchestrator-callable entry point returning structured payload.

    Args:
        argv: Command-line arguments (uses sys.argv[1:] if None)

    Returns:
        Payload dict with keys: status, exit_code, run_dir, manifest, telemetry
    """
    # Implementation extracts payload from main() flow
```

---

## 5. Modifications Log

### 5.1 Completed Changes

| # | Change | Date | Evidence |
|---|--------|------|----------|
| 1 | Added `run(argv)` wrapper returning payload dict | 2026-01-25 | Lines 489-598 |
| 2 | Added test `test_run_returns_payload_dict` | 2026-01-25 | test_check_inventory_health.py |

### 5.2 Pending Changes

| # | Change | Status | Blocker |
|---|--------|--------|--------|
| — | All modifications complete | ✅ | — |

---

## 6. Test Section

### 6.1 Existing Tests

| Test File | Lines | Status |
|-----------|-------|--------|
| `.repo_studios/tests/tests_producers/test_check_inventory_health.py` | 189 | inspected |

**Existing test coverage:**

- `test_default_paths_point_to_repo_root` — Path configuration
- `test_reports_written_without_issues` — Happy path, artifacts written
- Additional tests for threshold breaches, baseline comparison

### 6.2 Required Test Updates

| Test | Update | Priority |
|------|--------|----------|
| `test_run_returns_payload` | New test for `run(argv)` entry | High |

---

## 7. Transfer Checklist

- [x] 7.1 All modifications from Section 5 completed
- [x] 7.2 Tests pass (4/4)
- [x] 7.3 Tier-2 roster record (ASR-007) updated
- [x] 7.4 This document status changed to `archived`

---

## 8. Update Log

| Date | Author | Changes | Status |
|------|--------|---------|--------|
| 2026-01-25 | GitHub Copilot | Created working document; identified run(argv) gap | active |
| 2026-01-25 | GitHub Copilot | Added run(argv) wrapper, tests passing (4/4), Tier-2 updated | archived |
