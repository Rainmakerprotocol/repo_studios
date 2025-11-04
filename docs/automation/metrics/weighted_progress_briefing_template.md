# Weighted Progress Briefing Template

**Status:** Ready (2025-11-03)

Use this template when compiling the weekly automation readiness briefing. It blends duplicate resolution totals with lizard complexity scores and helper adoption stats so stakeholders see meaningful progress at a glance.

---

## Summary Snapshot

- Reporting period: `YYYY-MM-DD` – `YYYY-MM-DD`
- Operator(s): `@handle`
- Target scope: `scripts-duplicates` / `…`
- Overall weighted progress: `NN%`
- Metrics source bundle: `reports/<slug>/automation_manifest/metrics_summary-YYYY-MM-DD.json`
- Helper adoption snapshot: `reports/<slug>/helper_adoption/helper_adoption-YYYY-MM-DD.json`

## Weighting Formula

```text
weighted_progress = (
  (duplicate_groups_resolved * duplicate_weight)
  + (high_complexity_functions_remediated * complexity_weight)
  + (helpers_adopted * helper_weight)
) / total_possible_weight
```

- Default weights: `duplicate_weight = 0.5`, `complexity_weight = 0.3`, `helper_weight = 0.2`.
- When metrics summary includes additional keys, extend the formula and capture the rationale below the defaults.
- Adjust weights only with steward approval; record the approval date, approver, and linked decision log entry here.

## Key Metrics

| Metric | Current | Delta vs prior week | Notes |
| --- | --- | --- | --- |
| Duplicate groups resolved | `12` | `+3` | `slugify_relative` sweep completed |
| High complexity functions remediated | `5` | `+2` | Based on lizard top offenders |
| Helpers adopted | `8` | `+4` | CLI helpers rolled out to import validators |
| Average complexity score | `14.2` | `-1.8` | Computed from latest lizard report |

> Tip: Pull `Current` and `Delta` values from the latest metrics summary export to avoid manual transcription errors.

## Artifact Links

- Duplicate matrix: `[link]`
- Lizard report: `[link]`
- Helper adoption report: `[link]`
- Automation manifest + metrics summary: `[link]`
- Decision log entry confirming weight changes (if applicable): `[link]`

## Narrative Highlights

- **Wins:**
  - `…`
- **Risks or blockers:**
  - `…`
- **Upcoming focus:**
  - `…`

## Follow-up Actions

- [ ] Update guardrail checklist with any overrides approved this week.
- [ ] Schedule dry-run rehearsal if duplicate backlog falls below threshold.
- [ ] Refresh helper adoption CLI inputs before next briefing.
- [ ] Log deviations or weight adjustments in `memory-bank/decisionLog.md`.

---

## How to Use This Template

1. Retrieve the latest automation dry-run bundle under `reports/<slug>/automation_manifest/automation_manifest-<timestamp>/`.
2. Copy `metrics_summary.json` into your working folder and extract duplicate, helper, and runtime metrics for the Summary Snapshot and Key Metrics table.
3. Run the helper adoption audit CLI if no snapshot exists for the current week, then attach both JSON and Markdown outputs in the Artifact Links section.
4. Pull the top offenders table from the most recent lizard report to inform Narrative Highlights and adjustments to the weighting conversation.
5. Capture any weighting changes, overrides, or exceptions in the Decision Log and reference them near the weighting formula.
6. Review the `post_run_tests` node in `manifest.json` to note any required retries in Follow-up Actions.

## Data Sources

| Artifact | Location | Purpose |
| --- | --- | --- |
| Metrics summary | `reports/<slug>/automation_manifest/metrics_summary-YYYY-MM-DD.json` | Supplies duplicate counts, helper adoption totals, durations, and executed test suites. |
| Automation manifest | `reports/<slug>/automation_manifest/manifest.json` | Provides guardrail metadata, targets touched, and links to post-run test commands. |
| Helper adoption report | `reports/<slug>/helper_adoption/helper_adoption-YYYY-MM-DD.json` | Tracks helper uptake by target and supports the helper weighting component. |
| Lizard complexity briefing | `.repo_studios/reports/producer_reports/lizard_reports/<timestamp>/summary.md` | Lists high-complexity functions and changes used in the complexity weighting. |
| Decision log | `memory-bank/decisionLog.md` | Records approvals, weight adjustments, and rationale for auditability. |
