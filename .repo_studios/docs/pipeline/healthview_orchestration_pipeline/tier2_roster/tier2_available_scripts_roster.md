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
- Summarizer: `.repo_studios/scripts/summarizers/summarize_health_suite.py` (legacy/deprecation candidate)
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
- ASR-009 — `summarize_health_suite.py` — summarizer — [ASR-009](#asr-009-summarize_health_suitepy)
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
  allowed: false
  exists: false
  name: "tier3_generate_anchor_health_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv) -> run(argv)" 
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
      root: ".repo_studios/reports/consumer_reports/anchor_health_reports/anchor_health-YYYY-MM-DD_HHMM/"
      artifacts:
        - "summary.json"
        - "SUMMARY.md"
        - "bundle_summary.json"
        - "anchor_report.json"
        - "anchor_report.md"
        - "clusters.tsv"
        - "runs.log (in output base dir)"
        - "latest_summary.json (in output base dir)"
        - "latest_SUMMARY.md (in output base dir)"
        - "latest_bundle_summary.json (in output base dir)"
        - "anchor_report_latest.json (in output base dir)"
        - "anchor_report_latest.md (in output base dir)"
        - "clusters_latest.tsv (in output base dir)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep (default present; value not captured here)"
    - "Run directory stem prefix: anchor_health-YYYY-MM-DD_HHMM"
    - "Also maintains hardlinked/copied latest_* pointer files in output base dir"
  mechanism: "prune_run_directories(keep=N, stem_prefix=anchor_health-, current_run=<run_dir>)"
  targets:
    - ".repo_studios/reports/consumer_reports/anchor_health_reports/"
  guardrails:
    - "Keeps current run; prunes older run directories beyond keep"
  evidence:
    - "Artifacts are written into a timestamped run directory; a bundle_summary.json points at resolved artifact paths"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L1-L41"
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L105-L167"
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L301-L405"
    - ".repo_studios/scripts/consumers/generate_anchor_health_report.py#L407-L520"
  tests: []
  fixtures: []
notes:
  - "Classification: candidate for future orchestration."
  - "Contract gaps: output root is under consumer_reports (not the canonical HealthView root); emits pointer artifacts (latest_* / *_latest.*) and does not emit the base package as a single manifest.json/summary.md/telemetry.json bundle."
  - "Entry surface: CLI and importable (run(argv))."
  - "Primary purpose: generates an H1/H2 markdown anchor duplication summary, preferring existing anchor inventory artifacts when available and falling back to scanning docs/*.md; emits JSON + markdown artifacts for dashboarding/human review."
```

##### Promotion Mapping (hypothetical) — generate_anchor_health_report.py

- Proposed future orchestration (anchor/markdown integrity consumer vertical)
- Minimal orchestrator wrapper required: a orchestrator that invokes `run(argv)` (or the script’s
    main) and emits a single HealthView bundle (manifest/summary/telemetry) under the stage’s
    canonical output root
- Known contract deltas vs target stage:
  - Current output root is under `consumer_reports/anchor_health_reports/...` rather than the
    canonical HealthView root
  - Current artifacts include multiple pointer-style files (`latest_*` and `*_latest.*`) which
    violate the pointer-ban expected in promoted HealthView stages
  - Artifact set is richer than the base package; promotion would need a clear mapping into
    `manifest.json`, `summary.md`, and `telemetry.json` (with extra artifacts either excluded or
    treated as additional catalog entries under a non-pointer naming scheme)

#### Implementation Workstreams (checkbox-driven) — generate_anchor_health_report.py

- [ ] A. Discovery — confirm CLI surfaces, outputs, retention, and consumers
- [ ] B. Plan — define wrapper + mapping into base package; enumerate stop-gates
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

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

- [ ] A. Discovery — confirm runtime side effects and expected callsites
- [ ] B. Plan — decide import-only helper vs explicit stage step
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture callsites/tests and representative outputs (or mark N/A)
- [ ] E. Promote — wire into a destination stage (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

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

- [ ] A. Discovery — confirm outputs, retention, and expected consumers
- [ ] B. Plan — define wrapper + mapping into base package; enumerate stop-gates
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

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

- [ ] A. Discovery — confirm export surface, consumers, and payload schema
- [ ] B. Plan — confirm library-only vs wrapper adoption needs
- [ ] C. Implement — N/A (library-only)
- [ ] D. Evidence — capture tests and representative payload examples (or mark N/A)
- [ ] E. Promote — N/A (never orchestrated)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

##### ASR-005: validate_import_boundaries.py

```yaml
record_id: "ASR-005"
script:
  path: ".repo_studios/scripts/producers/validate_import_boundaries.py"
  name: "validate_import_boundaries.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_validate_import_boundaries.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv) -> run(argv)" 
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
      root: ".repo_studios/reports/producer_reports/import_boundary_reports/<run_id>/"
      artifacts:
        - "report.json"
        - "report.md"
        - "log.txt"
        - "violations.json"
        - "latest/latest_report.json"
        - "latest/latest_report.md"
        - "latest/latest_log.txt"
        - "latest/latest_violations.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep (default present; value not captured here)"
    - "Run directory stem prefix: import_boundary_check-YYYYMMDD_HHMMSS"
  mechanism: "prune_run_directories(keep=N, stem_prefix=import_boundary_check, current_run=<run_dir>)"
  targets:
    - ".repo_studios/reports/producer_reports/import_boundary_reports/"
  guardrails:
    - "Keeps current run; prunes historical run directories beyond keep"
  evidence:
    - "Script writes structured artifacts under run_id and mirrors select files into output_dir/latest"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L1-L40"
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L56-L124"
    - ".repo_studios/scripts/producers/validate_import_boundaries.py#L420-L534"
  tests: []
  fixtures: []
notes:
  - "Classification: candidate for future orchestration."
  - "Contract gaps: output root is producer_reports/import_boundary_reports (not the canonical HealthView root); emits pointer artifacts (latest/ subtree) and does not emit the base package as manifest.json/summary.md/telemetry.json."
  - "Entry surface: CLI (exits non-zero when violations exist); also importable (run(argv))."
  - "Primary purpose: reads a module-level import graph (when available) + performs a repo walk to detect forbidden static import patterns; applies a JSON allowlist to filter accepted exceptions; emits structured reports."
```

##### Promotion Mapping (hypothetical) — validate_import_boundaries.py

- Proposed future stage: **4.2** (import boundary / architectural integrity producer vertical)
- Minimal orchestrator wrapper required: a orchestrator that invokes
  `run(argv)` and then emits a single HealthView bundle
  (manifest/summary/telemetry) under the stage's canonical output root;
  wrapper should surface `--strict` and thread through `--artifacts-to-keep`
- Known contract deltas vs target stage:
  - Current output root is `producer_reports/import_boundary_reports/<run_id>/`
    rather than canonical HealthView root
  - Current outputs include a `latest/` mirror subtree, which violates
    the pointer-ban expected in promoted HealthView stages
  - Current artifacts are report-oriented (`report.json`, `violations.json`,
    logs); promotion would need a consistent mapping into base-package
    artifacts and clarify how the detailed report payload is represented
    (telemetry vs additional catalog artifacts)

#### Implementation Workstreams (checkbox-driven) — validate_import_boundaries.py

- [ ] A. Discovery — confirm inputs/outputs, retention, and failure modes
- [ ] B. Plan — define wrapper + mapping into base package; enumerate stop-gates
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

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

- [ ] A. Discovery — confirm export surface and consumers
- [ ] B. Plan — confirm library-only vs wrapper adoption needs
- [ ] C. Implement — N/A (library-only)
- [ ] D. Evidence — capture tests and representative payload examples (or mark N/A)
- [ ] E. Promote — N/A (never orchestrated)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

##### ASR-007: check_inventory_health.py

```yaml
record_id: "ASR-007"
script:
  path: ".repo_studios/scripts/producers/check_inventory_health.py"
  name: "check_inventory_health.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_check_inventory_health.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
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
retention:
  surfaces:
    - "--artifacts-to-keep (default present; value not captured here)"
  mechanism: "prune_run_directories(output_dir / viewer_slug / topic_slug, keep=N, current_run=run_dir)"
  targets:
    - ".repo_studios/command_center/reports/healthview/inventory_health/<YYYYMMDD-HHMM>/"
  guardrails:
    - "Exit code 2 when summary input missing"
    - "Exit code 1 when threshold breach detected"
  evidence:
    - "Docstring declares the artifact bundle and exit codes"
    - "Writes manifest/summary/telemetry via database integration storage"
    - "Prunes run history under output_dir/healthview/inventory_health"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/check_inventory_health.py"
  tests: []
  fixtures: []
notes:
  - "Classification: experimental/hold (outputs use viewer_slug=healthview but default output root is under command_center reports; unclear whether this belongs in HealthView HOP vs Command Center-only CI checks)."
  - "Contract gaps: emits the base package (manifest.json/summary.md/telemetry.json) but output root is under command_center/reports/healthview (not the canonical HealthView root)."
  - "Entry surface: CLI-only (main(argv)); no run(argv) helper observed."
  - "Summary input may be a directory: if so, the script selects the newest timestamped run directory and reads telemetry.json to obtain summary data."
  - "Output uses viewer_slug=healthview and topic_slug=inventory_health; run directories use a minute-granularity slug (YYYYMMDD-HHMM)."
```

#### Implementation Workstreams (checkbox-driven) — check_inventory_health.py

- [ ] A. Discovery — confirm scope and intended consumer(s)
- [ ] B. Plan — decide hold vs remove vs adopt into a destination stage
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

##### ASR-008: validate_inventory.py

```yaml
record_id: "ASR-008"
script:
  path: ".repo_studios/scripts/producers/validate_inventory.py"
  name: "validate_inventory.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_validate_inventory.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
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
    - "Output directory for artifacts. Default: .repo_studios/reports/producer_reports/validate_inventory"
  outputs:
    current:
      root: ".repo_studios/reports/producer_reports/validate_inventory/validate_inventory-<YYYYMMDD_HHMMSS>/"
      artifacts:
        - "report.json"
        - "report.md"
        - "log.txt"
        - "raw.json"
        - "latest_report.json"
        - "latest_report.md"
        - "latest_report.log"
        - "latest_raw.json"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep (default present; value not captured here)"
  mechanism: "prune_run_directories(output_dir, keep=N, stem_prefix=validate_inventory, current_run=run_dir)"
  targets:
    - ".repo_studios/reports/producer_reports/validate_inventory/validate_inventory-<YYYYMMDD_HHMMSS>/"
  guardrails:
    - "Exit code 1 when errors are present"
    - "Optional legacy stdout mode: --json emits issues JSON to stdout"
  evidence:
    - "Writes run-scoped report artifacts plus copies 'latest_*' siblings"
    - "Prunes historical validate_inventory-* run directories"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/validate_inventory.py"
  tests: []
  fixtures: []
notes:
  - "Classification: commandview-only."
  - "Contract gaps: output root is producer_reports/validate_inventory (not the canonical HealthView root); emits pointer artifacts (latest_* siblings) and does not emit the base package as manifest.json/summary.md/telemetry.json."
  - "Entry surface: CLI-only (main(argv)); no run(argv) helper observed."
  - "Iterates *.yaml under schema_root (excluding enums/template/config files and skipping any path containing a 'views' directory segment)."
  - "Validation includes required fields, list-typed fields, enum membership, dependency schema checks, and optional path existence checks (config-controlled)."
```

#### Implementation Workstreams (checkbox-driven) — validate_inventory.py

- [ ] A. Discovery — confirm scope and intended consumer(s)
- [ ] B. Plan — decide hold vs remove vs adopt into a destination stage
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

##### ASR-009: summarize_health_suite.py

```yaml
record_id: "ASR-009"
script:
  path: ".repo_studios/scripts/summarizers/summarize_health_suite.py"
  name: "summarize_health_suite.py"
  category: "summarizer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_summarize_health_suite.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "run(argv)"
  key_flags:
    - "--repo-root"
    - "--output-dir"
    - "--legacy-dir"
    - "--timestamp"
    - "--artifacts-to-keep"
    - "--log-level"
    - "--skip-legacy-mirror"
io_contract:
  inputs:
    - "Reads multiple upstream Health Suite artifacts from fixed locations under .repo_studios/ (selected by preferred timestamp dir or latest dir)."
    - "Uses anchor health latest dataset: .repo_studios/anchor_health/anchor_report_latest.json (if present)."
  outputs:
    current:
      root: ".repo_studios/command_center/reports/healthview/health_suite_overview/<YYYYMMDD-HHMM>/"
      artifacts:
        - "health_suite_summary.json"
        - "health_suite_summary.md"
        - "(optional) .repo_studios/health_suite/health_suite_summary_<YYYY-MM-DD_HHMM>.md (legacy mirror)"
        - "(optional) .repo_studios/health_suite/MOVED.txt (legacy marker)"
    target:
      root: ".repo_studios/reports/healthview/<class>/<topic>/<timestamp>/"
      artifacts:
        - "manifest.json"
        - "summary.md"
        - "telemetry.json"
retention:
  surfaces:
    - "--artifacts-to-keep (default present; value not captured here)"
    - "--skip-legacy-mirror (disables legacy markdown copy)"
  mechanism: "write_report_artifacts(..., keep=N, viewer=healthview, topic=health_suite_overview)"
  targets:
    - ".repo_studios/command_center/reports/healthview/health_suite_overview/<YYYYMMDD-HHMM>/"
  guardrails:
    - "None observed (missing upstream datasets become '(missing)' sections and add notes)"
  evidence:
    - "Docstring describes intended summary composition; implementation reads multiple report roots and composes a markdown plus JSON payload"
    - "Uses write_report_artifacts to emit run-scoped artifacts under output_dir/viewer/topic"
db_integration:
  gated_by: "REPO_STUDIOS_DB_ENABLED"
  marker_required: true
  marker_string: "DB_INTEGRATION_MARKER:"
evidence:
  code_refs:
    - ".repo_studios/scripts/summarizers/summarize_health_suite.py"
  tests:
    - ".repo_studios/tests/tests_summarizers/test_summarize_health_suite.py"
  fixtures: []
notes:
  - "Classification: legacy/deprecate."
  - "Contract gaps: does not emit the base package (manifest.json/summary.md/telemetry.json); emits health_suite_summary.* and optional legacy mirror artifacts."
  - "Entry surfaces: import-safe helper run(argv) plus CLI main(argv) that exits non-zero only when run() does not return status='ok'."
  - "Timestamp selection prefers a same-run timestamped directory when present, else falls back to the latest directory for each upstream dataset." 
```

#### Implementation Workstreams (checkbox-driven) — summarize_health_suite.py

- [ ] A. Discovery — confirm scope and overlap with other suites
- [ ] B. Plan — decide deprecate vs migrate into a destination stage
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

##### ASR-010: render_inventory_views.py

```yaml
record_id: "ASR-010"
script:
  path: ".repo_studios/scripts/producers/render_inventory_views.py"
  name: "render_inventory_views.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_render_inventory_views.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
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
evidence:
  code_refs:
    - ".repo_studios/scripts/producers/render_inventory_views.py"
  tests:
    - ".repo_studios/tests/tests_producers/test_render_inventory_views.py"
  fixtures: []
notes:
  - "Classification: commandview-only."
  - "Contract gaps: emits the base package (manifest.json/summary.md/telemetry.json) but output root is producer_reports/healthview/inventory_overview (not the canonical HealthView root); also writes legacy redirect stubs under inventory_schema/views."
  - "Entry surface: CLI-only (main(argv)); no run(argv) helper observed."
  - "Outputs are written via database integration storage (create_storage) with DB_INTEGRATION_MARKER blocks for manifest/summary/telemetry." 
```

#### Implementation Workstreams (checkbox-driven) — render_inventory_views.py

- [ ] A. Discovery — confirm scope and intended consumer(s)
- [ ] B. Plan — decide hold vs remove vs adopt into a destination stage
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

##### ASR-011: generate_lizard_report.py

```yaml
record_id: "ASR-011"
script:
  path: ".repo_studios/scripts/producers/generate_lizard_report.py"
  name: "generate_lizard_report.py"
  category: "producer"
tier3:
  metadata_block_version: "v1"
  allowed: false
  exists: false
  name: "tier3_generate_lizard_report.yaml"
  meets_template: "NA"
  last_updated: null
cli_surfaces:
  run_entrypoint: "main(argv)"
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
  - "Classification: experimental/hold (currently emits a healthview-style bundle but intended consumer/scope is not established in the roster evidence)."
  - "Contract gaps: emits the base package (manifest.json/summary.md/telemetry.json) but output root is producer_reports/healthview/lizard_report (not the canonical HealthView root)."
  - "Entry surface: CLI-only (main(argv)); no run(argv) helper observed."
  - "Output topic slug: lizard_report; run timestamps use minute granularity (YYYYMMDD-HHMM)."
```

#### Implementation Workstreams (checkbox-driven) — generate_lizard_report.py

- [ ] A. Discovery — confirm scope and intended consumer(s)
- [ ] B. Plan — decide hold vs remove vs adopt into a destination stage
- [ ] C. Implement — execute approved plan (if adopted)
- [ ] D. Evidence — capture tests and representative bundle artifacts (or mark N/A)
- [ ] E. Promote — move reference out of Stage 11.1 in Tier-1 (when approved)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

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

- [ ] A. Discovery — confirm export surface and consumers
- [ ] B. Plan — confirm library-only vs wrapper adoption needs
- [ ] C. Implement — N/A (library-only)
- [ ] D. Evidence — capture tests and representative payload examples (or mark N/A)
- [ ] E. Promote — N/A (never orchestrated)
- [ ] DONE — record outcome, close stop-gates, and update Tier-1 Available Scripts section

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
