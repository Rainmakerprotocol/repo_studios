# Inventory Reports Overview

Last updated: 2025-12-10

The `render_inventory_views.py` pipeline now emits machine-readable snapshots of the Repo Studios inventory into `.repo_studios/reports/producer_reports/render_inventory_views/` alongside `latest_*.json|yaml` pointers. Healthview mirrors consume the same payloads, so producer reports are the canonical source for downstream automation.

## Running the Renderer

From the repository root:

```bash
python .repo_studios/scripts/producers/render_inventory_views.py
```

The command regenerates all reports and refreshes the compatibility stubs in `inventory_schema/views/`.

## Report Layout

- `reports/producer_reports/render_inventory_views/latest_docs_overview.yaml`
  - Contains documents (`asset_kind == "document"`) with `id`, `name`, `path`, `maturity`, `status`, `consumers`, `tags`, and `artifact_type`.
- `reports/producer_reports/render_inventory_views/latest_scripts_overview.yaml`
  - Lists script assets including their `roles`, `related_assets`, and filesystem `path` for orchestration hooks.
- `reports/producer_reports/render_inventory_views/latest_tests_overview.yaml`
  - Enumerates test orchestration entries with `related_assets` and `artifact_type` for coverage dashboards.
- `reports/producer_reports/render_inventory_views/latest_summary.json`
  - Aggregated totals by asset kind, maturity, status, consumer, plus derived metrics such as `status_by_asset_kind`, `maturity_by_asset_kind`, and ranked `top_tags`.
- `reports/producer_reports/render_inventory_views/latest_dashboard.json`
  - Metrics snapshot intended for future dashboards or health summaries (no UI is bundled with this starter repo).

Each run produces timestamped directories (for example `render_inventory_views-YYYYMMDD_HHMMSS`) plus refreshed `latest_*` pointers in the producer reports folder so historical archives remain accessible without changing downstream integration points.

## CI Consumption Patterns

1. **Inventory Health Gates**
   - Validate `summary.json` for unexpected regressions (e.g., new `unknown` status counts) before deploying automation changes.
2. **Scoped Documentation Checks**
   - Use `docs_overview.yaml` to determine which document paths require linting or anchor validation.
3. **Script Dependency Graphs**
   - Build dependency charts from `scripts_overview.yaml` where `related_assets` link to supporting tooling.
4. **Test Matrix Generation**
   - Map `tests_overview.yaml` entries to orchestrator targets for selective CI execution.
5. **Dashboard Feeds**
   - Supply `dashboard.json` to visualization tooling to track maturity progress, role coverage, or artifact growth over time.

Downstream consumers should treat the `latest/` directory as ephemeral: always read the current artifacts at runtime rather than caching paths with timestamps.
