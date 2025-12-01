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
    `summarize_health_suite.py`; helper dependency on `utilities/test_log_analysis.py` remains
    outside the CommandView bundle.
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
- Gap tracking: `utilities/test_log_analysis.py` is absent from the CommandView index, so Phase 2
  helper work must decide whether to import it explicitly or provide an alternative ingestion
  path for Test Execution Telemetry.
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
  - [x] Validate topic script assignments against the 2025-11-29 inventory bundle (see 2025-11-30 snapshot).
  - [x] Finalise Healthview manifest schema by mapping CommandView fields to the new slug layout (see Healthview Manifest Mapping section).
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
  - [ ] Provide migration notes demonstrating how existing orchestrators would call the helpers if
    they were rewritten today, helping reviewers validate parity.
  - [ ] Stage migration of `test_log_analysis.py` into the shared library once naming-compliant scaffolding ships (tracked for Phase 2).
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
