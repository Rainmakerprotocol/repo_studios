# Inventory Validation Guide

Last updated: 2025-10-17

Use the inventory validator to ensure every catalog entry in `.repo_studios/inventory_schema/` conforms to the schema specification and enum definitions.

## Running the Validator

From the repository root:

```bash
make -C .repo_studios studio-validate-inventory
```

This command executes `scripts/validate_inventory.py` using the active Python interpreter (override with `PYTHON=/path/to/python`).

### JSON Output

To produce a machine-readable report, pass `--json` directly to the script:

```bash
python3 .repo_studios/scripts/validate_inventory.py --json
```

The JSON payload mirrors the structure:

```json
{
  "issues": [
    {
      "level": "error",
      "file": "inventory_schema/scripts/health_reports.yaml",
      "message": "Value 'foo' is not allowed for enum 'roles'",
      "context": {
        "record_id": "scripts.health.foo",
        "enum": "roles"
      }
    }
  ]
}
```

Errors cause a non-zero exit status. Warnings are reported but do not fail the run yet.

## Validation Coverage

The validator currently enforces:

- Presence of required fields (`id`, `name`, `path`, `asset_kind`, `roles`, `maturity`, `description`, `consumers`, `status`, `artifact_type`).
- List typing for `roles`, `consumers`, `governance_flags`, `related_assets`, and `tags`.
- Enum membership for `asset_kind`, `roles`, `maturity`, `consumers`, and `status` using `inventory_schema/enums.yaml`.
- Structure of the `dependencies` block, ensuring lists for `internal_paths`, `external_tools`, and `inputs`, plus a `path` key for each input mapping.
- Unique `id` values across all catalogs.
- Automatic exclusion of derived views under `inventory_schema/views/` so generated summaries do not trigger schema errors during migration.

## Roadmap

- Add configurable suppression for legacy paths that are intentionally missing until migration completes.
- Extend checks to verify file existence once migration stabilizes.
- Surface validation results inside future CI pipelines and dashboards.
