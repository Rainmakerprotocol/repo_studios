# Inventory Reports Overview

Last updated: 2025-10-18

The `render_inventory_views.py` pipeline emits machine-readable snapshots of the Repo Studios inventory into `.repo_studios/reports/<topic>/latest/`. These artifacts provide CI pipelines and dashboards with a stable contract for consuming catalog data without touching the source YAML directly.

## Running the Renderer

From the repository root:

```bash
python3 .repo_studios/scripts/render_inventory_views.py
```

The command regenerates all reports and refreshes the compatibility stubs in `inventory_schema/views/`.

## Report Layout

- `reports/docs/latest/docs_overview.yaml`
  - Contains documents (`asset_kind == "document"`) with `id`, `name`, `path`, `maturity`, `status`, `consumers`, `tags`, and `artifact_type`.
- `reports/scripts/latest/scripts_overview.yaml`
  - Lists script assets including their `roles`, `related_assets`, and filesystem `path` for orchestration hooks.
- `reports/tests/latest/tests_overview.yaml`
  - Enumerates test orchestration entries with `related_assets` and `artifact_type` for coverage dashboards.
- `reports/summary/latest/summary.json`
  - Aggregated totals by asset kind, maturity, status, consumer, plus derived metrics such as `status_by_asset_kind`, `maturity_by_asset_kind`, and ranked `top_tags`.
- `reports/summary/latest/dashboard.json`
  - CI-focused snapshot highlighting maturity totals per asset kind, role prevalence, and artifact type distribution.

Each topic folder always exposes its most recent snapshot under `latest/`; historical archives can be introduced later without changing downstream integration points.

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
