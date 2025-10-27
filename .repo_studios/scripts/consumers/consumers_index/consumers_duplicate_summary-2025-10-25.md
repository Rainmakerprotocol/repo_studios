# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/scripts/consumers`
- Python files scanned: 4
- Functions analysed: 40
- Scanner groups detected: 1
- Producer groups referenced: 1
- Scanner groups matched to producers: 0
- Scanner-only groups: 1

## Inputs

- Analysis dataset: `.repo_studios/scripts/consumers/consumers_index/consumers_analysis-2025-10-25.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `main` — 2 duplicate(s)
   - classify_monkey_patches.py:117-129 (13 line(s)): `sample unavailable`
   - generate_test_log_health_report.py:213-304 (92 line(s)): `sample unavailable`

2. `read` — 2 duplicate(s)
   - .repo_studios/scripts/consumers/generate_fault_artifacts.py:63-67 (5 line(s)): `def _read_text(p: Path) -> str:`
   - .repo_studios/scripts/consumers/generate_test_log_health_report.py:49-53 (5 line(s)): `def _read(p: Path) -> str:`


## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
