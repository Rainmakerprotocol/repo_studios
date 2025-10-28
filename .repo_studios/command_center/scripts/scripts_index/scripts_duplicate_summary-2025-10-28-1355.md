# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 5
- Functions analysed: 112
- Scanner groups detected: 5
- Producer groups referenced: 11
- Scanner groups matched to producers: 4
- Scanner-only groups: 1

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-2025-10-28.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_slugify_relative` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:348-354 (7 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:162-168 (7 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:74-80 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:348-354 (7 line(s)): `def _slugify_relative(relative_path: Path) -> str:`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:162-168 (7 line(s)): `def _slugify_relative(relative_path: Path) -> str:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:74-80 (7 line(s)): `def _slugify_relative(relative_path: Path) -> str:`

2. `build_paths` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:222-244 (23 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:82-90 (9 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:171-192 (22 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:83-104 (22 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:171-192 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:83-104 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

3. `_latest_artifact` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:278-284 (7 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:115-121 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:278-284 (7 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:115-121 (7 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`

4. `_load_cli_module` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:266-275 (10 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:93-102 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:266-275 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:93-102 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`

5. `build_options` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:247-256 (10 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:64-65 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:195-196 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:107-109 (3 line(s)): `sample unavailable`

6. `configure_logging` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:218-219 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:68-69 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:199-200 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:112-113 (2 line(s)): `sample unavailable`

7. `parse_args` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:156-215 (60 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:41-61 (21 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:126-159 (34 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:34-71 (38 line(s)): `sample unavailable`

8. `run` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:945-988 (44 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:203-264 (62 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:845-890 (46 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:320-357 (38 line(s)): `sample unavailable`

9. `main` — 3 duplicate(s)
    - orchestrators/run_command_center_pipeline.py:267-268 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:893-894 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:360-361 (2 line(s)): `sample unavailable`

10. `_resolve_within_repo` — 2 duplicate(s)
    - aggregators/scan_duplicates.py:339-345 (7 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:72-79 (8 line(s)): `sample unavailable`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
