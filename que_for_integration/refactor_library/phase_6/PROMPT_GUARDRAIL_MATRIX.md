# Phase 6 Prompt Guardrail Coverage Matrix (2025-11-04)

| Prompt Key | Guardrail Reference | Status | Notes |
| --- | --- | --- | --- |
| `session_primer` | Local-only operations | ✅ | Calls out local-only constraint, validator usage, and minimal diffs. |
|  | Command Center protocol | ⚠️ | No reference to `.repo_studios/command_center/README.md`; relies on legacy runbook reminders. |
|  | Guardrail reporting (`max_files_per_run`, lock checks) | ❌ | Does not mention guardrail artifacts or run locks added in Phases 4–5. |
| `guardrails` | Local-only operations | ✅ | Restates core repo guardrails accurately. |
|  | Command Center protocol | ❌ | No pointer to command center guardrail documentation or orchestrator usage. |
|  | Automation bundles | ❌ | Missing references to automation dry-run bundles or manifest requirements. |
| `update_docs` | Local-only operations | ✅ | Emphasises minimal diffs and doc scope. |
|  | Command Center protocol | ⚠️ | Does not direct doc updates to consult command center README despite cross-links added 2025-11-04. |
|  | Evidence capture / Decision log | ❌ | No reminder to log doc changes or cite guardrail evidence. |
| `after_coding_alignment` | Validator reporting | ✅ | Requires validator status lines. |
|  | Command Center protocol | ❌ | No pointer to duplicate remediation workflow or guardrail checklist. |
|  | Automation readiness | ❌ | Lacks prompt to capture guardrail evidence or manifest outputs. |
| `bundle_review` | Guardrail confirmation | ⚠️ | Mentions guardrails indirectly but does not cite command center README or guardrail artifacts. |
|  | Automation artifacts | ❌ | No call to attach manifest, metrics summary, or duplicate scan outputs. |
| `bundle_post_code_align` | Validator reporting | ✅ | Requires quoting validator lines. |
|  | Command Center protocol | ❌ | No instruction to confirm guardrail compliance or lock status. |
|  | Prompt change log | ❌ | Missing reminder to record prompt usage in decision log. |

## Coverage Summary

- Prompts consistently maintain local-only focus and validator reporting, preserving baseline guardrails.
- None of the audited prompts link to `.repo_studios/command_center/README.md`, automation guardrails, or Make target onboarding guidance added in Phase 5.
- No prompts reference new tooling outputs (automation manifest, metrics summary, weighted progress briefing) or the requirement to log evidence in the decision log.

## Follow-Up Targets

1. Inject command center entry point and guardrail reminders into `session_primer`, `guardrails`, and bundle prompts.
2. Add documentation and evidence logging guidance to `update_docs` and `bundle_review` to align with Phase 4/5 governance.
3. Capture automation bundle expectations (`manifest.json`, `metrics_summary.json`, run lock verification) in prompts that follow refactor or automation flows.
