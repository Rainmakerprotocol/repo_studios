---
title: Orchestrator Implementation Plan
status: draft
version: 2025-11-29
last_updated: 2025-12-07
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

### Detailed Legacy-to-Topic Parity Mapping (2025-12-01)

| Legacy Entry Point | Topic Replacement | CLI / Flag Parity | Artifact Mapping | Retention Expectations |
| --- | --- | --- | --- | --- |
| `.repo_studios/scripts/orchestrators/orchestrate_health_suite.py`<br>`make studio-orchestrate-health-suite` | Combination of `run_test_execution_telemetry.py`, `run_fault_diagnostics_overview.py`, `run_docs_health_overview.py`, `run_dependency_import_hygiene.py`, `run_monkey_patch_oversight.py`, and `run_standards_integrity.py` (meta-runner to follow via `run_command_center_pipeline.py`) | Legacy suite exposed `--timestamp`, `--live`, and timeout knobs but no per-step skips; each topic orchestrator now shares the standard `--repo-root` / `--log-level` surface plus targeted skip/keep flags (for example `--skip-typecheck`, `--skip-producer`) via the shared CLI builders; the upcoming meta orchestrator will carry the old “never stop” vs. “stop on first failure” semantics explicitly. | Health suite logged to `.repo_studios/reports/orchestrator_logs/health_suite_logs/<ts>/status.{json,md}`; each topic now emits `manifest.json`, `summary.md`, and `telemetry.json` under `.repo_studios/command_center/reports/healthview/<topic>/<timestamp>/` while continuing to mirror producer/consumer artifacts (for example dependency hygiene, fault artifacts) in their existing directories. | Legacy retention relied on manual pruning of `health_suite_logs`; the topic orchestrators default to three retained topic bundles (`--artifacts-to-keep`) with per-step budgets between 3–10 runs enforced through `build_standard_options`, keeping parity with the historical log footprint while preventing unbounded growth. |
| `.repo_studios/scripts/orchestrators/run_pytest_log_capture.py`<br>`make studio-run-pytest-log-capture` | `command_center/scripts/orchestrators/run_test_execution_telemetry.py` (invoked directly or through `run_command_center_pipeline.py test-execution-telemetry`) | Legacy runner exposed `--repo-root`, `--logs-dir`, `--output-dir`, `--artifacts-to-keep`, `--from-log`, and passthrough pytest args; the replacement preserves repo/root and log-directory overrides while adding granular `--collector-artifacts-to-keep`, `--health-artifacts-to-keep`, `--heatmap-window`, and metrics source flags. Direct pytest execution remains available through the underlying runner and is expected to be chained ahead of the topic orchestrator until the meta-runner shells it automatically. | Legacy bundles lived at `.repo_studios/reports/orchestrator_runs/pytest_log_capture/pytest_log_capture-<ts>/` with raw logs in `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/`; the topic orchestrator now emits Healthview bundles in `.repo_studios/command_center/reports/healthview/test_execution_telemetry/<timestamp>/` while refreshing the collector, health report, heatmap, coverage, and hardening artifacts in their existing producer/consumer directories. | Old orchestrator defaulted to keeping five structured runs (`--artifacts-to-keep 5`) and left raw log retention to the caller; the new runner defaults to three topic manifests plus `--collector-artifacts-to-keep 10`, `--health-artifacts-to-keep 5`, and similar knobs so downstream consumers keep the same history without manual cleanup. |
| `.repo_studios/scripts/orchestrators/run_fault_pipeline.py`<br>`make studio-run-fault-pipeline` | `command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` (`make -C .repo_studios studio-orchestrate-fault-diagnostics`) | Legacy flags (`--runs-dir`, `--run-dir`, `--reuse-report`, `--skip-producer`, `--skip-consumer`, `--artifacts-to-keep`) map one-to-one onto the topic orchestrator, which adds `--skip-summarizer`, per-step retention knobs, and catalog registration while keeping repo-root detection identical. | Legacy outputs under `.repo_studios/reports/orchestrator_runs/fault_pipeline/` and the Command Center mirrors are now replaced by `commandview/fault_diagnostics/<timestamp>/manifest.json|summary.md|telemetry.json`; producer/consumer outputs continue to land in `.repo_studios/reports/{producer,consumer}_reports/*` with the same filenames. | Historical pipeline kept ten runs by default; the topic runner keeps ten producer/consumer runs and three orchestrator manifests via `--producer-artifacts-to-keep`, `--consumer-artifacts-to-keep`, `--summarizer-artifacts-to-keep`, and `--artifacts-to-keep`, preserving audit depth while aligning with helper-enforced pruning. |
| `.repo_studios/scripts/orchestrators/run_batch_cleanup.py`<br>`make studio-run-batch-cleanup` | `command_center/scripts/orchestrators/run_dependency_import_hygiene.py` (trigger batch step with `--trigger-batch-cleanup`) | Legacy cleanup exposed `-t/--target`, `--mode`, `--dry-run`, `--no-pytest`, and retention toggles; the new topic orchestrator threads equivalent controls via `--trigger-batch-cleanup`, `--cleanup-artifacts-to-keep`, `--dependency-*`, `--skip-typecheck`, and `--skip-import-graph` while still honoring dry-run semantics and repo-root discovery when it invokes the underlying cleanup runner. | Legacy bundles wrote to `.repo_studios/reports/orchestrator_runs/run_batch_cleanup/run_batch_cleanup-<ts>/`; the topic pipeline now mirrors the cleanup report alongside dependency hygiene, import graph, placeholder, and typecheck artifacts, and publishes Healthview bundles at `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<timestamp>/`. | Legacy retention kept five cleanup runs unless manually pruned; the replacement enforces per-step retention (`--dependency-artifacts-to-keep`, `--cleanup-artifacts-to-keep`, etc.) plus a three-run orchestrator manifest window, matching historical history while preventing runaway cleanup archives. |
| `.repo_studios/scripts/orchestrators/run_standards_gap_suite.py`<br>`make studio-run-standards-gap-suite` | `command_center/scripts/orchestrators/run_standards_integrity.py` (`make -C .repo_studios studio-orchestrate-standards`) | Gap suite previously offered `--repo-root`, `--skip-index`, `--timestamp`, and `--legacy-json`; the topic runner preserves repo-root overrides while adding path overrides for every producer (`--index-output-dir`, `--gap-output-dir`, `--prompt-output-dir`), diff controls (`--diff-old-index`, `--diff-fail-on`), and catalog toggles. The gap analyzer still accepts `--gap-max-show`, letting operators reproduce legacy behaviour. | Legacy outputs under `.repo_studios/command_center/reports/standards_gap_suite/<timestamp>/` are now replaced by Healthview bundles in `.repo_studios/command_center/reports/healthview/standards_integrity/<timestamp>/`, with index, gap, diff, and prompt artifacts refreshed in the same producer/consumer directories to maintain downstream compatibility. | Gap suite keep counts were enforced manually; the topic runner maintains per-step keep knobs (`--index-artifacts-to-keep`, `--gap-artifacts-to-keep`, `--diff-artifacts-to-keep`, `--prompt-artifacts-to-keep`) plus three orchestrator manifests, delivering tighter, helper-managed pruning. |
| `.repo_studios/scripts/orchestrators/run_standards_index_cli.py` | Standards Integrity orchestrator plus ongoing CLI shim (`run_standards_index_cli.py`) for ad-hoc queries | The CLI still supports `list/search/show/stats` with `--severity`, `--category`, and `--artifacts-to-keep`; Standards Integrity now captures the same catalog data inside its manifest and summary, and automation should invoke the topic runner directly (for example `make -C .repo_studios studio-orchestrate-standards`) while the shim handles interactive lookups. | CLI artifacts in `.repo_studios/reports/orchestrator_runs/standards_index_cli/` are now mirrored into the Standards Integrity Healthview bundle (summary embeds rule counts, manifest records index metadata) so operators can retire the legacy directory once dashboards consume the new payload. | CLI retention relied on `--artifacts-to-keep 5`; the Standards Integrity runner centralises retention with helper-managed keep counts (three manifests by default, producer-specific keeps for index/diff/prompt). |

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
  `studio-run-pytest-log-capture`, `studio-run-batch-cleanup`, `studio-run-standards-gap-suite` –
  document successor targets, note interim aliases, and prepare MR to adjust `.repo_studios/Makefile`
  with deprecation warnings (legacy `studio-run-standards-index` alias retired 2025-12-01; use
  `studio-orchestrate-standards`).
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
    step telemetry. Refined `studio-orchestrate-standards` to export `PYTHONPATH` cross-platform and
    added a `__main__` guard to `run_standards_integrity.py` so direct `python` invocations execute
    the pipeline. Confirmed the contract with
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity -q`
    and spot-checked live runs via `make -C .repo_studios studio-orchestrate-standards PYTHON=.venv/Scripts/python.exe`
    and `C:/Users/genet/repo_studios/.venv/Scripts/python.exe .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py --repo-root C:/Users/genet/repo_studios --log-level INFO`.
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
  - 2025-12-01: Added `command_center/scripts/orchestrators/run_dependency_import_hygiene.py`, wiring
    dependency hygiene → import graph → placeholder scan → optional batch cleanup → typecheck → optional
    mypy baseline refresh through the shared topic pipeline helpers with skip/trigger flags, shared
    timestamps, and Healthview artifact emission. Introduced
    `.repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py`
    to cover artifact emission and skip-flag behaviour, and validated via
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest
    .repo_studios/tests/tests_command_center/dependency_import_hygiene -q`.
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
  - 2025-12-01: Confirmed we will stage Engineering Complexity Watch as its own orchestrator instead
    of merging structural complexity and inventory governance into Standards Integrity, aligning with
    RFC section 12 plus the runtime/ownership analysis from
    `.repo_studios/docs/automation/generate_lizard_report.md` and
    `.repo_studios/docs/automation/generate_dependency_hygiene_report.md`. The follow-up runner will
    ingest the existing Docs Health and Dependency & Import Hygiene artifacts alongside the standards
    summary so inventory governance can evolve independently.
  - 2025-12-01: Enumerated the Engineering Complexity Watch inputs by cross-referencing
    `.repo_studios/scripts/script_inventory_architecture.md` and the automation docs for
    `generate_lizard_report.py`, `render_inventory_views.py`, `check_inventory_health.py`,
    `validate_inventory.py`, `validate_metrics_anchor_stubs.py`, `generate_dependency_hygiene_report.py`,
    and the legacy `run_standards_index_cli.py` helper. All producers already emit structured
    bundles with pruning, pytest coverage, and Make targets, while the CLI surfaces filtered views of
    `latest_index.yaml`. Identified three gaps for the forthcoming orchestrator: (1) no shared
    summarizer currently blends the lizard, dependency hygiene, and inventory signals into a single
    Markdown/JSON Healthview payload; (2) `run_standards_index_cli.py` still writes to
    `.repo_studios/reports/orchestrator_runs/standards_index_cli/`, so the topic runner must mirror
    outputs into the Command Center Healthview slug and likely wrap the query logic behind a
    callable helper; (3) `check_inventory_health.py` depends on
    `reports/summary/latest/summary.json` plus `config/ci_inventory_thresholds.json`, so the
    orchestrator needs to schedule `render_inventory_views.py` (or another summary refresh) before
    invoking the health check and expose baseline overrides for CI parity.
  - 2025-12-01: Recorded rollout conditions for Engineering Complexity Watch—per
    `docs/automation/orchestrator_topic_refactor_rfc.md` section 10 the topic runner will remain in
    nightly-only mode until we capture runtime telemetry across the full `generate_lizard_report.py`
    + dependency hygiene + inventory sequence and review it with Platform Engineering and Standards
    Governance. The `generate_lizard_report.py` guide documents the repo-wide scan footprint, so the
    initial rollout avoids PR gating until runtime data demonstrates the pipeline fits existing CI
    budgets. The orchestrator will reuse `check_inventory_health.py` thresholds outlined in
    `docs/automation/ci_metrics_checks.md`, and stakeholder sign-off must confirm those guardrails are
    acceptable before wiring the topic into the meta-orchestrator schedule.
  - 2025-12-02: Re-evaluated the Engineering Complexity Watch scope against
    `.repo_studios/docs/automation/generate_lizard_report.md`,
    `.repo_studios/docs/automation/generate_dependency_hygiene_report.md`, and RFC section 12,
    confirming the rollout remains a unified orchestrator while documenting prerequisites (net-new
    summarizer, Healthview bundle wiring, runtime telemetry review) that must land before we schedule
    implementation.

## Phase Checklist

- [x] Phase 1 – Design Convergence — Completed 2025-12-02 after validating the 2025-11-29 topic
  inventory snapshot, mapping Healthview manifest fields, recording RFC approvals, documenting
  legacy retirement scope, and opening linked tickets for each legacy orchestrator.
- [x] Phase 2 – Library Foundations — Completed 2025-11-30
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
  - Stage migration of `test_log_analysis.py` into the shared library once naming-compliant
    scaffolding shipped on 2025-11-30 (helper relocated to `command_center/scripts/libraries/test_log_analysis.py`,
    with the legacy utility shim re-exporting the new module and pytest/documentation updates recorded).
- [x] Phase 3 – Topic Orchestrator Delivery — Completed 2025-12-02
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
  - 2025-12-01: Staged the legacy `run_fault_pipeline.py` shim to forward into
    `command_center/scripts/orchestrators/run_fault_diagnostics_overview.py` by default, translating
    key CLI knobs (`--output-dir`, `--command-center-dir`, `--artifacts-to-keep`) and injecting a
    `FAULT_PIPELINE_USE_LEGACY=1` escape hatch for the original pipeline. Updated
    `.repo_studios/tests/tests_orchestrators/test_run_fault_pipeline.py` to cover both the redirect
    and the legacy execution path, and backfilled the consumer module with a defensive `shutil`
    export so reuse flows remain intact during the transition.
  - [x] Deliver Docs Health orchestrator with aligned CLI surfaces.
    - 2025-12-02: Added `command_center/scripts/orchestrators/run_docs_health_overview.py`, wiring the Docs Health producers and aggregator through the shared topic pipeline with catalog registration, Healthview manifest emission, and retention knobs for every dependency. Published the `studio-orchestrate-docs-health` make target and validated the runner via `make -C .repo_studios studio-orchestrate-docs-health PYTHON=.venv/Scripts/python.exe` together with `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/docs_health -q`.
  - 2025-12-01: Delivered the Standards Integrity orchestrator with aligned CLI surfaces—retained the
    topic pipeline wiring in `run_standards_integrity.py`, added the `__main__` guard for direct CLI
    execution, and refreshed `studio-orchestrate-standards` to set `PYTHONPATH` on Windows and POSIX
    shells before launching the runner. Verified Healthview bundles under
    `.repo_studios/command_center/reports/healthview/standards_integrity/20251201-1857/` alongside
    refreshed producer outputs, and exercised the contract via
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity -q`
    together with `make -C .repo_studios studio-orchestrate-standards PYTHON=.venv/Scripts/python.exe`.
  - 2025-12-01: Delivered the Dependency & Import Hygiene orchestrator with aligned CLI surfaces,
    threading dependency hygiene → import graph → placeholder scan → optional batch cleanup →
    typecheck → optional mypy baseline refresh via the shared topic pipeline helpers. The runner
    mirrors Healthview manifests to
    `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/<timestamp>/`,
    registers each producer/utility in the catalog, honours retention knobs, and forwards skip or
    trigger flags (`--skip-import-graph`, `--skip-typecheck`, `--trigger-batch-cleanup`,
    `--refresh-mypy-baselines`). Validation covers artifact emission and failure telemetry through
    `.repo_studios/tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py`,
    exercised with
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/dependency_import_hygiene -q`.
  - 2025-12-01: Delivered the Monkey Patch Oversight orchestrator and companion summarizer with
    aligned CLI retention knobs, catalog registration, and viewer/topic manifest emission; see
    `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py` and
    `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py`.
  - 2025-12-01: Produced the detailed legacy-to-topic parity matrix in this plan (see “Detailed
    Legacy-to-Topic Parity Mapping”) documenting replacement scripts, CLI parity, artifact
    destinations, and retention knobs for `orchestrate_health_suite.py`, `run_pytest_log_capture.py`,
    `run_fault_pipeline.py`, `run_batch_cleanup.py`, `run_standards_gap_suite.py`, and
    `run_standards_index_cli.py`.
  - [x] Stage redirects or temporary shims for legacy orchestrators so tests and make targets can
    point to the new entry points without breaking interim workflows.
    - 2025-12-01: Fault pipeline shim now delegates to `run_fault_diagnostics_overview.py`.
    - 2025-12-01: Pytest log capture shim now defaults to
      `command_center/scripts/orchestrators/run_test_execution_telemetry.py`, translating CLI knobs such
      as `--output-dir` → `--healthview-root` and mirroring `--artifacts-to-keep` across the topic
      retention flags while preserving `PYTEST_LOG_CAPTURE_USE_LEGACY` for summary and pytest passthrough
      workflows; validated via `.venv/Scripts/python.exe -m pytest
      .repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py -q`.
    - 2025-12-01: Standards gap suite shim now fronts
      `command_center/scripts/orchestrators/run_standards_integrity.py`, remapping `--max-show` to
      `--gap-max-show`, threading index/gap directory overrides, and honoring
      `STANDARDS_GAP_USE_LEGACY` plus `--skip-index`/`--legacy-json` fallbacks for legacy parity;
      validated via `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_standards_gap_suite.py -q`
      and `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity -q`.
    - 2025-12-01: Batch cleanup shim now delegates to
      `command_center/scripts/orchestrators/run_dependency_import_hygiene.py` by default, translating
      retention knobs (`--artifacts-to-keep` → `--cleanup-artifacts-to-keep`), enforcing topic-only
      execution unless `RUN_BATCH_CLEANUP_USE_LEGACY=1` or legacy-only flags are supplied, and
      auto-appending `--skip-import-graph` / `--skip-typecheck` so the redirect mirrors the original
      cleanup scope. Covered via `.venv/Scripts/python.exe -m pytest
      .repo_studios/tests/tests_orchestrators/test_run_batch_cleanup.py -q`.
    - 2025-12-01: Standards index CLI now shells into
      `command_center/scripts/orchestrators/run_standards_integrity.py` ahead of processing `list`
      / `search` / `show` / `stats` commands, forwarding repo-root and retention knobs while
      exposing `RUN_STANDARDS_INDEX_CLI_USE_LEGACY=1` for operators who need the standalone query
      workflow. The shim still emits structured CLI artifacts and reports redirect telemetry, with
      coverage added via `.venv/Scripts/python.exe -m pytest
      .repo_studios/tests/tests_orchestrators/test_run_standards_index_cli.py -q`.
    - 2025-12-01: Audited make aliases and ad-hoc scripts; none shell the CLI in automation, and interactive guidance now sets `RUN_STANDARDS_INDEX_CLI_USE_LEGACY` only when operators intentionally skip the redirect.
    - 2025-12-01: Distributed the updated CLI instructions to Standards Ops analysts (Slack #standards-index) with links to the refreshed runbook so manual queries adopt the redirect-aware workflow.
    - 2025-12-02: `orchestrate_health_suite.py` now shells into the topic orchestrators by default,
      triggering Dependency & Import Hygiene (with batch cleanup and mypy baseline refresh), Test
      Execution Telemetry, Docs Health, Fault Diagnostics, Monkey Patch Oversight, and Standards
      Integrity via their shared `run()` shims while preserving the legacy pipeline behind
      `HEALTH_SUITE_USE_LEGACY=1`; the shim continues to emit health-suite status artifacts and
      logs the redirect for operators.
  - [x] Evaluated the Engineering Complexity Watch pipeline scope on 2025-12-02, reaffirming the
    RFC section 12 decision to stage a unified orchestrator while cataloguing prerequisites (net-new
    summarizer, Healthview bundle wiring, runtime telemetry review) and deferring implementation
    until those gating items land.
  - [x] Updated the topic orchestrator README and inline module docstrings on 2025-12-02 to document
    Healthview artifact locations, legacy replacements, and expected runtime footprints for each
    topic runner (`.repo_studios/command_center/scripts/orchestrators/README.md` and module docstrings
    refreshed accordingly).
- [x] Phase 4 – Summaries and Healthview Artifacts — Completed 2025-12-07 after validating topic summarizer suites and publishing the Healthview manifest guidance.
  - 2025-12-03: Updated the health suite and standards summarizers to consume the shared command
    center helper stack, emit Healthview-aligned JSON/Markdown bundles, and prune legacy mirrors;
    refreshed `.repo_studios/scripts/summarizers/summarize_health_suite.py` and
    `.repo_studios/scripts/summarizers/summarize_standards.py`, added the legacy `summarize()` shim
    for orchestrator compatibility, and validated via
    `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_summarizers/test_summarize_health_suite.py .repo_studios/tests/tests_summarizers/test_summarize_standards.py`.
  - 2025-12-04: Authored the Test Execution Telemetry summarizer
    (`.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`),
    wiring the orchestrator manifest to consume it, capturing JSON/Markdown Healthview bundles, and
    validating with `.venv/Scripts/python.exe -m pytest
    .repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py
    .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py`.
  - 2025-12-04: Published the Healthview manifest schema narrative and JSON example under
    `docs/automation/examples/healthview_manifest_example.md` and refreshed the plan section to
    reference slug placement, bundle naming, and viewer integration notes.
- [ ] Phase 5 – Meta-Orchestrator and Tooling
  - [x] Implement `orchestrate_full_diagnostic.py` with include/exclude controls, manifest
    emission, and stop-on-first-failure toggles.
    - 2025-12-04: Added `.repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py`
      with module caching, topic selection guards, manifest/summary/telemetry emission via
      `write_report_artifacts`, and CLI options for include/exclude plus failure handling; validated
      with `.venv/Scripts/python.exe -m pytest
      .repo_studios/tests/tests_command_center/orchestrators/test_orchestrate_full_diagnostic.py -q`.
  - [x] Add `studio-orchestrate-<topic>` and `studio-orchestrate-full-diagnostic` make targets with
    logging guidance for local runs.
    - 2025-12-04: Expanded `.repo_studios/Makefile` with `LOG_LEVEL` defaults, pre-run logging
      prompts, and new targets for `studio-orchestrate-test-execution-telemetry`,
      `studio-orchestrate-dependency-import-hygiene`, `studio-orchestrate-monkey-patch-oversight`,
      and `studio-orchestrate-full-diagnostic`; refreshed existing topic targets to honour the same
      log-level override so local runs can dial verbosity without editing Python modules.
  - 2025-12-05: Introduced telemetry counters for runtime and artifact sizing, updating
    `command_center/scripts/libraries/telemetry_emitters.py` and
    `command_center/scripts/orchestrators/orchestrate_full_diagnostic.py` to record per-topic and
    meta-level runtimes plus artifact counts; validated via
    `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/orchestrators -q`
    and confirmed manifest/telemetry outputs at
    `.repo_studios/command_center/reports/healthview/full_diagnostic/20251205-1448/` before cleanup.
  - 2025-12-05: Invoked the naming-audit utility inside documentation/reporting orchestrators so
    Docs Health and Standards Integrity runs fail fast when `latest_*` aliases or other
    non-compliant artifacts linger.
- [ ] Phase 6 – Documentation and Adoption
  - [x] Update `.repo_studios/scripts/script_inventory_architecture.md` and automation guides with
    new orchestrators and helper references.
    - 2025-12-05: Refreshed the script inventory to catalog Docs Health, Dependency & Import Hygiene,
      Standards Integrity, and the Command Center pipeline orchestrators alongside the
      `guardrails` helper, and expanded `orchestrator_automation_hooks.md` with dependency/import hygiene
      surfaces plus naming-audit guardrail enforcement notes. Validated the updates via
      `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py -q`.
  - [x] Publish Healthview onboarding material for Command Center, including tab wiring notes,
    slug placement, and viewer-specific CSS/JS considerations.
    - 2025-12-05: Authored `docs/automation/healthview_onboarding.md`, detailing selector wiring,
      viewer tab integration, naming expectations, and CSS/JS guardrails so Command Center crews can
      activate the Healthview tab without regressions. Documentation-only change; no tests required
      beyond existing linting standards.
  - [x] Announce migration timelines, flag deprecated targets, and capture agent integration
    outcomes.
    - 2025-12-05: Published `docs/automation/orchestrator_migration_announcement.md` with the cutover
      schedule, flagged legacy aliases in
      `.repo_studios/docs/automation/orchestrator_automation_hooks.md`, and recorded the Healthview
      prompt validation (`.repo_studios/command_center/docs/phase_6/validation_runs/2025-12-05-healthview_prompt_review.md`,
      `PROMPT_VALIDATION_RESULTS.md`) confirming agents recognise the new viewer and topic targets.
  - [x] Produce a cleanup checklist covering legacy doc pages, README pointers, and references in
    tests so removal work is traceable.
    - 2025-12-05: Authored `docs/automation/orchestrator_legacy_cleanup_checklist.md` capturing
      documentation, Makefile, test, CI, and artifact retirement tasks so Phase 8 can track shim
      removal and report cleanup.
- [ ] Phase 7 – Validation and Rollout
  - [x] Run sequential dry runs across all topics, recording runtimes, artifact paths, and
    summariser outputs.
    - 2025-12-07: Invoked the full diagnostic meta orchestrator via
      `command_center.scripts.orchestrators.orchestrate_full_diagnostic.run()` with `--keep-going`
      (repo root `C:/Users/genet/repo_studios`), producing
      `.repo_studios/command_center/reports/healthview/full_diagnostic/20251207-0239/` with a
      19.1s runtime (5/6 topics succeeded). The dependency/import hygiene topic exited with status
      `failed` because the typecheck step reported `status=error` despite zero logged errors in
      `.repo_studios/reports/producer_reports/typecheck_reports/typecheck-20251207_023916/`; captured
      telemetry lives alongside the slugged bundle for follow-up analysis.
    - Follow-up: Audit the dependency/import hygiene telemetry at
      `.repo_studios/command_center/reports/healthview/dependency_import_hygiene/20251207-0239/` and
      the associated typecheck producer output to determine why the run surfaced `status=error`
      before rerunning the suite.
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

- [x] 2025-12-07: `./.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_summarizers/test_summarize_health_suite.py .repo_studios/tests/tests_summarizers/test_summarize_standards.py .repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py -q` — summarizer suites remain ≥80% coverage, confirming Phase 4 artifacts stay healthy.
- [x] 2025-12-07: Updated `docs/automation/orchestrator_implementation.md` to mark Phase 4 complete and preserve Healthview manifest guidance for topic summaries.
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
- 2025-12-03: Modernised the health suite and standards summarizers to write Healthview-compliant
  bundles via `write_report_artifacts`, retained orchestrator compatibility with a legacy shim in
  `.repo_studios/scripts/summarizers/summarize_standards.py`, tightened prompt retention defaults in
  `command_center/scripts/orchestrators/run_standards_integrity.py`, and revalidated coverage with
  `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_summarizers/test_summarize_health_suite.py .repo_studios/tests/tests_summarizers/test_summarize_standards.py`.
- 2025-12-04: Landed the Test Execution Telemetry summarizer at
  `.repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py`, updated
  `run_test_execution_telemetry.py` to register the Healthview summary artifacts, and validated the
  workflow via `.venv/Scripts/python.exe -m pytest
  .repo_studios/tests/tests_command_center/test_execution_telemetry/test_summarize_test_execution_telemetry.py
  .repo_studios/tests/tests_command_center/orchestrators/test_run_test_execution_telemetry.py` to
  keep coverage above the 80% threshold for both the summarizer and orchestrator modules.
- 2025-12-04: Published the Healthview manifest example under
  `docs/automation/examples/healthview_manifest_example.md`, documenting slug placement, bundle
  naming, and selector integration guidance; documentation-only update, no tests required.
- [x] 2025-12-05: Captured runtime and artifact sizing telemetry in
  `command_center/scripts/libraries/telemetry_emitters.py` and the meta orchestrator, exercised via
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/orchestrators -q`
  with manual verification of `.repo_studios/command_center/reports/healthview/full_diagnostic/20251205-1448/{manifest.json,telemetry.json}`.
- [x] 2025-12-05: Wired `enforce_report_naming` guardrails into Docs Health
  (`.repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py`) and Standards
  Integrity (`.repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py`),
  extending failure-path coverage in
  `.repo_studios/tests/tests_command_center/docs_health/test_run_docs_health_overview.py` and
  `.repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py`;
  validated with
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/docs_health/test_run_docs_health_overview.py`
  and
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity/test_run_standards_integrity.py`
  to confirm non-compliant artifacts now halt the orchestrators.
- [x] 2025-12-05: Published `docs/automation/healthview_onboarding.md`, capturing selector wiring,
  viewer tab integration steps, naming expectations, and CSS/JS safeguards for the Healthview
  launch. Documentation-only update; no tests required beyond existing markdown standards.
- 2025-12-05: Posted `docs/automation/orchestrator_migration_announcement.md`, added migration
  notices to `.repo_studios/docs/automation/orchestrator_automation_hooks.md`, and archived the
  Healthview prompt review results in
  `.repo_studios/command_center/docs/phase_6/validation_runs/2025-12-05-healthview_prompt_review.md`
  plus `PROMPT_VALIDATION_RESULTS.md`.
- 2025-12-05: Created the legacy cleanup tracker at
  `docs/automation/orchestrator_legacy_cleanup_checklist.md` so Phase 8 decommissioning can retire
  documentation, Make aliases, tests, CI references, and legacy report folders in a controlled,
  auditable sequence (documentation-only update).
- [x] 2025-12-04: Added LOG_LEVEL-aware make targets in `.repo_studios/Makefile` for
  `studio-orchestrate-test-execution-telemetry`, `studio-orchestrate-dependency-import-hygiene`,
  `studio-orchestrate-monkey-patch-oversight`, and `studio-orchestrate-full-diagnostic`, plus
  refreshed existing topic targets with the same logging guidance; verified wiring with
  `make -C .repo_studios studio-orchestrate-test-execution-telemetry LOG_LEVEL=DEBUG --dry-run` to
  confirm command resolution without kicking off long pipelines.
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
- 2025-12-02: Re-evaluated Engineering Complexity Watch prerequisites by reviewing
  `.repo_studios/docs/automation/generate_lizard_report.md`,
  `.repo_studios/docs/automation/generate_dependency_hygiene_report.md`, and
  `docs/automation/orchestrator_topic_refactor_rfc.md` section 12, documenting the unified-orchestrator
  decision and gating actions in `docs/automation/orchestrator_implementation.md`; documentation-only,
  no tests executed.
- 2025-12-01: Redirected `run_pytest_log_capture.py` to the Test Execution Telemetry orchestrator by
  default, retaining the `PYTEST_LOG_CAPTURE_USE_LEGACY` escape hatch for summary and pytest
  passthrough flows and confirming both redirect and legacy behaviour via
  `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_pytest_log_capture.py -q`
  and `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_fault_pipeline.py -q`.
- 2025-12-01: Redirected `run_standards_gap_suite.py` to the Standards Integrity topic runner by
  default, translating `--max-show` to `--gap-max-show`, carrying directory overrides forward, and
  retaining `STANDARDS_GAP_USE_LEGACY` / `--skip-index` / `--legacy-json` escape hatches; confirmed via
  `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_standards_gap_suite.py -q`
  together with `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity -q`.
- 2025-12-02: Marked Phase 2 – Library Foundations complete in
  `docs/automation/orchestrator_implementation.md` and revalidated the Dependency & Import Hygiene
  orchestrator plan by running `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest
  .repo_studios/tests/tests_command_center/dependency_import_hygiene -q`, confirming Healthview bundle
  emission and telemetry alignment without additional code changes.
- 2025-12-02: Closed Phase 3 – Topic Orchestrator Delivery after auditing
  `docs/automation/orchestrator_implementation.md` to ensure every topic orchestrator milestone and
  associated validation is captured; phase checklist updated to reflect completion (documentation
  change only, no new test command executed).
- 2025-12-01: Validated Fault Diagnostics orchestrator delivery by executing
  `make -C .repo_studios studio-orchestrate-fault-diagnostics PYTHON=.venv/Scripts/python.exe`,
  inspecting `.repo_studios/command_center/reports/commandview/fault_diagnostics/20251201-1313/manifest.json`
  for aligned artifact pointers, and running
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/fault_diagnostics -q`
  to confirm orchestrator + summarizer test coverage.
- 2025-12-01: Verified Standards Integrity delivery end-to-end—ran
  `make -C .repo_studios studio-orchestrate-standards PYTHON=.venv/Scripts/python.exe` after baking the
  cross-platform `PYTHONPATH` export, inspected
  `.repo_studios/command_center/reports/healthview/standards_integrity/20251201-1857/manifest.json`, and
  reran the contract test suite via
  `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_command_center/standards_integrity -q`.
- 2025-12-01: Finalised Engineering Complexity Watch scope by revisiting RFC section 12 together with
  `.repo_studios/docs/automation/generate_lizard_report.md` and
  `.repo_studios/docs/automation/generate_dependency_hygiene_report.md`, confirming the topic will
  remain a standalone orchestrator that reuses existing Docs Health and Dependency & Import Hygiene
  artifacts via the follow-up runner. Documentation-only decision; no code changes or tests executed.
- 2025-12-01: Enumerated the Engineering Complexity Watch inputs using
  `.repo_studios/scripts/script_inventory_architecture.md` plus the automation docs for
  `generate_lizard_report.py`, `render_inventory_views.py`, `check_inventory_health.py`,
  `validate_inventory.py`, `validate_metrics_anchor_stubs.py`, `generate_dependency_hygiene_report.py`,
  and `run_standards_index_cli.py`, noting the absence of a blended summarizer, the need to relocate
  the CLI outputs into Healthview-friendly directories, and the requirement to refresh inventory
  summaries before running `check_inventory_health.py`. Documentation review only; tests were not
  executed.
- 2025-12-01: Documented Engineering Complexity Watch rollout conditions, keeping the topic runner
  in nightly-only mode until runtime telemetry from `generate_lizard_report.py` + dependency hygiene +
  inventory checks is reviewed with Platform Engineering and Standards Governance stakeholders.
  Confirmed the orchestrator will reuse the `check_inventory_health.py` thresholds from
  `docs/automation/ci_metrics_checks.md` and defer meta-orchestrator wiring until approvals land.
- 2025-12-02: Closed Phase 1 – Design Convergence after re-checking the 2025-11-29
  CommandView inventory bundle (`.repo_studios/scripts/scripts_index/scripts_commandview_20251129-2102.json`),
  confirming the Healthview manifest mapping updates in this plan, and ensuring every legacy
  retirement ticket recorded in the parity matrix remains linked to its orchestrator scope.
- 2025-12-01: Compiled the detailed legacy-to-topic parity matrix inside this plan, capturing CLI
  parity, artifact destinations, and retention expectations for every legacy orchestrator; no code
  changes or tests were required (documentation update only).
- 2025-12-01: Staged the `run_fault_pipeline.py` redirect to
  `command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`, added the
  `FAULT_PIPELINE_USE_LEGACY` escape hatch for reuse flows, patched the topic orchestrator return
  indentation, injected a defensive `shutil` export for the legacy consumer hook, and validated with
  `.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_orchestrators/test_run_fault_pipeline.py -q`.
