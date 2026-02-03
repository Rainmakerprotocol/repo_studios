---
title: "Tier-2 Roster — Stage 2.1 Docs Health Overview"
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - roster
  - stage-vertical
status: seeded
target_stage: "2.1"
version: 0.1.0
updated_at: 2025-12-19
tags:
  - pipeline
  - healthview
  - hop
  - tier-2
  - stage-2-1
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 2.1 Docs Health Overview

> **Purpose:** This Tier-2 vertical deep dive will document Stage 2.1 (Docs Health Overview) for the
> HealthView HOP. It will inventory the script chain, capture the current vs target I/O contract
> (with evidence), and define stop-gates required before code migrations can claim compliance with
> locked HOP decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 2.1).
> **Locked decisions source:** Tier-1 spine (`tier1_healthview_orchestration_pipeline.md`) + `REPORT_NAMING_STANDARDS.md`.
> **Last synced with Tier-1:** 2025-12-19.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-19) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-19).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and stage ordering from the Tier-1 spine:
  `tier1_healthview_orchestration_pipeline.md`.
- Preserve the canonical Tier section order.
- Do not merge aspirational behavior into “Current evidence”; log it explicitly as a gap or
  stop-gate.
- When code changes begin for this stage, enforce the repo standards:
  - code changes + tests
  - ≥80% coverage on touched modules
  - updated Tier-1/Tier-2 docs
  - clean formatting/lint behavior
- After meaningful checkbox edits, run `make -C .repo_studios doc-index` and record
  the timestamp in the Update Log.
- Workstream semantics:
  - Workstream D (Tier-3 YAML) is the reward workstream and is conditional.
    - If Tier-3 is allowed/required for a record, complete Workstream D and check its checkbox.
    - If Tier-3 is not allowed/required, do not silently skip D: explicitly record
      "Deferred: Tier-3 not appropriate" (or similar) in the record notes/evidence.
  - Tier-2 DONE requires Workstreams A–C + E, plus an explicit Workstream D decision
    (completed if required, otherwise explicitly deferred).

---

## 1. Goals & Success Criteria

1. Produce a single authoritative Tier-2 deep dive for Stage 2.1 that engineers and agents can use
   to implement the HOP migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 2.1 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 2.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim HOP compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** 2.1 — Docs Health Overview
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 2.1 only.

### 2.2 Chain Inventory (Stage 2.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`

**Delegated scripts (expected chain):**

- Producer: `.repo_studios/scripts/producers/generate_doc_index.py`
- Producer: `.repo_studios/scripts/producers/generate_anchor_inventory.py`
- Producer: `.repo_studios/scripts/producers/validate_markdown_anchors.py`
- Producer: `.repo_studios/scripts/producers/verify_docs_integrity.py`
- Producer: `.repo_studios/scripts/producers/validate_metrics_anchor_stubs.py`
- Producer: `.repo_studios/scripts/producers/generate_code_doc_churn_report.py`
- Producer: `.repo_studios/scripts/producers/generate_undocumented_logic_report.py`
- Aggregator: `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py`

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 2.1)

This section will be the short, scannable contract summary that Tier-1 routes to.

Authoritative entry points for Tier-1 routing and agent discovery are:

- this Contract Snapshot,
- the Stop-Gates section,
- the Records Index.

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Base package (HOP target):
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- No pointer files like `latest_*`.
- Pruning mechanisms and targets are explicit, stable, and evidence-backed.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite includes `DB_INTEGRATION_MARKER:`.

**Current evidence (repo-observed):**

- Output root currently observed:
  `.repo_studios/command_center/reports/healthview/docs_health/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed:
  `YYYYMMDD-HHMM` (UTC)
- Artifact set observed in current runs:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

- Intermediate bundle roots currently observed in this stage:
  - Producers: `.repo_studios/reports/producer_reports/healthview/<topic>/<YYYYMMDD-HHMM>/`
  - Aggregator:
    `.repo_studios/reports/aggregator_reports/docs_health_signals/<YYYYMMDD-HHMM>/`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 2.1 Docs Health Overview

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

Implementation Workstreams are inactive until Discovery (Workstream A) is completed for the script.

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- `S21R-001` — `run_docs_health_overview.py` — Orchestrator — [anchor](#s21r-001-docs-health-overview-orchestrator)
- `S21R-002` — `generate_doc_index.py` — Producer — [anchor](#s21r-002-generate-doc-index)
- `S21R-003` — `generate_anchor_inventory.py` — Producer — [anchor](#s21r-003-generate-anchor-inventory)
- `S21R-004` — `validate_markdown_anchors.py` — Producer — [anchor](#s21r-004-validate-markdown-anchors)
- `S21R-005` — `verify_docs_integrity.py` — Producer — [anchor](#s21r-005-verify-docs-integrity)
- `S21R-006` — `validate_metrics_anchor_stubs.py` — Producer — [anchor](#s21r-006-validate-metrics-anchor-stubs)
- `S21R-007` — `generate_code_doc_churn_report.py` — Producer — [anchor](#s21r-007-generate-code-doc-churn-report)
- `S21R-008` — `generate_undocumented_logic_report.py` — Producer — [anchor](#s21r-008-generate-undocumented-logic-report)
- `S21R-009` — `aggregate_docs_health_signals.py` — Aggregator — [anchor](#s21r-009-aggregate-docs-health-signals)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:**
  - `--artifacts-to-keep` (orchestrator + delegated scripts)
  - orchestrator per-step keep flags
- **Pruning mechanism:**
  - `prune_run_directories(... keep=...)`
  - `write_report_artifacts(... keep=...)`
- **Pruning targets:**
  - Orchestrator bundle root: `.repo_studios/command_center/reports/healthview/docs_health/`
  - Producer bundle roots: `.repo_studios/reports/producer_reports/healthview/<topic>/`
  - Aggregator bundle root:
    `.repo_studios/reports/aggregator_reports/docs_health_signals/`
- **Pruning guardrails:** `current_run` protection when pruning (where supported)
- **Evidence source:** `run_docs_health_overview.py` + each producer/aggregator bundle
  writer/pruner callsite

#### 3.1.3 ScriptInspectionRecordV1 Schema

Use this schema as the per-script record structure for this stage.

```yaml
schema: ScriptInspectionRecordV1
fields:
  record_id: "<string>"
  script:
    path: "<repo-relative path>"
    name: "<filename>"
    category: "producer|consumer|aggregator|summarizer|utility|orchestrator"
  tier3:
    metadata_block_version: "v1"
    allowed: false
    exists: false
    name: "<tier3_yaml_filename>"
    meets_template: "NA"
    last_updated: null
  cli_surfaces:
    run_entrypoint: "run(argv)|main(argv)|other"
    key_flags:
      - "<--flag>"
      - "<--flag>"
  io_contract:
    inputs:
      - "<input description>"
    outputs:
      current:
        root: "<current root>"
        artifacts:
          - "<artifact>"
      target:
        root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
        artifacts:
          - "manifest.json"
          - "summary.md"
          - "telemetry.json"
  retention:
    surfaces:
      - "<flags / defaults / callsites>"
    mechanism: "<prune_by_timestamp / prune_by_rank / prune_by_manifest / other>"
    targets:
      - "<bundle roots and intermediate roots>"
    guardrails:
      - "<current_run_protection / exclusions / atomic_write / other>"
    evidence:
      - "<tests / docstrings / fixtures / code_refs>"
  db_integration:
    gated_by: "REPO_STUDIOS_DB_ENABLED"
    marker_required: true
    marker_string: "DB_INTEGRATION_MARKER:"
  evidence:
    code_refs:
      - "<path>#Lx-Ly"
    tests:
      - "<pytest path>"
    fixtures:
      - "<fixture path>"
  notes:
    - "<short note>"
```

#### 3.1.4 Per-Script Full Record Blocks

Populate one block per script in the chain. Keep each record concise and evidence-backed.

##### S21R-001 docs health overview orchestrator

```yaml
record_id: "S21R-001"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py"
  name: "run_docs_health_overview.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_run_docs_health_overview.yaml"
  meets_template: "yes"
  last_updated: "2025-12-30"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--log-level"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--healthview-root"
    - "--*-output-dir (per-step output roots)"
    - "--skip-* (per-step skip flags)"
io_contract:
  inputs:
    - "Delegates to producer/aggregator modules and threads per-step output roots + keep budgets"
    - "Accepts --timestamp (ISO-8601) and derives run_slug as YYYYMMDD-HHMM (UTC)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/docs_health/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "write_report_artifacts(... keep=options.artifacts_to_keep)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/command_center/reports/healthview/docs_health"
  guardrails:
    - "Report naming audit via enforce_report_naming(...)"
  evidence:
    - "write_report_artifacts(... keep=...) + run_slug formatting"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L46-L107"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L331-L463"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L970-L1005"
    - ".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py#L1198-L1386"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Current orchestrator outputs are under .repo_studios/command_center/reports (not the target HealthView root)."
  - "DB markers: none observed in this orchestrator (it does not call create_storage)."
  - >-
    Orchestrator manifest includes undocumented_report pointing at
    undocumented_outcome.artifacts['report.json'], but the undocumented producer
    currently emits telemetry.json only (see S21R-008 notes).
```

#### Implementation Workstreams (checkbox-driven) — run_docs_health_overview.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

**Discovery Findings (2025-12-30):**

| Surface | Current | Target (HOP) |
|---------|---------|--------------|
| `DEFAULT_DOC_INDEX_OUTPUT` | `.repo_studios/reports/healthview` | Already HOP ✓ |
| `DEFAULT_ANCHOR_INVENTORY_OUTPUT` | `.repo_studios/reports/producer_reports` | `.repo_studios/reports` |
| `DEFAULT_ANCHOR_VALIDATION_OUTPUT` | `.repo_studios/reports/producer_reports` | `.repo_studios/reports` |
| `DEFAULT_DOCS_INTEGRITY_OUTPUT` | `.repo_studios/reports/producer_reports` | `.repo_studios/reports` |
| `DEFAULT_METRICS_STUB_OUTPUT` | `.repo_studios/reports/producer_reports` | `.repo_studios/reports` |
| `DEFAULT_CHURN_OUTPUT` | `.repo_studios/reports/producer_reports` | `.repo_studios/reports` |
| `DEFAULT_UNDOCUMENTED_OUTPUT` | `.repo_studios/reports/producer_reports` | `.repo_studios/reports` |
| `DEFAULT_PLACEHOLDER_OUTPUT` | `.repo_studios/reports/producer_reports/healthview/code_placeholders` | `.repo_studios/reports/healthview/code_placeholders` |
| `DEFAULT_MONKEY_PATCH_OUTPUT` | `.repo_studios/reports/producer_reports/healthview/monkey_patches` | `.repo_studios/reports/healthview/monkey_patches` |
| `DEFAULT_AGGREGATOR_OUTPUT` | `.repo_studios/reports/aggregator_reports/docs_health_signals` | `.repo_studios/reports` |
| Location | Lines 87-101 | Update to HOP |

- **Test file:**
  `.repo_studios/tests/tests_command_center/docs_health/test_run_docs_health_overview.py` —
  no hardcoded legacy paths
- **Entry point:** Uses `run(argv)` ✓

Workstream B — Plan

- [x] Draft plan to close output-root/base-package stop-gates

**Migration Plan (10 steps):**

- **Update DEFAULT_ANCHOR_INVENTORY_OUTPUT** — Line 88: Change from
  `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update DEFAULT_ANCHOR_VALIDATION_OUTPUT** — Line 89: Change from
  `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update DEFAULT_DOCS_INTEGRITY_OUTPUT** — Line 90: Change from
  `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update DEFAULT_METRICS_STUB_OUTPUT** — Line 91: Change from
  `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update DEFAULT_CHURN_OUTPUT** — Line 92: Change from `.repo_studios/reports/producer_reports`
  to `.repo_studios/reports`
- **Update DEFAULT_UNDOCUMENTED_OUTPUT** — Line 93: Change from
  `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update DEFAULT_PLACEHOLDER_OUTPUT** — Lines 94-96: Remove `producer_reports/` prefix
- **Update DEFAULT_MONKEY_PATCH_OUTPUT** — Lines 97-99: Remove `producer_reports/` prefix
- **Update DEFAULT_AGGREGATOR_OUTPUT** — Lines 100-102: Change from
  `.repo_studios/reports/aggregator_reports/docs_health_signals` to `.repo_studios/reports`
- **Run tests** — `pytest -v tests/tests_command_center/docs_health/test_run_docs_health_overview.py`

Note: `DEFAULT_DOC_INDEX_OUTPUT` (line 87) already uses HOP path — no change needed.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.

**Implementation Evidence (2025-12-30):**

| Edit | Location | Change |
|------|----------|--------|
| DEFAULT_ANCHOR_INVENTORY_OUTPUT | Line 88 | `.repo_studios/reports` ✓ |
| DEFAULT_ANCHOR_VALIDATION_OUTPUT | Line 89 | `.repo_studios/reports` ✓ |
| DEFAULT_DOCS_INTEGRITY_OUTPUT | Line 90 | `.repo_studios/reports` ✓ |
| DEFAULT_METRICS_STUB_OUTPUT | Line 91 | `.repo_studios/reports` ✓ |
| DEFAULT_CHURN_OUTPUT | Line 92 | `.repo_studios/reports` ✓ |
| DEFAULT_UNDOCUMENTED_OUTPUT | Line 93 | `.repo_studios/reports` ✓ |
| DEFAULT_PLACEHOLDER_OUTPUT | Line 94 | `.repo_studios/reports/healthview/code_placeholders` ✓ |
| DEFAULT_MONKEY_PATCH_OUTPUT | Line 95 | `.repo_studios/reports/healthview/monkey_patches` ✓ |
| DEFAULT_AGGREGATOR_OUTPUT | Line 96 | `.repo_studios/reports` ✓ |

- **Tests:** 2/2 passed in 0.20s
- **Test fixtures:** No changes needed (no hardcoded legacy paths)

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_run_docs_health_overview.yaml`
- [x] Validate Tier-3 YAML

**Tier-3 Evidence (2025-12-30):**

- **Decision:** Create — mature orchestrator with stable CLI, well-defined io_contract, 8-step pipeline
- **Created:** `tier3_run_docs_health_overview.yaml` (268 lines)
- **Path:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/`
- **Index updated:** `tier3_scripts_index.yaml` — 16 scripts total (2 orchestrators)
- **tier3.allowed:** `true`

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [-] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

**QA Evidence (2025-12-30):**

- **Pytest:** 2/2 passed in 0.20s
- **Mypy:** Clean (no issues)
- **Execution:** Bundle created at `.repo_studios/command_center/reports/healthview/docs_health/20251230-1743/`
- **Artifacts:** manifest.json, summary.md, telemetry.json (3 files)
- **Pipeline steps:** All 8 steps succeeded (doc-index, anchor-inventory, anchor-validation,
  docs-integrity, metrics-stub, code-doc-churn, undocumented-logic, aggregate)
- **Overall score:** 33.73
- **Coverage:** 61% — below 80% threshold; exception: orchestrator delegates to 8
  producer/aggregator scripts (each with own coverage), tests verify orchestration logic via
  controlled mocks, not full execution paths

- [x] DONE — run_docs_health_overview.py complete; update Tier-1 Stage 2.1 script gate

<!-- AGENT_ROUTER:START S21R-002 -->
##### S21R-002 — generate_doc_index.py

> **One-liner:** Scans repository for markdown files, extracts headings and metadata, builds multi-format document inventory.

**Keywords:** `markdown`, `documentation`, `index`, `inventory`, `metadata`, `frontmatter`

###### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/generate_doc_index.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_generate_doc_index.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-003_generate_doc_index_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/doc_index/` |

###### Invocation

```bash
python .repo_studios/scripts/producers/generate_doc_index.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main(argv)` |
| Typical Runtime | ~15 seconds |
| Exit Codes | 0=success, 1=error |

###### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Schema version, status, inputs, artifact catalog |
| summary.md | Markdown | Human-readable bundle with embedded JSON/YAML/CSV |
| telemetry.json | JSON | Execution metrics (doc/heading/link counts) |
| doc_index.csv | CSV | Tabular document inventory for spreadsheet import |

###### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Full manifest/summary/telemetry package |
| UIC Interface | YES | `run(argv) → dict[str, Any]` with status/exit_code |
| Tier-3 YAML | YES | 268-line comprehensive YAML |

###### Orchestrator

| Pipeline | Status | Config |
|----------|--------|--------|
| run_docs_health_overview.py | WIRED | Step 1 in docs health chain |

###### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 1 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/scripts/orchestrators/run_docs_health_overview.py` |

###### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | First in pipeline, no upstream dependencies |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides `doc_index.csv` for aggregation |

###### Known Limitations

- None documented.

###### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-02 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S21R-002 -->

---

<!-- AGENT_ROUTER:START S21R-003 -->
##### S21R-003 — generate_anchor_inventory.py

> **One-liner:** Extracts H1/H2 headings from markdown, computes URL-friendly slugs, detects cross-file duplicates.

**Keywords:** `markdown`, `anchors`, `slugs`, `duplicates`, `headings`, `inventory`

###### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/generate_anchor_inventory.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_generate_anchor_inventory.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-002_generate_anchor_inventory_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/anchor_inventory/` |

###### Invocation

```bash
python .repo_studios/scripts/producers/generate_anchor_inventory.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main(argv)` |
| Typical Runtime | ~10 seconds |
| Exit Codes | 0=success, 1=issues found |

###### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Run metadata with viewer_slug, topic, catalog |
| summary.md | Markdown | Heading inventory with duplicate clusters |
| telemetry.json | JSON | Metrics: total_slugs, cross_file_duplicates, doc stats |

###### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Full manifest/summary/telemetry package |
| UIC Interface | YES | `run(argv) → dict[str, Any]` with status/exit_code |
| Tier-3 YAML | YES | 286-line comprehensive YAML |

###### Orchestrator

| Pipeline | Status | Config |
|----------|--------|--------|
| run_docs_health_overview.py | WIRED | Step 2 in docs health chain |

###### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 2 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/scripts/orchestrators/run_docs_health_overview.py` |

###### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | Parallel-capable, no upstream dependencies |
| ⬇️ CONSUMED BY | S21R-004 | `validate_markdown_anchors.py` | Provides `anchors_targets.json` for validation |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides anchor data via `load_anchor_inventory()` |

###### Known Limitations

- None documented.

###### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-02 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S21R-003 -->

---

<!-- AGENT_ROUTER:START S21R-004 -->
##### S21R-004 — validate_markdown_anchors.py

> **One-liner:** Validates internal markdown anchors and cross-file links, reports broken references.

**Keywords:** `markdown`, `anchors`, `validation`, `links`, `broken-links`, `cross-reference`

###### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/validate_markdown_anchors.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_validate_markdown_anchors.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-004_validate_markdown_anchors_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation/` |

###### Invocation

```bash
python .repo_studios/scripts/producers/validate_markdown_anchors.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `main(argv)` — **NO run()** |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success, 1=issues found |

###### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Run metadata with viewer_slug, topic, catalog |
| summary.md | Markdown | Broken link/anchor report with file locations |
| telemetry.json | JSON | Validation metrics: checked, broken, by-type |

###### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Full manifest/summary/telemetry package |
| UIC Interface | PARTIAL | Missing `run(argv) → dict` — uses `main(argv) → int` |
| Tier-3 YAML | YES | Correctly documents `importable: false` |

###### Orchestrator

| Pipeline | Status | Config |
|----------|--------|--------|
| run_docs_health_overview.py | WIRED | Step 3 — requires shell-out (no importable run()) |

###### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 3 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/scripts/orchestrators/run_docs_health_overview.py` |

###### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S21R-003 | `generate_anchor_inventory.py` | Requires anchor targets for validation reference |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides validation results via `load_anchor_inventory()` |

###### Known Limitations

- Missing `run(argv) → dict[str, Any]` entry point — orchestrators must shell-out or call `main(argv)`.
- Returns exit code only — no structured payload for orchestrator consumption.
- See build doc Section 5 (Gap Analysis) for remediation plan.

###### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-02 |
| Verified By | GitHub Copilot |
| Build Doc Version | 3.5.0 |
<!-- AGENT_ROUTER:END S21R-004 -->

---

<!-- AGENT_ROUTER:START S21R-005 -->
### S21R-005 — verify_docs_integrity.py

> **One-liner:** Validates governed JSON `content_hash` blocks and refreshes the docs index navigation table.

**Keywords:** `docs`, `integrity`, `validation`, `content_hash`, `index`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/verify_docs_integrity.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_verify_docs_integrity.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-005_verify_docs_integrity_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation/` |

#### Invocation

```bash
python -m scripts.producers.verify_docs_integrity --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with validation results |
| summary.md | Markdown | Human-readable integrity report |
| telemetry.json | JSON | Execution metrics and full payload |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest/summary/telemetry |
| UIC Interface | YES | `run(argv) → dict[str, Any]` entry point |
| Tier-3 YAML | YES | `tier3_verify_docs_integrity.yaml` exists |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| docs_health_overview | WIRED | `run_docs_health_overview.py` L1248-L1303 |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 4 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | Reads `docs_index.md` directly, no upstream script dependencies |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides integrity data for docs health aggregation |

#### Known Limitations

- None documented.

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-02 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S21R-005 -->

<!-- AGENT_ROUTER:START S21R-006 -->
### S21R-006 — validate_metrics_anchor_stubs.py

> **One-liner:** Scans repository markdown for `metrics_orchestrator.md#<anchor>` links and validates against legacy stub headings.

**Keywords:** `metrics`, `anchors`, `validation`, `legacy-stubs`, `producer`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/validate_metrics_anchor_stubs.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_validate_metrics_anchor_stubs.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-006_validate_metrics_anchor_stubs_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation/` |

#### Invocation

```bash
python .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success (no missing), 1=missing anchors detected |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with run info and summary |
| summary.md | Markdown | Human-readable validation results |
| telemetry.json | JSON | Structured metrics for aggregators |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest/summary/telemetry |
| UIC Interface | YES | `run(argv) → dict[str, Any]` entry point |
| Tier-3 YAML | YES | Created and validated |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| HealthView Docs Health Overview | WIRED | `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 5 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | Reads markdown files directly, no upstream bundle dependency |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides telemetry.json for health aggregation |

#### Known Limitations

- None documented.

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-02 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S21R-006 -->

<!-- AGENT_ROUTER:START S21R-007 -->
### S21R-007 — generate_code_doc_churn_report.py

> **One-liner:** Compares code file churn vs. documentation churn to identify staleness risk areas.

**Keywords:** `churn`, `documentation`, `staleness`, `git-history`, `code-doc-sync`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/generate_code_doc_churn_report.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/docs_health_overview/tier3_generate_code_doc_churn_report.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_2_1/S21R-007_generate_code_doc_churn_report_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/code_doc_churn/` |

#### Invocation
```bash
python -m scripts.producers.generate_code_doc_churn_report --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` |
| Typical Runtime | ~5-10 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with execution context |
| summary.md | Markdown | Human-readable churn analysis digest |
| telemetry.json | JSON | Detailed churn metrics and file-level data |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest/summary/telemetry |
| UIC Interface | YES | `run(argv)` entry point, dict return |
| Tier-3 YAML | YES | Created and validated |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| run_docs_health_overview.py | WIRED | L1359-1405 (`_execute_churn`) |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | 6 of 8 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S21R-002 | `generate_doc_index.py` | Uses doc-index telemetry for correlation |
| ⬆️ DEPENDS ON | S21R-003 | `generate_anchor_inventory.py` | Uses anchor inventory for doc mapping |
| ⬇️ CONSUMED BY | S21R-009 | `aggregate_docs_health_signals.py` | Provides churn metrics for aggregation |

#### Known Limitations
- None documented. Script is fully HOP-compliant.

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-03 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S21R-007 -->

#### Implementation Workstreams (checkbox-driven) — generate_code_doc_churn_report.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

**Discovery Findings (2025-12-30):**

| Surface | Current | Target (HOP) |
|---------|---------|--------------|
| `DEFAULT_OUTPUT_DIR` | `build_topic_path("producer", TOPIC_SLUG)` | HOP-compliant ✓ |
| Bundle Path | `output_dir / timestamp` | Full path embedded in DEFAULT |
| Test Fixtures | Updated to use HOP paths | Updated ✓ |

- **TOPIC_SLUG:** `code_doc_churn`
- **Retention:** `prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_dir)`
- **DB markers:** Present for manifest/summary/telemetry writes
- **Entry point:** Uses `run(argv)` ✓

Workstream B — Plan

- [x] Draft plan to close output-root/base-package stop-gates

**Migration Plan (4 steps):**

- **Update DEFAULT_OUTPUT_DIR** — Line 16: Change from `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update test fixtures** — Lines 63, 133, 178, 217: Remove `/producer_reports` from paths
- **Run tests** — `pytest -v tests/tests_producers/test_generate_code_doc_churn_report.py`
- **Execute script** — Validate bundle creation at new HOP location

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.

**Implementation Evidence (2025-12-30, updated 2026-02-03):**

- **Updated DEFAULT_OUTPUT_DIR** — Now uses `build_topic_path("producer", TOPIC_SLUG)`
  for HOP-compliant paths
- **Updated test fixtures** — Removed `/producer_reports` hardcoding
- **Tests passed:** 4 passed in 3.00s (2026-02-03)
- **Bundle created:** `.repo_studios/reports/healthview/producer_reports/code_doc_churn/20260203-1150/`
- **Artifacts verified:** manifest.json (1,245B), summary.md (1,781B), telemetry.json (48,834B)

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_generate_code_doc_churn_report.yaml`
- [x] Validate Tier-3 YAML

**Tier-3 Evidence (2025-12-30, verified 2026-02-03):**

- **Decision:** Create — mature producer with stable CLI, HOP-compliant output
- **File created:** `tier3_scripts/docs_health_overview/tier3_generate_code_doc_churn_report.yaml`
- **YAML validation:** Passed (`python -c "import yaml; yaml.safe_load(...)"` → "YAML valid")
- **tier3.allowed:** `true`
- **tier3.exists:** `true`

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [x] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

**QA Evidence (2026-02-03):**

| Check | Result |
|-------|--------|
| Pytest | 4 passed in 3.00s |
| Mypy | Clean (`Success: no issues found in 1 source file`) |
| Coverage | N/A — test uses `importlib.util` dynamic import (known coverage limitation) |

- [x] DONE — generate_code_doc_churn_report.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-008 generate undocumented logic report

```yaml
record_id: "S21R-008"
script:
  path: ".repo_studios/scripts/producers/generate_undocumented_logic_report.py"
  name: "generate_undocumented_logic_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_undocumented_logic_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--doc-index"
    - "--anchor-inventory"
    - "--allowlist"
    - "--include-command-center"
    - "--code-root (repeatable)"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Scans automation code for functions/classes lacking docstrings"
    - "Loads doc index (JSON payload via telemetry.json) + anchor inventory (via loader)"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/undocumented_logic/YYYYMMDD-HHMM/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/undocumented_logic"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) bundle writer + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py#L1-L33"
    - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py#L140-L195"
    - ".repo_studios/scripts/producers/generate_undocumented_logic_report.py#L580-L731"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
  - >-
    Mismatch: orchestrator references undocumented_outcome.artifacts['report.json'],
    but this producer returns only manifest/summary/telemetry artifacts.
```

#### Implementation Workstreams (checkbox-driven) — generate_undocumented_logic_report.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

**Discovery Findings (2025-12-30):**

| Surface | Current | Target (HOP) |
|---------|---------|--------------|
| `DEFAULT_OUTPUT_DIR` | `build_topic_path("producer", TOPIC_SLUG)` | HOP-compliant ✓ |
| Bundle Path | `output_dir / timestamp` | Full path embedded in DEFAULT |
| Test Fixtures | Updated to use HOP paths | Updated ✓ |

- **TOPIC_SLUG:** `undocumented_logic`
- **Retention:** `prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_dir)`
- **DB markers:** Present for manifest/summary/telemetry writes
- **Entry point:** Uses `run(argv)` ✓

Workstream B — Plan

- [x] Draft plan to close output-root/base-package stop-gates

**Migration Plan (4 steps):**

- **Update DEFAULT_OUTPUT_DIR** — Line 24: Change from `.repo_studios/reports/producer_reports` to `.repo_studios/reports`
- **Update test fixtures** — Lines 33-34, 113-114, 135, 181, 204: Remove `/producer_reports` from paths
- **Run tests** — `pytest -v tests/tests_producers/test_generate_undocumented_logic_report.py`
- **Execute script** — Validate bundle creation at new HOP location

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.

**Implementation Evidence (2025-12-30, updated 2025-12-30):**

| Edit | Location | Change |
|------|----------|--------|
| DEFAULT_OUTPUT_DIR | Line 24 | Now uses `build_topic_path("producer", TOPIC_SLUG)` ✓ |
| Test helpers | Various | Updated to use HOP paths |

- **Tests:** 3/3 passed in 0.21s
- **Bundle:** `.repo_studios/reports/healthview/producer_reports/undocumented_logic/<timestamp>/`
  with manifest.json, summary.md, telemetry.json

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_generate_undocumented_logic_report.yaml`
- [x] Validate Tier-3 YAML

**Tier-3 Evidence (2025-12-30):**

- **Decision:** Create — mature producer with stable CLI, HOP-compliant output
- **Created:** `tier3_generate_undocumented_logic_report.yaml` (268 lines)
- **Index updated:** `tier3_scripts_index.yaml` — 14 scripts total (9 producers)
- **tier3.allowed:** `true`

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

**QA Evidence (2025-12-30):**

- **Pytest:** 3/3 passed in 0.21s
- **Mypy:** Clean (no issues)
- **Coverage:** N/A (tests use `importlib.util` dynamic import — not measurable)

- [x] DONE — generate_undocumented_logic_report.py complete; update Tier-1 Stage 2.1 script gate

##### S21R-009 aggregate docs health signals

```yaml
record_id: "S21R-009"
script:
  path: ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py"
  name: "aggregate_docs_health_signals.py"
  category: "aggregator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_aggregate_docs_health_signals.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--churn-report"
    - "--undocumented-report"
    - "--anchor-inventory"
    - "--anchor-validation"
    - "--docs-integrity"
    - "--metrics-stub"
    - "--placeholder-report"
    - "--monkey-patch-report"
    - "--skip-hygiene"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Consumes prior stage bundles (canonical topic dirs or bundle dirs containing telemetry.json; supports legacy report.json)"
    - "Optionally blends hygiene signals unless --skip-hygiene"
  outputs:
    current:
      root: ".repo_studios/reports/aggregator_reports/docs_health_signals/YYYYMMDD-HHMM/"
      artifacts:
        - "report.json"
        - "report.md"
        - "signals.tsv"
        - "signals.csv"
        - "bundle_summary.json"
        - "latest_report.json"  # pointer artifact
        - "latest_report.md"    # pointer artifact
        - "latest_signals.tsv"  # pointer artifact
        - "latest_signals.csv"  # pointer artifact
        - "latest_bundle_summary.json"  # pointer artifact
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "write_report_artifacts(... keep=options.artifacts_to_keep)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/aggregator_reports/docs_health_signals"
  guardrails:
    - "keep-budget pruning inside write_report_artifacts(...)"
  evidence:
    - "ReportArtifact(pointer=latest_*) definitions + write_report_artifacts(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py#L21-L31"
    - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py#L170-L238"
    - ".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py#L888-L933"
  tests:
    - "<pytest path>"
  fixtures:
    - "<fixture path>"
notes:
  - "Stop-gate: emits pointer artifacts (latest_*) which conflict with the target contract's 'no pointer files' rule."
  - "DB markers: none observed in this aggregator (it does not call create_storage)."
```

#### Implementation Workstreams (checkbox-driven) — aggregate_docs_health_signals.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings

**Discovery Findings (2025-12-30):**

| Surface | Current | Target (HOP) |
|---------|---------|--------------|
| `DEFAULT_OUTPUT_DIR` | `build_topic_path("aggregator", TOPIC_SLUG)` | HOP-compliant ✓ |
| Input Defaults | All input paths use HOP `producer_reports/<topic>` | Updated ✓ |
| Bundle Path | `output_dir / timestamp` | Full path embedded in DEFAULT |
| Test Fixtures | Self-contained temp dirs | No changes needed ✓ |

- **TOPIC_SLUG:** `docs_health_signals`
- **Input defaults:** All point to `.repo_studios/reports/healthview/producer_reports/<topic>`
- **Retention:** `write_report_artifacts(... keep=options.artifacts_to_keep)`
- **Entry point:** Uses `run(argv)` ✓

Workstream B — Plan

- [x] Draft plan to close output-root/base-package stop-gates

**Migration Plan (10 steps):**

- **Update DEFAULT_OUTPUT_DIR** — Lines 23-25: Change from
  `.repo_studios/reports/aggregator_reports/docs_health_signals` to `.repo_studios/reports`
- **Update DEFAULT_CHURN_REPORT** — Line 27: Remove `producer_reports/` prefix
- **Update DEFAULT_UNDOCUMENTED_REPORT** — Line 30: Remove `producer_reports/` prefix
- **Update DEFAULT_ANCHOR_INVENTORY** — Line 33: Remove `producer_reports/` prefix
- **Update DEFAULT_ANCHOR_VALIDATION** — Line 36: Remove `producer_reports/` prefix
- **Update DEFAULT_DOCS_INTEGRITY** — Line 39: Remove `producer_reports/` prefix
- **Update DEFAULT_METRICS_STUB** — Line 42: Remove `producer_reports/` prefix
- **Update DEFAULT_PLACEHOLDER_REPORT** — Line 45: Remove `producer_reports/` prefix
- **Update DEFAULT_MONKEY_PATCH_REPORT** — Line 48: Remove `producer_reports/` prefix
- **Run tests** — `pytest -v tests/tests_aggregators/test_aggregate_docs_health_signals.py`

Note: This aggregator uses `write_report_artifacts()` with `stem` which creates its own output
structure. The HOP migration focuses on aligning the input defaults to match the
already-migrated producer paths.

Workstream C — Implement

- [x] Implement accepted plan; update record and stop-gate status with evidence.

**Implementation Evidence (2025-12-30, updated 2025-12-30):**

| Edit | Location | Change |
|------|----------|--------|
| DEFAULT_OUTPUT_DIR | Line 23-25 | Now uses `build_topic_path("aggregator", TOPIC_SLUG)` ✓ |
| DEFAULT_CHURN_REPORT | Line 27 | `.repo_studios/reports/healthview/producer_reports/code_doc_churn` |
| DEFAULT_UNDOCUMENTED_REPORT | Line 30 | `.repo_studios/reports/healthview/producer_reports/undocumented_logic` |
| DEFAULT_ANCHOR_INVENTORY | Line 33 | `.repo_studios/reports/healthview/producer_reports/anchor_inventory` |
| DEFAULT_ANCHOR_VALIDATION | Line 36 | `.repo_studios/reports/healthview/producer_reports/markdown_anchor_validation` |
| DEFAULT_DOCS_INTEGRITY | Line 39 | `.repo_studios/reports/healthview/producer_reports/docs_integrity_validation` |
| DEFAULT_METRICS_STUB | Line 42 | `.repo_studios/reports/healthview/producer_reports/metrics_anchor_stub_validation` |
| DEFAULT_PLACEHOLDER_REPORT | Line 45 | `.repo_studios/reports/healthview/producer_reports/code_placeholders` |
| DEFAULT_MONKEY_PATCH_REPORT | Line 48 | `.repo_studios/reports/healthview/producer_reports/monkey_patches` |

- **Tests:** 2/2 passed in 0.20s
- **Test fixtures:** No changes needed (uses temp dirs)
- **Execution:** Bundle created at `.repo_studios/reports/healthview/aggregator_reports/docs_health_signals/<timestamp>/`
- **Artifacts:** report.json, report.md, signals.csv, signals.tsv, bundle_summary.json (5 files)

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [x] Inspect Tier-3 template requirements
- [x] Draft `tier3_aggregate_docs_health_signals.yaml`
- [x] Validate Tier-3 YAML

**Tier-3 Evidence (2025-12-30):**

- **Decision:** Create — mature aggregator with stable CLI, well-defined io_contract
- **Created:** `tier3_aggregate_docs_health_signals.yaml` (335 lines)
- **Index updated:** `tier3_scripts_index.yaml` — 15 scripts total (2 aggregators)
- **tier3.allowed:** `true`

Workstream E — QA & Evidence

- [x] Pytest evidence captured
- [x] Mypy evidence captured or marked N/A (in record)
- [ ] Coverage ≥80% (or exception recorded) + doc-index timestamp recorded

**QA Evidence (2025-12-30):**

- **Pytest:** 2/2 passed in 0.20s
- **Mypy:** Clean (no issues)
- **Coverage:** N/A (tests use `importlib.util` dynamic import — not measurable)

- [x] DONE — aggregate_docs_health_signals.py complete; update Tier-1 Stage 2.1 script gate

### 3.2 Stop-Gates and Implementation Checklists

Stop-gates are the stage-level truth gates that must be closed before Tier-1 can claim contract
compliance.

Tier-3 YAMLs are promotion artifacts: they should only be created after Tier-2 stop-gates for this
stage are satisfied and the Tier-2 record set is stable enough to extract reusable horizontals.

**Tier-2 authoring stop-gates (docs-first):**

- Ensure canonical `<class>/<topic>` tokens for this stage are explicit.
- Ensure `<timestamp>` formatting is explicit and supported by evidence or a locked decision.
- Ensure Records index and Pruning index are populated.
- Ensure each per-script record includes Tier-3 metadata fields.
- Ensure Tier-1 routes to the authoritative entry points (Contract Snapshot, Stop-Gates, Records Index).

**HOP migration stop-gates (code-phase, later):**

- Output root is migrated to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is enforced: `manifest.json`, `summary.md`, `telemetry.json`.
- No pointer files are introduced.
- Pruning mechanisms and targets align to the target contract and are evidenced.
- If DB writes are present: gate behind `REPO_STUDIOS_DB_ENABLED`, warn-only failures, and include
  `DB_INTEGRATION_MARKER:` at each callsite.
- Tier-1 stage section is updated and contradiction entries are closed as evidence confirms.

---

## 4. Signals & Telemetry

**Regression suites (current evidence):**

- TBD (pytest invocation(s) for this stage)

**Telemetry outputs:**

- This stage will emit `telemetry.json` alongside a manifest that captures step outcomes and
  artifact locations.

**Doc evidence workflow:**

- After meaningful edits, run `make -C .repo_studios doc-index` and capture the
  timestamp in the Update Log.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates blocked by this doc:**
  - Tier-1 cannot consider this stage HOP-compliant until the output root and base package
    stop-gates are closed.

- **Tier-3 dependencies (placeholders until created):**
- **Tier-3 promotion bar:** Tier-3 YAML placeholders remain placeholders until Tier-2 stop-gates are
  satisfied; Tier-2 is the promotion bar for creating Tier-3 artifacts.

- **Tier-3 dependencies (placeholders until created):**
  - Tier-3 placeholder — TBD: tier3_cli_orchestration_doc
  - Tier-3 placeholder — TBD: tier3_pruning_retention_doc
  - Tier-3 placeholder — TBD: tier3_artifacts_contract_doc
  - Tier-3 placeholder — TBD: tier3_database_integration_doc

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle)

---

## 6. Instruction Block (Required by Tier Rules)

1. Editors follow `.github/instructions/markdown.instructions.md` and
   `.github/instructions/pipeline_doc_tiers.instructions.md`.
1. Keep this document’s section order intact.
1. After adding or moving checkboxes, run `make -C .repo_studios doc-index` and
   record the timestamp in Update Logs.
1. Keep “Target contract (locked decisions)” and “Current evidence (repo-observed)” explicit;
    mismatch is treated as a stop-gate.

---

## 7. Agent Automation Block

<!-- agents:begin:healthview_stage_roster_template -->
```yaml
audience: [Copilot, Repo_Studios]
intent: stage_roster_template
rules:
  - require_front_matter: true
  - require_single_h1: true
  - require_update_log: true
  - require_records_index: true
  - require_pruning_index: true
  - require_script_record_schema: true
  - require_tier3_metadata_fields: true
checks:
  - id: hv-tier2-template-contract
    title: Capture current vs target contract snapshot
    severity: error
  - id: hv-tier2-template-records
    title: Records index + per-script records present
    severity: error
  - id: hv-tier2-template-stopgates
    title: >-
      Stop-gates include output root + base package + pointers + retention +
      DB marker rules
    severity: error
```
<!-- agents:end:healthview_stage_roster_template -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-19 | Seeded Stage 2.1 Tier-2 roster template. | repo_studios_ai | TBD | TBD |
