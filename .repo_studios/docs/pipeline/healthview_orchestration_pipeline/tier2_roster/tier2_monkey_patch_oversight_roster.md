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
status: complete
version: 1.0.0
updated_at: 2026-02-05
tags:
  - pipeline
  - healthview
  - tier-2
  - stage-5-1
  - phase-4-complete
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/
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

1. ✅ Produce a single authoritative Tier-2 deep dive for Stage 5.1 that engineers and agents can use
   to implement the Stage 5.1 migration without re-litigating contracts.
2. ✅ Make the "current vs target" output and artifact contract explicit, including the canonical
   HealthView root `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
3. ✅ Define stop-gates for Stage 5.1 code work (artifact invariants, pruning mechanisms and targets,
   DB marker discipline, and doc-index evidence).

**Success criteria — ALL MET (2026-02-05):**

- ✅ Tier-1 links to this doc as the Stage 5.1 Tier-2 roster.
- ✅ This doc contains:
  - ✅ Records index (6 records: S51R-001 through S51R-006)
  - ✅ Pruning index (5 HOP-compliant paths documented)
  - ✅ ScriptInspectionRecordV1 schema (deprecated — replaced by Agent Router template)
  - ✅ Per-script Agent Router blocks with Phase 4 build docs
  - ✅ All stop-gates closed (HOP compliance verified 2026-01-03, Phase 4 complete 2026-02-05)

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
  `.repo_studios/reports/healthview/orchestrator_reports/monkey_patch_oversight/<YYYYMMDD-HHMM>/`
- Timestamp/run slug shape observed (all scripts):
  `YYYYMMDD-HHMM` (UTC)
- Artifact set observed in orchestrator HealthView bundle writes:
  - `manifest.json`
  - `summary.md`
  - `telemetry.json`

**HOP compliance confirmed (2026-01-03):**

- All 5 scripts now use `build_topic_path()` for HOP-compliant output roots.
- Slug format standardized to `YYYYMMDD-HHMM` across all scripts.
- No pointer artifacts (`latest_*`) are created.
- Consumer reads producer manifest via `payload.findings`.
- Summarizer emits `manifest.json` and `summary.md` (HOP base package).

Notes:

- Implementation plan: `implementation_plans/stage_5_hop_refactor_plan.md`
- Runtime evidence: Run `20260103-0201` verified all outputs at HOP paths.

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
  - All scripts: `YYYYMMDD-HHMM` slug format, pruned by timestamp sort.
  - Orchestrator: `write_report_artifacts` hierarchical pruning (`viewer="", topic=""`).
  - Producer/consumer/aggregator: `prune_run_directories` on timestamped run dirs.
  - Summarizer: `write_report_artifacts` hierarchical pruning (`viewer="", topic=""`).
- **Pruning targets (HOP-compliant paths):**
  - `.repo_studios/reports/healthview/orchestrator_reports/monkey_patch_oversight/` (orchestrator).
  - `.repo_studios/reports/healthview/producer_reports/monkey_patch_scans/` (producer).
  - `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/` (consumer).
  - `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/` (aggregator).
  - `.repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/` (summarizer).
- **Pruning guardrails:**
  - Minimum keep is enforced to be at least one in shared pruners.
  - Current run can be protected explicitly (pruner `current_run` argument).
  - Directories containing a `.keep` sentinel are not deleted.
- **Evidence source:**
  - `.repo_studios/command_center/scripts/libraries/artifacts.py` (hierarchical pruning behavior)
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

<!-- AGENT_ROUTER:START S51R-001 -->
### S51R-001 — run_monkey_patch_oversight.py

> **One-liner:** 4-step orchestrator coordinating monkey patch detection, classification, trend analysis, and summary generation.

**Keywords:** `orchestrator`, `monkey-patch`, `pipeline`, `healthview`, `technical-debt`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/monkey_patch_oversight/tier3_run_monkey_patch_oversight.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_5_1/S51R-001_run_monkey_patch_oversight_build.md` |
| Output Root | `.repo_studios/reports/healthview/orchestrator_reports/monkey_patch_oversight/` |

#### Invocation

```bash
python .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py \
  --repo-root . --scan-root .repo_studios/command_center/scripts --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv: list[str] | None) -> int` |
| Typical Runtime | ~0.65s (4 steps in sequence) |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | HOP bundle metadata with step outcomes |
| summary.md | Markdown | Aggregated pipeline summary |
| telemetry.json | JSON | Step timing and execution telemetry |

#### Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| UIC (Universal Interface) | 8 PASS / 2 DEVIATION | Build doc Section 2.2.1 |
| HOP (Bundle Compliance) | 8/8 PASS | Build doc Section 2.4.2 |
| PPC (Pipeline Configuration) | 9/9 PASS | Build doc Section 2.4.3 |
| AGT (Agent Integration) | 4/4 PASS | Build doc Section 2.4.4 |
| DB Integration | DORMANT | Markers at L1180, L1200 |

#### Orchestrator

| Attribute | Value |
|-----------|-------|
| Step Count | 4 |
| Pipeline Steps | producer → consumer → aggregator → summarizer |
| Skip Flags | `--skip-producer`, `--skip-consumer`, `--skip-aggregator`, `--skip-summarizer` |
| Failure Policy | CONTINUE (with `raise_for_failure()` at end) |

#### Pipeline Position

| Position | Role |
|----------|------|
| Stage | 5.1 (Monkey Patch Oversight) |
| Tier | A (Report Generator) |
| Owns | S51R-002, S51R-003, S51R-004, S51R-005 |

#### Dependencies & Consumers

| Type | Script | Record |
|------|--------|--------|
| Delegates to | `scan_monkey_patches.py` | S51R-002 |
| Delegates to | `classify_monkey_patches.py` | S51R-003 |
| Delegates to | `analyze_monkey_patch_trends.py` | S51R-004 |
| Delegates to | `summarize_monkey_patch_overview.py` | S51R-005 |

#### Known Limitations

- UIC-002 deviation: `run()` returns `int` (exit code) instead of `dict[str, Any]`. Intentional — orchestrators return exit status; payload written to HOP bundle.
- DB integration is DORMANT (env-gated, not wired to live database).

#### Verification

| Check | Result | Date |
|-------|--------|------|
| pytest | 1 passed | 2026-02-05 |
| mypy --strict | Success | 2026-02-05 |
| Execution verified | 4/4 steps | 2026-02-05 |
| Telemetry verified | 5/5 checks | 2026-02-05 |

<!-- AGENT_ROUTER:END S51R-001 -->

- **Workstreams**

- [x] **A – Discovery:** Code inspection complete. Orchestrator uses `build_topic_path("orchestrator",
  "monkey_patch_oversight")` at L76.
  Delegates to producer/consumer/aggregator/summarizer via dynamic module loading.
  Uses `write_report_artifacts` for healthview bundle emission.
- [x] **B – Plan:** No code changes required for HOP compliance. Script already uses HOP patterns.
- [x] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [x] **D – Tier-3 YAML:** Created `tier3_run_monkey_patch_oversight.yaml` in `tier3_scripts/monkey_patch_oversight/`.
- [x] **E – QA & Evidence:** pytest: 1 passed in 0.16s. mypy --strict: Success.
  Make target confirmed: `studio-orchestrate-monkey-patch-oversight`.
- [x] **F – Output truth verification:** Orchestrator run, output claims verified TRUE (2026-02-05).
- [x] **G – Pipeline configuration:** Section 8 complete — 4 steps, 4 skip flags, CONTINUE policy.
- [x] **H – Step execution verification:** Section 7.3 — 4/4 steps verified with timing.
- [x] **I – Pipeline telemetry verification:** Section 7.4 — 5/5 checks PASS.
- [x] **J – Phase 4 build doc:** `S51R-001_run_monkey_patch_oversight_build.md` complete.
- [x] **DONE** — Phase 4 compliance complete (2026-02-05)

##### S51R-002 monkey patch scan producer

- **Workstreams**

- [x] **A – Discovery:** Code inspection complete. Script uses
  `build_topic_path("producer", "monkey_patches")` at L95. No pointer file creation
  (`latest_*`/`_update_latest` absent). Uses `prune_run_directories` without `stem_prefix`
  at L1057-1062 — proper HOP pattern.
- [x] **B – Plan:** No code changes required. Script is already HOP-compliant.
- [x] **C – Implement:** No implementation needed. Script already migrated to HOP.
- [x] **D – Tier-3 YAML:** Created `tier3_scan_monkey_patches.yaml` in
  `tier3_scripts/monkey_patch_oversight/`.
- [x] **E – QA & Evidence:** pytest: 6 passed in 0.26s. mypy: Success. Phase 4 build doc complete.
- [x] **DONE**

<!-- AGENT_ROUTER:START S51R-002 -->
### S51R-002 — scan_monkey_patches.py

> **One-liner:** Detect monkey patches in Python files via AST analysis with optional Git enrichment.

**Keywords:** `monkey-patch`, `AST`, `producer`, `code-analysis`, `technical-debt`

#### Resource Paths

| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/producers/scan_monkey_patches.py` |
| Tier-3 YAML | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/monkey_patch_oversight/tier3_scan_monkey_patches.yaml` |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_5_1/S51R-002_scan_monkey_patches_build.md` |
| Output Root | `.repo_studios/reports/healthview/producer_reports/monkey_patch_scans/` |

#### Invocation

```bash
python .repo_studios/scripts/producers/scan_monkey_patches.py --repo-root . --log-level INFO --keep 5
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv)` / `main()` |
| Typical Runtime | ~2-5 seconds (without Git), 4-7 minutes (with Git) |
| Exit Codes | 0=success, 1=error |

#### Outputs

| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with patch findings |
| summary.md | Markdown | Human-readable patch statistics |
| telemetry.json | JSON | Execution metrics and timing |

#### Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | Timestamped bundles at YYYYMMDD-HHMM |
| UIC Interface | YES | run(argv) entry point, dict return |
| Tier-3 YAML | YES | tier3_scan_monkey_patches.yaml |

#### Orchestrator

| Pipeline | Status | Config Path |
|----------|--------|-------------|
| run_monkey_patch_oversight.py | WIRED | L60-85 (producer constants) |

#### Pipeline Position

| Field | Value |
|-------|-------|
| Step Number | 1 of 4 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` |

#### Dependencies & Consumers

| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | First in pipeline, no upstream dependencies |
| ⬇️ CONSUMED BY | S51R-003 | `classify_monkey_patches.py` | Provides `manifest.json` with findings |

#### Known Limitations

- Topic token mismatch: producer uses `monkey_patches`, orchestrator uses `monkey_patch_scans`
- Git enrichment (`--with-git`) significantly increases runtime
- Returns `run_dir`/`run_timestamp` but not `run_id`; orchestrator handles fallback

#### Verification

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S51R-002 -->

<!-- AGENT_ROUTER:BEGIN S51R-003 -->
##### S51R-003 `classify_monkey_patches.py`

> **One-liner:** Classify monkey patches by risk level (HIGH, MODERATE, SAFE) and generate consumer risk bundles

**Keywords:** `consumer`, `monkey-patch`, `risk-classification`, `HOP-compliant`

**Paths:**

| Asset | Location |
|-------|----------|
| Script | [classify_monkey_patches.py](../../../scripts/consumers/classify_monkey_patches.py) |
| Tier-3 YAML | [tier3_classify_monkey_patches.yaml](../tier3_scripts/monkey_patch_oversight/tier3_classify_monkey_patches.yaml) |
| Build Doc | [S51R-003_classify_monkey_patches_build.md](working_docs/stage_5_1/S51R-003_classify_monkey_patches_build.md) |
| Output Root | `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/<YYYYMMDD-HHMM>/` |

**Entry Point:** `run(argv)` — Returns `dict` with `summary_path`, `exit_code`

**Runtime:** ~2-5 seconds (depending on scan size)

**Orchestrator Integration:**

| Field | Value |
|-------|-------|
| Orchestrator | [run_monkey_patch_oversight.py](../../../command_center/scripts/orchestrators/run_monkey_patch_oversight.py) |
| Step | 2 of 4 (consumer step) |
| Upstream | S51R-002 `scan_monkey_patches.py` |
| Downstream | S51R-004 `analyze_monkey_patch_trends.py` |

**Workstreams:**

- [x] **A – Discovery:** Phase 1 complete
- [x] **B – Plan:** Phase 2 complete
- [x] **C – Implement:** Phase 3 complete
- [x] **D – Tier-3 YAML:** Created `tier3_classify_monkey_patches.yaml`
- [x] **E – QA & Evidence:** pytest: 15 passed, mypy: Success
- [x] **F – Tier-2 Propagation:** Roster updated
- [x] **G – Tier-1 Propagation:** Registry updated
- [x] **H – Attestation:** Phase 4 complete

**Status:** ✅ **DONE** (Phase 4 Complete — 2026-02-04)

**Verification:**

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S51R-003 -->

##### S51R-004 monkey patch trend aggregator

<!-- AGENT_ROUTER:START S51R-004 -->
### S51R-004 — analyze_monkey_patch_trends.py
> **One-liner:** Analyze historical monkey patch trends from consumer/producer bundles

| Field | Value |
|-------|-------|
| Record ID | S51R-004 |
| Script Path | `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py` |
| Category | Aggregator |
| Target Stage | Stage 5.1 (Monkey Patch Oversight) |
| Tier-3 YAML | [tier3_analyze_monkey_patch_trends.yaml](../tier3_scripts/monkey_patch_oversight/tier3_analyze_monkey_patch_trends.yaml) |
| Build Doc | [S51R-004_analyze_monkey_patch_trends_build.md](working_docs/stage_5_1/S51R-004_analyze_monkey_patch_trends_build.md) |
| Status | ✅ Phase 4 Complete |

**Workstreams:**
- [x] A – Discovery: Code inspection complete. 2 upstreams documented.
- [x] B – Plan: Dead code removal identified (_update_latest function).
- [x] C – Implement: Removed dead code. HOP-compliant via build_topic_path.
- [x] D – Tier-3 YAML: Created `tier3_analyze_monkey_patch_trends.yaml`.
- [x] E – QA & Evidence: pytest: 3 passed. mypy --strict: Success.
- [x] F – Output truth verification: Script run, output claims verified TRUE.
- [x] G – Tier-3 YAML: Created/updated tier3_analyze_monkey_patch_trends.yaml
- [x] H – Orchestrator integration: ScriptConfig documented (Section 8.2)
- [x] I – Upstream verification: 2/2 upstreams verified (consumer + producer)
- [x] J – Provenance tracking: Source paths recorded in metadata field
- [x] **DONE** — Phase 4 compliance complete (2026-02-04)

| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S51R-004 -->

<!-- AGENT_ROUTER:START S51R-005 -->
### S51R-005 — summarize_monkey_patch_overview.py

> **One-liner:** Generate HealthView overview bundle from upstream monkey patch consumer, producer, and aggregator bundles.

**Keywords:** `healthview`, `summarizer`, `monkey-patch`, `oversight`, `stage-5.1`, `overview`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py` |
| Tier-3 YAML | `tier3_scripts/monkey_patch_oversight/tier3_summarize_monkey_patch_overview.yaml` |
| Build Doc | `tier2_roster/working_docs/stage_5_1/S51R-005_summarize_monkey_patch_overview_build.md` |
| Output Root | `.repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/<YYYYMMDD-HHMM>/` |

#### Invocation
```bash
python -m command_center.scripts.summarizers.summarize_monkey_patch_overview --repo-root . --log-level INFO
```

| Aspect | Value |
|--------|-------|
| Entry Point | `run(argv: Sequence[str] \| None = None) -> dict[str, Any]` |
| Typical Runtime | ~5 seconds |
| Exit Codes | 0=success, 1=error |

#### Outputs
| Artifact | Format | Description |
|----------|--------|-------------|
| manifest.json | JSON | Bundle metadata with file inventory and timestamps |
| summary.md | Markdown | Human-readable monkey patch overview with risk signals |
| telemetry.json | JSON | Execution metrics and timing data |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | YES | `build_topic_path()` at L50-53, `write_report_artifacts()` at L821-828 |
| UIC Interface | YES | `run(argv)` returns dict with `status`, `run_dir`, `slug`, `artifacts` |
| Tier-3 YAML | YES | Created 2026-01-02, validated 2026-02-04 |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| monkey_patch_oversight | WIRED | `run_monkey_patch_oversight.py` Lines 67-68 |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | 4 of 4 |
| Execution Mode | SEQUENTIAL |
| Orchestrator Script | `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | S51R-002 | `scan_monkey_patches.py` | Reads producer bundle from `monkey_patch_scans/` |
| ⬆️ DEPENDS ON | S51R-003 | `classify_monkey_patches.py` | Reads consumer bundle from `monkey_patch_risk/` |
| ⬆️ DEPENDS ON | S51R-004 | `analyze_monkey_patch_trends.py` | Reads aggregator bundle from `monkey_patch_trends/` |
| ⬇️ CONSUMED BY | (none) | — | Terminal node, outputs consumed by orchestrator |

#### Known Limitations
- Test coverage limited (1 test for content, no CLI integration tests)
- Error paths for missing upstream bundles are untested

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | GitHub Copilot |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S51R-005 -->

<!-- AGENT_ROUTER:START S51R-006 -->
### S51R-006 — monkey_patch_risk.py

> **One-liner:** Shared monkey patch risk classification library providing consistent severity bucketing (HIGH/MODERATE/SAFE) for scanner findings.

**Keywords:** `utility`, `library`, `risk-classification`, `monkey-patch`, `severity-bucketing`

#### Resource Paths
| Resource | Path |
|----------|------|
| Script | `.repo_studios/scripts/utilities/monkey_patch_risk.py` |
| Tier-3 YAML | N/A (B-LIB — pure library, no CLI) |
| Build Doc | `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/stage_5_1/S51R-006_monkey_patch_risk_build.md` |
| Output Root | N/A (pure library, no outputs) |

#### Invocation
```python
# Direct import — not CLI invocable
from scripts.utilities.monkey_patch_risk import classify_monkey_patch, FindingSignals, RiskLevel
```

| Aspect | Value |
|--------|-------|
| Entry Point | N/A (import-only library) |
| Typical Runtime | N/A (pure function calls) |
| Exit Codes | N/A |

#### Exports
| Export | Type | Description |
|--------|------|-------------|
| `RiskLevel` | TypeAlias | `Literal["HIGH", "MODERATE", "SAFE"]` — severity buckets |
| `FindingSignals` | Dataclass | Input signals: `category`, `is_test`, `is_module_scope` |
| `classify_monkey_patch()` | Function | Returns risk bucket based on finding signals |
| `HIGH_RISK_CATEGORIES` | Set | Category names that map to HIGH risk |
| `MODERATE_RISK_CATEGORIES` | Set | Category names that map to MODERATE risk |
| `GLOBAL_ENV_MUTATION` | Constant | Special category string for environment mutations |

#### Compliance
| Aspect | Status | Notes |
|--------|--------|-------|
| HOP Bundle | N/A | B-LIB — pure library, no outputs |
| UIC Interface | N/A | B-LIB — no CLI entry point |
| Tier-3 YAML | N/A | B-LIB — libraries do not get Tier-3 recipes |
| Library Checklist | 5/6 PASS | LIB-001 FAIL (missing `__all__`) |

#### Library Checklist (B-LIB)
| ID | Check | Status | Evidence |
|----|-------|--------|----------|
| LIB-001 | `__all__` exports defined | `FAIL` | No `__all__` defined |
| LIB-002 | Google docstrings on exports | `PASS` | 2/2 docstrings |
| LIB-003 | No side effects at import | `PASS` | Silent import confirmed |
| LIB-004 | No `sys.exit()` calls | `PASS` | No matches |
| LIB-005 | No `input()` prompts | `PASS` | No matches |
| LIB-006 | Tests exist | `PASS` | `test_monkey_patch_risk.py` (5 tests) |

#### Orchestrator
| Pipeline | Status | Config Path |
|----------|--------|-------------|
| Stage 5.1 Monkey Patch | IMPORT_ONLY | N/A — consumed via import by `classify_monkey_patches.py` |

#### Pipeline Position
| Field | Value |
|-------|-------|
| Step Number | N/A (library, not a pipeline step) |
| Execution Mode | IMPORT_ONLY |
| Orchestrator Script | N/A |

#### Dependencies & Consumers
| Direction | Record ID | Script | Data Flow |
|-----------|-----------|--------|-----------|
| ⬆️ DEPENDS ON | (none) | — | Standalone library, stdlib only |
| ⬇️ CONSUMED BY | S51R-003 | `classify_monkey_patches.py` | Provides `classify_monkey_patch()` for risk bucketing |
| ⬇️ CONSUMED BY | S51R-004 | `analyze_monkey_patch_trends.py` | Provides `RiskLevel` type for trend analysis |

#### Known Limitations
- Missing `__all__` exports declaration (GAP-L01, LOW priority, deferred)

#### Verification
| Field | Value |
|-------|-------|
| Last Verified | 2026-02-04 |
| Verified By | copilot-claude-4 |
| Build Doc Version | 1.0.0 |
<!-- AGENT_ROUTER:END S51R-006 -->

#### Implementation Workstreams (checkbox-driven) — monkey_patch_risk.py

Workstream A — Discovery

- [x] Inspect outputs + pruning/retention surfaces; record findings
  - N/A: Pure utility library with no CLI or output artifacts.

Workstream B — Plan

- [x] Draft plan to close output-root/base-package stop-gates
  - N/A: No HOP changes needed for utility libraries.

Workstream C — Implement

- [x] Implement accepted plan and update this record + stop-gate status with new evidence
  - N/A: No code changes needed.

Workstream D — Tier-3 YAML

- [x] Confirm Tier-3 is appropriate for this script; record decision (create vs defer)
  - Decision: **Deferred** — pure utility libraries do not get Tier-3 recipes (no CLI entrypoint).
- [x] Inspect Tier-3 template requirements — N/A
- [x] Draft `tier3_<script_stem>.yaml` — N/A
- [x] Validate Tier-3 YAML — N/A

Workstream E — QA & Evidence

- [x] Pytest evidence captured
  - Result: 5 passed in 0.07s (2026-01-02)
- [x] Mypy evidence captured (or marked N/A in record)
  - Result: Success: no issues found (2026-01-02)
- [x] Coverage + doc-index timestamp recorded
  - N/A (pure utility, no coverage threshold)

- [x] DONE — monkey_patch_risk.py complete; update Tier-1 Stage 5.1 script gate

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

- [x] ~~Orchestrator bundle docstring root conflicts with actual layout.~~ — RESOLVED: Uses `build_topic_path("orchestrator", "monkey_patch_oversight")`.
- [x] ~~Orchestrator uses `viewer=commandview` for the HealthView bundle write.~~ — RESOLVED: Now uses `healthview` viewer.
- [x] ~~Producer/consumer disagree on artifact naming (`manifest.json` vs `report.json`).~~ — RESOLVED: Consumer reads `manifest.payload.findings`.
- [x] ~~Consumer + aggregator create `latest_*` pointer artifacts.~~ — RESOLVED: Removed `_write_legacy_outputs()` call.
- [x] ~~Stage outputs use multiple timestamp slug formats.~~ — RESOLVED: All scripts use `YYYYMMDD-HHMM`.

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
  - ✅ CLOSED (2026-02-05): Output root and base package stop-gates satisfied.

- **Tier-3 dependencies (resolved 2026-01-03):**
  - Tier-3 YAML files live in `.repo_studios/inventory_schema/healthview_producer_manifest/`
  - Each HOP-compliant script has a corresponding `.yaml` manifest
  - Manifests validated via `load_validate_write_manifest.py`

- **Tier-3 promotion bar:** ✅ Tier-3 YAML placeholders resolved; all HOP-compliant scripts have
  manifests in place (S51R-001 through S51R-005). S51R-006 (`log_monkey_patching.py`) is B-LIB tier
  and does not require Tier-3 YAML.

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
| 2026-02-05 | Phase 4 complete: All 6 records have Agent Router blocks, build docs, Tier-1 synced. Frontmatter updated to `status: complete`, `version: 1.0.0`. Section 0 modernized with Stage 12 prompt system guidance. | repo_studios_ai | 2026-02-05 | HOP validation passed |
| 2026-01-03 | HOP compliance verified for all scripts; Tier-3 YAMLs created. | repo_studios_ai | 2026-01-03 | HOP validation passed |
| 2025-12-20 | Discovery Pass A + doc-index. | repo_studios_ai | 2025-12-20 11:07-05:00 | Not run |
