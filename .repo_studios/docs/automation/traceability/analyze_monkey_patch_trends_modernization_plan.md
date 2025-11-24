# Analyze Monkey Patch Trends — Modernization Plan (Draft 2025-11-24)

> Status: Completed 2025-11-24 — Aggregator refactor landed with inventory and governance updates captured.

## Objective

Retool `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py` so it ingests the hardened consumer risk summaries, retains provenance, and publishes history-managed artifacts under the aggregator reports hierarchy.

## Current State

- Input: raw producer `report.json` payloads in `.repo_studios/reports/producer_reports/monkey_patch_scans/<run>/`.
- Output: `trend_latest.md` and `trend_latest.json` written back into the producer directory plus a `trend.md` in the latest scan folder.
- Traceability: no linkage to consumer summaries or source metadata; relies on producer retention alone.
- Test coverage: none.

## Target Architecture

| Aspect | Current | Target |
| --- | --- | --- |
| Primary input | Producer `report.json` | Consumer `summary.json` + `bundle_summary.json` provenance (fallback to producer data when missing) |
| Output location | Producer scan directory | `.repo_studios/reports/aggregator_reports/monkey_patch_trends/<ts>/` + `latest` pointer |
| Provenance | Implicit (scan folder name) | Embed consumer bundle path, generated timestamp, and fallback reason in JSON & Markdown |
| Retention | Producer pruning only | Aggregator-level `--artifacts-to-keep` (default 10) |
| Invocation | CLI only | CLI + helper `run(argv=None)` with structured return (mirroring consumers) |
| Tests | None | Pytest covering consumer-first and fallback modes, retention pruning |

## Implementation Steps

1. **Input Discovery**
   - Accept `--consumer-base` (default `.repo_studios/reports/consumer_reports/monkey_patch_risk/`) and locate the latest timestamped bundle (`summary.json`, `bundle_summary.json`).
   - Extract metadata from the consumer summary (`run_metadata`, `scan_dir` from bundle metadata) to reuse file/category counts.
   - Preserve fallback path: if no consumer bundle exists, revert to producer `report.json`.

2. **Aggregation Logic**
   - Rebuild trend comparisons using consumer-provided totals/classifications (HIGH/MODERATE/SAFE) rather than recomputing from raw findings.
   - When falling back, rehydrate the legacy calculations for compatibility.

3. **Artifact Layout**
   - Introduce `--output-base` (default `.repo_studios/reports/aggregator_reports/monkey_patch_trends`).
   - Write timestamped run directory containing `trend.json`, `trend.md`, and metadata stub (`bundle_summary.json`).
   - Maintain optional copy of the Markdown summary alongside the latest consumer bundle for operator convenience.

4. **Retention & Latest Pointer**
   - Implement pruning (`--artifacts-to-keep`, default 10) mirroring consumer behavior.
   - Update or create `latest_report.json` / `latest.md` pointers within the aggregator directory (no symlinks on Windows).

5. **Logging & CLI Surface**
   - Add `--log-level`, `--consumer-summary`, and `--producer-base` overrides.
   - Provide `run(argv=None)` wrapper for orchestrator integration.

6. **Testing**
   - Add pytest module under `.repo_studios/tests/tests_aggregators/` covering:
     - Consumer-first ingestion.
     - Producer fallback.
     - Retention pruning.
     - Metadata integrity (source paths, timestamps).

7. **Documentation & Inventory Updates**
   - Update `.repo_studios/scripts/script_inventory_architecture.md` entry with new dependencies and notes.
   - Extend the traceability audit with aggregator summary ingestion details post-implementation.

## Dependencies & Coordination

- Requires consumer outputs from `classify_monkey_patches.py` to land in `.repo_studios/reports/consumer_reports/monkey_patch_risk/monkey_patch_risk-<ts>/` with retention (handled during consumer hardening).
- Ensure orchestrator or Make target updates align with new CLI options.
- Coordinate with duplicate remediation workflows if additional outputs (CSV, dashboards) are expected.

## Acceptance Criteria

- Aggregator defaults to consumer summaries and records provenance in every artifact.
- Trend outputs reside under `aggregator_reports/monkey_patch_trends/` with pruning + latest pointer.
- Producer fallback retains current behavior with explicit log warning.
- New pytest suite passes and integrates with existing CI pattern.
- Documentation and inventory blueprint reflect the new data flow.

## Open Questions

- Resolved 2025-11-24: Mirror the Markdown summary into the consumer bundle (`TREND_SNAPSHOT.md`) while keeping aggregator outputs canonical under `aggregator_reports/monkey_patch_trends/`.
- Should we emit a condensed CSV for dashboard ingestion alongside JSON/Markdown?
- Do aggregators need to surface diff metadata (e.g., new vs resolved HIGH risk entries) beyond aggregate counts?
