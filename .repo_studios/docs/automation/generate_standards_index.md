# generate_standards_index.py

**Last updated:** 2025-10-22

## Purpose

`generate_standards_index.py` assembles the canonical `repo_standards_index.yaml` by blending curated seed rules with optional heuristic extractions from markdown sources. The producer now emits a structured artifact bundle (JSON/Markdown/log/raw copies) so agents can audit build metadata, extraction diagnostics, and integrity hashes without scraping the YAML directly.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_standards_index.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/standards_index_reports \
  --categories-path .repo_studios/scripts/.repo_studios/standards_categories.yaml \
  --seed-path .repo_studios/scripts/.repo_studios/standards_seed.yaml \
  --artifacts-to-keep 10
```

### Key arguments

- `--repo-root` (default repo checkout): base directory used to resolve all relative inputs/outputs.
- `--output-dir` (default `.repo_studios/reports/producer_reports/standards_index_reports`): structured run directory home. Created automatically.
- `--categories-path`: YAML mapping of standards categories and markdown sources.
- `--seed-path`: seed rules merged into the index before extraction.
- `--extraction-module` (optional): path to `standards_extraction.py` providing `extract_rules(...)`. When missing, the producer records a diagnostic and continues.
- `--index-path` (default `.repo_studios/scripts/repo_standards_index.yaml`): canonical YAML output.
- `--pending-path` (default `.repo_studios/scripts/repo_standards_pending.yaml`): draft queue populated when extraction runs but auto-accept is disabled.
- `--timestamp`: ISO8601 value used for the run slug. When omitted the script captures current UTC.
- `--artifacts-to-keep` (default `10`): retention window applied after each run (minimum of one directory).
- `--log-level` (default `INFO`): Python logging verbosity.

Environment flags:

- `ENABLE_STANDARDS_EXTRACTION=1` enables heuristic extraction for markdown sources listed in the categories file.
- `AUTO_ACCEPT_EXTRACTED=1` inlines extracted rules into the canonical index instead of writing them to the pending queue.

PyYAML must be available in the active Python environment.

## Outputs

Every invocation creates `.repo_studios/reports/producer_reports/standards_index_reports/standards_index-<timestamp>/` containing:

- `report.json`: canonical payload with fields
  - `schema_version`: currently `1`.
  - `status`: `ok`, `pending_extractions`, or `error`.
  - `timestamp` / `generated_utc`: sanitized slug and UTC build time.
  - `index_path`, `output_dir`, `pending_path`, `integrity_hash`, `version`.
  - `summary`: rule/category/source counts.
  - `extraction`: flags for enable/auto_accept, extracted and accepted counts, diagnostics, pending file location.
  - `notes`: condensation of extraction diagnostics or failure message.
- `report.md`: human-friendly rundown that surfaces counts, integrity hash, and detailed extraction diagnostics (when present).
- `log.txt`: key=value digest suitable for diff-friendly monitoring.
- `index.yaml`: exact YAML committed to the canonical location when the build succeeds.
- `raw.yaml` / `raw.txt`: identical YAML copies stored alongside the run for archival diffing. (`raw.txt` provides a plain-text representation for simple consumers.)

The output directory also maintains convenience links:

- `latest_report.json`, `latest_report.md`, `latest_report.log`.
- `latest_index.yaml`, `latest_raw.yaml`, `latest_raw.txt`.

When extraction is disabled or accepts no rules, the script writes `repo_standards_index.yaml` only. If extraction discovers rules but auto-accept is disabled, the producer also saves `repo_standards_pending.yaml` with metadata and diagnostics.

Historical run directories are pruned down to the configured retention window after each execution.

## Status semantics

- `ok`: build completed, no pending extraction queue was produced.
- `pending_extractions`: extraction ran with auto-accept disabled and emitted rules into the pending queue.
- `error`: build failed (missing inputs, validation errors, malformed extraction output, etc.). Failure details are reflected in `notes` and `log.txt`; canonical index is untouched.

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_standards_index.py`
verifies structured artifact creation, canonical YAML copies, failure telemetry, and pruning behavior.

## Operational notes

- The producer enforces deterministic hashing on rule IDs (`id|last_updated|severity`) so regressions are easy to detect.
- Extraction modules run in a sandbox via `runpy.run_path`; they must expose `extract_rules(path, categories, known_ids, today)`.
- Downstream agents should ingest `report.json` first and consult `index.yaml`/`raw.yaml` for rule contents.
- Because failure cases still populate artifact bundles, CI can rely on the presence of `report.json` and `status=error` to detect regressions without parsing stderr.
