# Automation Post-Run Test Matrix

**Status:** Draft (2025-10-31)

Applies to every Phase 4 automation dry-run or write-run. Operators should execute the suites below immediately after the automation step completes and record the results in the PR checklist.

---

## Required Suites

| Suite | Command | Purpose | Notes |
| --- | --- | --- | --- |
| Library integration | `pwsh.exe -NoLogo -Command "& .\.venv\Scripts\python.exe -m pytest .repo_studios/tests/tests_library_integration --maxfail=1 --durations=10"` | Validates shared helper modules and command center libraries. | Run even during dry runs to ensure helper refactors remain safe; capture timings for metrics summary. |
| Producer regression | `pwsh.exe -NoLogo -Command "& .\.venv\Scripts\python.exe -m pytest .repo_studios/tests/tests_producers --maxfail=1 --durations=10"` | Confirms producers consuming shared helpers still behave correctly. | Include `-k` filters only when triaging failures; rerun full suite before sign-off. |
| Command center orchestrators | `pwsh.exe -NoLogo -Command "& .\.venv\Scripts\python.exe -m pytest .repo_studios/tests/tests_command_center/orchestrators --maxfail=1 --durations=10"` | Smoke-checks orchestrator sequencing when automation touches orchestration helpers or targets. | Mandatory once automation manifests/orchestrators change; log command output in metrics summary. |

## Conditional Suites

| Condition | Additional Command | Rationale |
| --- | --- | --- |
| Automation touched docs/templates | `pwsh.exe -NoLogo -Command "& .\.venv\Scripts\python.exe -m pytest docs/tests --maxfail=1 --durations=10"` | Placeholder for future documentation validation tooling. |
| Automation modified docs/templates | `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest docs/tests` (future) | Placeholder for future documentation validation tooling. |

## Execution Guidance

1. Execute suites from a clean worktree or dedicated worktree slug created for the automation run.
2. Capture output via `pytest --maxfail=1 --durations=10` when diagnosing failures; attach logs to the PR.
3. Record pass/fail status and duration in `metrics_summary.json` and the PR checklist template.
4. When failures occur, halt the automation rollout, document remediation steps, and rerun the full matrix before resuming.
5. `run_automation_dry_run.py` copies this matrix into the run bundle and injects the parsed command lists into both `manifest.json` and `metrics_summary.json` under `post_run_tests`, so operators and automation tooling can trigger the suites directly from the artifacts.
