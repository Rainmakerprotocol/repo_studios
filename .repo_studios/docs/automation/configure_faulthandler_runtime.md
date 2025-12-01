# configure_faulthandler_runtime.py

## Overview

`configure_faulthandler_runtime.py` runs during interpreter start via the repository
sitecustomize shim. It standardises faulthandler defaults across every entry
point, creates structured artifacts under
`.repo_studios/reports/orchestrator_logs/faulthandler_logs/`, and writes the
metadata that downstream producers, consumers, and orchestrators rely on. The
helper now exposes a `bootstrap()` function so tests and utilities can drive the
setup without triggering import-time side effects.

## Responsibilities

- Ensures the repo root is present on `sys.path` and applies the global warning
  filters that keep CI noise manageable.
- Resolves `FAULT_*` environment variables, derives a timestamped run
  directory when `FAULT_OUTDIR` is not provided, and prunes historical runs to a
  configurable retention window (`FAULT_ARTIFACTS_TO_KEEP`, default `10`).
- Relies on the shared `prune_run_directories()` helper so `.keep` sentinels are
  honoured consistently across faulthandler utilities.
- Enables `faulthandler` with a thread-safe writer (`stacks.log`), optional
  stderr teeing (`FAULT_TEE_STDERR`), and recurring hang dumps when
  `FAULT_DUMP_LATER=1`.
- Emits `MANIFEST.json` and `bundle_summary.json` beside each run so the
  faulthandler producer (`collect_faulthandler_reports.py`) and orchestrators can
  ingest provenance, retention decisions, and activation status.

## Environment Flags

| Variable | Default | Description |
| --- | --- | --- |
| `FAULT_DISABLE` | `0` | Skip bootstrap entirely when set to a truthy value. |
| `FAULT_ENABLE` | `1` in CI, `0` locally | Controls whether faulthandler activation runs. |
| `FAULT_OUTDIR` | derived | Absolute path override for the run directory. |
| `FAULT_BASE_DIR` | derived | Base directory when overriding the default orchestrator logs path. |
| `FAULT_ARTIFACTS_TO_KEEP` | `10` | Retention limit (including the latest run). |
| `FAULT_TEE_STDERR` | `1` | Mirror writes to stderr when truthy. |
| `FAULT_DUMP_LATER` | `1` in CI, `0` locally | Enables recurring hang dumps via `dump_traceback_later`. |
| `FAULT_LOGS_ALLOW_LEGACY` | `0` | When `1`, reverts the base directory to `.repo_studios/faulthandler`. |

All other legacy flags (`FAULT_MIN_INTERVAL_SEC`, `FAULT_DUMP_TIMEOUT`,
`FAULT_MAX_DUMPS_PER_RUN`, `FAULT_REDACT_PATHS`) remain available and are
recorded in the manifest for downstream tooling.

## Testing

Unit coverage lives in
`.repo_studios/tests/tests_utilities/test_configure_faulthandler_runtime.py` and
exercises activation, retention pruning, and disabled flows through the public
`bootstrap()` helper.

Run the tests with:

```bash
.venv/Scripts/python.exe -m pytest \
  .repo_studios/tests/tests_utilities/test_configure_faulthandler_runtime.py
```

## Legacy Compatibility

The helper defaults to the orchestrator logs tree, matching
`collect_faulthandler_reports.py` and the fault diagnostics orchestrator
(`command_center/scripts/orchestrators/run_fault_diagnostics_overview.py`). Set
`FAULT_LOGS_ALLOW_LEGACY=1` (or explicitly provide `FAULT_OUTDIR`) when you need
captures under the historical `.repo_studios/faulthandler/` path for older
artifacts or reproductions.
