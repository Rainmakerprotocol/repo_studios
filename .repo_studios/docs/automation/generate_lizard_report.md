# generate_lizard_report.py

**Last updated:** 2025-10-22

## Purpose

`generate_lizard_report.py` runs `python -m lizard` across the owned source tree, captures the JSON output, and emits structured artifacts so downstream agents can track cyclomatic complexity hotspots and long functions. It is designed to be tolerant: regardless of scan results it exits with status `0`, encoding failure details inside the report payload.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_lizard_report.py \
  --repo-root . \
  --targets src package_a \
  --output-dir .repo_studios/reports/producer_reports/lizard_reports \
  --max-ccn 15 \
  --max-length 80 \
  --artifacts-to-keep 10
```

### Key arguments

- `--repo-root` (default `.`): working tree root used to resolve relative targets.
- `--targets` (optional, repeats): explicit directories/packages to scan. When omitted the script probes the default set `("agents", "api", "scripts")` under the repo root.
- `--extra-args`: verbatim switches appended before the targets (passes directly to `lizard`).
- `--output-dir` (default `.repo_studios/reports/producer_reports/lizard_reports`): structured reports home.
- `--timestamp`: ISO8601 string (UTC preferred) to seed the run directory. When omitted the script snapshots `datetime.now(timezone.utc)`.
- `--max-ccn`, `--max-length`: thresholds for flagging high-complexity or long functions (defaults respect `LIZARD_MAX_CCN` / `LIZARD_MAX_LENGTH` environment overrides).
- `--artifacts-to-keep` (default `10`): retention window applied after each run.
- `--log-level` (default `INFO`): Python logging verbosity during execution.

- `generate_lizard_report.py` always injects `-Ejson -i -1` ahead of any provided extra arguments so the lizard run emits JSON and never fails the producer because of warning counts. Supply your own `--extra-args` only when you need *additional* flags.
- On first use the script auto-installs a lightweight `lizard_ext.lizardjson` helper (vendored under `.repo_studios/vendor/lizard_ext/lizardjson.py`) into the active environment when it is absent, ensuring consistent JSON output across virtual environments.

`lizard` must be installed in the active Python environment (`pip install lizard`).

## Outputs

Each run creates `.repo_studios/reports/producer_reports/lizard_reports/lizard-<timestamp>/` containing:

- `report.json`: canonical payload with fields
  - `schema_version`: currently `1`.
  - `status`: one of `ok`, `issues`, `no_targets`, or `error`.
  - `timestamp`: sanitized slug used for the run directory.
  - `generated_utc`: ISO timestamp of execution.
  - `max_ccn`, `max_length`, `targets`, `command`, `command_str`.
  - `issue_count`: number of offending functions.
  - `files_scanned`: count of files emitted by lizard JSON.
  - `offenders`: list of `{path, name, cyclomatic_complexity, length}`.
  - `notes`: contextual warnings or failure reason (blank on success).
- `report.md`: human-readable summary with run parameters and a markdown table of top offenders (capped to 25 rows).
- `log.txt`: key/value digest for tooling plus an offenders section mirroring `report.json`.
- `raw.json`: verbatim `lizard` JSON output when parsing succeeds.
- `raw.txt`: combined stdout/stderr stream reformatted as pretty-printed JSON when available (also populated for failure cases).

The script also maintains convenience links at the output root:

- `latest_report.json`, `latest_report.md`, `latest_report.log`.
- `latest_raw.json`, `latest_raw.txt` when the respective raw artifacts are present.

Historical run directories are pruned after each execution according to `--artifacts-to-keep` (minimum retention is one run).

## Status semantics

- `ok`: lizard succeeded and no functions breached configured thresholds.
- `issues`: lizard succeeded and at least one offender exceeded thresholds.
- `no_targets`: the resolved target list was empty (raw artifacts remain blank).
- `error`: lizard invocation failed, produced empty output, or returned non-JSON data. Failure details live in `notes` and `raw.txt`.

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_lizard_report.py`
validates structured artifact creation, offender serialization, pruning behavior, and the `no_targets` path with simulated lizard output.

## Operational notes

- Downstream consumers should rely on `report.json` for deterministic parsing and fall back to `log.txt` for quick diff-friendly checks.
- When adding new default targets update both `DEFAULT_TARGETS` inside the script and any downstream documentation or allowlists.
- Because the producer never raises on failure, CI jobs must interpret `report.json["status"]` to detect scan regressions.
