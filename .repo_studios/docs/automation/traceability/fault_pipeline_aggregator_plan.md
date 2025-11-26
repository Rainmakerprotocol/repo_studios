# Fault Pipeline Aggregator Blueprint

## Status

- **Last Updated:** 2025-11-26
- **Owner:** repo_studios_ai
- **Readiness:** Draft (orchestrator freshly landed; aggregator design pending)

## Purpose

Capture the scope, dependencies, and success criteria for a future faulthandler aggregator that will
blend multiple orchestrator runs into trend summaries.

## Context

- The faulthandler producer (`collect_faulthandler_reports.py`) and consumer (`generate_fault_artifacts.py`)
  now emit structured bundles with retention controls and Command Center mirrors.
- The `run_fault_pipeline.py` orchestrator mirrors summaries to
  `.repo_studios/command_center/reports/fault_pipeline_orchestrator/` and maintains `latest_*` pointers for
  downstream consumption.
- No aggregator currently synthesises these runs into longitudinal metrics.

## Open Questions

1. Which severity metrics (repeat offenders, multi-hit threads, stack volume) should be trended
  week over week?
1. Should the aggregator emit Markdown plus CSV exports to align with existing docs health dashboards?
1. How many historical runs must be analysed to satisfy incident response SLAs?

## Proposed Next Steps

1. Collect two additional orchestrator runs to confirm bundle stability (owner: TBD, due: 2025-12-03).
1. Draft the aggregator schema covering JSON, Markdown, and bundle summary outputs (owner: TBD,
   due: 2025-12-05).
1. Identify downstream consumers (duplicate triage, incident reports) and document ingestion expectations.
1. Add pytest coverage plan to `.repo_studios/tests/tests_aggregators/` once the schema draft is approved.

## Risks

- Aggregator work may overlap with Command Center duplicate scanning; ensure scope alignment before coding.
- Missing historical runs could skew trend analysis; capture retention expectations early.

## Notes

Encourage contributors to update this blueprint before starting aggregator implementation so the command
center inventory stays authoritative.
