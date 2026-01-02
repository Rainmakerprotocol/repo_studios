# DB Integration: Typecheck Report Producer

## Script Identity

- **Script**: `generate_typecheck_report.py`
- **Path**: `.repo_studios/scripts/producers/generate_typecheck_report.py`
- **Category**: Producer
- **Topic Slug**: `typecheck_report`

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--target` | CLI | Scan target relative to repo root (default: `.repo_studios`) |
| `--output-dir` | CLI | Output directory override |
| `--artifacts-to-keep` | CLI | Number of timestamped runs to retain (default: 10) |
| `--log-level` | CLI | Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--timestamp` | CLI | ISO8601 timestamp override |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| manifest.json | `<output_dir>/<YYYYMMDD-HHMM>/manifest.json` | Run manifest with metadata |
| summary.md | `<output_dir>/<YYYYMMDD-HHMM>/summary.md` | Markdown summary |
| telemetry.json | `<output_dir>/<YYYYMMDD-HHMM>/telemetry.json` | Execution telemetry |
| mypy_raw.txt | `<output_dir>/<YYYYMMDD-HHMM>/mypy_raw.txt` | Raw mypy output |

**Default Output Directory**: `.repo_studios/reports/producer_reports/healthview/typecheck_report/`

## CLI Arguments

```text
--repo-root PATH         Repository root override
--target PATH            Scan target relative to repo root (default: .repo_studios)
--output-dir PATH        Output directory override
--artifacts-to-keep N    Number of timestamped runs to retain (default: 10)
--log-level LEVEL        Logging verbosity (default: INFO)
--timestamp ISO8601      Timestamp override for run directory
```

## Storage Integration

- **Database Integration**: Uses `database_integration.create_storage()` for dual-write capability
- **Retention Strategy**: Timestamp-slug pruning via `artifacts_to_keep`

## Invocation Pattern

### Standalone

```bash
python .repo_studios/scripts/producers/generate_typecheck_report.py \
  --repo-root . \
  --target .repo_studios \
  --log-level INFO
```

### From Orchestrator

Invoked by `run_dependency_import_hygiene.py` unless `--skip-typecheck` is passed.

## Dependencies

- External: mypy
- Internal: `database_integration` module, `write_report_artifacts` library

## Notes

- Runs mypy type-checking and emits structured artifacts
- Part of the Dependency & Import Hygiene pipeline (Stage 4.1)
- Contributes to HealthView catalog via database storage markers
