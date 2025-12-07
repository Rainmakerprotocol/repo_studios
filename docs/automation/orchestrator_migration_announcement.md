# Orchestrator Migration Announcement

**Published:** 2025-12-05

## Overview

- Communicates the cutover schedule for topic orchestrators and the retirement path for legacy
  health-suite entry points.
- Clarifies which Make targets now act as shims, when warnings begin, and when removals are
  scheduled.
- Records the latest agent-integration review so operators know prompts and automation workflows
  already understand the Healthview viewer and topic-specific runners.

## Timeline

| Date | Milestone | Notes |
| --- | --- | --- |
| 2025-12-05 | Announcement posted | Timeline distributed to Command Center maintainers, docs owners, and agent teams. |
| 2025-12-08 | Default to topic orchestrators | Daily operations and runbooks switch to `studio-orchestrate-<topic>` and `studio-orchestrate-full-diagnostic`; legacy shims remain callable. |
| 2025-12-12 | Begin deprecation warnings | Legacy Make aliases emit a warning banner directing operators to the replacement targets; agent prompts call the new commands. |
| 2026-01-16 | Remove legacy orchestration entry points | Delete deprecated Make aliases, retire `orchestrate_health_suite.py` and remaining `run_*` shims, and update CI/automation references. |

## Deprecated Targets

| Legacy Entry Point | Replacement | Current Status | Retirement Plan |
| --- | --- | --- | --- |
| `make studio-run-fault-pipeline` | `make -C .repo_studios studio-orchestrate-fault-diagnostics` | Alias remains but emits a warning from 2025-12-12 onward. | Remove alias and delete `run_fault_pipeline.py` on or after 2026-01-16 once telemetry shows zero legacy usage for two consecutive weeks. |
| `python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py` | `python .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py` or `make -C .repo_studios studio-orchestrate-test-execution-telemetry` | Shim delegates to the topic orchestrator today. | Keep shim until 2026-01-16 to support scripted fallbacks; removal conditioned on docs/reference migration completion. |
| `make studio-run-batch-cleanup` | `make -C .repo_studios studio-orchestrate-dependency-import-hygiene --trigger-batch-cleanup` | Legacy Make target already removed; docs flagged. | No further action required beyond removing doc references and closing backlog ticket. |
| `make studio-run-standards-gap-suite` | `make -C .repo_studios studio-orchestrate-standards` | Shim now delegates to the topic orchestrator. | Retire alias 2026-01-16; ensure Standards Ops sign off after three successful weekly runs. |
| `python .repo_studios/scripts/orchestrators/orchestrate_health_suite.py` | `python .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py` | Health suite runner forwards into the meta orchestrator. | Remove shim once all CI jobs call the meta orchestrator directly and documentation updates merge (target 2026-01-16). |
| `python .repo_studios/scripts/orchestrators/run_standards_index_cli.py` (without legacy flag) | `python .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py` or CLI with redirect | Redirect active; operators only set `RUN_STANDARDS_INDEX_CLI_USE_LEGACY=1` when intentionally opting out. | Remove redirect path after documenting the standalone CLI retirement and draining residual usage (target 2026-01-16). |

## Agent Integration Outcomes (2025-12-05)

- Reviewed `repo_prompts.md` (v1.3.0) to confirm Phase 6 guardrails already direct agents to check
  `studio-orchestrate-<topic>` targets and recognise the `healthview` viewer slug—no prompt edits
  required.
- Executed the prompt validation dry-run documented in
  `.repo_studios/command_center/docs/phase_6/validation_runs/2025-12-05-healthview_prompt_review.md`;
  all assertions passed and the review captured in `PROMPT_VALIDATION_RESULTS.md`.
- Verified command-center automation references inside
  `.repo_studios/docs/automation/orchestrator_automation_hooks.md` now link back to this
  announcement so humans and agents see the same retirement schedule.

## Next Checkpoints

1. Wire warning banners for the remaining legacy Make aliases by 2025-12-12.
2. Capture nightly usage telemetry for the shims and store results alongside the Command Center
   decision log.
3. Re-run the agent prompt validation suite before removing any shim to keep guardrail evidence
   current.
