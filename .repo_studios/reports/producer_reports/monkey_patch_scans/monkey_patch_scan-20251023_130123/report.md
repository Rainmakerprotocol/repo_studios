# Monkey Patch Scan Report

- Status: `ok`
- Timestamp: `2025-10-23T13:01:23.706927+00:00`
- Scan Root: `.repo_studios\scripts\producers`
- Files Scanned: 18
- Files With Findings: 2
- Total Findings: 2
- Parse Errors: 0

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 2 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |

## Files With Highest Patch Counts

| File | Count |
| --- | ---: |
| .repo_studios\scripts\producers\generate_dependency_hygiene_report.py | 1 |
| .repo_studios\scripts\producers\generate_typecheck_report.py | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
