# Inventory Reports Overview

Last updated: 2025-12-10

The `render_inventory_views.py` pipeline emits a canonical inventory overview bundle under `.repo_studios/reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/`. Downstream automation (including inventory health checks) consumes the latest run in that directory.

## Running the Renderer

From the repository root:

```bash
python .repo_studios/scripts/producers/render_inventory_views.py
```

The command regenerates all reports and refreshes the compatibility stubs in `inventory_schema/views/`.

## Report Layout


The canonical bundle contains exactly:

- `reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/manifest.json`
- `reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/summary.md`
- `reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/telemetry.json`

The `inventory_schema/views/` files are compatibility stubs that redirect readers to the producer report topic directory.

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

Downstream consumers should treat the topic directory as the stable entry point and select the newest run folder at runtime.
