# collect_test_log_reports.py Blueprint

**Updated:** 2025-11-23  
**Owner:** repo_studios_ai  
**Scope:** `.repo_studios/scripts/producers/collect_test_log_reports.py`

## Purpose

Design the dedicated pytest log producer so downstream consumers and orchestrators can reuse structured artifacts instead of re-parsing raw log bundles. The producer will wrap the shared helpers in `command_center.scripts.libraries.test_log_analysis` and emit timestamped JSON/Markdown/csv snapshots under the standard reports hierarchy with pruning and latest pointers.

## Entry Criteria

- Shared helpers for pytest log parsing exist (`command_center.scripts.libraries.test_log_analysis`).
- Orchestrators capture pytest runs into `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/<slug>/<timestamp>/` directories (legacy `.repo_studios/pytest_logs/` runs remain available during the migration window).
- Consumer (`generate_test_log_health_report.py`) still owns on-demand parsing logic.
- No structured producer currently mirrors pytest log health data under `.repo_studios/reports/producer_reports/`.

## Exit Criteria

- New producer module `collect_test_log_reports.py` located under `scripts/producers/`.
- CLI supports `--logs-dir`, `--output-dir`, `--artifacts-to-keep` (default 10), optional `--logs-run` override, and shared `--log-level` switch.
- Artifacts emitted per run:
  - `report.json` (verbatim payload from `build_test_log_report`).
  - `report.md` (from `render_markdown`).
  - `warnings_by_type.csv` and `warnings_by_file.csv` (optional future iteration) or equivalent CSV summarising top tables.
  - `slow_tests.csv` capturing nodeid + duration.
  - `combined.log` copy of selected pytest log (for tracebacks) when present.
- Latest symlinks/hardlinks maintained (`latest_report.json`, etc.) parallel to faulthandler producer behavior; history pruned to `--artifacts-to-keep`.
- Pytest added at `.repo_studios/tests/tests_producers/test_collect_test_log_reports.py` covering:
  - happy path (structured artifacts, pruning, latest pointers).
  - fallback behaviour when no pytest bundles found (returns sentinel metadata without raising).
- Documentation published under `docs/automation/collect_test_log_reports.md` outlining CLI, artifacts, pruning, and integration expectations.
- Make target `studio-collect-test-log-reports` wired in `.repo_studios/Makefile` mirroring existing patterns.
- `generate_test_log_health_report.py` reconfigured to reuse producer artifacts by default (future step, tracked separately).

## Inputs & Dependencies

| Dependency | Notes |
| --- | --- |
| `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/<slug>/<timestamp>/` | Expected directory tree created by `run_pytest_log_capture.py`; producer selects latest if none supplied. |
| `command_center.scripts.libraries.test_log_analysis` | Provides `build_test_log_report` and markdown rendering; producer imports through the shared Command Center library path with the legacy utility shim retained for older callers. |
| `defusedxml` (optional) | Used by utilities; producer must handle absence gracefully (utility already falls back to stdlib). |

## Output Layout

```text
.repo_studios/reports/producer_reports/test_log_reports/
  test_log_report-YYYYMMDD_HHMMSS/
    report.json
    report.md
    warnings_by_type.csv
    warnings_by_file.csv
    slow_tests.csv
    combined.log (best-effort copy)
  latest_report.json
  latest_report.md
  latest_warnings_by_type.csv
  latest_warnings_by_file.csv
  latest_slow_tests.csv
```

## CLI & Behaviour Notes

1. `--logs-dir`: Base directory (default `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs`; legacy `.repo_studios/pytest_logs` discovery remains available while the migration flag `PYTEST_LOG_REPORTS_ALLOW_LEGACY` is enabled).
2. `--logs-run`: Explicit run folder; when omitted select best run via heuristics:
   - prefer latest directory under `logs-dir` (sorted by mtime).
   - allow slug subdirectories; if `logs-dir` contains child folders, inspect each for latest run.
3. `--output-dir`: Defaults to `.repo_studios/reports/producer_reports/test_log_reports`.
4. `--artifacts-to-keep`: Integer cap ≥1; apply same pruning helper as faulthandler producer.
5. Logging via `logging.basicConfig` honoring `--log-level`.
6. Return metadata dictionary (`run_dir`, `logs_dir`, `output_dir`, `report_path`, `warnings_total`, `slow_count`).

## Implementation Plan

1. **Run Discovery**: Inspect `--logs-dir` for candidate run directories. Accept explicit `--logs-run`. Resolve to absolute paths.
2. **Analysis**: Call `build_test_log_report(logs_run)` to collect structured payload; reuse selected junit/log paths when available.
3. **Artifact Writing**:
   - JSON: pretty-print with stable key order.
   - Markdown: use `report["markdown"]` from `TestLogAnalysisResult` (or render on producer side).
   - CSV exports: convert counters and lists to deterministic tables.
   - Combined log: copy source pytest log if path available.
4. **Latest Links + Pruning**: Mirror `_update_latest` and `_prune_old_runs` helpers from faulthandler producer (consider extracting shared helper later).
5. **Return Metadata**: Provide structured dict to aid tests and orchestrators.

## Testing Strategy

- Unit tests (pytest) to simulate logs directory with synthetic junit + log fixtures; ensure counters computed as expected.
- Verify missing junit/log gracefully yields zeroed metrics and still emits JSON/MD.
- Confirm `--artifacts-to-keep=1` prunes older directories and maintains latest symlinks.
- Ensure CLI returns metadata with absolute paths and counts matching synthetic fixtures.

## Integration & Sequencing

1. Implement producer + tests.
2. Update script inventory blueprint producer table (mark pruning/test/docs states as tasks).
3. Publish automation doc and add Make target.
4. Follow-on task: update consumer to prefer producer artifacts (tracked separately).
5. Record completion in decision log.

## Open Questions

- Do we also emit histogram/plots (JSON) for warnings over time? Defer until visualization requirements clarified.
- Should combined log support gzip to save space? For now, plain text to match current consumer expectations.
- Confirm orchestrator slug naming (e.g., `pytest_suite/<timestamp>`). Implementation should surface slug in metadata for future dashboards.
