# Phase 7 Reporting Interface Plan (Draft 2025-11-04)

## Purpose

- Describe how duplicate remediation metrics flow into operator-facing dashboards, weekly briefings, and decision logs.
- Ensure Phase 7 metrics baseline integrates with existing automation artifacts (manifest, metrics summary, weighted briefing template).

## Data Flow Overview

| Source | Transformation | Destination | Consumer |
| --- | --- | --- | --- |
| Automation manifest (`manifest.json`) | Extract guardrail status, run metadata | Weighted progress briefing template | Automation reviewer |
| Metrics summary (`metrics_summary.json`) | Aggregate lines deduplicated, groups resolved | Weighted progress briefing + dashboard CSV export | Stakeholders, leadership |
| Duplicate matrix (before/after) | Compute delta in groups/occurrences | Metric baseline log (`METRIC_BASELINE_LOG.csv`) | Command center operator |
| Pytest reports | Capture pass/fail, duration, coverage | Testing dashboard tab | QA partner |
| Decision log entries | Tag with prompt key and artifact links | Governance timeline | All contributors |

## Interfaces

1. **Weighted Progress Briefing**
   - Populate using data from manifest + metrics summary + baseline log.
   - Sections: Summary, Guardrail Compliance, Duplicate Reduction, Coverage Impact, Open Risks.
   - Delivered weekly (Fridays) and attached to decision log as evidence.
2. **Dashboard CSV Export**
   - Append metrics to `phase_7/baseline_exports/metrics_<YYYY-MM-DD>.csv` for import into reporting tools.
   - Columns: `date`, `lines_dedup`, `groups_resolved`, `guardrail_compliance_pct`, `avg_test_duration`.
3. **Decision Log Enhancements**
   - Ensure each remediation entry lists: prompt key, manifest path, metrics summary path, duplicate delta, testing outcome.
   - Add quick-reference table monthly summarizing key metrics.
4. **CI Status Badges**
   - Publish badges for guardrail compliance and duplicate reduction on README once blocking modes enabled.

## Implementation Steps

1. Extend `weighted_progress_briefing_template.md` with placeholders referencing `METRIC_BASELINE_LOG.csv`.
2. Create helper script under `phase_7/tools/` to merge manifest + metrics summary into CSV export.
3. Update decision log contribution guidelines to require metric snippet per entry.
4. Coordinate with CI team to surface guardrail status badges post-run.

## Success Criteria

- Weekly briefings automatically include latest metric deltas without manual copy/paste.
- Dashboard exports remain under 200 rows (six-month window) with archival plan when exceeded.
- Decision log entries show consistent metric references and guardrail evidence links.

## Next Actions

- Prototype CSV export script once first post-baseline remediation completes.
- Align with stakeholders on dashboard platform (spreadsheet vs BI tool).
- Add reporting checklist section to automation PR template to confirm exports updated.
