# DB Integration: Monkey Patch Trends Aggregator

## Script Identity

- **Script**: `analyze_monkey_patch_trends.py`
- **Path**: `.repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py`
- **Category**: Aggregator
- **Topic Slug**: `monkey_patch_trends`

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--consumer-base` | CLI | Directory containing consumer bundles |
| `--consumer-summary` | CLI | Explicit consumer summary path override |
| `--producer-base` | CLI | Producer scans directory for fallback |
| `--output-base` | CLI | Output directory override |
| `--artifacts-to-keep` | CLI | Number of trend bundles to retain |
| `--max-runs` | CLI | Maximum runs to include in overview (default: 20) |
| `--log-level` | CLI | Logging verbosity |
| `--verbose` | CLI | Shortcut for --log-level DEBUG |

### Consumer Artifact Location

- **HOP Path**: `.repo_studios/reports/healthview/consumer_reports/monkey_patch_risk/<YYYYMMDD-HHMM>/`
- **Expected files**: `summary.json`, `bundle_summary.json`

### Producer Fallback Location

- **HOP Path**: `.repo_studios/reports/healthview/producer_reports/monkey_patch_scans/<YYYYMMDD-HHMM>/`
- **Expected file**: `manifest.json`

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| trend.json | `<output_base>/<bundle-id>/trend.json` | Trend data JSON |
| trend.md | `<output_base>/<bundle-id>/trend.md` | Trend markdown summary |
| bundle_summary.json | `<output_base>/<bundle-id>/bundle_summary.json` | Bundle metadata |
| TREND_SNAPSHOT.md | Consumer dir | Copied trend snapshot |

**Default Output Directory**: `.repo_studios/reports/healthview/aggregator_reports/monkey_patch_trends/`

## Risk Levels Tracked

- HIGH
- MODERATE
- SAFE

## CLI Arguments

```text
--repo-root PATH         Repository root override
--consumer-base PATH     Consumer bundles directory (default: .repo_studios/reports/consumer_reports/monkey_patch_risk)
--consumer-summary PATH  Explicit consumer summary.json path
--producer-base PATH     Producer scans fallback directory
--output-base PATH       Output directory override
--artifacts-to-keep N    Number of trend bundles to retain
--max-runs N             Maximum runs to blend (default: 20)
--log-level LEVEL        Logging verbosity (default: INFO)
--verbose                Shortcut for --log-level DEBUG
```

## Invocation Pattern

### Standalone

```bash
python .repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py \
  --repo-root . \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_monkey_patch_oversight.py` unless `--skip-aggregator` is passed.

## Dependencies

- Upstream: `classify_monkey_patches.py` (consumer)
- Internal: `monkey_patch_risk.py` utility module

## Notes

- Aggregates consumer risk classification bundles into trend reports
- Part of the Monkey Patch Oversight pipeline (Stage 5.1)
- Provides historical trend data with provenance tracking
