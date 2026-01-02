# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 40
- Functions analysed: 660
- Scanner groups detected: 43
- Producer groups referenced: 38
- Scanner groups matched to producers: 20
- Scanner-only groups: 23

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-20260102-0422.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_parse_timestamp` — 16 duplicate(s)
    - orchestrators/run_fault_diagnostics_overview.py:173-190 (18 line(s)): `sample unavailable`
    - summarizers/summarize_fault_diagnostics_overview.py:206-223 (18 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:101-110 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:84-93 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:313-322 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:397-406 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:235-244 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:246-255 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:248-257 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:105-114 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:137-146 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:173-190 (18 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:206-223 (18 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:161-170 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py:180-189 (10 line(s)): `def _resolve_timestamp(raw: str | None) -> datetime:`

2. `configure_logging` — 16 duplicate(s)
    - aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:245-246 (2 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:146-147 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:147-148 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:72-73 (2 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:366-367 (2 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:439-443 (5 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:60-62 (3 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:288-289 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:293-294 (2 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:283-284 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:894-895 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:159-160 (2 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:184-185 (2 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:184-185 (2 line(s)): `sample unavailable`

3. `_relativize` — 13 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:246-252 (7 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:411-417 (7 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:465-471 (7 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:309-315 (7 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:338-344 (7 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:320-326 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:411-417 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:465-471 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:309-315 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:338-344 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:320-326 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:289-304 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:306-321 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`

4. `build_paths` — 13 duplicate(s)
    - aggregators/scan_duplicates.py:249-268 (20 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:198-199 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:132-139 (8 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:86-94 (9 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:325-326 (2 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:409-410 (2 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:256-257 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:267-268 (2 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:260-261 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:857-886 (30 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:120-151 (32 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:158-159 (2 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:188-189 (2 line(s)): `sample unavailable`

5. `_parse_timestamp` — 11 duplicate(s)
    - aggregators/generate_automation_manifest.py:101-110 (10 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:84-93 (10 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:161-170 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:313-322 (10 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:397-406 (10 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:235-244 (10 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:246-255 (10 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:248-257 (10 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:105-114 (10 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:137-146 (10 line(s)): `sample unavailable`

6. `run` — 11 duplicate(s)
    - aggregators/generate_automation_manifest.py:261-382 (122 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:201-256 (56 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:304-542 (239 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:329-469 (141 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:888-1119 (232 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:977-1389 (413 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:73-99 (27 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:546-732 (187 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:587-815 (229 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:870-1088 (219 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:396-455 (60 line(s)): `sample unavailable`

7. `build_options` — 10 duplicate(s)
    - aggregators/scan_duplicates.py:271-280 (10 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:202-211 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:142-144 (3 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:68-69 (2 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:335-363 (29 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:413-436 (24 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:264-280 (17 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:889-891 (3 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:154-156 (3 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:192-195 (4 line(s)): `sample unavailable`

8. `_resolve_optional_path` — 8 duplicate(s)
    - orchestrators/run_monkey_patch_oversight.py:247-253 (7 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:258-264 (7 line(s)): `sample unavailable`
    - producers/analyze_standards_index_gaps.py:171-177 (7 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:149-155 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:247-253 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:258-264 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py:171-177 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:149-155 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`

9. `configure_logging` — 8 duplicate(s)
    - orchestrators/run_fault_diagnostics_overview.py:250-256 (7 line(s)): `sample unavailable`
    - summarizers/summarize_fault_diagnostics_overview.py:281-287 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:250-256 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:281-287 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_inventory_update.py:60-62 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:117-119 (3 line(s)): `def _configure_logging(level: str) -> None:`

10. `main` — 8 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:545-546 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:472-473 (2 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:1122-1123 (2 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:1392-1393 (2 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:735-736 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:818-819 (2 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:1091-1092 (2 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:657-659 (3 line(s)): `sample unavailable`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
