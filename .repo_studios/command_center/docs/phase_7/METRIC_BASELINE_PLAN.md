# Phase 7 Metric Baseline Plan (Draft 2025-11-04)

## Objectives

- Establish initial measurements for duplicate remediation aligned with the 360-occurrence baseline captured on 2025-10-24.
- Define how lines deduplicated, duplicate groups resolved, and test coverage delta will be tracked across manual and automated runs.
- Provide collection cadence, source artifacts, and owners before Phase 7 hardening work begins.

## Baseline Sources

| Metric | Baseline Artifact | Snapshot Date | Value | Notes |
| --- | --- | --- | --- | --- |
| Duplicate occurrences | `reports/duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/scripts_duplicate_matrix-2025-10-24.json` | 2025-10-24 | 360 occurrences across 22 producer scripts | Producer analysis baseline prior to Phase 3 extractions. |
| Duplicate groups | `reports/duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/scripts_duplicate_matrix-2025-10-27.json` | 2025-10-27 | 3 groups (command center root scan) | Mirrors orchestrator pipeline coverage. |
| Summarizer scan groups | `reports/duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/summarizers_duplicate_matrix-2025-10-28-1340.json` | 2025-10-28 | 1 scanner-only group (2 files) | Validates slug retention for summarizers target. |
| Utilities scan groups | `reports/duplicates_scan/repo-studios__command-center__scripts_duplicate_scan/utilities_duplicate_matrix-2025-10-28-1344.json` | 2025-10-28 | 0 groups | Confirms clean state for utilities target. |
| Automation manifest sample | `.repo_studios/command_center/reports/repo-studios__command-center__automation_run/automation_manifest-20251103_170000/metrics_summary.json` | 2025-11-03 | `lines_touched`: 0 (dry-run), `groups_resolved`: 0 | Establishes schema for future change tracking. |
| Test coverage reference | `.repo_studios/tests/` pytest suites (phase 4 matrix) | 2025-11-03 | Library + producer suites passing | Baseline for future coverage deltas. |

## Metric Definitions

| Metric | Description | Collection Method | Owner | Cadence |
| --- | --- | --- | --- | --- |
| Lines Deduplicated | Net lines removed or refactored when duplicates are extracted | Compare `git diff --stat` for remediation commits and capture `lines_removed` versus `lines_added`; supplement with automation manifest `lines_touched` field | Genet | Per remediation run, aggregated weekly |
| Duplicate Groups Resolved | Count of duplicate groups where consolidated helper replaces redundant code | Diff duplicate matrix before/after run; automation manifest `groups_resolved` acts as authoritative record | Genet | Per remediation run, aggregated weekly |
| Test Coverage Change | Δ in relevant pytest suite results (pass count, duration, coverage %) after remediation | Record pytest run summary (`--maxfail=1 --durations=10`) and coverage report snapshots when available | Genet + assigned QA partner | Per remediation run, aggregated monthly |
| Guardrail Compliance Rate | Percentage of remediation runs completing guardrail checklist without deviations | Leverage automation manifest status + guardrail prompts captured in run log template | Command Center operator on duty | Weekly |
| Documentation Drift | Count of doc updates linked to remediation versus outstanding TODOs | Track `memory-bank/decisionLog.md` entries tagged with prompt keys and compare to scheduled doc updates | Documentation steward | Monthly |

## Collection Workflow

1. **Pre-run snapshot**: Export duplicate matrix and metrics summary pointers before starting remediation.
2. **Remediation run**: Execute manual or automated extraction while capturing manifest and metrics summary artifacts.
3. **Post-run reconciliation**: Update weighted progress briefing template with new metrics; log decision entries citing artifacts.
4. **Baseline ledger**: Append new measurements to `phase_7/METRIC_BASELINE_LOG.csv` (to be created once data collection begins).

## Validation Cadence & Responsibilities

- **Weekly metric review (Tuesdays by 18:00 UTC)**
  - *Owner:* Genet (Command Center steward).
  - *Inputs:* Fresh duplicate scan (or automation dry run), updated automation manifest bundle, appended entries in `phase_7/METRIC_BASELINE_LOG.csv`.
  - *Outputs:* Updated weighted progress briefing draft, decision log note if thresholds breached, confirmation that guardrail checklist remained green.
  - *Checks:* Ensure duplicate groups resolved metric moves in the expected direction; flag any guardrail exceptions for same-week remediation.
- **Monthly deep-dive (first Thursday)**
  - *Owners:* Genet + rotating QA partner.
  - *Inputs:* Aggregated weekly ledger entries, latest lizard complexity report, helper adoption snapshot.
  - *Outputs:* Monthly synopsis stored with the weighted briefing archive, backlog adjustments, refreshed risk register items (if needed).
  - *Checks:* Validate that coverage deltas remain within ±1% of baseline; trigger follow-up tickets if helper adoption stalls for two consecutive months.
- **Prompt drift audit (quarterly)**
  - *Owner:* Prompt steward (per `repo_prompts.md`).
  - *Inputs:* Ledger totals, prompt validation transcripts, guardrail feedback log.
  - *Outputs:* Quarterly note in `memory-bank/decisionLog.md` summarizing prompt efficacy vs. metrics movement.
- **Cadence tooling**
  - Capture cadence results in the ledger (new rows tagged with `cadence_review`), and cite review timestamps in the weighted briefing template for traceability.
  - Maintain a rolling four-week retention of briefing drafts; archive monthly deep-dive decks alongside automation run bundles.

## Acceptance Criteria

- Initial metric values captured for duplicate occurrences, groups, and test coverage before Phase 7 hardening tasks commence.
- Owners acknowledge cadence expectations and storage locations.
- Checklist references updated to point at this plan and upcoming log file.
- Weekly, monthly, and quarterly review schedule documented with named owners and required artifacts.

## Next Steps

1. **Completed 2025-11-04:** Created `METRIC_BASELINE_LOG.csv` capturing duplicate matrix totals and the 2025-11-03 automation metrics summary snapshot.
2. **Completed 2025-11-04:** Documented validation cadence (weekly, monthly, quarterly) with owners and artifact expectations.
3. Align CI integration plan with metrics to ensure pass/fail thresholds use the same data sources.
