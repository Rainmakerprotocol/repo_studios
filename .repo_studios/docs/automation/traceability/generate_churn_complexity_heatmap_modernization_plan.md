# Generate Churn × Complexity Heatmap — Modernization Plan (Draft 2025-11-24)

## Objective

Realign `.repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py` with the hardened producer/consumer pipeline by formalizing inputs, provenance, retention, and testing.

## Current State

- **Inputs:** ad-hoc `git log` queries, direct AST walks over the repo tree, and raw `junit_*.xml` files under `.repo_studios/pytest_logs/`.
- **Outputs:** single run directory under `.repo_studios/reports/aggregator_reports/churn_complexity_heatmap/<ts>/` containing `heatmap.json` and `heatmap.md`.
- **Traceability:** no metadata about source commits, pytest bundle provenance, or calculation parameters.
- **Retention:** relies on callers to prune old runs; no CLI controls.
- **Testing:** absent.

## Target Architecture

| Aspect | Current | Target |
| --- | --- | --- |
| Test log data | Direct `junit_*.xml` parsing | Consume `bundle_summary.json` from `generate_test_log_health_report.py` to locate failure metrics and provenance |
| Churn/complexity computation | Coupled inside aggregator | Optionally delegate heavy lifting to a reusable producer helper (`collect_churn_complexity_metrics.py` style) while aggregator focuses on joins and presentation |
| Provenance | Implicit | Record repo SHA, git window, consumer bundle path, log root, and generation timestamp in JSON/Markdown |
| Retention | None | `--artifacts-to-keep` (default 10) with pruning + `latest` pointer |
| CLI surface | `--repo-root`, `--window`, `--output-base`, `--logs-dir` | Add `--test-log-summary`, `--metrics-source`, `--log-level`; expose `run(argv=None)` helper |
| Testing | None | Pytests covering consumer-driven failure counts, optional helper metrics source, fallback to raw JUnit, pruning behavior |

## Implementation Steps

1. **Input Wiring**
   - Add optional `--test-log-summary` (default `.repo_studios/reports/consumer_reports/test_log_health_reports/latest/bundle_summary.json`).
   - Resolve failure counts via consumer summary when present; log a warning and fallback to raw JUnit only when necessary.
   - Capture repo commit SHA (`git rev-parse HEAD`) and store in metadata.

2. **Metrics Extraction**
   - Evaluate splitting churn/complexity calculation into a reusable producer. If deferred, document the decision and retain the in-script logic with improved comments.
   - Ensure ignores/defaults align with repo standards (`.venv/`, `legacy/`, etc.).

3. **Artifact Layout & Metadata**
   - Continue using `aggregator_reports/churn_complexity_heatmap/<ts>/`, but include `bundle_summary.json` describing inputs, parameters, and provenance.
   - Append a "Source References" section to the Markdown summary linking to git window command output, metrics helper (if any), and test log bundle.

4. **Retention Controls**
   - Introduce `--artifacts-to-keep` (default 10) and prune older timestamped runs while retaining the newest.
   - Publish a `latest` hardlink/copy for JSON/Markdown assets.

5. **Logging & Helper**
   - Honor `--log-level` and centralize logging via `logging.getLogger(__name__)`.
   - Expose a `run(argv=None)` function returning paths and pruning results for orchestrators/tests.

6. **Testing**
   - Add `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py` covering:
     - Primary flow using consumer test log summary.
     - Fallback to raw JUnit when summary missing.
     - Retention pruning.
     - Metadata content (SHA, parameters, source references).

7. **Documentation & Governance**
   - Update `.repo_studios/scripts/script_inventory_architecture.md` with new dependencies and CLI switches.
   - Extend the aggregator dependency audit once implementation lands.
   - Log completion in the decision log with reference to the modernization artifacts.

## Implementation Notes (2025-11-24)

- Completed Steps 1, 3–7: the script now accepts `--test-log-summary`, `--metrics-source`, provenance-aware logging controls, emits timestamped bundles with pruning/latest pointers, and ships with pytest coverage covering consumer-first, logs fallback, and retention flows.
- Step 2 evaluation: retained in-script churn/complexity computation while exposing `--metrics-source` for precomputed data; helper extraction remains deferred until additional aggregators justify a shared producer.
- Step 6 delivered `.repo_studios/tests/tests_aggregators/test_generate_churn_complexity_heatmap.py` to validate consumer provenance, fallback mode, and pruning behavior.
- Documentation updates touched `script_inventory_architecture.md`, `aggregator_dependency_audit.md`, and the command-center decision log to capture the modernization outcome and deferred helper decision.

## Risks & Considerations

- **Performance:** Git churn over large windows may remain expensive; consider caching or warning when runtime exceeds threshold.
- **Cross-platform:** Ensure git commands respect Windows environments (no reliance on POSIX-only options).
- **Backwards compatibility:** Provide clear logging when falling back to legacy behavior so operators understand provenance gaps.

## Open Questions

- Should churn/complexity metrics be persisted as their own producer bundle for reuse beyond this aggregator?
- Do we need to expose per-module summary CSVs for dashboard ingestion alongside the JSON/Markdown outputs?
- Are additional filters (e.g., excluding generated files) required before promoting this aggregator to CI gating?
