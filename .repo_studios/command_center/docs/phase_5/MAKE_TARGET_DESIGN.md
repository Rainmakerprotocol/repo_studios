# Phase 5 Make Target Design

## Purpose

Outline the proposed `make` targets that will eventually wrap the command center orchestration and automation rehearsals without implementing any code changes yet. This design preserves auditability, mirrors the reference plan naming (`studio-detect-duplicates`, `studio-refactor-duplicates`), and documents operator expectations ahead of Phase 5 development.

## Design Principles

- Reuse the existing command center orchestrator (`run_command_center_pipeline.py`) and dry-run automation CLI (`run_automation_dry_run.py`) so Make targets stay thin wrappers.
- Keep all logging routed through the delegated scripts; the Make layer only forwards flags and environment variables.
- Ensure Windows and POSIX parity by surfacing example invocations with `pwsh` friendly syntax and letting callers override `PYTHON`.
- Mirror the existing retention policy (keep latest three runs unless `.keep` is present) and document where artifacts land so operators know where to collect evidence.
- Require explicit repo-root arguments (`--repo-root .`) for deterministic path resolution in local and CI contexts.

## Proposed Targets

### `studio-detect-duplicates`

Purpose: Refresh duplicate insights for a single slug using the existing command center pipeline.

Command flow (pseudocode):

```makefile
PYTHON ?= .venv/Scripts/python.exe

studio-detect-duplicates:
    $(PYTHON) .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
        --repo-root . \
        --target $(TARGET) \
        --log-level INFO
```

Key notes:

- `TARGET` defaults to `scripts` but should allow overrides (e.g., `scripts/summarizers`).
- The orchestrator threads inventory → analysis → duplicate scan; Make target simply captures the exit code.
- Operators should run `make studio-detect-duplicates TARGET=.repo_studios/scripts` or set `TARGET=.repo_studios/scripts/summarizers` for scoped runs.
- Outputs: timestamped artifacts under the target slug (e.g., `.repo_studios/scripts/summarizers/summarizers_index/`) and mirrored duplicates scan under `.repo_studios/command_center/reports/<slug>_duplicate_scan/`.
- Failure behavior: Make exits on the first non-zero code, matching orchestrator semantics.

### `studio-refactor-duplicates`

Purpose: Exercise the automation dry-run workflow to rehearse duplicate extractions.

Command flow (pseudocode):

```makefile
PYTHON ?= .venv/Scripts/python.exe

studio-refactor-duplicates:
    $(PYTHON) .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py \
        --repo-root . \
        --target $(TARGET) \
        --log-level INFO
    $(PYTHON) .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py \
        --repo-root . \
        --timestamp $(RUN_STAMP) \
        --targets $(TARGET)
```

Key notes:

- The target first refreshes the baseline artifacts via the orchestrator and then launches the automation dry run.
- `RUN_STAMP` defaults to the current UTC timestamp if not provided; callers can override for reproducibility.
- Inputs bundle, manifest, and metrics summary are written under `.repo_studios/command_center/reports/repo-studios__command-center__automation_run/automation_manifest-<timestamp>/`.
- The target should fail fast if the dry run reports guardrail violations (`max_files_per_run`, lock checks, etc.).
- Future automation wiring can append post-run pytest invocations defined in `phase_4/POST_RUN_TEST_MATRIX.md`.

## Operator Checklist Integration

- Each target will print the location of generated artifacts so operators can populate the PR checklist template (`phase_4/PR_CHECKLIST_TEMPLATE.md`).
- The Make documentation will reference the weighted progress briefing template to maintain reporting continuity.
- Before implementation, review branch protection requirements for `.github/workflows/verify-command-center-locks.yaml` to ensure CI lock checks trigger when these targets run in pipelines.

## Dependencies & Risks

- Requires the orchestrator and automation CLIs to remain stable; any flag changes must propagate to the Makefile simultaneously.
- Makefile should live under `.repo_studios/` to align with existing command center tooling (`make -C .repo_studios command-center`).
- Windows operators must have access to GNU `make` (via Git for Windows, MSYS2, or Chocolatey) or follow the documented PowerShell fallback script.

## Windows Tooling Validation (2025-11-04)

- **Detection:** `pwsh` users can validate availability with `Get-Command make` or `make --version`; Git for Windows installs `make.exe` under `C:\Program Files\Git\usr\bin` by default.
- **Recommended installation:** `choco install make` (Chocolatey) or `pacman -S make` inside MSYS2. Include the binary on `PATH` so the Make targets work from PowerShell.
- **Fallback workflow:** Provide a `pwsh` helper script (`scripts\windows\studio-detect-duplicates.ps1`) that proxies the Make logic by invoking the orchestrator and dry-run CLIs directly. Document usage in the command center README for environments without GNU `make`.
- **CI implications:** Windows runners must install `make` explicitly (e.g., via Chocolatey) before invoking Phase 5 targets; Linux runners can rely on system packages (`apt-get install make`).
- **Action:** Publish installation and fallback instructions alongside the Makefile when implementation lands so operators can self-check tooling before running automation rehearsals.

## Target Contract and Guardrail Surfacing (2025-11-04)

- **Environment variables:**
- `PYTHON` defaults to `.venv/Scripts/python.exe` on Windows and `./.venv/bin/python` on POSIX; callers may override with `PYTHON=<path>`.
- `TARGET` defaults to `.repo_studios/scripts`; scoped runs accept any slugged path such as `.repo_studios/scripts/summarizers`.
- `RUN_STAMP` optional; when omitted the dry-run script generates an ISO8601 timestamp slug. Operators can pin deterministic runs with `RUN_STAMP=2025-11-04T19-00-00Z`.
- **Flag forwarding:** Both targets pass `--repo-root .` and `--log-level INFO` while allowing extra flags via `EXTRA_ARGS` (future extension). Any CLI changes must update the Makefile and documentation in lockstep.
- **Guardrail surfacing:**
- Prior to invoking automation, the Make targets echo a reminder to run `verify-command-center-locks` or reference the latest workflow status.
- After the dry run completes, the target prints the manifest path, metrics summary path, and reiterates post-run pytest commands from `phase_4/POST_RUN_TEST_MATRIX.md`.
- Guardrail violations (lock present, `max_files_per_run` breach) bubble up from the automation CLI; the Makefile must propagate non-zero exit codes.
- **Operator prompts:** Add `@echo` statements that reference the PR checklist template and weighted progress briefing so evidence capture stays consistent.
- **Documentation note:** Once implemented, the command center README needs an appendix capturing these defaults and the guardrail reminder output.

## CI Rehearsal Job Outline (2025-11-04)

- **Workflow location:** `.github/workflows/studio-make-dryrun.yml` (proposed) triggered on pull requests touching `.repo_studios/` or the Makefile.
- **Matrix:** `os: [ubuntu-latest, windows-latest]` to guarantee parity; Windows job installs GNU `make` via Chocolatey.
- **Steps (per OS):**
    1. Checkout repository with depth 0 for accurate timestamps.
    2. Set up Python using `actions/setup-python` (3.11) and restore `.venv` via `pip install -r requirements.txt`.
    3. Install GNU `make` on Windows (`choco install make`) and verify with `make --version`.
    4. Run `make -C . studio-detect-duplicates TARGET=.repo_studios/scripts --dry-run` (dry-run flag to confirm wiring once implemented).
    5. Run `make -C . studio-refactor-duplicates TARGET=.repo_studios/scripts RUN_STAMP=${{ steps.timestamp.outputs.value }}` pointing at a deterministic timestamp; capture manifest/metrics paths as artifacts.
    6. Execute post-run pytest smoke suites (`pytest .repo_studios/tests/tests_command_center/orchestrators/test_run_automation_dry_run.py`).
- **Artifacts:** Upload automation bundle directories from both OS runs for inspection.
- **Guardrail reporting:** Summarize lock check status and `max_files_per_run` results in the job output, failing the job if violations occur.
- **Next steps:** Finalize the workflow once Make targets exist; until then, document this plan so CI integration is ready when development begins.

## Health Suite Orchestrator Impact Summary (Draft 2025-11-04)

- **Current state:** The health suite orchestrator continues to call the inventory → analysis → duplicate scan sequence directly; introducing Make targets must preserve that contract without duplicating orchestration logic.
- **Impact assessment:**
- The `studio-detect-duplicates` Make target simply wraps the orchestrator, so no additional orchestration layer is added; health suite orchestration should remain untouched, relying on direct Python invocations in CI until Make targets pass review.
- `studio-refactor-duplicates` adds a dry-run automation invocation after the orchestrator completes; health suite orchestrators should not call this target automatically to avoid triggering automation without approval.
- **Integration plan:**
- Document in the health suite README that the new Make targets are optional operator conveniences and should not replace the orchestrator module in existing CI workflows until automation is enabled.
- When the Make targets are approved, add a note to `.repo_studios/command_center/README.md` clarifying when to use Make vs. direct Python invocations (e.g., Make for local workflows, orchestrator modules for automated health suite runs).
- Ensure any future orchestration updates reference the Post-Run Test Matrix so test coverage remains aligned regardless of Make usage.
- **Open question:** Will the health suite orchestrator eventually offer a flag to call the dry-run automation CLI? Capture this as a decision point in Phase 7 once automation readiness is re-evaluated.

## Documentation Cross-Link Plan (Draft 2025-11-04)

- **Primary updates once Make targets land:**
- `.repo_studios/command_center/README.md` → add new section covering Make targets, env var defaults, guardrail reminders, Windows fallback script, and PR checklist references.
- `.repo_studios/scripts/README.md` → note the availability of studio Make targets alongside existing command center Make invocation guidance.
- `.repo_studios/command_center/docs/metrics/weighted_progress_briefing_template.md` → reference the Make targets as a preparation step for weekly automation briefings (ensuring the latest metrics exist).
- `.repo_studios/command_center/docs/guardrails/library_extraction_guardrails.md` → mention that Make targets surface guardrail reminders and rely on the same `max_files_per_run` enforcement.
- **Additional touchpoints:**
- `phase_4/POST_RUN_TEST_MATRIX.md` → add a sidebar reminding operators to use the Make targets’ post-run prompts when available.
- `repo_prompts.md` (Phase 6) → insert pointers to the Make targets so prompt-driven workflows know about the new entry points once prompts are revised.
- **Publication timing:** Make these documentation updates part of the Make target implementation PR to keep instructions synchronized with tooling changes.

## Next Steps

1. Review this design with the developer to confirm target naming, flag defaults, and artifact messaging.
2. Extend the design with post-run test hooks referencing `phase_4/POST_RUN_TEST_MATRIX.md` once automation readiness is confirmed.
3. Document the PowerShell fallback script skeleton in the repository tooling guide before wiring Make targets.
4. Implement the Makefile changes in Phase 5 after approval, ensuring CI and local workflows stay consistent.
