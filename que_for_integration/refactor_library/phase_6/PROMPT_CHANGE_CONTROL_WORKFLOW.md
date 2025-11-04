# Phase 6 Prompt Change-Control Workflow (Draft 2025-11-04)

## Roles

- **Author (Agent):** Drafts prompt deltas, guardrail matrix updates, and validation plans.
- **Reviewer (Developer):** Confirms guardrail coverage, validates wording, and approves rollout.
- **Recorder:** Updates `memory-bank/decisionLog.md` and `repo_prompts.md` change log after approval (can be author or reviewer).

## Change Sequence

1. **Draft Preparation**
   - Create/update supporting artifacts (`PROMPT_GUARDRAIL_MATRIX.md`, `PROMPT_DELTA_DRAFTS.md`).
   - Capture summary of changes and evidence paths in `library_integration_checklist.md`.
2. **Peer Review**
   - Reviewer validates guardrail coverage, command center linkage, and doc standards.
   - Feedback captured directly in the draft files or via tracked comments.
3. **Approval & Logging**
   - Reviewer records approval in `memory-bank/decisionLog.md` with date, prompts touched, and artifacts cited.
   - Update `repo_prompts.md` version metadata and add entry to prompt library change log section (new subsection to be added during rollout).
4. **Publication**
   - Apply approved deltas to `repo_prompts.md` (single commit with referenced artifacts).
   - Run prompt validation dry-runs per Phase 6 plan; store transcripts in `phase_6/validation_runs/`.
5. **Rollback Plan**
   - If issues arise, revert prompt changes using Git history; record reversal in decision log and restore prior version metadata.

## Governance Hooks

- Every prompt update must reference command center guardrail documentation and any new automation artifacts introduced since Phase 5.
- Validation dry-runs required for prompts influencing remediation or automation workflows prior to publication.
- No direct edits to `repo_prompts.md` without corresponding updates to Phase 6 artifacts and decision log.
