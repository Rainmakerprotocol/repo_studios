# DB Integration: Inventory Validator

## Script Identity

- **Script**: `validate_inventory.py`
- **Path**: `.repo_studios/scripts/producers/validate_inventory.py`
- **Category**: Producer
- **Topic Slug**: `validate_inventory`
- **Schema Version**: 1
- **Status**: Active (Stage 11.1 orchestrator integration complete)

## I/O Contract

### Inputs

| Input | Source | Description |
|-------|--------|-------------|
| `--repo-root` | CLI | Repository root override |
| `--schema-root` | CLI | Schema root directory |
| `--enums-path` | CLI | Enums YAML path |
| `--template-path` | CLI | Template YAML path |
| `--config-path` | CLI | Validator config path |
| `--output-dir` | CLI | Output directory override |
| `--artifacts-to-keep` | CLI | Retention budget |
| `--log-level` | CLI | Logging verbosity |

### Default Paths

| Path | Description |
|------|-------------|
| `.repo_studios/inventory_schema/` | Default schema root |
| `.repo_studios/inventory_schema/enums.yaml` | Default enums path |
| `.repo_studios/inventory_schema/inventory_entry_template.yaml` | Default template |
| `.repo_studios/inventory_schema/validator_config.yaml` | Default config |

### Required Entry Fields

- `id`, `name`, `path`, `asset_kind`, `roles`, `maturity`
- `description`, `consumers`, `status`, `artifact_type`

### List Fields

- `roles`, `consumers`, `governance_flags`, `related_assets`, `tags`

### Outputs

| Output | Path Pattern | Description |
|--------|--------------|-------------|
| Bundle artifacts | `<output_dir>/<run-prefix>-<timestamp>/` | Validation results |

**Default Output Directory**: `.repo_studios/reports/producer_reports/healthview/validate_inventory/`

## Storage Integration

- Uses `build_topic_path("producer", TOPIC_SLUG)` for default output path
- Uses `prune_history()` for retention (not `prune_run_directories`)
- **Does NOT use `create_storage()`** — uses direct file writes via `write_run_artifacts()`
- **No `latest_*` pointers** — HOP-compliant

> **DB Integration Status:** This script does NOT currently have `DB_INTEGRATION_MARKER`
> tags. To enable dual-write support, markers would need to be added at the artifact
> write locations in `write_run_artifacts()` (lines 515-549).

## ValidationIssue Dataclass

```python
@dataclass
class ValidationIssue:
    level: str      # Error level
    file: Path      # File with issue
    message: str    # Issue description
    context: dict   # Additional context
```

## Dependencies

- External: pyyaml
- Internal: `build_topic_path`, `prune_run_directories`, `copy_latest_artifact`

## Notes

- Validates Repo Studios inventory entries against schema
- Emits structured validation artifacts (HOP base package + raw.json)
- Orchestrator integration: Stage 11.1 `run_available_scripts_oversight.py`
- Phase 4 compliance: Complete (2026-01-28)

## Update Log

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-28 | Agent | Fixed status (was "Questionable"), corrected storage integration section, noted missing DB markers |
