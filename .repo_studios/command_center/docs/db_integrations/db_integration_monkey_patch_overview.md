# DB Integration: Monkey Patch Overview Summarizer

## Script Identity

- **Script**: `summarize_monkey_patch_overview.py`
- **Path**: `.repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py`
- **Category**: Summarizer
- **Viewer Slug**: `healthview`
- **Topic Slug**: `monkey_patch_overview`
- **Schema Version**: 1

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--consumer-output-dir` | CLI | Consumer reports directory |
| `--producer-output-dir` | CLI | Producer reports directory |
| `--aggregator-output-dir` | CLI | Aggregator reports directory |
| `--output-dir` | CLI | Output directory override |
| `--consumer-summary` | CLI | Explicit consumer summary.json override |
| `--consumer-bundle-summary` | CLI | Explicit consumer bundle_summary.json override |
| `--trend-json` | CLI | Explicit aggregator trend.json override |
| `--trend-markdown` | CLI | Explicit aggregator trend markdown override |
| `--trend-bundle-summary` | CLI | Explicit aggregator bundle_summary.json override |
| `--producer-report` | CLI | Explicit producer report.json override |
| `--producer-matches` | CLI | Explicit producer matches.json override |
| `--duplicate-matrix` | CLI | Optional duplicate detection matrix |
| `--artifacts-to-keep` | CLI | Retention budget (default: 5) |
| `--timestamp` | CLI | ISO-8601 timestamp override |
| `--log-level` | CLI | Logging verbosity |

### Default Input Directories

| Source | Default Path |
|--------|--------------|
| Consumer | `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/` |
| Producer | `.repo_studios/reports/healthview/producer_reports/monkey_patch_scans/` |
| Aggregator | `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/` |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| manifest.json | `<output_dir>/<YYYYMMDD-HHMM>/manifest.json` | HealthView JSON manifest |
| summary.md | `<output_dir>/<YYYYMMDD-HHMM>/summary.md` | HealthView markdown summary |

**Default Output Directory**: `.repo_studios/reports/healthview/summarizer_reports/monkey_patch_overview/`

## CLI Arguments

```text
--repo-root PATH                 Repository root override
--consumer-output-dir PATH       Consumer reports directory
--producer-output-dir PATH       Producer reports directory
--aggregator-output-dir PATH     Aggregator reports directory
--output-dir PATH                Output directory override
--consumer-summary PATH          Explicit consumer summary.json
--consumer-bundle-summary PATH   Explicit consumer bundle_summary.json
--trend-json PATH                Explicit aggregator trend.json
--trend-markdown PATH            Explicit aggregator trend markdown
--trend-bundle-summary PATH      Explicit aggregator bundle_summary.json
--producer-report PATH           Explicit producer report.json
--producer-matches PATH          Explicit producer matches.json
--duplicate-matrix PATH          Optional duplicate matrix
--artifacts-to-keep N            Retention budget (default: 5)
--timestamp ISO8601              Timestamp override
--log-level LEVEL                Logging verbosity (default: INFO)
```

## Storage Integration

- **Library**: Uses `write_report_artifacts` for output
- **Registry**: Uses standard PathsConfig and OptionsConfig

## Invocation Pattern

### Standalone

```bash
python .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py \
  --repo-root . \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_monkey_patch_oversight.py` unless `--skip-summarizer` is passed.

## Dependencies

- Upstream: Consumer, Producer, and Aggregator artifacts
- Internal: `write_report_artifacts` library

## Notes

- Summarizer that generates HealthView-ready overview artifacts
- Blends consumer, producer, and aggregator outputs
- Part of the Monkey Patch Oversight pipeline (Stage 5.1)
