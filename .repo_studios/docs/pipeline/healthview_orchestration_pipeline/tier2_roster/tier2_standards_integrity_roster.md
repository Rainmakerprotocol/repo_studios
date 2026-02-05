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

**Current evidence (repo-observed — HOP-compliant as of 2026-01-03):**

- Output roots currently observed (all HOP-compliant):
  - Orchestrator bundle:
    `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/<YYYYMMDD-HHMM>/`
  - Standards index bundle:
    `.repo_studios/reports/healthview/producer_reports/standards_index/<YYYYMMDD-HHMM>/`
  - Gap analysis bundle:
    `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/<YYYYMMDD-HHMM>/`
  - Index diff bundle:
    `.repo_studios/reports/healthview/producer_reports/standards_index_diff/<YYYYMMDD-HHMM>/`
  - Prompt seed bundle:
    `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/<YYYYMMDD-HHMM>/`
  - Standards overview bundle:
    `.repo_studios/reports/healthview/summarizer_reports/standards_overview/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shapes observed:
  - All stage bundles: `YYYYMMDD-HHMM` (UTC)
- Artifact sets observed (base package enforced):
  - Orchestrator bundle:
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`
  - Standards index / gap analysis / diff bundles:
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`
  - Prompt seed bundles:
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`
    - `seed.txt`
    - `seed.yaml`
    - `seed.json`
  - Standards overview bundle:
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`

**All stop-gates closed** — base package enforced, no pointer artifacts, HOP-compliant paths.

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
  - `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/` (orchestrator bundle)
  - `.repo_studios/reports/healthview/producer_reports/standards_index/` (index bundle)
  - `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/` (gap bundle)
  - `.repo_studios/reports/healthview/producer_reports/standards_index_diff/` (diff bundle)
  - `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/` (prompt seed bundle)
  - `.repo_studios/reports/healthview/summarizer_reports/standards_overview/` (overview bundle)
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

<!-- AGENT_ROUTER:START S61R-001 -->
### S61R-001 — run_standards_integrity.py

> **One-liner:** Topic orchestrator for standards integrity that coordinates index generation, gap analysis, diff comparison, prompt seeding, and summary creation.

**Keywords:** `orchestrator`, `standards`, `integrity`, `pipeline`, `healthview`, `compliance`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/standards_integrity/tier3_run_standards_integrity.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_6_1/S61R-001_run_standards_integrity_build.md` |
| Output Root | `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/` |

#### Invocation
```bash
python .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` returns `int` |
| Typical Runtime | 5-8 minutes |
| Exit Codes | 0=success, 1=pipeline failure |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Full pipeline state, artifact paths, catalog, inputs |
| summary.md | Markdown | Human-readable step report with outcomes |
| telemetry.json | JSON | Pipeline telemetry with step results and metrics |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest, uses `write_report_artifacts()` |
| UIC Interface | PARTIAL | `run(argv)` returns `int` (orchestrator deviation, acceptable) |
| Tier-3 YAML | YES | Created 2026-01-02, 294 lines |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| (self) | IS_ORCHESTRATOR | N/A — this is the orchestrator |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | N/A — Orchestrator |
| Execution Mode | COORDINATES 5 SEQUENTIAL STEPS |
| Orchestrator Script | (self) |

#### Pipeline Steps Coordinated
| # | Step Name | Script | Record ID |
|---|-----------|--------|-----------|
| 1 | index | `generate_standards_index.py` | S61R-002 |
| 2 | gap | `analyze_standards_index_gaps.py` | S61R-003 |
| 3 | diff | `diff_standards_index.py` | S61R-004 |
| 4 | prompts | `seed_standards_prompts.py` | S61R-005 |
| 5 | summary | `summarize_standards.py` | S61R-006 |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | Top-level orchestrator, no upstream dependencies |
| ⬇️ CONSUMED BY | (none) | — | Terminal node, outputs consumed by HealthView dashboard |

#### Known Limitations
- `run()` missing Google-style docstring (GAP-001)
- Skip flags not implemented (GAP-002)
- Tier-3 YAML retention default mismatch (GAP-003)
- Tier-3 YAML continue_on_failure mismatch on index step (GAP-004)

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-05 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S61R-001 -->

<!-- AGENT_ROUTER:START S61R-002 -->
### S61R-002 — generate_standards_index.py

> **One-liner:** Scans markdown standards files, extracts rules, and builds a compliance index with integrity hash for process governance tracking.

**Keywords:** `standards`, `compliance`, `index`, `markdown`, `rules`, `governance`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/generate_standards_index.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/standards_integrity/tier3_generate_standards_index.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_6_1/S61R-002_generate_standards_index_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/standards_index/` |

#### Invocation
```bash
python .repo_studios/scripts/producers/generate_standards_index.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `main(argv)` |
| Typical Runtime | ~15 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with file inventory and integrity hash |
| summary.md | Markdown | Human-readable standards index overview |
| telemetry.json | JSON | Execution metrics and timing data |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest, uses `build_topic_path()` |
| UIC Interface | PARTIAL | Has `main(argv)`, missing `run(argv)` wrapper |
| Tier-3 YAML | YES | Created 2026-01-02 |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| run_standards_integrity.py | WIRED | Step 1 of 5 |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | 1 of 5 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | First in pipeline, no upstream dependencies |
| ⬇️ CONSUMED BY | S61R-003 | `analyze_standards_index_gaps.py` | Provides standards index for gap analysis |
| ⬇️ CONSUMED BY | S61R-004 | `diff_standards_index.py` | Provides current index for diff comparison |
| ⬇️ CONSUMED BY | S61R-005 | `seed_standards_prompts.py` | Provides standards rules for prompt seeding |
| ⬇️ CONSUMED BY | S61R-006 | `summarize_standards.py` | Provides index data for overview synthesis |

#### Known Limitations
- Missing `run(argv)` entry point (GAP-001 documented)
- Requires `standards_categories.yaml` prerequisite file (GAP-002 documented)
- Tier-3 YAML output path shows legacy `rawview/` path (GAP-003 documented)

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-05 |
| Verified By | GitHub Copilot (copilot-claude-4) |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S61R-002 -->

<!-- AGENT_ROUTER:START S61R-003 -->
### S61R-003 — analyze_standards_index_gaps.py

> **One-liner:** Analyzes the standards index against source files to identify gaps where standards are declared but not implemented.

**Keywords:** `standards`, `gap-analysis`, `compliance`, `producer`, `markdown`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/analyze_standards_index_gaps.py` |
| Implementation | `.repo_studios/command_center/scripts/cc_producers/analyze_standards_index_gaps.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/standards_integrity/tier3_analyze_standards_index_gaps.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_6_1/S61R-003_analyze_standards_index_gaps_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/` |

#### Invocation
```bash
python -m scripts.producers.analyze_standards_index_gaps --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success, 2=error |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with schema version, status, provenance |
| summary.md | Markdown | Human-readable gap report with candidate lines |
| telemetry.json | JSON | Execution metrics, candidate counts, top sources |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles with manifest/summary/telemetry |
| UIC Interface | PARTIAL | `run(argv)` exists but missing `status`/`exit_code` in return dict |
| Tier-3 YAML | YES | Created 2026-01-02, v1 template |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| run_standards_integrity.py | WIRED | Step 2 of 5 (index → **gap** → diff → prompts → summary) |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 2 of 5 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S61R-002 | `generate_standards_index.py` | Requires `repo_standards_index.yaml` for gap analysis |
| ⬇️ CONSUMED BY | S61R-006 | `summarize_standards.py` | Provides gap data for standards overview |

#### Known Limitations

- Return dict missing `status` and `exit_code` keys (GAP-001, GAP-002)
- Exceptions raise instead of returning error dict (GAP-003)
- Summary.md contains absolute paths (cosmetic, GAP-004)

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-05 |
| Verified By | GitHub Copilot |
| Build Doc Version | 0.3.0 |
<!-- AGENT_ROUTER:END S61R-003 -->

<!-- AGENT_ROUTER:START S61R-004 -->
### S61R-004 — diff_standards_index.py

> **One-liner:** Compare two standards index YAML files and emit a canonical report bundle with change detection.

**Keywords:** `standards`, `diff`, `index`, `compliance`, `producer`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/diff_standards_index.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/standards_integrity/tier3_diff_standards_index.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_6_1/S61R-004_diff_standards_index_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/standards_index_diff/` |

#### Invocation

```bash
python .repo_studios/scripts/producers/diff_standards_index.py <old_index> <new_index> --repo-root . --log-level INFO --fail-on any
```

| Aspect | Value |
|--------|-------|
| Entry Point | `main(argv)` |
| Typical Runtime | ~2 seconds |
| Exit Codes | 0=success/no-changes, 1=changes-match-fail-on, 2=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Schema version, status, inputs, diff summary |
| summary.md | Markdown | Human-readable diff summary with rule changes |
| telemetry.json | JSON | Execution metrics and timing |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | 8/8 checks pass, uses `build_topic_path()` |
| UIC Interface | PARTIAL | 4/10 — `main(argv)` exists, missing `run(argv) -> dict` |
| Tier-3 YAML | YES | 232-line YAML with all required fields |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| run_standards_integrity.py | WIRED | Step 3 of 5 (conditional, skipped if no baseline) |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 3 of 5 |
| Execution Mode | CONDITIONAL (skipped if `--diff-old-index` not provided) |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S61R-002 | `generate_standards_index.py` | Requires baseline and current index YAML files |
| ⬇️ CONSUMED BY | S61R-006 | `summarize_standards.py` | Provides diff data for standards overview summary |

#### Known Limitations

- Missing `run(argv) -> dict` entry point (UIC gaps GAP-001 through GAP-006 documented, deferred)
- Orchestrator invokes via `main()` function, not UIC-compliant `run()` pattern

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-05 |
| Verified By | GitHub Copilot (copilot-claude-opus-4.5) |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S61R-004 -->

<!-- AGENT_ROUTER:START S61R-005 -->
### S61R-005 — seed_standards_prompts.py

> **One-liner:** Generate structured prompt seed bundles from standards index for AI agent consumption.

**Keywords:** `standards`, `prompts`, `seeds`, `yaml`, `json`, `agent`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/seed_standards_prompts.py` |
| Tier-3 YAML | `.repo_studios/scripts/tier3_scripts/standards_integrity/tier3_seed_standards_prompts.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_6_1/S61R-005_seed_standards_prompts_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/` |

#### Invocation
```bash
python -m scripts.producers.seed_standards_prompts --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~2 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with file inventory |
| summary.md | Markdown | Human-readable seed statistics |
| telemetry.json | JSON | Execution telemetry and metrics |
| seed.txt | Text | Plain text prompt seed content |
| seed.yaml | YAML | Structured YAML prompt seed |
| seed.json | JSON | JSON-formatted prompt seed |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | 8/8 HOP checks pass |
| UIC Interface | PARTIAL | 8/10 — missing exit_code, docstring |
| Tier-3 YAML | YES | Created 2026-01-02 |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| Standards Integrity | WIRED | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | 4 of 5 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S61R-002 | `generate_standards_index.py` | Requires `repo_standards_index.yaml` from producer_reports |
| ⬇️ CONSUMED BY | S61R-006 | `summarize_standards.py` | Provides seed artifacts for standards overview |
| ⬇️ CONSUMED BY | (none) | — | Terminal node for prompt seeding workflow |

#### Known Limitations
- Missing `exit_code` key in return payload (GAP-001)
- Missing Google-style docstring on `run()` function (GAP-002)
- No DB integration markers (GAP-003/004/005) — deferred

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-05 |
| Verified By | GitHub Copilot (copilot-claude-opus-4.5) |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S61R-005 -->

<!-- AGENT_ROUTER:START S61R-006 -->
### S61R-006 — summarize_standards.py

> **One-liner:** Generates a HealthView-ready summary of the standards index with metrics, markdown samples, and pending file status.

**Keywords:** `standards`, `summarizer`, `metrics`, `healthview`, `compliance`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/summarizers/summarize_standards.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/standards_integrity/tier3_summarize_standards.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_6_1/S61R-006_summarize_standards_build.md` |
| Output Root | `.repo_studios/reports/healthview/summarizer_reports/standards_overview/` |

#### Invocation
```bash
python .repo_studios/scripts/summarizers/summarize_standards.py --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~2 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with metrics, samples, artifact paths |
| summary.md | Markdown | Human-readable overview with metrics table |
| telemetry.json | JSON | Telemetry payload with schema version and metrics |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Emits manifest.json + summary.md + telemetry.json |
| UIC Interface | PARTIAL | Missing `exit_code` in return dict (GAP-001) |
| Tier-3 YAML | YES | 141 lines, validated |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| Standards Integrity | WIRED | `run_standards_integrity.py` |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | 5 of 5 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S61R-002 | `generate_standards_index.py` | Reads `repo_standards_index.yaml` |
| ⬆️ DEPENDS ON | (none) | `repo_standards_pending.yaml` | Reads pending standards file |
| ⬇️ CONSUMED BY | (none) | — | Terminal node, outputs consumed by orchestrator |

#### Known Limitations
- Return dict missing `exit_code` key (UIC-004 gap)
- `run()` function lacks Google-style docstring (UIC-007 gap)

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-05 |
| Verified By | GitHub Copilot (copilot-claude-opus-4.5) |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S61R-006 -->

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

**Discovery Pass A discrepancies (resolved 2026-01-03 via HOP refactor):**

- ~~Output roots are split across `.repo_studios/command_center/reports/...` and
  `.repo_studios/reports/producer_reports/...`~~ — **RESOLVED**: Gap, diff, prompt now use
  `build_topic_path()` via orchestrator defaults.
- ~~Viewer slugs differ across scripts~~ — **RESOLVED**: All HOP-compliant scripts use `healthview`.
- ~~Prompt seed producer writes pointer artifacts under `latest/`~~ — **RESOLVED**: Pointer
  artifacts removed; base package enforced.
- ~~Timestamp slug shapes differ across the chain~~ — **RESOLVED**: All scripts emit `YYYYMMDD-HHMM`.
- ~~Standards overview summarizer does not emit the base package~~ — **RESOLVED**: Now emits
  `manifest.json`, `summary.md`, `telemetry.json`.
- ~~Gap analyzer path mismatch~~ — **RESOLVED**: Orchestrator correctly references
  `.repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py`.

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
| 2026-01-22 | 6.1: corrected orchestrator output root references to use `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/` (aligned with current evidence); regenerated doc-index. | GitHub Copilot | 20260122-1218 | doc-index |
| 2026-01-03 | 6.1: HOP refactor complete — S61R-005/006 artifacts, orchestrator paths, stop-gates closed. | repo_studios_ai | pending | 26 passed |
| 2025-12-20 | 6.1: per-record workstreams; doc-index. | repo_studios_ai | 20251220-1636 | Not run |
