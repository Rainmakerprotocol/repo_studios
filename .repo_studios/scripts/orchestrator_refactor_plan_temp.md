# Orchestrator Refactor Plan (Working Notes)

## 1. Purpose

- Capture the scope and sequencing for re-shaping the orchestration layer so every script participates
    in an orchestrator-run pipeline.
- Document test, pruning, logging, and documentation work required for the new topology.
- Provide a checklist that can graduate into a permanent RFC once decisions solidify.

## 2. Current Snapshot

- Total scripts under management: 47.
- Scripts covered by `orchestrate_health_suite.py`: 15.
- Scripts additionally covered by other orchestrators (`command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`,
    `run_standards_gap_suite.py`): 3.
- Scripts without orchestrator coverage: 29 (spanning aggregators, consumers, orchestrators,
    producers, summarizers, utilities).
- Summarizers currently tied to orchestrators: health suite only; standards summarizer is standalone.

## 3. Target Topology

- **Topic-Oriented Orchestrators**: Establish one orchestrator per health "topic" (e.g., Test
    Execution Telemetry, Fault Diagnostics, Docs Health, Standards Integrity, Dependency
    Hygiene, Engineering Hygiene).
- **Orchestrator Responsibilities**:
  - Run all producer/consumer/aggregator steps for the topic.
  - Invoke the paired summarizer (if applicable) to emit Markdown for humans/command_center viewers/agents.
  - Mirror structured bundles and summary artifacts into `.repo_studios/command_center/reports/<topic>/`.
  - Surface retention budgets and logging controls sourced from command_center
    `OptionsConfig`/`PathsConfig` helpers.
  - Validate whether topic-specific utilities exist; when absent, document whether a helper should
    be authored or why it is unnecessary.
- **Utility Integration**: Utilities become first-class dependencies—each orchestrator either
    consumes an existing utility (timed at the most useful stage) or records a backlog
    item to fill a gap.
- **Meta-Orchestrator**: Create a top-level runner that sequentially invokes each topic
    orchestrator (configurable include/exclude list, parallelism optional later).
- **Make Targets**: Provide `studio-orchestrate-<topic>` per topic, plus
    `studio-orchestrate-full-diagnostic` for the meta runner.

## 4. Topic Buckets and Script Assignments (Draft)

| Topic | Candidate Scripts | Notes |
| --- | --- | --- |
| Test Execution Telemetry | `run_pytest_log_capture.py`, `collect_test_log_reports.py`, `generate_test_log_health_report.py`, `generate_churn_complexity_heatmap.py`, `generate_test_coverage_inventory.py`, `test_log_analysis.py`, `analyze_test_hardening.py` | Focused on live test signals, duration trends, and warning density; outputs feed the health-suite summarizer. |
| Fault Diagnostics | `dump_faulthandler_snapshot.py`, `collect_faulthandler_reports.py`, `generate_fault_artifacts.py`, `fault_run_analysis.py`, `configure_faulthandler_runtime.py`, `refresh_mypy_baselines.py` | Consolidates crash triage and baseline refresh tooling; ensure markdown summary highlights repeat offenders and baseline drift. |
| Docs Health | `generate_doc_index.py`, `generate_anchor_inventory.py`, `generate_anchor_health_report.py`, `validate_markdown_anchors.py`, `verify_docs_integrity.py`, `generate_code_doc_churn_report.py`, `generate_undocumented_logic_report.py`, `aggregate_docs_health_signals.py` | Produces documentation governance bundle and human/command_center digests; revisits `summarize_standards.py` only if content overlaps. |
| Standards Integrity | `generate_standards_index.py`, `analyze_standards_index_gaps.py`, `diff_standards_index.py`, `extract_standards_rules.py`, `seed_standards_prompts.py`, `summarize_standards.py` | Keeps standards inventory coherent; orchestrator threads index regeneration, gap analysis, and prompt seeding with a dedicated summary. |
| Dependency & Import Hygiene | `generate_dependency_hygiene_report.py`, `validate_import_boundaries.py`, `scan_code_placeholders.py`, `generate_import_graph_report.py`, `run_batch_cleanup.py` (lint/mypy hooks), `generate_typecheck_report.py` | Centers on dependency risk, layering violations, and static cleanup; utilities applied pre/post runs where helpful. |
| Monkey Patch Oversight | `scan_monkey_patches.py`, `classify_monkey_patches.py`, `monkey_patch_risk.py`, `analyze_monkey_patch_trends.py` | Dedicated pipeline for runtime monkey-patch detection and trend analysis; outputs should integrate with Command Center duplicates tooling. |
| Engineering Complexity Watch (optional expansion) | `generate_lizard_report.py`, `render_inventory_views.py`, `check_inventory_health.py`, `validate_metrics_anchor_stubs.py`, `validate_inventory.py`, `run_standards_index_cli.py`, `run_standards_gap_suite.py` | My suggestion: combine structural complexity and inventory governance to spotlight long-term maintainability metrics; evaluate if this becomes one orchestrator or two smaller follow-ups. |

## 5. Testing Strategy

- **Unit Tests**: For each new orchestrator function (`run()` + CLI shim), craft pytest suites similar
    to the modernized orchestrators. Include path builder mocks, retention behavior, summarizer
    invocation, and error handling (skip/resume logic).
- **Integration Smoke**: Add lightweight tests that run orchestrators against fixture directories
    (reusing existing producers’ fixtures where possible).
- **Topic Summaries**: Introduce snapshot tests for generated Markdown to lock formatting and critical
    sections.
- **Meta-Orchestrator Test**: Validate sequence ordering, failure propagation
    (stop on first failure vs. continue), and aggregated manifest output.
- **Coverage Tracking**: Update coverage ledger to confirm each script is reachable via
    orchestrator tests (use parametrized coverage assertions if needed).

## 6. Shared Helper Opportunities (Command Center Library)

- Extend `command_center.scripts.libraries` with:
  - `build_topic_pipeline(topic_config)` helper to reduce boilerplate for multi-step orchestrators.
  - `summarizer_runner` utility that standardizes summary invocation, bundling, and retention mirroring.
  - `telemetry_emitters` for meta-orchestrator manifest and per-topic status outputs.
  - `catalog_registry` (JSON/YAML) describing script → orchestrator mapping for auditability.
- Ensure helpers follow naming conventions (`verb_noun`) and stay ASCII-only per repo guidance.

## 7. Artifact Management & Pruning

- Standardize retention defaults (likely 5 runs) across new orchestrators; expose CLI overrides.
- Ensure all new bundles write `bundle_summary.json`, Markdown summary, JSON manifest, and pointer
    files (`latest_*`).
- Mirror orchestrator bundles into `.repo_studios/command_center/reports/<topic>_orchestrator/` with
    consistent naming and pruning logic (reuse `copy_latest_artifact` + `prune_run_directories`).

## 8. Documentation & Inventory Updates

- Update `.repo_studios/scripts/script_inventory_architecture.md` with new orchestrators and
    coverage statuses.
- Produce topic-specific automation docs under `.repo_studios/docs/automation/` describing
    CLI usage, inputs, and outputs.
- Refresh `docs/automation/orchestrator_automation_hooks.md` to enumerate new make targets.
- Draft an RFC or README describing the meta-orchestrator flow for internal consumers and agents.
- Capture summarizer schema guarantees in `docs/standards/global/std-global-markdown-authoring.md`
    appendices if needed.

## 9. Execution Phases (Draft Timeline)

1. **Design Finalization**: Confirm topic buckets, orchestrator boundaries, and summarizer
    expectations. Produce RFC draft.
2. **Library Prep**: Implement shared helpers + catalog registry to reduce duplication.
3. **Orchestrator Build-Out**: Iteratively create topic orchestrators, wiring in existing
    producers/consumers/aggregators; add tests.
4. **Summarizer Alignment**: Update existing summarizers (health, standards) and author new
    ones as needed; integrate agent-friendly outputs.
5. **Meta-Orchestrator**: Build the top-level runner, manifest, and make target.
6. **Documentation Pass**: Update automation docs, inventory tables, makefiles, and governance notes.
7. **Validation & Rollout**: Dry runs, CI integration, agent handshake testing, and final sign-off.

## 10. Risks & Open Questions

- Runtime duration: running all topics sequentially may be lengthy; consider parallelization or
    optional flags.
- Data dependencies: ensure orchestrators resolve producer outputs deterministically
    (avoid conflicting timestamps).
- Summarizer scope: decide between topic-level summaries vs. aggregated meta summary only.
- Backward compatibility: maintain existing make targets during transition; include deprecation timeline.
- Agent adoption: define machine-readable schema for orchestrator manifest to support agent diagnostics.

## 11. Next Actions

- Review topic mapping with stakeholders.
- Prototype shared helper (`summarizer_runner`) to validate ergonomics.
- Audit each topic for utility coverage; file backlog issues when a useful utility hook is missing.
- Draft RFC outline referencing this working doc (convert to long-form once consensus emerges).
- Begin designing tests for first topic orchestrator (likely Test Health) to set patterns.
