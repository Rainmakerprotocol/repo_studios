# Phase 6 Prompt Validation Dry-Run Plan (Draft 2025-11-04)

## Scenarios

1. **Duplicate Remediation Kickoff**
   - Prompt key: `session_primer`
   - Inputs: Existing duplicate matrix, guardrail checklist, pending remediation ticket.
   - Expected flow: Agent reviews command center README, confirms run-lock status, plans guardrail evidence collection, and records intended artifacts.
   - Success criteria:
     - Command center guardrail section referenced explicitly.
     - Lock check confirmed with documented command.
     - Planned evidence includes duplicate matrix path, manifest, and metrics summary.

2. **Post-Change Alignment Review**
   - Prompt key: `after_coding_alignment`
   - Inputs: Completed duplicate remediation run, generated manifest and metrics summary.
   - Expected flow: Agent reports validator status, confirms guardrail evidence, cites command center README for follow-up.
   - Success criteria:
     - Manifest and metrics summary linked in the response.
     - Run-lock status revalidated.
     - Decision log update noted with prompt key reference.

3. **Documentation Touch-Up**
   - Prompt key: `update_docs`
   - Inputs: Requirement to add guardrail reference to documentation.
   - Expected flow: Agent reviews documentation section in command center README, drafts minimal doc change, logs decision.
   - Success criteria:
     - Documentation instructions cited before editing.
     - Decision log entry drafted referencing guardrail impact.
     - Change remains under ten lines with cross-link confirmation.

4. **Bundle Review Alignment**
   - Prompt key: `bundle_review`
   - Inputs: Set of changes involving duplicate remediation and automation manifest updates.
   - Expected flow: Agent summarizes changes, attaches guardrail evidence, verifies command center expectations.
   - Success criteria:
     - Duplicate matrix, manifest, metrics summary, and lock check cited.
     - Follow-up actions reference guardrail documentation.

## Execution Steps

1. Set up sandbox transcripts under `phase_6/validation_runs/<date>-scenario.md`.
2. For each scenario, simulate agent usage of the prompt and capture the response.
3. Evaluate response against success criteria; record PASS/FAIL with notes.
4. Aggregate findings in `PROMPT_VALIDATION_RESULTS.md` (to be created post-run).
5. If failures occur, log remediation tasks in `library_integration_checklist.md` and iterate prompts before re-running.
