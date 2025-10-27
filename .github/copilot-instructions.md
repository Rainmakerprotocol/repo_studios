# Repo Studios Copilot Playbook

## Big Picture
- Automation lives in `.repo_studios/scripts` and is grouped into tiers: `producers/` (raw data), `consumers/` (single-hop analyzers), `aggregators/` (multi-source blends), `orchestrators/` (suite entry points), and `summarizers/` (final digests).
- Most scripts expose a `run(argv)` helper plus a thin `main()` shim so they can be imported safely in tests and orchestrators (see `scripts/command_center/duplicates/scan_duplicates.py`).
- Outputs are timestamped JSON/markdown assets co-located with the source folder (for example `scripts/aggregators/aggregators_index/aggregators_index-YYYY-MM-DD.json`) with history pruning rather than mutable pointers.

## Core Workflows
- Use `make -C .repo_studios studio-index path=<target>` to run the end-to-end inventory → analysis → duplicate scan pipeline; `scan_duplicates.py` now orchestrates upstream steps unless `--skip-upstream` is supplied.
- Producers write inventories to `<target>/<name>_index/` and analyses alongside them; the duplicate scanner mirrors its matrix/summary into both the index directory and `.repo_studios/command_center/reports/<name>_duplicate_scan/`.
- When scripting locally prefer dynamic imports plus `run(argv)` invocations over spawning subprocesses, matching how `scan_duplicates.py` calls the inventory and analysis producers.

## Conventions & Patterns
- Logging goes through `logging` with level control, never `print`; honor the `--log-level` flag for every CLI.
- Markdown summaries follow `docs/standards/global/std-global-markdown-authoring.md`: single H1, tidy bullet hierarchy, and wrapped lines.
- Legacy `latest.json` pointers are being removed; ensure tests assert absence rather than recreating them (see `tests/tests_producers/test_generate_function_inventory.py`).
- Keep new helpers in ASCII and add explanatory comments only where the flow is non-obvious, per repository editing guidance.

## Testing & Validation
- Pytest suites live under `.repo_studios/tests`; target a subpackage when iterating (e.g. `pytest tests/tests_producers/test_generate_function_inventory.py`).
- Duplicate scanner logic is covered via `tests/tests_command_center/duplicates/test_scan_duplicates.py`; extend fixtures instead of writing ad-hoc test harnesses.
- Make targets typically depend on `PYTHON` env configuration—mirror existing invocations (`PYTHON=".venv/Scripts/python.exe"`) when documenting or scripting automation.

## Reference Material
- `repo_prompts.md` enumerates canonical prompt flows for agents; cite the appropriate key when working on scripted operations.
- Standards live in `docs/standards/global/`; consult them before touching Python, markdown, or cleanup processes.
- The scripts README (`.repo_studios/scripts/README.md`) documents tier responsibilities and migration notes—update it when adding or moving automation.

## Collaboration Tips
- Capture new artifacts alongside existing timestamped files so downstream aggregators do not break.
- Prefer adapting shared utilities or extracting new ones under `scripts/utilities/` when cross-tier logic emerges.
- Surface orchestration changes in `.repo_studios/Makefile` to keep local developer workflows consistent with automation.
- When expanding duplicate reporting, ensure both the index directory and `command_center/reports` receive matching matrix/summary pairs even when no groups are found.
