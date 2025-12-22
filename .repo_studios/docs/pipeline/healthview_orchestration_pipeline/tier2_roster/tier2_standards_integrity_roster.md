---
title: "Tier-2 Roster — Stage 6.1 Standards Integrity"
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
  - stage-6-1
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 6.1 Standards Integrity

> **Purpose:** This Tier-2 vertical deep dive will document Stage 6.1 (Standards Integrity) for the
> HealthView pipeline. It will inventory the script chain, capture the current vs target I/O contract
> (with evidence), and define stop-gates required before code migrations can claim compliance with
> locked decisions.
>
> **Tier-1 source:** `tier1_healthview_orchestration_pipeline.md` (Stage 6.1).
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

1. Produce a single authoritative Tier-2 deep dive for Stage 6.1 that engineers and agents can use
  to implement the Stage 6.1 migration without re-litigating contracts.
1. Make the “current vs target” output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
1. Define stop-gates for Stage 6.1 code work (artifact invariants, pruning mechanisms and targets,
  DB marker discipline, and doc-index evidence).

**Success criteria:**

- Tier-1 links to this doc as the Stage 6.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks (full records),
  - stop-gates that must be closed before Tier-1 can claim contract compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** Stage 6.1 — Standards Integrity
  (`tier1_healthview_orchestration_pipeline.md` → stage section)
- **Tier-2 scope:** This document will cover Stage 6.1 only.

### 2.2 Chain Inventory (Stage 6.1)

**Orchestrator:**

- `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`

**Delegated scripts (expected chain):**

- Producer: `.repo_studios/scripts/producers/generate_standards_index.py`
- Producer: `.repo_studios/scripts/producers/analyze_standards_index_gaps.py`
- Producer: `.repo_studios/scripts/producers/diff_standards_index.py`
- Producer: `.repo_studios/scripts/producers/seed_standards_prompts.py`
- Summarizer: `.repo_studios/scripts/summarizers/summarize_standards.py`

Notes:

- Keep the chain list in the same order as the orchestrator executes it.
- If the stage includes optional steps, mark them clearly and capture the flag surface.

### 2.3 Current vs Target Contract Snapshot (Stage 6.1)

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

- Output roots currently observed:
  - Orchestrator bundle:
    `.repo_studios/command_center/reports/healthview/standards_integrity/<YYYYMMDD-HHMM>/`
  - Standards index bundle:
    `.repo_studios/reports/producer_reports/rawview/standards_index/<YYYYMMDD-HHMM>/`
  - Gap analysis bundle:
    `.repo_studios/command_center/reports/commandview/standards_index_gaps/<YYYYMMDD-HHMM>/`
  - Index diff bundle:
    `.repo_studios/command_center/reports/rawview/standards_index_diff/<YYYYMMDD-HHMM>/`
  - Prompt seed bundle:
    `.repo_studios/reports/producer_reports/standards_prompt_seeds/standards_prompt_seed-<YYYYMMDD_HHMMSS>/`
  - Standards overview bundle:
    `.repo_studios/command_center/reports/healthview/standards_overview/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shapes observed:
  - Most stage bundles: `YYYYMMDD-HHMM` (UTC)
  - Prompt seed run id: `standards_prompt_seed-YYYYMMDD_HHMMSS` (UTC)
- Artifact sets observed:
  - Orchestrator bundle:
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`
  - Standards index / gap analysis / diff bundles:
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`
  - Prompt seed bundles:
    - `report.json`
    - `report.md`
    - `log.txt`
    - `seed.txt`
    - `seed.yaml`
    - `seed.json`
    - `latest/latest_seed.json` (pointer)
    - `latest/latest_seed.yaml` (pointer)
    - `latest/latest_seed.txt` (pointer)
  - Standards overview bundle:
    - `standards_overview.json`
    - `standards_overview.md`

Mismatch is treated as a stop-gate.

---

## 3. Stage Narrative — Stage 6.1 Standards Integrity

### 3.1 Records & Inspection (v1)

This section will keep the stage’s script-level inspection evidence in Tier-2 (not Tier-1).

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- `S61R-001` — `run_standards_integrity.py` — orchestrator — [S61R-001](#s61r-001-standards-integrity-orchestrator)
- `S61R-002` — `generate_standards_index.py` — producer — [S61R-002](#s61r-002-standards-index-producer)
- `S61R-003` — `analyze_standards_index_gaps.py` — producer — [S61R-003](#s61r-003-standards-index-gap-producer)
- `S61R-004` — `diff_standards_index.py` — producer — [S61R-004](#s61r-004-standards-index-diff-producer)
- `S61R-005` — `seed_standards_prompts.py` — producer — [S61R-005](#s61r-005-standards-prompt-seed-producer)
- `S61R-006` — `summarize_standards.py` — summarizer — [S61R-006](#s61r-006-standards-overview-summarizer)

#### 3.1.2 Pruning Index (mini-block)

A compact, mechanism-oriented summary of pruning surfaces and how pruning is enforced.

- **Pruning surfaces:**
  - Orchestrator: `--artifacts-to-keep` (and per-step keep flags) forwarded into delegated scripts.
  - Standards index: `--artifacts-to-keep` applied via `prune_run_directories`.
  - Gap analysis: `--artifacts-to-keep` applied via `prune_run_directories`.
  - Index diff: `--artifacts-to-keep` applied via `prune_run_directories`.
  - Prompt seed: `--artifacts-to-keep` applied via `prune_run_directories`.
  - Standards overview: `--artifacts-to-keep` applied via `write_report_artifacts`.
- **Pruning mechanism:**
  - `prune_run_directories` for timestamped run folders.
  - `write_report_artifacts` for viewer/topic run folders.
- **Pruning targets:**
  - `.repo_studios/command_center/reports/healthview/standards_integrity/` (orchestrator bundle)
  - `.repo_studios/reports/producer_reports/rawview/standards_index/` (index bundle)
  - `.repo_studios/command_center/reports/commandview/standards_index_gaps/` (gap bundle)
  - `.repo_studios/command_center/reports/rawview/standards_index_diff/` (diff bundle)
  - `.repo_studios/reports/producer_reports/standards_prompt_seeds/` (prompt seed bundles + latest pointers)
  - `.repo_studios/command_center/reports/healthview/standards_overview/` (overview bundle)
- **Pruning guardrails:**
  - Shared pruner enforces minimum keep of at least one.
  - Shared pruner can protect the current run directory.
  - Shared pruner skips directories containing a `.keep` sentinel.
- **Evidence source:**
  - `.repo_studios/command_center/scripts/libraries/prune_logs.py`
  - `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`
  - `.repo_studios/scripts/producers/generate_standards_index.py`
  - `.repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py`
  - `.repo_studios/scripts/producers/diff_standards_index.py`
  - `.repo_studios/scripts/producers/seed_standards_prompts.py`
  - `.repo_studios/scripts/summarizers/summarize_standards.py`

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

##### S61R-001: Standards Integrity Orchestrator

```yaml
record_id: "S61R-001"
script:
  path: ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py"
  name: "run_standards_integrity.py"
  category: "orchestrator"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_standards_integrity.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--healthview-root"
    - "--index-output-dir"
    - "--gap-output-dir"
    - "--diff-output-dir"
    - "--prompt-output-dir"
    - "--diff-old-index"
    - "--diff-fail-on"
    - "--gap-max-show"
    - "--prompt-include-warn"
    - "--prompt-formats"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--index-artifacts-to-keep"
    - "--gap-artifacts-to-keep"
    - "--diff-artifacts-to-keep"
    - "--prompt-artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Delegates to standards index producer, gap analysis, diff, prompt seed, summarizer."
    - "Reads standards index + categories + optional baseline index for diffs."
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/standards_integrity/<YYYYMMDD-HHMM>/"
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
    - "--artifacts-to-keep (orchestrator bundle)"
    - "Per-step keep flags forwarded to delegated scripts"
  mechanism: "prune_by_timestamp"
  targets:
    - ".repo_studios/command_center/reports/healthview/standards_integrity/"
  guardrails:
    - "Shared pruning enforces keep>=1 and protects current run"
  evidence:
    - ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py#L788-L815"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: false
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py#L788-L815"
  tests:
    - ".repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py"
  fixtures:
    - ".repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity_helpers.py"
notes:
  - "Writes a Healthview manifest/summary/telemetry bundle and embeds delegated run dirs in the manifest."
```

#### Implementation Workstreams (checkbox-driven) — run_standards_integrity.py

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
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — run_standards_integrity.py complete; update Tier-1 Stage 6.1 script gate

##### S61R-002: Standards Index Producer

```yaml
record_id: "S61R-002"
script:
  path: ".repo_studios/scripts/producers/generate_standards_index.py"
  name: "generate_standards_index.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_standards_index.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--categories-path"
    - "--seed-path"
    - "--extraction-module"
    - "--index-path"
    - "--pending-path"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Scans sources listed in standards_categories.yaml (plus seed/extraction rules)."
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/rawview/standards_index/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(output_dir/rawview/standards_index)"
  mechanism: "prune_by_timestamp"
  targets:
    - ".repo_studios/reports/producer_reports/rawview/standards_index/"
  guardrails:
    - "Shared pruning enforces keep>=1 and protects current run"
  evidence:
    - ".repo_studios/scripts/producers/generate_standards_index.py#L713-L736"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_standards_index.py#L624-L629"
    - ".repo_studios/scripts/producers/generate_standards_index.py#L689-L736"
  tests:
    - "NA"
  fixtures:
    - "NA"
notes:
  - "Also writes the index snapshot to .repo_studios/scripts/repo_standards_index.yaml."
  - "May write .repo_studios/scripts/repo_standards_pending.yaml when extractions are pending."
```

#### Implementation Workstreams (checkbox-driven) — generate_standards_index.py

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
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — generate_standards_index.py complete; update Tier-1 Stage 6.1 script gate

##### S61R-003: Standards Index Gap Producer

```yaml
record_id: "S61R-003"
script:
  path: ".repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py"
  name: "analyze_standards_index_gaps.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_analyze_standards_index_gaps.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--index-path"
    - "--categories-path"
    - "--json"
    - "--max"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Reads repo_standards_index.yaml + standards_categories.yaml and scans sources for missing directives."
  outputs:
    current:
      root: ".repo_studios/command_center/reports/commandview/standards_index_gaps/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(output_dir/commandview/standards_index_gaps)"
  mechanism: "prune_by_timestamp"
  targets:
    - ".repo_studios/command_center/reports/commandview/standards_index_gaps/"
  guardrails:
    - "Shared pruning enforces keep>=1 and protects current run"
  evidence:
    - ".repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py#L503-L534"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py#L514-L519"
  tests:
    - "NA"
  fixtures:
    - "NA"
notes:
  - "A shim exists at .repo_studios/scripts/producers/analyze_standards_index_gaps.py that delegates here."
```

#### Implementation Workstreams (checkbox-driven) — analyze_standards_index_gaps.py

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
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — analyze_standards_index_gaps.py complete; update Tier-1 Stage 6.1 script gate

##### S61R-004: Standards Index Diff Producer

```yaml
record_id: "S61R-004"
script:
  path: ".repo_studios/scripts/producers/diff_standards_index.py"
  name: "diff_standards_index.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_diff_standards_index.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
  key_flags:
    - "old (positional)"
    - "new (positional)"
    - "--repo-root"
    - "--output-dir"
    - "--timestamp"
    - "--run-timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
    - "--json"
    - "--fail-on"
io_contract:
  inputs:
    - "Two index YAML snapshots (old/new)."
  outputs:
    current:
      root: ".repo_studios/command_center/reports/rawview/standards_index_diff/<YYYYMMDD-HHMM>/"
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
    - "prune_run_directories(output_dir/rawview/standards_index_diff)"
  mechanism: "prune_by_timestamp"
  targets:
    - ".repo_studios/command_center/reports/rawview/standards_index_diff/"
  guardrails:
    - "Shared pruning enforces keep>=1 and protects current run"
  evidence:
    - ".repo_studios/scripts/producers/diff_standards_index.py#L371-L467"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/diff_standards_index.py#L377-L467"
  tests:
    - "NA"
  fixtures:
    - "NA"
notes:
  - "Supports both ISO8601 timestamp seeding and explicit run slug override."
```

#### Implementation Workstreams (checkbox-driven) — diff_standards_index.py

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
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — diff_standards_index.py complete; update Tier-1 Stage 6.1 script gate

##### S61R-005: Standards Prompt Seed Producer

```yaml
record_id: "S61R-005"
script:
  path: ".repo_studios/scripts/producers/seed_standards_prompts.py"
  name: "seed_standards_prompts.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_seed_standards_prompts.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--index-path"
    - "--output-dir"
    - "--include-warn"
    - "--artifact-formats"
    - "--format"
    - "--out"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Reads repo_standards_index.yaml to build a severity-filtered prompt seed."
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/standards_prompt_seeds/standards_prompt_seed-<YYYYMMDD_HHMMSS>/"
      artifacts:
        - "report.json"
        - "report.md"
        - "log.txt"
        - "seed.txt"
        - "seed.yaml"
        - "seed.json"
        - "latest/latest_seed.txt"
        - "latest/latest_seed.yaml"
        - "latest/latest_seed.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "prune_run_directories(output_dir, stem_prefix=standards_prompt_seed)"
  mechanism: "prune_by_prefix"
  targets:
    - ".repo_studios/reports/producer_reports/standards_prompt_seeds/"
  guardrails:
    - "Shared pruning enforces keep>=1 and protects current run"
  evidence:
    - ".repo_studios/scripts/producers/seed_standards_prompts.py#L379-L468"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: false
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/seed_standards_prompts.py#L410-L468"
  tests:
    - "NA"
  fixtures:
    - "NA"
notes:
  - "Writes latest pointer artifacts under output_dir/latest/."
```

#### Implementation Workstreams (checkbox-driven) — seed_standards_prompts.py

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
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — seed_standards_prompts.py complete; update Tier-1 Stage 6.1 script gate

##### S61R-006: Standards Overview Summarizer

```yaml
record_id: "S61R-006"
script:
  path: ".repo_studios/scripts/summarizers/summarize_standards.py"
  name: "summarize_standards.py"
  category: "summarizer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_summarize_standards.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--index-path"
    - "--pending-path"
    - "--output-dir"
    - "--label"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Reads repo_standards_index.yaml and repo_standards_pending.yaml for metrics and notes."
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/standards_overview/<YYYYMMDD-HHMM>/"
      artifacts:
        - "standards_overview.json"
        - "standards_overview.md"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep"
    - "write_report_artifacts(keep=...)"
  mechanism: "prune_by_timestamp"
  targets:
    - ".repo_studios/command_center/reports/healthview/standards_overview/"
  guardrails:
    - "Shared pruning enforces keep>=1 and protects current run"
  evidence:
    - ".repo_studios/scripts/summarizers/summarize_standards.py#L324-L334"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: false
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/summarizers/summarize_standards.py#L324-L334"
  tests:
    - "NA"
  fixtures:
    - "NA"
notes:
  - "Writes JSON/Markdown only (no manifest/telemetry bundle)."
```

#### Implementation Workstreams (checkbox-driven) — summarize_standards.py

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
- [ ] Mypy evidence captured (or marked N/A in record)
- [ ] Coverage + doc-index timestamp recorded

- [ ] DONE — summarize_standards.py complete; update Tier-1 Stage 6.1 script gate

### 3.2 Stop-Gates and Implementation Checklists

Stop-gates are the stage-level truth gates that must be closed before Tier-1 can claim contract
compliance.

Tier-3 YAMLs are promotion artifacts: they should only be created after Tier-2 stop-gates for this
stage are satisfied and the Tier-2 record set is stable enough to extract reusable horizontals.

**Tier-2 authoring stop-gates (docs-first):**

- Ensure canonical class/topic tokens for this stage are explicit.
- Ensure timestamp formatting is explicit and supported by evidence or a locked decision.
- Ensure Records index and Pruning index are populated.
- Ensure each per-script record includes Tier-3 metadata fields.
- Ensure Tier-1 routes to the authoritative entry points (Contract Snapshot, Stop-Gates, Records Index).

**Discovery Pass A discrepancies (repo-observed; do not resolve here):**

- Output roots are split across `.repo_studios/command_center/reports/...` and
  `.repo_studios/reports/producer_reports/...`, not the Tier-1 canonical
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Viewer slugs differ across scripts (`healthview`, `rawview`, `commandview`).
- Prompt seed producer writes pointer artifacts under `latest/`.
- Timestamp slug shapes differ across the chain (`YYYYMMDD-HHMM` vs `YYYYMMDD_HHMMSS`).
- Standards overview summarizer does not emit the base package
  (`manifest.json`, `summary.md`, `telemetry.json`).
- The Stage 6.1 chain inventory in this roster lists a non-Command-Center gap analyzer path; the
  orchestrator references `.repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py`.

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

- `pytest -q .repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py`

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
| 2025-12-20 | 6.1: per-record workstreams; doc-index. | repo_studios_ai | 20251220-1636 | Not run |
