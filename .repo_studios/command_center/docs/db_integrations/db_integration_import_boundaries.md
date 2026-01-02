# DB Integration: Import Boundaries Validator

## Script Identity

- **Script**: `validate_import_boundaries.py`
- **Path**: `.repo_studios/scripts/producers/validate_import_boundaries.py`
- **Category**: Producer
- **Topic Slug**: `import_boundary`
- **Schema Version**: 1
- **Planned Stage**: 4.2

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--output-dir` | CLI | Output directory override |
| `--allowlist-path` | CLI | Import rules allowlist file |
| `--graph-dir` | CLI | Import graph directory |
| `--graph-path` | CLI | Explicit graph file path |
| `--strict` | CLI | Enable strict mode |
| `--artifacts-to-keep` | CLI | Retention budget |
| `--log-level` | CLI | Logging verbosity |

### Default Paths

| Path | Description |
|------|-------------|
| `.repo_studios/scripts/producers/import_rules_allowlist.json` | Default allowlist |
| `.repo_studios/reports/producer_reports/healthview/import_graph/` | Default graph directory |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| Bundle artifacts | `<output_dir>/<run-prefix>-<timestamp>/` | Validation results |

**Default Output Directory**: `.repo_studios/reports/producer_reports/healthview/import_boundary/`

## CLI Arguments

```text
--repo-root PATH         Repository root override
--output-dir PATH        Output directory override
--allowlist-path PATH    Import rules allowlist
--graph-dir PATH         Import graph directory
--graph-path PATH        Explicit graph file
--strict                 Enable strict mode
--artifacts-to-keep N    Retention budget
--log-level LEVEL        Logging verbosity
```

## Storage Integration

- Uses standard PathsConfig and OptionsConfig
- Uses `prune_run_directories` for retention

## Dependencies

- Upstream: `generate_import_graph_report.py` (producer)
- Internal: `build_topic_path`, `prune_run_directories`

## Notes

- Structured import boundary checker with artifact emission
- Validates imports against allowlist rules
- Planned for Stage 4.2 (not yet integrated into orchestrator)
