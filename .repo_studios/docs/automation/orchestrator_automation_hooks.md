# Orchestrator Automation Hooks

<!-- markdownlint-disable MD013 -->

This reference captures the current run surfaces, automation wiring, and success criteria for the Repo Studios
orchestrator tier. Record changes here before altering orchestrator code so downstream automation stays aligned
with expected behaviors.

| Script | Invocation Surface | Make Target | CI Hook | Expected Success Criteria |
| --- | --- | --- | --- | --- |
| `orchestrators/run_batch_cleanup.py` | `python .repo_studios/scripts/orchestrators/run_batch_cleanup.py [--mode ...] [--target ...] [--output-base ...] [--artifacts-to-keep ...] [--log-level ...] [--refresh-only]` | Pending (`studio-batch-clean` placeholder) | None | Command exits 0, creates `.repo_studios/reports/orchestrator_runs/run_batch_cleanup/run_batch_cleanup-<ts>/` bundles (`cleanup_summary.json`, `cleanup_log.txt`, `bundle_summary.json`), updates `latest_*` pointers, and records per-command status (including markdownlint availability). |
| `orchestrators/run_fault_pipeline.py` | `python .repo_studios/scripts/orchestrators/run_fault_pipeline.py [--repo-root ...] [--run-dir ...] [--skip-producer] [--skip-consumer] [--reuse-report ...] [--artifacts-to-keep ...] [--producer-artifacts-to-keep ...] [--consumer-artifacts-to-keep ...] [--log-level ...]` | `studio-run-fault-pipeline` | None | Command exits 0, writes `.repo_studios/reports/orchestrator_runs/fault_pipeline/fault_pipeline-<ts>/` bundles (`summary.json`, `SUMMARY.md`, `bundle_summary.json`, `pipeline.log`), maintains `latest_*` pointers, and mirrors artifacts into `.repo_studios/command_center/reports/fault_pipeline_orchestrator/` while enforcing retention. |
| `orchestrators/run_pytest_log_capture.py` | `python .repo_studios/scripts/orchestrators/run_pytest_log_capture.py [--repo-root ...] [--logs-dir ...] [--output-dir ...] [--artifacts-to-keep ...] [--log-level ...] [--from-log ...] [--from-junit ...] -- [pytest args...]` | None (invoked by health suite) | Planned addition to health suite once refactor lands | Writes `.repo_studios/reports/orchestrator_runs/pytest_log_capture/pytest_log_capture-<ts>/` bundles (`report.json`, `report.md`, `bundle_summary.json`, `failures.tsv/csv`, `skips.tsv/csv`, `full_log.txt`, optional `junit.xml`), refreshes `latest_*` pointers, stages raw logs under `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/`, prunes history to `--artifacts-to-keep` (default five), and returns pytest's exit code (including serial retry fallback on xdist hangs). |
| `orchestrators/orchestrate_health_suite.py` | `python .repo_studios/scripts/orchestrators/orchestrate_health_suite.py [--timestamp ...] [--live]` | Pending (`studio-health-suite` placeholder) | None | Generates `.repo_studios/reports/orchestrator_logs/health_suite_logs/<ts>/` with `status.json` and `status.md` (mirrored into the legacy folder for consumers), preserves per-step logs, and records non-zero step exits in status payload while overall command exits 0. |
| `orchestrators/run_standards_index_cli.py` | `python .repo_studios/scripts/orchestrators/run_standards_index_cli.py [--repo-root ...] [--output-dir ...] [--index-path ...] [--artifacts-to-keep ...] [--log-level ...] <subcommand>` | None (manual helper) | None | Subcommands (`list`, `search`, `show`, `stats`) exit 0, emit structured bundles under `.repo_studios/reports/orchestrator_runs/standards_index_cli/` (`report.json`, `report.md`, `bundle_summary.json`, `stdout.txt`), refresh `latest_*` pointers, and preserve stdout output for interactive use; non-zero exits record errors in the summary payload. |

## Notes

- The command center Make target (`make -C .repo_studios command-center COMMAND_CENTER_TARGET=<path>`) now sits alongside
  `studio-run-fault-pipeline`; the remaining orchestrators still require manual invocation until their dedicated Make targets are added.
- Update this table whenever Make targets or CI hooks change so the script inventory can reference the latest wiring
  before orchestrator refactors proceed.

<!-- markdownlint-enable MD013 -->
