# Repo Studios Copilot Playbook

## Big Picture
- Automation lives in `.repo_studios/scripts` and is grouped into tiers: `producers/` (raw data), `consumers/` (single-hop analyzers), `aggregators/` (multi-source blends), `orchestrators/` (suite entry points), and `summarizers/` (final digests).
- Most scripts expose a `run(argv)` helper plus a thin `main()` shim so they can be imported safely in tests and orchestrators (see `scripts/command_center/duplicates/scan_duplicates.py`).
- Outputs are timestamped JSON/markdown assets co-located with the source folder (for example `scripts/aggregators/aggregators_index/aggregators_index-YYYY-MM-DD.json`) with history pruning rather than mutable pointers.

## Core Workflows
- Prefer `.repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py <target> --repo-root .` or `make -C .repo_studios command-center COMMAND_CENTER_TARGET=<target> PYTHON=.venv/Scripts/python.exe` to refresh the inventory → analysis → duplicate scan pipeline; the orchestrator chains the three scripts with a shared log level, threads the freshly written analysis path into the duplicate scan, and aborts on the first failure. `scan_duplicates.py` still accepts `--skip-upstream` when you need to reuse existing producer artifacts directly.
- Producers write inventories to `<target>/<name>_index/` and analyses alongside them; the duplicate scanner mirrors its matrix/summary into both the index directory and `.repo_studios/command_center/reports/<name>_duplicate_scan/`.
- When scripting locally prefer dynamic imports plus `run(argv)` invocations over spawning subprocesses, matching how `scan_duplicates.py` calls the inventory and analysis producers.

## Command Center Orchestrator
- **Purpose:** Provide a single make-style command for refreshing the staged artifacts that underpin manual duplicate remediation.
- **How it works:** Loads each CLI’s `run(argv)` helper (inventory → analysis → duplicate scan), applies a shared `--log-level`, threads the freshly generated analysis file into the scan step, and stops on the first non-zero exit so partial runs do not slip through.
- **Outputs:** Emits no new files; it updates `<target>/<name>_index/`, `.repo_studios/command_center/reports/<slug>_analysis/`, and `.repo_studios/command_center/reports/<slug>_duplicate_scan/` via the delegated scripts. Each run writes a single timestamped matrix/summary pair and prunes stale siblings in both locations.
- **Triggers:** `producers/generate_function_inventory.py`, `summarizers/generate_function_analysis.py`, and `aggregators/scan_duplicates.py` with `--skip-upstream` to avoid redundant producer work.
- **Benefits:** Keeps sequencing deterministic, aligns with the library-integration micro-cycle, and ensures today’s slug-based retention stays tidy even when the pipeline is run repeatedly in a single day.

## Conventions & Patterns
- Logging goes through `logging` with level control, never `print`; honor the `--log-level` flag for every CLI.
- Markdown summaries follow `docs/standards/global/std-global-markdown-authoring.md`: single H1, tidy bullet hierarchy, and wrapped lines.
- Legacy `latest.json` pointers are being removed; ensure tests assert absence rather than recreating them (see `tests/tests_producers/test_generate_function_inventory.py`).
- Shared helpers live under `.repo_studios/command_center/scripts/libraries/` as a staging area; import `slugify_relative`, `copy_latest_artifact`, `write_report_artifacts`, and `cli` utilities from there rather than duplicating inline helpers. The CLI module now exposes config-driven builders (`PathsConfig`, `OptionsConfig`, `build_standard_paths`, `build_standard_options`) and every Command Center producer already consumes them—mirror that pattern whenever you touch CLI glue. These modules must stay compliant with the library naming rules captured in `que_for_integration/refactor_library/phase_1/naming_conventions.md` (training copy at `.repo_studios/command_center/docs/naming_conventions.md`), so name new functions `verb_noun`, keep depth ≤3 levels when the real `.repo_studios/library/` tree is created, and document staging locations when helpers have not yet moved.
- Keep new helpers in ASCII and add explanatory comments only where the flow is non-obvious, per repository editing guidance.

## Testing & Validation
- Pytest suites live under `.repo_studios/tests`; target a subpackage when iterating (e.g. `pytest tests/tests_producers/test_generate_function_inventory.py`).
- Duplicate scanner logic is covered via `tests/tests_command_center/duplicates/test_scan_duplicates.py`; extend fixtures instead of writing ad-hoc test harnesses.
- Make targets typically depend on `PYTHON` env configuration—mirror existing invocations (`PYTHON=".venv/Scripts/python.exe"`) when documenting or scripting automation.

## Reference Material
- `repo_prompts.md` enumerates canonical prompt flows for agents; cite the appropriate key when working on scripted operations.
- Standards live in `docs/standards/global/`; consult them before touching Python, markdown, or cleanup processes.
- Library naming and staging guidance lives in `que_for_integration/refactor_library/phase_1/naming_conventions.md` (canonical) and `.repo_studios/command_center/docs/naming_conventions.md` (training copy); review before adding or relocating shared helpers.
- The scripts README (`.repo_studios/scripts/README.md`) documents tier responsibilities and migration notes—update it when adding or moving automation.

## Collaboration Tips
- Capture new artifacts alongside existing timestamped files so downstream aggregators do not break.
- Prefer adapting shared utilities or extracting new ones under `scripts/utilities/` when cross-tier logic emerges.
- Surface orchestration changes in `.repo_studios/Makefile` to keep local developer workflows consistent with automation.
- When expanding duplicate reporting, ensure both the index directory and `command_center/reports` receive matching matrix/summary pairs even when no groups are found.

## Terminal Coordination
- Use `terminal-tools_sendCommand` with `captureOutput: true` whenever command output or logging is required; avoid bare fire-and-forget sends.
- Prefer unbuffered invocations (`python -u`) or tee (`2>&1 | Tee-Object`) so Python logging reaches the transcript immediately.
- For inline Python snippets stick to PowerShell here-strings (`@'... '@ | python -`); do not mix Bash-style `<<'PY'` heredocs.
- When reusing a terminal, call `logging.basicConfig(..., force=True)` or open a fresh session so subsequent CLI runs emit logs.
- If a command remains quiet, validate success by inspecting expected artifacts directly (for example `Get-ChildItem` on the target report folder).
