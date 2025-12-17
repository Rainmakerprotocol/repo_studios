---
title: Render Inventory Views Producer
audience: [Copilot, Agents, Developer]
role: [Operational-Doc]
owners: [repo_studios_team@rainmakerprotocol.dev]
status: active
version: 1.0.0
updated: 2025-12-17
tags: [inventory, producer, healthview]
related_files:
  - .repo_studios/scripts/producers/render_inventory_views.py
  - .repo_studios/tests/tests_producers/test_render_inventory_views.py
  - .repo_studios/scripts/producers/check_inventory_health.py
  - .repo_studios/command_center/scripts/libraries/database_integration.py
  - REPORT_NAMING_STANDARDS.md
---

# Render Inventory Views Producer

The `render_inventory_views.py` producer assembles the inventory YAML sources into curated document, script, and test views while exporting them as structured artifacts for downstream automation.

## Invocation

```bash
python .repo_studios/scripts/producers/render_inventory_views.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports \
  --log-level INFO
```

Key flags:

- `--schema-root` — alternative inventory schema path when testing outside the repo root.
- `--views-dir` — directory for legacy compatibility stubs (defaults to `.repo_studios/inventory_schema/views`).
- `--timestamp` — optional ISO8601 seed used to name the run directory.
- `--output-dir` — base directory for positional producer bundles (defaults to `.repo_studios/reports/producer_reports`).

## Outputs

Artifacts land under `.repo_studios/reports/producer_reports/healthview/inventory_overview/<YYYYMMDD-HHMM>/` with the layout:

```text
producer_reports/
  healthview/
    inventory_overview/
      <YYYYMMDD-HHMM>/
        manifest.json
        summary.md
        telemetry.json
```

- `manifest.json` — run metadata (viewer/topic/timestamp/catalog/inputs).
- `summary.md` — human-readable digest of the inventory overview.
- `telemetry.json` — structured metrics and the rendered view payloads (docs/scripts/tests) for agent queries.

After each execution the producer rewrites compatibility stubs under `.repo_studios/inventory_schema/views/` to redirect to the positional topic directory (`reports/producer_reports/healthview/inventory_overview`). The producer keeps only the latest run directory (no `latest_*` pointers).

## Testing

```bash
python -m pytest .repo_studios/tests/tests_producers/test_render_inventory_views.py
```

The test suite validates structured artifact creation, latest pointers, stub regeneration, and pruning behaviour.

Updated behavior: the suite validates canonical bundle creation (manifest/summary/telemetry), stub regeneration, and overwrite pruning (keep=1).
