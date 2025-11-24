# Orchestrator Automation Hooks

This reference captures the current run surfaces, automation wiring, and success criteria for the Repo Studios
orchestrator tier. Record changes here before altering orchestrator code so downstream automation stays aligned
with expected behaviors.

| Script | Invocation Surface | Make Target | CI Hook | Expected Success Criteria |
| --- | --- | --- | --- | --- |
| `orchestrators/run_batch_cleanup.py` | `python .repo_studios/scripts/orchestrators/run_batch_cleanup.py [--mode ...] [--target ...] [--output-base ...] [--artifacts-to-keep ...] [--log-level ...] [--refresh-only]` | Pending (`studio-batch-clean` placeholder) | None | Command exits 0, creates `.repo_studios/reports/orchestrator_runs/run_batch_cleanup/run_batch_cleanup-<ts>/` bundles (`cleanup_summary.json`, `cleanup_log.txt`, `bundle_summary.json`), updates `latest_*` pointers, and records per-command status (including markdownlint availability). |
| `orchestrators/run_pytest_log_capture.py` | `python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py [pytest args...]` | None (invoked by health suite) | Planned addition to health suite once refactor lands | Creates `.repo_studios/pytest_logs/<slug>/<ts>/` with `pytest.log`, `summary.json`, and `bundle_manifest.json`; process exits 0 when pytest succeeds or propagates pytest exit codes. |
| `orchestrators/orchestrate_health_suite.py` | `python .repo_studios/scripts/orchestrators/orchestrate_health_suite.py [--timestamp ...] [--live]` | Pending (`studio-health-suite` placeholder) | None | Generates `.repo_studios/health_suite/logs/<ts>/` with `status.json` and `status.md`, preserves per-step logs, and records non-zero step exits in status payload while overall command exits 0. |
| `orchestrators/run_standards_index_cli.py` | `python .repo_studios/scripts/orchestrators/run_standards_index_cli.py <subcommand>` | None (manual helper) | None | Subcommands (`list`, `search`, `show`, `stats`) exit 0, read `repo_standards_index.yaml`, and render output without mutating artifacts. |

## Notes

- The command center Make target (`make -C .repo_studios command-center COMMAND_CENTER_TARGET=<path>`) remains the only
  wired orchestrator today; the scripts above require manual invocation until their dedicated Make targets are added.
- Update this table whenever Make targets or CI hooks change so the script inventory can reference the latest wiring
  before orchestrator refactors proceed.
