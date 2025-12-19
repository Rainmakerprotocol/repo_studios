---
title: Stage 1.1 Roster — Test Execution Telemetry
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - roster
  - stage-vertical
status: draft
version: 0.1.0
updated_at: 2025-12-19
tags:
  - pipeline
  - healthview
  - hop
  - stage-1
  - test-execution-telemetry
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_implementation.md
  - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py
  - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py
  - .repo_studios/scripts/producers/collect_test_log_reports.py
  - .repo_studios/scripts/producers/generate_test_coverage_inventory.py
  - .repo_studios/scripts/producers/analyze_test_hardening.py
  - .repo_studios/scripts/consumers/generate_test_log_health_report.py
  - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py
  - .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Stage 1.1 Roster — Test Execution Telemetry

> **Purpose:** This Tier-2 vertical deep dive documents Stage 1.1 (Test Execution Telemetry) for the
> HealthView HOP. It inventories the script chain, captures the current vs target I/O contract, and
> defines stop-gates required before code migrations can claim compliance with locked HOP decisions.
>
> Tier-1 source: `tier1_healthview_orchestration_pipeline.md` (Stage 1.1).
> Locked decisions source: `hop_implementation.md`.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-18) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-18).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and stage ordering from the Tier-1 spine:
  `tier1_healthview_orchestration_pipeline.md`.
- Preserve the canonical Tier section order.
- Do not merge aspirational behavior into “Current state”; log it explicitly as a gap or stop-gate.
- When Stage 1.1 code changes begin, enforce the repo standards:
  - code changes + tests
  - ≥80% coverage on touched modules
  - updated Tier-1/Tier-2 docs
  - clean formatting/lint behavior
- After meaningful checkbox edits, run `make -C .repo_studios studio-generate-doc-index` and record
  the timestamp in the Update Log.

---

## 1. Goals & Success Criteria

1. Produce a single authoritative Tier-2 deep dive for Stage 1.1 that engineers and agents can use
   to implement the HOP migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 1.1 code work (artifact invariants, retention defaults, DB marker
   discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 Section 13 links to this doc as the Stage 1.1 Tier-2 roster.
- This doc contains a per-script inspection table (v1) for the full chain.
- This doc lists Stage 1.1 stop-gates that must be closed before Tier-1 can claim Stage 1.1 is HOP-
  compliant.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 1.1 — Test Execution Telemetry
  (`tier1_healthview_orchestration_pipeline.md` → Stage 1.1 section)
- **Tier-2 scope:** This doc covers Stage 1.1 only.
- **Tier-3 dependencies (placeholders):**
  - Tier-3 placeholder — `tier3_cli.yaml` (shared CLI builders)
  - Tier-3 placeholder — `tier3_prune_logs.yaml` (retention + current_run protection)
  - Tier-3 placeholder — `tier3_artifacts.yaml` (3-artifact bundle contract + discovery semantics)
  - Tier-3 placeholder — `tier3_database_integration.yaml` (DB dual-write semantics + schema)

### 2.2 Chain Inventory (Stage 1.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`

**Delegated scripts (6 total, Tier-1 stated chain):**

- Producer: `.repo_studios/scripts/producers/collect_test_log_reports.py`
- Producer: `.repo_studios/scripts/producers/generate_test_coverage_inventory.py`
- Producer: `.repo_studios/scripts/producers/analyze_test_hardening.py`
- Consumer: `.repo_studios/scripts/consumers/generate_test_log_health_report.py`
- Aggregator: `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py`
- Summarizer: `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`

### 2.3 Current vs Target Contract Snapshot (Stage 1.1)

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Exactly three per-run artifacts:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- No pointer files like `latest_*`.
- Default retention is history mode with `keep=5` unless explicitly justified.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite requires `DB_INTEGRATION_MARKER:`.

**Current contract (code evidence):**

- Output root currently defaults under:
  `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<run_slug>/`
  via `--healthview-root` default.
- Timestamp/run slug shape observed in tests: `YYYYmmdd-HHmm` (example: `20251201-0101`).
- Stage 1.1 emits more than three artifacts today:
  - `manifest.json`
  - `telemetry.json`
  - `test_execution_telemetry_summary.md` (markdown summary)
  - `test_execution_telemetry_summary.json` (JSON summary)

This mismatch is treated as a stop-gate for future code changes.

---

## 3. Stage Narrative — Stage 1.1 Test Execution Telemetry

### 3.1 Per-Script Inspection Table (v1)

This section uses a bullet layout (not a wide markdown table) to keep line length ≤100 and improve
scanability.

- `run_test_execution_telemetry.py`
  - **Role:** Orchestrator
  - **Entry surface:** `run(argv)`
  - **Key inputs:** `--logs-dir`, `--test-coverage-xml`, `--heatmap-metrics-source`,
    `--healthview-root`, `--timestamp`
  - **Current outputs:** HealthView run folder under `--healthview-root`
  - **Retention surface:** `--artifacts-to-keep` (default 3)
  - **Notes:** Writes `manifest.json` + `telemetry.json`, then invokes summarizer (adds extra
    artifacts)

- `collect_test_log_reports.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` returns dict
  - **Key inputs:** logs dir (`--logs-dir`)
  - **Current outputs:** producer report directory
  - **Retention surface:** `--artifacts-to-keep` forwarded as `--collector-artifacts-to-keep`
  - **Notes:** Orchestrator reads `warnings_total` and `slow_tests` from returned payload

- `generate_test_coverage_inventory.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` returns exit code
  - **Key inputs:** coverage XML (`--coverage-xml`)
  - **Current outputs:** `test_coverage-*` run directory with `report.json`
  - **Retention surface:** `--coverage-artifacts-to-keep`
  - **Notes:** Orchestrator reads `report.json` summary for coverage status

- `analyze_test_hardening.py`
  - **Role:** Producer
  - **Entry surface:** `run(argv)` returns dict
  - **Key inputs:** repo root, `--output-dir`
  - **Current outputs:** hardening run directory
  - **Retention surface:** `--hardening-artifacts-to-keep`
  - **Notes:** Orchestrator infers output dir from payload fields

- `generate_churn_complexity_heatmap.py`
  - **Role:** Aggregator
  - **Entry surface:** `run(argv)` returns dict
  - **Key inputs:** repo root, `--output-base`, optional `--metrics-source`
  - **Current outputs:** heatmap run directory
  - **Retention surface:** `--heatmap-artifacts-to-keep`
  - **Notes:** Supports churn-only fallback if metrics source missing

- `generate_test_log_health_report.py`
  - **Role:** Consumer
  - **Entry surface:** `run(argv)` returns dict
  - **Key inputs:** logs dir, `--output-base`, `--producer-bundle-dir`
  - **Current outputs:** health report run directory + `bundle_summary`
  - **Retention surface:** `--health-artifacts-to-keep`
  - **Notes:** Orchestrator only runs this step when collect step produced a structured report

- `summarize_test_execution_telemetry.py`
  - **Role:** Summarizer
  - **Entry surface:** `run(argv)` returns dict
  - **Key inputs:** `--manifest`, `--telemetry`, output dir
  - **Current outputs:** summary markdown + JSON artifacts
  - **Retention surface:** `--artifacts-to-keep`
  - **Notes:** Writes extra per-run artifacts (conflicts with 3-artifact invariant)

### 3.2 Stop-Gates and Implementation Checklists

**Stage 1.1 Tier-2 authoring stop-gates (docs-first):**

- [ ] Confirm the canonical `<class>/<topic>` tokens for Stage 1.1 under
  `.repo_studios/reports/healthview/`.
- [ ] Confirm the canonical `<timestamp>` formatting expectation and record it here (do not assume
  `YYYY-MM-DD` or `YYYYmmdd-HHmm` without evidence and an explicit decision).

**Stage 1.1 HOP migration stop-gates (code-phase, later):**

- [ ] Output root migrated to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- [ ] Artifact invariant enforced: exactly `manifest.json`, `summary.md`, `telemetry.json`.
- [ ] No pointer files introduced.
- [ ] Retention defaults align to keep=5 where applicable.
- [ ] If DB writes are added: gate behind `REPO_STUDIOS_DB_ENABLED`, warn-only failures, and include
  `DB_INTEGRATION_MARKER:` at each callsite.
- [ ] Update Tier-1 Stage 1.1 and close contradiction entries as they are resolved.

---

## 4. Signals & Telemetry

**Regression suites (current evidence):**

- `pytest -q .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`

**Telemetry outputs:**

- Stage 1.1 produces `telemetry.json` alongside a manifest containing step outcomes and artifact
  locations.

**Doc evidence workflow:**

- Run `make -C .repo_studios studio-generate-doc-index` after editing this Tier-2 doc and capture
  the timestamp in Update Logs.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates blocked by this doc:**
  - Stage 1.1 migration cannot be considered HOP-compliant until the artifact invariant and output
    root contradictions are resolved.

- **Tier-3 YAML required (placeholders until created):**
  - `tier3_cli.yaml`
  - `tier3_prune_logs.yaml`
  - `tier3_artifacts.yaml`
  - `tier3_database_integration.yaml`

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle)

---

## 6. Instruction Block (Required by Tier Rules)

1. Editors must follow `.github/instructions/markdown.instructions.md` and
   `.github/instructions/pipeline_doc_tiers.instructions.md`.
1. Keep this doc’s section order intact.
1. After changing checkboxes, run `make -C .repo_studios studio-generate-doc-index` and record the
  timestamp in Update Logs.
1. Do not collapse “current vs target” mismatches; keep them explicit and tracked as stop-gates.

---

## 7. Agent Automation Block

<!-- agents:begin:healthview_stage1_1_roster -->
```yaml
audience: [Copilot, Repo_Studios]
intent: stage_roster
rules:
  - require_front_matter: true
  - require_single_h1: true
  - require_update_log: true
  - no_inline_chat_transcripts: true
  - require_language_fences: true
checks:
  - id: hv-stage1-1-contract
    title: Verify current vs target contract captured
    severity: error
  - id: hv-stage1-1-chain
    title: Verify chain inventory includes 6 delegated scripts
    severity: error
  - id: hv-stage1-1-stopgates
    title: Stop-gates include output root + 3-artifact invariant
    severity: error
```
<!-- agents:end:healthview_stage1_1_roster -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-19 | Correct doc-index command + evidence. | repo_ai | 20251219-1058 | doc-index |
| 2025-12-18 | Drafted Stage 1.1 roster doc. | repo_studios_ai | 20251219-1058 | mdlint; doc-index |
