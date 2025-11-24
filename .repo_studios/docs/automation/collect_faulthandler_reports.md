# collect_faulthandler_reports.py

**Last updated:** 2025-11-23

## Purpose

`collect_faulthandler_reports.py` converts raw faulthandler capture directories into structured bundles that downstream consumers can reuse without re-parsing stack logs. Each run produces JSON, Markdown, CSV, and combined log artifacts, maintains `latest_*` pointers, and prunes historical runs to a configurable retention window. The producer wraps the shared `utilities.fault_run_analysis` helpers so the consumer and orchestration flows stay in sync.

## Invocation

```bash
python .repo_studios/scripts/producers/collect_faulthandler_reports.py \
  --runs-dir .repo_studios/faulthandler \
  --output-dir .repo_studios/reports/producer_reports/faulthandler_reports \
  --artifacts-to-keep 10 \
  --log-level INFO
```

From `.repo_studios/`, run `make studio-collect-faulthandler-reports` to execute the producer with repository defaults.

### Key arguments

- `--runs-dir`: Directory containing timestamped faulthandler capture folders (default `.repo_studios/faulthandler`).
- `--run-dir`: Explicit run directory to process; when omitted the producer selects the newest run under `--runs-dir`.
- `--output-dir`: Destination for structured artifacts (default `.repo_studios/reports/producer_reports/faulthandler_reports`).
- `--artifacts-to-keep`: Number of historical run directories retained after pruning (minimum 1, default 10).
- `--top-frames`: Override for the number of stack frames captured per signature (defaults to utility constant).
- `--log-level`: Logging verbosity (`INFO` default).

## Outputs

Each execution creates `.repo_studios/reports/producer_reports/faulthandler_reports/faulthandler_report-<timestamp>/` containing:

- `report.json`: Canonical payload with summary metrics, signature list, manifest metadata, and process salt.
- `report.md`: Markdown summary highlighting signature counts, top frames, and thread blocks.
- `stacks.csv`: Tabular view of signatures (ID, count, top frame details, thread list, timestamps).
- `combined.txt`: Reconstituted stack log text for quick inspection.
- `log.txt`: Key metrics for CI parsing (generated UTC, run directory, signature counts, stack size).

The producer also refreshes `latest_*` pointers in the output directory (e.g., `latest_report.json`, `latest_report.md`, `latest_stacks.csv`, `latest_combined.txt`). Historical run directories are pruned to the configured retention threshold after each run.

## Diagnostics

`report.json` surfaces:

- `summary.signature_count`: Total unique signatures detected.
- `summary.thread_block_count`: Number of thread blocks parsed from the capture.
- `summary.stack_text_bytes`: Size of the original stack text payload.
- `signatures[*]`: Detailed fingerprints with top module/function/file/line and observed thread IDs.
- `manifest`: Persisted capture metadata (timestamp, interpreter, platform, flags) created via `ensure_manifest`.

`log.txt` mirrors critical metrics for automation workflows and can drive lightweight CI assertions.

## Testing

`pytest .repo_studios/tests/tests_producers/test_collect_faulthandler_reports.py`

The suite validates artifact emission, latest-pointer refresh, pruning behaviour, and resilience when captures are missing or malformed.

## Operational notes

- Ensure `utilities.configure_faulthandler_runtime` and `utilities.dump_faulthandler_snapshot` populate `.repo_studios/faulthandler/<timestamp>/` before running the producer; otherwise the command exits with a no-op message.
- Downstream consumers (e.g., `generate_fault_artifacts.py`) now prefer the structured producer payloads while retaining a fallback to on-demand parsing.
- When orchestrating repeated captures, adjust `--artifacts-to-keep` to balance audit history with storage limits; CI jobs should favour tighter retention (5–10 runs).
- The producer tolerates missing stack logs by still emitting `report.json` with empty signatures, enabling monitoring dashboards to distinguish between “no capture” and “no findings.”
