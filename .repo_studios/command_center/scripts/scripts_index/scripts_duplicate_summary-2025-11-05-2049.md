# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 16
- Functions analysed: 274
- Scanner groups detected: 15
- Producer groups referenced: 19
- Scanner groups matched to producers: 8
- Scanner-only groups: 7

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-2025-11-05.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `configure_logging` — 9 duplicate(s)
    - aggregators/generate_automation_manifest.py:207-209 (3 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:134-136 (3 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:235-236 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:123-124 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:68-69 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:871-872 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:122-123 (2 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:207-209 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:134-136 (3 line(s)): `def configure_logging(level: str) -> None:`

2. `_parse_timestamp` — 8 duplicate(s)
    - aggregators/generate_automation_manifest.py:99-108 (10 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:81-90 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:71-80 (10 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:103-112 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:99-108 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:81-90 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:71-80 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:103-112 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

3. `build_paths` — 7 duplicate(s)
    - aggregators/scan_duplicates.py:239-261 (23 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:110-115 (6 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:82-90 (9 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:842-863 (22 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:93-114 (22 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/producers/generate_function_inventory.py:842-863 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:93-114 (22 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

4. `PathSpec.__post_init__` — 6 duplicate(s)
    - libraries/cli.py:18-19 (2 line(s)): `sample unavailable`
    - libraries/cli.py:29-30 (2 line(s)): `sample unavailable`
    - libraries/manifest.py:26-28 (3 line(s)): `sample unavailable`
    - libraries/manifest.py:76-91 (16 line(s)): `sample unavailable`
    - libraries/metrics.py:24-28 (5 line(s)): `sample unavailable`
    - libraries/metrics.py:50-63 (14 line(s)): `sample unavailable`

5. `_load_cli_module` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:283-292 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:38-47 (10 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:93-102 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:283-292 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:38-47 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:93-102 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`

6. `ManifestFile.to_dict` — 5 duplicate(s)
    - libraries/manifest.py:30-34 (5 line(s)): `sample unavailable`
    - libraries/manifest.py:46-58 (13 line(s)): `sample unavailable`
    - libraries/manifest.py:93-110 (18 line(s)): `sample unavailable`
    - libraries/metrics.py:30-35 (6 line(s)): `sample unavailable`
    - libraries/metrics.py:65-76 (12 line(s)): `sample unavailable`

7. `build_options` — 5 duplicate(s)
    - aggregators/scan_duplicates.py:264-273 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:118-120 (3 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:64-65 (2 line(s)): `sample unavailable`
    - producers/generate_function_inventory.py:866-868 (3 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:117-119 (3 line(s)): `sample unavailable`

8. `_latest_artifact` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:295-301 (7 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:115-121 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:295-301 (7 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:115-121 (7 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`

9. `_load_slugify` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:36-45 (10 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:17-26 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:36-45 (10 line(s)): `def _load_slugify() -> Callable[[Path], str]:`
    - .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py:17-26 (10 line(s)): `def _load_slugify() -> Callable[[Path], str]:`

10. `_load_tests` — 4 duplicate(s)
    - aggregators/generate_automation_manifest.py:111-137 (27 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:93-119 (27 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:111-137 (27 line(s)): `def _load_tests(mapping: Mapping[str, object]) -> dict[str, TestRunResult]:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:93-119 (27 line(s)): `def _load_tests(mapping: Mapping[str, object]) -> dict[str, TestRunResult]:`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
