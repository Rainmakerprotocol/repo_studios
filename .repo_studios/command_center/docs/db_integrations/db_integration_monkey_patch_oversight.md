# DB Integration: Monkey Patch Oversight Orchestrator

## Script Identity

- **Script**: `run_monkey_patch_oversight.py`
- **Path**: `.repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py`
- **Category**: Orchestrator
- **Topic Slug**: `monkey-patch-oversight`
- **HealthView Topic**: `monkey_patch_oversight`
- **Viewer Slug**: `healthview`
- **Schema Version**: 1

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--scan-root` | CLI | Scan root for producer (default: `.`) |
| `--producer-output-dir` | CLI | Producer output directory |
| `--consumer-output-dir` | CLI | Consumer output directory |
| `--aggregator-output-dir` | CLI | Aggregator output directory |
| `--summarizer-output-dir` | CLI | Summarizer output directory |
| `--healthview-root` | CLI | HealthView root directory |
| `--artifacts-to-keep` | CLI | Orchestrator retention budget (default: 3) |
| `--timestamp` | CLI | ISO-8601 timestamp override |
| `--log-level` | CLI | Logging verbosity |

### Skip Flags

| Flag | Description |
|------|-------------|
| `--skip-producer` | Skip scan_monkey_patches.py |
| `--skip-consumer` | Skip classify_monkey_patches.py |
| `--skip-aggregator` | Skip analyze_monkey_patch_trends.py |
| `--skip-summarizer` | Skip summarize_monkey_patch_overview.py |

### Retention Flags (per-step)

| Flag | Default | Description |
|------|---------|-------------|
| `--producer-artifacts-to-keep` | 10 | Producer retention |
| `--consumer-artifacts-to-keep` | 10 | Consumer retention |
| `--aggregator-artifacts-to-keep` | 10 | Aggregator retention |
| `--summarizer-artifacts-to-keep` | 5 | Summarizer retention |

### Producer-Specific Flags

| Flag | Description |
|------|-------------|
| `--producer-context-lines` | Context lines for findings (default: 2) |
| `--producer-with-git` | Enable Git history enrichment |
| `--producer-strict` | Enable strict mode |
| `--producer-project-packages` | Owned project packages |
| `--producer-exclude-dirs` | Directories to exclude |
| `--producer-exclude-globs` | Glob patterns to exclude |

### Other Flags

| Flag | Description |
|------|-------------|
| `--trend-max-runs` | Maximum trend runs to blend (default: 20) |
| `--duplicate-matrix` | Optional duplicate matrix for summarizer |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| manifest.json | `<healthview_root>/<YYYYMMDD-HHMM>/manifest.json` | HOP manifest with pipeline metadata |
| summary.md | `<healthview_root>/<YYYYMMDD-HHMM>/summary.md` | HOP markdown summary |
| telemetry.json | `<healthview_root>/<YYYYMMDD-HHMM>/telemetry.json` | HOP telemetry data |

**Default HealthView Root**: `.repo_studios/reports/healthview/orchestrator_reports/monkey_patch_oversight/`

## Invoked Scripts

| # | Script | Category | Condition |
|---|--------|----------|-----------|
| 1 | `scan_monkey_patches.py` | Producer | Unless `--skip-producer` |
| 2 | `classify_monkey_patches.py` | Consumer | Unless `--skip-consumer` |
| 3 | `analyze_monkey_patch_trends.py` | Aggregator | Unless `--skip-aggregator` |
| 4 | `summarize_monkey_patch_overview.py` | Summarizer | Unless `--skip-summarizer` |

### Utility Dependency

- `monkey_patch_risk.py` — Used by consumer and aggregator for classification

## CLI Arguments

```text
--repo-root PATH                      Repository root override
--scan-root PATH                      Scan root for producer (default: .)
--producer-output-dir PATH            Producer output directory
--consumer-output-dir PATH            Consumer output directory
--aggregator-output-dir PATH          Aggregator output directory
--summarizer-output-dir PATH          Summarizer output directory
--healthview-root PATH                HealthView root directory
--artifacts-to-keep N                 Orchestrator retention (default: 3)
--producer-artifacts-to-keep N        Producer retention (default: 10)
--consumer-artifacts-to-keep N        Consumer retention (default: 10)
--aggregator-artifacts-to-keep N      Aggregator retention (default: 10)
--summarizer-artifacts-to-keep N      Summarizer retention (default: 5)
--trend-max-runs N                    Max trend runs (default: 20)
--producer-context-lines N            Context lines (default: 2)
--producer-with-git                   Enable Git enrichment
--producer-strict                     Enable strict mode
--producer-project-packages PKG...    Project packages
--producer-exclude-dirs DIR...        Exclude directories
--producer-exclude-globs GLOB...      Exclude globs
--duplicate-matrix PATH               Duplicate matrix for summarizer
--skip-producer                       Skip producer step
--skip-consumer                       Skip consumer step
--skip-aggregator                     Skip aggregator step
--skip-summarizer                     Skip summarizer step
--timestamp ISO8601                   Timestamp override
--log-level LEVEL                     Logging verbosity (default: INFO)
```

## Storage Integration

- **Registry**: Uses `CatalogRegistry` for topic context
- **Context**: Uses `TopicContext` and `TopicStep` for structured execution
- **Artifacts**: Uses `write_report_artifacts` for output

## Invocation Pattern

### Full Pipeline

```bash
python .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py \
  --repo-root . \
  --producer-with-git \
  --log-level INFO
```

### Skip Expensive Steps

```bash
python .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py \
  --repo-root . \
  --skip-producer \
  --log-level INFO
```

## Runtime

- **Typical Duration**: 4-7 minutes with Git enrichment enabled
- **Trend scaling**: Scales with configured history window (`--trend-max-runs`)

## Dependencies

- External: Git (optional, for producer enrichment)
- Internal: `CatalogRegistry`, `TopicContext`, `TopicStep`, `write_report_artifacts`

## Notes

- Primary orchestrator for Monkey Patch Oversight (Stage 5.1)
- Replaces monkey patch stages from legacy `orchestrate_health_suite.py`
- Coordinates producer → consumer → aggregator → summarizer flow
- Emits HealthView bundles with manifest, summary, and telemetry
