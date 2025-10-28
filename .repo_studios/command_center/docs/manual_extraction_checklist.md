# Manual Extraction Checklist (Repo Studios Command Center)

Use this checklist whenever you migrate a duplicated helper into `.repo_studios/library/`. It adapts the Phase 3 guide for Repo Studios workflows, Windows shell conventions, and the refreshed orchestrator pipeline (2025-10-28).

> **Tip:** Copy this file into your run notes (for example `checklists/2025-10-28-library-extraction.md`) and tick items as you progress. Keep the pristine version in `docs/` for reference.

---

## 0. Pre-flight (once per work session)

- [ ] Confirm you are on a clean branch derived from `main`.
- [ ] Ensure the virtual environment is active (`.venv\\Scripts\\Activate.ps1`).
- [ ] Run the orchestrator for the target folder to refresh artifacts:

  ```powershell
  make -C .repo_studios command-center COMMAND_CENTER_TARGET=/.repo_studios/command_center/scripts/ `
      PYTHON=.venv/Scripts/python.exe
  ```

- [ ] Note the latest duplicate matrix/summary paths under both `<target>/<name>_index/` and `.repo_studios/command_center/reports/<slug>_duplicate_scan/`.
- [ ] Snapshot relevant matrix entries for the functions you plan to extract.

## 1. Scope & Planning

- [ ] Identify the canonical implementation to migrate (pick the version with the richest tests or most complete logic).
- [ ] Record the planned library destination using the naming conventions in `docs/naming_conventions.md` (e.g., `filesystem/path_operations/slugify_relative_path.py`).
- [ ] Log the intent and owner in the active checklist under `checklists/`.

## 2. Library Module Authoring

- [ ] Create the folder structure under `.repo_studios/library/` if it does not yet exist (max three levels deep).
- [ ] Add the new module with a public function that matches the filename (`verb_noun`).
- [ ] Copy (and adapt as needed) the canonical implementation into the new module.
- [ ] Provide a focused docstring describing inputs/outputs; keep implementation comments minimal.
- [ ] Export the function via `__all__` if appropriate.

## 3. Test Coverage

- [ ] Add or extend a unit test in `.repo_studios/tests/tests_library/…` covering primary behaviours and edge cases.
- [ ] Identify the producer/consumer/orchestrator tests affected and update fixtures or expectations.
- [ ] Run targeted tests locally:

  ```powershell
  C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest <relative-test-path>
  ```

- [ ] Capture test results (pass/fail, command used) for inclusion in the run summary.

## 4. Integration & Replacement

- [ ] Update all duplicate call sites to import the new library function.
- [ ] Remove redundant, now-empty helper definitions.
- [ ] Ensure logging/import order matches repository standards.
- [ ] Rerun affected test suites (orchestrator smoke, producer-specific, etc.) and verify green status.

## 5. Artifact Updates

- [ ] Re-run the orchestrator for each modified target directory to refresh duplicate matrices:

  ```powershell
  make -C .repo_studios command-center COMMAND_CENTER_TARGET=<target> `
      PYTHON=.venv/Scripts/python.exe
  ```

- [ ] Confirm the duplicate matrix shows the group resolved or reduced in count.
- [ ] Update the manual checklist with outcomes and follow-ups.

## 6. Documentation & Run Notes

- [ ] Fill out the run-folder summary (see `docs/run_folder_summary_template.md`) with:
  - Functions tackled and final status
  - Tests executed (with commands)
  - Any manual follow-up actions
- [ ] If naming conventions or process adjustments were required, update the relevant doc under `docs/`.

## 7. Wrap-up

- [ ] Run `git status` to double-check expected file changes only.
- [ ] Stage work-in-progress commits or open a draft PR as appropriate.
- [ ] Share the updated checklist/run summary with the reviewer.

---

*Keep historical copies of filled checklists alongside duplicate reports so future agents can trace what changed and why.*
