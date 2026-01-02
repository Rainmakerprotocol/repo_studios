# DB Integration: Faulthandler Snapshot Utility

## Script Identity

- **Script**: `dump_faulthandler_snapshot.py`
- **Path**: `.repo_studios/scripts/utilities/dump_faulthandler_snapshot.py`
- **Category**: Utility
- **Topic Slug**: `fault_snapshot`
- **Planned Stage**: 3.2

## Purpose

Emits structured faulthandler snapshot bundles. Replaces legacy best-effort stderr dump with structured artifacts for downstream tooling to ingest on-demand stack captures.

## I/O Contract

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FAULT_SNAPSHOT_BASE_DIR` | — | Override base directory |
| `FAULT_SNAPSHOT_OUTDIR` | — | Override output directory |
| `FAULT_OUTDIR` | — | Alternative output override |
| `FAULT_SNAPSHOT_TO_KEEP` | 10 | Retention budget |
| `FAULT_ARTIFACTS_TO_KEEP` | 10 | Alternative retention override |
| `FAULT_LOGS_ALLOW_LEGACY` | 0 | Allow legacy directory structure |

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| MANIFEST.json | `<output_dir>/MANIFEST.json` | Run manifest |
| bundle_summary.json | `<output_dir>/bundle_summary.json` | Bundle metadata |
| Snapshot output | `<output_dir>/` | Raw stack capture |

**Default Base Directory**: `.repo_studios/reports/healthview/rawview_reports/fault_snapshot/`

## Invocation

Safe to invoke multiple times. Maintains retention and records provenance.

```bash
python .repo_studios/scripts/utilities/dump_faulthandler_snapshot.py
```

## Library Integration

- Uses `prune_run_directories` for retention
- Uses `build_topic_path` for HOP-compliant paths

## Dependencies

- Internal: `prune_run_directories`, `build_topic_path`

## Notes

- Utility for on-demand faulthandler stack captures
- Produces structured artifacts for downstream tooling
- Planned for Stage 3.2 (not yet integrated into orchestrator)
