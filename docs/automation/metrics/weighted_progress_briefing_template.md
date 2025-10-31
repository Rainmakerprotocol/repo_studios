# Weighted Progress Briefing Template

**Status:** Draft (2025-10-31)

Use this template when compiling the weekly automation readiness briefing. It blends raw duplicate counts with lizard complexity scores to spotlight high-impact progress.

---

## Summary Snapshot

- Reporting period: `YYYY-MM-DD` – `YYYY-MM-DD`
- Operator(s): `@handle`
- Target scope: `scripts-duplicates` / `…`
- Overall weighted progress: `NN%`

## Weighting Formula

```text
weighted_progress = (
    (duplicate_groups_resolved * duplicate_weight)
    + (high_complexity_functions_remediated * complexity_weight)
    + (helpers_adopted * helper_weight)
) / total_possible_weight
```

- Default weights: `duplicate_weight = 0.5`, `complexity_weight = 0.3`, `helper_weight = 0.2`.
- Adjust weights only with steward approval; document changes in this section when they occur.

## Key Metrics

| Metric | Current | Delta vs prior week | Notes |
| --- | --- | --- | --- |
| Duplicate groups resolved | `12` | `+3` | `slugify_relative` sweep completed |
| High complexity functions remediated | `5` | `+2` | Based on lizard top offenders |
| Helpers adopted | `8` | `+4` | CLI helpers rolled out to import validators |
| Average complexity score | `14.2` | `-1.8` | Computed from latest lizard report |

## Artifact Links

- Duplicate matrix: `[link]`
- Lizard report: `[link]`
- Helper adoption report: `[link]`
- Automation manifest + metrics summary (if available): `[link]`

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
