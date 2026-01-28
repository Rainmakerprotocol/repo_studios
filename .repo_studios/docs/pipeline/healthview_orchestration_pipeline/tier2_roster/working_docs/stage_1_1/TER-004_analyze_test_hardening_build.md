---
title: "Script Build — analyze_test_hardening.py"
tier: working-document
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - build-document
  - phase-4-artifact
status: active
version: 1.0.0
updated_at: 2026-01-28
tags:
  - stage-1.1
  - producer
  - phase-4
  - TER-004
related_files:
  - .repo_studios/scripts/producers/analyze_test_hardening.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_analyze_test_hardening.yaml
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build — analyze_test_hardening.py

> **Purpose:** Working document for Phase 4 per-script processing of TER-004.
> Documents the compliance state of the Stage 1.1 test hardening analysis producer.
>
> **Record ID:** TER-004
> **Status:** `active`
> **Created:** 2026-01-28
> **Completed:** (pending)

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `analyze_test_hardening.py` |
| **Path** | `.repo_studios/scripts/producers/analyze_test_hardening.py` |
| **Tier Class** | Producer |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | 1135 |
| **Record ID** | TER-004 |
| **Stage** | 1.1 — Test Execution Telemetry |

### 1.1 Purpose

Producer script that analyzes test files for hardening quality issues (missing mocks, long tests,
no assertions, etc.) and emits a positional-encoded HealthView bundle under:

```
.repo_studios/reports/healthview/producer_reports/test_hardening/<YYYYMMDD-HHMM>/
```

### 1.2 Current Capabilities

- **Inputs:** Test file directories (`.repo_studios/tests` by default)
- **Produces:** HealthView bundle with manifest.json, summary.md, telemetry.json
- **Features:**
  - AST-based test file analysis
  - Issue categorization by severity (high, medium, low)
  - Database integration via `create_storage()`
  - Retention pruning via `--artifacts-to-keep`

---

## 2. Current State Analysis

### 2.1 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `Sequence[str] \| None` → `int` | Exit code | ✅ |
| `run(argv)` | `Sequence[str] \| None` → `dict` | Payload dict | ✅ |

#### 2.2.1 Universal Interface Contract

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ✅ | Line L1054 |
| Returns `dict[str, Any]` | ✅ | Return type annotation L1054 |
| `--repo-root` flag supported | ✅ | argparse |
| `--log-level` flag supported | ✅ | argparse |
| Google-style docstring on `run()` | ✅ | Lines L1054-1066 |
| No `sys.exit()` inside `run()` | ✅ | Confirmed |
| Non-interactive | ✅ | No `input()` prompts |

### 2.2 Database Integration

| Aspect | Status | Evidence |
|--------|--------|----------|
| DB markers present | ✅ | Lines L1095-1100 — three `DB_INTEGRATION_MARKER:` comments |
| DB writes via `create_storage()` | ✅ | L1081 |
| Warn-only on failure | ✅ | Library handles graceful degradation |

### 2.3 Tier-3 YAML

| Aspect | Status | Evidence |
|--------|--------|----------|
| Tier-3 YAML exists | ✅ | `tier3_analyze_test_hardening.yaml` |

---

## 3. Compliance Summary

| Category | Status |
|----------|--------|
| HOP Base Package | ✅ |
| Universal Interface | ✅ Returns dict |
| Tier-3 YAML | ✅ |
| DB Integration | ✅ With markers |
| Orchestrator Integration | ✅ |

**Phase 4 Verdict:** ✅ **COMPLIANT**

---

## 4. Implementation Workstreams

- [x] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [x] B. Plan — artifact renaming to HOP base package (already compliant)
- [x] C. Implement — no changes required (already compliant)
- [x] D. Evidence — code references documented
- [x] E. Tier-3 YAML — verified meets template
- [x] F. Orchestrator integration — verified wiring in `run_test_execution_telemetry.py`
- [x] **DONE** — Phase 4 compliance complete (2026-01-28)

---

## 5. Update Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-28 | Initial build document created — Phase 4 COMPLIANT | GitHub Copilot |
