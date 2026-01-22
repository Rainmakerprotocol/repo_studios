# generate_standards_index.py

**Last updated:** 2026-01-22

## Purpose

`generate_standards_index.py` assembles the canonical standards index by blending curated seed rules with optional heuristic extractions from markdown sources. The producer emits a HealthView/HOP-compliant artifact bundle so agents can audit build metadata, extraction diagnostics, and integrity hashes without scraping the YAML directly.

## Invocation

```bash
python .repo_studios/scripts/producers/generate_standards_index.py \
  --repo-root . \
  --output-dir .repo_studios/reports/healthview/producer_reports/standards_index \
  --categories-path .repo_studios/scripts/.repo_studios/standards_categories.yaml \
  --seed-path .repo_studios/scripts/.repo_studios/standards_seed.yaml \
  --index-path .repo_studios/scripts/repo_standards_index.yaml \
  --artifacts-to-keep 10
```

### Key arguments

- `--repo-root` (default repo checkout): base directory used to resolve all relative inputs/outputs.
- `--output-dir` (default `.repo_studios/reports/healthview/producer_reports/standards_index`): HealthView producer bundle root. Created automatically.
- `--categories-path`: YAML mapping of standards categories and markdown sources.
- `--seed-path`: seed rules merged into the index before extraction.
- `--extraction-module` (optional): path to `standards_extraction.py` providing `extract_rules(...)`. When missing, the producer records a diagnostic and continues.
- `--index-path` (default `.repo_studios/scripts/repo_standards_index.yaml`): canonical index output path.
- `--pending-path` (default `.repo_studios/scripts/repo_standards_pending.yaml`): draft queue populated when extraction runs but auto-accept is disabled.
- `--timestamp`: ISO8601 value used for the run slug. When omitted the script captures current UTC.
- `--artifacts-to-keep` (default is policy-driven): retention window applied after each run (minimum of one directory).
- `--log-level` (default `INFO`): Python logging verbosity.

Environment flags:

- `ENABLE_STANDARDS_EXTRACTION=1` enables heuristic extraction for markdown sources listed in the categories file.
- `AUTO_ACCEPT_EXTRACTED=1` inlines extracted rules into the canonical index instead of writing them to the pending queue.

PyYAML must be available in the active Python environment.

## Outputs

Every invocation:

1) Writes/refreshes the canonical index YAML at:

- `.repo_studios/scripts/repo_standards_index.yaml`

2) Emits a HOP-compliant producer bundle under:

- `.repo_studios/reports/healthview/producer_reports/standards_index/<YYYYMMDD-HHMM>/`

Bundle artifacts:

- `manifest.json`
- `summary.md`
- `telemetry.json`

Historical run directories are pruned down to the configured retention window after each execution.
No mutable pointer artifacts (`latest_*`) are written in the HealthView output root.

## Status semantics

- `ok`: build completed, no pending extraction queue was produced.
- `pending_extractions`: extraction ran with auto-accept disabled and emitted rules into the pending queue.
- `error`: build failed (missing inputs, validation errors, malformed extraction output, etc.). Failure details are reflected in `notes` and `log.txt`; canonical index is untouched.

## Testing

`pytest .repo_studios/tests/tests_producers/test_generate_standards_index.py`
verifies structured artifact creation, canonical YAML copies, failure telemetry, and pruning behavior.

## Operational notes

- The producer enforces deterministic hashing over rule fragments so regressions are easy to detect.
- Extraction modules run in a sandbox via `runpy.run_path`; they must expose `extract_rules(path, categories, known_ids, today)`.
- Downstream agents should ingest `telemetry.json` first and consult `.repo_studios/scripts/repo_standards_index.yaml` for rule contents.
- Because failure cases still populate the HealthView bundle, CI can rely on `telemetry.json` + status to detect regressions without parsing stderr.
