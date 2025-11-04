# Library Integration Metrics Specification

**Status:** Draft (2025-10-30)

**Purpose:** Define the quantitative signals that demonstrate Phase 3 manual extractions are reducing duplication without destabilising the Repo Studios command-center workflow. These metrics guide prioritisation, surface regressions early, and feed later automation phases.

---

## Metric Catalog

| Metric | Description | Calculation | Data Source | Frequency | Owner |
| --- | --- | --- | --- | --- | --- |
| Duplicate groups resolved | Counts duplicate groups closed since the previous report, segmented by helper/function | `prior_groups - current_groups` using latest duplicate matrix per target | `.repo_studios/command_center/reports/<slug>_duplicate_scan/*matrix*.json` | Weekly (or after each remediation batch) | Genet |
| Helper adoption rate | Percentage of targeted scripts importing the shared helper instead of local copies | `adopted_scripts / total_scripts` for each helper tracked in the Phase 3 snapshot | Producer inventories + scripted grep of `.repo_studios/scripts` | Weekly | Genet |
| Regression incidents | Number of failed regressions (tests or manual verification) attributed to recent extractions | Count entries in run logs flagged as failed/⚠️ plus linked bug tickets | `.repo_studios/command_center/reports/<campaign>/RUNLOG.md` and issue tracker | Continuous; summarise weekly | Genet |
| Orchestrator run cadence | Number of orchestrator runs executed per target to keep artifacts fresh | Count `Run YYYY-MM-DD-HHMM` entries grouped by target | Campaign run logs | Weekly | Genet |
| Test coverage delta | Change in library + producer test coverage for migrated helpers | `current_coverage - baseline` (store baseline in checklist) | `pytest --cov` outputs archived in run folders | Monthly | Genet |
| Mean time to merge | Average elapsed time from first commit referencing a duplicate group to merge/sign-off | `(merge_timestamp - first_commit_timestamp)` aggregated per campaign | Git history + run logs | Monthly | Genet |

---

## Data Collection Process

1. **Refresh artifacts:** After each remediation batch, rerun the command-center pipeline for the affected target so the duplicate matrix reflects the new baseline.
2. **Update run log:** Append a run entry using the template in `.repo_studios/command_center/docs/run_log_template.md`, noting tests executed and any anomalies.
3. **Extract counts:** Use lightweight scripts (planned for Phase 4) or manual spreadsheet tracking to pull helper adoption totals, regression counts, and orchestrator run frequency.
4. **Store snapshots:** Place metric snapshots in the campaign run folder (`reports/<campaign>/metrics-YYYY-MM-DD.json|md`) to enable trend analysis.

---

## Reporting Cadence

- **Weekly briefing:** Summarise duplicate groups resolved, helper adoption rate, and regression incidents. Share alongside updated run logs.
- **Monthly review:** Include orchestrator run cadence, test coverage delta, and mean time to merge to evaluate overall health.
- **Phase transition gates:** Require at least two consecutive weeks with zero regressions and a net duplicate reduction before considering automation pilots.

---

## Actionability Guidelines

- Trigger an immediate review if regression incidents exceed 1 in any week or if helper adoption stalls for two consecutive reports.
- Reprioritise targets if duplicate groups resolved plateaus while orchestrator runs continue to climb (indicates diminishing returns).
- Use mean time to merge to flag process bottlenecks; if MTM > 5 days, schedule a working session to unblock approvals.

---

## Open Questions

- Should helper adoption audits be automated via a dedicated CLI, or is spreadsheet tracking sufficient for Phase 3?

    **Working response (2025-10-31):** Prototype a lightweight CLI in Phase 4; continue spreadsheet tracking through Phase 3 while requirements solidify. Capture CLI requirements in the automation design brief.

- Where should long-term metric storage live once automation starts (dedicated database vs. repo snapshots)?

    **Working response (2025-10-31):** Keep Phase 3 snapshots in-repo, then evaluate pushing summaries to the existing telemetry workspace once automation begins. Action item: add a decision point to the Phase 4 plan comparing Git-based storage vs. central metrics service.

- Do we need per-target severity weighting (e.g., complexity-based scoring) to reflect the impact of each resolved duplicate group?

    **Working response (2025-10-31):** Yes—derive a weighting from the lizard complexity delta and store it alongside duplicate groups. Follow-up: extend the weekly briefing template to include weighted progress once the data pipeline exists.
