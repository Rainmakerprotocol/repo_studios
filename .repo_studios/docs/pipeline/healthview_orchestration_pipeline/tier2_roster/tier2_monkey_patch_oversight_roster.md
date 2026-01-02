---
title: "Tier-2 Roster — Stage 5.1 Monkey Patch Oversight"
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
version: 0.1.0
updated_at: 2025-12-20
tags:
  - pipeline
  - healthview
  - tier-2
  - stage-5-1
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 5.1 Monkey Patch Oversight

> **Purpose:** This Tier-2 vertical deep dive will document Stage 5.1 (Monkey Patch Oversight) for the
> HealthView pipeline. It will inventory the script chain, capture the current vs target I/O contract
> (with evidence), and define stop-gates required before code migrations can claim compliance with
> locked decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 5.1).
> **Locked decisions source:** Tier-1 spine (`tier1_healthview_orchestration_pipeline.md`) + `REPORT_NAMING_STANDARDS.md`.
> **Last synced with Tier-1:** 2025-12-20.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-20) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-20).

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

1. Produce a single authoritative Tier-2 deep dive for Stage 5.1 that engineers and agents can use
  to implement the Stage 5.1 migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 5.1 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 5.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim contract compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 5.1 — Monkey Patch Oversight
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 5.1 only.

### 2.2 Chain Inventory (Stage 5.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py`

**Delegated scripts (expected chain):**

- Producer: `.repo_studios/scripts/producers/scan_monkey_patches.py`
- Consumer: `.repo_studios/scripts/consumers/classify_monkey_patches.py`
- Aggregator: `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py`
- Summarizer: `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py`
- Utility: `.repo_studios/scripts/utilities/monkey_patch_risk.py`

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 5.1)

This section will be the short, scannable contract summary that Tier-1 routes to.

Authoritative entry points for Tier-1 routing and agent discovery are:

- this Contract Snapshot,
- the Stop-Gates section,
- the Records Index.

**Target contract (locked decisions):**

- Canonical HealthView output root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- Base package (locked target):
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`
- No pointer files like `latest_*`.
- Pruning mechanisms and targets are explicit, stable, and evidence-backed.
- DB integration is gated behind `REPO_STUDIOS_DB_ENABLED` and is best-effort (warn-only failures).
  Every DB callsite includes `DB_INTEGRATION_MARKER:`.

**Current evidence (repo-observed):**

- Output root currently observed (orchestrator HealthView bundle write):
  `.repo_studios/command_center/reports/commandview/monkey_patch_oversight/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed (orchestrator HealthView bundle write):
  `YYYYMMDD-HHMM` (UTC)
- Artifact set observed in orchestrator HealthView bundle writes:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

Mismatch is treated as a stop-gate.

Notes:

- The orchestrator module docstring describes a different root than the actual
  `viewer/topic/<slug>` layout.
- The stage currently mixes multiple run slug formats across
  producer/consumer/aggregator/summarizer outputs.
- Pointer files (`latest_*`) exist in consumer/aggregator outputs and are consumed by the summarizer.

Evidence source (entry points):

- `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py`
- `.repo_studios/command_center/scripts/libraries/artifacts.py`

---

## 3. Stage Narrative — Stage 5.1 Monkey Patch Oversight

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- `S51R-001` — `run_monkey_patch_oversight.py` — orchestrator — [S51R-001](#s51r-001-monkey-patch-oversight-orchestrator)
- `S51R-002` — `scan_monkey_patches.py` — producer — [S51R-002](#s51r-002-monkey-patch-scan-producer)
- `S51R-003` — `classify_monkey_patches.py` — consumer — [S51R-003](#s51r-003-monkey-patch-risk-consumer)
- `S51R-004` — `analyze_monkey_patch_trends.py` — aggregator — [S51R-004](#s51r-004-monkey-patch-trend-aggregator)
- `S51R-005` — `summarize_monkey_patch_overview.py` — summarizer — [S51R-005](#s51r-005-monkey-patch-overview-summarizer)
- `S51R-006` — `monkey_patch_risk.py` — utility — [S51R-006](#s51r-006-risk-classification-utility)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:**
  - Orchestrator: `--artifacts-to-keep` + per-step keep budgets forwarded to producer/consumer/aggregator/summarizer.
  - Producer: `--artifacts-to-keep` (producer keep) applied via `prune_run_directories`.
  - Consumer: `--artifacts-to-keep` applied via `prune_run_directories`.
  - Aggregator: `--artifacts-to-keep` applied via `prune_run_directories`.
  - Summarizer: `--artifacts-to-keep` applied via `write_report_artifacts`.
- **Pruning mechanism:**
  - Orchestrator: `write_report_artifacts` hierarchical pruning (`viewer/topic/<YYYYMMDD-HHMM>`).
  - Producer/consumer/aggregator: `prune_run_directories` on timestamped run dirs.
  - Summarizer: `write_report_artifacts` non-hierarchical pruning (`<stem>-<YYYYMMDD_%H%M%S>`).
- **Pruning targets:**
  - `.repo_studios/command_center/reports/<viewer>/<topic>/` (orchestrator bundle outputs).
    - `.repo_studios/reports/producer_reports/...` (producer outputs; note orchestrator overrides
      base dir).
  - `.repo_studios/reports/consumer_reports/monkey_patch_risk/` (consumer bundles + pointers).
  - `.repo_studios/reports/aggregator_reports/monkey_patch_trends/` (aggregator bundles + pointers).
  - `.repo_studios/reports/summarizer_reports/monkey_patch_overview/` (summarizer outputs).
- **Pruning guardrails:**
  - Minimum keep is enforced to be at least one in shared pruners.
  - Current run can be protected explicitly (pruner `current_run` argument).
  - Directories containing a `.keep` sentinel are not deleted.
- **Evidence source:**
  - `.repo_studios/command_center/scripts/libraries/artifacts.py` (hierarchical/non-hierarchical
    pruning behavior)
  - `.repo_studios/command_center/scripts/libraries/prune_logs.py` (`prune_run_directories` behavior)
  - Script-level retention wiring in each per-script record.

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

##### <record_id>: <script_name>

##### S51R-001 monkey patch oversight orchestrator

```yaml
record_id: "S51R-001"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py"
  name: "run_monkey_patch_oversight.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_run_monkey_patch_oversight.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--scan-root"
    - "--producer-output-dir"
    - "--consumer-output-dir"
    - "--aggregator-output-dir"
    - "--summarizer-output-dir"
    - "--healthview-root"
    - "--artifacts-to-keep"
    - "--producer-artifacts-to-keep"
    - "--consumer-artifacts-to-keep"
    - "--aggregator-artifacts-to-keep"
    - "--summarizer-artifacts-to-keep"
    - "--trend-max-runs"
    - "--producer-context-lines"
    - "--producer-with-git"
    - "--producer-strict"
    - "--producer-project-packages"
    - "--producer-exclude-dirs"
    - "--producer-exclude-globs"
    - "--duplicate-matrix"
    - "--skip-producer"
    - "--skip-consumer"
    - "--skip-aggregator"
    - "--skip-summarizer"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "repo_root + scan_root + per-step output roots + keep budgets + timestamp + feature flags"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/commandview/monkey_patch_oversight/<YYYYMMDD-HHMM>/"
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
    - "--artifacts-to-keep (healthview bundle)"
    - "--producer-artifacts-to-keep"
    - "--consumer-artifacts-to-keep"
    - "--aggregator-artifacts-to-keep"
    - "--summarizer-artifacts-to-keep"
  mechanism: "write_report_artifacts hierarchical pruning + per-step delegated pruning"
  targets:
    - ".repo_studios/command_center/reports/commandview/monkey_patch_oversight/<YYYYMMDD-HHMM>/"
  guardrails:
    - "Minimum keep is enforced"
    - "Directories with a .keep sentinel are protected"
  evidence:
    - ".repo_studios/command_center/scripts/libraries/artifacts.py"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L1-L20"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L49-L76"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L289-L307"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L317-L420"
    - ".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py#L656-L735"
    - ".repo_studios/command_center/scripts/libraries/artifacts.py#L127-L188"
  tests:
    - ".repo_studios/tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py"
  fixtures: []
qa:
  pytest: "1 passed in 0.15s (2026-01-02)"
  mypy: "Success (7 errors fixed: added cast, TopicStepOutcome, removed unused type: ignore)"
  coverage: "N/A"
notes:
  - "The module docstring describes a healthview output root that does not match the actual viewer/topic layout (see stop-gates)."
  - "Dynamic module loading sets sys.modules[module_name] = module; track as a monkey patch surface."
  - "Producer outcome parsing expects run_id/report.json/matches.json; producer emits run_dir + manifest/summary/telemetry."
  - "Mypy errors fixed: L257 no-any-return, L302 unused-ignore, L306 no-any-return, L562/584/601/618 no-untyped-def."
```

**Workstreams**

- [ ] **A – Discovery:** Code inspection complete. Orchestrator uses `build_topic_path("orchestrator", "monkey_patch_oversight")` at L76. Delegates to producer/consumer/aggregator/summarizer via dynamic module loading. Uses `write_report_artifacts` for healthview bundle emission.
- [ ] **B – Plan:** No code changes required for HOP compliance. Script already uses HOP patterns.
- [ ] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [ ] **D – Tier-3 YAML:** Deferred — `tier3.allowed: false` per record metadata. No Tier-3 creation required.
- [ ] **E – QA & Evidence:** pytest: 1 passed in 0.15s. mypy --strict: Success (7 errors fixed). Tests path added to evidence block.
- [ ] **DONE**

##### S51R-002 monkey patch scan producer

**Workstreams**

- [ ] **A – Discovery:** Code inspection complete. Script uses `build_topic_path("producer", "monkey_patches")` at L88. No pointer file creation (`latest_*`/`_update_latest` absent). Uses `prune_run_directories` without `stem_prefix` at L1057-1062 — proper HOP pattern.
- [ ] **B – Plan:** No code changes required. Script is already HOP-compliant.
- [ ] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [ ] **D – Tier-3 YAML:** Deferred — `tier3.allowed: false` per record metadata. No Tier-3 creation required.
- [ ] **E – QA & Evidence:** pytest: 6 passed in 0.22s. mypy --strict: Success. Tests path added to evidence block.
- [ ] **DONE**

```yaml
record_id: "S51R-002"
script:
  path: ".repo_studios/scripts/producers/scan_monkey_patches.py"
  name: "scan_monkey_patches.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_scan_monkey_patches.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--root"
    - "--output-dir"
    - "--context-lines"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--with-git"
    - "--strict"
    - "--project-packages"
    - "--exclude-dirs"
    - "--exclude-globs"
    - "--log-level"
    - "--self-test"
io_contract:
  inputs:
    - "repo_root + scan_root + exclusion globs + optional git enrichment + timestamp override"
  outputs:
    current:
      root: "<output_dir>/healthview/monkey_patches/<YYYYMMDD-HHMM>/"
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
  mechanism: "prune_run_directories"
  targets:
    - "<output_dir>/healthview/monkey_patches/<YYYYMMDD-HHMM>/"
  guardrails:
    - "Minimum keep is enforced"
    - "current_run is protected"
    - "Directories with a .keep sentinel are protected"
  evidence:
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/scan_monkey_patches.py#L1-L30"
    - ".repo_studios/scripts/producers/scan_monkey_patches.py#L84-L110"
    - ".repo_studios/scripts/producers/scan_monkey_patches.py#L867-L880"
    - ".repo_studios/scripts/producers/scan_monkey_patches.py#L1034-L1075"
    - ".repo_studios/scripts/producers/scan_monkey_patches.py#L1278-L1335"
    - ".repo_studios/command_center/scripts/libraries/database_integration.py#L300-L444"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L16-L150"
  tests:
    - ".repo_studios/tests/tests_producers/test_scan_monkey_patches.py"
  fixtures: []
  qa:
    pytest: "6 passed in 0.22s"
    mypy: "Success: no issues found"
notes:
  - "The producer writes via DualWriteStorage (file primary; DB best-effort warn-only when enabled)."
  - "The producer returns run_dir/run_timestamp but does not return run_id; orchestrator parsing currently expects run_id."
  - "Topic token mismatches exist across the chain (producer topic monkey_patches; orchestrator defaults monkey_patch_scans)."
```

##### S51R-003 monkey patch risk consumer

**Workstreams**

- [ ] **A – Discovery:** Code inspection complete. Script uses `build_topic_path("consumer", "monkey_patch_risk")` at L67. Comment at L308 confirms pointer file removal. `_update_latest` function exists (L312-320) but is never called — dead code. Uses `prune_run_directories(..., stem_prefix=BUNDLE_PREFIX)` at L334. HOP-compliant output path.
- [ ] **B – Plan:** No code changes required. Script is already HOP-compliant. Dead code (`_update_latest`) should be removed in future cleanup pass but does not block compliance.
- [ ] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [ ] **D – Tier-3 YAML:** Deferred — `tier3.allowed: false` per record metadata. No Tier-3 creation required.
- [ ] **E – QA & Evidence:** pytest: 15 passed in 0.22s. mypy --strict: Success. YAML metadata corrected to reflect code truth (removed stale pointer file references from io_contract.outputs.current.artifacts and notes).
- [ ] **DONE**

```yaml
record_id: "S51R-003"
script:
  path: ".repo_studios/scripts/consumers/classify_monkey_patches.py"
  name: "classify_monkey_patches.py"
  category: "consumer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_classify_monkey_patches.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--scan-dir"
    - "--base-dir"
    - "--output-base"
    - "--artifacts-to-keep"
    - "--log-level"
    - "--verbose"
io_contract:
  inputs:
    - "scan_dir override OR base_dir roots (structured + legacy)"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/<YYYYMMDD-HHMM>/"
      artifacts:
        - "summary.json"
        - "SUMMARY.md"
        - "bundle_summary.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
  mechanism: "prune_run_directories"
  targets:
    - ".repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/"
  guardrails:
    - "Minimum keep is enforced"
    - "current_run is protected"
    - "Directories with a .keep sentinel are protected"
  evidence:
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/consumers/classify_monkey_patches.py#L1-L70"
    - ".repo_studios/scripts/consumers/classify_monkey_patches.py#L240-L350"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L16-L150"
  tests:
    - ".repo_studios/tests/tests_consumers/test_classify_monkey_patches.py"
  fixtures: []
  qa:
    pytest: "15 passed in 0.22s"
    mypy: "Success: no issues found"
notes:
  - "Pointer file creation was removed (L308 comment). _update_latest function is dead code."
  - "Script is HOP-compliant via build_topic_path at L67."
```

##### S51R-004 monkey patch trend aggregator

**Workstreams**

- [ ] **A – Discovery:** Code inspection complete. Script uses `build_topic_path("aggregator", "monkey_patch_trends")` at L49. Comment at L501 confirms pointer file removal. `_update_latest` function exists (L378) but is never called — dead code. Uses `prune_run_directories` at L399 without `stem_prefix`. HOP-compliant.
- [ ] **B – Plan:** No code changes required. Script is already HOP-compliant.
- [ ] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [ ] **D – Tier-3 YAML:** Deferred — `tier3.allowed: false` per record metadata. No Tier-3 creation required.
- [ ] **E – QA & Evidence:** pytest: 3 passed in 0.17s. mypy --strict: Success. YAML metadata corrected (removed stale pointer file references).
- [ ] **DONE**

```yaml
record_id: "S51R-004"
script:
  path: ".repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py"
  name: "analyze_monkey_patch_trends.py"
  category: "aggregator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_analyze_monkey_patch_trends.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--consumer-base"
    - "--consumer-summary"
    - "--producer-base"
    - "--output-base"
    - "--artifacts-to-keep"
    - "--max-runs"
    - "--log-level"
    - "--verbose"
io_contract:
  inputs:
    - "consumer bundles (preferred) OR producer fallback"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/<YYYYMMDD-HHMM>/"
      artifacts:
        - "trend.json"
        - "trend.md"
        - "bundle_summary.json"
        - "TREND_SNAPSHOT.md (copied into latest consumer bundle)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "--max-runs"
  mechanism: "prune_run_directories"
  targets:
    - ".repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/"
  guardrails:
    - "Minimum keep is enforced"
    - "current_run is protected"
    - "Directories with a .keep sentinel are protected"
  evidence:
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py#L1-L80"
    - ".repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py#L350-L520"
    - ".repo_studios/command_center/scripts/libraries/prune_logs.py#L16-L150"
  tests:
    - ".repo_studios/tests/tests_aggregators/test_analyze_monkey_patch_trends.py"
  fixtures: []
  qa:
    pytest: "3 passed in 0.17s"
    mypy: "Success: no issues found"
notes:
  - "Pointer file creation was removed (L501 comment). _update_latest function is dead code."
  - "Script is HOP-compliant via build_topic_path at L49."
  - "The aggregator also mirrors trend markdown into the latest consumer bundle as TREND_SNAPSHOT.md."
```

##### S51R-005 monkey patch overview summarizer

**Workstreams**

- [x] **A – Discovery:** Code inspection complete. Script uses `build_topic_path("summarizer",
  "monkey_patch_overview")` at L48. Uses `write_report_artifacts` at L468 for output (HOP-compliant).
  Reads `latest_*` pointers from upstream (consumer/aggregator) via `_latest_pointer` helper
  (L197) — does not create pointer files.
- [x] **B – Plan:** No code changes required. Script is already HOP-compliant for its own output.
  Artifacts (`monkey_patch_overview.json`, `monkey_patch_overview.md`) are summarizer-specific;
  base package template is a placeholder.
- [x] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [x] **D – Tier-3 YAML:** Created `tier3_summarize_monkey_patch_overview.yaml` under
  `tier3_scripts/monkey_patch_oversight/` (2026-01-02).
- [x] **E – QA & Evidence:** No test file exists. mypy --strict: Success (verified 2026-01-02).
- [ ] **DONE**

```yaml
record_id: "S51R-005"
script:
  path: ".repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py"
  name: "summarize_monkey_patch_overview.py"
  category: "summarizer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_summarize_monkey_patch_overview.yaml"
  meets_template: "yes"
  last_updated: "2026-01-02"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--consumer-output-dir"
    - "--producer-output-dir"
    - "--aggregator-output-dir"
    - "--output-dir"
    - "--consumer-summary"
    - "--consumer-bundle-summary"
    - "--trend-json"
    - "--trend-markdown"
    - "--trend-bundle-summary"
    - "--producer-report"
    - "--producer-matches"
    - "--duplicate-matrix"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "consumer + aggregator outputs (explicit overrides OR latest_* pointers OR latest run heuristics)"
    - "optional duplicate matrix for overlap analysis"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/<YYYYMMDD-HHMM>/"
      artifacts:
        - "monkey_patch_overview.json"
        - "monkey_patch_overview.md"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
  mechanism: "write_report_artifacts non-hierarchical pruning"
  targets:
    - ".repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/"
  guardrails:
    - "Minimum keep is enforced"
    - "Directories with a .keep sentinel are protected"
  evidence:
    - ".repo_studios/command_center/scripts/libraries/artifacts.py"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py#L1-L80"
    - ".repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py#L195-L260"
    - ".repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py#L310-L380"
    - ".repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py#L450-L488"
    - ".repo_studios/command_center/scripts/libraries/artifacts.py#L127-L188"
  tests: []
  fixtures: []
  qa:
    pytest: "No test file exists"
    mypy: "Success: no issues found (8 errors fixed)"
notes:
  - "The summarizer reads latest_* pointers from consumer/aggregator outputs — does not write them."
  - "Script is HOP-compliant via build_topic_path at L48 and write_report_artifacts at L467."
```

##### S51R-006 risk classification utility

```yaml
record_id: "S51R-006"
script:
  path: ".repo_studios/scripts/utilities/monkey_patch_risk.py"
  name: "monkey_patch_risk.py"
  category: "utility"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_monkey_patch_risk.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "other"
  key_flags: []
io_contract:
  inputs:
    - "FindingSignals(category, is_test, is_module_scope)"
  outputs:
    current:
      root: "N/A"
      artifacts: []
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces: []
  mechanism: "N/A"
  targets: []
  guardrails: []
  evidence: []
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/utilities/monkey_patch_risk.py#L1-L75"
  tests:
    - ".repo_studios/tests/tests_utilities/test_monkey_patch_risk.py"
  fixtures: []
qa:
  pytest: "5 passed in 0.06s (2026-01-02)"
  mypy: "Success: no issues found (2026-01-02)"
  coverage: "N/A"
notes:
  - "Pure utility library; no CLI or output artifacts."
  - "Defines the risk bucketing used by consumer + aggregator for consistent reporting."
  - "Workstreams A–D marked N/A; only Workstream E applies."
```

#### Implementation Workstreams (checkbox-driven) — <script_name>

Workstream A — Discovery

- [ ] Inspect outputs + pruning/retention surfaces; record findings

Workstream B — Plan

- [ ] Draft plan to close output-root/base-package stop-gates

Workstream C — Implement

- [ ] Implement accepted plan and update this record + stop-gate status with new evidence

Workstream D — Tier-3 YAML

- [ ] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
- [ ] Inspect Tier-3 template requirements
- [ ] Draft `tier3_<script_stem>.yaml`
- [ ] Validate Tier-3 YAML

Workstream E — QA & Evidence

- [ ] Pytest evidence captured
  - Result: 5 passed in 0.06s (2026-01-02)
- [ ] Mypy evidence captured (or marked N/A in record)
  - Result: Success: no issues found
- [ ] Coverage + doc-index timestamp recorded
  - N/A (pure utility, no coverage threshold)

- [ ] DONE — monkey_patch_risk.py complete; update Tier-1 Stage 5.1 script gate

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

**Discovery stop-gates (repo-observed mismatches to resolve before code-phase claims):**

- Orchestrator bundle docstring root conflicts with actual `viewer/topic/<YYYYMMDD-HHMM>` layout.
- Orchestrator uses `viewer=commandview` for the HealthView bundle write.
- Producer/consumer/aggregator/summarizer disagree on producer artifact naming:
  - `manifest.json` vs `report.json`
  - `matches.json` expectations vary
- Producer/consumer/aggregator/summarizer disagree on producer artifact naming:
  - `manifest.json` vs `report.json`
  - `matches.json` expectations vary
- Orchestrator expects producer payload `run_id` and a flat `producer_output_dir/<run_id>/` structure.
  The producer returns `run_dir` and writes under `output_dir/healthview/monkey_patches/<YYYYMMDD-HHMM>/`.
- Consumer + aggregator create `latest_*` pointer artifacts; summarizer consumes pointers when present.
- Stage outputs use multiple timestamp slug formats (`YYYYMMDD-HHMM`, `YYYYMMDD_%H%M%S`, `%Y-%m-%d_%H%M%S`).

---

## 4. Signals & Telemetry

**Regression suites (current evidence):**

- `pytest -q .repo_studios/tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py`

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
| 2025-12-20 | Discovery Pass A + doc-index. | repo_studios_ai | 2025-12-20 11:07-05:00 | Not run |
