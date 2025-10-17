# Monkey Patch Scan Summary

Date: 2025-09-11T10:45:37.241192


## Totals by Category

- attribute_reassignment_on_import: 2

## Top Externals Patched

- fcntl: 1
- tomllib: 1

## Files with Highest Patch Count

- dep_hygiene_report.py: 1
- faulthandler.py: 1

## Patches Grouped by Package

| Package | Count |
|---|---:|
| fcntl | 1 |
| tomllib | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
