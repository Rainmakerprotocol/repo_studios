# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 21
- Functions analysed: 323
- Scanner groups detected: 16
- Producer groups referenced: 20
- Scanner groups matched to producers: 7
- Scanner-only groups: 9

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-20251130-0456.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `configure_logging` — 12 duplicate(s)
    - aggregators/generate_automation_manifest.py:207-209 (3 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:135-137 (3 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:241-242 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:136-137 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:64-65 (2 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:60-62 (3 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:891-892 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:152-153 (2 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:207-209 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:135-137 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_inventory_update.py:60-62 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:115-117 (3 line(s)): `def _configure_logging(level: str) -> None:`

2. `_parse_timestamp` — 8 duplicate(s)
    - aggregators/generate_automation_manifest.py:99-108 (10 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:82-91 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:67-76 (10 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:103-112 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:99-108 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:82-91 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:67-76 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:103-112 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

3. `PathSpec.__post_init__` — 6 duplicate(s)
    - libraries/cli.py:18-19 (2 line(s)): `sample unavailable`
    - libraries/cli.py:29-30 (2 line(s)): `sample unavailable`
    - libraries/manifest.py:26-28 (3 line(s)): `sample unavailable`
    - libraries/manifest.py:76-91 (16 line(s)): `sample unavailable`
    - libraries/metrics.py:24-28 (5 line(s)): `sample unavailable`
    - libraries/metrics.py:50-63 (14 line(s)): `sample unavailable`

4. `_load_cli_module` — 6 duplicate(s)
    - aggregators/scan_duplicates.py:286-295 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:34-43 (10 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:89-98 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:286-295 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:34-43 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:89-98 (10 line(s)): `def _load_cli_module(script_path: Path, module_name: str):`

5. `ManifestFile.to_dict` — 5 duplicate(s)
    - libraries/manifest.py:30-34 (5 line(s)): `sample unavailable`
    - libraries/manifest.py:46-58 (13 line(s)): `sample unavailable`
    - libraries/manifest.py:93-107 (15 line(s)): `sample unavailable`
    - libraries/metrics.py:30-35 (6 line(s)): `sample unavailable`
    - libraries/metrics.py:65-76 (12 line(s)): `sample unavailable`

6. `build_options` — 5 duplicate(s)
    - aggregators/scan_duplicates.py:267-276 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:131-133 (3 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:60-61 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:886-888 (3 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:147-149 (3 line(s)): `sample unavailable`

7. `build_paths` — 5 duplicate(s)
    - aggregators/scan_duplicates.py:245-264 (20 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:121-128 (8 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:78-86 (9 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:854-883 (30 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:113-144 (32 line(s)): `sample unavailable`

8. `main` — 5 duplicate(s)
    - aggregators/generate_automation_manifest.py:383-384 (2 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:257-258 (2 line(s)): `sample unavailable`
    - producers/analyze_standards_index_gaps.py:457-463 (7 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:456-457 (2 line(s)): `sample unavailable`
    - utilities/reports_naming_audit.py:293-297 (5 line(s)): `sample unavailable`

9. `run` — 5 duplicate(s)
    - aggregators/generate_automation_manifest.py:259-380 (122 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:199-254 (56 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:318-458 (141 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:73-99 (27 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:394-453 (60 line(s)): `sample unavailable`

10. `_latest_artifact` — 4 duplicate(s)
    - aggregators/scan_duplicates.py:298-302 (5 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:111-115 (5 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/scan_duplicates.py:298-302 (5 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py:111-115 (5 line(s)): `def _latest_artifact(directory: Path, pattern: str, label: str) -> Path:`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
