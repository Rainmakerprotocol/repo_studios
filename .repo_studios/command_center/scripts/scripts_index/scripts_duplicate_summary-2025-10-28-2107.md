# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 7
- Functions analysed: 113
- Scanner groups detected: 5
- Producer groups referenced: 11
- Scanner groups matched to producers: 4
- Scanner-only groups: 1

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-2025-10-28.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_load_slugify` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:36-45 (10 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:20-29 (10 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:17-26 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:36-45 (10 line(s)): `def _load_slugify() -> Callable[[Path], str]:`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:20-29 (10 line(s)): `def _load_slugify() -> Callable[[Path], str]:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:17-26 (10 line(s)): `def _load_slugify() -> Callable[[Path], str]:`

2. `build_paths` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:239-261 (23 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:82-90 (9 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:182-203 (22 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:93-114 (22 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:182-203 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:93-114 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

3. `_latest_artifact` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:295-301 (7 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:115-121 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:295-301 (7 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:115-121 (7 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`

4. `_load_cli_module` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:283-292 (10 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:93-102 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:283-292 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:93-102 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`

5. `build_options` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:264-273 (10 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:64-65 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:206-207 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:117-119 (3 line(s)): `sample unavailable`

6. `configure_logging` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:235-236 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:68-69 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:210-211 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:122-123 (2 line(s)): `sample unavailable`

7. `parse_args` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:173-232 (60 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:41-61 (21 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:143-176 (34 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:50-87 (38 line(s)): `sample unavailable`

8. `run` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:956-999 (44 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:203-264 (62 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:856-901 (46 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:330-367 (38 line(s)): `sample unavailable`

9. `main` — 3 duplicate(s)
    - orchestrators/run_command_center_pipeline.py:267-268 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:904-905 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:370-371 (2 line(s)): `sample unavailable`

10. `_resolve_within_repo` — 2 duplicate(s)
    - aggregators/scan_duplicates.py:356-362 (7 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:72-79 (8 line(s)): `sample unavailable`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
