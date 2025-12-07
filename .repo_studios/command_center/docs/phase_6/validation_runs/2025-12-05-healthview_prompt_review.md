# Healthview Prompt Review — 2025-12-05

## Scenario

Validate that updated orchestrator prompts and guardrail guidance steer agents toward the
`healthview` viewer and replacement `studio-orchestrate-<topic>` Make targets while flagging legacy
aliases.

## Procedure

1. Reviewed `repo_prompts.md` keys most likely to launch orchestrator automation:
   - `session_primer`
   - `guardrails`
   - `bundle_review`
   - `prioritize_next_steps`
2. Confirmed each prompt references the Command Center guardrail section and avoids legacy
   `studio-run-*` targets.
3. Cross-checked `.repo_studios/docs/automation/orchestrator_automation_hooks.md` to ensure prompts
   point at the same canonical targets described in the automation reference.
4. Verified `docs/automation/orchestrator_migration_announcement.md` is accessible so prompts can
   cite the retirement schedule when summarising next steps.

## Observations

- No prompt text required modification; all keys instruct agents to consult the guardrail section in
  `.repo_studios/command_center/README.md`, which now links to the Healthview onboarding guide.
- Guardrail prompts emphasise capturing viewer slug information, satisfying the Healthview adoption
  requirement.
- No lingering references to `studio-run-pytest-log-capture`, `studio-run-batch-cleanup`, or
  `studio-run-standards-gap-suite` were found.
- Prompt instructions already call for citing automation evidence (manifest, telemetry), aligning
  with Healthview retention expectations.

## Result

- **PASS** — Prompts remain aligned with the topic orchestrator rollout; no edits required.

## Follow-Up

- Re-run this review after deprecation banners ship (target 2025-12-12) to confirm prompts mention
  the warning window where appropriate.
