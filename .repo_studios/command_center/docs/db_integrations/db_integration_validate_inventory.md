# DB Integration: Inventory Validator

## Script Identity

- **Script**: `validate_inventory.py`
- **Path**: `.repo_studios/scripts/producers/validate_inventory.py`
- **Category**: Producer
- **Topic Slug**: `validate_inventory`
- **Schema Version**: 1
- **Status**: Questionable (may be deprecated)

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

- Uses standard PathsConfig and OptionsConfig
- Uses `prune_run_directories` for retention
- Uses `copy_latest_artifact` for convenience pointers

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
- Emits structured validation artifacts
- Status: Questionable — may overlap with other validation scripts
