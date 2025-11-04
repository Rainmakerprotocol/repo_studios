# Phase 7 False-Positive Feedback Loop (Draft 2025-11-04)

## Purpose

- Capture, triage, and resolve duplicate remediation false positives surfaced by scanners, automation manifest checks, or CI guardrails.
- Ensure every false-positive report feeds improvements to detection logic, prompt guidance, or guardrail configuration.

## Workflow Summary

1. **Detection**
   - Source events: duplicate matrix anomalies, automation manifest WARN states, operator feedback during manual runs, CI job WARN/FAIL logs.
   - Required evidence: offending file paths, duplicate group IDs, guardrail outputs, relevant log excerpts.
2. **Triage**
   - Owner reviews submissions within 24 hours.
   - Classify issue type:
     - `scanner_noise`: legitimate unique code flagged as duplicate.
     - `guardrail_noise`: run-size/lock rule misfire.
     - `doc_gap`: prompts or docs led to incorrect guardrail application.
   - Record triage status in `phase_7/FEEDBACK_LOG.md` (to add) with date, owner, evidence links.
3. **Resolution**
   - Determine action: adjust detection thresholds, update allow-lists, revise prompt guidance, or clarify guardrail docs.
   - Implement change via normal change-control (PR + decision log entry).
   - Schedule validation rerun if tooling changed.
4. **Review & Close**
   - Confirm reporter agrees issue is resolved.
   - Archive case in feedback log with outcome (`resolved`, `needs follow-up`, `deferred`).
   - Feed summary into weighted progress briefing under "Guardrail Notes".

## Roles

| Role | Responsibilities |
| --- | --- |
| Feedback Steward (Genet) | Monitor submissions, coordinate triage, ensure log stays current. |
| Tooling Maintainer | Adjust scanner/manifest configs, run regression tests. |
| Documentation Steward | Update prompts/docs when wording drives false positives. |
| QA Partner | Validate fix effectiveness during next remediation dry-run. |

## Intake Channels

- `.repo_studios/command_center/docs/decision_log.md` entries flagged with `false-positive` tag.
- CI job annotations linking to `automation_manifest` bundle.
- Manual run logs stored via `phase_4` run log template with false-positive checkbox.

## Metrics

- Time-to-triage (goal ≤24h).
- Resolution cycle time (goal ≤5 business days).
- Recurrence count by category per quarter.
- % of automation runs affected by false positives (target <5%).

## Next Steps

- Create `phase_7/FEEDBACK_LOG.md` to capture intake → resolution lifecycle.
- Add false-positive tag guidance to prompt library notes and run log template.
- Integrate summary statistics into weighted progress briefing template once log is populated.
