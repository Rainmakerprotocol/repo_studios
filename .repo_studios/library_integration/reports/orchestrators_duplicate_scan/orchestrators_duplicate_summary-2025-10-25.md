# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/scripts/orchestrators`
- Python files scanned: 4
- Functions analysed: 44
- Scanner groups detected: 1
- Producer groups referenced: 0
- Scanner groups matched to producers: 0
- Scanner-only groups: 1

## Inputs

- Analysis dataset: `.repo_studios/scripts/orchestrators/orchestrators_index/orchestrators_analysis-2025-10-25.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `cmd_list` — 2 duplicate(s)
   - .repo_studios/scripts/orchestrators/run_standards_index_cli.py:112-117 (6 line(s)): `def cmd_list(index: dict[str, Any], args: argparse.Namespace) -> int:`
   - .repo_studios/scripts/orchestrators/run_standards_index_cli.py:120-124 (5 line(s)): `def cmd_search(index: dict[str, Any], args: argparse.Namespace) -> int:`


## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
