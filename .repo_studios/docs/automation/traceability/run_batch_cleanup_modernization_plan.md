# Run Batch Cleanup — Modernization Plan (Draft 2025-11-24)

## Status

- 2025-11-24: Modernization implemented in `.repo_studios/scripts/orchestrators/run_batch_cleanup.py` with structured bundles, retention, and import-safe entry point.
- 2025-11-24: Pytest coverage landed under `.repo_studios/tests/tests_orchestrators/test_run_batch_cleanup.py`.

Existing tables below retain the pre-modernization snapshot for historical context.

## Objective

Bring `.repo_studios/scripts/orchestrators/run_batch_cleanup.py` in line with the refactor loop blueprint by emitting structured run artifacts, supporting configurable pruning, and exposing a reusable `run(argv=None)` entry point so orchestrators and tests can invoke the cleaner without shelling out.

## Current State

| Aspect | Current Behaviour |
| --- | --- |
| Inputs | CLI-only parameters (`--target`, `--mode`, etc.) resolved at import time; no dependency injection for orchestrators. |
| Outputs | Single timestamped log file under `.repo_studios/cleanup_logs/` per execution; no bundle metadata, pruning, or latest pointer. |
| Retention | Log files accumulate indefinitely. |
| Entry Point | Script executes work in `__main__`; no import-safe `run()` helper or return payload. |
| Error Handling | Delegated to subprocess return codes; failures only surfaced through log inspection. |
| Testing | No pytest coverage; behaviour validated manually. |
| Tooling Gaps | `run_markdownlint()` silently skips when Node tooling is absent; no summary of executed commands. |
| Tree Refresh | `refresh_project_tree()` rewrites `.repo_studios/repo_standards_project.md` but does not retain provenance of source/targets. |

## Target Architecture

| Aspect | Target Behaviour |
| --- | --- |
| Inputs | `run(argv=None)` helper returning structured result; CLI remains intact. |
| Outputs | Timestamped run bundle directory under `.repo_studios/reports/orchestrator_runs/run_batch_cleanup/` containing `cleanup_summary.json`, `cleanup_log.txt`, and optional `bundle_summary.json`. |
| Retention | `--artifacts-to-keep` (default 5) trimming old bundles and updating `latest_*` pointers. |
| Entry Point | `run()` orchestrates steps based on options; `main()` shim only handles CLI exit codes. |
| Error Handling | Structured result captures per-command status and errors with exit codes. |
| Testing | Pytest module covering success path, markdown-only mode, retention pruning, and error propagation. |
| Tooling Gaps | Summaries record which commands executed/skipped and whether markdown tooling was available. |
| Tree Refresh | Records source markdown path, rendered root, and timestamp in bundle metadata for governance traceability. |

## Implementation Steps

1. **Refactor & Harden** — ✅ Completed 2025-11-24
   - Extracted `_parse_args()` and introduced `run(argv=None)` returning structured results.
   - Replaced global log files with bundle-scoped `cleanup_log.txt` under the generated run directory.
   - Added option wiring (`--output-base`, `--artifacts-to-keep`, `--log-level`) and command metadata capture.
   - Hardened markdown lint handling to report unavailable tooling within summaries.

2. **Outputs & Retention** — ✅ Completed 2025-11-24
   - Bundles now include `cleanup_summary.json`, `cleanup_log.txt`, and `bundle_summary.json`.
   - Implemented `latest_*` pointers plus `_prune_history()` honoring `--artifacts-to-keep`.

3. **Execute & Validate** — ✅ Completed 2025-11-24
   - Exercised full and markdown-only modes via the new `run()` helper in tests.
   - Confirmed tree refresh metadata captured in each summary.

4. **Testing** — ✅ Completed 2025-11-24
   - Added `.repo_studios/tests/tests_orchestrators/test_run_batch_cleanup.py` covering happy path, markdown-only, retention pruning, and command failure propagation with stubbed subprocesses.

5. **Documentation & Governance** — ✅ Completed 2025-11-24
   - Updated `script_inventory_architecture.md`, `docs/automation/orchestrator_automation_hooks.md`, and `.repo_studios/command_center/docs/decision_log.md` to reflect the modernized orchestrator outputs and options.

## Dependencies & Coordination

- Ensure Ruff, Mypy, Pytest, and markdownlint command invocations remain configurable via environment variables or CLI overrides for CI compatibility.
- Coordinate with command center team on desired retention defaults and log destinations.
- Confirm the refreshed tree block is acceptable to standards maintainers once provenance metadata is stored in the summary.

## Acceptance Criteria

- Import-safe `run()` function returns structured payload used by tests and future orchestrators.
- Cleanup runs emit structured bundle directories with pruning and latest pointers.
- Pytest suite passes locally and in CI with subprocess calls stubbed/mocked.
- CLI backwards compatibility maintained (existing flags continue to work).
- Documentation and decision log updated upon completion.

## Open Questions

- Should the tree-refresh helper move into a shared utility module for reuse across orchestrators?
- Do we need environment-driven opt-outs for Ruff/Mypy when CI stages provide their own lint/test steps?
- Is additional reporting (e.g., markdown of applied fixes) required for operator review beyond the JSON summary?
