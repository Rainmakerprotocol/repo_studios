---
title: "Tier-2 Roster — Stage 11.1 Available Scripts (Holding Area)"
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
updated_at: 2025-12-21
tags:
  - pipeline
  - healthview
  - hop
  - tier-2
  - stage-11-1
  - available-scripts
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/scripts/script_inventory_architecture.md
  - .github/instructions/markdown.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Roster — Stage 11.1 Available Scripts (Holding Area)

> **Purpose:** This Tier-2 roster documents Stage 11.1 (“Available Scripts”) for the HealthView HOP.
> Unlike stages 1.1–7, Stage 11.1 is a holding area: these scripts are *discoverable and eligible*
> for HealthView use, but are *not yet* wired into the orchestrator blast-radius chain.
>
> This roster exists to:
>
> - preserve provenance (what scripts are in the holding area, and why),
> - define promotion stop-gates (what must be true before a script is adopted into an orchestrator),
> - provide per-script inspection records so adoption work can start without re-discovery.
>
> **Tier-1 source:** Stage 11.1 in
> `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`.
> **Locked decisions source:** Tier-1 spine + `REPORT_NAMING_STANDARDS.md`.
> **Last synced with Tier-1:** 2025-12-20.
>
> Standards: `.github/instructions/markdown.instructions.md` (reviewed 2025-12-20).

---

## 0. Instruction Block for Editors & AI Assistants

- This document inherits terminology and stage ordering from the Tier-1 spine:
  `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier1_healthview_orchestration_pipeline.md`.
- Preserve the canonical Tier-2 section order.
- Do not treat “Available Scripts” as orchestration coverage; Stage 11.1 is a holding roster.
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

1. Provide a single authoritative Tier-2 roster for Stage 11.1 that engineers and agents can use
   to promote a script into an orchestrator without re-litigating the contract.
1. Make promotion gates explicit (HOP output contract, pruning discipline, pointer-ban, DB marker
   rules) while keeping Stage 11.1 truthful: it is not a runtime chain.
1. Maintain per-script inspection records so “holding” does not become “lost in inventory.”

**Success criteria:**

- Tier-1 Stage 11.1 links to this doc as the Stage 11.1 Tier-2 roster.
- This doc contains:
  - a Records index + Pruning index,
  - a ScriptInspectionRecordV1 schema,
  - per-script record blocks,
  - stop-gates required before any orchestrator claims promotion/compliance.

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** 11.1 — Available Scripts
  (`tier1_healthview_orchestration_pipeline.md` → Stage 11.1)
- **Tier-2 scope:** This document covers Stage 11.1 only.

### 2.2 Holding Inventory (Stage 11.1)

**Orchestrator:**

- None. Stage 11.1 is a holding roster, not an executed chain.

**Available scripts (Tier-1 holding list):**

- Consumer: `.repo_studios/scripts/consumers/generate_anchor_health_report.py` (planned Stage 2.2)
- Utility: `.repo_studios/scripts/utilities/configure_faulthandler_runtime.py` (planned Stage 3.2)
- Utility: `.repo_studios/scripts/utilities/dump_faulthandler_snapshot.py` (planned Stage 3.2)
- Utility: `.repo_studios/scripts/utilities/fault_run_analysis.py` (planned Stage 3.2)
- Producer: `.repo_studios/scripts/producers/validate_import_boundaries.py` (planned Stage 4.2)
- Producer: `.repo_studios/scripts/producers/extract_standards_rules.py` (planned Stage 6.2)
- Producer: `.repo_studios/scripts/producers/check_inventory_health.py` (questionable)
- Producer: `.repo_studios/scripts/producers/validate_inventory.py` (questionable)
- Producer: `.repo_studios/scripts/producers/render_inventory_views.py`
  (out-of-scope for HealthView today)
- Producer: `.repo_studios/scripts/producers/generate_lizard_report.py`
  (out-of-scope for HealthView today)
- Library: `.repo_studios/command_center/scripts/libraries/test_log_analysis.py` (available by design)

### 2.3 Current vs Target Contract Snapshot (Stage 11.1)

This section is the short, scannable contract summary that Tier-1 routes to.

Authoritative entry points for Tier-1 routing and agent discovery are:

- this Contract Snapshot,
- the Stop-Gates section,
- the Records Index.

**Target contract (locked decisions):**

- Stage 11.1 is a holding roster only; it does not claim orchestration coverage.
- Promotion into an orchestrator is performed by wiring the script into an orchestrator and moving
  its reference out of Stage 11.1 in Tier-1.
- When a promoted script emits HealthView bundles, the promoted surface must align to the HOP
  contract:
  - Canonical HealthView output root:
    `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
  - Base package (HOP target):
    - `manifest.json`
    - `summary.md`
    - `telemetry.json`
  - No pointer files like `latest_*` / `current_*`.
  - Pruning mechanisms and targets are explicit, stable, and evidence-backed.
  - If DB writes are present: gate behind `REPO_STUDIOS_DB_ENABLED`, warn-only failures, and include
    `DB_INTEGRATION_MARKER:` at each callsite.

**Current evidence (repo-observed):**

- Stage 11.1 is currently represented as a Tier-1 holding list.
- Output roots, artifact sets, retention surfaces, and DB callsites are partially captured; depth
  varies by script; unknowns remain stop-gates.

Mismatch and unknowns are treated as stop-gates for promotion.

---

## 3. Stage Narrative — 11.1 Available Scripts

### 3.1 Records & Inspection (v1)

This section keeps the script-level inspection evidence in Tier-2 (not Tier-1).

#### 3.1.1 Records Index

A short index that links to each per-script record block in this document.

- ASR-001 — `generate_anchor_health_report.py` — consumer — [ASR-001](#asr-001-generate_anchor_health_reportpy)
- ASR-002 — `configure_faulthandler_runtime.py` — utility — [ASR-002](#asr-002-configure_faulthandler_runtimepy)
- ASR-003 — `dump_faulthandler_snapshot.py` — utility — [ASR-003](#asr-003-dump_faulthandler_snapshotpy)
- ASR-004 — `fault_run_analysis.py` — utility — [ASR-004](#asr-004-fault_run_analysispy)
- ASR-005 — `validate_import_boundaries.py` — producer — [ASR-005](#asr-005-validate_import_boundariespy)
- ASR-006 — `extract_standards_rules.py` — producer — [ASR-006](#asr-006-extract_standards_rulespy)
- ASR-007 — `check_inventory_health.py` — producer — [ASR-007](#asr-007-check_inventory_healthpy)
- ASR-008 — `validate_inventory.py` — producer — [ASR-008](#asr-008-validate_inventorypy)
- ASR-010 — `render_inventory_views.py` — producer — [ASR-010](#asr-010-render_inventory_viewspy)
- ASR-011 — `generate_lizard_report.py` — producer — [ASR-011](#asr-011-generate_lizard_reportpy)
- ASR-013 — `test_log_analysis.py` — utility (library) — [ASR-013](#asr-013-test_log_analysispy)

#### 3.1.2 Pruning Index (mini-block)

Stage 11.1 is not a bundle-emitting chain, so pruning is not defined at the stage level.
Pruning/retention semantics are per-script and become gating only once a script is promoted into an
orchestrator.

- **Pruning surfaces:** Per-script (unknown until inspected)
- **Pruning mechanism:** Per-script (unknown until inspected)
- **Pruning targets:** Per-script (unknown until inspected)
- **Pruning guardrails:** Per-script (unknown until inspected)
- **Evidence source:** Per-script records (once populated)

#### 3.1.3 ScriptInspectionRecordV1 Schema

Use this schema as the per-script record structure for this stage.

```yaml
schema: ScriptInspectionRecordV1
fields:
  record_id: "ASR-001"
  script:
    path: ".repo_studios/scripts/consumers/generate_anchor_health_report.py"
    name: "generate_anchor_health_report.py"
    category: "producer|consumer|aggregator|summarizer|utility|orchestrator"
  tier3:
    metadata_block_version: "v1"
    allowed: false
    exists: false
    name: "tier3_generate_anchor_health_report.yaml"
    meets_template: "NA"
    last_updated: null
  cli_surfaces:
    run_entrypoint: "run(argv)|main(argv)|other"
    key_flags:
      - "--log-level"
  io_contract:
    inputs:
      - "Not yet inspected"
    outputs:
      current:
        root: "Unknown (not yet inspected)"
        artifacts: []
      target:
        root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
        artifacts:
          - "manifest.json"
          - "summary.md"
          - "telemetry.json"
  retention:
    surfaces:
      - "Unknown (not yet inspected)"
    mechanism: "Unknown (not yet inspected)"
    targets:
      - "Unknown (not yet inspected)"
    guardrails:
      - "Unknown (not yet inspected)"
    evidence:
      - "None captured yet"
  db_integration:
    gated_by: "REPO_STUDIOS_DB_ENABLED"
    marker_required: true
    marker_string: "DB_INTEGRATION_MARKER:"
  evidence:
    code_refs: []
    tests: []
    fixtures: []
  notes:
    - "Short, evidence-backed notes. Unknowns must be explicit."
```

#### 3.1.4 Per-Script Full Record Blocks

These records are intentionally seeded in a “not yet inspected” state; promotion work should
populate evidence and close stop-gates before a script is adopted.

##### ASR-001: generate_anchor_health_report.py

```yaml
record_id: "ASR-001"
script:
  path: ".repo_studios/scripts/consumers/generate_anchor_health_report.py"
  name: "generate_anchor_health_report.py"
  category: "consumer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_generate_anchor_health_report.yaml"
  meets_template: "yes"
  last_updated: "2026-01-28"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_generate_anchor_health_report.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/ASR-001_generate_anchor_health_report_build.md"
cli_surfaces:
  run_entrypoint: "run(*, argv=...)"
  key_flags:
    - "--inventory-report"
    - "--output-dir"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Optional anchor inventory report path (--inventory-report); if absent, attempts to load latest via utilities.anchor_inventory_loader"
    - "Docs tree scan root (defaults to docs/) when no inventory report is available"
    - "Baseline JSON: tests/docs/anchor_slug_baseline.json (read if present)"
  outputs:
    current:
      root: ".repo_studios/reports/consumer_reports/anchor_health/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
        - "anchor_report.json (supplementary)"
        - "anchor_report.md (supplementary)"
        - "clusters.tsv (supplementary)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    status: "✅ Base package aligned (2026-01-25)"
retention:
  surfaces:
    - "--artifacts-to-keep (default present)"
    - "Run directory prefix: anchor_health-YYYY-MM-DD_HHMM"
  mechanism: "prune_run_directories(keep=N, stem_prefix=anchor_health-, current_run=<run_dir>)"
  targets:
    - ".repo_studios/reports/consumer_reports/anchor_health/"
  guardrails:
    - "Keeps current run; prunes older run directories beyond keep"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "Artifacts written into timestamped run directory; manifest.json contains artifact paths"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: false
  marker_string: null
  notes:
    - "Script uses direct file writes (not create_storage())"
    - "DB_INTEGRATION_MARKER tags not present — would need retrofit for dual-write"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_available_scripts_oversight.py"
  supports_output_dir: false
  supports_artifacts_to_keep: true
  uses_argv_kwarg: true
evidence:
  code_refs:
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L1-L27 (HOP docstring)"
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L292 (OUTPUT_DIR via build_topic_path)"
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L405-L513 (write_artifacts with base package)"
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L558-L625 (run(*, argv=...) entry)"
  tests:
    - ".repo_studios/tests/tests_consumers/test_generate_anchor_health_report.py::test_anchor_health_uses_inventory_artifacts (PASSED)"
    - ".repo_studios/tests/tests_consumers/test_generate_anchor_health_report.py::test_anchor_health_falls_back_to_docs_scan (PASSED)"
    - ".repo_studios/tests/tests_consumers/test_generate_anchor_health_report.py::test_anchor_health_prunes_history (PASSED)"
  fixtures: []
notes:
  - "Classification: HOP-compliant consumer, orchestrator integration complete."
  - "Contract status: ✅ aligned with HOP base package (manifest.json, summary.md, telemetry.json)"
  - "Entry surface: run(*, argv=...) — keyword-args signature with argv passthrough."
  - "DB integration: NOT using create_storage(), no DB_INTEGRATION_MARKER tags."
  - "Phase 4 processing: Code complete 2026-01-25; Doc complete 2026-01-28."
```

#### Implementation Workstreams (checkbox-driven) — generate_anchor_health_report.py

- [x] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [x] B. Plan — artifact renaming to HOP base package
- [x] C. Implement — docstring update, artifact names changed, return keys updated
- [x] D. Evidence — tests passing (3/3)
- [x] E. Bug fix — `main()` now properly passes `sys.argv[1:]` to `run()` (2026-01-26)
- [x] F. Output truth verification — script run, output claims verified TRUE
- [x] G. Tier-3 YAML — created tier3_generate_anchor_health_report.yaml (Stage 11.1 location)
- [x] H. Orchestrator integration — added to run_available_scripts_oversight.py, uses_argv_kwarg=True
- [x] DONE — Phase 4 compliance complete (2026-01-28)

##### ASR-002: configure_faulthandler_runtime.py

```yaml
record_id: "ASR-002"
script:
  path: ".repo_studios/scripts/utilities/configure_faulthandler_runtime.py"
  name: "configure_faulthandler_runtime.py"
  category: "utility"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_configure_faulthandler_runtime.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "import-time bootstrap (auto) + __main__ prints JSON payload"
  key_flags: []
io_contract:
  inputs:
    - "Environment variables (selected): FAULT_DISABLE, FAULT_ENABLE, FAULT_OUTDIR, FAULT_BASE_DIR,
        FAULT_ARTIFACTS_TO_KEEP, FAULT_DUMP_LATER, FAULT_TEE_STDERR, FAULT_MIN_INTERVAL_SEC, FAULT_DUMP_TIMEOUT,
        FAULT_MAX_DUMPS_PER_RUN, FAULT_REDACT_PATHS, FAULT_LOGS_ALLOW_LEGACY"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/rawview/fault_diagnostics_runs/<YYYY-MM-DD_HHMM>/ (default)"
      artifacts:
        - "stacks.log"
        - "MANIFEST.json"
        - "bundle_summary.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "FAULT_ARTIFACTS_TO_KEEP (default present; value not captured here)"
    - "Derived outdir naming: YYYY-MM-DD_HHMM (when FAULT_OUTDIR is not set)"
  mechanism: "prune_run_directories(keep=N, current_run=<outdir>)"
  targets:
    - ".repo_studios/command_center/reports/rawview/fault_diagnostics_runs/ (default base)"
    - ".repo_studios/faulthandler/ (when FAULT_LOGS_ALLOW_LEGACY is enabled)"
  guardrails:
    - "Keeps current run; prunes older derived run directories beyond keep"
  evidence:
    - "Writes a MANIFEST.json and bundle_summary.json into the resolved outdir when enabled"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/utilities/configure_faulthandler_runtime.py#L1-L43"
    - ".repo_studios/scripts/utilities/configure_faulthandler_runtime.py#L60-L118"
    - ".repo_studios/scripts/utilities/configure_faulthandler_runtime.py#L252-L374"
  tests: []
  fixtures: []
notes:
  - "Classification: experimental/hold (import-time bootstrap + runnable script; unclear whether this should be orchestrated as a stage step vs treated as shared runtime setup)."
  - "Contract gaps: output root defaults under command_center rawview; artifacts are stacks.log/MANIFEST.json/bundle_summary.json (not the base package: manifest.json/summary.md/telemetry.json)."
  - "Entry surface: import-time side effects (auto bootstrap unless FAULT_DISABLE); also runnable as a script (prints JSON payload)."
  - "Primary purpose: configures Python faulthandler and a thread-safe stacks.log writer; records a manifest + bundle summary for later analysis tooling."
```

#### Implementation Workstreams (checkbox-driven) — configure_faulthandler_runtime.py

- [x] A. Discovery — import-time bootstrap utility, no CLI entry point
- [x] B. Plan — library/utility classification, no HOP processing needed
- [x] C. Implement — N/A (no artifact output requiring HOP alignment)
- [x] D. Evidence — N/A (library module)
- [ ] E. Promote — N/A (runtime utility, not orchestrated)
- [x] DONE — Phase 4 classification: utility/library, no changes needed (2026-01-25)

##### ASR-003: dump_faulthandler_snapshot.py

```yaml
record_id: "ASR-003"
script:
  path: ".repo_studios/scripts/utilities/dump_faulthandler_snapshot.py"
  name: "dump_faulthandler_snapshot.py"
  category: "utility"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_dump_faulthandler_snapshot.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main() -> dump_snapshot()"
  key_flags: []
io_contract:
  inputs:
    - "Environment variables (selected): FAULT_SNAPSHOT_BASE_DIR, FAULT_SNAPSHOT_OUTDIR, FAULT_SNAPSHOT_TO_KEEP"
    - "Fallback env surfaces: FAULT_OUTDIR, FAULT_ARTIFACTS_TO_KEEP, FAULT_LOGS_ALLOW_LEGACY"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/rawview/fault_snapshots/<YYYY-MM-DD_HHMMSS>/ (default)"
      artifacts:
        - "snapshot.txt"
        - "MANIFEST.json"
        - "bundle_summary.json"
        - "SUMMARY.md"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "FAULT_SNAPSHOT_TO_KEEP or FAULT_ARTIFACTS_TO_KEEP (default present; value not captured here)"
    - "Derived outdir naming: YYYY-MM-DD_HHMMSS (when FAULT_SNAPSHOT_OUTDIR/FAULT_OUTDIR not set)"
  mechanism: "prune_run_directories(keep=N, current_run=<outdir>)"
  targets:
    - ".repo_studios/command_center/reports/rawview/fault_snapshots/ (default base)"
    - ".repo_studios/faulthandler/ (when FAULT_LOGS_ALLOW_LEGACY is enabled)"
  guardrails:
    - "Keeps current run; prunes older derived run directories beyond keep"
  evidence:
    - "Writes MANIFEST.json and bundle_summary.json alongside snapshot.txt"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/utilities/dump_faulthandler_snapshot.py#L1-L24"
    - ".repo_studios/scripts/utilities/dump_faulthandler_snapshot.py#L60-L124"
    - ".repo_studios/scripts/utilities/dump_faulthandler_snapshot.py#L126-L209"
    - ".repo_studios/scripts/utilities/dump_faulthandler_snapshot.py#L211-L268"
  tests: []
  fixtures: []
notes:
  - "Classification: candidate for future orchestration."
  - "Contract gaps: output root defaults under command_center rawview; artifact names include MANIFEST.json/SUMMARY.md and bundle_summary.json (not the base package: manifest.json/summary.md/telemetry.json)."
  - "Entry surface: CLI (main) and importable (dump_snapshot)."
  - "Primary purpose: emits a structured faulthandler snapshot bundle (snapshot.txt + JSON manifest/summary + SUMMARY.md) under a timestamped rawview directory for downstream ingestion."
```

##### Promotion Mapping (hypothetical) — dump_faulthandler_snapshot.py

- Proposed future stage: **3.2** (fault diagnostics / faulthandler vertical)
- Minimal orchestrator wrapper required: a orchestrator that calls
  `dump_snapshot()` (or `main()`), then packages the run into the HealthView
  base bundle (manifest/summary/telemetry) under the stage's canonical
  output root
- Known contract deltas vs target stage:
  - Current output root defaults under
    `command_center/reports/rawview/fault_snapshots/...` (rawview) rather than
    canonical HealthView root
  - Artifact naming is mixed (e.g., `MANIFEST.json` + `SUMMARY.md` vs target `manifest.json` + `summary.md`)
  - Retention is env-driven today; promotion would need the wrapper to expose
    (or standardize) a stage-level pruning surface consistent with other
    HealthView stages

#### Implementation Workstreams (checkbox-driven) — dump_faulthandler_snapshot.py

- [x] A. Discovery — rawview utility with main(), writes MANIFEST.json/SUMMARY.md
- [x] B. Plan — rawview utility classification, deferred HOP alignment
- [ ] C. Implement — deferred (rawview scripts follow different artifact pattern)
- [x] D. Evidence — N/A for Phase 4 (rawview utility)
- [ ] E. Promote — deferred to rawview alignment phase
- [x] DONE — Phase 4 classification: rawview utility, deferred (2026-01-25)

##### ASR-004: fault_run_analysis.py

```yaml
record_id: "ASR-004"
script:
  path: ".repo_studios/scripts/utilities/fault_run_analysis.py"
  name: "fault_run_analysis.py"
  category: "utility"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_fault_run_analysis.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "import-only (library module)"
  key_flags: []
io_contract:
  inputs:
    - "Run directory path (outdir) containing stacks.log and optionally MANIFEST.json"
    - "Optional parameters: top_n, now (datetime)"
  outputs:
    current:
      root: "None (returns in-memory structures); may create MANIFEST.json in outdir if missing"
      artifacts:
        - "MANIFEST.json (created if missing by ensure_manifest)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "None observed (no retention/pruning logic in this module)"
  mechanism: "None observed"
  targets:
    - "None"
  guardrails:
    - "None observed"
  evidence:
    - "Reads stacks.log and emits a structured analysis payload (dict + signature list)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/utilities/fault_run_analysis.py#L1-L34"
    - ".repo_studios/scripts/utilities/fault_run_analysis.py#L109-L170"
    - ".repo_studios/scripts/utilities/fault_run_analysis.py#L261-L319"
  tests: []
  fixtures: []
notes:
  - "Classification: utility/library (never orchestrated)."
  - "Contract gaps: import-only module; does not emit the base package (manifest.json/summary.md/telemetry.json) under the canonical HealthView root; may create MANIFEST.json in an arbitrary outdir when missing."
  - "Entry surface: import-only library (exports build_fault_report and related helpers)."
  - "Primary purpose: parses faulthandler stacks.log text into aggregated signature metrics and a structured report payload for reuse by producer/consumer scripts."
```

#### Implementation Workstreams (checkbox-driven) — fault_run_analysis.py

- [x] A. Discovery — library module, exports parsing helpers
- [x] B. Plan — library classification, no HOP processing needed
- [x] C. Implement — N/A (library-only)
- [x] D. Evidence — N/A (library module)
- [ ] E. Promote — N/A (never orchestrated)
- [x] DONE — Phase 4 classification: library module, no changes needed (2026-01-25)

##### ASR-005: validate_import_boundaries.py

```yaml
record_id: "ASR-005"
script:
  path: ".repo_studios/scripts/producers/validate_import_boundaries.py"
  name: "validate_import_boundaries.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_validate_import_boundaries.yaml"
  meets_template: "yes"
  last_updated: "2026-01-28"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_validate_import_boundaries.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/ASR-005_validate_import_boundaries_build.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--graph-path"
    - "--output-dir"
    - "--allowlist-path"
    - "--artifacts-to-keep"
    - "--strict"
    - "--log-level"
io_contract:
  inputs:
    - "Repo root (used for static scan + resolving relative paths)"
    - "Import graph payload: either explicit --graph-path, or latest telemetry.json/graph.json under .repo_studios/reports/producer_reports/healthview/import_graph/"
    - "Allowlist JSON (defaults to .repo_studios/scripts/producers/import_rules_allowlist.json)"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/producer_reports/import_boundary/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
        - "violations.json"
        - "log.txt"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    status: "✅ ALIGNED (2026-01-26)"
retention:
  surfaces:
    - "--artifacts-to-keep (default from get_keep('validate_import_boundaries'))"
    - "Run directory: timestamp-only YYYYMMDD-HHMM"
  mechanism: "prune_run_directories(keep=N, current_run=<run_dir>)"
  targets:
    - ".repo_studios/reports/healthview/producer_reports/import_boundary/"
  guardrails:
    - "Keeps current run; prunes historical run directories beyond keep"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "Script writes HOP base package (manifest.json, summary.md, telemetry.json)"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
  markers_present:
    - "L442 — manifest.json write"
    - "L446 — summary.md write"  
    - "L464 — telemetry.json write"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_available_scripts_oversight.py"
  supports_output_dir: false
  supports_artifacts_to_keep: true
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L62 (build_topic_path HOP path)"
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L26 (DEFAULT_RELATIVE_GRAPH_DIR — FIXED path order)"
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L442-L464 (DB_INTEGRATION_MARKER writes)"
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L525-L592 (run(argv) entry)"
  tests:
    - ".repo_studios/tests/tests_producers/test_validate_import_boundaries.py::test_emits_structured_artifacts_without_violations (PASSED)"
    - ".repo_studios/tests/tests_producers/test_validate_import_boundaries.py::test_detects_violations_and_honors_allowlist (PASSED)"
  fixtures: []
  qa:
    mypy: "Success: no issues found in 1 source file"
    pytest: "2 passed in 0.19s"
    last_verified: "2026-01-26"
notes:
  - "Classification: HOP-compliant producer, orchestrator integration complete."
  - "Contract status: ✅ aligned with HOP base package (manifest.json, summary.md, telemetry.json)"
  - "Entry surface: run(argv) returns full payload dict; main(argv) returns exit code."
  - "DB integration: Has DB_INTEGRATION_MARKER tags at L442, L446, L464."
  - "Phase 4 processing: Code complete 2026-01-26; Doc complete 2026-01-28."
  - "Note: Legacy Tier-3 also exists at tier3_scripts/dependency_import_hygiene/ (S42R-001 record_id)."
```

#### Implementation Workstreams (checkbox-driven) — validate_import_boundaries.py

- [x] A. Discovery — confirm inputs/outputs, retention, and failure modes
- [x] B. Gap analysis — identify delta between current and target contract
- [x] C. Modification — apply HOP alignment (docstring, artifact naming, telemetry.json)
- [x] D. Evidence — capture tests and representative payload examples
- [x] E. DB markers — added DB_INTEGRATION_MARKER comments to artifact writes (L442, L446, L464)
- [x] F. Tier-3 YAML — created tier3_validate_import_boundaries.yaml (Stage 11.1 location)
- [x] G. QA verification — mypy --strict PASSED, pytest 2/2 PASSED, CLI execution verified
- [x] H. Orchestrator integration — added to run_available_scripts_oversight.py, supports_output_dir=False
- [x] DONE — Phase 4 compliance complete (2026-01-28)
- [ ] I. Promote — wrap in Stage 4.2 orchestrator (pending Stage 4.2 implementation)
- [x] **DONE** — Phase 4 complete with full output truth verification (2026-01-26)

##### ASR-006: extract_standards_rules.py

```yaml
record_id: "ASR-006"
script:
  path: ".repo_studios/scripts/producers/extract_standards_rules.py"
  name: "extract_standards_rules.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_extract_standards_rules.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "import-only (extract_rules)"
  key_flags: []
io_contract:
  inputs:
    - "Markdown file path (Path)"
    - "Rule categories list (list[str])"
    - "Existing rule ids set (set[str])"
    - "Optional today override (YYYY-MM-DD)"
  outputs:
    current:
      root: "None (returns in-memory structures)"
      artifacts: []
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "None observed (no on-disk outputs in this module)"
  mechanism: "None observed"
  targets:
    - "None"
  guardrails:
    - "None observed"
  evidence:
    - "Module parses text and returns (rules, diagnostics) without writing artifacts"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/extract_standards_rules.py#L1-L66"
    - ".repo_studios/scripts/producers/extract_standards_rules.py#L76-L145"
    - ".repo_studios/scripts/producers/extract_standards_rules.py#L151-L246"
  tests: []
  fixtures: []
notes:
  - "Classification: utility/library (never orchestrated)."
  - "Contract gaps: import-only module; does not emit the base package (manifest.json/summary.md/telemetry.json) under the canonical HealthView root (no on-disk bundle)."
  - "Entry surface: import-only helper (extract_rules)."
  - "Primary purpose: parses Markdown source documents to extract standards-rule candidates from HTML comment marker blocks and from a specific heading+bullets pattern; returns a list of rule dicts and a diagnostics dict."
```

#### Implementation Workstreams (checkbox-driven) — extract_standards_rules.py

- [x] A. Discovery — confirm export surface and consumers
- [x] B. Plan — confirm library-only vs wrapper adoption needs
- [x] C. Implement — N/A (library-only; no HOP alignment needed)
- [x] D. Evidence — N/A (tests exist: `test_extract_standards_rules.py`)
- [x] E. Promote — N/A (never orchestrated; used by `generate_standards_index.py`)
- [x] DONE — Classification confirmed: library module, no Phase 4 processing required (2026-01-25)

##### ASR-007: check_inventory_health.py

```yaml
record_id: "ASR-007"
script:
  path: ".repo_studios/scripts/producers/check_inventory_health.py"
  name: "check_inventory_health.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_check_inventory_health.yaml"
  meets_template: "yes"
  last_updated: "2026-01-28"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--summary"
    - "--baseline"
    - "--thresholds"
    - "--output-dir"
    - "--artifacts-to-keep"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "Inventory summary JSON (file or directory). Default: .repo_studios/reports/producer_reports/healthview/inventory_overview"
    - "Baseline JSON. Default: .repo_studios/config/inventory/inventory_summary_baseline.json"
    - "Threshold configuration JSON. Default: config/ci_inventory_thresholds.json"
    - "Output root directory. Default: .repo_studios/command_center/reports"
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/inventory_health/<YYYYMMDD-HHMM>/"
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
    status: "✅ Base package aligned (2026-01-25); output root intentionally under command_center/"
retention:
  surfaces:
    - "--artifacts-to-keep (default from get_keep('check_inventory_health'))"
  mechanism: "prune_run_directories(output_dir / viewer_slug / topic_slug, keep=N, current_run=run_dir)"
  targets:
    - ".repo_studios/command_center/reports/healthview/inventory_health/<YYYYMMDD-HHMM>/"
  guardrails:
    - "Exit code 2 when summary input missing"
    - "Exit code 1 when threshold breach detected"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "Writes manifest/summary/telemetry via database integration storage"
    - "Prunes run history under output_dir/healthview/inventory_health"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/check_inventory_health.py#L1-L15 (docstring)"
    - ".repo_studios/scripts/producers/check_inventory_health.py#L497-L609 (run(argv) entry)"
  tests:
    - ".repo_studios/tests/tests_producers/test_check_inventory_health.py::test_run_returns_payload_dict (PASSED)"
    - ".repo_studios/tests/tests_producers/test_check_inventory_health.py::test_reports_written_without_issues (PASSED)"
    - ".repo_studios/tests/tests_producers/test_check_inventory_health.py::test_threshold_breach_and_pruning (PASSED)"
  fixtures: []
  tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_check_inventory_health.yaml"
  phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/ASR-007_check_inventory_health_build.md"
orchestrator_integration:
  orchestrator_ready: true
  db_integration_ready: true
  phase_4_status: complete
  promoted_to_orchestrator: true
  promotion_date: "2026-01-25"
  target_orchestrator: "run_available_scripts_oversight.py"
notes:
  - "Classification: HOP-compliant producer for inventory health validation."
  - "Contract status: ✅ emits base package; run(argv) entry added 2026-01-25"
  - "Entry surface: run(argv) returns Tier A payload with 8 keys"
  - "Output topic slug: inventory_health; run timestamps use minute granularity (YYYYMMDD-HHMM)"
  - "Phase 4 processing: Completed 2026-01-25; Tier-3 YAML created 2026-01-28"
```

#### Implementation Workstreams (checkbox-driven) — check_inventory_health.py

- [x] A. Discovery — confirm scope and intended consumer(s)
- [x] B. Plan — decided: add run(argv) wrapper only (base package already correct)
- [x] C. Implement — run(argv) entry point added returning payload dict
- [x] D. Evidence — tests passing (4/4), including new test_run_returns_payload_dict
- [ ] E. Promote — move to destination stage when CI orchestrator is implemented
- [x] DONE — record updated, Phase 4 processing complete (2026-01-25)

##### ASR-008: validate_inventory.py

```yaml
record_id: "ASR-008"
script:
  path: ".repo_studios/scripts/producers/validate_inventory.py"
  name: "validate_inventory.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_validate_inventory.yaml"
  meets_template: "yes"
  last_updated: "2026-01-28"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_validate_inventory.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/ASR-008_validate_inventory_build.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--schema-root"
    - "--enums-path"
    - "--template-path"
    - "--config-path"
    - "--output-dir"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--json"
    - "--log-level"
io_contract:
  inputs:
    - "Inventory schema directory (YAML files). Default: .repo_studios/inventory_schema"
    - "Enums YAML. Default: .repo_studios/inventory_schema/enums.yaml"
    - "Validator config YAML (optional). Default: .repo_studios/inventory_schema/validator_config.yaml"
  outputs:
    current:
      root: ".repo_studios/reports/healthview/producer/validate_inventory/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
        - "raw.json (supplementary)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
    status: "✅ Base package aligned (2026-01-25)"
retention:
  surfaces:
    - "--artifacts-to-keep (default present)"
    - "Run directory format: YYYYMMDD-HHMM (HOP timestamp-only naming)"
  mechanism: "prune_history(output_dir, keep=N, current_run=run_dir)"
  targets:
    - ".repo_studios/reports/healthview/producer/validate_inventory/"
  guardrails:
    - "Exit code 1 when errors are present"
    - "No latest_* pointers (HOP-compliant)"
  evidence:
    - "Writes HOP base package artifacts; prunes older run directories"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: false
  marker_string: null
  notes:
    - "Script uses direct file writes (not create_storage())"
    - "DB_INTEGRATION_MARKER tags not present — would need retrofit for dual-write"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_available_scripts_oversight.py"
  supports_output_dir: false
  supports_artifacts_to_keep: true
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/validate_inventory.py#L1-L28 (HOP docstring)"
    - ".repo_studios/scripts/producers/validate_inventory.py#L47-L50 (artifact constants)"
    - ".repo_studios/scripts/producers/validate_inventory.py#L509-L549 (write_run_artifacts)"
    - ".repo_studios/scripts/producers/validate_inventory.py#L880-L970 (run(argv) wrapper)"
  tests:
    - ".repo_studios/tests/tests_producers/test_validate_inventory.py::test_validate_inventory_success_and_pruning (PASSED)"
    - ".repo_studios/tests/tests_producers/test_validate_inventory.py::test_run_returns_payload_dict (PASSED)"
  fixtures: []
notes:
  - "Classification: HOP-compliant producer, orchestrator integration complete."
  - "Contract status: ✅ aligned with HOP base package (manifest.json, summary.md, telemetry.json)"
  - "Entry surface: run(argv) returns payload dict with 7 keys."
  - "DB integration: NOT using create_storage() — needs marker retrofit for dual-write."
  - "Phase 4 processing: Code complete 2026-01-25; Doc complete 2026-01-28."
```

#### Implementation Workstreams (checkbox-driven) — validate_inventory.py

- [x] A. Discovery — confirm scope and artifact structure
- [x] B. Plan — artifact renaming to HOP base package, add run(argv)
- [x] C. Implement — docstring update, artifact names changed, run(argv) added
- [x] D. Evidence — tests passing (2/2)
- [x] E. Promote — Tier-3 YAML created, build doc formalized, roster updated
- [x] DONE — Phase 4 compliance complete (2026-01-28)

##### ASR-010: render_inventory_views.py

```yaml
record_id: "ASR-010"
script:
  path: ".repo_studios/scripts/producers/render_inventory_views.py"
  name: "render_inventory_views.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_render_inventory_views.yaml"
  meets_template: "yes"
  last_updated: "2026-01-28"
tier3_yaml: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier3_scripts/available_scripts_oversight/tier3_render_inventory_views.yaml"
phase4_build_doc: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/tier2_roster/working_docs/ASR-010_render_inventory_views_build.md"
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--schema-root"
    - "--views-dir"
    - "--reports-root"
    - "--output-dir"
    - "--timestamp"
    - "--log-level"
io_contract:
  inputs:
    - "Inventory schema YAML files under schema_root (excluding enums.yaml and inventory_entry_template.yaml; and excluding anything under views_dir)."
    - "Legacy views directory (views_dir) used for writing redirect stub files."
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
        - "(legacy stubs) .repo_studios/inventory_schema/views/docs_overview.yaml"
        - "(legacy stubs) .repo_studios/inventory_schema/views/scripts_overview.yaml"
        - "(legacy stubs) .repo_studios/inventory_schema/views/tests_overview.yaml"
        - "(legacy stubs) .repo_studios/inventory_schema/views/summary.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "Hard-coded keep value present (value not captured here) for topic directory"
  mechanism: "prune_run_directories(output_dir / healthview / inventory_overview, keep=<default>)"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/"
  guardrails:
    - "Warns and normalizes legacy --output-dir when it ends with 'render_inventory_views' (uses parent directory)"
  evidence:
    - "Docstring declares canonical bundle under reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/"
    - "Writes legacy redirect stubs under views_dir pointing at the topic directory"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
  markers_present:
    - "L539 — manifest.json write"
    - "L541 — summary.md write"
    - "L543 — telemetry.json write"
orchestrator_integration:
  orchestrator_ready: true
  promoted_to_orchestrator: true
  target_orchestrator: "run_available_scripts_oversight.py"
  supports_output_dir: false
  supports_artifacts_to_keep: false
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/render_inventory_views.py#L30-L33 (VIEWER_SLUG, TOPIC_SLUG)"
    - ".repo_studios/scripts/producers/render_inventory_views.py#L538-L544 (create_storage + DB markers)"
    - ".repo_studios/scripts/producers/render_inventory_views.py#L450-L571 (run(argv) entry)"
  tests:
    - ".repo_studios/tests/tests_producers/test_render_inventory_views.py::test_render_inventory_views_structured_output (PASSED)"
    - ".repo_studios/tests/tests_producers/test_render_inventory_views.py::test_run_returns_payload_dict (PASSED)"
  fixtures: []
notes:
  - "Classification: HOP-compliant producer, orchestrator integration complete."
  - "Contract status: ✅ emits base package via create_storage() (manifest.json/summary.md/telemetry.json)"
  - "Entry surface: run(argv) returns payload dict with 7 keys."
  - "DB integration: Uses create_storage() with DB_INTEGRATION_MARKER tags at L539, L541, L543."
  - "Special: Only Stage 11.1 script using create_storage(); hard-coded keep=1 retention."
  - "Phase 4 processing: Code complete 2026-01-26; Doc complete 2026-01-28."
```

#### Implementation Workstreams (checkbox-driven) — render_inventory_views.py

- [x] A. Discovery — confirmed HOP-compliant base package, commandview scope
- [x] B. Plan — add run(argv) wrapper for orchestrator integration
- [x] C. Implement — run(argv) entry point added (2026-01-26)
- [x] D. Evidence — tests passing 2/2
- [x] E. Tier-3 YAML — created tier3_render_inventory_views.yaml (Stage 11.1 location)
- [x] F. Orchestrator integration — in run_available_scripts_oversight.py
- [x] DONE — Phase 4 compliance complete (2026-01-28)

##### ASR-011: generate_lizard_report.py

```yaml
record_id: "ASR-011"
script:
  path: ".repo_studios/scripts/producers/generate_lizard_report.py"
  name: "generate_lizard_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: true
  exists: true
  name: "tier3_generate_lizard_report.yaml"
  meets_template: "full"
  last_updated: "2026-01-27"
cli_surfaces:
  run_entrypoint: "run(argv) -> dict"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--output-base"
    - "--timestamp"
    - "--max-ccn"
    - "--max-length"
    - "--targets"
    - "--extra-args"
    - "--artifacts-to-keep"
    - "--log-level"
io_contract:
  inputs:
    - "Executes `python -m lizard` and parses JSON stdout."
    - "Environment defaults: LIZARD_MAX_CCN, LIZARD_MAX_LENGTH, LIZARD_TARGETS."
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/healthview/lizard_report/<YYYYMMDD-HHMM>/"
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
    - "--artifacts-to-keep (default present; value not captured here)"
  mechanism: "prune_run_directories(output_dir / healthview / lizard_report, keep=N, current_run=bundle_dir)"
  targets:
    - ".repo_studios/reports/producer_reports/healthview/lizard_report/<YYYYMMDD-HHMM>/"
  guardrails:
    - "Rejects command arguments containing newline characters"
    - "Skips target directories outside repo_root"
    - "Tolerant: per-module docstring claims it always exits 0; failures are encoded in telemetry payload"
  evidence:
    - "Uses database integration storage to write manifest/summary/telemetry for each run"
    - "Telemetry includes a truncated copy of raw stdout/stderr and an optional JSON summary"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/generate_lizard_report.py"
  tests:
    - ".repo_studios/tests/tests_producers/test_generate_lizard_report.py"
  fixtures: []
notes:
  - "Classification: HOP-compliant producer — promoted to orchestrator (2026-01-28)."
  - "Contract status: ✅ emits base package (manifest.json/summary.md/telemetry.json)"
  - "Entry surface: run(argv) -> dict; returns Tier A payload with 8 keys."
  - "Output topic slug: lizard_complexity; run timestamps use minute granularity (YYYYMMDD-HHMM)."
  - "Tests: 3/3 passing (test_structured_artifacts_success, test_no_targets_and_pruning, test_rejects_newline_arguments)"
  - "Build doc: tier2_roster/working_docs/ASR-011_generate_lizard_report_build.md"
  - "Tier-3 YAML: .repo_studios/scripts/producers/tier3_generate_lizard_report.yaml"
orchestrator_integration:
  orchestrator_ready: true
  db_integration_ready: true
  phase_4_status: complete
  promoted_to_orchestrator: true
  promotion_date: "2026-01-28"
  target_orchestrator: "run_available_scripts_oversight.py"
```

#### Implementation Workstreams (checkbox-driven) — generate_lizard_report.py

- [x] A. Discovery — confirmed HOP-compliant base package, experimental/hold classification
- [x] B. Plan — hold classification retained; script already emits correct artifacts
- [x] C. Implement — run(argv) entry point added; Tier-3 YAML created (2026-01-27)
- [x] D. Evidence — tests passing 3/3; mypy 0 errors
- [x] E. Promote — wired to run_available_scripts_oversight.py (2026-01-28)
- [x] DONE — Phase 4 build + promotion complete (2026-01-28)

##### ASR-013: test_log_analysis.py

```yaml
record_id: "ASR-013"
script:
  path: ".repo_studios/command_center/scripts/libraries/test_log_analysis.py"
  name: "test_log_analysis.py"
  category: "utility"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_test_log_analysis.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "other"
  key_flags: []
io_contract:
  inputs:
    - "logs_dir: directory containing pytest run artifacts (pytest text output + JUnit XML)"
    - "Optional overrides: junit_path, full_log_path"
    - "Optional metadata: generated datetime"
  outputs:
    current:
      root: "Not applicable (library; returns in-memory payload)"
      artifacts:
        - "report (dict)"
        - "markdown (string)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "None (library does not prune; it selects candidate artifacts inside logs_dir)"
  mechanism: "Selection-only (choose JUnit + pytest log candidates; no deletion)"
  targets:
    - "Not applicable (library; no retained bundles)"
  guardrails:
    - "Skips internal-only JUnit artifacts (pytest internal test-only bundles)"
  evidence:
    - "Parses JUnit XML via defusedxml when available; falls back to xml.etree"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/command_center/scripts/libraries/test_log_analysis.py"
    - ".repo_studios/command_center/scripts/libraries/__init__.py"
    - ".repo_studios/scripts/producers/collect_test_log_reports.py"
    - ".repo_studios/scripts/consumers/generate_test_log_health_report.py"
  tests:
    - ".repo_studios/tests/tests_utilities/test_test_log_analysis.py"
  fixtures: []
notes:
  - "Classification: utility/library (never orchestrated)."
  - "Contract gaps: library does not emit the base package (manifest.json/summary.md/telemetry.json) under the canonical HealthView root; callers are responsible for bundle emission and must uphold the pointer-ban when promoted."
  - "Export surface (__all__): TestHealth, TestLogAnalysisResult, select_junit_artifact, select_full_log, build_test_log_report, render_markdown."
  - "Primary behavior: parse JUnit totals; count warnings + tracebacks from pytest text log; parse 'slowest N durations' entries."
  - "This module does not write artifacts; callers persist bundles (e.g., collect_test_log_reports.py, generate_test_log_health_report.py)."
```

#### Implementation Workstreams (checkbox-driven) — test_log_analysis.py

- [x] A. Discovery — confirmed library module with `__all__` exports
- [x] B. Plan — library-only, no HOP alignment needed
- [x] C. Implement — N/A (library module)
- [x] D. Evidence — tests passing 2/2 (test_build_test_log_report_parses_artifacts, test_select_junit_artifact_skips_internal_only)
- [x] E. Promote — N/A (never orchestrated; used by collect_test_log_reports.py, generate_test_log_health_report.py)
- [x] DONE — classified as library module, no Phase 4 processing required (2026-01-26)

### 3.2 Stop-Gates and Implementation Checklists

Stop-gates are the stage-level truth gates that must be closed before a script is promoted into an
 orchestrator.

Tier-3 YAMLs are promotion artifacts: they should only be created after the destination stage’s
Tier-2 stop-gates are satisfied and the record set is stable enough to extract reusable
horizontals.

**Tier-2 authoring stop-gates (docs-first):**

- Ensure this roster is linked from Tier-1 Stage 11.1.
- Ensure Records index and Pruning index are present.
- Ensure each record includes Tier-3 metadata fields.
- Ensure unknowns are treated as promotion stop-gates (not silently assumed).

**Promotion stop-gates (code-phase, per script):**

- The destination orchestrator exists and executes the promoted script deterministically.
- If the promoted script emits HealthView bundles:
  - Output root is migrated to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
  - Base package is enforced: `manifest.json`, `summary.md`, `telemetry.json`.
  - No pointer files are introduced.
  - Pruning mechanisms and targets are explicit and evidenced.
  - If DB writes are present: gate behind `REPO_STUDIOS_DB_ENABLED`, warn-only failures, and include
    `DB_INTEGRATION_MARKER:` at each callsite.
- Tier-1 is updated to move the script out of Stage 11.1 and into the adopted orchestrator section.

---

## 4. Signals & Telemetry

**Regression suites (current evidence):**

- None captured yet for Stage 11.1 (holding roster). Per-script suites should be recorded in the
  relevant ASR record as inspection proceeds.

**Telemetry outputs:**

- Stage 11.1 does not emit `telemetry.json` (it is not an orchestrated stage). Telemetry is a
  requirement for promoted bundle-emitting scripts.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 stop-gates blocked by this doc:**
  - Tier-1 can only treat Stage 11.1 as “holding roster present” when this Tier-2 roster exists and
    is linked.

- **Feature flags:**
  - `REPO_STUDIOS_DB_ENABLED` (DB dual-write toggle)

---

## 6. Instruction Block (Required by Repo Markdown Rules)

1. Editors follow `.github/instructions/markdown.instructions.md`.
1. Keep this document’s section order intact.
1. Keep “Target contract (locked decisions)” and “Current evidence (repo-observed)” explicit;
   mismatch is treated as a stop-gate.

---

## 7. Agent Automation Block

<!-- agents:begin:healthview_stage11_available_scripts_roster -->
```yaml
audience: [Copilot, Repo_Studios]
intent: stage_11_1_available_scripts_roster
rules:
  - require_front_matter: true
  - require_single_h1: true
  - require_update_log: true
  - require_records_index: true
  - require_pruning_index: true
  - require_script_record_schema: true
  - require_tier3_metadata_fields: true
checks:
  - id: hv-stage11-contract
    title: Capture holding vs promotion contract snapshot
    severity: error
  - id: hv-stage11-records
    title: Records index + per-script records present
    severity: error
  - id: hv-stage11-stopgates
    title: Stop-gates include promotion gates (output root/base package/pointers/retention/DB marker)
    severity: error
```
<!-- agents:end:healthview_stage11_available_scripts_roster -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-20 | Seeded Stage 11.1 Tier-2 roster from the HealthView Tier-2 roster template; initial records created with inspection pending. | repo_studios_ai | Not run (doc-only seed) | None |
| 2025-12-21 | Stage 11.1 Discovery Pass B — Classification: labeled each ASR record as candidate/utility/commandview-only/legacy/experimental based on current repo evidence; no Tier-1 edits. | repo_studios_ai | Not run (doc-only) | None |
| 2025-12-21 | Stage 11.1 Discovery Pass C — Promotion Mapping (hypothetical): proposed candidate stage mappings + minimal wrapper needs + known contract deltas for ASR-001/003/005; no Tier-1 edits; no Tier-3 YAMLs. | repo_studios_ai | Not run (doc-only) | None |
| 2025-12-21 | Stage 11.1 Contract Gap Notes: documented base-contract contradictions/gaps (canonical root + base package + pointer-ban applicability) across ASR records to support later checkbox-driven remediation. | repo_studios_ai | Not run (doc-only) | None |
