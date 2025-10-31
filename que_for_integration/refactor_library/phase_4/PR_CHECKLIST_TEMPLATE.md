# Automation Run Pull Request Checklist

**Status:** Draft (2025-10-31)

Use this template when opening a PR generated from Phase 4 automation runs. Copy the section below into the PR description and update each item before requesting review.

---

## Summary

- [ ] Automation target(s): `scripts-duplicates` / `…`
- [ ] Run date: `YYYY-MM-DD`
- [ ] Operator(s): `@handle`
- [ ] Guardrail configuration version: `docs/automation/guardrails/automation_config.yaml`

## Pre-flight Validation

- [ ] Fresh inventory, analysis, and duplicate scans were generated immediately before the run (attach artifact links).
- [ ] Command center lock check passed via `verify-command-center-locks` workflow.
- [ ] `max_files_per_run` limit respected (list file count vs. configured limit).
- [ ] Manual override applied? ☐ No ☐ Yes (provide approver + rationale).

## Execution Details

- [ ] Dry-run performed first with artifacts attached.
- [ ] Automation executed from clean worktree/worktree slug: `<path>`.
- [ ] Rollback bundle captured under `.repo_studios/command_center/reports/<slug>_automation_run/`.
- [ ] `manifest.json` and `metrics_summary.json` attached to the PR (link or upload).

## Testing

- [ ] `pytest .repo_studios/tests/tests_library_integration` → ✅ / ❌ (attach output)
- [ ] `pytest .repo_studios/tests/tests_producers` → ✅ / ❌ (attach output)
- [ ] Additional suites (list): `…`

## Review Notes

- [ ] Highlights of duplicate groups resolved (reference matrix IDs).
- [ ] Follow-up actions required (docs, manual verification, etc.).
- [ ] Approval sign-off (steward / QA) recorded in guardrail log.

---

## Attachments

- [ ] Dry-run diff (`*.patch`)
- [ ] Automation run logs
- [ ] Metrics summary report
- [ ] Helper adoption report (if generated)
