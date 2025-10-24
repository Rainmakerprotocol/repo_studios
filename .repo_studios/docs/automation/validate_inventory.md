# Validate Inventory Producer

The `validate_inventory.py` producer walks the inventory catalog, enforces schema conventions, and writes structured validation bundles for downstream tooling.

## Invocation

```bash
python .repo_studios/scripts/producers/validate_inventory.py \
  --repo-root . \
  --output-dir .repo_studios/reports/producer_reports/validate_inventory \
  --log-level INFO
```

Notable flags:

- `--schema-root` — alternate inventory schema directory (defaults to `.repo_studios/inventory_schema`).
- `--enums-path` — explicit enums YAML path when testing in isolation.
- `--timestamp` — optional ISO8601 moment to seed the run directory name.
- `--artifacts-to-keep` — number of historical structured runs to retain (default 10).
- `--json` — emits the legacy JSON issue list to stdout, useful for quick triage.

## Outputs

Artifacts live under `.repo_studios/reports/producer_reports/validate_inventory/` with the shape:

```text
validate_inventory/
  validate_inventory-<timestamp>/
    report.json
    report.md
    log.txt
    raw.json
  latest_report.json
  latest_report.md
  latest_report.log
  latest_raw.json
```

- `report.json` — high-level summary containing status, counts, inputs, and statistics.
- `report.md` — friendly Markdown summary for changelog or PR context.
- `log.txt` — key/value snapshot suitable for machine ingestion.
- `raw.json` — complete issue payload separated into `errors`, `warnings`, and the full issue list.

Each run refreshes the `latest_*` pointers and prunes historical runs according to `--artifacts-to-keep`.

## Testing

```bash
python -m pytest .repo_studios/tests/tests_producers/test_validate_inventory.py
```

The tests cover successful validation, structured artifact creation, latest pointer refresh, error reporting, and pruning behaviour.
