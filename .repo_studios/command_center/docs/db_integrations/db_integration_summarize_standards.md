# DB Integration: Standards Summarizer

## Script Identity

- **Script**: `summarize_standards.py`
- **Path**: `.repo_studios/scripts/summarizers/summarize_standards.py`
- **Category**: Summarizer
- **Viewer Slug**: `healthview`
- **Topic Slug**: `standards_overview`
- **Schema Version**: 1

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--index-path` | CLI | Path to standards index YAML |
| `--pending-path` | CLI | Path to pending rules YAML |
| `--output-dir` | CLI | Output directory for artifacts |
| `--label` | CLI | Label used in emitted metadata (default: summary) |
| `--timestamp` | CLI | ISO-8601 timestamp override |
| `--artifacts-to-keep` | CLI | Retention budget |
| `--log-level` | CLI | Logging verbosity |
| `INDEX_PATH` | ENV | Environment variable for index path |
| `PENDING_PATH` | ENV | Environment variable for pending path |

### Default Input Paths

| Source | Default Path |
|--------|--------------|
| Index | `.repo_studios/scripts/repo_standards_index.yaml` |
| Pending | `.repo_studios/scripts/repo_standards_pending.yaml` |
| Legacy Index | `.repo_studios/reports/producer_reports/standards_index_reports/latest_index.yaml` |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| HealthView bundle | `<output_dir>/<YYYYMMDD-HHMM>/` | Manifest, summary, telemetry |

**Default Output Directory**: `.repo_studios/reports/healthview/summarizer_reports/standards_overview/`

**Base Package Artifacts**:

- `manifest.json` — Structured summary with metrics, samples, and artifact paths
- `summary.md` — Human-readable markdown summary with metrics table and notes
- `telemetry.json` — Telemetry payload with schema version, metrics, and run timestamp

## CLI Arguments

```text
--repo-root PATH         Repository root override
--index-path PATH        Path to standards index YAML
--pending-path PATH      Path to pending rules YAML
--output-dir PATH        Output directory for artifacts
--label LABEL            Label for metadata (default: summary)
--timestamp ISO8601      Timestamp override
--artifacts-to-keep N    Retention budget
--log-level LEVEL        Logging verbosity (default: INFO)
```

## Storage Integration

- **Library**: Uses `write_report_artifacts` for output
- **Registry**: Uses standard PathsConfig and OptionsConfig

## Invocation Pattern

### Standalone

```bash
python .repo_studios/scripts/summarizers/summarize_standards.py \
  --repo-root . \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_standards_integrity.py` as the final summarization step.

## Dependencies

- External: pyyaml
- Internal: `write_report_artifacts`, `build_topic_path`

## Notes

- Generates HealthView-ready summary of the standards index
- Reads both active index and pending rules
- Part of the Standards Integrity pipeline (Stage 6.1)
