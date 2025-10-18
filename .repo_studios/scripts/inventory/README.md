# Inventory Automation Scripts

This folder groups the active inventory management utilities that already live in the refreshed layout.

## Current Modules

- `check_inventory_health.py` – validates inventory schemas and reports mismatches.
- `render_inventory_views.py` – produces YAML/Markdown views for quick review.
- `validate_inventory.py` – lightweight schema checks that run inside commit hooks or CI.

## Migration Notes

- Retain these filenames; they already align with the new naming convention.
- When new inventory helpers arrive, document their role and downstream dependencies here.
- Inventory scripts should remain lean—prefer referencing shared utilities (e.g., upcoming `prune_logs`) instead of duplicating helpers.
