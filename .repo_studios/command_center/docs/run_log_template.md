# Command Center Run Log Template

> Use this template to record each duplicate-remediation run so manual extractions stay auditable. Store per-campaign logs alongside report folders (for example, `.repo_studios/command_center/reports/2025-10-30-library-cleanup/RUNLOG.md`) and append a new entry for every run in reverse-chronological order.

---

## Usage Checklist

- Create the destination log file before kicking off a remediation cycle.
- Paste the entry block below and replace bracketed placeholders after each run completes.
- Link related artifacts (matrices, summaries, PRs) so reviewers can trace every change.
- Record skipped tests or outstanding follow-ups to surface risk early.

## Entry Block Template

````markdown
### Run [YYYY-MM-DD-HHMM]

- **Operator:** [Name or handle]
- **Targets:** [`/.repo_studios/scripts/<tier>/...`]
- **Run Window:** [Start time – End time]
- **Purpose:** [e.g., "Extract _copy_latest into shared library"]
- **Source Matrix:** [`<target>/<name>_index/<name>_duplicate_matrix-YYYY-MM-DD-HHMM.json`]
- **Summary Artifact:** [`<target>/<name>_index/<name>_duplicate_summary-YYYY-MM-DD-HHMM.md`]
- **Commands Executed:**

  ```powershell
  make -C .repo_studios command-center COMMAND_CENTER_TARGET=[target] PYTHON=.venv/Scripts/python.exe
  [additional commands]

  ```

- **Artifacts Produced:**
  - `[path/to/output.json]` – `[short description]`
  - `[path/to/output.md]` – `[short description]`

- **Tests Executed:**

  | Command | Scope | Result |
  | --- | --- | --- |
  | `C:/Users/genet/repo_studios/.venv/Scripts/python.exe -m pytest .repo_studios/tests/tests_producers/test_validate_inventory.py` | Inventory validation | ✅ |
  | `[command]` | `[suite]` | ✅/⚠️ |

- **Manual Verification:** `[notes about spot checks, file diffs, or linters]`
- **Checklist Updates:** `[link to updated checklist entry]`
- **Follow-Ups:**
  - [ ] `[e.g., rerun scan on summarizers after refactor]`
  - [ ] `[additional TODO]`

---

````

*Keep log entries concise but complete so downstream automation can parse them once the workflow graduates to CI.*
