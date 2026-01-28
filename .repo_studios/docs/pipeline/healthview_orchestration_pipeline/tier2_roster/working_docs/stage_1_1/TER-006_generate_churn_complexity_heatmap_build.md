---
title: "Script Build — generate_churn_complexity_heatmap.py"
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
  - aggregator
  - phase-4
  - TER-006
related_files:
  - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/tier2_test_execution_telemetry_roster.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/test_execution_telemetry/tier3_generate_churn_complexity_heatmap.yaml
---

<!-- markdownlint-disable-next-line MD025 -->
# Script Build — generate_churn_complexity_heatmap.py

> **Purpose:** Working document for Phase 4 per-script processing of TER-006.
> Documents the compliance state of the Stage 1.1 churn × complexity heatmap aggregator.
>
> **Record ID:** TER-006
> **Status:** `active`
> **Created:** 2026-01-28
> **Completed:** (pending)

---

## 1. Script Identity

| Field | Value |
|-------|-------|
| **Name** | `generate_churn_complexity_heatmap.py` |
| **Path** | `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` |
| **Tier Class** | Aggregator |
| **Compliance Tier** | A (Report Generator) |
| **Lines** | 862 |
| **Record ID** | TER-006 |
| **Stage** | 1.1 — Test Execution Telemetry |

### 1.1 Purpose

Aggregator script that combines churn (git commit history), complexity (cyclomatic), and failure
metrics into a prioritized heatmap, emitting a HealthView bundle under:

```
.repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap/<YYYYMMDD-HHMM>/
```

### 1.2 Current Capabilities

- **Inputs:** Git history, complexity metrics, test log summaries
- **Produces:** heatmap.json, heatmap.md, bundle_summary.json
- **Features:**
  - Configurable commit window via `--window`
  - Optional precomputed metrics via `--metrics-source`
  - Failure density annotation from test logs
  - Retention pruning via `--artifacts-to-keep`

---

## 2. Current State Analysis

### 2.1 Entry Points

| Entry | Signature | Returns | Status |
|-------|-----------|---------|--------|
| `main(argv)` | `Sequence[str] \| None` → `int` | Exit code | ✅ |
| `run(argv)` | `Sequence[str] \| None` → `dict[str, Any]` | Payload dict | ✅ |

#### 2.1.1 Universal Interface Contract

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `run(argv)` entry point exists | ✅ | Line L684 |
| Returns `dict[str, Any]` | ✅ | Return type annotation L684 |
| `--repo-root` flag supported | ✅ | argparse L68-72 |
| `--log-level` flag supported | ✅ | argparse L82 |
| Google-style docstring on `run()` | ✅ | Lines L684-698 |
| No `sys.exit()` inside `run()` | ✅ | Confirmed |
| Non-interactive | ✅ | No `input()` prompts |

### 2.2 Tier-3 YAML

| Aspect | Status | Evidence |
|--------|--------|----------|
| Tier-3 YAML exists | ✅ | `tier3_generate_churn_complexity_heatmap.yaml` |

---

## 3. Compliance Summary

| Category | Status |
|----------|--------|
| HOP Base Package | ✅ heatmap.json, heatmap.md, bundle_summary.json |
| Universal Interface | ✅ Returns dict |
| Tier-3 YAML | ✅ |
| Orchestrator Integration | ✅ |
| DB Integration | ⏸️ Deferred |

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
