---
title: Orchestrator Implementation Plan
status: draft
version: 2025-11-29
last_updated: 2025-11-29
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

- **Make Targets**: `studio-orchestrate-health-suite`, `studio-run-fault-pipeline`,
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

## Topic Assignment Validation (2025-11-29)

- CommandView bundle `scripts_commandview_20251129-2102.json` confirms 45 of 46 planned topic
  scripts are present; `test_log_analysis.py` lives under `.repo_studios/scripts/utilities/` and
  requires inclusion or alternative coverage in the Test Execution Telemetry pipeline.
- All other topic lists (Fault Diagnostics, Docs Health, Standards Integrity, Dependency & Import
  Hygiene, Monkey Patch Oversight, Engineering Complexity Watch) align with the inventory by
  basename.
- Next step: decide whether to import `test_log_analysis.py` via helper wiring or run the utility
  directly from the topic orchestrator to maintain parity with current workflows.

## Topic Implementation Workstreams

- **Test Execution Telemetry**
  - [ ] Confirm inventory of dependent producers/consumers (pytest log capture, collectors, churn
    heatmap, coverage inventory, hardening analysis) using the latest CommandView bundle.
  - [ ] Define orchestration order, required CLI flags, and dependency wiring (e.g., coverage JSON
    inputs, retention budgets).
  - [ ] Identify and migrate associated fixtures from `tests/tests_command_center/test_health_suite`
    and `tests/tests_orchestrators/test_run_pytest_log_capture.py`.
  - [ ] Draft Markdown summary template for Healthview, including runtime metrics and failure
    highlights.
- **Fault Diagnostics**
  - [ ] Map producer/consumer handoff expectations from `run_fault_pipeline.py`, including
    faulthandler environment variables and legacy directory fallbacks.
  - [ ] Design fault summary sections (repeat offenders, baseline drift) and required data pulls
    from crash artifacts.
  - [ ] Validate retention policies for producer/consumer outputs and align them with Healthview
    mirroring.
- **Docs Health**
  - [ ] Aggregate script list (doc index, anchor inventory/validation, churn report, undocumented
    logic report) and capture input dependencies (e.g., doc index cache).
  - [ ] Plan summariser structure with sections for anchor integrity, undocumented logic, and churn
    highlights.
  - [ ] Audit documentation under `docs/automation/` for references to standalone scripts and
    stage updates for the seeding orchestrator.
- **Standards Integrity**
  - [ ] Consolidate standards scripts (index generator, gap analyser, diff tool, prompt seeding,
    summariser) and ensure they use shared helper settings.
  - [ ] Determine whether Engineering Complexity Watch responsibilities remain bundled here or
    split based on RFC discussion.
  - [ ] Update standards governance docs and CI definitions to reference the topic orchestrator.
- **Dependency & Import Hygiene**
  - [ ] Outline sequence for dependency hygiene, import graph, placeholder scans, batch cleanup,
    and typecheck runs to ensure consistent outputs.
  - [ ] Reconcile existing lint/mypy/placeholder make targets with the new orchestrator CLI.
  - [ ] Capture utility hooks (e.g., placeholder debt allowlist, typecheck baselines) required for
    parity.
- **Monkey Patch Oversight**
  - [ ] Collect scripts (scan, classify, risk scoring, trend analysis) and required shared state or
    caches.
  - [ ] Define summariser artefacts that integrate with duplicate detection tooling or Healthview
    dashboards.
  - [ ] Verify test coverage in `tests/tests_command_center/monkey_patch` and plan migrations.
- **Engineering Complexity Watch (stretch)**
  - [ ] Decide whether to merge structural complexity and inventory governance or stage separate
    orchestrators.
  - [ ] Enumerate script set (lizard report, inventory validation, metrics stubs, standards index
    CLI) and identify any tooling gaps.
  - [ ] Document rollout conditions (runtime budgets, stakeholder sign-off) before implementation.

## Phase Checklist

- [ ] Phase 1 – Design Convergence
  - [ ] Validate topic script assignments against the 2025-11-29 inventory bundle.
  - [ ] Finalise Healthview manifest schema by mapping CommandView fields to the new slug layout.
  - [ ] Record RFC decisions in section 13 with approvals and outstanding risks.
  - [ ] Document legacy removal scope (modules, tests, docs, artifacts) in issue tracker tickets so
    teams can claim discrete workstreams.
  - [ ] Open issue tickets for legacy orchestrator retirement (one per legacy runner) and link them
    to the parity matrix for cross-team tracking.
- [ ] Phase 2 – Library Foundations
  - [ ] Implement `build_topic_pipeline`, `summarizer_runner`, `telemetry_emitters`, and
    `catalog_registry` helpers with unit tests.
  - [ ] Ensure helpers honour ASCII naming, repo logging configuration, and pruning semantics.
  - [ ] Document helper usage patterns inside `.repo_studios/command_center/docs/`.
  - [ ] Provide migration notes demonstrating how existing orchestrators would call the helpers if
    they were rewritten today, helping reviewers validate parity.
- [ ] Phase 3 – Topic Orchestrator Delivery
  - [ ] Ship Test Execution Telemetry orchestrator with end-to-end fixtures and Markdown snapshot
    tests.
  - [ ] Deliver Fault Diagnostics, Docs Health, Standards Integrity, Dependency & Import Hygiene,
    and Monkey Patch Oversight orchestrators with aligned CLI surfaces.
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
