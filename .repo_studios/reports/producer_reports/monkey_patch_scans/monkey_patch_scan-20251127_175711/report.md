# Monkey Patch Scan Report

- Status: `ok`
- Timestamp: `2025-11-27T17:57:11.586737+00:00`
- Scan Root: `.`
- Files Scanned: 190
- Files With Findings: 3
- Total Findings: 3
- Parse Errors: 0

## Findings by Category

| Category | Count |
| --- | ---: |
| attribute_reassignment_on_import | 3 |

## Patched Import Bases

| Package | Count |
| --- | ---: |
| tomllib | 2 |
| fcntl | 1 |

## Files With Highest Patch Counts

| File | Count |
| --- | ---: |
| .repo_studios\scripts\producers\generate_dependency_hygiene_report.py | 1 |
| .repo_studios\scripts\producers\generate_typecheck_report.py | 1 |
| .repo_studios\scripts\utilities\configure_faulthandler_runtime.py | 1 |

## Next Steps

- [ ] Review global mutations (builtins, os.environ) and confine to startup phases.
- [ ] Replace module-scope patches with context-managed patches in tests.
- [ ] Isolate import-time overrides behind flags or dependency injection.
- [ ] Add targeted tests for any retained patches with clear rationale.
