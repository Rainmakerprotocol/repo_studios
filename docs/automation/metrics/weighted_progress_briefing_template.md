# Weighted Progress Briefing Template

**Status:** Review requested (2025-11-03)

Use this template when compiling the weekly automation readiness briefing. It blends duplicate resolution totals with lizard complexity scores and helper adoption stats so stakeholders see meaningful progress at a glance.

---

## Summary Snapshot

- Reporting period: `YYYY-MM-DD` – `YYYY-MM-DD`
- Operator(s): `@handle`
- Target scope: `scripts-duplicates` / `…`
- Overall weighted progress: `NN%`
- Metrics source bundle: `reports/<slug>/automation_manifest/metrics_summary-YYYY-MM-DD.json`

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
