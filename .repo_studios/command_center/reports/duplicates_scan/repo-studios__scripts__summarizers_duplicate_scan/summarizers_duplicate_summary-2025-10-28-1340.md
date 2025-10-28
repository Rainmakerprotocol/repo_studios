# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/scripts/summarizers`
- Python files scanned: 2
- Functions analysed: 39
- Scanner groups detected: 1
- Producer groups referenced: 0
- Scanner groups matched to producers: 0
- Scanner-only groups: 1

## Inputs

- Analysis dataset: `.repo_studios/scripts/summarizers/summarizers_index/summarizers_analysis-2025-10-28.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `append_table` — 2 duplicate(s)
    - .repo_studios/scripts/summarizers/summarize_health_suite.py:83-89 (7 line(s)): `def _append_table(lines: list[str], rows: list[str]) -> None:`
    - .repo_studios/scripts/summarizers/summarize_health_suite.py:92-99 (8 line(s)): `def _append_blockquote(lines: list[str], rows: list[str]) -> None:`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
