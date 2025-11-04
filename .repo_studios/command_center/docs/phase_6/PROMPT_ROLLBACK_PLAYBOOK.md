# Phase 6 Prompt Rollback & Versioning Playbook (Draft 2025-11-04)

## Versioning

- Maintain semantic versioning for `repo_prompts.md` (major.minor.patch) with metadata updated at the top of the file.
- Record every published version in `library_integration_checklist.md` and `.repo_studios/command_center/docs/decision_log.md` with date, scope, and evidence links.

## Change Tracking

- Store draft deltas in `PROMPT_DELTA_DRAFTS.md` and keep prior versions for comparison until publication.
- After publishing a new version, archive previous drafts under `phase_6/archive/<version>/` for reference.

## Rollback Procedure

1. Identify the last known good version (e.g., v1.2.0) via Git history and documented metadata.
2. Revert `repo_prompts.md` to the prior version using Git (`git checkout <commit> -- repo_prompts.md`) and increment version metadata with a rollback suffix (e.g., `1.3.0-rollback` if needed).
3. Update `library_integration_checklist.md` and `.repo_studios/command_center/docs/decision_log.md` documenting the rollback, rationale, and affected prompts.
4. Remove or revise any supporting artifacts (validation results, change control notes) that are no longer accurate; archive the reverted version’s validation runs under `phase_6/archive/<version>-rollback/`.
5. Notify stakeholders (developer reviewer) and schedule a re-validation run before reapplying prompt updates.

## Safeguards

- No direct edits to `repo_prompts.md` outside approved change-control workflow.
- Validation dry-runs must pass before tag/branch merges releasing new prompt versions.
- Maintain transcripts for the latest successful validation runs to expedite regression checks.
