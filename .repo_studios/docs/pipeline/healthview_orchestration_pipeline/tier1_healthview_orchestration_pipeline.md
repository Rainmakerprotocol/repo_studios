---
title: HealthView Orchestration Pipeline
tier: tier-1
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - pipeline-spine
status: in-progress
version: 0.3.2
updated_at: 2026-01-04
tags:
  - pipeline
  - healthview
  - hop
  - orchestration
related_files:
  - REPORT_NAMING_STANDARDS.md
  - .repo_studios/command_center/scripts/libraries/cli.py
  - .repo_studios/command_center/scripts/orchestrators/
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
---

# HealthView Orchestration Pipeline

> **Purpose:** This document maps the HealthView measurement pipeline from BEGIN → END, describing
> how repository health is continuously monitored through staged orchestration of measurement
> scripts that track testing, documentation, dependencies, faults, technical debt, and process governance.

---

## 0. Instruction Block for Editors & AI Assistants

- This document is **Tier-1**: it describes **system-level behavior**, not code internals.
- All statements must be **backed by repo evidence** (code, tests, ADRs, design docs).
- Structure (H2s/H3s) should be preserved; add/remove major sections deliberately, then renumber
  **all** top-level headings (Stages, Snapshot, Contradiction Registry, etc.) so numbering stays contiguous.
- During Phase 0 seeding, create the blank **Update Log & Evidence Tracking** table before drafting
  stage content so evidence capture is ready from the first edit.
- Use the Working Notes section only as temporary scratch space; move resolved items into the Update
  Log once evidence (doc-index timestamp + regression suites) is recorded.
- When hardening, follow the **Pass A / Pass B / Pass C** evidence cycle per stage, as described in
  the how-to guide, and log each doc-index run/regression suite in
  **Section 17. Update Log & Evidence Tracking**.
- Before calling any Tier-1 edit complete, refresh the doc-index (via the `doc-index` make target or
  platform-equivalent command), execute the validating regression suites, and only then log the
  evidence in **Section 17. Update Log & Evidence Tracking**; that section is mandatory and should
  never be skipped.
- Editors must follow `.github/instructions/markdown.instructions.md` and `.github/instructions/pipeline_doc_tiers.instructions.md`.

**Pipeline-Specific Notes:**

- HealthView orchestrators measure **externally observable repository health signals**
  (test results, typecheck status, documentation coverage, fault reports, standards compliance).
- Each Stage NN class represents a **maturity domain** (Testing, Docs, Dependencies, etc.).
- Each Stage NN.N orchestrator can be run independently or via the meta-orchestrator.
- Gaps are tracked as "Planned Expansions" within appropriate stage classes.

---

## 0.1 Agent Execution Loop (Entry Point)

This section is the canonical entry point for the HealthView checkbox-driven execution loop.
It is intentionally outside the stage taxonomy and contains no checkboxes.

<!-- agents:begin:healthview_agent_entry_point -->
```yaml
entry_point:
  selector_command: "make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO"
  workflow_spec: ".repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml"
  validator_command: "make -C .repo_studios healthview-agent-validate-workflow LOG_LEVEL=INFO"
  refresh_queue_command: "make -C .repo_studios doc-index LOG_LEVEL=INFO"
expected_compact_output:
  - "tier1=<file_path>:<line_number>"
  - "tier2=<relative_link>#<anchor>"
approval_gates:
  require_user_approval_for:
    - begin_implementation
    - check_done
    - update_tier1
    - create_tier3_yaml
```
<!-- agents:end:healthview_agent_entry_point -->

Commands:

```powershell
make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO
```

Workflow spec:

- `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml`

Tool index (compact):

- **Make targets:**
  - `make -C .repo_studios healthview-agent-next-compact LOG_LEVEL=INFO`
  - `make -C .repo_studios healthview-agent-validate-workflow LOG_LEVEL=INFO`
  - `make -C .repo_studios doc-index LOG_LEVEL=INFO`
- **Workflow assets:**
  - Spec: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml`
  - Schema: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/schema/healthview_agent_execution_loop.schema.json`
  - Validator: `.repo_studios/scripts/utilities/validate_healthview_agent_workflow_spec.py`
  - Runner: `.repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py`
  - Tier-3 onboarding template: `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/tier3_agent_pipeline_template.yaml`

---

## 1. 5W1H – Purpose & Context

### 1.1 Who

**Primary stakeholders:**

- Development teams maintaining Repo Studios codebase
- AI agents (Copilot, coding assistants) querying repo health status
- DevOps/SRE teams monitoring CI/CD pipeline health

**Secondary stakeholders:**

- Code reviewers assessing PR quality impact
- Project managers tracking technical debt accumulation
- New contributors understanding codebase maturity

### 1.2 What

**High-level function:**  
HealthView orchestrates automated measurement of repository health across six maturity domains
(Testing, Documentation, Runtime Reliability, Dependency Management, Technical Debt, Process
Governance). Each orchestrator chains producer → consumer → aggregator scripts that collect metrics,
analyze trends, and publish timestamped reports.

**Inputs:**

- Repository source code (`.py`, `.md`, `.yaml` files)
- Test execution logs and coverage data
- Git history and churn metrics
- Dependency manifests and import graphs
- Configuration files and baselines

**Outputs:**

- **Current (repo evidence today):** timestamped HealthView bundles are published under
  `.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/`.
- **Target contract (HOP hardening):** the canonical HealthView output root becomes
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- **Target bundle invariant (HOP hardening):** HealthView bundles converge on the base package:
  `manifest.json`, `summary.md`, `telemetry.json`.
  - **Current evidence is stage-scoped:** during migration, individual stages may be missing base
    package artifacts and/or emit additional artifacts; see the relevant Tier-2 roster.
- **No mutable pointers (HOP target):** HealthView bundles must be discoverable by timestamped
  directories; mutable pointer aliases (`latest_*` / `current_*`) are disallowed by contract.
- **Retention (HOP target):** retention is enforced in code; see Tier-2 rosters for current
  evidence and pruning surfaces.
- **DB dual-write (HOP target):** when `REPO_STUDIOS_DB_ENABLED` is enabled, orchestrators may
  best-effort persist bundle metadata to a DB; failures must log at `WARNING` and must not block
  filesystem artifact writing.

### 1.3 Why

**Problem solved:**  
Without continuous health measurement, technical debt accumulates silently, documentation coverage
degrades invisibly, and runtime reliability issues surface only during incidents. HealthView
provides **proactive visibility** into repo health trends before they become critical.

**Design intent (target outcomes):**

- Orchestrator runs are intended to produce timestamped, reproducible artifacts
- Health signals are intended to remain comparable across execution cycles
- Trend data is intended to enable early intervention before metrics degrade critically
- Gaps between ideal and actual health are intended to be surfaced systematically

### 1.4 Where

**Architecture position:**  
HealthView sits in the **automation tier** of Repo Studios, operating as a standalone pipeline that
reads from the codebase and writes to the reports directory. It does not modify source code or block
CI/CD workflows.

**Upstream systems:**

- Git repository (source of truth for code, docs, history)
- Test runners (pytest, coverage tools)
- Static analysis tools (mypy, lizard, custom scanners)

**Downstream dependencies:**

- Dashboard UIs consuming health reports (future)
- Alerting systems monitoring metric thresholds (future)
- Developer CLIs querying latest health status (current: ad-hoc manual inspection)

### 1.5 When

**Invocation triggers:**

- **Manual:** Developer runs orchestrator via CLI or make target
- **CI/CD:** GitHub Actions workflow executes after main branch merge (future: automated)
- **Scheduled:** Nightly cron job refreshes baseline metrics (future: not yet implemented)
- **On-demand:** AI agent requests health snapshot during code review (future: integration pending)

**State transitions:**

- **Idle:** No orchestrator running, reports directory stable
- **Active:** Orchestrator executing, temporary artifacts being written
- **Complete:** All scripts finished, timestamped bundle published
- **Failed:** Script returned non-zero exit code, partial artifacts may exist

### 1.6 How

**BEGIN → END flow:**

1 Operator invokes orchestrator (via CLI, make target, or meta-orchestrator)
2 Orchestrator validates environment (repo root, Python interpreter, dependencies)
3 Scripts execute sequentially in producer → consumer → aggregator pipeline
4 Each script writes intermediate artifacts (JSON, markdown) to topic-specific directory
5 Final aggregator/summarizer produces bundle (manifest + summary + telemetry)
6 Orchestrator prunes stale artifacts, keeping only N most recent timestamped bundles
  (retention is enforced in code; see Tier-2 for current evidence)
7 Exit code signals success/failure; logs capture execution telemetry

**Stage organization:**  
Six maturity domain classes (Stage 1–6), each containing one or more orchestrators.
Meta-orchestrator chains all Stage NN.1 orchestrators for full-suite diagnostics.

---

## 2. Document Metadata

- **Version:** `v0.3.1`  
- **Last Updated:** `2025-12-18`  
- **Owner / Steward:** `Repo Studios Core Team`  
- **Overall Status:** `In Progress – Phase 2 Pass B complete (all 7 stages code-verified),
  awaiting Pass C polish`

**Hardening Progress:**

- **Phase 0 (Seeding):** Complete – BEGIN → END skeleton with all stages
- **Phase 1 (Structure & Global Concepts):** Complete – Spine, Envelope, Global Controls, Stage Matrix
- **Phase 2 (Stage-by-Stage Hardening):** Pass B complete (100%)
  - Stage 1 (Test Execution Telemetry): Pass B complete, Pass C pending
  - Stage 2 (Docs Health Overview): Pass B complete, Pass C pending
  - Stage 3 (Fault Diagnostics Overview): Pass B complete, Pass C pending
  - Stage 4 (Dependency & Import Hygiene): Pass B complete, Pass C pending
  - Stage 5 (Monkey Patch Oversight): **Pass C complete** (HOP-compliant 2026-01-03)
  - Stage 6 (Standards Integrity): **Pass C complete** (HOP-compliant 2026-01-03)
  - Stage 7 (Meta-Orchestrator): Pass B complete, Pass C pending
- **Phase 3 (Consolidation & Freeze):** Not started

---

## 3. Global Pipeline Overview

### 3.1 Narrative Summary

The HealthView Orchestration Pipeline measures repository health by executing staged orchestrators
across six maturity domains: Testing Perspectives (test coverage, hardening), Documentation Quality
(integrity, churn), Runtime Reliability (fault diagnostics), Dependency Management (import hygiene,
typecheck), Technical Debt Oversight (monkey patches, anti-patterns), and Process Governance
(standards compliance). Each orchestrator chains producer scripts (raw data collection), consumer
scripts (single-hop analysis), and aggregator scripts (multi-source blending) into timestamped
report bundles. A meta-orchestrator can execute all domain orchestrators sequentially for
full-suite diagnostics.

**Outputs & discovery semantics:**

- **Current (repo evidence today):** bundles are written under
  `.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/`.
- **Target (HOP contract):** migrate to
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- **Discovery invariant:** HealthView bundles must be discoverable by scanning timestamped
  directories; HealthView does not rely on mutable “latest” pointers.
- **Retention (HOP target):** history pruning is enforced in code; see Tier-2 rosters for current
  evidence and pruning surfaces.

The pipeline is invoked manually via CLI/make targets; future work includes CI/CD integration and
automated alerting.

### 3.2 High-Level Stage List

- **Stage 1 – Testing Perspectives**  
- **Stage 2 – Documentation Quality**  
- **Stage 3 – Runtime Reliability**  
- **Stage 4 – Dependency Management**  
- **Stage 5 – Technical Debt Oversight**  
- **Stage 6 – Process Governance**  
- **Stage 7 – Running the Complete Suite**

---

## 3.3 How to Read This Document

- Start with **Sections 1–3** for context and the global map.
- Read **Stages 1–6** in maturity order to understand each health domain's orchestrators.
- Use **Stage 7** to understand how the meta-orchestrator chains all domains.
- Consult the **Snapshot and Stage Matrix (Section 13)** for a quick status overview.
- Check the **Contradiction Registry (Section 14)** for known inconsistencies.
- Reference the **Tier-2 Document Index (Section 15)** for implementation details.
- Unchecked Tier-1 gate checkboxes (`[ ]`) are the canonical work queue; follow the linked Tier-2
  records and stop-gates to pick up the next unit of work.

---

## 3.4 HealthView Report Bundle Spine (Shared Backbone)

**What it is:**  
Design intent (HOP target): HealthView orchestrators converge on a standardized **report bundle**
structure consisting of
three files: `manifest.json` (metadata), `summary.md` (human-readable digest), and `telemetry.json`
(metrics time series). This shared backbone ensures consistent artifact discovery, retention
policies, and downstream consumption patterns across all health domains.

**Components participating:**

- All orchestrators in Stages 1–6
- Shared utilities in `.repo_studios/command_center/scripts/libraries/cli.py` (bundle writing, pruning)
- Report naming standards enforced by `REPORT_NAMING_STANDARDS.md`

**Lifecycle contract (HOP target, with stage-scoped current evidence):**

- **Target lifecycle guarantee (HOP):** each orchestrator publishes a timestamped HealthView bundle
  with the base package (`manifest.json`, `summary.md`, `telemetry.json`).
- **Current evidence is stage-scoped:** while migration is in progress, stages may be missing base
  package artifacts and/or emit additional artifacts; Tier-2 rosters are the source of truth.
- **Current (repo evidence today):** bundles live at
  `.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/`
- **Target (HOP contract):** bundles live at
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
- **Discovery invariant (HOP target):** bundles are discovered by scanning timestamped
  directories; mutable pointer files (`latest_*` / `current_*`) are disallowed by contract.
- **Retention (HOP target):** retention is enforced in code; see Tier-2 rosters for current
  evidence and pruning surfaces.
- Missing artifacts are treated as a stop-gate for contract compliance; stage-specific failure
  behavior and cleanup semantics are documented in Tier-2 rosters.

**Why downstream stages assume this:**  
Aggregators and meta-orchestrators can discover latest reports by scanning directory timestamps
without requiring mutable "latest" pointers. Trend analysis tools can compare bundles across time
by iterating timestamp-sorted directories.

**Evidence:**

- [REPORT_NAMING_STANDARDS.md](../../../../REPORT_NAMING_STANDARDS.md)
- [.repo_studios/command_center/scripts/libraries/cli.py]
  (../../../command_center/scripts/libraries/cli.py) (bundle writing functions)
- [.repo_studios/command_center/scripts/orchestrators/]
  (../../../command_center/scripts/orchestrators/) (all orchestrators follow pattern)

---

## 3.5 HealthView Orchestration Envelope (Shared Payload)

**What it contains:**  
Each orchestrator run propagates an **execution envelope** tracking:

- Orchestrator name and topic slug
- Timestamp (ISO 8601)
- Repo root path
- Invoked scripts (ordered list with paths)
- Exit codes per script
- Log level configuration
- Output artifact paths
- Success/failure status

**Where created:**  
Envelope is initialized at orchestrator entry point (e.g., `run_test_execution_telemetry.py`'s
`main()` function) and written to `manifest.json` upon completion.

**How enriched:**  
As each script executes, the orchestrator appends its exit code and artifact paths to the envelope.
Final aggregator/summarizer adds analysis metadata (e.g., metrics computed, trends detected).

**How surfaced:**  
The meta-orchestrator (`orchestrate_full_diagnostic.py`) collects envelopes from all Stage NN.1
orchestrators and produces a **composite envelope** showing full-suite status.

**Evidence:**

- [.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py]
  (../../../command_center/scripts/orchestrators/run_test_execution_telemetry.py)
  (lines 20–80: envelope initialization)
- [.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py]
  (../../../command_center/scripts/orchestrators/orchestrate_full_diagnostic.py)
  (composite envelope logic)

**Envelope fields (manifest.json schema):**

- `orchestrator_name` (string)
- `topic_slug` (string, e.g., "test_execution_telemetry")
- `timestamp` (ISO 8601 string)
- `repo_root` (absolute path)
- `scripts_invoked` (array of objects: `{name, path, exit_code, artifacts}`)
- `log_level` (string: DEBUG, INFO, WARNING, ERROR)
- `output_directory` (absolute path to bundle; current vs target roots are tracked in the
  Contradiction Registry until migration is complete)
- `status` (string: "success" | "partial_failure" | "complete_failure")
- `duration_seconds` (float)

---

## 3.6 Orchestrator Lifecycle, Fallback Modes, and Global Controls

**Session lifecycle:**

- **Start:** Orchestrator parses CLI args, validates repo root, initializes logging
- **Execute:** Scripts run sequentially; each script failure is logged but does not always abort
  pipeline (configurable)
- **Aggregate:** Final script synthesizes outputs from earlier scripts
- **Publish:** Bundle written to timestamped directory, history pruned
- **End:** Orchestrator exits with aggregated status code (0 = success, non-zero = failure)

**Fallback modes:**

- **Continue-on-error:** If a non-critical script fails, orchestrator logs warning and proceeds
  (used for utilities)
- **Abort-on-failure:** If a producer script fails, orchestrator aborts immediately (used for data
  collection steps)
- **Partial-bundle mode:** Orchestrator writes partial manifest noting which scripts completed
  before failure

**Global controls (conceptual):**

- Logging verbosity
- Repository root override
- Optional reuse of existing upstream artifacts (debug mode)
- Dry-run validation (future: not yet implemented)
- Python interpreter selection (virtual env coordination)

**Evidence:**

- [.repo_studios/command_center/scripts/libraries/cli.py]
  (../../../command_center/scripts/libraries/cli.py) (`build_standard_options` function)

---

## 3.7 HealthView Assumptions & Guarantees

**Target contract and design intent:**

- **Target guarantee (HOP):** HealthView bundles converge on the base package:
  `manifest.json`, `summary.md`, `telemetry.json`.
  - **Current evidence is stage-scoped:** see Tier-2 rosters for current completeness and any
    additional artifacts.
- **Current (repo evidence today):** bundles are written under
  `.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/`.
- **Target (HOP contract):** bundles are written under
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- **Discovery invariant:** bundles are discovered by timestamped directories; HealthView does not
  create mutable pointer files (`latest_*`, `current_*`).
- **Retention (HOP target):** retention is enforced in code; see Tier-2 rosters for current
  evidence and pruning surfaces.
- Exit code 0 = success, non-zero = failure (script-level failures propagate to orchestrator level)
- All artifacts follow [REPORT_NAMING_STANDARDS.md](../../../../REPORT_NAMING_STANDARDS.md) (viewer/topic/timestamp/artifact)
- Scripts invoked via dynamic imports (`run(argv)` helpers), not subprocess spawning (except where noted)

**Assumptions:**

- Python 3.10+ environment with dependencies installed (`.venv` or conda env)
- Repository root is a valid Git working directory with `.repo_studios/` structure
- Upstream scripts honor CLI contracts (`--repo-root`, `--log-level`, `--output`)
- Filesystem write permissions to the active HealthView output root
  (`.repo_studios/command_center/reports/` today; `.repo_studios/reports/` after HOP migration)
- Git history available for churn/trend analysis (shallow clones may degrade metrics)

**Evidence:**

- [.repo_studios/scripts/README.md](../../../scripts/README.md) (tier responsibilities)
- [.repo_studios/Makefile](../../../Makefile) (make targets invoking orchestrators)
- [pytest tests/tests_command_center/](../../../tests/tests_command_center/) (orchestrator
  integration tests)

---

## 4. Stage 1 – Testing Perspectives

> **Purpose:** Measure test suite health through coverage analysis, log parsing, hardening metrics,
> and churn-complexity heatmaps to ensure testing keeps pace with codebase growth.

### 4.1 Stage 1.1: Test Execution Telemetry

_Tier-2 references (depth lives here):_

- [Contract snapshot](tier2_roster/tier2_test_execution_telemetry_roster.md#23-current-vs-target-contract-snapshot-stage-11)
  — target vs current, bundle invariants, naming/paths
- [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates)
  — verification checks + failure signatures + next actions
- [Records index](tier2_roster/tier2_test_execution_telemetry_roster.md#31-per-script-inspection-table-v1)
  — per-script inspection index + evidence links (Tier-2 holds proof)

**Stage 1.1 Script Gate Summary (Tier-1):**

- [x] collect_test_log_reports.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--collect_test_log_reportspy)
- [x] generate_test_coverage_inventory.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--generate_test_coverage_inventorypy)
- [x] analyze_test_hardening.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--analyze_test_hardeningpy)
- [x] generate_test_log_health_report.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--generate_test_log_health_reportpy)
- [x] generate_churn_complexity_heatmap.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--generate_churn_complexity_heatmappy)
- [x] summarize_test_execution_telemetry.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#record--summarize_test_execution_telemetrypy)
  - Tier-3: [tier3_summarize_test_execution_telemetry.yaml](tier3_scripts/test_execution_telemetry/tier3_summarize_test_execution_telemetry.yaml)
- [x] run_test_execution_telemetry.py — Tier-2 DONE checked. See: [Tier-2 record](tier2_roster/tier2_test_execution_telemetry_roster.md#fixture-example-permanent--run_test_execution_telemetrypy)

**Stage 1.1 Gate Checklist (Tier-1):**

These are Stage 1.1 readiness gates after all Tier-2 DONE script gates are closed.

- [x] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`).
  See: [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates)
- [x] No pointer artifacts (`latest_*` / `current_*`).
  See: [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates)
- [x] Output root aligned to HOP contract (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`). See: [Contract snapshot](tier2_roster/tier2_test_execution_telemetry_roster.md#23-current-vs-target-contract-snapshot-stage-11)
- [x] Tier-3 eligible (Stage 1.1 Tier-2 depth captured; ready for Tier-3 extraction). See: [Records index](tier2_roster/tier2_test_execution_telemetry_roster.md#31-per-script-inspection-table-v1)

**Target contract (locked decisions):**

- Output root migrates to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present: `manifest.json`, `summary.md`, `telemetry.json`.
- Discovery is timestamp-based only (no pointer files such as `latest_*`).

**Current evidence (Stage 1.1):**

- Stage 1.1 output root is aligned to the Tier-1 contract:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present (`manifest.json`, `summary.md`, `telemetry.json`).
- No pointer artifacts (`latest_*` / `current_*`) were observed under `.repo_studios/reports/healthview`.
- Details and evidence live in the Stage 1.1 Tier-2 roster:
  [Current vs Target snapshot](tier2_roster/tier2_test_execution_telemetry_roster.md#23-current-vs-target-contract-snapshot-stage-11),
  [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates).

**Overview:**  
The Test Execution Telemetry orchestrator runs a producer → consumer → aggregator → summarizer
pipeline to synthesize test execution signals into a HealthView topic bundle. Expect 5-6 minute
runtime when churn analysis is enabled; pipeline stops on first hard failure (with snapshot-mode
exceptions explicitly recorded in the relevant manifests when enabled).

**Orchestrator:**  
[.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py](../../../command_center/scripts/orchestrators/run_test_execution_telemetry.py)

**Invoked Scripts:**

- The authoritative Stage 1.1 script inventory (with per-script I/O evidence) lives in the Tier-2
  roster: [Records index](tier2_roster/tier2_test_execution_telemetry_roster.md#31-per-script-inspection-table-v1).

**Inputs:**

- Pytest log files and JUnit XML from `.repo_studios/reports/healthview/rawview/test_execution_runs/<timestamp>/`
- `coverage.xml` from `coverage.xml` (repo root; refreshed when configured)
- Git history for churn analysis (via git log)
- Optional: Lizard complexity metrics source (JSON file, fallback to churn-only if missing)

**Outputs:**

- **Healthview bundle (current evidence):**
  `.repo_studios/reports/healthview/orchestrator_reports/test_execution_telemetry/<timestamp>/`
  - Base package: `manifest.json`, `summary.md`, `telemetry.json`.
- **Intermediate artifacts (current evidence):** stage- and script-specific; Tier-1 does not
  enumerate current per-script output roots.
  - See Tier-2 Stage 1.1: [Current vs Target snapshot](tier2_roster/tier2_test_execution_telemetry_roster.md#23-current-vs-target-contract-snapshot-stage-11)
    and [Stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#32-stop-gates).
**Status:** `Operational – Partial hardening complete`

**Execution Details:**

- Scripts invoked via dynamic imports using `run(argv)` helpers (not subprocess spawning)
- Exit code propagation: first non-zero exit stops pipeline by default.
  - Snapshot mode may tolerate coverage refresh failures so the orchestrator still emits a usable
    bundle while recording refresh exit codes in the coverage producer manifest.
- Artifact retention is configurable; Stage 1.1 exposes multiple retention knobs during migration.
  See Tier-2 Stage 1.1 for the current retention surfaces and pruning evidence.
- Stage-specific configuration (timestamp overrides, optional inputs, tuning knobs) lives in Tier-2;
  see the Stage 1.1 roster for current evidence.

**Planned Expansions:**

- **Stage 1.2: Performance Test Health** – Orchestrator for tracking performance regression tests,
  benchmarking, profiling (future)
- **Stage 1.3: Integration Test Coverage** – Orchestrator for end-to-end test suite metrics, external
  dependency mocking (future)

**Known Gaps:**

- Test hardening analysis computes metrics but detailed flaky test reports not yet wired into
  health summary
- Churn-complexity heatmap gracefully degrades to churn-only mode when optional complexity
  metrics are unavailable
- Warnings and slow test counts collected but threshold-based alerting not yet implemented

**Evidence Links:**

- **Orchestrator:** [run_test_execution_telemetry.py]
  (../../../command_center/scripts/orchestrators/run_test_execution_telemetry.py)
  (pipeline coordination, dynamic imports, artifact retention)
- **Tier-2 roster (authoritative per-script evidence):**
  [Stage 1.1 records + stop-gates](tier2_roster/tier2_test_execution_telemetry_roster.md#31-per-script-inspection-table-v1)
- **Tests:** [test_run_test_execution_telemetry.py]
  (../../../tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py)
  (orchestrator integration tests with mocked script execution)

---

## 5. Stage 2 – Documentation Quality

> **Purpose:** Monitor documentation coverage, integrity, anchor validity, and churn to prevent
> documentation debt from accumulating silently.

### 5.1 Stage 2.1: Docs Health Overview

_Tier-2 references (depth lives here):_

- [Contract snapshot](tier2_roster/tier2_docs_health_overview_roster.
  d#23-current-vs-target-contract-snapshot-stage-21) — target vs current, bundle invariants, naming/paths
- [Stop-gates](tier2_roster/tier2_docs_health_overview_roster.md#32-stop-gates-and-implementation-checklists)
  — verification checks + failure signatures + next actions
- [Records index](tier2_roster/tier2_docs_health_overview_roster.md#311-records-index) — per-script
  inspection index + evidence links (Tier-2 holds proof)

**Stage 2.1 Script Gate Summary (Tier-1):**

- [x] generate_doc_index.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-002-generate-doc-index)
- [x] generate_anchor_inventory.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-003-generate-anchor-inventory)
- [x] validate_markdown_anchors.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-004-validate-markdown-anchors)
- [x] verify_docs_integrity.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-005-verify-docs-integrity)
- [x] validate_metrics_anchor_stubs.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-006-validate-metrics-anchor-stubs)
- [x] generate_code_doc_churn_report.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-007-generate-code-doc-churn-report)
- [x] generate_undocumented_logic_report.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-008-generate-undocumented-logic-report)
- [x] aggregate_docs_health_signals.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-009-aggregate-docs-health-signals)
- [x] run_docs_health_overview.py — complete. See: [Tier-2 record](tier2_roster/tier2_docs_health_overview_roster.md#s21r-001-docs-health-overview-orchestrator)

**Stage 2.1 Gate Checklist (Tier-1):**

These are Stage 2.1 readiness gates after all Tier-2 DONE script gates are closed.

- [x] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`). See: [Stop-gates](tier2_roster/tier2_docs_health_overview_roster.md#32-stop-gates-and-implementation-checklists)
- [x] No pointer artifacts (`latest_*` / `current_*`). See: [Stop-gates](tier2_roster/tier2_docs_health_overview_roster.md#32-stop-gates-and-implementation-checklists)
- [x] Output root aligned to HOP contract (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`).
  See: [Contract snapshot](tier2_roster/tier2_docs_health_overview_roster.md#23-current-vs-target-contract-snapshot-stage-21)
- [x] Tier-3 eligible (Stage 2.1 Tier-2 depth captured; ready for Tier-3 extraction). See:
  [Records index](tier2_roster/tier2_docs_health_overview_roster.md#311-records-index)

**Target contract (HOP):**

- Canonical output root is `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present: `manifest.json`, `summary.md`, `telemetry.json`.
- No pointer files such as `latest_*`.

**Current evidence (Stage 2.1):**

- Current output root observed: `.repo_studios/command_center/reports/healthview/docs_health/<YYYYMMDD-HHMM>/`.
- Base package artifacts observed for current runs: `manifest.json`, `summary.md`, `telemetry.json`.
- Pointer artifacts remain a stop-gate (`latest_*`), per Stage 2.1 stop-gates.
- Details and evidence live in the Stage 2.1 Tier-2 roster:
  [Current vs Target snapshot](tier2_roster/tier2_docs_health_overview_roster.md#23-current-vs-target-contract-snapshot-stage-21),
  [Stop-gates](tier2_roster/tier2_docs_health_overview_roster.md#32-stop-gates-and-implementation-checklists).

**Overview:**  
The Docs Health Overview orchestrator chains eight scripts in producer → aggregator pipeline: (1)
generate doc index scanning markdown files for headings/links, (2) build anchor inventory
extracting markdown anchor IDs, (3) validate markdown anchors checking for broken links, (4) verify
docs integrity by validating governed JSON `content_hash` blocks (and regenerating the docs index table), (5) validate metrics anchor stubs
ensuring metric definitions have anchors, (6) generate code-doc churn report comparing code vs. doc
file churn, (7) generate undocumented logic report identifying functions lacking docstrings, and
(8) aggregate all signals into final HealthView bundle. Expect 6-8 minute runtime depending on
anchor validation and churn aggregation. Replaces legacy ad hoc docs inventory/anchor/analysis chain.

**Orchestrator:**  
[.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py](../../../command_center/scripts/orchestrators/run_docs_health_overview.py)

**Invoked Scripts (8):**

| Script | Category | Purpose | Tier-3 YAML |
| ------ | -------- | ------- | ----------- |
| `generate_doc_index.py` | Producer | Scan repository for markdown files, extract headings, build document inventory | TBD |
| `generate_anchor_inventory.py` | Producer | Extract markdown anchor IDs, build cross-reference map with duplicates flagged | TBD |
| `validate_markdown_anchors.py` | Producer | Check for broken internal links, orphaned anchors, cross-file reference errors | TBD |
| `verify_docs_integrity.py` | Producer | Validate governed JSON `content_hash` blocks and refresh the docs index table | [tier3_verify_docs_integrity.yaml](tier3_scripts/docs_health_overview/tier3_verify_docs_integrity.yaml) |
| `validate_metrics_anchor_stubs.py` | Producer | Ensure metric definitions have corresponding anchor points for linking | [tier3_validate_metrics_anchor_stubs.yaml](tier3_scripts/docs_health_overview/tier3_validate_metrics_anchor_stubs.yaml) |
| `generate_code_doc_churn_report.py` | Producer | Compare code file churn vs. doc file churn, identify staleness risk areas | [tier3_generate_code_doc_churn_report.yaml](tier3_scripts/docs_health_overview/tier3_generate_code_doc_churn_report.yaml) |
| `generate_undocumented_logic_report.py` | Producer | Identify functions/classes lacking docstrings or external doc references | TBD |
| `aggregate_docs_health_signals.py` | Aggregator | Synthesize all doc metrics into single health score, trend report, signal matrix | TBD |

**Inputs:**

- Markdown files across repository (recursively scanned)
- Python source files (for docstring analysis)
- Git history for churn metrics (via git log)
- Standards definitions from `docs/standards/` (for integrity validation)
- Previous doc index and anchor inventory (for diff comparison)
**Outputs:**

- **Healthview bundle:** `.repo_studios/command_center/reports/healthview/docs_health/<YYYY-MM-DD>/`
  - `manifest.json` (orchestrator execution metadata)
  - `summary.md` (human-readable digest)
  - `telemetry.json` (time-series metrics)
- **Intermediate artifacts:** Tier-1 does not enumerate intermediate output roots for this stage.
  See Tier-2 Stage 2.1 for current intermediate roots, retention surfaces, and pruning evidence:
  [Contract snapshot](tier2_roster/tier2_docs_health_overview_roster.md#23-current-vs-target-contract-snapshot-stage-21),
  [Stop-gates](tier2_roster/tier2_docs_health_overview_roster.md#32-stop-gates-and-implementation-checklists).

**Status:** `Operational – Partial hardening complete`

**Execution Details:**

- Scripts invoked via dynamic imports using `run(argv)` helpers loaded via `_load_callable()`
  (not subprocess spawning)
- Shared configuration is threaded through the pipeline (timestamp, repo-root, log-level)
- Selective step skipping is supported during migration; see Tier-2 Stage 2.1 for the current
  skip surfaces and evidence
- Retention behavior is enforced in code; see Tier-2 Stage 2.1 for current retention surfaces and
  pruning evidence.
- Report naming enforced via `enforce_report_naming()` guardrail (raises `GuardrailViolationError`
  if violated)

**Planned Expansions:**

- **Stage 2.2: Anchor Health Report** – Integrate `generate_anchor_health_report.py` for deeper
  cross-reference validation and link health scoring (gap identified in coverage analysis)

**Known Gaps:**

- Undocumented logic report covers Python only; JavaScript/TypeScript support pending
- Doc-code staleness heuristic uses simple churn ratio; needs adjustment based on module
  criticality weighting
- Metrics stub validation is basic regex matching; does not verify anchor target validity
- No automated remediation suggestions (e.g., "add docstring here") – reports are diagnostic only

**Evidence Links:**

- **Orchestrator:** [run_docs_health_overview.py]
  (../../../command_center/scripts/orchestrators/run_docs_health_overview.py)
  (pipeline coordination, shared configuration, report naming guardrails)
- **Producer scripts:**
  - [generate_doc_index.py](../../../scripts/producers/generate_doc_index.py)
    (lines 394-432: `_execute_doc_index` invocation)
  - [generate_anchor_inventory.py](../../../scripts/producers/generate_anchor_inventory.py)
    (lines 433-469: `_execute_anchor_inventory` invocation)
  - [validate_markdown_anchors.py](../../../scripts/producers/validate_markdown_anchors.py)
    (lines 470-506: `_execute_anchor_validation` invocation)
  - [verify_docs_integrity.py](../../../scripts/producers/verify_docs_integrity.py)
    (lines 507-531: `_execute_docs_integrity` invocation)
  - [validate_metrics_anchor_stubs.py](../../../scripts/producers/validate_metrics_anchor_stubs.py)
    (lines 532-556: `_execute_metrics_stub` invocation)
  - [generate_code_doc_churn_report.py](../../../scripts/producers/generate_code_doc_churn_report.py)
    (lines 557-584: `_execute_churn` invocation)
  - [generate_undocumented_logic_report.py](../../../scripts/producers/generate_undocumented_logic_report.py)
    (lines 585-649: `_execute_undocumented` invocation
- **Aggregator script:**
  [aggregate_docs_health_signals.py](../../../scripts/aggregators/aggregate_docs_health_signals.py)
  (lines 650-710: `_execute_aggregator` invocation)
- **Tests:** No dedicated orchestrator tests found (marked "tests TBD" in Stage Matrix)

---

## 6. Stage 3 – Runtime Reliability

> **Purpose:** Track runtime faults, segfaults, and error conditions through faulthandler reports
> to identify stability risks before production deployment.

### 6.1 Stage 3.1: Fault Diagnostics Overview

_Tier-2 references (depth lives here):_

- [Contract snapshot](tier2_roster/tier2_fault_diagnostics_overview_roster.md#23-current-vs-target-contract-snapshot-stage-31)
  — target vs current, bundle invariants, naming/paths
- [Stop-gates](tier2_roster/tier2_fault_diagnostics_overview_roster.md#32-stop-gates-and-implementation-checklists)
  — verification checks + failure signatures + next actions
- [Records index](tier2_roster/tier2_fault_diagnostics_overview_roster.md#311-records-index)
  — per-script inspection index + evidence links (Tier-2 holds proof)

**Stage 3.1 Script Gate Summary (Tier-1):**

- [x] collect_faulthandler_reports.py — complete.
  See: [Tier-2 record](tier2_roster/tier2_fault_diagnostics_overview_roster.md#s31r-002-collect-faulthandler-reports)
  Tier-3: [tier3_collect_faulthandler_reports.yaml](tier3_scripts/fault_diagnostics_overview/tier3_collect_faulthandler_reports.yaml)
- [x] generate_fault_artifacts.py — complete.
  See: [Tier-2 record](tier2_roster/tier2_fault_diagnostics_overview_roster.md#s31r-003-generate-fault-artifacts)
  Tier-3: [tier3_generate_fault_artifacts.yaml](tier3_scripts/fault_diagnostics_overview/tier3_generate_fault_artifacts.yaml)
- [x] summarize_fault_diagnostics_overview.py — complete.
  See: [Tier-2 record](tier2_roster/tier2_fault_diagnostics_overview_roster.md#s31r-004-summarize-fault-diagnostics-overview)
  Tier-3: [tier3_summarize_fault_diagnostics_overview.yaml](tier3_scripts/fault_diagnostics_overview/tier3_summarize_fault_diagnostics_overview.yaml)
- [x] run_fault_diagnostics_overview.py — complete.
  See: [Tier-2 record](tier2_roster/tier2_fault_diagnostics_overview_roster.md#s31r-001-fault-diagnostics-overview-orchestrator)
  Tier-3: [tier3_run_fault_diagnostics_overview.yaml](tier3_scripts/fault_diagnostics_overview/tier3_run_fault_diagnostics_overview.yaml)

**Stage 3.1 Gate Checklist (Tier-1):**

These are Stage 3.1 readiness gates after all Tier-2 DONE script gates are closed.

- [x] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`).
  See: [Stop-gates](tier2_roster/tier2_fault_diagnostics_overview_roster.md#32-stop-gates-and-implementation-checklists)
- [x] No pointer artifacts (`latest_*` / `current_*`).
  See: [Stop-gates](tier2_roster/tier2_fault_diagnostics_overview_roster.md#32-stop-gates-and-implementation-checklists)
- [x] Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`).
  See: [Contract snapshot](tier2_roster/tier2_fault_diagnostics_overview_roster.md#23-current-vs-target-contract-snapshot-stage-31)
- [x] Tier-3 eligible (Stage 3.1 Tier-2 depth captured; ready for Tier-3 extraction).
  See: [Records index](tier2_roster/tier2_fault_diagnostics_overview_roster.md#311-records-index)

**Target contract (HOP):**

- Output root migrates to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present: `manifest.json`, `summary.md`, `telemetry.json`.
- Discovery is timestamp-based only (no pointer files such as `latest_*`).

**Current evidence (Stage 3.1):**

- Stage 3.1 output root is aligned to the Tier-1 contract:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present (`manifest.json`, `summary.md`, `telemetry.json`).
- No pointer artifacts (`latest_*` / `current_*`) were observed under `.repo_studios/reports/healthview`.
- All 4 scripts use `build_topic_path()` library for HOP-compliant output paths.
- Details and evidence live in the Stage 3.1 Tier-2 roster:
  [Current vs Target snapshot](tier2_roster/tier2_fault_diagnostics_overview_roster.md#23-current-vs-target-contract-snapshot-stage-31),
  [Stop-gates](tier2_roster/tier2_fault_diagnostics_overview_roster.md#32-stop-gates-and-implementation-checklists).

**Overview:**  
The Fault Diagnostics Overview orchestrator chains a 3-script pipeline
(producer → consumer → summarizer) for end-to-end faulthandler diagnostics. Replaces legacy
`run_fault_pipeline.py`. Runtime: 3-5 minutes typical (from docstring, lines 1-25).

**Orchestrator:**
[run_fault_diagnostics_overview.py](../../../command_center/scripts/orchestrators/run_fault_diagnostics_overview.py)
(604 lines)

**Invoked Scripts (3):**

| Script | Category | Purpose | Tier-3 YAML |
| ------ | -------- | ------- | ----------- |
| `collect_faulthandler_reports.py` | Producer | Scan HealthView rawview fault diagnostics runs, parse faulthandler dumps, categorize faults | [tier3_collect_faulthandler_reports.yaml](tier3_scripts/fault_diagnostics_overview/tier3_collect_faulthandler_reports.yaml) |
| `generate_fault_artifacts.py` | Consumer | Process producer output into structured artifacts (CSV, JSON, SUMMARY.md) | [tier3_generate_fault_artifacts.yaml](tier3_scripts/fault_diagnostics_overview/tier3_generate_fault_artifacts.yaml) |
| `summarize_fault_diagnostics_overview.py` | Summarizer | Generate HealthView overview bundle with cross-run comparisons | [tier3_summarize_fault_diagnostics_overview.yaml](tier3_scripts/fault_diagnostics_overview/tier3_summarize_fault_diagnostics_overview.yaml) |

**Inputs:**

- `.repo_studios/reports/healthview/rawview/fault_diagnostics/<timestamp>/` (runtime directories with crash dumps)
- `--runs-dir` (optional override for the rawview runs base)
- Optional `--run-dir` (explicit run directory override)
- Optional `--reuse-report` (path to existing producer report JSON)
- Optional `--producer-top-frames` (override frame depth for producer)

**Outputs:**

- Producer bundle: `.repo_studios/reports/healthview/producer_reports/faulthandler_reports/<YYYYMMDD-HHMM>/`
- Consumer bundle: `.repo_studios/reports/healthview/consumer_reports/fault_artifacts/<YYYYMMDD-HHMM>/`
- Summarizer bundle: `.repo_studios/reports/healthview/summarizer_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/`
- Orchestrator bundle: `.repo_studios/reports/healthview/orchestrator_reports/fault_diagnostics_overview/<YYYYMMDD-HHMM>/`

**Execution Notes:**

- Dynamic imports via `_load_callable()` for producer, consumer, and summarizer scripts (lines 218-235)
- Supports 3 skip flags: `--skip-producer`, `--skip-consumer`, `--skip-summarizer` (lines 206-208)
- Can reuse existing producer reports via `--reuse-report` flag (lines 211, 343-344)
- Can override producer frame depth via `--producer-top-frames` (lines 212, 293-294)
- Retention behavior is enforced in code; see Tier-2 Stage 3.1 for current evidence.
- Fail-fast: Aborts on summarizer failure, continues if producer/consumer skipped (lines 512-518)
- Writes orchestrator telemetry to HealthView bundle with metrics (file count, total bytes,
  timestamps, lines 534-543)
- Execution functions: `_execute_producer()` (lines 272-312), `_execute_consumer()` (lines 315-371),
  `_execute_summarizer()` (lines 374-423)
- Script registration via `CatalogRegistry` for downstream discovery (lines 427-431)

**Status:** `Operational (partial hardening)` – Script count corrected from 2 to 3, runtime verified
at 3-5 minutes, special reuse/override flags confirmed

**Planned Expansions:**

- **Stage 3.2: Fault Runtime Utilities** – Integrate `configure_faulthandler_runtime.py`,
  `dump_faulthandler_snapshot.py`, `fault_run_analysis.py` (gap identified in coverage analysis)

**Known Gaps:**

- Faulthandler collection requires explicit environment variable configuration; not all CI/CD runs
  enable it
- Crash dump parsing is basic; does not yet extract full stack frames or thread states

**Evidence Links:**

- [.repo_studios/scripts/producers/collect_faulthandler_reports.py](../../../scripts/producers/collect_faulthandler_reports.py)
- [.repo_studios/scripts/consumers/generate_fault_artifacts.py](../../../scripts/consumers/generate_fault_artifacts.py)
- [.repo_studios/tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py](../../../tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py)

---

## 7. Stage 4 – Dependency Management

> **Purpose:** Enforce dependency hygiene, import graph health, typecheck compliance,
> and placeholder tracking to prevent import cycles and type safety regressions.

### 7.1 Stage 4.1: Dependency & Import Hygiene

_Tier-2 references (depth lives here):_

- [Contract snapshot](tier2_roster/tier2_dependency_import_hygiene_roster.md#23-current-vs-target-contract-snapshot-stage-41)
  — target vs current, bundle invariants, naming/paths
- [Stop-gates](tier2_roster/tier2_dependency_import_hygiene_roster.md#32-stop-gates-and-implementation-checklists)
  — verification checks + failure signatures + next actions
- [Records index](tier2_roster/tier2_dependency_import_hygiene_roster.md#311-records-index)
  — per-script inspection index + evidence links (Tier-2 holds proof)

**Stage 4.1 Script Gate Summary (Tier-1):**

- [x] generate_dependency_hygiene_report.py — complete. See: [Tier-2 record](tier2_roster/tier2_dependency_import_hygiene_roster.md#s41r-002-generate_dependency_hygiene_reportpy)
  Tier-3: [tier3_generate_dependency_hygiene_report.yaml](tier3_scripts/dependency_import_hygiene/tier3_generate_dependency_hygiene_report.yaml)
- [x] generate_import_graph_report.py — complete. See: [Tier-2 record](tier2_roster/tier2_dependency_import_hygiene_roster.md#s41r-003-generate_import_graph_reportpy)
  Tier-3: [tier3_generate_import_graph_report.yaml](tier3_scripts/dependency_import_hygiene/tier3_generate_import_graph_report.yaml)
- [x] scan_code_placeholders.py — complete. See: [Tier-2 record](tier2_roster/tier2_dependency_import_hygiene_roster.md#s41r-004-scan_code_placeholderspy)
  Tier-3: [tier3_scan_code_placeholders.yaml](tier3_scripts/dependency_import_hygiene/tier3_scan_code_placeholders.yaml)
- [x] generate_typecheck_report.py — complete. See: [Tier-2 record](tier2_roster/tier2_dependency_import_hygiene_roster.md#s41r-005-generate_typecheck_reportpy)
  Tier-3: [tier3_generate_typecheck_report.yaml](tier3_scripts/dependency_import_hygiene/tier3_generate_typecheck_report.yaml)
- [x] refresh_mypy_baselines.py — complete (utility, non-HOP). See: [Tier-2 record](tier2_roster/tier2_dependency_import_hygiene_roster.md#s41r-006-refresh_mypy_baselinespy)
  Tier-3: [tier3_refresh_mypy_baselines.yaml](tier3_scripts/dependency_import_hygiene/tier3_refresh_mypy_baselines.yaml)
- [x] run_dependency_import_hygiene.py — complete (orchestrator). See: [Tier-2 record](tier2_roster/tier2_dependency_import_hygiene_roster.md#s41r-001-dependency-import-hygiene-orchestrator)
  Tier-3: [tier3_run_dependency_import_hygiene.yaml](tier3_scripts/dependency_import_hygiene/tier3_run_dependency_import_hygiene.yaml)

**Stage 4.1 Gate Checklist (Tier-1):**

These are Stage 4.1 readiness gates after all Tier-2 DONE script gates are closed.

- [ ] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`).
  See: [Stop-gates](tier2_roster/tier2_dependency_import_hygiene_roster.md#32-stop-gates-and-implementation-checklists)
- [ ] No pointer artifacts (`latest_*` / `current_*`).
  See: [Stop-gates](tier2_roster/tier2_dependency_import_hygiene_roster.md#32-stop-gates-and-implementation-checklists)
- [ ] Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`).
  See: [Contract snapshot](tier2_roster/tier2_dependency_import_hygiene_roster.md#23-current-vs-target-contract-snapshot-stage-41)
- [ ] Tier-3 eligible (Stage 4.1 Tier-2 depth captured; ready for Tier-3 extraction).
  See: [Records index](tier2_roster/tier2_dependency_import_hygiene_roster.md#311-records-index)

**Target contract (locked decisions):**

- Output root migrates to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present: `manifest.json`, `summary.md`, `telemetry.json`.
- Discovery is timestamp-based only (no pointer files such as `latest_*`).

**Current evidence (Stage 4.1):**

- HealthView bundle root is still under `.repo_studios/command_center/reports/healthview/...`
  (not the canonical target root).
- Base package artifacts (`manifest.json`, `summary.md`, `telemetry.json`) are observed
  in current runs.
- Pointer artifacts remain a stop-gate (cleanup planning and mypy baselines flows write
  `latest_*` artifacts in rawview roots).
- Details and evidence live in the Stage 4.1 Tier-2 roster:
  [Current vs Target snapshot](tier2_roster/tier2_dependency_import_hygiene_roster.md#23-current-vs-target-contract-snapshot-stage-41),
  [Stop-gates](tier2_roster/tier2_dependency_import_hygiene_roster.md#32-stop-gates-and-implementation-checklists).

**Overview:**  
The Dependency & Import Hygiene orchestrator chains a 5-script pipeline (4 producers + 1 utility)
that analyzes dependency hygiene, import graphs, typecheck compliance, code placeholders
(TODO/FIXME/HACK), optional batch cleanup dry-run planning, and optional mypy baseline refresh.
Replaces legacy `run_batch_cleanup.py` with structured dry-run artifacts. Runtime: 7-11 minutes
typical in CI, with linting and mypy dominating when baseline refresh is enabled
(from docstring, lines 1-10).

**Orchestrator:**
[run_dependency_import_hygiene.py](../../../command_center/scripts/orchestrators/run_dependency_import_hygiene.py)
(1111 lines)

**Invoked Scripts (5):**

| Script | Category | Purpose | Tier-3 YAML |
| ------ | -------- | ------- | ----------- |
| `generate_dependency_hygiene_report.py` | Producer | Analyze `requirements.txt`/`pyproject.toml`, detect unused dependencies, version conflicts | TBD |
| `generate_import_graph_report.py` | Producer (optional) | Build import graph, detect cycles, compute coupling metrics | TBD |
| `scan_code_placeholders.py` | Producer | Extract TODO/FIXME/HACK comments from code, track technical debt markers | TBD |
| `generate_typecheck_report.py` | Producer (optional) | Run mypy, collect type errors, categorize by severity | TBD |
| `refresh_mypy_baselines.py` | Utility (optional) | Update mypy baseline files after type errors are resolved | TBD |

**Inputs:**

- `requirements.txt`, `pyproject.toml` (dependency manifests)
- Python source files (import statements, type hints, placeholder comments)
- Mypy configuration (`mypy.ini`)
- Existing mypy baseline files (if present)
- Placeholder allowlist (`.repo_studios/config/placeholder_allowlist.txt`, line 69)
- Optional: `--dependency-requirements-pattern` (glob patterns for dependency files, lines 256-260)
- Optional: `--import-owned` (owned package prefixes for import graph, lines 263-267)
- Optional: `--placeholder-include-ext`, `--placeholder-pattern`, `--placeholder-exclude-prefix`
  (lines 268-281)

**Outputs:**

- Dependency: `.repo_studios/reports/producer_reports/dependency_hygiene_reports/` (lines 65)
- Import Graph: `.repo_studios/reports/producer_reports/import_graph_reports/` (lines 66)
- Placeholder: `.repo_studios/reports/producer_reports/code_placeholder_scans/` (lines 67)
- Batch Cleanup: `.repo_studios/command_center/reports/rawview/dependency_import_hygiene_cleanup/`
  (lines 70-72, dry-run plan only)
- Typecheck: `.repo_studios/reports/producer_reports/typecheck_reports/` (lines 73)
- Mypy Baselines: `.repo_studios/command_center/reports/rawview/mypy_baselines/` (lines 74)
- HealthView bundle: `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<timestamp>/`
  (manifest + summary + telemetry, lines 1082-1091)

**Execution Notes:**

- Dynamic imports via `_load_callable()` for all 5 scripts (lines 365-376)
- Supports 6 skip flags: `--skip-import-graph` (lines 282-283), `--skip-typecheck` (lines 284),
  `--trigger-batch-cleanup` (lines 285-289, opt-in), `--refresh-mypy-baselines`
  (lines 290-294, opt-in), dependency patterns via `--dependency-requirements-pattern`
  (lines 256-260), `--dependency-skip-pyproject` (lines 261-262)
- Retention behavior is enforced in code; see Tier-2 Stage 4.1 for current evidence.
- Fail-tolerant pipeline: `stop_on_failure=False` (line 1005) – continues through failures except
  for cleanup step (line 1003)
- Batch cleanup dry-run: Generates structured plan without executing commands
  (lines 639-711, legacy shim retired)
- Mypy baseline refresh: Optional post-typecheck step (lines 765-793)
- Execution functions: `_dependency_report()` (lines 437-468),
  `_import_graph_report()` (lines 471-500), `_placeholder_scan()` (lines 503-543),
  `_batch_cleanup()` (lines 639-711), `_typecheck_report()` (lines 714-742),
  `_refresh_baselines()` (lines 765-793)
- Script registration via `CatalogRegistry` for downstream discovery (lines 796-803)
- Pipeline steps: dependency (mandatory), import_graph (optional), placeholders (mandatory),
  cleanup (opt-in), typecheck (optional), refresh_baselines (opt-in) – lines 999-1006

**Status:** `Operational (partial hardening)` – 5-script pipeline verified, 7-11 min runtime
confirmed, 6 skip flags documented, batch cleanup dry-run capability validated,
fail-tolerant execution confirmed

**Planned Expansions:**

- **Stage 4.2: Import Boundary Validation** – Integrate `validate_import_boundaries.py`
  to enforce architectural layer boundaries (gap identified in coverage analysis)

**Known Gaps:**

- Dependency hygiene report does not yet detect transitive dependency conflicts
- Import graph report covers Python only; JavaScript module graph pending

**Evidence:**

- Code: `.repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py`
  (lines 1-1111)
  - Script constants: Lines 51-61 (5 script paths, 5 module names)
  - Default paths: Lines 63-75 (8 output directories)
  - Option parsing: Lines 318-352 (`build_options()`)
  - Dynamic imports: Lines 365-376 (`_load_callable()`)
  - Execution functions: Lines 437-468 (`_dependency_report()`), 471-500
    (`_import_graph_report()`), 503-543 (`_placeholder_scan()`), 639-711 (`_batch_cleanup()`
    dry-run), 714-742 (`_typecheck_report()`), 765-793 (`_refresh_baselines()`)
  - Pipeline definition: Lines 999-1006 (6-step pipeline with fail-tolerant behavior)
  - Telemetry/manifest: Lines 1033-1072 (telemetry payload, artifacts section, manifest assembly)
  - Report bundle write: Lines 1082-1091 (3 artifacts, HealthView retention)
- Tests: `.repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py`

---

## 8. Stage 5 – Technical Debt Oversight

> **Purpose:** Monitor monkey patches, anti-patterns, and technical debt accumulation
> to surface risks before they metastasize into architectural issues.

### 8.1 Stage 5.1: Monkey Patch Oversight

_Tier-2 references (depth lives here):_

- [Contract snapshot](tier2_roster/tier2_monkey_patch_oversight_roster.md#23-current-vs-target-contract-snapshot-stage-51)
  — target vs current, bundle invariants, naming/paths
- [Stop-gates](tier2_roster/tier2_monkey_patch_oversight_roster.md#32-stop-gates-and-implementation-checklists)
  — verification checks + failure signatures + next actions
- [Records index](tier2_roster/tier2_monkey_patch_oversight_roster.md#311-records-index)
  — per-script inspection index + evidence links (Tier-2 holds proof)

**Stage 5.1 Script Gate Summary (Tier-1):**

- [x] scan_monkey_patches.py — Tier-2 DONE. HOP-compliant. pytest: 6. mypy: OK. Tier-3 created. See: [Tier-2 record](tier2_roster/tier2_monkey_patch_oversight_roster.md#s51r-002-monkey-patch-scan-producer)
- [x] classify_monkey_patches.py — Tier-2 DONE. HOP-compliant. pytest: 15. mypy: OK. Dead code removed. Tier-3 created. See: [Tier-2 record](tier2_roster/tier2_monkey_patch_oversight_roster.md#s51r-003-monkey-patch-risk-consumer)
- [x] analyze_monkey_patch_trends.py — Tier-2 DONE. HOP-compliant. pytest: 3. mypy: OK. Dead code removed. Tier-3 created. See: [Tier-2 record](tier2_roster/tier2_monkey_patch_oversight_roster.md#s51r-004-monkey-patch-trend-aggregator)
- [x] summarize_monkey_patch_overview.py — Tier-2 DONE. HOP-compliant. No tests. mypy: OK. Tier-3 created. See: [Tier-2 record](tier2_roster/tier2_monkey_patch_oversight_roster.md#s51r-005-monkey-patch-overview-summarizer)
- [x] monkey_patch_risk.py — Tier-2 DONE. Utility (no CLI). pytest: 5. mypy: OK. Tier-3: N/A. See: [Tier-2 record](tier2_roster/tier2_monkey_patch_oversight_roster.md#s51r-006-risk-classification-utility)
- [x] run_monkey_patch_oversight.py — Tier-2 DONE. HOP-compliant. pytest: 1. mypy: OK. Tier-3 created. Make target confirmed. See: [Tier-2 record](tier2_roster/tier2_monkey_patch_oversight_roster.md#s51r-001-monkey-patch-oversight-orchestrator)

**Stage 5.1 Gate Checklist (Tier-1):**

These are Stage 5.1 readiness gates after all Tier-2 DONE script gates are closed.

- [x] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`).
  See: [Stop-gates](tier2_roster/tier2_monkey_patch_oversight_roster.md#32-stop-gates-and-implementation-checklists)
- [x] No pointer artifacts (`latest_*` / `current_*`).
  See: [Stop-gates](tier2_roster/tier2_monkey_patch_oversight_roster.md#32-stop-gates-and-implementation-checklists)
- [x] Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`).
  See:
  [Contract snapshot](tier2_roster/tier2_monkey_patch_oversight_roster.md#23-current-vs-target-contract-snapshot-stage-51)
- [x] Tier-3 eligible (Stage 5.1 Tier-2 depth captured; ready for Tier-3 extraction).
  See:
  [Records index](tier2_roster/tier2_monkey_patch_oversight_roster.md#311-records-index)

**Target contract (locked decisions):**

- Output root migrates to `.repo_studios/reports/healthview/<class>_reports/<topic>/<timestamp>/`.
- Base package is present: `manifest.json`, `summary.md`, `telemetry.json`.
- Discovery is timestamp-based only (no pointer files such as `latest_*`).

**Current evidence (Stage 5.1 — HOP-compliant 2026-01-03):**

- All 5 scripts use `build_topic_path()` for HOP-compliant output roots.
- Slug format standardized to `YYYYMMDD-HHMM` across all scripts.
- Base package artifacts (`manifest.json`, `summary.md`, `telemetry.json`) emitted by
  producer, orchestrator, and summarizer.
- No pointer artifacts (`latest_*`) are created.
- Consumer reads producer manifest via `payload.findings`.
- Implementation plan: `implementation_plans/stage_5_hop_refactor_plan.md`
- Runtime evidence: Run `20260103-0201` verified all outputs at HOP paths.
- Details and evidence live in the Stage 5.1 Tier-2 roster:
  [Current vs Target snapshot](tier2_roster/tier2_monkey_patch_oversight_roster.md#23-current-vs-target-contract-snapshot-stage-51),
  [Stop-gates](tier2_roster/tier2_monkey_patch_oversight_roster.md#32-stop-gates-and-implementation-checklists).

**Overview:**  
The Monkey Patch Oversight orchestrator chains a 4-script pipeline
(producer → consumer → aggregator → summarizer) that scans for monkey patches via AST analysis,
classifies them by risk category, analyzes historical trends, and generates overview artifacts.
Replaces monkey patch stages that previously lived inside `orchestrate_health_suite.py` alongside
standalone summarizer invocation. Runtime: 4-7 minutes typical when Git history enrichment is
enabled; trend aggregation scales with the configured history window (from docstring, lines 1-11).

**Orchestrator:**
[run_monkey_patch_oversight.py](../../../command_center/scripts/orchestrators/run_monkey_patch_oversight.py)
(735 lines)

**Invoked Scripts (5):**

| Script | Category | Purpose | Tier-3 YAML |
| ------ | -------- | ------- | ----------- |
| `scan_monkey_patches.py` | Producer | Detect monkey patches via AST analysis, extract patch locations with Git enrichment | TBD |
| `classify_monkey_patches.py` | Consumer | Categorize patches (test fixture, workaround, production risk) into risk bundles | TBD |
| `analyze_monkey_patch_trends.py` | Aggregator | Track patch count over time across multiple runs, identify growth patterns | TBD |
| `summarize_monkey_patch_overview.py` | Summarizer | Generate HealthView overview bundle with cross-run comparisons | TBD |
| `monkey_patch_risk.py` | Utility | Compute risk score per patch based on scope, target, frequency (registered for catalog) | TBD |

**Inputs:**

- Python source files (AST parsing for monkey patch detection)
- Git history (patch introduction dates, optional via `--producer-with-git`, line 224)
- Test vs. production code boundaries (via `--producer-project-packages`, lines 221-223)
- Optional: `--producer-context-lines` (context lines around patches, line 218)
- Optional: `--producer-strict` (strict mode for producer, line 225)
- Optional: `--producer-exclude-dirs`, `--producer-exclude-globs` (exclusion patterns, lines 226-227)
- Optional: `--duplicate-matrix` (duplicate matrix path for summarizer, line 228)

**Outputs:**

- Producer: `.repo_studios/reports/healthview/producer_reports/monkey_patch_scans/<YYYYMMDD-HHMM>/`
- Consumer: `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/<YYYYMMDD-HHMM>/`
- Aggregator: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/<YYYYMMDD-HHMM>/`
- Summarizer: `.repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/<YYYYMMDD-HHMM>/`
- HealthView bundle:
  `.repo_studios/reports/healthview/orchestrator_reports/monkey_patch_oversight/<YYYYMMDD-HHMM>/`
  (manifest + summary + telemetry)

**Execution Notes:**

- Dynamic imports via `_load_callable()` for all 4 pipeline scripts (lines 288-298)
- Supports 4 skip flags: `--skip-producer`, `--skip-consumer`, `--skip-aggregator`,
  `--skip-summarizer` (lines 229-232)
- Retention behavior is enforced in code; see Tier-2 Stage 5.1 for current evidence.
- Trend analysis: Configurable history window
  (see Tier-2 Stage 5.1 for current surfaces and evidence)
- Git enrichment: Optional Git history analysis support
  (see Tier-2 Stage 5.1 for current surfaces and evidence)
- Producer configurability: Context lines, strict mode, project packages, exclude patterns
  (see Tier-2 Stage 5.1)
- Fail-fast: Aborts on summarizer failure (line 665), continues if
  producer/consumer/aggregator skipped
- Execution functions: `_execute_producer()` (lines 303-361), `_execute_consumer()`
  (lines 364-400), `_execute_aggregator()` (lines 403-449), `_execute_summarizer()`
  (lines 452-515)
- Script registration via `CatalogRegistry` for downstream discovery, includes utility script
  (lines 518-524)
- Pipeline steps: producer, consumer, aggregator, summarizer (4-step sequential with fail-fast
  on summarizer, lines 658-665)

**Status:** `Operational (partial hardening)` – 4-script pipeline verified, 4-7 min runtime
confirmed, 4 skip flags documented, Git enrichment capability validated,
trend analysis with configurable history window confirmed

**Planned Expansions:**

- TBD (no immediate gaps identified)

**Known Gaps:**

- Classification logic uses heuristics; may misclassify legitimate test fixtures as production risks
- Risk scoring does not yet account for patch stability (whether it causes test flakiness)

**Evidence:**

- Code: `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py`
  (lines 1-735)
  - Script constants: Lines 48-60 (6 script paths including utility and summarizer)
  - Default paths: Lines 63-68 (6 output directories)
  - Option parsing: Lines 254-279 (`build_options()`)
  - Dynamic imports: Lines 288-298 (`_load_callable()`)
  - Execution functions: Lines 303-361 (`_execute_producer()`), 364-400
    (`_execute_consumer()`), 403-449 (`_execute_aggregator()`), 452-515
    (`_execute_summarizer()`)
  - Pipeline definition: Lines 658-665 (4-step pipeline with fail-fast on summarizer)
  - Telemetry/manifest: Lines 670-691 (telemetry payload, artifacts section, manifest assembly)
  - Report bundle write: Lines 707-716 (3 artifacts, HealthView retention)
- Tests: `.repo_studios/tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py`

---

## 9. Stage 6 – Process Governance

> **Purpose:** Track standards compliance, prompt engineering guidelines, and process
> integrity to ensure organizational policies are consistently followed.

### 9.1 Stage 6.1: Standards Integrity

_Tier-2 references (depth lives here):_

- [Contract snapshot](tier2_roster/tier2_standards_integrity_roster.md#23-current-vs-target-contract-snapshot-stage-61)
  — target vs current, bundle invariants, naming/paths
- [Stop-gates](tier2_roster/tier2_standards_integrity_roster.md#32-stop-gates-and-implementation-checklists)
  — verification checks + failure signatures + next actions
- [Records index](tier2_roster/tier2_standards_integrity_roster.md#311-records-index)
  — per-script inspection index + evidence links (Tier-2 holds proof)

**Stage 6.1 Script Gate Summary (Tier-1):**

- [x] generate_standards_index.py — Tier-2 DONE. HOP-compliant. pytest: 4. mypy: OK. Tier-3: created. See: [Tier-2 record](tier2_roster/tier2_standards_integrity_roster.md#s61r-002-standards-index-producer)
- [x] analyze_standards_index_gaps.py — Tier-2 DONE. HOP-compliant. pytest: 7. mypy: OK. Tier-3: created. See: [Tier-2 record](tier2_roster/tier2_standards_integrity_roster.md#s61r-003-standards-index-gap-producer)
- [x] diff_standards_index.py — Tier-2 DONE. HOP-compliant. pytest: 2. mypy: OK. Tier-3: created. See: [Tier-2 record](tier2_roster/tier2_standards_integrity_roster.md#s61r-004-standards-index-diff-producer)
- [x] seed_standards_prompts.py — Tier-2 DONE. HOP-compliant. pytest: 2. mypy: OK. Tier-3: created. See: [Tier-2 record](tier2_roster/tier2_standards_integrity_roster.md#s61r-005-standards-prompt-seed-producer)
- [x] summarize_standards.py — Tier-2 DONE. HOP-compliant. pytest: 2. mypy: OK. Tier-3: created. See: [Tier-2 record](tier2_roster/tier2_standards_integrity_roster.md#s61r-006-standards-overview-summarizer)
- [x] run_standards_integrity.py — Tier-2 DONE. HOP-compliant. pytest: 2. mypy: 7 errors (nested closures — acceptable). Tier-3: created. See: [Tier-2 record](tier2_roster/tier2_standards_integrity_roster.md#s61r-001-standards-integrity-orchestrator)

**Stage 6.1 Gate Checklist (Tier-1):**

These are Stage 6.1 readiness gates after all Tier-2 DONE script gates are closed.

- [x] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`).
  See: [Stop-gates](tier2_roster/tier2_standards_integrity_roster.md#32-stop-gates-and-implementation-checklists)
- [x] No pointer artifacts (`latest_*` / `current_*`).
  See: [Stop-gates](tier2_roster/tier2_standards_integrity_roster.md#32-stop-gates-and-implementation-checklists)
- [x] Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`).
  See: [Contract snapshot](tier2_roster/tier2_standards_integrity_roster.md#23-current-vs-target-contract-snapshot-stage-61)
- [x] Tier-3 eligible (Stage 6.1 Tier-2 depth captured; ready for Tier-3 extraction).
  See: [Records index](tier2_roster/tier2_standards_integrity_roster.md#311-records-index)

**Target contract (locked decisions):**

- Output root migrates to `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is present: `manifest.json`, `summary.md`, `telemetry.json`.
- Discovery is timestamp-based only (no pointer files such as `latest_*`).

**Current evidence (Stage 6.1 — HOP-compliant as of 2026-01-03):**

- All Stage 6.1 scripts emit HOP-compliant output roots:
  `.repo_studios/reports/healthview/<class>_reports/<topic>/<YYYYMMDD-HHMM>/`
- All scripts emit base package: `manifest.json`, `summary.md`, `telemetry.json`.
- No pointer artifacts (`latest_*`) are created.
- Timestamp slug format unified: `YYYYMMDD-HHMM` (UTC).
- Details and evidence live in the Stage 6.1 Tier-2 roster:
  [Current vs Target snapshot](tier2_roster/tier2_standards_integrity_roster.md#23-current-vs-target-contract-snapshot-stage-61),
  [Stop-gates](tier2_roster/tier2_standards_integrity_roster.md#32-stop-gates-and-implementation-checklists).

**What Happens (Tier-1) — shim:**

- Keep this Stage 6.1 section as a high-level narrative of what the orchestrator does.
- Do not copy Tier-2 workstreams or per-script evidence into Tier-1.

**Section Order (Tier-1) — shim:**

- Tier-2 references → Script Gate Summary (leaf scripts first, orchestrator last) →
  Stage gate checklist (after all Tier-2 DONEs) → Overview/Orchestrator/Invoked Scripts.

**Overview:**  
The Standards Integrity orchestrator chains five delegated scripts in sequence
(index generation → gap analysis → diff → prompt seeding → summarization). Together (six scripts
including the orchestrator), they scan standards markdown files, analyze coverage gaps, track
changes over time, seed standards prompts for AI agents, and synthesize compliance metrics.
Runtime typically lands between 5-8 minutes, with diff scopes and prompt generation driving the
upper bound. This Stage 6.1 orchestrator supersedes older ad-hoc entry points (now retired):
`orchestrators/run_standards_gap_suite.py` and `orchestrators/run_standards_index_cli.py`.
(817 lines)

**Orchestrator:**
[run_standards_integrity.py](../../../command_center/scripts/orchestrators/run_standards_integrity.py)

**Invoked Scripts (5):**

| Script | Category | Purpose | Tier-3 YAML |
| ------ | -------- | ------- | ----------- |
| `generate_standards_index.py` | Producer | Scan `docs/standards/`, extract rules, build compliance index with integrity hash | TBD |
| `analyze_standards_index_gaps.py` | Producer | Identify standards coverage gaps across markdown sources, build gap report with candidate suggestions | TBD |
| `diff_standards_index.py` | Producer | Compare current vs. baseline index, identify additions/removals/changes, optional fail-on policy | TBD |
| `seed_standards_prompts.py` | Producer | Generate AI agent prompt bundles from standards with configurable formats (text/yaml/json) | TBD |
| `summarize_standards.py` | Summarizer | Synthesize standards metrics, compliance scores, gap analysis | TBD |

**Inputs:**

- `--index-output-dir`: Index artifact directory
  (default: `.repo_studios/reports/healthview/producer_reports/standards_index/`)
- `--index-path`: Path to the canonical standards index YAML
  (default: `.repo_studios/scripts/repo_standards_index.yaml`; no legacy pointer fallback)
- `--categories-path`: Standards categories YAML
  (default: `.repo_studios/scripts/standards_categories.yaml`)
- `--gap-output-dir`: Gap analysis output directory
  (default: `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/`)
- `--diff-output-dir`: Diff artifact directory
  (default: `.repo_studios/reports/healthview/producer_reports/standards_index_diff/`)
- `--diff-old-index`: Baseline index for diff
  (optional, skips diff step if not provided)
- `--diff-fail-on`: Fail policy forwarded to diff script (default: `any`)
- `--prompt-output-dir`: Prompt seed artifact directory
  (default: `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/`)
- `--prompt-include-warn`: Include warn-severity rules in prompt seed
- `--prompt-formats`: Artifact formats (text/yaml/json)
- `--gap-max-show`: Maximum gap candidates to log per source (default: 8)
- `--pending-path`: Pending standards YAML path
  (default: `.repo_studios/scripts/repo_standards_pending.yaml`)

**Outputs:**

- Orchestrator bundle:
  `.repo_studios/reports/healthview/orchestrator_reports/standards_integrity/<YYYYMMDD-HHMM>/`
  - `manifest.json`, `summary.md`, `telemetry.json`
- Index artifacts:
  `.repo_studios/reports/healthview/producer_reports/standards_index/<YYYYMMDD-HHMM>/`
- Gap artifacts:
  `.repo_studios/reports/healthview/producer_reports/standards_index_gaps/<YYYYMMDD-HHMM>/`
- Diff artifacts:
  `.repo_studios/reports/healthview/producer_reports/standards_index_diff/<YYYYMMDD-HHMM>/`
- Prompt artifacts:
  `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/<YYYYMMDD-HHMM>/`
- Overview artifacts:
  `.repo_studios/reports/healthview/summarizer_reports/standards_overview/<YYYYMMDD-HHMM>/`

**Execution Notes:**

- **Dynamic imports:** Lines 286-296 (`_load_callable()`) – orchestrator loads each script's
  `run()` or `main()` helper via importlib, matching the library-integration pattern
- **Pipeline structure:** Lines 730-736 (5-step pipeline: index → gap → diff → prompts → summary)
- **Conditional diff:** Line 638 (`step_skipped()`) – diff step skipped if `--diff-old-index`
  not provided, no error raised
- **Fail-fast on summary:** Line 736 (`continue_on_failure=False`) – pipeline aborts if
  summarizer fails
- **Execution functions:** Lines 332-361 (`_execute_index()`), 364-413 (`_execute_gap()`),
  416-467 (`_execute_diff()`), 470-512 (`_execute_prompts()`), 515-522 (`_execute_summary()`)
- **Artifact retention:** HealthView topic=3 (line 259), index=5 (line 250), gap=5 (line 254),
  diff=10 (line 255), prompt=5 (line 256)
- **Script registration:** Lines 525-531 (registers 6 scripts: orchestrator + 5 delegated scripts)
- **Telemetry assembly:** Lines 739-768 (builds pipeline telemetry, relativizes artifact paths,
  populates manifest)
- **Report naming audit:** Lines 803-811 (enforces viewer/topic/timestamp/artifact naming
  standards)
- **Timestamp handling:** Lines 257-268 (`_parse_timestamp()`) – accepts ISO8601 via `--timestamp`
  or defaults to UTC now
- **Path resolution:** Lines 270-278 (`_resolve_optional_path()`) – handles
  absolute/relative/repo-relative paths for optional diff baseline
- **Prompt configurability:** Lines 495-506 (formats deduplication, include-warn flag, artifact
  format selection)

**Status:** `Operational (partial hardening)` – 5-script pipeline verified, 5-8 min runtime
confirmed, conditional diff skip logic validated, retention defaults documented

**Planned Expansions:**

- **Stage 6.2: Standards Rules Extraction** – Integrate `extract_standards_rules.py`
  for deeper compliance validation (gap identified in coverage analysis;
  `analyze_standards_index_gaps.py` now confirmed as part of Stage 6.1 pipeline)

**Known Gaps:**

- Diff step is optional and skipped silently if baseline not provided;
  may surprise users expecting diffs
- Prompt formats default to None if not specified;
  unclear whether all formats should be generated by default
- Gap analysis logging capped at `--gap-max-show` candidates;
  complete gap list requires reading artifacts

**Evidence:**

- Code: `.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`
  (lines 1-817)
  - Runtime note: Lines 1-11 (docstring: "Runtime typically lands between five and eight
    minutes, with diff scopes and prompt generation driving the upper bound")
  - Script constants: Lines 56-60 (5 script paths), 62-70 (5 module names)
  - Default paths: Lines 72-80 (8 path constants including index, gap, diff, prompt, pending,
    healthview root)
  - Run prefixes: Lines 82-84 (3 prefixes for timestamped artifact directories)
  - PathsConfig: Lines 100-125 (8 path specs with ensure_dir flags)
  - KeepParameters: Lines 128-134 (5 retention parameters)
  - OptionsConfig: Lines 137-145 (5 keep specs with minimum=1)
  - Options dataclass: Lines 148-161 (13 option fields including diff_old_index, prompt_formats)
  - Outcome dataclasses: Lines 164-189 (5 outcome types for index/gap/diff/prompt/summary steps)
  - Argument parsing: Lines 192-241 (13 path arguments, 5 retention arguments, 5 behavior flags)
  - Timestamp parsing: Lines 244-252 (`_parse_timestamp()`)
  - Path resolution: Lines 255-263 (`_resolve_optional_path()`)
  - build_paths: Line 266 (delegates to library `build_standard_paths()`)
  - build_options: Lines 269-281 (retention via library, custom diff/prompt config)
  - Dynamic imports: Lines 286-296 (`_load_callable()`)
  - Execution functions: Lines 332-361 (`_execute_index()`), 364-413 (`_execute_gap()`),
    416-467 (`_execute_diff()`), 470-512 (`_execute_prompts()`), 515-522 (`_execute_summary()`)
  - Script registration: Lines 525-531 (6 scripts including orchestrator)
  - Markdown summary: Lines 534-578 (`_summarize_markdown()` with step outcomes)
  - run() function: Lines 581-813 (pipeline execution, telemetry, manifest assembly,
    report bundle write)
  - Pipeline definition: Lines 730-736 (5 TopicStep definitions, fail-fast on summary)
  - Telemetry assembly: Lines 739-768 (relativized paths, artifact tracking)
  - Report artifacts: Lines 796-801 (3 artifacts: manifest.json, summary.md, telemetry.json)
  - Report naming audit: Lines 803-811 (enforces viewer/topic/timestamp/artifact standards)
- Tests: `.repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py`

**Evidence Links:**

- [.repo_studios/scripts/producers/generate_standards_index.py](../../../scripts/producers/generate_standards_index.py)
- [.repo_studios/command_center/scripts/cc_producers/analyze_standards_index_gaps.py](../../../command_center/scripts/cc_producers/analyze_standards_index_gaps.py)
- [.repo_studios/scripts/producers/diff_standards_index.py](../../../scripts/producers/diff_standards_index.py)
- [.repo_studios/scripts/producers/seed_standards_prompts.py](../../../scripts/producers/seed_standards_prompts.py)
- [.repo_studios/scripts/summarizers/summarize_standards.py](../../../scripts/summarizers/summarize_standards.py)
- [.repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py](../../../tests/tests_command_center/standards_integrity/test_run_standards_integrity.py)

---

## 10. Stage 7 – Running the Complete Suite

> **Purpose:** Execute all HealthView orchestrators sequentially via the meta-orchestrator
> to generate a full-suite diagnostic snapshot.

_Tier-2 references (depth lives here):_

- [Contract snapshot](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#23-current-vs-target-contract-snapshot-stage-7)
  — target vs current, bundle invariants, naming/paths
- [Stop-gates](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#32-stop-gates-and-implementation-checklists)
  — verification checks + failure signatures + next actions
- [Records index](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#311-records-index)
  — per-script inspection index + evidence links (Tier-2 holds proof)

**Stage 7 Script Gate Summary (Tier-1):**

- [x] Stage 1.1 — Test execution telemetry — complete.
  [Tier-2 record](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#s7r-002-test-execution-telemetry)
- [x] Stage 2.1 — Docs health overview — complete.
  [Tier-2 record](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#s7r-003-docs-health)
- [x] Stage 3.1 — Fault diagnostics overview — complete.
  [Tier-2 record](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#s7r-004-fault-diagnostics)
- [ ] Stage 4.1 — Dependency import hygiene — pending until Tier-2 DONE is checked —
  [Tier-2 record](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#s7r-005-dependency-import-hygiene)
- [ ] Stage 5.1 — Monkey patch oversight — pending until Tier-2 DONE is checked —
  [Tier-2 record](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#s7r-006-monkey-patch-oversight)
- [ ] Stage 6.1 — Standards integrity — pending until Tier-2 DONE is checked —
  [Tier-2 record](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#s7r-007-standards-integrity)

**Stage 7 Stage Gate Checklist (Tier-1):**

- [ ] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`) — pending until Tier-2
  DONE is checked —
  [Contract snapshot](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#23-current-vs-target-contract-snapshot-stage-7)
- [ ] No pointer artifacts (`latest_*` / `current_*`) — pending until Tier-2 DONE is checked —
  [Stop-gates](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#32-stop-gates-and-implementation-checklists)
- [ ] Output root aligned to HealthView contract:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/` — pending until Tier-2 DONE is
  checked —
  [Contract snapshot](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#23-current-vs-target-contract-snapshot-stage-7)
- [ ] Tier-3 eligible (Tier-2 depth captured; ready for Tier-3 extraction) — pending until Tier-2
  DONE is checked —
  [Stop-gates](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#32-stop-gates-and-implementation-checklists)

**Target contract (locked decisions):**

- Stage 7 is a meta-orchestrator that runs Stages 1.1–6.1 sequentially (fail-fast),
  producing a full-suite snapshot.
- All emitted HealthView bundles (meta + delegated topic bundles) converge on the canonical root:
  `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`.
- Base package is stable: `manifest.json`, `summary.md`, `telemetry.json`.
- Pointer artifacts (`latest_*`, `current_*`) are disallowed.

See Tier-2 for the authoritative contract snapshot and stop-gates:
`tier2_full_suite_overview_roster.md` →
[Contract snapshot](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#23-current-vs-target-contract-snapshot-stage-7)
and
[Stop-gates](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#32-stop-gates-and-implementation-checklists).

**Current evidence (Stage 7):**

- The Stage 7 chain exists and emits the expected base package.
- Output root is currently observed under `.repo_studios/command_center/reports/<viewer>/<topic>/<YYYYMMDD-HHMM>/`.
- The root mismatch vs the canonical HealthView contract is treated as a stop-gate until remediated.

See Tier-2 for the repo-grounded evidence summary:
[Current vs Target Contract snapshot](../healthview_orchestration_pipeline/tier2_roster/tier2_full_suite_overview_roster.md#23-current-vs-target-contract-snapshot-stage-7).

### 10.1 Meta-Orchestrator: Full Diagnostic Suite

**Overview:**
The `orchestrate_full_diagnostic.py` meta-orchestrator runs Stages 1.1–6.1 sequentially by importing
each topic orchestrator and invoking its `run(argv)` with shared configuration (`--repo-root`,
`--log-level`). Non-zero exit codes abort the remaining topics (fail-fast). Contract alignment and
proof live in Tier-2.

**Orchestrator:**  
[.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py](../../../command_center/scripts/orchestrators/orchestrate_full_diagnostic.py)

**Invoked Orchestrators (6):**

1. `run_test_execution_telemetry.py` (Stage 1.1) – topic slug: `test-execution-telemetry`
1. `run_docs_health_overview.py` (Stage 2.1) – topic slug: `docs-health`
1. `run_fault_diagnostics_overview.py` (Stage 3.1) – topic slug: `fault-diagnostics`
1. `run_dependency_import_hygiene.py` (Stage 4.1) – topic slug: `dependency-import-hygiene`
1. `run_monkey_patch_oversight.py` (Stage 5.1) – topic slug: `monkey-patch-oversight`
1. `run_standards_integrity.py` (Stage 6.1) – topic slug: `standards-integrity`

**Execution Notes:**

- Sequential execution only; topic orchestrators are invoked directly (dynamic import, no subprocess).
- Shared `--repo-root` and `--log-level` are threaded through every topic.
- Output rooting and pruning behavior are treated as contract items and are validated via Tier-2 stop-gates.

**Inputs:**

- Repository root path (auto-detected or via `--repo-root`)
- Shared log level configuration (default: INFO)
- Optional timestamp override (ISO 8601 format)

**Outputs:**

- Meta-level HealthView bundle + the six delegated topic bundles.
- Target vs current bundle roots are tracked in Tier-2 (Stage 7 contract snapshot).

**Status:** `Operational – Partial hardening complete`

**Known Gaps:**

- Stage 7 still needs contract convergence (output rooting, pruning targets) and checklist closure.
- Treat all gap details and remediation steps as Tier-2 stop-gates.

**Evidence Links:**

- **Orchestrator:**
  [orchestrate_full_diagnostic.py](../../../command_center/scripts/orchestrators/orchestrate_full_diagnostic.py)
  (lines 1-554: dynamic imports, sequential execution, composite manifest)
- **Tests:**
  [test_orchestrate_full_diagnostic.py](../../../tests/tests_command_center/orchestrators/test_orchestrate_full_diagnostic.py)
  (integration tests with mocked topic orchestrators)

---

## 11. Stage 11 – Available Scripts (Holding Area)

> **Purpose:** Maintain a Tier-1 holding place for scripts that are _available to HealthView_ but
> not yet wired into the orchestrator blast-radius chain (Stages 1.1–7). Promotion into an
> orchestrator is intended to be a copy/paste wiring step plus a Tier-1 doc update.

### 11.1 Available Scripts

_Tier-2 references (depth lives here):_

- Stage 11.1 Tier-2 roster: [tier2_roster/tier2_available_scripts_roster.md](tier2_roster/tier2_available_scripts_roster.md)
  - Contract snapshot: [Stage 11.1 contract snapshot](tier2_roster/tier2_available_scripts_roster.md#23-current-vs-target-contract-snapshot-stage-111)
  - Stop-gates: [Stage 11.1 stop-gates](tier2_roster/tier2_available_scripts_roster.md#32-stop-gates-and-implementation-checklists)
  - Records index: [Stage 11.1 records index](tier2_roster/tier2_available_scripts_roster.md#311-records-index)
- Script inventory and provenance: [script_inventory_architecture.md](../../../scripts/script_inventory_architecture.md)

**Stage 11.1 Script Gate Summary (Tier-1):**

_Producers — Orchestrator-Promoted (6 scripts in `run_available_scripts_oversight.py`):_

- [x] `validate_import_boundaries.py` — ✅ HOP-compliant; ✅ promoted to orchestrator (Phase 1).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-005-validate_import_boundariespy)
- [x] `validate_inventory.py` — ✅ HOP-compliant; ✅ promoted to orchestrator (Phase 1).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-008-validate_inventorypy)
- [x] `generate_lizard_report.py` — ✅ HOP-compliant; ✅ promoted to orchestrator (Phase 1).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-011-generate_lizard_reportpy)
- [x] `render_inventory_views.py` — ✅ HOP-compliant; ✅ promoted to orchestrator (Phase 1).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-010-render_inventory_viewspy)
- [x] `check_inventory_health.py` — ✅ HOP-compliant; ✅ promoted to orchestrator (Phase 1).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-007-check_inventory_healthpy)

_Consumers — Orchestrator-Promoted:_

- [x] `generate_anchor_health_report.py` — ✅ HOP-compliant; ✅ promoted to orchestrator (Phase 2).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-001-generate_anchor_health_reportpy)

_Utilities (not directly orchestrated — Tier B):_

- [x] `configure_faulthandler_runtime.py` — utility; invoked by other scripts (classified, no changes needed).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-002-configure_faulthandler_runtimepy)
- [x] `dump_faulthandler_snapshot.py` — utility; invoked by other scripts (classified, no changes needed).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-003-dump_faulthandler_snapshotpy)
- [x] `fault_run_analysis.py` — utility; invoked by other scripts (classified, no changes needed).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-004-fault_run_analysispy)

_Libraries (import-only; no CLI — Tier B):_

- [x] `extract_standards_rules.py` — library module; no CLI entry point (classified).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-006-extract_standards_rulespy)
- [x] `test_log_analysis.py` — library module; no CLI entry point (classified).
  See: [Tier-2 record](tier2_roster/tier2_available_scripts_roster.md#asr-013-test_log_analysispy)

**Stage 11.1 Gate Checklist (Tier-1):**

These are Stage 11.1 promotion gates when a script is picked up by an orchestrator.

- [x] Base package complete (`manifest.json`, `summary.md`, `telemetry.json`) when the script is a
  bundle-emitting stage participant.
- [x] No pointer artifacts (`latest_*` / `current_*`) in the promoted bundle surface.
- [x] Output root aligned to HOP contract
  (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`)
  when the script emits HealthView bundles.
- [x] Tier-3 eligible once Tier-2 depth exists (a Tier-2 roster is created for the new vertical).
- [x] Orchestrator implemented (`run_available_scripts_oversight.py`) with 6-script pipeline.
- [x] Phase 4 compliance: Tier-3 YAML + build doc for all 6 orchestrated scripts.

**Target contract (locked decisions):**

- “Available scripts” are discoverable, stable repo assets that are _eligible_ for HealthView use
  but are not yet part of the orchestrator blast-radius chain.
- Promotion is performed by wiring the script into an appropriate orchestrator (copy/
  paste integration) and updating this Tier-1 document to move the reference from Stage 11.1 into
  the relevant stage narrative/matrix row.
- Scripts do not move on disk; only the Tier-1 references and orchestrator wiring change.

**Current evidence (Stage 11.1):**

_Validated 2026-01-28 — orchestrator operational with full test suite:_

**Orchestrator:** `run_available_scripts_oversight.py` (12/12 tests passing)

**Orchestrated scripts (6):**

| Phase | Script | Output Path | Status |
|-------|--------|-------------|--------|
| 1 | `validate_import_boundaries.py` | `.repo_studios/reports/healthview/producer_reports/import_boundary/<ts>/` | ✅ |
| 1 | `check_inventory_health.py` | `.repo_studios/reports/healthview/producer_reports/inventory_health/<ts>/` | ✅ |
| 1 | `validate_inventory.py` | `.repo_studios/reports/healthview/producer_reports/validate_inventory/<ts>/` | ✅ |
| 1 | `render_inventory_views.py` | `.repo_studios/reports/healthview/producer_reports/inventory_overview/<ts>/` | ✅ |
| 1 | `generate_lizard_report.py` | `.repo_studios/reports/healthview/producer_reports/lizard_complexity/<ts>/` | ✅ |
| 2 | `generate_anchor_health_report.py` | `.repo_studios/reports/healthview/consumer_reports/anchor_health/<ts>/` | ✅ |

**Phase 4 documentation compliance (all 6 scripts):**

- Tier-3 YAML created at `tier3_scripts/available_scripts_oversight/`
- Build doc created at `tier2_roster/working_docs/`
- Tier-2 roster records updated with orchestrator_integration block
- DB integration docs verified/fixed

**Classified but not orchestrated (Tier B — libraries/utilities):**

- `extract_standards_rules.py` — library module (no CLI)
- `test_log_analysis.py` — library module (no CLI)
- `configure_faulthandler_runtime.py` — utility (invoked by other scripts)
- `dump_faulthandler_snapshot.py` — utility (invoked by other scripts)
- `fault_run_analysis.py` — utility (invoked by other scripts)

**Meaning of "available scripts" (Tier-1 contract):**

- Stage 11.1 scripts are now orchestrated via `run_available_scripts_oversight.py`.
- The orchestrator runs as part of the HealthView diagnostic chain.
- Tier B items (libraries/utilities) remain classified but not directly invoked by the orchestrator.

**Overview:**  
Stage 11.1 is now **operational**: the `run_available_scripts_oversight.py` orchestrator manages
6 HOP-compliant scripts (5 producers + 1 consumer) with full Phase 4 documentation compliance.
Tier B items (libraries/utilities) are classified but not directly orchestrated.

**Orchestrator location:** `.repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py`  
**Tier-2 orchestrator roster:** [tier2_available_scripts_orchestrator_roster.md](tier2_roster/tier2_available_scripts_orchestrator_roster.md)

---

## 12. Stage 12 – Script Development Templates (Governance Staging)

> **Purpose:** Temporary staging area for script requirement templates that standardize
> the design, build, test, and QA process for HealthView scripts. This stage will detach
> and migrate to the Jarvis governance index when Repo Studios docks.

_Tier-2 references (depth lives here):_

- Stage 12.1 Producer Template: [tier2_producer_template.md](tier2_roster/templates/tier2_producer_template.md)
- Stage 12.2 Consumer Template: [tier2_consumer_template.md](tier2_roster/templates/tier2_consumer_template.md)
- Stage 12.3 Aggregator Template: [tier2_aggregator_template.md](tier2_roster/templates/tier2_aggregator_template.md)
- Stage 12.4 Summarizer Template: [tier2_summarizer_template.md](tier2_roster/templates/tier2_summarizer_template.md)
- Stage 12.5 Orchestrator Template: [tier2_orchestrator_template.md](tier2_roster/templates/tier2_orchestrator_template.md)
- Stage 12.6 Utility Template: [tier2_utility_template.md](tier2_roster/templates/tier2_utility_template.md)
- Stage 12.7 Promotion Template: [tier2_promotion_template.md](tier2_roster/templates/tier2_promotion_template.md)
- Templates README: [README.md](tier2_roster/templates/README.md)
- Stage 11.1 Available Scripts Roster: [tier2_available_scripts_roster.md](tier2_roster/tier2_available_scripts_roster.md)
- Stage 11.1 Orchestrator Roster: [tier2_available_scripts_orchestrator_roster.md](tier2_roster/tier2_available_scripts_orchestrator_roster.md)

**Implementation Plan:**
[stage12_template_development_plan.md](implementation_plans/stage12_template_development_plan.md)

**Stage 12 Gate Checklist (Tier-1):**

- [x] 12.1 Producer template extracted and validated
- [x] 12.2 Consumer template extracted and validated
- [x] 12.3 Aggregator template extracted and validated
- [x] 12.4 Summarizer template extracted and validated
- [x] 12.5 Orchestrator template extracted and validated
- [x] All templates linked from this section
- [x] 12.6 Utility template extracted and validated (`tier2_utility_template.md`)
- [x] 12.7 Promotion template extracted and validated (`tier2_promotion_template.md`)
- [x] Stage 11.1 orchestrator implemented and operational (2026-01-28)
- [ ] Stage 11.1 orchestrator wired to Stage 7 meta-orchestrator (pending)
- [ ] Existing Stage 1.1 scripts refactored to template standards

**Target contract (locked decisions):**

- Templates capture the full lifecycle: design → build → test → tier3.yaml → wiring → QA → docs
- Working documents live in `/.repo_studios/docs/archives/` with `status: active` during work
- Completed work transfers to assigned Tier-2 orchestrator roster
- Archived working documents retain `status: archived` for audit trail
- Templates evolve through iteration (each script improves the template design)

**Governance destiny:**

- Stage 12 is explicitly temporary; it will detach and migrate to the Jarvis governance index
  when Repo Studios docks with the parent repository
- Templates for RawView and CommandView may be added later but are out of scope for initial work

**Current evidence (Stage 12):**

- Implementation plan: `implementation_plans/stage12_template_development_plan.md` — Phases 1-5 complete
- Stage 11.1 Available Scripts roster: `tier2_roster/tier2_available_scripts_roster.md` — 11 scripts processed
- Stage 11.1 Orchestrator roster: `tier2_roster/tier2_available_scripts_orchestrator_roster.md` — operational
- Templates created: `tier2_roster/templates/` (7 templates: 5 tier-class + utility + promotion)
- Phase 4 results (2026-01-28): 6 orchestrated scripts with full documentation compliance
- Orchestrator: `run_available_scripts_oversight.py` — 12/12 tests passing

---

## 13. Snapshot & Stage Matrix

### 13.1 Pipeline Snapshot

**Current State (2026-01-28):**  

All eight maturity domain orchestrators (Stages 1–7 + Stage 11) are **operational** and produce
timestamped HealthView bundles. Stage 12 (Script Development Templates) is complete with 7 templates.

**Orchestrator coverage:**

- **Stages 1–6:** 6 maturity domain orchestrators operational (partial hardening complete)
- **Stage 7:** Meta-orchestrator chains Stages 1–6 sequentially
- **Stage 11:** Available Scripts orchestrator operational (6 scripts, 12/12 tests)
- **Stage 12:** 7 templates complete (5 tier-class + utility + promotion)

**Hardening status:**

- **Stage 1 (Test Execution Telemetry):** Pass B complete – code-verified 6-script pipeline,
  artifact retention, dynamic imports, 5-6 min runtime
- **Stage 2 (Docs Health Overview):** Pass B complete – code-verified 8-script pipeline,
  skip flags (9 CLI options), report naming guardrails, 6-8 min runtime
- **Stage 3 (Fault Diagnostics Overview):** Pass B complete – code-verified 3-script pipeline
  (corrected from 2), 3-5 min runtime, special reuse/override flags
- **Stage 4 (Dependency & Import Hygiene):** Pass B complete – code-verified 5-script pipeline
  (4 producers + 1 utility), 7-11 min runtime, 6 skip flags, batch cleanup dry-run capability,
  fail-tolerant execution
- **Stage 5 (Monkey Patch Oversight):** Pass B complete – code-verified 4-script pipeline
  (producer → consumer → aggregator → summarizer + 1 utility), 4-7 min runtime, Git enrichment,
  trend analysis (max 20 runs)
- **Stage 6 (Standards Integrity):** Pass B complete – code-verified 5-script pipeline
  (index → gap → diff → prompts → summary), 5-8 min runtime, conditional diff skip,
  prompt format configurability
- **Stage 7 (Meta-Orchestrator):** Pass B complete – code-verified sequential execution,
  fail-fast strategy, composite manifest generation
- **Stage 11 (Available Scripts):** **Complete** – 6-script pipeline (5 producers + 1 consumer),
  Phase 4 documentation compliance, 12/12 tests passing
- **Stage 12 (Templates):** **Complete** – 7 templates in `tier2_roster/templates/`
- **All core stages (1–7):** Phase 2 Pass B hardening 100% complete – code validation done,
  awaiting Pass C polish (wording, transitions, cross-references)

**Meta-orchestrator (Stage 7)** chains all six Stage NN.1 orchestrators (1–6) sequentially via
dynamic imports. Stage 11.1 orchestrator is operational but not yet wired to Stage 7.

**Stage-chain contradictions are tracked explicitly.** Structural contract mismatches
(output roots, retention defaults, timestamp shapes, and stage-specific stop-gates) are tracked in
**Section 14** and the relevant Tier-2 rosters.

**Remaining gaps:**

- Stage 11.1 orchestrator not yet wired to Stage 7 meta-orchestrator
- Stage 1.1 scripts not yet refactored to Stage 12 template standards
- 5 Tier B items (libraries/utilities) classified but not directly orchestrated

**High-Level Risks:**

- Orchestrators lack CI/CD integration; currently manual-only execution (invoke via CLI or make target)
- No automated alerting when health metrics degrade below thresholds (metrics collected but not monitored)
- Sequential meta-orchestrator execution causes 20-30 min full-suite runtimes (parallel mode pending)
- Test coverage incomplete: only 4 of 8 orchestrators have dedicated integration tests

### 13.2 Stage Matrix

| Stage | Name | Orchestrators | Status | Top Gap | Evidence |
| ----- | ---- | ------------- | ------ | ------- | -------- |
| 1 | Testing Perspectives | 1.1 Test Execution Telemetry (6 scripts) | Operational (partial hardening) | Flaky test metrics not in health summary | [orchestrator](../../../command_center/scripts/orchestrators/run_test_execution_telemetry.py), [tests](../../../tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py) |
| 2 | Documentation Quality | 2.1 Docs Health Overview (8 scripts) | Operational (partial hardening) | Anchor health report not integrated | [orchestrator](../../../command_center/scripts/orchestrators/run_docs_health_overview.py), tests TBD |
| 3 | Runtime Reliability | 3.1 Fault Diagnostics Overview (3 scripts) | Operational (partial hardening) | Runtime utilities not integrated | [orchestrator](../../../command_center/scripts/orchestrators/run_fault_diagnostics_overview.py), [tests](../../../tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py) |
| 4 | Dependency Management | 4.1 Dependency & Import Hygiene (5 scripts) | Operational (partial hardening) | Import boundary validation not integrated | [orchestrator](../../../command_center/scripts/orchestrators/run_dependency_import_hygiene.py), [tests](../../../tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py) |
| 5 | Technical Debt Oversight | 5.1 Monkey Patch Oversight (5 scripts) | Operational (partial hardening) | Risk scoring incomplete | [orchestrator](../../../command_center/scripts/orchestrators/run_monkey_patch_oversight.py), [tests](../../../tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py) |
| 6 | Process Governance | 6.1 Standards Integrity (6 scripts) | Operational (partial hardening) | Standards rules extraction not integrated | [orchestrator](../../../command_center/scripts/orchestrators/run_standards_integrity.py), [tests](../../../tests/tests_command_center/standards_integrity/test_run_standards_integrity.py) |
| 7 | Running Complete Suite | Meta-Orchestrator (chains 6 topics) | Operational (partial hardening) | Sequential execution only (no parallel mode) | [orchestrator](../../../command_center/scripts/orchestrators/orchestrate_full_diagnostic.py), [tests](../../../tests/tests_command_center/orchestrators/test_orchestrate_full_diagnostic.py) |
| 11 | Available Scripts Oversight | 11.1 Available Scripts (6 scripts) | **Operational** | Wire to Stage 7 meta-orchestrator | [orchestrator](../../../command_center/scripts/orchestrators/run_available_scripts_oversight.py), [tests](../../../tests/tests_command_center/orchestrators/test_run_available_scripts_oversight.py) |
| 12 | Script Development Templates | 12.1–12.7 Templates (7 templates) | **Complete** | Apply to Stage 1.1 scripts | [templates](tier2_roster/templates/), [plan](implementation_plans/stage12_template_development_plan.md) |

---

## 14. Contradiction Registry

| ID | Description | Sections Affected | Reality Source | Next Step |
| -- | ----------- | ----------------- | -------------- | --------- |
| CR-001 | Tier-1 “current output root” references `.repo_studios/command_center/reports/healthview/...` while HOP target contract requires `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`. | 1.2, 3.1, 3.4, stage I/O bullets | `REPORT_NAMING_STANDARDS.md`, current orchestrator outputs | Keep Tier-1 explicit about “current vs target” until code migration lands; update Stage 1.1 Tier-2 vertical with per-script “current vs target” output tables. |
| CR-002 | Retention policy language drifts between “days,” per-script knobs, and bundle-level behavior across the pipeline docs. | 1.6, 3.4, stage retention bullets | Tier-2 rosters; current orchestrator CLI flags | Keep Tier-1 contract-level: retention is enforced in code; track current retention surfaces and evidence in Tier-2 rosters until migrations converge. |
| CR-003 | DB dual-write semantics are part of the HOP target contract; current implementation is partial and not end-to-end across all stages. | 1.2, 1.6, global controls | HOP locked decision; stage rosters (Tier-2) | Keep Tier-1 target contract language and treat DB as a stop-gate until best-effort DB persistence is consistently evidenced where required; Tier-2 rosters track current DB marker coverage by stage. |
| CR-004 | Timestamp directory shape varies across stages (`<YYYY-MM-DD>`, `<YYYYmmdd-HHmm>`, `<timestamp>`), which makes discovery ambiguous. | 1.2, stage output bullets | Stage tables and output examples in this Tier-1 doc | Standardize Tier-1 narrative to use `<timestamp>` consistently; push exact formatting requirements into Tier-2 verticals and Tier-3 artifacts doc. |
| CR-005 | Stage 1.1 base package is incomplete (missing required `summary.md` in the HealthView bundle). | 4.1 | Stage 1.1 Tier-2 roster | Treat as a stop-gate for Stage 1.1 contract compliance; track closure in Tier-2 stop-gates and update Tier-1 when resolved. |
| CR-006 | Stage 1.1 emits pointer artifacts (`latest_*`) in downstream outputs (violates “no mutable pointers”). | 4.1 | Stage 1.1 Tier-2 roster | Treat as a stop-gate for Stage 1.1 contract compliance; remove pointers during migration and close the contradiction when Tier-2 evidence confirms. |
| CR-007 | Stage 2.1 retains split intermediate output roots (producer/aggregator reports) during migration rather than a single HOP-rooted bundle surface. | 5.1 | Stage 2.1 Tier-2 roster | Treat as a stop-gate until output roots converge; rely on Tier-2 evidence for current roots and close when migrations land. |
| CR-008 | Stage 2.1 emits pointer artifacts (`latest_*`) in intermediate outputs (violates “no mutable pointers”). | 5.1 | Stage 2.1 Tier-2 roster | Treat as a stop-gate; close via Tier-2 stop-gates when pointers are removed and evidence confirms. |
| CR-009 | ~~Stage 3.1 current bundle writes land under a CommandView-rooted path (viewer/root mismatch vs HealthView/HOP contract).~~ | 6.1 | Stage 3.1 Tier-2 roster | **CLOSED (2026-01-06):** Stage 3.1 pipeline output roots align to the HOP contract (`.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`). |
| CR-010 | Stage 4.1 remains on the current output root (`.repo_studios/command_center/reports/...`) rather than the HOP contract root. | 7.1 | Stage 4.1 Tier-2 roster | Track as a stop-gate in Tier-2; update Tier-1 once output roots align and evidence confirms. |
| CR-011 | ~~Stage 5.1 mixes run slug formats and uses pointer artifacts (`latest_*`) across pipeline outputs.~~ | 8.1 | Stage 5.1 Tier-2 roster | **CLOSED (2026-01-03):** All scripts now use `YYYYMMDD-HHMM` slug format; pointer artifacts removed. |
| CR-012 | Stage 6.1 output roots and timestamp formats are inconsistent across the chain (viewer/root split; prompt seed uses a different run id shape). | 9.1 | Stage 6.1 Tier-2 roster | Treat as a stop-gate; close via Tier-2 once outputs converge on the HOP contract and evidence confirms. |

---

## 15. Tier-2 Document Index

**Tier-2 (Roster) Documents (per-orchestrator BEGIN → END):**

- [tier2_test_execution_telemetry_roster.md](tier2_roster/tier2_test_execution_telemetry_roster.md)
  – Stage 1.1 deep dive
- [tier2_docs_health_overview_roster.md](tier2_roster/tier2_docs_health_overview_roster.md)
  – Stage 2.1 deep dive
- [tier2_fault_diagnostics_overview_roster.md](tier2_roster/tier2_fault_diagnostics_overview_roster.md)
  – Stage 3.1 deep dive
- [tier2_dependency_import_hygiene_roster.md](tier2_roster/tier2_dependency_import_hygiene_roster.md)
  – Stage 4.1 deep dive
- [tier2_monkey_patch_oversight_roster.md](tier2_roster/tier2_monkey_patch_oversight_roster.md)
  – Stage 5.1 deep dive
- [tier2_standards_integrity_roster.md](tier2_roster/tier2_standards_integrity_roster.md)
  – Stage 6.1 deep dive
- [tier2_full_suite_overview_roster.md](tier2_roster/tier2_full_suite_overview_roster.md)
  – Stage 7 (meta-orchestrator) deep dive
- [tier2_available_scripts_roster.md](tier2_roster/tier2_available_scripts_roster.md)
  – Stage 11.1 (holding roster) deep dive
- [tier2_available_scripts_orchestrator_roster.md](tier2_roster/tier2_available_scripts_orchestrator_roster.md)
  – Stage 11.1 orchestrator deep dive (pending creation)

**Tier-2 (Template) Documents (script development lifecycle):**

- Stage 12.1 Producer Template: TBD
- Stage 12.2 Consumer Template: TBD
- Stage 12.3 Aggregator Template: TBD
- Stage 12.4 Summarizer Template: TBD
- Stage 12.5 Orchestrator Template: TBD

**Tier-3 (YAML) Documents (per-script agent tools):**

- Tier-3 YAMLs are not yet created for this pipeline. Tier-2 rosters define the promotion bar and
  stop-gates that must be closed before Tier-3 artifacts are drafted.

**Related Architecture Documents:**

- [.repo_studios/scripts/README.md](../../../scripts/README.md)
  – Script tier responsibilities (producers, consumers, aggregators, orchestrators, summarizers)
- [REPORT_NAMING_STANDARDS.md](../../../../REPORT_NAMING_STANDARDS.md)
  – Bundle structure conventions (viewer/topic/timestamp/artifact layout)
- [std-global-python-engineering.md](../../standards/global/std-global-python-engineering.md)
  – Python engineering standards
- [std-global-markdown-authoring.md](../../standards/global/std-global-markdown-authoring.md)
  – Markdown authoring conventions
- [markdown.instructions.md](../../../../.github/instructions/markdown.instructions.md)
  – Markdown editing instructions for agents
- [pipeline_doc_tiers.instructions.md](../../../../.github/instructions/pipeline_doc_tiers.instructions.md)
  – Tier-1/2/3 documentation requirements

**Validation Suites:**

- [tests/tests_command_center/](../../../tests/tests_command_center/) – Orchestrator integration tests
- [tests/tests_producers/](../../../tests/tests_producers/) – Producer script tests
- [tests/tests_consumers/](../../../tests/tests_consumers/) – Consumer script tests
- [tests/tests_aggregators/](../../../tests/tests_aggregators/) – Aggregator script tests

---

## 16. Working / Future Notes

**Future enhancements (not yet scheduled):**

- When CI/CD integration lands, update Stage 7 meta-orchestrator section with GitHub Actions
  workflow details
- When automated alerting is implemented, revise Section 3.6 (Global Controls) to include alert
  threshold flags
- When parallel orchestrator execution is added, update Stage 7 with concurrency model
- When dashboard UI is built, add "Downstream Dependencies" bullet to Section 1.4 (Where)
- When performance test orchestrator (Stage 1.2) is implemented, update Stage 1 overview and
  matrix row
- When import boundary validation (Stage 4.2) is implemented, update Stage 4 Planned Expansions
  and matrix

---

## 17. Update Log & Evidence Tracking

| Date | Author / Steward | Change | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2026-01-28 | GitHub Copilot | **Stage 11 & 12 finalized:** Stage 11.1 orchestrator operational (6 scripts, 12/12 tests); Phase 4 documentation complete for all scripts (Tier-3 YAML + build docs); Stage 12 templates complete (7 templates); Tier-2 rosters promoted to `active` v1.0.0; Stage Matrix updated with Stages 11 & 12. | N/A | 570/580 suite; 12/12 orchestrator |
| 2026-01-25 | GitHub Copilot | Introduced Stage 12 (Script Development Templates) as governance staging; created implementation plan; renumbered downstream sections (Snapshot → 13, Contradictions → 14, Tier-2 Index → 15, Working Notes → 16, Update Log → 17); added Stage 11.1 orchestrator roster placeholder to Tier-2 index. | pending | pending |
| 2026-01-23 | GitHub Copilot | Stage 6.1 reality sync: corrected orchestrator output root and removed legacy index-pointer language from Tier-1 Stage 6.1 narrative and inputs/outputs. | 20260123-0152 | pytest Stage 6.1 focused suites (11 passed); doc-index |
| 2026-01-22 | GitHub Copilot | Stage 6.1 follow-up: corrected Stage Matrix script count for Standards Integrity to reflect current 6-script chain; regenerated doc-index artifacts after paired-doc drift cleanup. | 20260122-1218 | doc-index |
| 2026-01-06 | GitHub Copilot | Stage 3.1 follow-up: corrected Tier-1 Inputs/Outputs for `collect_faulthandler_reports.py` to use HealthView rawview + HOP bundle roots; verified Make target `studio-collect-faulthandler-reports` runs successfully (requires explicit `--repo-root` because `.repo_studios/scripts/.repo_studios/` exists and can confuse repo-root discovery). | 20260106-1502 | make studio-collect-faulthandler-reports; doc-index producer |
| 2026-01-04 | GitHub Copilot | Updated Stage 1.1 Inputs/Execution notes to reflect repo-root coverage defaults (`coverage.xml`) and snapshot-mode coverage refresh behavior (continue-on-error + recorded exit codes). | 20260104-1710 | doc-index; make studio-orchestrate-test-execution-telemetry |
| 2026-01-03 | GitHub Copilot | Stage 6.1 HOP refactor complete: S61R-005/006 artifact names, orchestrator default paths, stop-gates closed, Pass C complete. | pending | 26 passed (Stage 6.1 tests) |
| 2025-12-25 | GitHub Copilot | Closed Stage 1.1 script gate for `run_test_execution_telemetry.py` after Tier-2 DONE; validated Make target `studio-orchestrate-test-execution-telemetry` emits canonical HealthView bundles. | 20251225-0517 | make studio-orchestrate-test-execution-telemetry; doc-index |
| 2025-12-24 | GitHub Copilot | Closed Stage 1.1 script gate for `summarize_test_execution_telemetry.py` after Tier-2 DONE + Tier-3 YAML create/validate; refreshed doc-index. | 20251224-2318 | doc-index; pytest tier3_index (29 passed) |
| 2025-12-22 | GitHub Copilot | Closed Stage 1.1 script gate for `generate_test_log_health_report.py` after Tier-2 DONE; refreshed doc-index and confirmed deterministic selector advanced to the next Tier-2 record. | 20251222-0450 | doc-index; healthview-agent-next-compact |
| 2025-12-22 | GitHub Copilot | Closed Stage 1.1 script gate for `analyze_test_hardening.py` after Tier-2 DONE; refreshed doc-index and confirmed deterministic selector advanced to the next Tier-2 record. | 2025-12-22 | doc-index; healthview-agent-next-compact |
| 2025-12-22 | GitHub Copilot | Closed Stage 1.1 script gate for `collect_test_log_reports.py` after Tier-2 DONE + Tier-3 YAML draft/validation; refreshed doc-index + tier3 index outputs. | 20251222-0029 | doc-index; pytest tier3_index (28 passed) |
| 2025-12-21 | GitHub Copilot | Phase 5: added compact tool index to Section 0.1 (make targets + spec/schema/validator/runner/template paths); refreshed doc-index to confirm checkbox report remains stable. | 2025-12-21T13:29:43Z | N/A (doc-only; no code changes) |
| 2025-12-20 | GitHub Copilot | Seeded the Stage 11.1 Tier-2 roster and linked it from Tier-1 Stage 11.1 and the Tier-2 index; reran targeted anchor validation. | 20251220-2257 | markdown anchor validation (bundle 20251220-2257) |
| 2025-12-20 | GitHub Copilot | Introduced Stage 11 (Available Scripts holding area) using the Stage 1.1 gate layout; migrated planned/available script lists into Stage 11.1; renumbered downstream sections and updated internal section references; reran targeted anchor validation. | 20251220-2037 | markdown anchor validation (bundle 20251220-2037) |
| 2025-12-19 | GitHub Copilot | Replaced non-existent Tier-3 placeholder links with plain `TBD` text and corrected Fault Diagnostics evidence links to point at the actual `.repo_studios/scripts/...` + `.repo_studios/tests/...` locations; reran targeted anchor validation for the HealthView pipeline docs. | 20251219-0124 | markdown anchor validation (bundle 20251219-0123) |
| 2025-12-18 | GitHub Copilot | Hardened Tier-1 Sections 1–3 to explicitly separate current vs HOP target contract (output roots/discovery, bundle invariants, retention framing, DB best-effort dual-write) and populated Contradiction Registry entries. | 20251218-2328 | Doc-index producer; markdown anchor validation (bundle 20251218-2337) |
| 2025-12-12 | Repo Studios Core Team | Initial tier-1 skeleton generated from template (Phase 0 complete) | N/A (draft) | N/A |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 1 (Test Execution Telemetry) \u2013 updated script count to 6 (added summarizer), verified 5-6 min runtime, artifact retention defaults, dynamic imports, actual input/output paths from orchestrator code inspection | N/A (no doc-index yet) | Verified via code inspection: [run_test_execution_telemetry.py](../../../command_center/scripts/orchestrators/run_test_execution_telemetry.py) lines 1-670, [test_run_test_execution_telemetry.py](../../../tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py) lines 1-362 |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 7 (Meta-Orchestrator) \u2013 verified sequential execution via dynamic imports, 6-topic chain, fail-fast strategy, composite manifest generation, 20-30 min runtime expectations | N/A (no doc-index yet) | Verified via code inspection: [orchestrate_full_diagnostic.py](../../../command_center/scripts/orchestrators/orchestrate_full_diagnostic.py) lines 1-554, TOPIC_DEFINITIONS tuple with 6 entries |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 2 (Docs Health Overview) \u2013 verified 8-script pipeline, 6-8 min runtime, step skipping support, report naming guardrails via enforce_report_naming(), retention behavior enforced, execution order confirmed | N/A (no doc-index yet) | Verified via code inspection: [run_docs_health_overview.py](../../../command_center/scripts/orchestrators/run_docs_health_overview.py) lines 1-1095, 8 _execute_* functions (lines 394-710) |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 3 (Fault Diagnostics Overview) \u2013 corrected script count from 2 to 3 (added missing summarizer), verified 3-5 min runtime, special reuse/override flags (--reuse-report, --producer-top-frames), artifact retention defaults | N/A (no doc-index yet) | Verified via code inspection: [run_fault_diagnostics_overview.py](../../../command_center/scripts/orchestrators/run_fault_diagnostics_overview.py) lines 1-604, execution functions (lines 272-312, 315-371, 374-423), [test_run_fault_diagnostics_overview.py](../../../tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py) |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 4 (Dependency & Import Hygiene) \u2013 verified 5-script pipeline (4 producers + 1 utility), 7-11 min runtime, 6 skip flags (import-graph, typecheck, batch-cleanup opt-in, mypy-baselines opt-in, dependency patterns, skip-pyproject), batch cleanup dry-run capability (legacy shim retired), fail-tolerant execution (stop_on_failure=False) | N/A (no doc-index yet) | Verified via code inspection: [run_dependency_import_hygiene.py](../../../command_center/scripts/orchestrators/run_dependency_import_hygiene.py) lines 1-1111, execution functions (lines 437-468, 471-500, 503-543, 639-711, 714-742, 765-793), [test_run_dependency_import_hygiene.py](../../../tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py) |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 5 (Monkey Patch Oversight) \u2013 verified 4-script pipeline (producer \u2192 consumer \u2192 aggregator \u2192 summarizer) + 1 utility, 4-7 min runtime, step skipping support, optional Git enrichment, trend analysis support, producer configurability (context lines, strict mode, project packages, exclude patterns) | N/A (no doc-index yet) | Verified via code inspection: [run_monkey_patch_oversight.py](../../../command_center/scripts/orchestrators/run_monkey_patch_oversight.py) lines 1-735, execution functions (lines 303-361, 364-400, 403-449, 452-515), [test_run_monkey_patch_oversight.py](../../../tests/tests_command_center/orchestrators/test_run_monkey_patch_oversight.py) |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening: Stage 6 (Standards Integrity) – corrected script count from 4 to 5 (added missing analyze_standards_index_gaps.py producer), verified 5-8 min runtime, conditional diff skip logic, prompt format configurability (text/yaml/json), retention behavior enforced, 5-step pipeline (index → gap → diff → prompts → summary), fail-fast on summarizer | N/A (no doc-index yet) | Verified via code inspection: [run_standards_integrity.py](../../../command_center/scripts/orchestrators/run_standards_integrity.py) lines 1-817, execution functions (lines 332-361, 364-413, 416-467, 470-512, 515-522), [test_run_standards_integrity.py](../../../tests/tests_command_center/standards_integrity/test_run_standards_integrity.py) |
| 2025-12-12 | GitHub Copilot | Updated Stage Matrix with accurate test file paths (only 3 of 7 orchestrators have tests), updated Pipeline Snapshot to reflect partial hardening status, Phase 2 Pass B hardening 86% complete (Stages 1-5, 7), incremented version to v0.2.0 | N/A (no doc-index yet) | N/A |
| 2025-12-12 | GitHub Copilot | Phase 2 Pass B hardening 100% complete – all 7 stages code-verified with evidence, incremented version to v0.3.0. Ready for Phase 2 Pass C polish (wording, transitions, cross-references across all stages) | N/A (no doc-index yet) | N/A |
