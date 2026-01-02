# DB Integration: Faulthandler Runtime Configuration

## Script Identity

- **Script**: `configure_faulthandler_runtime.py`
- **Path**: `.repo_studios/scripts/utilities/configure_faulthandler_runtime.py`
- **Category**: Utility (bootstrap/runtime)
- **Topic Slug**: `fault_diagnostics`
- **Planned Stage**: 3.2

## Purpose

Faulthandler bootstrap and runtime configuration helpers. Keeps historical sitecustomize side effects but routes faulthandler setup through testable helpers for safe retention, manifests, and import-time behaviour testing.

## I/O Contract

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITHUB_ACTIONS` | Detect CI environment |
| `CI` | Detect CI environment |

### Configuration

| Setting | Description |
|---------|-------------|
| `enable` | Enable faulthandler |
| `dump_later` | Defer dumps |
| `tee_stderr` | Tee to stderr |
| `min_interval` | Minimum dump interval |
| `dump_timeout` | Dump timeout |
| `max_dumps_per_run` | Maximum dumps per run |
| `redact_paths` | Redact sensitive paths |
| `artifacts_to_keep` | Retention budget |
| `outdir` | Output directory |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| Faulthandler logs | `<base_dir>/<timestamp>/` | Stack traces and diagnostics |

**Default Base Directory**: `.repo_studios/reports/healthview/rawview_reports/fault_diagnostics/`

## Library Integration

- Uses `prune_run_directories` for retention
- Uses `build_topic_path` for HOP-compliant paths

## Warning Filters

Reduces noise from known non-actionable warnings:
- `ResourceWarning` for unclosed sqlite3 connections
- `DeprecationWarning` for class-based config

## Dependencies

- Internal: `prune_run_directories`, `build_topic_path`

## Notes

- Utility module imported by repository sitecustomize shim
- Provides testable helpers for faulthandler configuration
- Planned for Stage 3.2 (not yet integrated into orchestrator)
