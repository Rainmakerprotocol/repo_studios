# Automation Run Pull Request Checklist

**Status:** Ready (2025-11-03)

**Usage:** Copy the section below into any PR raised from a Phase 4 automation run, replacing the placeholder values before requesting review.

**References:** Guardrails — `docs/automation/guardrails/library_extraction_guardrails.md`; Post-run suites — `phase_4/POST_RUN_TEST_MATRIX.md`; Manifest bundle — `phase_4/AUTOMATION_PLANNING_NOTES.md`.

---

## Summary

- [ ] Automation target(s): `scripts-duplicates` / `…`
- [ ] Run date: `YYYY-MM-DD`
- [ ] Operator(s): `@handle`
- [ ] Guardrail configuration version: `docs/automation/guardrails/automation_config.yaml`
- [ ] Guardrail reference link: `docs/automation/guardrails/library_extraction_guardrails.md`
- [ ] Weighted progress briefing attached? ☐ N/A ☐ Yes (link to `docs/automation/metrics/weighted_progress_briefing_template.md` instance)

## Pre-flight Validation

- [ ] Fresh inventory, analysis, and duplicate scans generated immediately before the run (attach artifact links).
- [ ] Command center lock check passed via `verify-command-center-locks` workflow (link to successful run).
- [ ] `max_files_per_run` limit respected (record file count vs. configured limit from manifest).
- [ ] Manual override applied? ☐ No ☐ Yes (provide approver + rationale).
- [ ] Helper adoption audit executed when applicable (link to latest `helper_adoption.md/json`).

## Execution Details

- [ ] Dry-run performed first with artifacts attached.
- [ ] `run_automation_dry_run.py` invocation recorded (command, timestamp slug, bundle path).
- [ ] Automation executed from clean worktree/worktree slug: `<path>`.
- [ ] Rollback bundle captured under `.repo_studios/command_center/reports/repo-studios__command-center__automation_run/` with README updated.
- [ ] `manifest.json` and `metrics_summary.json` attached to the PR (link or upload).
- [ ] Guardrail configuration snapshot attached (`automation_config.yaml` or excerpt) if changes were made.
- [ ] Inputs bundle (`inputs/`) mirrors dry-run contents and is referenced in the PR.

## Testing

- [ ] `pytest .repo_studios/tests/tests_library_integration` → ✅ / ❌ (attach output)
- [ ] `pytest .repo_studios/tests/tests_producers` → ✅ / ❌ (attach output)
- [ ] Additional suites listed in `phase_4/POST_RUN_TEST_MATRIX.md` executed (record command, status, duration).
- [ ] Orchestrator dry-run regression suite (`pytest .repo_studios/tests/tests_command_center/orchestrators/test_run_automation_dry_run.py`) → ✅ / ❌ (attach output).
- [ ] Any failing suite rerun after fixes with updated evidence linked.

## Review Notes

- [ ] Highlights of duplicate groups resolved (reference matrix IDs and `metrics_summary.json`).
- [ ] Follow-up actions required (docs, manual verification, etc.).
- [ ] Approval sign-off (steward / QA) recorded in guardrail log with date (`docs/automation/guardrails/library_extraction_guardrails.md`).
- [ ] Weighted progress impact summarized (reference latest briefing).

---

## Attachments

- [ ] Dry-run diff (`*.patch`)
- [ ] Automation run logs
- [ ] Metrics summary report
- [ ] Helper adoption report (if generated)
- [ ] Updated weighted progress briefing (if scope warrants)
- [ ] Additional evidence (link): `…`

---

**Current status:** Template is ready for use; automation tooling should surface this link after each dry run so operators can populate it immediately.
