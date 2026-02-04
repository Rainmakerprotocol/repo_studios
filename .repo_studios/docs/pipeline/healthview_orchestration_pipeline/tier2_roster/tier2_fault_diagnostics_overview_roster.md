---
title: "Tier-2 Roster — Stage 3.1 Fault Diagnostics Overview"
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
target_stage: "3.1"
version: 0.1.0
updated_at: 2025-12-19
tags:
  - pipeline
  - healthview
  - tier-2
  - stage-3-1
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 3.1 Fault Diagnostics Overview

> **Purpose:** This Tier-2 vertical deep dive will document Stage 3.1 (Fault Diagnostics Overview)
> for the
> HealthView pipeline. It will inventory the script chain, capture the “Target contract (locked decisions)”
> vs “Current evidence (repo-observed)” I/O contract
> (with evidence), and define stop-gates required before code migrations can claim compliance with
> locked decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 3.1).
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

1. Produce a single authoritative Tier-2 deep dive for Stage 3.1 that engineers and agents can use
  to implement the Stage 3.1 migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 3.1 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 3.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim HOP compliance.
    - stop-gates that must be closed before Tier-1 can claim contract compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 3.1 — Fault Diagnostics Overview
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 3.1 only.

### 2.2 Chain Inventory (Stage 3.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`

**Delegated scripts (expected chain):**

- Producer: `.repo_studios/scripts/producers/collect_faulthandler_reports.py`
- Consumer: `.repo_studios/scripts/consumers/generate_fault_artifacts.py`
- Summarizer: `.repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py`

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 3.1)

This section will be the short, scannable contract summary that Tier-1 routes to.

Authoritative entry points for Tier-1 routing and agent discovery are:

- this Contract Snapshot,
- the Stop-Gates section,
- the Records Index.

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Base package (HOP target):
- Base package (locked target):
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- No pointer files like `latest_*`.
- Pruning mechanisms and targets are explicit, stable, and evidence-backed.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite includes `DB_INTEGRATION_MARKER:`.

**Current evidence (repo-observed):**

- Output root currently observed:
  `.repo_studios/command_center/reports/commandview/fault_diagnostics/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed:
  `YYYYMMDD-HHMM`
- Artifact set observed in current runs:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 3.1 Fault Diagnostics Overview

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- `S31R-001` — `run_fault_diagnostics_overview.py` — Orchestrator — [anchor](#s31r-001-fault-diagnostics-overview-orchestrator)
- `S31R-002` — `collect_faulthandler_reports.py` — Producer — [anchor](#s31r-002-collect-faulthandler-reports)
- `S31R-003` — `generate_fault_artifacts.py` — Consumer — [anchor](#s31r-003-generate-fault-artifacts)
- `S31R-004` — `summarize_fault_diagnostics_overview.py` — Summarizer — [anchor](#s31r-004-summarize-fault-diagnostics-overview)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:**
  - `--artifacts-to-keep` (orchestrator, producer, consumer, summarizer)
  - `--producer-artifacts-to-keep`, `--consumer-artifacts-to-keep`,
    `--summarizer-artifacts-to-keep` (orchestrator)
- **Pruning mechanism:** keep-budget pruning via `write_report_artifacts(... keep=...)` and `prune_run_directories(...)`
- **Pruning targets:**
  - Orchestrator bundle root: `.repo_studios/command_center/reports/commandview/fault_diagnostics/`
  - Producer bundle root (as invoked by orchestrator defaults):
    `.repo_studios/reports/producer_reports/faulthandler_reports/rawview/fault_artifacts_producer/`
  - Consumer bundle root: `.repo_studios/reports/consumer_reports/fault_artifacts/`
  - Consumer Command Center mirror root: `.repo_studios/command_center/reports/fault_artifacts_consumer/`
  - Summarizer bundle root: `.repo_studios/reports/summarizer_reports/fault_diagnostics_overview/`
- **Pruning guardrails:**
  - `current_run` protection (producer + consumer)
  - `.keep` sentinel respected (write_report_artifacts)
- **Evidence source:** orchestrator + delegated script pruning callsites

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

<!-- AGENT_ROUTER:START S31R-001 -->
### S31R-001 — run_fault_diagnostics_overview.py

> **One-liner:** Topic orchestrator coordinating the Fault Diagnostics workflow (producer → consumer → summarizer) with HOP-compliant timestamped bundles.

**Keywords:** `orchestrator`, `fault-diagnostics`, `healthview`, `pipeline`, `topic-orchestrator`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/fault_diagnostics_overview/tier3_run_fault_diagnostics_overview.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_3_1/S31R-001_run_fault_diagnostics_overview_build.md` |
| Output Root | `.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/` |

#### Invocation

```bash
python .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~0.13 seconds (3 steps) |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with step inventory and metrics |
| summary.md | Markdown | Pipeline Status table with per-step results |
| telemetry.json | JSON | Per-step timing, status, and execution metrics |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | `build_topic_path()` + `write_report_artifacts()` |
| UIC Interface | YES | `run(argv)` entry point, importable |
| Tier-3 YAML | YES | Created and validated |
| DB Integration | NO | `create_storage()` not used; markers deferred |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| Fault Diagnostics Overview | SELF | This is the orchestrator |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Count | 3 |
| Steps | producer → consumer → summarizer |
| Execution Mode | SEQUENTIAL |
| Failure Policy | STOP_ON_FAILURE (summarizer has `continue_on_failure=False`) |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬇️ ORCHESTRATES | S31R-002 | `collect_faulthandler_reports.py` | Producer step — generates faulthandler reports |
| ⬇️ ORCHESTRATES | S31R-003 | `generate_fault_artifacts.py` | Consumer step — processes producer output |
| ⬇️ ORCHESTRATES | S31R-004 | `summarize_fault_diagnostics_overview.py` | Summarizer step — generates overview bundle |

#### Known Limitations

- DB Integration markers not present (deferred — dormant across codebase)
- No test coverage verification (execution evidence comprehensive)

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S31R-001 -->

<!-- AGENT_ROUTER:START S31R-002 -->
### S31R-002 — collect_faulthandler_reports.py

> **One-liner:** Collect structured summaries for faulthandler runs, parsing crash/dump data into HOP-compliant producer bundles.

**Keywords:** `producer`, `faulthandler`, `crash-dumps`, `diagnostics`, `healthview`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/collect_faulthandler_reports.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/fault_diagnostics_overview/tier3_collect_faulthandler_reports.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_3_1/S31R-002_collect_faulthandler_reports_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/faulthandler_reports/` |

#### Invocation

```bash
python -m scripts.producers.collect_faulthandler_reports --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with schema version, status, inputs |
| summary.md | Markdown | Human-readable faulthandler summary |
| telemetry.json | JSON | Execution metrics and timing |
| report.json | JSON | Parsed faulthandler signatures and stack data |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest/summary/telemetry |
| UIC Interface | YES | `run(argv)` entry point returning dict |
| Tier-3 YAML | YES | Complete at tier3_scripts/fault_diagnostics_overview/ |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| Fault Diagnostics Overview | WIRED | run_fault_diagnostics_overview.py |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 1 of 3 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | First in pipeline, reads from rawview |
| ⬇️ CONSUMED BY | S31R-003 | `generate_fault_artifacts.py` | Provides `report.json` for artifact generation |
| ⬇️ CONSUMED BY | S31R-004 | `summarize_fault_diagnostics_overview.py` | Provides producer outputs for summarization |

#### Known Limitations

- Missing explicit `exit_code` key in return dict (cosmetic — orchestrators do not require it)
- summary.md contains absolute paths (aids debugging but not portable)
- No actionable next-steps section in summary.md (optional for producer reports)

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | GitHub Copilot |
| Build Doc Version | 3.5.0 |
<!-- AGENT_ROUTER:END S31R-002 -->

<!-- AGENT_ROUTER:START S31R-003 -->
### S31R-003 — generate_fault_artifacts.py

> **One-liner:** Processes raw faulthandler stack dumps and producer reports to emit HOP-compliant consumer artifacts for downstream summarization.

**Keywords:** `consumer`, `fault-artifacts`, `faulthandler`, `crash-dumps`, `healthview`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/consumers/generate_fault_artifacts.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/fault_diagnostics_overview/tier3_generate_fault_artifacts.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_3_1/S31R-003_generate_fault_artifacts_build.md` |
| Output Root | `.repo_studios/reports/healthview/consumer_reports/fault_artifacts/` |

#### Invocation

```bash
python -m scripts.consumers.generate_fault_artifacts --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~3 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with artifact inventory |
| summary.md | Markdown | Human-readable fault signature summary |
| telemetry.json | JSON | Execution telemetry for pipeline monitoring |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles via `build_topic_path()` |
| UIC Interface | PARTIAL | `run(argv)` present; return dict missing `status`/`exit_code` keys (GAP-001, GAP-002) |
| Tier-3 YAML | YES | Validated, active |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| fault_diagnostics_overview | WIRED | `run_fault_diagnostics_overview.py` at L468-522 |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 2 of 3 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S31R-002 | `collect_faulthandler_reports.py` | Reads producer report JSON from `faulthandler_reports/<timestamp>/` |
| ⬇️ CONSUMED BY | S31R-004 | `summarize_fault_diagnostics_overview.py` | Provides `fault_artifacts/<timestamp>/` outputs for summarization |

#### Known Limitations

- UIC-003: Return dict missing `status` key (tech debt)
- UIC-004: Return dict missing `exit_code` key (tech debt)

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-03 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S31R-003 -->

<!-- AGENT_ROUTER:START S31R-004 -->
### S31R-004 — summarize_fault_diagnostics_overview.py

> **One-liner:** Consolidates fault diagnostics consumer and producer outputs into a summary bundle for operator review.

**Keywords:** `summarizer`, `fault-diagnostics`, `healthview`, `summary`, `bundle`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/fault_diagnostics_overview/tier3_summarize_fault_diagnostics_overview.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_3_1/S31R-004_summarize_fault_diagnostics_overview_build.md` |
| Output Root | `.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview/` |

#### Invocation

```bash
python -m command_center.scripts.summarizers.summarize_fault_diagnostics_overview --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with artifact inventory |
| summary.md | Markdown | Human-readable fault diagnostics summary |
| telemetry.json | JSON | Execution telemetry for pipeline monitoring |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles via `write_report_artifacts` |
| UIC Interface | PARTIAL | `run(argv)` present; return dict missing `exit_code` key (GAP-001) |
| Tier-3 YAML | YES | 269 lines, valid structure |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| fault_diagnostics_overview | WIRED | `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 3 of 3 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S31R-002 | `collect_faulthandler_reports.py` | Requires producer outputs from rawview |
| ⬆️ DEPENDS ON | S31R-003 | `generate_fault_artifacts.py` | Requires consumer outputs from fault_artifacts |
| ⬇️ CONSUMED BY | (none) | — | Terminal node, outputs consumed by orchestrator |

#### Known Limitations

- UIC return dict missing `exit_code` key (GAP-001: MEDIUM priority)
- Test expects deprecated filename `fault_diagnostics_overview.json` but script writes `manifest.json` (GAP-002: test bug)

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-03 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S31R-004 -->

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

**Migration stop-gates (code-phase, later):**

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

- `<pytest -q path/to/test_file.py>`

**Telemetry outputs:**

- This stage will emit `telemetry.json` alongside a manifest that captures step outcomes and
  artifact locations.

**Doc evidence workflow:**

- After meaningful edits, run `make -C .repo_studios doc-index` and capture the
  timestamp in the Update Log.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates blocked by this doc:**
  - Tier-1 cannot consider this stage contract-compliant until the output root and base package
    stop-gates are closed.

- **Tier-3 dependencies (placeholders until created):**
- **Tier-3 promotion bar:** Tier-3 YAML placeholders remain placeholders until Tier-2 stop-gates are
  satisfied; Tier-2 is the promotion bar for creating Tier-3 artifacts.

- **Tier-3 dependencies (placeholders until created):**
  - Tier-3 placeholder — `<tier3_cli_orchestration_doc>`
  - Tier-3 placeholder — `<tier3_pruning_retention_doc>`
  - Tier-3 placeholder — `<tier3_artifacts_contract_doc>`
  - Tier-3 placeholder — `<tier3_database_integration_doc>`

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
    title: Stop-gates include output root + base package + pointers + retention + DB marker rules
    severity: error
```
<!-- agents:end:healthview_stage_roster_template -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-19 | Seeded Stage 3.1 Tier-2 roster skeleton. | repo_studios_ai | TBD | TBD |
