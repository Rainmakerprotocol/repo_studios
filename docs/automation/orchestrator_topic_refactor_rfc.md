# RFC: Topic-Oriented Orchestrator Refactor

## 1. Overview

This RFC proposes restructuring the Repo Studios orchestration layer around
topic-aligned pipelines so every automation script is executed through a
consistent orchestrator entry point. The document summarizes roadmap context,
expected benefits, design details, and rollout steps that convert the working
notes in `.repo_studios/scripts/orchestrator_refactor_plan_temp.md` into an
implementable initiative.

## 2. Motivation

- Orchestrator coverage currently reaches 18 of 47 managed scripts, leaving
  29 utilities and producers outside scheduled runs.
- Summaries and reports are inconsistent, with several topic areas lacking the
  Markdown artifacts agents and humans rely on.
- Reporting retention and logging behaviors drift across orchestrators because
  common helpers (`PathsConfig`, `OptionsConfig`, pruning utilities) are not
  universally adopted.
- Downstream consumers (Command Center, agents, manual reviewers) need a single
  meta-orchestrator to refresh diagnostics in one pass.

## 3. Goals

- Establish topic-oriented orchestrators that group related producers,
  consumers, aggregators, and summarizers.
- Ensure every managed script participates in at least one orchestrator run.
- Standardize artifact shape (JSON bundles + Markdown digest) and retention
  behavior via shared helpers.
- Provide CLI surfaces (`studio-orchestrate-<topic>`) and a
  `studio-orchestrate-full-diagnostic` meta-runner for developers and agents.
- Document testing, documentation, and migration expectations so rollout can be
  staged without regressions.

## 4. Non-Goals

- Rewriting existing producer logic beyond what is required for orchestrator
  compatibility.
- Altering legacy make targets until new orchestrators reach parity and pass
  rollout validation.
- Delivering parallel execution in the first iteration; the meta-orchestrator
  will run sequentially initially.

## 5. Proposed Architecture

### 5.1 Topic-Oriented Orchestrators

Each topic orchestrator:

- Runs all producer/consumer/aggregator steps for its focus area.
- Invokes (or introduces) a summarizer to emit Markdown for humans, Command
  Center viewers, and agent workflows.
- Mirrors structured bundles and summaries into
  `.repo_studios/command_center/reports/<topic>/` while enforcing shared
  retention budgets.
- Consumes Command Center helpers (`PathsConfig`, `OptionsConfig`,
  `copy_latest_artifact`, `write_report_artifacts`) instead of duplicating
  boilerplate.
- Documents utilities that are missing for the topic and opens backlog tickets
  where gaps exist.

### 5.2 Topic Buckets and Script Assignments (initial draft)

| Topic | Candidate Scripts | Notes |
| --- | --- | --- |
| Test Execution Telemetry | `run_pytest_log_capture.py`, `collect_test_log_reports.py`, `generate_test_log_health_report.py`, `generate_churn_complexity_heatmap.py`, `generate_test_coverage_inventory.py`, `test_log_analysis.py`, `analyze_test_hardening.py` | Captures live test signals, duration trends, and warning density; feeds the health-suite summarizer. |
| Fault Diagnostics | `dump_faulthandler_snapshot.py`, `collect_faulthandler_reports.py`, `generate_fault_artifacts.py`, `fault_run_analysis.py`, `configure_faulthandler_runtime.py`, `refresh_mypy_baselines.py` | Consolidates crash triage and baseline refresh tooling; summary highlights repeat offenders and baseline drift. |
| Docs Health | `generate_doc_index.py`, `generate_anchor_inventory.py`, `generate_anchor_health_report.py`, `validate_markdown_anchors.py`, `verify_docs_integrity.py`, `generate_code_doc_churn_report.py`, `generate_undocumented_logic_report.py`, `aggregate_docs_health_signals.py` | Produces documentation governance bundle and Markdown digest for Command Center. |
| Standards Integrity | `generate_standards_index.py`, `analyze_standards_index_gaps.py`, `diff_standards_index.py`, `extract_standards_rules.py`, `seed_standards_prompts.py`, `summarize_standards.py` | Maintains standards inventory coherence; orchestrator threads regeneration, gap analysis, and prompt seeding. |
| Dependency & Import Hygiene | `generate_dependency_hygiene_report.py`, `validate_import_boundaries.py`, `scan_code_placeholders.py`, `generate_import_graph_report.py`, `run_batch_cleanup.py`, `generate_typecheck_report.py` | Targets dependency risk, layering violations, and static cleanup; utilities applied pre/post runs. |
| Monkey Patch Oversight | `scan_monkey_patches.py`, `classify_monkey_patches.py`, `monkey_patch_risk.py`, `analyze_monkey_patch_trends.py` | Dedicated pipeline for runtime monkey-patch detection and trend analysis. |
| Engineering Complexity Watch (stretch) | `generate_lizard_report.py`, `render_inventory_views.py`, `check_inventory_health.py`, `validate_metrics_anchor_stubs.py`, `validate_inventory.py`, `run_standards_index_cli.py`, `run_standards_gap_suite.py` | Monitors structural complexity and inventory governance; scope to be validated before implementation. |

### 5.3 Meta-Orchestrator

A new meta-runner (`orchestrate_full_diagnostic.py`) will sequentially invoke
all topic orchestrators with a shared configuration payload. It will accept an
include/exclude list, thread a consistent log level, and produce a manifest that
records success, failure, and artifact locations per topic. Parallel execution
remains an optional enhancement once the sequential baseline stabilizes.

## 6. Shared Helper Enhancements

Extend `.repo_studios/command_center/scripts/libraries/` with reusable helpers:

- `build_topic_pipeline(topic_config)` to standardize orchestrator setup and
  reduce per-file boilerplate.
- `summarizer_runner` to consolidate summary invocation, bundle mirroring, and
  retention pruning.
- `telemetry_emitters` to record orchestrator status payloads for the
  meta-runner.
- `catalog_registry` (JSON/YAML) enumerating script → orchestrator mappings for
  auditability and coverage assertions.

All helpers must follow existing naming conventions (`verb_noun`) and remain
ASCII-only per repository guidance.

## 7. Artifact Management and Retention

- Adopt shared retention defaults (target: 5 runs) exposed via CLI overrides.
- Emit a consistent bundle shape for each orchestrator: `bundle_summary.json`,
  Markdown digest, JSON manifest, and symbolic `latest_*` pointers.
- Mirror outputs into
  `.repo_studios/command_center/reports/<topic>_orchestrator/` via existing
  helpers (`copy_latest_artifact`, `prune_run_directories`).

## 8. Testing Strategy

- **Unit Tests**: Exercise each orchestrator's `run()` helper and CLI shim using
  path builder mocks, retention hooks, summarizer invocation assertions, and
  failure propagation scenarios.
- **Integration Smoke**: Execute orchestrators against fixture directories
  reseeded from existing producers to validate cross-script choreography.
- **Markdown Snapshots**: Lock critical sections of generated summaries to
  prevent regressions in agent-facing content.
- **Meta-Orchestrator Coverage**: Verify ordering, stop-on-failure behavior, and
  manifest emission for the top-level runner.
- **Coverage Ledger**: Update the script coverage ledger to assert that every
  managed script is exercised through orchestrator tests.

## 9. Documentation Plan

- Update `.repo_studios/scripts/script_inventory_architecture.md` to reflect new
  orchestrators and coverage status.
- Author topic-specific automation guides under `docs/automation/` describing
  inputs, outputs, CLI arguments, and retention settings.
- Refresh `docs/automation/orchestrator_automation_hooks.md` to enumerate new
  make targets and usage examples.
- Capture summarizer schema expectations in
  `docs/standards/global/std-global-markdown-authoring.md` if new sections are
  introduced.
- Provide a developer-focused README or overview in Command Center docs to
  detail meta-orchestrator usage.

## 10. Rollout Phases

1. **Design Finalization**: Confirm topic boundaries, summarizer needs, and
   success metrics; socialize this RFC for sign-off.
2. **Library Prep**: Implement shared helpers and catalog registry to unblock
   orchestrator implementation.
3. **Topic Orchestrator Delivery**: Build orchestrators incrementally, starting
   with Test Execution Telemetry, and land unit/integration tests with each.
4. **Summarizer Alignment**: Update existing summaries (health suite, standards)
   and author new ones where topics lack coverage.
5. **Meta-Orchestrator Build**: Implement the sequential meta-runner, CLI, and
   manifest reporting.
6. **Documentation + Make Targets**: Publish updated docs, add
   `studio-orchestrate-<topic>` and `studio-orchestrate-full-diagnostic`
   targets, and note transition guidance.
7. **Validation & Launch**: Run dry runs, ensure CI stability, verify Command
   Center + agent integration, and schedule the rollout announcement.

## 11. Risks and Mitigations

- **Long-Running Pipelines**: Sequential execution may extend runtimes; provide
  topic selection flags and monitor runtime metrics before enabling parallelism.
- **Data Dependency Collisions**: Timestamped producer outputs can conflict; use
  deterministic naming and ensure orchestrators cleanly hand off artifacts.
- **Summarizer Scope Creep**: Guard against duplicated content by agreeing on
  topic-level vs. meta-level summary responsibilities early in implementation.
- **Backward Compatibility**: Maintain existing make targets during rollout and
  announce deprecation timelines in advance.
    Immediately depreciate old targets once new orchestrators reach parity.
- **Agent Adoption**: Define the manifest schema up front so agents can consume
  the new outputs without churn.

## 12. Open Questions

- Should Engineering Complexity Watch remain a single orchestrator or split into
  separate structural complexity and inventory governance pipelines?

ANSWER: Start unified; split if runtime or scope demands.

- Which topic should deliver the first net-new summarizer, and how do we balance
  detail vs. readability across Markdown outputs?

ANSWER: Test Execution Telemetry is a strong candidate due to its broad impact.

- Is additional telemetry (e.g., run duration, artifact size) required for the
  meta-orchestrator manifest to satisfy future observability goals?

ANSWER: Start with success/failure and artifact paths; expand as needed for the human readable summary.
There is stil the format for the .json for the viewer to consume. The viewer uses mermaid .js and
can be seen in the command center documentation and the `generate_commandview_inventory.py` script.
Which we use the "commandview" slug for location purposes. So we should be using similar format for
the orchestrator manifest, such as in place of "commandview" we use "healthview" or similar.
The AI view can be duplicitous with the healthview, right?
The last consideration is the best view for agents to consume. Would they want the same view as humans?

## 13. Decision Record

- **2025-11-29 – Report Naming Standard**: Adopt the viewer-centric path schema
  `<root>/<viewer_slug>/<topic>/<timestamp>/<artifact_role>.<ext>` for all
  orchestrator and Command Center reports. New artifacts must comply
  immediately; historical bundles remain grandfathered until migrated during
  implementation. `latest_*` aliases are deprecated and will be removed once
  the audit and helper updates land. Canonical reference: `REPORT_NAMING_STANDARDS.md`.

## 14. References

- `.repo_studios/scripts/orchestrator_refactor_plan_temp.md`
- `.repo_studios/scripts/script_inventory_architecture.md`
- Existing orchestrators: `orchestrate_health_suite.py`, `run_fault_pipeline.py`,
  `run_standards_gap_suite.py`
- Command Center helper modules in
  `.repo_studios/command_center/scripts/libraries/`
