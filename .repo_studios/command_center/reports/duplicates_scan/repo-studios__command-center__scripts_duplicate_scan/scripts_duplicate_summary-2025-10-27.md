# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 4
- Functions analysed: 99
- Scanner groups detected: 3
- Producer groups referenced: 8
- Scanner groups matched to producers: 2
- Scanner-only groups: 1

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-2025-10-27.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_slugify_relative` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:348-354 (7 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:162-168 (7 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:74-80 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:348-354 (7 line(s)): `def _slugify_relative(relative_path: Path) -> str:`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:162-168 (7 line(s)): `def _slugify_relative(relative_path: Path) -> str:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:74-80 (7 line(s)): `def _slugify_relative(relative_path: Path) -> str:`

2. `build_paths` — 5 duplicate(s)
    - aggregators/scan_duplicates.py:222-244 (23 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:171-192 (22 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:83-104 (22 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:171-192 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:83-104 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

3. `build_options` — 3 duplicate(s)
    - aggregators/scan_duplicates.py:247-256 (10 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:195-196 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:107-109 (3 line(s)): `sample unavailable`

4. `configure_logging` — 3 duplicate(s)
    - aggregators/scan_duplicates.py:218-219 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:199-200 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:112-113 (2 line(s)): `sample unavailable`

5. `parse_args` — 3 duplicate(s)
    - aggregators/scan_duplicates.py:156-215 (60 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:126-159 (34 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:34-71 (38 line(s)): `sample unavailable`

6. `run` — 3 duplicate(s)
    - aggregators/scan_duplicates.py:932-975 (44 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:845-890 (46 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:320-357 (38 line(s)): `sample unavailable`

7. `compose_payload` — 2 duplicate(s)
    - aggregators/scan_duplicates.py:848-867 (20 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:234-265 (32 line(s)): `sample unavailable`

8. `main` — 2 duplicate(s)
    - producers/generate_function_inventory.py:893-894 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:360-361 (2 line(s)): `sample unavailable`

9. `visit_functiondef` — 2 duplicate(s)
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:375-377 (3 line(s)): `def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: D401 - docstring inherited`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:379-381 (3 line(s)): `def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: D401`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
