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
- After meaningful checkbox edits, run `make -C .repo_studios studio-generate-doc-index` and record
- After meaningful checkbox edits, run `make -C .repo_studios doc-index` and record
  the timestamp in the Update Log.

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

##### S31R-001 fault diagnostics overview orchestrator

```yaml
record_id: "S31R-001"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py"
  name: "run_fault_diagnostics_overview.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_fault_diagnostics_overview.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--runs-dir"
    - "--run-dir"
    - "--producer-output-dir"
    - "--producer-command-center-dir"
    - "--consumer-output-dir"
    - "--consumer-command-center-dir"
    - "--summarizer-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep"
    - "--producer-artifacts-to-keep"
    - "--consumer-artifacts-to-keep"
    - "--summarizer-artifacts-to-keep"
    - "--reuse-report"
    - "--producer-top-frames"
    - "--skip-producer"
    - "--skip-consumer"
    - "--skip-summarizer"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "Raw runs base: .repo_studios/command_center/reports/rawview/fault_diagnostics_runs/ (or --runs-dir / --run-dir)"
    - "Optional: --reuse-report (producer report JSON override)"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/commandview/fault_diagnostics/YYYYMMDD-HHMM/"
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
    - ".repo_studios/command_center/reports/commandview/fault_diagnostics"
  guardrails:
    - "topic-dir pruning inside write_report_artifacts(...)"
    - "write_report_artifacts respects .keep sentinel"
  evidence:
    - "write_report_artifacts(viewer/topic layout) + run_slug formatting"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L51-L79"
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L147-L178"
    - ".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py#L456-L607"
  tests:
    - ".repo_studios/tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py"
  fixtures:
    - "<fixture path>"
notes:
  - "Stop-gate: current output root is under .repo_studios/command_center/reports (not the locked HealthView root)."
  - "Run slug is YYYYMMDD-HHMM (UTC), via write_report_artifacts viewer/topic layout."
  - "DB markers: none observed in this orchestrator (no create_storage callsites)."
  - >-
    Stop-gate: orchestrator passes --command-center-dir to
    collect_faulthandler_reports, but that producer does not define this flag.
  - >-
    Stop-gate: orchestrator expects producer payload keys (run_dir/report) that
    are not emitted by the producer's current return payload.
```

#### Implementation Workstreams (checkbox-driven) — run_fault_diagnostics_overview.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_run_fault_diagnostics_overview.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_fault_diagnostics_overview.py complete; update Tier-1 Stage 3.1 script gate

##### S31R-002 collect faulthandler reports

```yaml
record_id: "S31R-002"
script:
  path: ".repo_studios/scripts/producers/collect_faulthandler_reports.py"
  name: "collect_faulthandler_reports.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_collect_faulthandler_reports.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--runs-dir"
    - "--run-dir"
    - "--output-dir"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--top-frames"
    - "--validate-only"
    - "--log-level"
io_contract:
  inputs:
    - >-
      Reads raw runs under
      .repo_studios/command_center/reports/rawview/fault_diagnostics_runs/
      (or legacy .repo_studios/faulthandler when enabled)
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/faulthandler_reports/rawview/fault_artifacts_producer/YYYYMMDD-HHMM/"
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
    - "prune_run_directories(... keep=options.artifacts_to_keep, current_run=run_bundle_dir)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/producer_reports/faulthandler_reports/rawview/fault_artifacts_producer"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "create_storage(...) + prune_run_directories(...)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/collect_faulthandler_reports.py#L24-L35"
    - ".repo_studios/scripts/producers/collect_faulthandler_reports.py#L86-L121"
    - ".repo_studios/scripts/producers/collect_faulthandler_reports.py#L387-L441"
  tests:
    - ".repo_studios/tests/tests_producers/test_collect_faulthandler_reports.py"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers present for manifest/summary/telemetry writes."
  - >-
    Stop-gate: script docstring describes output under
    .repo_studios/command_center/reports, but orchestrator defaults pass
    --output-dir .repo_studios/reports/producer_reports/faulthandler_reports.
  - "Stop-gate: producer does not accept --command-center-dir, but orchestrator passes it."
```

#### Implementation Workstreams (checkbox-driven) — collect_faulthandler_reports.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_collect_faulthandler_reports.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — collect_faulthandler_reports.py complete; update Tier-1 Stage 3.1 script gate

##### S31R-003 generate fault artifacts

```yaml
record_id: "S31R-003"
script:
  path: ".repo_studios/scripts/consumers/generate_fault_artifacts.py"
  name: "generate_fault_artifacts.py"
  category: "consumer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_fault_artifacts.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--outdir"
    - "--report"
    - "--output-dir"
    - "--command-center-dir"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Reads a faulthandler run directory containing stacks.log (explicit via --outdir/FAULT_OUTDIR or auto-discovers latest)"
    - "Optional --report: reuse legacy producer report JSON; otherwise scan stacks.log"
  outputs:
    current:
      root: ".repo_studios/reports/consumer_reports/fault_artifacts/fault_artifacts-YYYY-MM-DD_HHMMSS-<run_dir_name>/"
      artifacts:
        - "summary.json"
        - "SUMMARY.md"
        - "bundle_summary.json"
        - "latest_summary.json"  # pointer artifact
        - "latest_SUMMARY.md"    # pointer artifact
        - "latest_bundle_summary.json"  # pointer artifact
        - "(run_dir side effects) SUMMARY.md, stacks.csv, dumps/combined.txt"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(... keep=keep_count, stem_prefix=CONSUMER_DIR_PREFIX, current_run=bundle_dir)"
    - "prune_run_directories(... keep=..., stem_prefix=CONSUMER_DIR_PREFIX, current_run=mirror_dir) (Command Center mirror)"
  mechanism: "prune_by_keep_budget"
  targets:
    - ".repo_studios/reports/consumer_reports/fault_artifacts"
    - ".repo_studios/command_center/reports/fault_artifacts_consumer"
  guardrails:
    - "current_run protection when pruning"
  evidence:
    - "LATEST_POINTERS + copy_latest_artifact + prune_run_directories"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/consumers/generate_fault_artifacts.py#L43-L60"
    - ".repo_studios/scripts/consumers/generate_fault_artifacts.py#L292-L360"
    - ".repo_studios/scripts/consumers/generate_fault_artifacts.py#L387-L456"
    - ".repo_studios/scripts/consumers/generate_fault_artifacts.py#L499-L565"
  tests:
    - ".repo_studios/tests/tests_consumers/test_generate_fault_artifacts.py"
  fixtures:
    - "<fixture path>"
notes:
  - >-
    Stop-gate: emits pointer artifacts (latest_*) in both consumer root and
    command_center mirror, conflicting with the locked 'no pointer files' rule.
  - "DB markers: none observed in this consumer (no create_storage callsites)."
```

#### Implementation Workstreams (checkbox-driven) — generate_fault_artifacts.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_generate_fault_artifacts.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_fault_artifacts.py complete; update Tier-1 Stage 3.1 script gate

##### S31R-004 summarize fault diagnostics overview

```yaml
record_id: "S31R-004"
script:
  path: ".repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py"
  name: "summarize_fault_diagnostics_overview.py"
  category: "summarizer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_summarize_fault_diagnostics_overview.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--consumer-output-dir"
    - "--producer-output-dir"
    - "--output-dir"
    - "--consumer-summary"
    - "--consumer-bundle-summary"
    - "--producer-report"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "Reads consumer summary.json + bundle_summary.json (prefers latest_* pointers when present)"
    - "Optionally reads producer report.json via override; otherwise attempts latest_report.json pointer"
  outputs:
    current:
      root: ".repo_studios/reports/summarizer_reports/fault_diagnostics_overview/fault_diagnostics_overview-YYYYMMDD_HHMMSS/"
      artifacts:
        - "fault_diagnostics_overview.json"
        - "fault_diagnostics_overview.md"
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
    - ".repo_studios/reports/summarizer_reports/fault_diagnostics_overview"
  guardrails:
    - "run pruning via write_report_artifacts (_prune_old_runs)"
    - "write_report_artifacts respects .keep sentinel"
  evidence:
    - "write_report_artifacts non-hierarchical slug format"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py#L43-L75"
    - ".repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py#L120-L170"
    - ".repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py#L316-L460"
    - ".repo_studios/command_center/scripts/libraries/artifacts.py#L127-L202"
  tests:
    - ".repo_studios/tests/tests_command_center/fault_diagnostics/test_summarize_fault_diagnostics_overview.py"
  fixtures:
    - "<fixture path>"
notes:
  - "DB markers: none observed in this summarizer (no create_storage callsites)."
  - >-
    Stop-gate: summarizer attempts to locate producer report.json via
    latest_report.json pointer, but the producer emits manifest/summary/telemetry
    (no report.json) and does not write latest_report.json.
  - "Stop-gate: summarizer depends on consumer latest_* pointers for discovery by default."
```

#### Implementation Workstreams (checkbox-driven) — summarize_fault_diagnostics_overview.py

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is allowed for this script (Tier-2 stop-gates closed)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_summarize_fault_diagnostics_overview.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — summarize_fault_diagnostics_overview.py complete; update Tier-1 Stage 3.1 script gate

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
