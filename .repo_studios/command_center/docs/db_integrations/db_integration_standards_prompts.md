# DB Integration: Standards Prompt Seeds Producer

## Script Identity

- **Script**: `seed_standards_prompts.py`
- **Path**: `.repo_studios/scripts/producers/seed_standards_prompts.py`
- **Category**: Producer
- **Topic Slug**: `standards_prompt_seeds`
- **Schema Version**: 1

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--index-path` | CLI | Path to repo_standards_index.yaml |
| `--output-dir` | CLI | Directory for structured artifacts |
| `--include-warn` | CLI | Include warn severity rules |
| `--artifact-formats` | CLI | Formats to materialize (text, yaml, json) |
| `--format` | CLI | Legacy output format for stdout |
| `--out` | CLI | Write legacy format to file instead of stdout |
| `--artifacts-to-keep` | CLI | Number of run directories to retain |
| `--log-level` | CLI | Logging verbosity |

### Default Index Locations

- **Primary**: `.repo_studios/scripts/repo_standards_index.yaml`

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| Bundle artifacts | `<output_dir>/<YYYYMMDD-HHMM>/` | Prompt seed bundle |

**Default Output Directory**: `.repo_studios/reports/healthview/producer_reports/standards_prompt_seeds/`

**Base Package Artifacts**:

- `manifest.json` — Run metadata including status, timestamp, summary, and seed integrity hash
- `summary.md` — Human-readable report with severity counts and category breakdown
- `telemetry.json` — Structured telemetry for automation consumption
- `seed.txt` / `seed.yaml` / `seed.json` — Prompt seed in requested formats

## CLI Arguments

```text
--repo-root PATH              Repository root override
--index-path PATH             Path to standards index YAML
--output-dir PATH             Output directory for artifacts
--include-warn                Include warn severity rules
--artifact-formats FMT...     Formats to materialize (text, yaml, json)
--format FMT                  Legacy output format (text, yaml, json)
--out PATH                    Write legacy format to file
--artifacts-to-keep N         Retention budget
--log-level LEVEL             Logging verbosity (default: INFO)
```

## Storage Integration

- **Library**: Uses standard PathsConfig and OptionsConfig
- **Pruning**: Uses `prune_run_directories` for retention

## Invocation Pattern

### Standalone

```bash
python .repo_studios/scripts/producers/seed_standards_prompts.py \
  --repo-root . \
  --artifact-formats text yaml json \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_standards_integrity.py` as part of the standards pipeline.

## Dependencies

- External: pyyaml
- Internal: `build_topic_path`, `prune_run_directories`

## Notes

- Generates structured prompt seed bundles from the standards index
- Supports multiple output formats (text, yaml, json)
- Part of the Standards Integrity pipeline (Stage 6.1)
