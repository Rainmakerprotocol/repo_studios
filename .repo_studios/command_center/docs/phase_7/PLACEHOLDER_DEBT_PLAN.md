# Placeholder Debt Remediation Plan

**Last updated:** 2025-11-24

<!-- markdownlint-disable MD013 MD029 -->

## Purpose

The `studio-scan-code-placeholders` producer currently reports 1,175 unresolved placeholder markers (0 allowlisted). CI gating remains disabled to avoid noisy build failures. This plan defines the remediation path required to reduce placeholder debt, introduce an allowlist for tolerated instances, and re-evaluate CI enforcement.

## Baseline Snapshot (2025-10-23 scan)

| Metric | Value |
| --- | --- |
| Total matches | 1,175 |
| Allowlist size | 0 |
| Dominant pattern | TODO (657 hits) |
| Dominant extension | .py (1,150 hits) |
| Source report | `.repo_studios/reports/producer_reports/code_placeholder_scans/placeholder_scan-20251023_122859/report.json` |

## Objectives

1. Reduce unallowlisted placeholder count below 150 before enabling gating.
2. Maintain an explicit allowlist of sanctioned placeholders with owners and review dates.
3. Establish weekly monitoring of placeholder trends through automated reports.
4. Reactivate the gating evaluation once Targets 1 and 2 are satisfied.

## Workstreams

### A. Baseline Analysis

- [x] Capture current scan metrics and log gating deferral (2025-11-23).
- [x] Tag top placeholder-heavy repo files for focused remediation (2025-11-23).
- [x] Draft communication to code owners describing required cleanup expectations (2025-11-23).
- [x] Propose exclusion rules to prevent `.venv/` artifacts from inflating future scans (2025-11-23).

### B. Allowlist Creation

- [x] Document interim allowlist guardrails in `docs/automation/scan_code_placeholders.md` (2025-11-23).
- [x] Define allowlist file format updates (2025-11-23) and finalize guardrails.
- [x] Seed initial allowlist scaffold (`.repo_studios/config/placeholder_allowlist.txt`) (currently no active entries) (2025-11-23).
- [x] Establish review cadence (monthly; next review due 2025-12-23) and owner sign-off process (2025-11-23).

### C. Remediation Campaign

- [x] Prioritize TODO/FIXME cleanup across `legacy/` and `src/` packages (2025-11-23 zero-match scan confirmed no outstanding repo-owned placeholders).
- [ ] Track weekly burn-down metrics in `.repo_studios/command_center/docs/phase_7/METRIC_BASELINE_LOG.csv`.
- [ ] Require owners to link PRs that resolve high-volume files in the decision log.

### D. Gating Re-evaluation

- [x] Re-run `make studio-scan-code-placeholders` after remediation to confirm counts (2025-11-23 repo-root scan produced zero matches).
- [x] Update script inventory blueprint with new metrics and allowlist status (2025-11-23).
- [x] Draft CI gating proposal (thresholds, failure policy, alerting) once counts <150 and allowlist established (2025-11-23).

## Milestones

| Milestone | Target Date | Exit Criteria | Owner |
| --- | --- | --- | --- |
| Baseline triage complete | 2025-12-05 | Top 50 files catalogued; outreach draft ready | Standards Guild |
| Allowlist activated | 2026-01-10 | Allowlist file committed with owners + review cadence | Standards Guild |
| Debt burn-down checkpoint | 2026-02-15 | Placeholder count <= 300; trend documented in metrics log | Engineering Leads |
| Gating readiness review | 2026-03-01 | Placeholder count <= 150; allowlist active; CI proposal drafted | Standards Guild + Dev Productivity |

## Baseline File Catalog (2025-10-23 scan)

| Rank | Matches | Path |
| --- | --- | --- |
| 1 | 11 | `.repo_studios/docs/governance/alignment-ledger.md` |
| 2 | 3 | `que_for_integration/refactor_library/phase_3/PHASE_3_MANUAL_EXTRACTION_GUIDE.md` |
| 3 | 2 | `legacy/legacy_makefile_reference.txt` |
| 4 | 2 | `que_for_integration/refactor_library/phase_2/scan_code_duplicates_USAGE.md` |
| 5 | 1 | `.repo_studios/agent_notes/meta/phase1_foundation_review_2025-10-18_0138.md` |
| 6 | 1 | `.repo_studios/docs/templates/agent_note_template.md` |
| 7 | 1 | `.repo_studios/scripts/orchestrators/run_pytest_log_capture.py` |
| 8 | 1 | `.repo_studios/scripts/producers/extract_standards_rules.py` |
| 9 | 1 | `legacy/repo_tests/standards_seed.yaml` |
| 10 | 1 | `que_for_integration/refactor_library/phase_1/library_README.md` |
| 11 | 1 | `que_for_integration/refactor_library/phase_1/setup_library_structure.py` |
| 12 | 1 | `que_for_integration/refactor_library/phase_2/PHASE_2_QUICKSTART.md` |
| 13 | 1 | `que_for_integration/refactor_library/phase_3/PHASE_3_QUICKSTART.md` |
| 14 | 1 | `que_for_integration/test_analyzer_concept/TEST_ANALYZER_GUIDE.md` |

> Note: The remaining 1,161 placeholders originate from the local `.venv/` tree. Future scans must exclude virtual environments so remediation focuses on repository-owned code.

## Owner Outreach Packet

- **Audience:** code owners for files listed in the baseline catalog and future scan deltas.
- **Channel:** Slack/Teams message plus PR checklist reminder.
- **Call to Action:** remove or resolve placeholders, or justify allowlist inclusion with owner + review date.
- **Template:**

  > Subject: Placeholder cleanup needed – `<file>` (TODOS/FIXMES)
  >
  > Hi `<owner>`,
  >
  > `studio-scan-code-placeholders` flagged `<count>` placeholder markers in `<file>`. We’re driving the count below 150 before we enable CI gating. Please either:
  >
  > 1. Replace the placeholder with a real implementation or documented TODO issue, **or**
  > 2. Add the entry to the placeholder allowlist with your name, justification, and review date (≤30 days).
  >
  > See `.repo_studios/command_center/docs/phase_7/PLACEHOLDER_DEBT_PLAN.md` for milestones and allowlist policies. Let us know if you need support unblocking cleanup.

## Allowlist Guidance (Draft)

- New allowlist entries must include `path:line`, owner initials, justification, and review date.
- Default expiration is 30 days; renewals require written justification in the decision log.
- Store the allowlist at `.repo_studios/config/placeholder_allowlist.txt` (tracked in git).
- Update the automation runbook with any schema changes before committing allowlist edits.
- Re-run `make studio-scan-code-placeholders` after allowlist updates to verify counts and history pruning.

## Scanner Exclusions Rollout (2025-11-23)

- Shipped default exclusions on 2025-11-23: the producer now omits `.venv/`, `node_modules/`, and intermediate `site-packages/` directories when scanning the repo root, while exposing `--exclude-prefix` for overrides.
- The JSON payload advertises `exclude_prefixes`, `exclude_segments`, and whether defaults were applied so downstream tooling can confirm coverage.
- Operators can disable defaults with `--exclude-prefix` (no values) or supply explicit prefixes, keeping ad-hoc scans flexible.
- Work items closed:
  - [x] Implement CLI support + default exclusions in `scan_code_placeholders.py` (2025-11-23).
  - [x] Add pytest coverage proving excluded directories are ignored (2025-11-23).
  - [x] Update runbook and plan with the finalized behavior (2025-11-23).

## Placeholder Detection Hardening (2025-11-23)

- Updated the producer to only record matches when the placeholder token appears in uppercase (e.g., `TODO`, `FIXME`, `NOTE`), eliminating noise from documentation headings and prose.
- Added regression coverage for the uppercase heuristic and refreshed the automation runbook so downstream operators understand the behavior.
- Latest scan (placeholder_scan-20251123_203707) reported zero matches with defaults applied; metrics ledger updated accordingly.
- Observation cadence kickoff (placeholder_scan-20251123_211100) confirmed the weekly schedule; details logged in metrics and CI rollout records.
- Observation week 2 (placeholder_scan-20251124_235519) sustained zero delta; metrics ledger and CI rollout log both updated, and a blocking-mode transition brief now outlines readiness checkpoints.

## CI Gating Proposal Draft (2025-11-23)

- **Rollout Path:**
  - Weeks 1–2 (observation): Run `make studio-scan-code-placeholders` within a new `placeholder-scan` GitHub Actions job in warning mode, publish artifacts, and log outcomes in `phase_7/CI_ROLLOUT_LOG.md`.
  - Weeks 3–4 (stabilization): Require successful runs for automation-authored PRs; failures create WARN status checks with links to remediation guidance.
  - Week 5+ (enforcement): Promote the job to blocking once two consecutive weekly scans report ≤ allowlist matches and zero untriaged WARN events.
- **Thresholds:**
  - `total_matches - allowlist_size` must equal 0.
  - `allowlist_size` must remain ≤ 20 entries, each with <30 day review date.
  - Any new placeholder outside the allowlist triggers failure with path/line surfaced from `matches.json`.
- **Failure Policy:**
  - CI posts a comment guiding owners to remediate or expand the allowlist with decision-log approval.
  - Overrides require a temporary decision log entry plus follow-up scan confirming return to baseline.
- **Alerting & Reporting:**
  - Upload `report.json`, `matches.json`, and `report.md` as job artifacts for review.
  - Add a slack/Teams webhook card summarizing totals and pointing to the metrics ledger when WARN/FAIL occurs.
- **Next Integration Steps:**
  - Draft `placeholder-scan.yml` workflow stub that mirrors Command Center make invocation.
  - Update `CI_INTEGRATION_STRATEGY.md` pipeline table with the new stage before flipping to blocking.
  - Socialize thresholds with Dev Productivity and Standards Guild sign-off.
  - Maintain `CI_ROLLOUT_LOG.md` entries each week to document warning → blocking readiness.

## Reporting & Governance

- Update `.repo_studios/command_center/docs/phase_7/METRIC_BASELINE_LOG.csv` after each scan.
- Track phased enforcement outcomes in `.repo_studios/command_center/docs/phase_7/CI_ROLLOUT_LOG.md`.
- Record major remediations and gating decisions in `.repo_studios/command_center/docs/decision_log.md`.
- Reference this plan from `script_inventory_architecture.md` and the automation doc for `scan_code_placeholders`.

## Next Actions

- [ ] Maintain the placeholder allowlist via monthly reviews (next check 2025-12-23) and capture any new sanctioned entries in the decision log.
- [x] Start the weekly scan cadence and log outcomes in the metrics ledger + CI rollout log beginning week of 2025-11-24.
- [ ] Monitor the `placeholder-scan` workflow (warning mode), circulate weekly run summaries, and prepare sign-off for the transition to blocking enforcement. *(Week 2 summary logged 2025-11-24; next action: collect two additional clean observation runs before requesting blocking review.)*

<!-- markdownlint-enable MD013 MD029 -->
