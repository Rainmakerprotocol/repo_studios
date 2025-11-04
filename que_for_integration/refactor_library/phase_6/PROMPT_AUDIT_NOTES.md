# Phase 6 Prompt Audit Notes (2025-11-04)

## Scope

- Reviewed `repo_prompts.md` to identify instructions that impact library integration, duplicate remediation, or command center operations.
- Evaluated prompt coverage for guardrail alignment, command center discoverability, and automation readiness messaging.

## Observations

1. **Guardrail alignment:** Existing prompts reference local-only execution, minimal diffs, and validator reporting; they do not mention command center guardrails (duplicate retention, lock checks, `max_files_per_run`).
2. **Command center visibility:** No prompts direct operators or agents to `.repo_studios/command_center/README.md` before taking remediation actions.
3. **Automation hooks:** Prompts lack guidance on Make targets, helper adoption audits, or automation dry-run bundles introduced in Phases 4–5.
4. **Documentation reminders:** `update_docs` prompt focuses on small edits but does not require referencing the weighted progress briefing or updated checklist artifacts.

## Risks

- Agents may miss mandatory command center guardrails when executing remediation tasks driven by prompts.
- Prompt-driven workflows might continue to use legacy instructions, delaying adoption of automation bundles and guardrail reporting.

## Recommended Follow-Ups

- Draft instruction deltas that add command center entry points, guardrail references, and automation bundle expectations to relevant prompts (`session_primer`, `guardrails`, `update_docs`, and bundle prompts).
- Introduce prompt change-control workflow documenting reviewers, decision logging, and rollback strategy (Phase 6 subsequent tasks).
- Plan validation dry-runs using updated prompts to confirm agents navigate to the command center protocol and capture required evidence artifacts.

## Next Actions

- Develop draft prompt updates (Phase 6 task `Draft candidate instruction deltas`).
- Define change-control workflow and rollback mechanisms before publishing new prompt revisions.
- Schedule validation scenarios once deltas are ready to ensure prompts route operators through command center guardrails.
