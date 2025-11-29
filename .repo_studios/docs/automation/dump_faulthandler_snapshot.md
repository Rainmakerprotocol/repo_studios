# dump_faulthandler_snapshot.py

## Overview

`dump_faulthandler_snapshot.py` captures a one-off faulthandler stack dump and
stores it as a structured bundle under
`.repo_studios/reports/orchestrator_logs/faulthandler_snapshots/`. The utility is
idempotent, keeps the latest stacks accessible via `latest_*` pointers, and
prunes historical snapshot directories to a configurable retention window.

## Responsibilities

- Resolve `FAULT_*` environment variables (including the legacy
  `FAULT_LOGS_ALLOW_LEGACY` toggle) to determine the output directory.
- Import and enable `faulthandler` if necessary, then write a raw stack dump to
  `snapshot.txt` alongside structured metadata (`MANIFEST.json`,
  `bundle_summary.json`, `SUMMARY.md`).
- Enforce retention (default keep `10`) while preserving the latest snapshot.

## Environment Flags

| Variable | Default | Description |
| --- | --- | --- |
| `FAULT_SNAPSHOT_OUTDIR` | derived | Overrides the exact output directory. |
| `FAULT_SNAPSHOT_BASE_DIR` | derived | Overrides the base directory (defaults to orchestrator logs). |
| `FAULT_SNAPSHOT_TO_KEEP` | `10` | Retention window for snapshot directories. |
| `FAULT_LOGS_ALLOW_LEGACY` | `0` | When `1`, fallback to the legacy `.repo_studios/faulthandler/` root. |
| `FAULT_OUTDIR` | `''` | Reused when `FAULT_SNAPSHOT_OUTDIR` is unset for compatibility. |

All other `FAULT_*` flags are recorded in `MANIFEST.json` when present so
producers and orchestrators can trace provenance.

## Usage

Invoke directly:

```bash
python .repo_studios/scripts/utilities/dump_faulthandler_snapshot.py
```

or use the smoke Make target (see below) to run with repository defaults.

## Testing

Run the dedicated pytest suite:

```bash
.venv/Scripts/python.exe -m pytest \
  .repo_studios/tests/tests_utilities/test_dump_faulthandler_snapshot.py
```

## Automation

A smoke target is available for quick validation:

```bash
make -C .repo_studios studio-dump-faulthandler-snapshot-smoke
```

Set `FAULT_ENABLE=1 FAULT_DUMP_LATER=0` (or reuse the runtime defaults) before
invoking if you need the snapshot to run against an actively configured
faulthandler writer.

## Legacy Compatibility

When `FAULT_LOGS_ALLOW_LEGACY=1`, snapshots fall back to
`.repo_studios/faulthandler/<ts>/snapshot.txt`, matching the historical layout
used by the CI bootstrap script. This is intended for migration-only scenarios;
new automation should rely on the orchestrator logs tree.
