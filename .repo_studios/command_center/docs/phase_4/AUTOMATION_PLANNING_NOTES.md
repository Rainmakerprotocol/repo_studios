# Phase 4 Automation Planning Notes

**Status:** Draft (2025-10-31)

**Purpose:** Capture design inputs, guardrail follow-ups, and implementation sequencing for future automated extractions. This working doc bridges the approved Phase 3 guardrails with the automation work that will kick off once manual validation completes.

---

## Guardrail Follow-ups

- [x] **CI lock prototype** – Design a GitHub status check that reads `.repo_studios/command_center/run_locks/*.lock` and blocks automation jobs when active.
  - *Progress (2025-11-03):* Reusable workflow lives at `.github/workflows/verify-command-center-locks.yaml` and is now consumed by `.github/workflows/command-center-automation.yml`, registering the lock check as a CI status gate before automation runs.
- [x] **Max files per run** – Add a `max_files_per_run` setting alongside the allow-list and enforce it during pre-flight validation (default: 15 files).
  - *Progress (2025-11-03):* `generate_automation_manifest.py` now enforces the configured limit via `enforce_run_size_limit`, rejecting over-budget runs and surfacing the counts in manifest guardrail snapshots.
- [x] **Manifest metrics summary** – Extend the automation manifest to emit `metrics_summary.json` including lines touched and duplicate groups resolved.
  - *Progress (2025-11-03):* Automation manifest bundle now produced by `.repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py`, which writes `manifest.json` and `metrics_summary.json` via the new library helper (`.repo_studios/command_center/scripts/libraries/manifest.py`) with tests covering guardrail snapshots and pointer retention; schema documented at `.repo_studios/command_center/docs/guardrails/automation_manifest_schema.md`.

### CI Lock Status Check Draft (2025-10-31)

- **Goal:** Prevent concurrent automation runs by failing CI when a lock file exists under `.repo_studios/command_center/run_locks/`.
- **Status check outline:**

```yaml
name: verify-command-center-locks

on:
  workflow_call:
    inputs:
      allow-ignore:
        description: 'Set to true to bypass lock validation (manual overrides only)'
        required: false
        default: 'false'

jobs:
  lock-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Detect command center lockfiles
        id: detect-locks
        run: |
          LOCK_DIR=.repo_studios/command_center/run_locks
          if [ "${{ inputs.allow-ignore }}" = "true" ]; then
            echo "override enabled; skipping lock check"
            exit 0
          fi
          if [ -d "$LOCK_DIR" ] && ls "$LOCK_DIR"/*.lock 1> /dev/null 2>&1; then
            echo "Detected active automation lock(s):"
            ls "$LOCK_DIR"/*.lock
            exit 1
          fi
          echo "no lockfiles present"

      - name: Upload lock snapshot on failure
        if: failure() && steps.detect-locks.conclusion == 'failure'
        uses: actions/upload-artifact@v4
        with:
          name: active-locks
          path: .repo_studios/command_center/run_locks/*.lock
          if-no-files-found: ignore
```

- **Integration plan:**

  - Invoke this reusable workflow from automation pipelines before any destructive step.
  - Require success via GitHub branch protection so PR merges are blocked when locks exist.
  - For manual overrides, supply `allow-ignore: true` with explicit checklist approval.

- **Next steps:**

  - Validate lock directory structure and naming conventions.
  - Add documentation to the guardrail file describing override usage and audit expectations.

### `max_files_per_run` Configuration Draft (2025-10-31)

#### Manifest metrics summary schema draft

```json
{
  "schema_version": "1.0",
  "run_id": "2025-10-31T15-42-00",
  "targets": ["scripts-duplicates"],
  "lines_touched": 124,
  "files_changed": 9,
  "duplicate_groups_resolved": 3,
  "runtime_seconds": 312,
  "tests_executed": {
    "library_integration": {"status": "passed", "duration_seconds": 92},
    "producer_suite": {"status": "passed", "duration_seconds": 155}
  },
  "notes": "Dry-run rehearsal; no files written"
}
```

#### Validation checklist

- Ensure schema version is pinned and bumped on breaking changes; store canonical schema in `.repo_studios/command_center/docs/metrics/metrics_summary_schema.md`.
- Cross-check `lines_touched` and `files_changed` against the manifest totals before writing to avoid drift.
- Require at least `library_integration` and `producer_suite` test entries; additional suites may be appended.
- Emit the metrics summary alongside the manifest and rollback bundle; include the file path in the automation log header for visibility.

### Helper Adoption Audit CLI Spec (Draft 2025-10-31)

- **Spec reference:** `phase_4/HELPER_ADOPTION_CLI_SPEC.md` captures objectives, CLI contract, schema, and open questions.
- **Role:** Replaces manual spreadsheets by inventorying helper usage across allowed targets with machine-readable outputs.
- **Integration plan:** New producer (`audit_helper_adoption.py`) will reuse shared CLI builders, `write_report_artifacts`, and feed stats into future `metrics_summary.json` bundles.
- **Testing approach:** Add targeted fixtures under `tests/tests_producers/test_audit_helper_adoption.py` once implementation begins.

### Automation PR Checklist Template (Accepted 2025-11-03)

- **Completed:** Hardened the template on 2025-11-03 with guardrail references, manifest/metrics prompts, and attachment requirements (`phase_4/PR_CHECKLIST_TEMPLATE.md`).
- **In progress:** Operators populate the ready template for every manual Phase 4 run to document guardrails, link evidence, and summarize weighted progress impacts.
- **Upcoming:** Integrate an automated reminder into future tooling so the checklist link surfaces after each dry run and stays aligned as automation workflows evolve.

### Weighted Progress Briefing Template (Accepted 2025-11-03)

- **Template reference:** `.repo_studios/command_center/docs/metrics/weighted_progress_briefing_template.md` documents the weekly reporting structure that combines duplicate groups, lizard complexity, and helper adoption metrics.
- **Purpose:** Replace manual spreadsheets with a consistent briefing that feeds into Phase 4 readiness reviews and highlights overall weighted progress.
- **Status:** Template finalized with usage workflow, helper adoption linkage, and data source catalogue (2025-11-03).
- **Follow-up:** Schedule first briefing dry-run using the template and collect feedback for future weighting adjustments.

### Post-Run Test Matrix (Draft 2025-10-31)

- **Matrix reference:** `phase_4/POST_RUN_TEST_MATRIX.md` enumerates mandatory and conditional pytest suites to execute after every automation run.
- **Purpose:** Ensure library, producer, and orchestrator regressions are caught before PR submission and provide structured commands for operators.
- **Next steps:** Integrate the matrix with the PR checklist template and surface commands in future automation tooling (e.g., auto-suggest in logs).

### 2025-11-02 Implementation Update



```yaml
# .repo_studios/command_center/docs/guardrails/automation_config.yaml (draft)
allowed_targets:
  - slug: scripts-duplicates
    path: .repo_studios/scripts
    owners:
      - genet
    notes: Primary command center scripts

constraints:
  max_files_per_run: 15
  max_groups_per_run: 5
```


- Count files slated for modification before emitting patches.
- Fail pre-flight if the number exceeds `max_files_per_run` unless `--allow-override` is passed.
- Emit a summary in the automation manifest noting the configured limit and actual count.
- Guardrail helper `libraries/guardrails.py` now exposes `load_guardrail_config` and `enforce_run_size_limit` with library tests covering enforcement behaviour, and `generate_automation_manifest.py` now enforces the limit before writing artifacts.

- Guardrail doc: add subsection explaining the cap, override process, and rationale (keeps PRs reviewable).
- Checklist template: include checkbox confirming the file count was reviewed and within bounds.


### 2025-11-03 Implementation Update

- Helper adoption audit CLI now lives at `.repo_studios/command_center/scripts/producers/audit_helper_adoption.py`, producing `helper_adoption.json`/Markdown via shared artifact helpers with per-slug adoption counts and lists.
- Regression coverage added at `tests/tests_producers/test_audit_helper_adoption.py`, validating adoption vs. legacy detection, format toggles, and pointer mirroring.
- Planning spec (`phase_4/HELPER_ADOPTION_CLI_SPEC.md`) marked implemented with an execution summary for operators and future automation consumers.
- Automation PR checklist template promoted to ready status with expanded guardrail/testing prompts so PR reviewers receive consistent evidence without additional manual checklists.

### 2025-11-03 Dry-Run Rehearsal Pilot

- Generated the first rehearsal bundle via `run_automation_dry_run.py` (run id `dryrun-probe`, timestamp `2025-11-03T16:00:00Z`) targeting `scripts-duplicates`.
- Artifacts stored under `.repo_studios/command_center/reports/repo-studios__command-center__automation_run/automation_manifest-20251103_160000/` with mirrored pointers and README.
- Inputs sourced from `phase_4/dry_run_samples/files_sample.json` and `tests_sample.json`; guardrail snapshot copied from `.repo_studios/command_center/docs/guardrails/automation_config.yaml`.
- Metrics summary confirms 42 lines touched, 2 files changed, 1 duplicate group resolved, and captures pytest durations/outputs for post-run verification.
- Ran expanded rehearsal `dryrun-probe-02` (timestamp `2025-11-03T17:00:00Z`) covering multi-target metrics, guardrail helper updates, and the library integration pytest suite; artifacts live at `automation_manifest-20251103_170000/` with copied inputs and README.
- Developer reviewed both bundles on 2025-11-03; dry-run step now marked complete in the master checklist.
- Post-run test matrix refreshed with PowerShell commands, `--maxfail`/`--durations` flags, and orchestrator coverage so operators have exact commands prior to tooling integration.


### Automation Success Criteria (Accepted 2025-11-03)

- **Regression hygiene:** Maintain a four-week streak of manual extractions without rollback, with each run bundling rollback artifacts and passing the shared library + producer pytest suites.
- **Duplicate reduction:** Eliminate at least 80% of the duplicated helper occurrences identified in the 2025-10-28 matrix for the Phase 3 target set before enabling write automation.
- **Artifact fidelity:** Produce automation dry-run bundles whose manifest, metrics summary, and README contents match the manual baseline templates byte-for-byte aside from timestamps.
- **Guardrail compliance:** Demonstrate three consecutive dry-run rehearsals that honor lock checks, respect `max_files_per_run`, and document approvals in the guardrail log before requesting automation rollout.

*Status:* Ratified 2025-11-03 as the baseline gate for enabling automated write runs.

### Planning Sprint Success Criteria (Draft 2025-10-31)

- All success criteria above reviewed with developer, thresholds ratified, and recorded in this document and the master checklist.
- Dependency readiness checklist receives sign-off, with open items tracked via explicit follow-ups.
  - *Status update (2025-11-03):* Sign-off complete; see the updated dependency checklist below.
- Guardrail follow-up tasks each have documented status (CI lock workflow, run-size enforcement, metrics summary schema) and designated owners.
- Communication artifacts (helper adoption spec, weighted briefing, PR checklist, post-run test matrix) receive developer feedback or approval so configuration sprint can begin without ambiguity.

### Dependency Readiness Checklist (Draft 2025-10-31)

| Dependency | Status | Evidence/Notes |
| --- | --- | --- |
| Inventory and analysis producers | ✅ | Latest orchestrator run (2025-10-28) refreshed inventory + analysis without failure; artifacts stored under `.repo_studios/command_center/reports/`. |
| Duplicate scanner outputs | ✅ | `scan_duplicates.py` matrix mirrored for summarizers/utilities on 2025-10-28 with retention helper active. |
| Shared helper coverage | ✅ | Phase 3 helper backlog confirmed 2025-11-03; outstanding targets documented in the checklist and gated by the accepted success criteria before automation writes proceed. |
| Test coverage | ✅ | Library integration and producer suites green on Windows; automation dry-run regression coverage (`test_run_automation_dry_run.py`) now guards manifest/metrics flows, with cross-platform validation queued during the configuration sprint. |
| Library namespace slots | ✅ | Naming conventions and mapping recorded in `docs/duplicate_target_mappings.md`; no conflicting `.repo_studios/library/` tree identified. |
| Guardrail documentation | ✅ | `.repo_studios/command_center/docs/guardrails/library_extraction_guardrails.md` approved 2025-10-31; follow-up sections pending CI lock and run-size updates. |
| Metrics storage plan | ✅ | Weekly in-repo snapshots with manual monthly aggregates logged in metrics spec and reiterated here. |
| Operator playbooks | ✅ | Manual execution charter, run-log template, and PR checklist template (`phase_4/PR_CHECKLIST_TEMPLATE.md`) accepted 2025-11-03; operators now have end-to-end guidance. |

## Metrics Integration Tasks

- [x] **Helper adoption CLI requirements** – CLI implemented at `.repo_studios/command_center/scripts/producers/audit_helper_adoption.py`, emitting JSON/Markdown summaries with retention via `write_report_artifacts`; coverage captured in `tests/tests_producers/test_audit_helper_adoption.py` (2025-11-03).
- [x] **Long-term storage decision** – Retain weekly metric snapshots in-repo under `.repo_studios/command_center/reports/<campaign>/metrics-YYYY-MM-DD.json`, then publish a monthly aggregate (`metrics/monthly/metrics-YYYY-MM.md`) to shareable storage once automation matures. *(Decision logged 2025-10-31 — manual team will own exports until an automated pipeline exists.)*
- [x] **Weighted progress briefing template** – Template ready with weighting formula, usage checklist, and artifact source table for weekly briefings (updated 2025-11-03).

## Automation Design Brief (Manual)

### Objective

Deliver a vetted blueprint for automated duplicate extraction that adheres to Phase 3 guardrails, maintains auditability, and minimizes regression risk. Implementation remains manual until this brief is approved.

### Scope

- Targets: helpers already validated in Phase 3 (`slugify_relative`, `copy_latest_artifact`, `write_report_artifacts`, CLI configs, logging).
- Exclusions: new detection logic, non-command-center scripts, and any write automation beyond dry-run rehearsals.

### Deliverables

1. **Guardrail Configuration Pack**

   - Annotated allow-list with `max_files_per_run` entry.
   - CI lock status check design doc (GitHub workflow snippet + failure modes).
2. **Automation Workflow Spec**

   - Step-by-step flow (dry-run, staging worktree, tests, PR draft).
   - Updated rollback bundle schema (`manifest.json`, `metrics_summary.json`, `README.md`).
3. **Testing Matrix**

   - Mandatory test commands (library integration, producer suites, future automation smoke).
   - Manual verification checklist (file diff spot checks, docs updates).
4. **Reporting & Telemetry Plan**

   - Metrics capture/export process (weekly in-repo, monthly aggregate).
   - Weighted progress briefing template draft.

### Risks & Mitigations

- **Risk:** Automation exceeds manual guardrails. → Mitigation: enforce pre-flight validation and lock checks before any automated run.
- **Risk:** Regression feedback arrives late. → Mitigation: bundle post-run pytest results and require human approval before merge.
- **Risk:** Metric drift between manual and automated phases. → Mitigation: maintain shared snapshot format and document monthly export cadence.

### Acceptance Criteria

- All deliverables stored under `phase_4/` with cross-links in the main checklist.
- Guardrail and metrics decisions reflected in repository docs (`.repo_studios/command_center/docs/guardrails`, `.repo_studios/command_center/docs/metrics`).
- Dry-run rehearsal produces artifacts that match the specified rollback bundle without modifying source files.

## Manual Execution Charter

- The current Repo Studios team (including this coding agent) performs every Phase 4 artifact creation manually—no automated code mods will run until these deliverables are complete and validated.
- Manual runs must follow the Phase 3 guardrails: fresh artifacts, documented checklists, retention limits, and rollback bundles even during design rehearsals.
- Decisions, approvals, and storage exports are recorded immediately in the checklist or planning notes so future automation inherits a clean audit trail.

## Sequencing Roadmap (Manual)

1. **Planning Sprint** – Expand this document into a full automation design brief, capture success criteria, and confirm dependency readiness (fresh inventories, test coverage, library slots).
2. **Configuration Sprint** – Implement the CI lock status prototype, introduce `max_files_per_run`, and update allow-list/metrics storage configuration.
3. **Tooling Sprint** – Design the helper adoption CLI spec, extend the manifest with `metrics_summary.json`, and draft the weighted briefing template.
4. **Dry-Run Sprint** – Execute a scripted dry-run using disposable worktrees, capture rollback bundles, run required tests, and iterate on the PR checklist template before any real code mods. Document the `run_automation_dry_run.py` invocation (command, timestamp slug, bundle path) rather than wiring it into other orchestrators until the manual process is fully approved.

Each sprint remains manual: tasks may use scripts, but operators review, commit, and document outputs.

## Automation Decision Log (2025-11-03)

- **Library seeding strategy:** Treat `setup_library_structure.py` as a read-only blueprint; create library modules only when an extraction lands so every addition maps to a manifest entry.
- **Duplicate detector scope:** Keep `.repo_studios/command_center/scripts/aggregators/scan_duplicates.py` as the canonical detector through Phase 4; evaluate secondary signals after the core loop stabilises.
- **Orchestrator contract:** Retain `run_command_center_pipeline.py` as the inventory → analysis → duplicate-scan entry point and lock the current flag/exit-code semantics for downstream tooling.
- **Pilot helper scope:** Prioritise `_slugify_relative`, `_copy_latest`, `write_report_artifacts`, shared CLI helpers, and logging/bootstrap helpers in the first extraction wave.
- **Artifact retention policy:** Standardise on `write_report_artifacts` with `keep=3` by default, allowing `.keep` overrides for longer retention where justified.
- **Automation success gate:** Require the accepted four-week regression streak, ≥80% duplicate reduction, and 100% manifest/guardrail compliance before enabling automated writes.
- **Dry-run rehearsal path:** Keep `run_automation_dry_run.py` as a checklist-driven manual command until guardrails mature; a Make wrapper can follow once the process proves out.

## Decisions & Assumptions

- Guardrails are approved and binding for all future automation work (see sign-off table).
- Metrics remain in-repo until automation can publish to telemetry; monthly aggregates will be exported manually to maintain continuity with future pipelines.
- Sequencing assumes Phase 3 stays active; automation pilots will not begin until manual extraction achieves regression-free status for at least two consecutive weeks.

## Open Questions (Automation)

- How should we schedule automation to avoid clashing with manual remediation (e.g., quiet hours vs. explicit toggles)?
- What level of diff chunking keeps PRs reviewable without sacrificing throughput?
- Should we instrument telemetry hooks (e.g., Application Insights) once automation moves beyond dry-run pilots?
- How should weighted progress calculations adjust when helper adoption stats (from the forthcoming CLI) diverge from duplicate resolution rates?
