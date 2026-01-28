# DB Integration: Import Boundaries Validator

## Script Identity

- **Script**: `validate_import_boundaries.py`
- **Path**: `.repo_studios/scripts/producers/validate_import_boundaries.py`
- **Category**: Producer
- **Topic Slug**: `import_boundary`
- **Schema Version**: 1
- **Status**: Active (Stage 11.1 orchestrator integration complete)

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

- Uses `build_topic_path("producer", TOPIC_SLUG)` for default output path
- Uses `prune_run_directories()` for retention
- **Does NOT use `create_storage()`** — uses direct file writes
- **No `latest_*` pointers** — HOP-compliant
- **DB_INTEGRATION_MARKER tags present** at L442, L446, L464

## DB Integration Markers

| Line | Marker | Artifact |
|------|--------|----------|
| L442 | `DB_INTEGRATION_MARKER: import boundary manifest write` | manifest.json |
| L446 | `DB_INTEGRATION_MARKER: import boundary summary markdown write` | summary.md |
| L464 | `DB_INTEGRATION_MARKER: import boundary telemetry write` | telemetry.json |

## Dependencies

- Upstream: `generate_import_graph_report.py` (producer)
- Internal: `build_topic_path`, `prune_run_directories`

## Notes

- Structured import boundary checker with artifact emission
- Validates imports against allowlist rules
- Detects cycles, forbidden edges, and static import violations
- Orchestrator integration: Stage 11.1 `run_available_scripts_oversight.py`
- Phase 4 compliance: Complete (2026-01-28)

## Update Log

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-28 | Agent | Updated status to Active, added DB marker locations, corrected storage integration section |
