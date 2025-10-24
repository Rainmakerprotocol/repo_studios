# Script Inventory Template

Last updated: 2025-10-21

Use this template when documenting script migrations into `.repo_studios/scripts/`. It mirrors the structure in `scripts/script_inventory_architecture.md` so alignment notes and inventory YAML stay synchronized.

## Instructions

1. Copy the sections below into a working document (or directly into the script inventory architecture file) before cataloging a new batch of scripts.
2. Update the metadata block so agents know the status, owner, and last review.
3. For each script, fill in the table fields. Leave `TODO` markers where follow-up work is needed.
4. Record category-level next actions to keep migration tasks visible.
5. When ready to publish machine-readable data, convert completed tables to YAML using the provided key names.

## Document Metadata Block

```markdown
- **Status:** Draft
- **Owner:** repo_studios_ai
- **Last Updated:** YYYY-MM-DD
- **Scope:** .repo_studios/scripts/
```

## Per-Script Table Skeleton

```markdown
| Script Path | Legacy Name | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |
```

## Next Actions List

```markdown
- TODO: <Follow-up task>
- TODO: <Follow-up task>
```

## YAML Conversion Example

Use this structure when exporting table rows into the inventory catalogs.

```yaml
- script_path: .repo_studios/scripts/<category>/example.py
  legacy_name: .repo_studios_legacy/repo_scripts/example.py
  description: Baseline metrics collector.
  needed: true
  wired: make studio-example
  dependencies:
    internal_paths: []
    external_tools: []
  testing_coverage: tests/<category>/test_example.py
  entry_points:
    - manual
  migration_target: scripts/<category>/example.py
  conformance_review: std-global-python-engineering.md
  duplicates: []
  notes: Pending prune_logs helper.
```

Adapt the category headings (collectors, processors, etc.) as needed, but keep the field names stable so automated tooling can parse the exported YAML later.
