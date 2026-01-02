# DB Integration: Mypy Baselines Utility

## Script Identity

- **Script**: `refresh_mypy_baselines.py`
- **Path**: `.repo_studios/scripts/utilities/refresh_mypy_baselines.py`
- **Category**: Utility
- **Run Stem**: `mypy_baselines`

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--target` | CLI | Targets relative to repo root (repeatable) |
| `--output-dir` | CLI | Output directory override |
| `--artifacts-to-keep` | CLI | Number of timestamped runs to retain (default: 5) |
| `--log-level` | CLI | Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Default Targets

- `agents`
- `agents/core/monitoring`

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| Baseline files | `<output_dir>/<timestamp>/` | Refreshed mypy baseline artifacts |

**Default Output Directory**: `.repo_studios/command_center/reports/rawview/mypy_baselines/`

## CLI Arguments

```text
--repo-root PATH         Repository root override
--target PATH            Target paths relative to repo root (repeatable)
--output-dir PATH        Output directory override
--artifacts-to-keep N    Number of timestamped runs to retain (default: 5)
--log-level LEVEL        Logging verbosity (default: INFO)
```

## Storage Integration

- **Library**: Uses `write_report_artifacts` for output
- **View**: RawView (not HealthView)
- **Retention Strategy**: Timestamp-slug pruning

## Invocation Pattern

### Standalone

```bash
python .repo_studios/scripts/utilities/refresh_mypy_baselines.py \
  --repo-root . \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_dependency_import_hygiene.py` when `--refresh-mypy-baselines` flag is passed.

## Dependencies

- External: mypy
- Internal: `write_report_artifacts` library

## Notes

- Utility script for refreshing mypy baseline files
- Outputs to RawView (not HealthView) as supporting infrastructure
- Optional step in the Dependency & Import Hygiene pipeline (Stage 4.1)
- Only runs when explicitly requested via orchestrator flag
