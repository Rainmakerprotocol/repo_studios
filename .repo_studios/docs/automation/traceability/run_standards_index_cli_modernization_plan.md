# Run Standards Index CLI — Modernization Plan (Draft 2025-11-27)

## Status

- 2025-11-27: Plan drafted; implementation not yet started.
- 2025-12-02: Modernization delivered; adoption follow-up pending.

## Objective

Modernize `.repo_studios/scripts/orchestrators/run_standards_index_cli.py` so standards analysts
and tooling receive structured, retainable outputs while preserving its lightweight CLI ergonomics.
The refactor will introduce an import-safe `run(argv=None)` helper, bundle-based artifacts,
configurable retention, and documentation/tests that mirror the Command Center orchestrator playbook.

## Current State

| Aspect | Current Behaviour |
| --- | --- |
| Inputs | CLI-only execution; global `argparse` parser invoked in `main()` with stdout writes and immediate `sys.exit`. |
| Outputs | Plain stdout lines (list/search/stats) with no JSON/Markdown bundle, log retention, or provenance metadata. |
| Logging | Global `logging.basicConfig` at import time with `INFO` default; no CLI flag to adjust verbosity. |
| Retention | No structured artifacts; interactive runs leave no historical record. |
| Entry Point | No reusable `run()` helper; helper functions return exit codes but not structured payloads. |
| Testing | Lacks pytest coverage; behaviour validated manually. |
| Documentation | No automation doc describing commands, filters, or expected outputs. |
| Command Center Integration | Does not leverage `build_standard_paths`/`write_report_artifacts`; orchestrators cannot reuse results programmatically. |

## Target Architecture

| Aspect | Target Behaviour |
| --- | --- |
| Inputs | `run(argv=None)` helper returning structured results, backed by `build_standard_options` for log level and retention controls. |
| Outputs | Timestamped bundle under `.repo_studios/reports/orchestrator_runs/standards_index_cli/` with `report.json`, optional `report.md`, filtered results payload, and `bundle_summary.json`, plus refreshed `latest_*` pointers. |
| Logging | CLI exposes `--log-level` to align with orchestrator norms; logging configured inside `run()`. |
| Retention | `--artifacts-to-keep` (default 5) prunes historical bundles via `write_report_artifacts`. |
| Entry Point | `run()` performs all work; `main()` thin shim returning exit code. |
| Testing | New pytest module covering list/search/show/stats flows, artifact emission, and retention pruning. |
| Documentation | Dedicated automation guide (`docs/automation/run_standards_index_cli.md`) describing commands, filters, outputs, and examples. |
| Command Center Integration | Uses shared CLI/path helpers so future orchestrators can import and reuse the command programmatically. |

## Implementation Steps

1. **Design & Helper Wiring** — Capture desired CLI flags (`--output-dir`, `--artifacts-to-keep`,
    `--log-level`) and adopt Command Center path/option builders. *(Completed 2025-12-02)*
2. **Structured Output & Retention** — Implement `run()` returning payload, invoke
    `write_report_artifacts`, and maintain `latest_*` pointers. *(Completed 2025-12-02)*
3. **Testing & Validation** — Add
    `.repo_studios/tests/tests_orchestrators/test_run_standards_index_cli.py`
    covering primary commands, stderr/exit scenarios, and retention trimming. *(Completed 2025-12-02)*
4. **Documentation & Inventory Updates** — Publish automation doc, refresh
    `script_inventory_architecture.md`, and log decision in
    `.repo_studios/command_center/docs/decision_log.md`. *(Completed 2025-12-02)*
5. **Adoption Follow-Up** — Coordinate with standards pipeline owners to replace any legacy
    references with new bundle locations and ensure downstream tooling consumes structured outputs. *(In progress)*

## Dependencies & Coordination

- Requires `PyYAML` (already vendored) and Command Center libraries (`cli`, `artifacts`).
- Coordinate with standards maintainers to confirm default retention and output expectations.
- Validate that generated bundles integrate cleanly with existing standards workflows before
    deprecating stdout-only usage.

## Acceptance Criteria

- CLI remains backward compatible for interactive use (stdout mirrors prior behaviour) while
    emitting structured bundles by default.
- `run()` helper is import-safe and returns a dict summarizing command, filters, and results.
- Retention keeps the most recent N runs (default 5) with refreshed `latest_*` pointers.
- Pytest coverage verifies list/search/show/stats commands, artifact content, and error exits.
- Documentation and inventory notes describe the modernized workflow and output schema.

## Open Questions

- Should the CLI expose a `--format` flag to let users opt into Markdown-only or JSON-only outputs
    per run?
- Do we need to support piping input (e.g., reading ids from stdin) or is file-based filtering
    sufficient for downstream tooling?
- Should stats include additional integrity metadata (e.g., category counts) in the structured
    summary by default?
