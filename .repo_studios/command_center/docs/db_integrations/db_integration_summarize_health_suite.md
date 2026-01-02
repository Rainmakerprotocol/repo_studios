# DB Integration: Health Suite Summarizer

## Script Identity

- **Script**: `summarize_health_suite.py`
- **Path**: `.repo_studios/scripts/summarizers/summarize_health_suite.py`
- **Category**: Summarizer
- **Viewer Slug**: `healthview`
- **Topic Slug**: `health_suite_overview`
- **Schema Version**: 1
- **Status**: Legacy candidate (superseded by topic orchestrators)

## Purpose

Composes a compact summary markdown from multiple producer/aggregator outputs:
- Repo Insight trends (monkey patch trend preview)
- Dependency Hygiene (summary)
- Import Graph (hotspots + cycles)
- Test Log Health (pytest warnings/exceptions + slowest tests)
- Churn × Complexity Heatmap (top risk items)

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--output-dir` | CLI | Output directory override |
| `--legacy-dir` | CLI | Legacy mirror directory |
| `--timestamp` | CLI | ISO-8601 timestamp override |
| `--artifacts-to-keep` | CLI | Retention budget |
| `--mirror-legacy` | CLI | Mirror to legacy directory |
| `--log-level` | CLI | Logging verbosity |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| HealthView bundle | `<output_dir>/<timestamp>/` | Manifest, summary, telemetry |
| Legacy mirror | `<legacy_dir>/health_suite_<timestamp>.md` | Optional legacy copy |

**Default Output Directory**: `.repo_studios/command_center/reports/`
**Default Legacy Directory**: `.repo_studios/health_suite/`

## CLI Arguments

```text
--repo-root PATH         Repository root override
--output-dir PATH        HealthView output directory
--legacy-dir PATH        Legacy mirror directory
--timestamp ISO8601      Timestamp override
--artifacts-to-keep N    Retention budget
--mirror-legacy          Enable legacy mirroring
--log-level LEVEL        Logging verbosity
```

## Storage Integration

- Uses `write_report_artifacts` for output
- Uses standard PathsConfig and OptionsConfig

## Dependencies

- Internal: `write_report_artifacts`, `build_standard_paths`, `build_standard_options`

## Notes

- Legacy summarizer that aggregates multiple producer outputs
- Status: Legacy candidate — functionality now covered by individual topic orchestrators
- May be deprecated in favor of `orchestrate_full_diagnostic.py`
