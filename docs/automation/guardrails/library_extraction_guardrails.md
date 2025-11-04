# Library Extraction Guardrails

**Status:** Draft (2025-10-30)

## Purpose

Provide the mandatory safeguards required before any automated extraction or mass-remediation tooling operates on Repo Studios scripts. These guardrails ensure duplicate remediation remains auditable, reversible, and consistent with the manual Phase 3 workflow documented in `.repo_studios/command_center/`.

## Scope

These guardrails apply to any automation that modifies source files based on duplicate or complexity analysis (for example, future `refactor_from_report.py` tooling). They cover pre-run validation, execution controls, logging expectations, and post-run verification.

## Guardrail Overview

| Domain | Guardrail | Requirement |
| --- | --- | --- |
| Pre-flight validation | **Dry-run availability** | Automation must support an idempotent dry-run that emits proposed edits as artifacts without touching source files. Output includes patch previews and affected targets derived from current duplicate matrices. |
| Pre-flight validation | **Dependency freshness** | The latest inventory, analysis, duplicate scan, and lizard reports must be regenerated immediately before execution (use the command center orchestrator). Automation refuses to run if artifacts are older than 24 hours relative to start time. |
| Execution controls | **Target allow-list** | Only directories explicitly enumerated in a configuration file (checked into version control) can be modified. The allow-list references slugged duplicate reports and is reviewed before each run. |
| Execution controls | **Concurrent run lock** | Automation writes a lock file under `.repo_studios/command_center/run_locks/` to prevent concurrent refactors. Stale locks older than four hours require manual clearance. |
| Execution controls | **Run size cap** | Pre-flight validation enforces a `max_files_per_run` budget defined in the guardrail configuration. Overrides require documented approval and CI lock acknowledgement. |
| Safety net | **Transactional workspace** | All edits occur inside a throwaway git worktree or branch. Automation shells out only after verifying `git status` is clean and aborts if uncommitted changes exist. |
| Safety net | **Rollback bundle** | Each run produces a rollback bundle (patch + copied originals) under `.repo_studios/command_center/reports/<slug>_automation_run/`. Bundles include the commit SHA used as baseline and restore instructions. |
| Logging | **Structured log stream** | Execution logs use key/value pairs (matching producer conventions) and stream to both stdout and a timestamped `automation.log`. Include run metadata, targets touched, actions taken, and exit code. |
| Logging | **Artifact manifest** | Automation emits a manifest JSON summarising every file touched, grouped by outcome (`updated`, `skipped`, `conflicted`). Manifest lives alongside the rollback bundle. |
| Reporting | **Run artifact retention** | Automation writes artifacts via `write_report_artifacts` with a default `keep=3`; teams add a `.keep` sentinel or documented override when longer history is required. |
| Verification | **Post-run pytest** | Automation must trigger the relevant pytest suites (producer regressions + library integration tests) and halt on any failure. Results are stored with the manifest. |
| Verification | **Manual sign-off checkpoint** | A human reviews the manifest, rollback bundle, and test results before merging changes. Automations conclude by opening a draft PR with a checklist referencing this guardrail document. |

## Implementation Notes

1. **Dry-run contract**
   - Implement a `--dry-run` flag returning a diff bundle (`*.patch`) and machine-readable summary (JSON). Consumers can inspect the artifacts and rerun without the flag once approved.
   - Highlight how the diff aligns with duplicate scan groups by embedding group IDs in the summary.

2. **Baseline freshness**
   - Wrap automation with the command center orchestrator: `run_command_center_pipeline.py <target> --repo-root . --log-level INFO --skip-scan 0` (future flag) or explicitly run the three producers before automation kicks in.
   - Validate timestamps by parsing the freshly written `*-duplicate_summary-YYYY-MM-DD.md` files. Abort if the timestamp delta exceeds the configured threshold.

3. **Allow-list management**
   - Store the allow-list as `docs/automation/guardrails/allowed_targets.yaml` containing slug IDs, paths, and owner notes.
   - Require a checklist entry documenting updates to this file prior to each automated run.

4. **Worktree isolation**
   - Automation creates a temporary worktree (e.g., `.repo_studios/tmp/worktrees/library-refactor-<slug>`). Clean up on success or failure and include the cleanup status in the log stream.

5. **Rollback bundle contents**
   - `originals/` – copies of files before modification.
   - `patches/changes.patch` – unified diff generated post-run.
   - `pytest_results.json` – structured report of executed tests.
   - `manifest.json` – summary of touched files, referencing duplicate group IDs (see `docs/automation/guardrails/automation_manifest_schema.md`).
   - `metrics_summary.json` – impact snapshot that follows `docs/automation/metrics/metrics_summary_schema.md`.
   - `README.md` – instructions to apply the patch or restore originals.
   - Store bundles under `.repo_studios/command_center/reports/repo-studios__command-center__automation_run/` with mirrored `latest_automation_manifest.json` and `latest_metrics_summary.json` pointers for reviewers.

6. **Logging & telemetry**
   - Use the shared logging helper once it moves into the library (`configure_basic_logging`) and integrate with the command center retention utilities so logs are pruned to the latest three runs.
   - Include run metadata (`run_id`, `targets`, `dry_run`, `git_branch`, `lock_file`) in the first log entries for quick traceability.

7. **CI lock enforcement**
   - Publish a reusable GitHub Actions workflow (draft lives in `phase_4/AUTOMATION_PLANNING_NOTES.md`) at `.github/workflows/verify-command-center-locks.yaml`.
   - Require dependent automation jobs to invoke the workflow via `workflow_call` before any destructive step and block merges when it fails.
   - Allow manual overrides only when `allow-ignore: true` is passed alongside a checklist entry referencing who approved the bypass and why.
   - Store lock files in `.repo_studios/command_center/run_locks/` with descriptive names (`<slug>-automation.lock`) and capture snapshots as CI artifacts on failure for auditing.
   - Workflow landed 2025-10-31; `Command Center Automation Guardrails` (`.github/workflows/command-center-automation.yml`, added 2025-11-03) now invokes `verify-command-center-locks` so branch protection can require the lock check status before automation steps execute.

8. **Run size cap enforcement**
   - Define `constraints.max_files_per_run` inside `docs/automation/guardrails/automation_config.yaml`; default budget set to 15 files until phased review increases the cap.
   - Extend pre-flight validation to count targeted files before patch emission. Abort the run if the budget is exceeded unless `--allow-override` is supplied, in which case log the approving reviewer.
   - Emit the configured limit, actual file count, and override state in the automation manifest and run log header so reviewers can confirm compliance.
   - Helper reference: `.repo_studios/command_center/scripts/libraries/guardrails.py` exposes `load_guardrail_config` and `enforce_run_size_limit` for Phase 4 tooling and includes integration tests under `tests/tests_library_integration/libraries/test_guardrails.py`.
      - `generate_automation_manifest.py` (2025-11-03) now calls `enforce_run_size_limit` before writing artifacts, rejecting over-budget runs and carrying the enforced counts into manifest guardrail snapshots.

9. **Post-run validation**
   - Mandatory pytest commands:

      ```powershell
      C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_library_integration
      C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_producers
      ```

   - Capture exit codes and durations; include them in the manifest.

10. **Artifact retention policy**
    - Use the shared `write_report_artifacts` helper for all automation outputs; default `keep=3` ensures a short, reviewable history while avoiding report sprawl.
    - To retain more runs, drop a `.keep` sentinel inside the relevant directory or document an override in the guardrail log; monitor overrides during retrospectives.
    - Ensure retention expectations are mirrored in the command center README and automation checklist so operators know when additional pruning is required.

## Review & Sign-off Process

1. **Distribute draft:** Share this document with the command center steward(s), producer owners, and QA liaison via the `#repo-studios-command-center` channel and attach it to the Phase 3 checklist entry.
2. **Collect feedback:** Allow a two-business-day comment window. Track questions or requested amendments in the checklist so the next revision is discoverable.
3. **Record approvals:** Update the table below as reviewers sign off. A minimum of one steward and one QA representative must approve before automation planning proceeds.

| Role | Reviewer | Status | Notes |
| --- | --- | --- | --- |
| Command center steward | Genet (self) | ☑ Approved | Signed off 2025-10-31 via checklist note |
| Producer representative | Genet (self) | ☑ Approved | Single-owner project; approval recorded 2025-10-31 |
| QA liaison | Genet (self) | ☑ Approved | QA responsibilities owned by same operator; noted 2025-10-31 |
| Automation engineer (optional) | Genet (self) | ☑ Approved | Acting automation owner; approval logged 2025-10-31 |

## Open Questions

- Should the guardrail lock integrate with CI (e.g., GitHub environment protection) to prevent concurrent automations across clones?

   **Working response (2025-10-31):** Yes—link the lockfile state to a GitHub environment check so concurrent automation runs fail fast. Follow-up: reusable workflow documented in Implementation Note 7; next step is landing the CI file and wiring branch protection.

- Do we enforce a maximum number of files per run to keep review manageable, or is the allow-list sufficient?

   **Working response (2025-10-31):** Cap automated refactors to 15 files per run while the allow-list remains the source of truth. Action item: `automation_config.yaml` now reserves `constraints.max_files_per_run`; implementation must wire the validator and manifest reporting per Implementation Note 8.

- How do we surface metrics (lines deduplicated, groups resolved) automatically from the manifest for the Phase 7 validation plan?

   **Working response (2025-10-31):** Extend the manifest post-processor to emit a metrics snippet (`metrics_summary.json`) aggregating lines touched and duplicate groups resolved. Schedule design work during Phase 4 automation planning.

## Next Steps

1. Review and approve these guardrails with the steward(s) of the command center workflow.
2. Backfill the allow-list and rollback directory structure so manual dry-runs can rehearse the process.
3. Update `.repo_studios/command_center/README.md` with a summary and pointer to this document once approved.
4. Enforce these requirements in the future automation design brief (Phase 4) before any implementation begins.
