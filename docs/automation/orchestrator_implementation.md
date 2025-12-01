---
title: Orchestrator Implementation Plan
status: draft
version: 2025-11-29
last_updated: 2025-11-30
owner: repo_studios_ai
tags:
  - automation
  - orchestrators
  - command-center
---

# Orchestrator Implementation Plan

This plan sequences the work required to deliver topic-oriented orchestrators, shared helpers, and
Healthview artifacts so Repo Studios diagnostics can graduate from the RFC to an executable
roadmap.

## Context

- The RFC in `docs/automation/orchestrator_topic_refactor_rfc.md` defines the topic topology,
  helper inventory, and Healthview slug separation from CommandView.
- `generate_commandview_inventory.py` captured the latest scripts snapshot at
  `.repo_studios/scripts/scripts_index/scripts_commandview_20251129-2102.json`, confirming 46
  tracked files, 897 functions, and 118 classes across the automation tree.
- CommandView remains the microscope on source files, while Healthview will expose orchestrator
  outputs via a new slug to avoid conflicts with existing JS and CSS bindings.

## Current Progress (2025-11-30)

- Duplicate scan aggregator (`command_center/scripts/aggregators/scan_duplicates.py`) now emits viewer/topic/timestamp bundles with mirrored index artifacts; integration tests pass and the command center pipeline incorporates the refactor.
- Function analysis summarizer (`command_center/scripts/summarizers/generate_function_analysis.py`) mirrors analysis JSON into the CommandView index while publishing viewer artifacts; producer tests and pipeline smoke checks are green.
- `docs/automation/orchestrator_implementation.md` and `script_inventory_architecture.md` capture the Command Center migrations, so prerequisites for topic orchestrator sequencing are in place.
- Healthview naming adoption work is partially complete: Command Center duplicate outputs comply with the approved slug/timestamp schema, and helper usage is consistent across the migrated scripts.
- Phase 2 helper scaffolding landed on 2025-11-30; the pipeline, summarizer runner, telemetry emitter, and catalog registry modules now ship with unit tests under `tests/tests_command_center` and align with the ASCII/logging conventions.
- Topic pipeline helper now emits structured logging for each step while catalog registry documentation stays ASCII-only, confirming compliance with repository logging and naming guidance.

## Implementation Objectives

1. Build topic orchestrators that exercise every managed script with consistent retention,
   logging, and artifact mirroring patterns.
2. Publish Healthview manifests that mirror the CommandView schema while using a distinct slug so
   viewer tabs stay isolated.
3. Deliver helper modules and documentation updates that keep agents, Command Center, and local
   developers aligned on usage and expectations.

## Deliverables

- New orchestrator modules under `.repo_studios/scripts/orchestrators/` for each agreed topic.
- Shared helper additions to `.repo_studios/command_center/scripts/libraries/` covering pipeline
  assembly, summarizer execution, telemetry emission, and catalog registry duties.
- Healthview manifest schema, Markdown summaries, and retention fixtures located in
  `.repo_studios/command_center/reports/healthview/`.
- Updated documentation: script inventory, automation guides, make targets, and manifest schema
  notes for Human and AI consumers.

## Legacy-to-Target Parity Matrix

| Existing Orchestrator | Current Scope | Key CLI Flags | Primary Outputs | Successor Topic(s) | Transition Notes |
| --- | --- | --- | --- | --- | --- |
| `.repo_studios/scripts/orchestrators/orchestrate_health_suite.py` | Health suite meta-runner chaining inventory, analysis, duplicate scan, fault artefacts, and summariser | `--log-level`, `--stop-on-error` (historical flag), implicit script order | `.repo_studios/reports/orchestrator_logs/health_suite_logs/<ts>/` (status.json, status.md, per-step logs); summariser bundles under `.repo_studios/reports/summarizer_reports/health_suite_summary_reports/` | Test Execution Telemetry, Fault Diagnostics, Meta-Orchestrator | Retire after new topics land; preserve CLI alias during migration; replicate status manifest structure in Healthview bundles. |
| `.repo_studios/scripts/orchestrators/run_fault_pipeline.py` | Faulthandler pipeline orchestrating producer + consumer with retention enforcement | `--runs-dir`, `--run-dir`, `--output-dir`, `--artifacts-to-keep`, `--log-level`, `--skip-producer`, `--skip-consumer` | `.repo_studios/reports/orchestrator_runs/fault_pipeline/` + mirrored Command Center bundles; producer/consumer outputs in `.repo_studios/reports/{producer,consumer}_reports/` | Fault Diagnostics | Consolidate CLI flags into topic runner; update tests in `tests/tests_command_center/faults/` and docs referencing the pipeline. |
| `.repo_studios/scripts/orchestrators/run_pytest_log_capture.py` | Pytest log capture automation with optional watch mode and retention pruning | `--repo-root`, `--output-dir`, `--artifacts-to-keep`, `--log-level`, `--pytest-args ...` | `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/<ts>/` plus Command Center mirrors | Test Execution Telemetry | Decommission once topic orchestrator calls producer chain; relocate fixtures in `tests/tests_orchestrators/test_run_pytest_log_capture.py`. |
| `.repo_studios/scripts/orchestrators/run_batch_cleanup.py` | Batch static-cleanup harness orchestrating lint, mypy, placeholder scans | `--log-level`, `-t/--target`, `--no-pytest`, `--max-workers`, `--extra-args` | `.repo_studios/reports/orchestrator_logs/batch_cleanup_logs/<ts>/` and tool-specific outputs (lint reports, placeholder TSV) | Dependency & Import Hygiene | Replace make target invocations; update automation docs referencing batch cleanup outputs; ensure placeholder debt plan still resolves to new location. |
| `.repo_studios/scripts/orchestrators/run_standards_gap_suite.py` | Standards gap detection orchestrator running index builders and gap analysers | `--repo-root`, `--log-level`, `--artifacts-to-keep`, `--skip-upstream` | `.repo_studios/command_center/reports/standards_gap_suite/` bundles and Markdown summary | Standards Integrity | Ensure gap analysis markdown migrates to Healthview; update standards docs and CI jobs using the suite. |
| `.repo_studios/scripts/orchestrators/run_standards_index_cli.py` | Wrapper for regenerating standards index and optional gap summary | `--repo-root`, `--log-level`, `--artifacts-to-keep`, positional selectors | `.repo_studios/reports/orchestratorRuns/standards_index_cli/` (legacy) and command center mirrors | Standards Integrity, Engineering Complexity Watch (if split) | Fold index regeneration into topic pipeline; archive CLI shim once make targets pivot to new entry point, documenting new slug usage. |

## Legacy Retirement Targets

- `.repo_studios/scripts/orchestrators/` modules listed above (and their `__main__` shims).
- Tests referencing legacy orchestrators, including suites under `tests/tests_command_center/`,
  `tests/tests_orchestrators/`, and any fixtures within `.repo_studios/tests/fixtures/`.
- Documentation touchpoints: `docs/automation/orchestrator_automation_hooks.md`,
  `.repo_studios/scripts/script_inventory_architecture.md`, makefile comments, and README snippets
  that instruct operators to run the existing entry points.
- Output directories currently populated by legacy orchestrators (for example,
  `.repo_studios/scripts/orchestrators/health_suite_*`, fault pipeline reports, standards gap
  reports) that must be redirected to the Healthview structure.
- Command Center configuration, dashboards, or agent scripts that reference old slugs or bundle
  names; ensure they shift to the Healthview manifest naming convention.

## Testing and Fixture Migration Requirements

- Tag existing orchestrator-specific fixtures so they can be migrated or deleted in lockstep with
  the new topic pipelines; avoid orphaned fixture directories.
- Rebaseline pytest snapshots and golden files as soon as new summarizers and manifest shapes
  stabilise to prevent flaky comparisons during the transition.
- Update CI configuration to swap legacy orchestrator smoke tests for the new topic-oriented test
  suites, keeping runtime budgets equivalent or better.
- Create regression cases that assert deprecated CLIs emit guidance pointing to the replacement
  targets until the shims are removed.

## Operational Impact Inventory

- **Make Targets**: `studio-orchestrate-health-suite`, `studio-orchestrate-fault-diagnostics` (`studio-run-fault-pipeline` alias),
  `studio-run-pytest-log-capture`, `studio-run-batch-cleanup`, `studio-run-standards-gap-suite`,
  `studio-run-standards-index` – document successor targets, note interim aliases, and prepare MR
  to adjust `.repo_studios/Makefile` with deprecation warnings.
- **CI Jobs**: Identify pipelines invoking the legacy orchestrators (health suite nightly,
  fault-pipeline smoke, standards gap weekly) and draft changes to point at topic runners and the
  meta orchestrator once live.
- **Agent Integrations**: Catalog agent prompts, scripts, and MPC workflows referencing legacy
  slugs so they can transition to Healthview manifest consumption.
- **Documentation Nodes**: Flag wiki pages, onboarding guides, and automation docs leveraging the
  superseded commands, adding TODO markers for the rollout PR checklist.
- **Telemetry Dashboards**: Inventory dashboards or notebooks that aggregate legacy bundle
  locations so migration to Healthview manifests can be scheduled alongside production roll-out.

## Legacy Removal Ticket Backlog (to be opened)

- `Ticket: Sunset orchestrate_health_suite.py` – remove module, update summaries, migrate make
  targets once Test Execution Telemetry and Fault Diagnostics reach parity.
- `Ticket: Sunset run_fault_pipeline.py` – fold CLI flags into Fault Diagnostics orchestrator and
  clean consumer/producer mirrors.
- `Ticket: Sunset run_pytest_log_capture.py` – migrate pytest fixtures, redirect logs, and retire
  make targets.
- `Ticket: Sunset run_batch_cleanup.py` – replace batch cleanup automation with Dependency & Import
  Hygiene topic runner; update placeholder debt documentation.
- `Ticket: Sunset run_standards_gap_suite.py` – shift standards reporting to Healthview and remove
  redundant summaries.
- `Ticket: Sunset run_standards_index_cli.py` – collapse CLI shim into Standards Integrity topic or
  Engineering Complexity Watch scope.

### Legacy Orchestrator Ticket Matrix (2025-11-30)

| Ticket Stub | Legacy Scope | Replacement Topic | Dependencies & Exit Criteria | Notes |
| --- | --- | --- | --- | --- |
| `Ticket: Sunset orchestrate_health_suite.py` | `orchestrate_health_suite.py`, health-suite fixtures, legacy summary wiring | Test Execution Telemetry (plus meta-orchestrator) | Meta-runner reproduces status manifest, Healthview summary online, legacy make target alias documented | Coordinate deprecation announcement with Command Center operators. |
| `Ticket: Sunset run_fault_pipeline.py` | `run_fault_pipeline.py`, fault smoke tests, command center mirrors | Fault Diagnostics | Topic orchestrator supports reuse flags, emits viewer/topic bundles, cleans legacy report directories | Ensure crash triage docs updated with new CLI. |
| `Ticket: Sunset run_pytest_log_capture.py` | `run_pytest_log_capture.py`, pytest log fixtures, orchestrator docs | Test Execution Telemetry | Topic orchestrator exposes pytest passthrough, retention knobs, CI smoke job flipped | Keep shim until new orchestrator validated across weekly runs. |
| `Ticket: Sunset run_batch_cleanup.py` | `run_batch_cleanup.py`, batch cleanup logs, placeholder debt docs | Dependency & Import Hygiene | Topic orchestrator sequences static cleanup tasks, replaces make targets, updates placeholder plan references | Align with placeholder remediation milestones prior to removal. |
| `Ticket: Sunset run_standards_gap_suite.py` | `run_standards_gap_suite.py`, gap fixtures, command center mirrors | Standards Integrity | Topic orchestrator reproduces gap markdown, analysis JSON, and standards CI wiring | Schedule standards team review before final removal. |
| `Ticket: Sunset run_standards_index_cli.py` | `run_standards_index_cli.py`, CLI smoke tests, docs | Standards Integrity / Engineering Complexity Watch | Provide new CLI wrapper/subcommand, migrate docs & agent prompts | Plan staged deprecation messaging for manual operators. |

## Topic Assignment Validation (2025-11-30)

- CommandView bundle `scripts_commandview_20251129-2102.json` inventories 46 automation scripts
  (26 producers, 4 consumers, 3 aggregators, 6 orchestrators, 2 summarizers, 5 utilities) and
  matches the topic scope outlined in the RFC.
- Topic coverage snapshot using the 2025-11-29 inventory:
  - **Test Execution Telemetry** – `run_pytest_log_capture.py`, `collect_test_log_reports.py`,
    `generate_test_log_health_report.py`, `generate_churn_complexity_heatmap.py`,
    `generate_test_coverage_inventory.py`, `analyze_test_hardening.py`,
    `summarize_health_suite.py`; helper dependency now resides under
    `command_center/scripts/libraries/test_log_analysis.py` with a legacy shim for
    `scripts/utilities/test_log_analysis.py` imports.
  - **Fault Diagnostics** – `run_fault_pipeline.py`, `collect_faulthandler_reports.py`,
    `generate_fault_artifacts.py`, `configure_faulthandler_runtime.py`,
    `dump_faulthandler_snapshot.py`, `fault_run_analysis.py`.
  - **Docs Health** – `aggregate_docs_health_signals.py`, `generate_doc_index.py`,
    `generate_anchor_inventory.py`, `generate_anchor_health_report.py`,
    `validate_markdown_anchors.py`, `verify_docs_integrity.py`,
    `generate_code_doc_churn_report.py`, `generate_undocumented_logic_report.py`.
  - **Standards Integrity** – `run_standards_gap_suite.py`, `run_standards_index_cli.py`,
    `generate_standards_index.py`, `analyze_standards_index_gaps.py`, `diff_standards_index.py`,
    `extract_standards_rules.py`, `validate_inventory.py`, `seed_standards_prompts.py`,
    `summarize_standards.py`.
  - **Dependency & Import Hygiene** – `run_batch_cleanup.py`,
    `generate_dependency_hygiene_report.py`, `generate_import_graph_report.py`,
    `scan_code_placeholders.py`, `validate_import_boundaries.py`, `generate_typecheck_report.py`,
    `generate_lizard_report.py`, `refresh_mypy_baselines.py`.
  - **Monkey Patch Oversight** – `scan_monkey_patches.py`, `classify_monkey_patches.py`,
    `analyze_monkey_patch_trends.py`, `monkey_patch_risk.py`.
  - **Engineering Complexity Watch (stretch)** – `generate_lizard_report.py`,
    `generate_dependency_hygiene_report.py`, `generate_undocumented_logic_report.py`,
    `generate_doc_index.py`, `validate_metrics_anchor_stubs.py`; confirm final scope once stretch
    charter is ratified.
- Gap tracking: Migrated the test log analysis helper into
  `command_center/scripts/libraries/test_log_analysis.py`, exposing it through the Command Center
  library index while keeping the legacy utility module as a compatibility re-export for existing
  callers.
- Next step: incorporate the inventory snapshot into Phase 1 documentation updates and capture the
  `test_log_analysis.py` decision in the RFC decision log.

## Healthview Manifest Mapping (2025-11-30)

- CommandView selector fields map 1:1 to Healthview with only the viewer slug changing:
  - `slug` → topic slug (e.g., `test-execution-telemetry`).
  - `category` → viewer namespace (`healthview`).
  - `label` → human-readable label including timestamp.
  - `relative_path` / `absolute_path` / `target_path` / `target_repo_relative` → reuse path layout with viewer slug swapped to `healthview` and topic folder names matching the report naming convention.
  - `timestamp` / `timestamp_iso` → identical semantics; generated alongside artifacts via shared timestamp helper.
- Healthview manifest JSON mirrors the CommandView schema; only the base directory (`.repo_studios/command_center/reports/healthview/<topic>/`) and slug strings differ.
- Metadata additions: include `source_viewer` to help agents distinguish CommandView vs. Healthview entries when both are loaded.
- Action item: incorporate the mapping into Phase 2 helper work so `write_report_artifacts` can emit both CommandView and Healthview selector entries without duplication.

## Topic Implementation Workstreams

- **Test Execution Telemetry**
  - Confirmed the dependent producer and consumer roster (pytest log capture, log collectors,
    churn heatmap, coverage inventory, hardening analysis) against
    `.repo_studios/scripts/scripts_index/scripts_commandview_20251129-2102.json`, verifying each
    script remains tracked by the CommandView inventory.
  - Locked the telemetry pipeline sequence to `collect → analyse → summarize`, ensuring the
    orchestrator calls coverage + log collection before running hardening and churn analysis, then
    gates the health summary on a structured log report. Documented the CLI surfaces exposed by
    `parse_args` (repo root override, per-script artifact retention controls, heatmap metrics
    source/window, explicit timestamp, log level) and confirmed dependency wiring: the collect step
    feeds the health summarizer via `report.json`, coverage consumes `--test-coverage-xml`, the
    heatmap accepts optional `--heatmap-metrics-source`, and retention budgets map to the
    corresponding `--*-artifacts-to-keep` knobs.
   - Migrated the sample pytest log and JUnit payloads into the shared fixture module at
     `.repo_studios/tests/fixtures/test_execution_telemetry/__init__.py`, updating
     `.repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py` and
     `.repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py` to
     rely on the common helpers so future orchestrator work can reuse the same artifacts.
   - Authored `docs/templates/test_execution_telemetry_summary_template.md`, capturing the Healthview
     Markdown layout (run context, runtime metrics table, failure highlights, artifact pointers) that
     operators and agents will use when reviewing Test Execution Telemetry results.
- **Fault Diagnostics**
  - Replaced the legacy `run_fault_pipeline.py` wrapper with `command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`. The topic runner loads the producer, consumer, and overview summarizer through the standard `PathsConfig`/`OptionsConfig` helpers, registers catalog metadata, and threads shared logging plus retention budgets across every step before emitting Command Center-compliant viewer/topic bundles.
  - [x] Anchored the Markdown and JSON overview artifacts on the consumer bundle emitted by `generate_fault_artifacts.py`, surfacing repeat-offender counts, baseline drift signals, and direct links to `stacks.csv`/`dumps/combined.txt`. The summarizer payload now carries a slug so the orchestrator can reference the run directory when mirroring assets into `commandview/fault_diagnostics/<slug>/`.
  - [x] Confirmed retention alignment by tracing `collect_faulthandler_reports.py`, `generate_fault_artifacts.py`, and the new summarizer output. Producer, consumer, and summarizer directories each obey their dedicated `--*-artifacts-to-keep` values, while the orchestrator mirrors manifest/summary/telemetry bundles into `.repo_studios/command_center/reports/commandview/fault_diagnostics/` and records telemetry for every step without reintroducing `latest_*` aliases.
- **Docs Health**
  - [x] Catalogued the Docs Health inputs by cross-referencing
    `.repo_studios/scripts/script_inventory_architecture.md` with the automation guides for
    `generate_doc_index.py`, `generate_anchor_inventory.py`, `validate_markdown_anchors.py`,
    `verify_docs_integrity.py`, `generate_code_doc_churn_report.py`, and
    `generate_undocumented_logic_report.py`. Confirmed that each producer maintains latest-pointer
    caches under `.repo_studios/reports/producer_reports/**/latest_*` (doc index mirror, anchor
    inventory bundle, markdown anchor validation run, docs integrity hash audit, churn TSV, and
    undocumented logic table) and that the Docs Health aggregator
    (`aggregate_docs_health_signals.py`) defaults to those paths while tolerating overrides for
    fixtures. Noted the shared reliance on the doc index JSON for enrichment, so orchestrator wiring
    must ensure the producer runs first to refresh the cache before downstream consumers compare
    churn and undocumented logic findings.
  - [x] Drafted the Docs Health Markdown summary layout by reviewing
    `aggregate_docs_health_signals.py`’s `_render_markdown` helper: the bundle already emits a
    **Summary** block with overall score and status counts followed by per-signal headings. The topic
    orchestrator will reuse that shape, pinning dedicated subsections for **Freshness** (code/doc churn
    gap analysis), **Coverage** (undocumented logic findings), **Structure** (anchor integrity and
    validation issues), and **Integrity** (docs hash + metrics stub status), with optional **Hygiene**
    notes when placeholder or monkey-patch signals are included. Each subsection will carry a metrics
    table plus a lint-guarded “Top findings” list so long doc paths and module names remain readable,
    and the summary preface will enumerate which signals were scored to keep anchor integrity,
    undocumented logic, and churn highlights front-and-center for Healthview reviewers.
  - [x] Audited Docs Health automation coverage by reviewing
    `.repo_studios/docs/automation/generate_doc_index.md`, `generate_anchor_inventory.md`,
    `validate_markdown_anchors.md`, `verify_docs_integrity.md`, `generate_code_doc_churn_report.md`,
    and `generate_undocumented_logic_report.md` alongside the aggregator guide at
    `aggregate_docs_health_signals.md`. Each producer doc already references the shared retention
    helpers, latest-pointer locations, and existing Make targets (for example `studio-generate-code-doc-churn-report`,
    `studio-verify-docs-integrity`, `studio-generate-undocumented-logic-report`). Updated the
    implementation plan to note that the forthcoming Docs Health orchestrator needs mirrored make
    targets (`studio-orchestrate-docs-health`) plus cross-links in
    `orchestrator_automation_hooks.md` once the topic runner ships; documentation edits shipped with
    the orchestrator rollout on 2025-12-02.
  - [x] 2025-12-02: Delivered the Docs Health topic orchestrator and smoke suite. The run module
    (`.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`) threads the
    doc index, anchor inventory, anchor validation, docs integrity, metrics stub, code/doc churn, and
    undocumented logic producers into the aggregator, mirrors Healthview manifests via
    `write_report_artifacts`, and registers catalog coverage for every dependency. Added
    `.repo_studios/tests/tests_command_center/docs_health/test_run_docs_health_overview.py` to assert
    manifest emission against seeded fixture data and refreshed `.repo_studios/Makefile` with the
    `studio-orchestrate-docs-health` target for local operators and CI.
- **Standards Integrity**
  - [x] Consolidated the Standards Integrity roster by cross-referencing
    `.repo_studios/scripts/script_inventory_architecture.md` with the automation guides for
    `generate_standards_index.py`, `diff_standards_index.py`, `seed_standards_prompts.py`, and
    `summarize_standards.py`, plus the Command Center shim for
    `analyze_standards_index_gaps.py`. Each producer exposes the standard `--artifacts-to-keep`
    retention knob, refreshes `latest_*` pointers, and honours logging overrides, while the gap
    analyser reuses the Command Center `PATHS_CONFIG` / `OPTIONS_CONFIG` setup so the topic
    orchestrator can thread repo-root and output directories through the shared helper stack. The
    summariser depends only on the `latest_index.yaml` pointer emitted by the index producer, so the
    orchestrator sequence will run index → gap analysis → diff (optional) → prompt seeding before
    invoking the log-only summary step.
  - [x] Determined that Engineering Complexity Watch should ship as a follow-up orchestrator
    instead of remaining bundled under Standards Integrity. Reviewed the RFC section 12 guidance
    ("start unified; split if runtime or scope demands") together with the automation docs for
    `generate_lizard_report.py` and `generate_dependency_hygiene_report.py`, which both highlight
    repo-wide scans, retention pruning, and non-trivial runtimes. Keeping the topic split lets the
    Standards Integrity runner focus on index → gap → diff → prompt seeding while the stretch
    orchestrator reuses the existing Docs Health and Dependency & Import Hygiene artifacts plus the
    standards summary to surface maintainability signals without rerunning heavy producers on every
    standards refresh.
  - 2025-11-30: Updated standards governance docs and CI definitions for the Standards
  Integrity topic orchestrator—refreshed
  `.repo_studios/docs/automation/orchestrator_automation_hooks.md`, extended
  `.repo_studios/docs/standards/docs_index.md` with Healthview bundle guidance, added
  `studio-orchestrate-standards` to `.repo_studios/Makefile`, and wired
  `.github/workflows/studio-inventory.yml` to execute the new target.
  - 2025-12-01: Landed `.repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py`
    to monkey-patch the producer shims, seed minimal outputs, and assert that the orchestrator
    writes Healthview `manifest.json`, `summary.md`, and `telemetry.json` bundles with the expected
    step telemetry. Confirmed the contract with
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity -q`
    and spot-checked a live run via
    `PYTHONPATH="C:/Users/genet/repo_studios/.repo_studios" make -C .repo_studios studio-orchestrate-standards PYTHON=.venv/Scripts/python.exe`.
- **Dependency & Import Hygiene**
  - 2025-11-30: Outlined the Dependency & Import Hygiene execution order so the forthcoming topic
  orchestrator can reuse a shared timestamp and retention budget. The run will start with
  `generate_dependency_hygiene_report.py` (defaults plus repo-root override) to capture requirement
  risk before other steps mutate state, then call `generate_import_graph_report.py` with the owned
  package defaults to refresh `import_graph_reports/` for downstream boundary checks.
  `scan_code_placeholders.py` follows, pointing at `.repo_studios/config/placeholder_allowlist.txt`
  to keep allowlisted debt separate from new findings. The orchestration then shells into
  `run_batch_cleanup.py` in dry-run mode with `--no-pytest` so Ruff/markdownlint command plans and
  the project tree refresh are recorded without altering tracked files; failures still surface via
  the structured bundle. Finally, `generate_typecheck_report.py` runs with the orchestrator timestamp
  (and an optional `--refresh-mypy-baselines` flag will trigger `refresh_mypy_baselines.py` when the
  caller opts in) so mypy diagnostics and historical baselines remain aligned with the hygiene readings.
  - 2025-11-30: Reconciled existing make targets with the planned CLI by earmarking
  `studio-generate-dependency-hygiene`, `studio-generate-import-graph`, `studio-scan-code-placeholders`,
  `studio-run-batch-cleanup`, `studio-generate-typecheck-report`, and `studio-refresh-mypy-baselines`
  as the legacy entry points. The orchestrator will continue invoking the underlying producers directly
  while exposing pass-through knobs (`--skip-import-graph`, `--skip-typecheck`, `--trigger-batch-cleanup`)
  so callers can emulate the make targets’ behaviour without shelling out. Existing recipes remain for
  ad-hoc runs until the orchestrator deprecation window opens.
  - 2025-11-30: Captured supporting utility hooks for parity—`scan_code_placeholders.py` relies on
  `.repo_studios/config/placeholder_allowlist.txt` and the governance cadence defined in
  `command_center/docs/phase_7/PLACEHOLDER_DEBT_PLAN.md`, `generate_typecheck_report.py` and
  `refresh_mypy_baselines.py` share the mypy target definitions under
  `.repo_studios/config/typecheck_targets.yaml` plus `pyproject.toml` strictness toggles, and
  `generate_import_graph_report.py`/`validate_import_boundaries.py` consume the command center
  `libraries` helpers alongside the legacy boundary allowlist
  (`.repo_studios/config/import_boundary_rules.yaml`). The orchestrator will surface overrides for
  each hook and mirror default retention to keep parity with the standalone producers.
- **Monkey Patch Oversight**
  - 2025-11-30: Collected the Monkey Patch Oversight pipeline assets—`scan_monkey_patches.py` produces
  structured findings under `.repo_studios/reports/producer_reports/monkey_patch_scans/` with legacy
  mirrors in `.repo_studios/monkey_patch/`; `classify_monkey_patches.py` consumes those runs and writes
  risk-tier bundles to `.repo_studios/reports/consumer_reports/monkey_patch_risk/`;
  `monkey_patch_risk.py` exposes the shared risk taxonomy used by both consumer and aggregator layers;
  and `analyze_monkey_patch_trends.py` aggregates the consumer summaries into
  `.repo_studios/reports/aggregator_reports/monkey_patch_trends/` with Markdown/JSON trend snapshots
  plus latest pointers. All assets honor the Command Center helper stack for retention, logging, and
  catalog registration.
  - 2025-11-30: Defined the Monkey Patch summary artefact layout so the forthcoming orchestrator
    can publish consistent Healthview bundles and feed duplicate detection triage. The summarizer will
    emit a timestamped Markdown + JSON pair under
    `.repo_studios/reports/summarizer_reports/monkey_patch_overview/monkey_patch_overview-<timestamp>.{md,json}`
    via `write_report_artifacts`, mirroring the helper pattern already used by
    `summarize_standards.py`. Each Markdown file opens with the portfolio snapshot (risk tiers,
    outstanding manual patches, and recommendation heatmap), then anchors a "Duplicate Follow-up"
    section that links to the latest scan matrices and surfaces any patch modules that already appear
    in the duplicate report matrix. The JSON sibling keeps the normalized counts and duplicate
    cross-references so the duplicate scanner and Healthview dashboards can ingest the payload without
    re-parsing Markdown. Both artefacts record the source producer/consumer runs, include the
    orchestrator timestamp, and publish the relative path to the patch trend aggregator so the
    duplicate remediation checklist can jump straight to detailed timelines.
  - 2025-11-30: Verified Monkey Patch coverage spans `.repo_studios/tests/tests_producers/test_scan_monkey_patches.py`,
    `.repo_studios/tests/tests_consumers/test_classify_monkey_patches.py`,
    `.repo_studios/tests/tests_aggregators/test_analyze_monkey_patch_trends.py`, and
    `.repo_studios/tests/tests_utilities/test_monkey_patch_risk.py`, giving us producer signal
    validation, consumer risk tiering, aggregator trend retention, and helper taxonomy safeguards.
  - 2025-12-01: Established `.repo_studios/tests/tests_command_center/monkey_patch/` with shared
    helpers, `test_orchestrator_contract.py`, and `test_summarizer_contract.py` to assert the topic
    pipeline wiring, CLI `run()` shims, and Healthview overview contract now that the orchestrator
    and summarizer have landed; suite validated via
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/monkey_patch -q`.
  - 2025-12-01: Executed the Monkey Patch Oversight orchestrator end-to-end, producing
    `commandview/monkey_patch_oversight/20251201-1155/manifest.json` plus refreshed producer,
    consumer, aggregator, and summarizer artifacts under
    `.repo_studios/reports/{producer,consumer,aggregator,summarizer}_reports/monkey_patch_*`, confirming
    retention pruning and duplicate matrix threading behave as documented.
- **Engineering Complexity Watch (stretch)**
  - [ ] Decide whether to merge structural complexity and inventory governance or stage separate
    orchestrators.
  - [ ] Enumerate script set (lizard report, inventory validation, metrics stubs, standards index
    CLI) and identify any tooling gaps.
  - [ ] Document rollout conditions (runtime budgets, stakeholder sign-off) before implementation.

## Phase Checklist

- [ ] Phase 1 – Design Convergence
  - [x] Validate topic script assignments against the 2025-11-29 inventory bundle (see 2025-11-30 snapshot).
  - [x] Finalise Healthview manifest schema by mapping CommandView fields to the new slug layout
    (see Healthview Manifest Mapping section).
  - [x] Record RFC decisions in section 13 with approvals and outstanding risks (see 2025-11-30 entry).
  - [x] Document legacy removal scope (modules, tests, docs, artifacts) in issue tracker tickets so
    teams can claim discrete workstreams (see Legacy Orchestrator Ticket Matrix).
  - [x] Open issue tickets for legacy orchestrator retirement (one per legacy runner) and link them
    to the parity matrix for cross-team tracking (ticket stubs recorded above).
- [ ] Phase 2 – Library Foundations
  - Implemented `build_topic_pipeline`, `summarizer_runner`, `telemetry_emitters`, and
    `catalog_registry` helpers with unit tests on 2025-11-30; validated with
    `pytest .repo_studios/tests/tests_command_center` and the helper-focused suites to confirm the
    viewer/topic output layout and pruning semantics.
  - Verified helper modules honour ASCII naming, repository logging configuration, and pruning
    semantics on 2025-11-30 by instrumenting `topic_pipeline` logging, auditing
    `catalog_registry` docstrings for ASCII-only content, and rerunning
    `pytest .repo_studios/tests/tests_command_center/test_topic_pipeline.py` together with the full
    Command Center suite.
  - Delivered `reports_naming_audit.py` under `.repo_studios/command_center/scripts/utilities/` on
    2025-11-30, wiring the `run(argv)` shim to emit JSON and Markdown summaries plus optional rename
    hints for orchestrator consumption; validated with
    `.venv/Scripts/python.exe -u -m pytest .repo_studios/tests/tests_command_center/test_reports_naming_audit.py`.
  - Documented helper usage patterns inside `.repo_studios/command_center/docs/code_library/helper_usage_patterns.md`
    on 2025-11-30, outlining orchestration wiring, telemetry emission, and catalog registry usage
    with pointers to the supporting test suites.
  - Authored migration notes on 2025-11-30 in `.repo_studios/command_center/docs/orchestrator_migration_notes.md`
    to demonstrate how legacy orchestrators integrate the topic pipeline, summarizer runner,
    telemetry emitters, and catalog registry helpers; cross-references the helper unit tests under
    `.repo_studios/tests/tests_command_center/` for parity validation.
  - [x] Stage migration of `test_log_analysis.py` into the shared library once naming-compliant
  scaffolding ships (2025-11-30: helper relocated to `command_center/scripts/libraries/test_log_analysis.py`,
  with the legacy utility shim re-exporting the new module and pytest/documentation updates recorded).
- [ ] Phase 3 – Topic Orchestrator Delivery
  - [x] Ship Test Execution Telemetry orchestrator with end-to-end fixtures and Markdown snapshot
    tests.
    - 2025-12-01: Added `.repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py`
      implementing the topic pipeline (collect → analyse → summarize), catalog registration, and
      Healthview artifact emission via `write_report_artifacts`.
    - Exercised collector and summarizer integration using fixture-backed logs while stubbing
      coverage, hardening, and heatmap helpers for deterministic validation in
      `tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`; Markdown
      summary assertions cover success and log-missing scenarios.
    - Verified the generated manifest/telemetry payload mirrors step outcomes and surfaces relative
      artifact paths per `REPORT_NAMING_STANDARDS.md` viewer/topic guidance.
  - 2025-12-01: Delivered the Fault Diagnostics orchestrator with aligned CLI surfaces, wiring
    `run_fault_diagnostics_overview.py` through the shared helper stack, updating
    `.repo_studios/Makefile` with the `studio-orchestrate-fault-diagnostics` target (aliasing the
    legacy fault pipeline entry point), refreshing automation docs (`orchestrator_automation_hooks.md`,
    `run_fault_pipeline.md`), and confirming viewer/topic bundles under
    `.repo_studios/command_center/reports/commandview/fault_diagnostics/20251201-1313/` alongside the
    producer/consumer mirrors; validated end-to-end via `make -C .repo_studios
    studio-orchestrate-fault-diagnostics PYTHON=.venv/Scripts/python.exe` and
    `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/fault_diagnostics -q`.
  - [x] Deliver Docs Health orchestrator with aligned CLI surfaces.
    - 2025-12-02: Added `command_center/scripts/orchestrators/run_docs_health_overview.py`, wiring the Docs Health producers and aggregator through the shared topic pipeline with catalog registration, Healthview manifest emission, and retention knobs for every dependency. Published the `studio-orchestrate-docs-health` make target and validated the runner via `make -C .repo_studios studio-orchestrate-docs-health PYTHON=.venv/Scripts/python.exe` together with `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/docs_health -q`.
  - [ ] Deliver Standards Integrity orchestrator with aligned CLI surfaces.
  - [ ] Deliver Dependency & Import Hygiene orchestrator with aligned CLI surfaces.
  - 2025-12-01: Delivered the Monkey Patch Oversight orchestrator and companion summarizer with
    aligned CLI retention knobs, catalog registration, and viewer/topic manifest emission; see
    `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` and
    `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py`.
  - [ ] Produce a parity matrix that maps every existing orchestrator invocation and artifact to
    its replacement topic pipeline, including scripts, CLI flags, and retention expectations.
  - [ ] Stage redirects or temporary shims for legacy orchestrators so tests and make targets can
    point to the new entry points without breaking interim workflows.
  - [ ] Evaluate the Engineering Complexity Watch pipeline scope and either implement the unified
    orchestrator or split follow-up work as agreed in RFC Q&A.
  - [ ] Update topic orchestrator READMEs and inline module docstrings to reference Healthview
    artifact locations, replacements for legacy outputs, and expected runtime characteristics.
- [ ] Phase 4 – Summaries and Healthview Artifacts
  - [ ] Update existing summarizers (health suite, standards) to consume helper APIs and emit
    Healthview-compatible Markdown.
  - [ ] Author new summarizers where topic coverage is net-new, starting with Test Execution
    Telemetry.
  - [ ] Publish the Healthview manifest schema and JSON example alongside viewer integration notes,
    including the slug placement and bundle naming strategy that distinguishes Healthview from
    CommandView.
- [ ] Phase 5 – Meta-Orchestrator and Tooling
  - [ ] Implement `orchestrate_full_diagnostic.py` with include/exclude controls, manifest
    emission, and stop-on-first-failure toggles.
  - [ ] Add `studio-orchestrate-<topic>` and `studio-orchestrate-full-diagnostic` make targets with
    logging guidance for local runs.
  - [ ] Introduce telemetry counters for runtime and artifact sizing to inform future
    parallelisation decisions and support Healthview dashboard instrumentation.
  - [ ] Invoke the naming-audit utility inside documentation/reporting orchestrators to block
    non-compliant artifacts.
- [ ] Phase 6 – Documentation and Adoption
  - [ ] Update `.repo_studios/scripts/script_inventory_architecture.md` and automation guides with
    new orchestrators and helper references.
  - [ ] Publish Healthview onboarding material for Command Center, including tab wiring notes,
    slug placement, and viewer-specific CSS/JS considerations.
  - [ ] Announce migration timelines, flag deprecated targets, and capture agent integration
    outcomes.
  - [ ] Produce a cleanup checklist covering legacy doc pages, README pointers, and references in
    tests so removal work is traceable.
- [ ] Phase 7 – Validation and Rollout
  - [ ] Run sequential dry runs across all topics, recording runtimes, artifact paths, and
    summariser outputs.
  - [ ] Enable CI coverage and ensure tests gate on orchestrator and helper suites.
  - [ ] Close any backlog items opened for missing utilities or schema adjustments before marking
    the project live.
- [ ] Phase 8 – Legacy Decommissioning
  - [ ] Remove superseded orchestrator modules, CLI shims, and associated unit tests once parity is
    verified, recording the change in the decision log.
  - [ ] Delete or archive obsolete artifacts under previous report folders, ensuring Healthview
    becomes the canonical destination.

## Healthview Viewer Wiring Reference

Capture the manifest payload now so wiring the Healthview tab is a data-mapping exercise later. The
viewer selector mirrors CommandView’s `selector.json` format with topic-specific slugs and bundle
paths:

```python
healthview_selector_stub = {
  "generated_at": "<iso8601 timestamp>",
  "entries": [
    {
      "slug": "healthview",
      "options": [
        {
          "slug": "test-execution-telemetry",
          "category": "healthview",
          "label": "Test Execution Telemetry (2025-11-29 21:02 UTC)",
          "relative_path": "healthview/test_execution_telemetry/healthview_test_execution_telemetry_20251129-2102.json",
          "absolute_path": "C:/Users/genet/repo_studios/.repo_studios/command_center/reports/healthview/test_execution_telemetry/healthview_test_execution_telemetry_20251129-2102.json",
          "target_path": "C:/Users/genet/repo_studios/.repo_studios/command_center/reports/healthview/test_execution_telemetry",
          "target_repo_relative": ".repo_studios/command_center/reports/healthview/test_execution_telemetry",
          "timestamp": "20251129-2102",
          "timestamp_iso": "2025-11-29T21:02:00+00:00"
        }
      ]
    }
  ]
}
```

Populate one `options` entry per topic bundle (Fault Diagnostics, Docs Health, and so on) once the
Healthview artifacts land. Retaining `category`, `slug`, and dual absolute/relative paths keeps the
viewer dropdown logic compatible with existing CommandView plumbing.

## Report Naming Standard Initiative

The naming convention below is now **approved** (see `REPORT_NAMING_STANDARDS.md`) and should guide
all future artifact emissions under `.repo_studios/command_center/reports/`. Legacy bundles remain
grandfathered until migration tasks execute, but new outputs must comply immediately.

- **Audit** – reports naming audit script now scans `/reports/` directories (CommandView, Healthview
  previews, legacy bundles) and emits JSON plus Markdown variance summaries covering slug position,
  timestamp stem, and artifact suffixes per topic.
- [ ] **Convention Adoption** – update helpers and orchestrators so fresh Healthview and
  CommandView-compatible bundles emit in the approved layout without `latest_*` aliases. *(2025-11-29:
  automation manifest and metrics summary producers now emit under `commandview/<topic>/<timestamp>`;
  tests `test_generate_automation_manifest.py` and `test_generate_metrics_summary.py` updated and
  passing. Duplicate scan aggregator and function analysis summarizer now mirror artifacts to
  `commandview/duplicate_scan/<ts>/` and `commandview/function_analysis/<ts>/` with
  `test_scan_duplicates.py`, `test_generate_function_analysis.py`, and the orchestrator smoke suite
  all green after rerun.)*
- [ ] **Legacy Migration Plan** – identify high-traffic legacy directories that need shims or
  redirects, staging renames after Phase 4 when new artifacts are live but before Phase 8 cleanup.
- [ ] **Compliance Report** – bolt the audit script into Phase 5 validation so nightly runs flag
  non-conforming artifacts until the migration is complete.

### Proposed schema sketch

| Component | Description | Example |
| --- | --- | --- |
| `<root>` | Physical root on disk | `C:/Users/genet/repo_studios/.repo_studios/command_center/reports` |
| `<viewer_slug>` | Primary tab identifier (`commandview`, `healthview`, `jarvis`) | `healthview` |
| `<topic>` | Topic or orchestrator slug using kebab-case | `test_execution_telemetry` |
| `<timestamp>` | UTC stamp `YYYYMMDD-HHMM` matching bundle contents | `20251129-2102` |
| `<artifact_role>` | Describes payload type (`manifest`, `summary`, `matrix`, `telemetry`) | `manifest` |
| `<ext>` | File extension aligned with content type | `json` |

Example manifest path: `.../healthview/test_execution_telemetry/20251129-2102/manifest.json`

### Audit automation expectations

- List every artifact under `/reports/`, decomposing the current path into the schema components.
- Highlight deviations (missing slug, inconsistent timestamp format, unexpected suffix) in both
  stdout and a machine-consumable JSON report to feed future CI checks.
- Provide roll-up metrics (per topic compliance ratios, top offenders) to inform migration order.
- Offer a `--dry-run-rename` option that prints the proposed new path without mutating files.
- Flag `latest_*` shortcuts so they can be removed; instead point consumers at the newest
  timestamped bundle using the standard hierarchy.

### Integration checkpoints

- Gate helper updates in Phase 2 after prototype naming schema is ratified so new topics never emit
  non-compliant paths.
- Schedule the legacy rename window between Phase 4 (artifacts live) and Phase 6 (documentation
  refresh) to ensure docs capture final locations.
- Fold compliance reporting into Phase 7 validation, marking the project complete only after the
  nightly audit reports zero variances for CommandView and Healthview.
  - [ ] Update make targets, CI jobs, and agent scripts to drop references to retired entry points
    and confirm the CommandView index reflects the new orchestrator set only.

## Dependencies and Tooling

- Python 3.13 virtual environment at `.venv` (configured via
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe`).
- Command Center helper modules and make targets already adopted by existing orchestrators.
- CommandView inventory bundles for ongoing coverage verification during implementation.

## Reporting and Tracking

- Use the checkboxes above as the authoritative delivery tracker; update them in source control for
  transparency.
- Capture deviations, blocked tasks, and risk notes in section 11 of the RFC so stakeholders can
  reconcile plan vs. execution quickly.
- Store Healthview manifest examples under `docs/automation/examples/` once stabilised to keep
  reviewers aligned on expected outputs.

### Governance Notes (2025-11-30)

- Completed Phase 2 helper scaffolding (`build_topic_pipeline`, `summarizer_runner`,
  `telemetry_emitters`, `catalog_registry`) with coverage backed by
  `tests/tests_command_center/test_topic_pipeline.py`, `test_summarizer_runner.py`,
  `test_telemetry_emitters.py`, and `test_catalog_registry.py`; full suite validation captured via
  `pytest .repo_studios/tests/tests_command_center` on 2025-11-30.
- Confirmed helper compliance with ASCII-only naming and repository logging guidance by updating
  `topic_pipeline.py` to emit `logging`-based step telemetry, normalising
  `catalog_registry.py` docstrings, and rerunning
  `pytest .repo_studios/tests/tests_command_center/test_topic_pipeline.py` followed by the full
  Command Center suite (2025-11-30).
- Added `reports_naming_audit.py` utility to the shared library catalogue on 2025-11-30, producing
  JSON and Markdown audit bundles under `.repo_studios/command_center/reports/reports_naming_audit/`
  and validating its CLI via `.venv/Scripts/python.exe -u -m pytest
  .repo_studios/tests/tests_command_center/test_reports_naming_audit.py`.
- Authored `docs/code_library/helper_usage_patterns.md` on 2025-11-30 to document usage patterns for
  the topic pipeline, summarizer runner, telemetry emitter, and catalog registry helpers; crosslinks
  include the helper test suites under `.repo_studios/tests/tests_command_center/`.
- Captured orchestrator migration guidance in `.repo_studios/command_center/docs/orchestrator_migration_notes.md`
  on 2025-11-30, mapping each legacy orchestrator to the new helpers with references to
  `.repo_studios/tests/tests_command_center/` parity suites.
- 2025-11-30: Verified the Test Execution Telemetry dependencies by loading
  `.repo_studios/scripts/scripts_index/scripts_commandview_20251129-2102.json` and confirming the
  expected scripts (`run_pytest_log_capture.py`, `collect_test_log_reports.py`,
  `generate_test_log_health_report.py`, `generate_churn_complexity_heatmap.py`,
  `generate_test_coverage_inventory.py`, `analyze_test_hardening.py`) are all present (inline check
  executed via `@'... '@ | python -`).
- 2025-11-30: Documented the Test Execution Telemetry sequencing (collect → analyse → summarize)
  and CLI wiring inside `run_test_execution_telemetry.py`, validating retention and dependency
  flags through `parse_args` plus the orchestrator tests
  (`pytest .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`).
- 2025-11-30: Centralised the pytest log/JUnit fixtures for Test Execution Telemetry inside
  `.repo_studios/tests/fixtures/test_execution_telemetry/__init__.py`, updating both
  `test_run_pytest_log_capture.py` and `test_run_test_execution_telemetry.py` to consume the shared
  helpers; confirmed behaviour with
  `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py .repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py`.
- 2025-11-30: Added `docs/templates/test_execution_telemetry_summary_template.md` to codify the
  Healthview Markdown structure (run context bullets, runtime metrics table, failure highlights,
  artifact links) for Test Execution Telemetry reviews.
- 2025-11-30: Mapped Fault Diagnostics handoffs by reviewing `run_fault_pipeline.py`, confirming the
  `.repo_studios/reports/orchestrator_logs/faulthandler_logs` default with
  `FAULT_PIPELINE_ALLOW_LEGACY` fallback, the producer’s `faulthandler_report-<ts>` +
  `latest_report.json` mirrors, and the consumer’s reliance on `--outdir` / `--report` together with
  `FAULT_OUTDIR` and `FAULT_TOP_FRAMES_N` before mirroring artifacts to
  `.repo_studios/command_center/reports/fault_artifacts_consumer`.
- 2025-11-30: Confirmed Fault Diagnostics retention alignment by inspecting
  `.repo_studios/scripts/producers/collect_faulthandler_reports.py` (`DEFAULT_KEEP`, `_mirror_to_command_center`)
  and `.repo_studios/scripts/consumers/generate_fault_artifacts.py` (`DEFAULT_ARTIFACTS_TO_KEEP`,
  `_mirror_to_command_center`, `_prune_history`); backed the check with
  `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_producers/test_collect_faulthandler_reports.py .repo_studios/tests/tests_consumers/test_generate_fault_artifacts.py`.
- 2025-11-30: Reviewed `.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py`
  (`_render_markdown`, signal weighting helpers) to map planned Docs Health summary sections; docs-only
  planning, no tests executed.
- 2025-11-30: Cross-checked Docs Health automation guides
  (`generate_doc_index.md`, `generate_anchor_inventory.md`, `validate_markdown_anchors.md`,
  `verify_docs_integrity.md`, `generate_code_doc_churn_report.md`, `generate_undocumented_logic_report.md`,
  `aggregate_docs_health_signals.md`) to confirm retention knobs, make targets, and latest-pointer
  references ahead of wiring the topic orchestrator; documentation review only.
- 2025-11-30: Surveyed Standards Integrity assets via
  `.repo_studios/scripts/script_inventory_architecture.md` and the automation docs for
  `generate_standards_index.py`, `diff_standards_index.py`, `seed_standards_prompts.py`,
  `summarize_standards.py`, plus the Command Center shim
  `.repo_studios/scripts/producers/analyze_standards_index_gaps.py` to confirm shared retention/logging
  flags and pointer usage before sequencing the topic orchestrator; documentation-only review.
- 2025-11-30: Reassessed Engineering Complexity Watch bundling by revisiting RFC section 12 along
  with `.repo_studios/docs/automation/generate_lizard_report.md` and
  `.repo_studios/docs/automation/generate_dependency_hygiene_report.md`; decided to keep Standards
  Integrity focused on index/gap sequencing while staging Engineering Complexity Watch as a
  follow-up orchestrator that ingests the existing Docs Health and Dependency & Import Hygiene
  artifacts alongside the standards summary.
- 2025-11-30: Logged the Standards Integrity documentation/CI touchpoints ahead of the topic
  orchestrator rollout—`orchestrator_automation_hooks.md`, `docs_index.md`, the Make target roster,
  and the inventory health workflow—so the governance update can execute immediately once the new
  runner merges.
- 2025-11-30: Re-validated that the Standards Integrity topic runner has not landed yet
  (`.repo_studios/scripts/orchestrators/` only contains the legacy standards gap suite and index
  CLI), so the governance/CI refactors remain blocked pending the new orchestrator entry point.
- 2025-11-30: Surveyed Docs Health inputs via
  `.repo_studios/scripts/script_inventory_architecture.md` and the automation docs for
  `generate_doc_index.py`, `generate_anchor_inventory.py`, `validate_markdown_anchors.py`,
  `verify_docs_integrity.py`, `generate_code_doc_churn_report.py`, `generate_undocumented_logic_report.py`,
  and `aggregate_docs_health_signals.py` to confirm latest-pointer caches and enrichment ordering; docs-only
  review, no tests required.
- 2025-11-30: Updated Standards Integrity governance touchpoints—edited `.repo_studios/docs/automation/orchestrator_automation_hooks.md`, `.repo_studios/docs/standards/docs_index.md`, `.repo_studios/Makefile`, and `.github/workflows/studio-inventory.yml`; validated integration with `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center` to keep coverage baselines intact.
- 2025-11-30: Documented the Dependency & Import Hygiene pipeline ordering in `docs/automation/orchestrator_implementation.md`; documentation-only change, no tests required.
- 2025-11-30: Reconciled Dependency & Import Hygiene make targets with the forthcoming CLI—tracked legacy recipes (`studio-generate-dependency-hygiene`, `studio-generate-import-graph`, `studio-scan-code-placeholders`, `studio-run-batch-cleanup`, `studio-generate-typecheck-report`, `studio-refresh-mypy-baselines`) and noted the orchestrator pass-through flags for parity; documentation-only, no tests.
- 2025-11-30: Recorded supporting utility hooks for the hygiene orchestrator—`scan_code_placeholders.py` consumes `.repo_studios/config/placeholder_allowlist.txt` and the governance cadence in `command_center/docs/phase_7/PLACEHOLDER_DEBT_PLAN.md`; the typecheck/refresh duo reads targets and strictness from `pyproject.toml` (`tool.mypy.targets`, `tool.mypy.overrides`, `tool.repo_studios.strict`) while deferring to `HEALTH_TYPECHECK_FAST`; import hygiene relies on the command center library helpers plus the boundary configuration surfaced by `validate_import_boundaries.py`. Documentation-only, test suite unchanged.
- 2025-11-30: Catalogued Monkey Patch Oversight scripts and artifact flows—`scan_monkey_patches.py` → `classify_monkey_patches.py` → `analyze_monkey_patch_trends.py`, with shared risk helpers; documentation-only update.
- 2025-12-01: Shipped Monkey Patch Oversight pipeline implementation and verified artifacts by
  running `@'\nfrom command_center.scripts.orchestrators import run_monkey_patch_oversight\nstatus = run_monkey_patch_oversight.run(["--repo-root", ".", "--log-level", "INFO"])\nprint("EXIT", status)\n'@ | C:/Users/genet/repo_studios/.venv/Scripts/python.exe -`, which emitted
  `.repo_studios/command_center/reports/commandview/monkey_patch_oversight/20251201-1155/manifest.json`
  together with refreshed producer (`monkey_patch_scan-20251201_115542`), consumer
  (`monkey_patch_risk-2025-12-01_115542`), aggregator (`monkey_patch_trends-2025-12-01_115542`), and
  summarizer (`monkey_patch_overview-20251201_115540`) bundles; contract coverage reconfirmed via
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/monkey_patch -q`.
- 2025-12-01: Validated Fault Diagnostics orchestrator delivery by executing
  `make -C .repo_studios studio-orchestrate-fault-diagnostics PYTHON=.venv/Scripts/python.exe`,
  inspecting `.repo_studios/command_center/reports/commandview/fault_diagnostics/20251201-1313/manifest.json`
  for aligned artifact pointers, and running
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/fault_diagnostics -q`
  to confirm orchestrator + summarizer test coverage.
