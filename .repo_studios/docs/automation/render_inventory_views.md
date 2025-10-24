# Render Inventory Views Producer

The `render_inventory_views.py` producer assembles the inventory YAML sources into curated document, script, and test views while exporting them as structured artifacts for downstream automation.

## Invocation

```bash
python .repo_studios/scripts/producers/render_inventory_views.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/render_inventory_views \
  --log-level INFO
```

Key flags:

- `--schema-root` — alternative inventory schema path when testing outside the repo root.
- `--views-dir` — directory for legacy compatibility stubs (defaults to `.repo_studios/inventory_schema/views`).
- `--timestamp` — optional ISO8601 seed used to name the run directory.
- `--artifacts-to-keep` — number of historical structured runs to retain (default 10).

## Outputs

Artifacts land in `.repo_studios/reports/producer_reports/render_inventory_views/` with the layout:

```text
render_inventory_views/
  render_inventory_views-<timestamp>/
    report.json
    report.md
    log.txt
    raw.json
  latest_report.json
  latest_report.md
  latest_report.log
  latest_raw.json
```

- `report.json` — summary payload capturing counts, leading tags/consumers, and input parameters.
- `report.md` — human-readable overview of the same metrics.
- `log.txt` — single-line key/value output for quick ingestion.
- `raw.json` — full set of rendered views plus the summary/dashboard data.

After each execution the producer refreshes the topic-specific `reports/<topic>/latest/` directories and rewrites compatibility stubs under `.repo_studios/inventory_schema/views/` so legacy consumers still function. Historical run directories are pruned according to `--artifacts-to-keep`.

## Testing

```bash
python -m pytest .repo_studios/tests/tests_producers/test_render_inventory_views.py
```

The test suite validates structured artifact creation, latest pointers, stub regeneration, and pruning behaviour.
