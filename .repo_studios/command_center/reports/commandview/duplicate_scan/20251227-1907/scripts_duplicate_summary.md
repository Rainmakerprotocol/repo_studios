# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 38
- Functions analysed: 628
- Scanner groups detected: 41
- Producer groups referenced: 42
- Scanner groups matched to producers: 18
- Scanner-only groups: 23

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-20251227-1907.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_parse_timestamp` — 27 duplicate(s)
    - aggregators/generate_automation_manifest.py:99-108 (10 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:82-91 (10 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:160-169 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:312-321 (10 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:396-405 (10 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:177-186 (10 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:234-243 (10 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:247-256 (10 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:243-252 (10 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:103-112 (10 line(s)): `sample unavailable`
    - summarizers/summarize_fault_diagnostics_overview.py:121-130 (10 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:135-144 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:99-108 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:82-91 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:312-321 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:396-405 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:177-186 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:234-243 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:247-256 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:243-252 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:103-112 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:121-130 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:135-144 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:160-169 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py:175-184 (10 line(s)): `def _resolve_timestamp(raw: str | None) -> datetime:`

2. `configure_logging` — 22 duplicate(s)
    - aggregators/generate_automation_manifest.py:207-209 (3 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:135-137 (3 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:243-244 (2 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:145-146 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:147-148 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:72-73 (2 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:365-366 (2 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:438-442 (5 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:220-221 (2 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:60-62 (3 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:287-288 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:294-295 (2 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:278-279 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:894-895 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:157-158 (2 line(s)): `sample unavailable`
    - summarizers/summarize_fault_diagnostics_overview.py:160-161 (2 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:182-183 (2 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:181-182 (2 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:207-209 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:135-137 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_inventory_update.py:60-62 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:115-117 (3 line(s)): `def _configure_logging(level: str) -> None:`

3. `build_paths` — 15 duplicate(s)
    - aggregators/scan_duplicates.py:247-266 (20 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:197-198 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:132-139 (8 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:86-94 (9 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:324-325 (2 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:408-409 (2 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:198-199 (2 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:255-256 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:268-269 (2 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:255-256 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:857-886 (30 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:118-149 (32 line(s)): `sample unavailable`
    - summarizers/summarize_fault_diagnostics_overview.py:142-143 (2 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:156-157 (2 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:185-186 (2 line(s)): `sample unavailable`

4. `_relativize` — 13 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:245-251 (7 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:410-416 (7 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:464-470 (7 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:241-247 (7 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:308-314 (7 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:339-345 (7 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:315-321 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:410-416 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:464-470 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:241-247 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:308-314 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:339-345 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:315-321 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`

5. `run` — 12 duplicate(s)
    - aggregators/generate_automation_manifest.py:259-380 (122 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:199-254 (56 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:304-544 (241 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:329-469 (141 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:887-1118 (232 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:970-1382 (413 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:441-600 (160 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:73-99 (27 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:545-731 (187 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:588-828 (241 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:520-726 (207 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:394-453 (60 line(s)): `sample unavailable`

6. `_resolve_optional_path` — 10 duplicate(s)
    - orchestrators/run_monkey_patch_oversight.py:246-252 (7 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:259-265 (7 line(s)): `sample unavailable`
    - producers/analyze_standards_index_gaps.py:166-172 (7 line(s)): `sample unavailable`
    - summarizers/summarize_fault_diagnostics_overview.py:133-139 (7 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:147-153 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:246-252 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:259-265 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py:166-172 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:133-139 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:147-153 (7 line(s)): `def _resolve_optional_path(repo_root: Path, raw: str | None) -> Path | None:`

7. `build_options` — 10 duplicate(s)
    - aggregators/scan_duplicates.py:269-278 (10 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:201-210 (10 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:142-144 (3 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:68-69 (2 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:334-362 (29 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:412-435 (24 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:259-275 (17 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:889-891 (3 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:152-154 (3 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:189-192 (4 line(s)): `sample unavailable`

8. `main` — 9 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:547-548 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:472-473 (2 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:1121-1122 (2 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:1385-1386 (2 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:603-604 (2 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:734-735 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:831-832 (2 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:729-730 (2 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:654-656 (3 line(s)): `sample unavailable`

9. `parse_args` — 9 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:172-194 (23 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:87-129 (43 line(s)): `sample unavailable`
    - orchestrators/run_dependency_import_hygiene.py:237-309 (73 line(s)): `sample unavailable`
    - orchestrators/run_docs_health_overview.py:331-393 (63 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:147-174 (28 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:194-231 (38 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:203-244 (42 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:201-240 (40 line(s)): `sample unavailable`
    - producers/analyze_standards_index_gaps.py:121-158 (38 line(s)): `sample unavailable`

10. `_register_scripts` — 8 duplicate(s)
    - orchestrators/run_dependency_import_hygiene.py:804-814 (11 line(s)): `sample unavailable`
    - orchestrators/run_fault_diagnostics_overview.py:426-430 (5 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:528-534 (7 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:509-519 (11 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:498-509 (12 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:804-814 (11 line(s)): `def _register_scripts(registry: CatalogRegistry) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:528-534 (7 line(s)): `def _register_scripts(registry: CatalogRegistry) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:509-519 (11 line(s)): `def _register_scripts(registry: CatalogRegistry) -> None:`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
