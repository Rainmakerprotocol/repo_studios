<!-- markdownlint-disable MD013 -->

# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 42
- Functions analysed: 703
- Scanner groups detected: 51
- Producer groups referenced: 40
- Scanner groups matched to producers: 27
- Scanner-only groups: 24

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-20260205-1341.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_parse_timestamp` — 17 duplicate(s)
    - orchestrators/run_monkey_patch_oversight.py:374-396 (23 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:193-215 (23 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:101-110 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:84-93 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/cc_producers/audit_helper_adoption.py:105-114 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:273-282 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py:292-312 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:214-234 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:222-242 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:374-396 (23 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:193-215 (23 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/cc_producers/analyze_standards_index_gaps.py:163-172 (10 line(s)): `def _resolve_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:161-170 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:475-495 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:548-568 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:455-475 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

2. `configure_logging` — 15 duplicate(s)
    - orchestrators/run_test_execution_telemetry.py:526-532 (7 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:275-281 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py:350-360 (11 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:295-305 (11 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:472-480 (9 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:285-293 (9 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:526-532 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:275-281 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/cc_producers/audit_helper_adoption.py:117-119 (3 line(s)): `def _configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_inventory_update.py:60-62 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:588-594 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:617-626 (10 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:303-309 (7 line(s)): `def configure_logging(level: str) -> None:`

3. `_relativize` — 13 duplicate(s)
    - orchestrators/run_docs_health_overview.py:662-677 (16 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:603-618 (16 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py:395-410 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:339-354 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:246-252 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:365-371 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:669-684 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:662-677 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:516-533 (18 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:603-618 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:329-344 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:369-386 (18 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:310-325 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`

4. `run` — 11 duplicate(s)
    - aggregators/generate_automation_manifest.py:261-382 (122 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:201-256 (56 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:989-1031 (43 line(s)): `sample unavailable`
    - cc_producers/audit_helper_adoption.py:414-479 (66 line(s)): `sample unavailable`
    - cc_producers/generate_commandview_inventory.py:2928-2983 (56 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:304-542 (239 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:329-469 (141 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:205-266 (62 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:73-99 (27 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:649-885 (237 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:373-410 (38 line(s)): `sample unavailable`

5. `configure_logging` — 10 duplicate(s)
    - aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:250-251 (2 line(s)): `sample unavailable`
    - cc_producers/generate_commandview_inventory.py:894-895 (2 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:146-147 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:147-148 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:72-73 (2 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:60-62 (3 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:320-321 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:159-160 (2 line(s)): `sample unavailable`

6. `main` — 9 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:545-546 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:472-473 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:888-889 (2 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:1515-1524 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:2217-2226 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:1001-1007 (7 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:1224-1232 (9 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:751-757 (7 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:864-872 (9 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`

7. `build_paths` — 8 duplicate(s)
    - orchestrators/run_test_execution_telemetry.py:478-496 (19 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:284-293 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py:315-325 (11 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:255-265 (11 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:571-580 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:419-430 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:238-249 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:284-293 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

8. `latest_churn` — 8 duplicate(s)
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1475-1485 (11 line(s)): `def _latest_anchor_inventory(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1488-1498 (11 line(s)): `def _latest_anchor_validation(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1501-1511 (11 line(s)): `def _latest_docs_integrity(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1514-1524 (11 line(s)): `def _latest_metrics_stub(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1527-1537 (11 line(s)): `def _latest_churn(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1540-1550 (11 line(s)): `def _latest_undocumented(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1553-1562 (10 line(s)): `def _latest_placeholder(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1565-1574 (10 line(s)): `def _latest_monkey_patch(paths: Paths) -> Path:`

9. `parse_args` — 8 duplicate(s)
    - aggregators/scan_duplicates.py:184-247 (64 line(s)): `sample unavailable`
    - cc_producers/analyze_standards_index_gaps.py:109-146 (38 line(s)): `sample unavailable`
    - cc_producers/generate_commandview_inventory.py:811-851 (41 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:173-195 (23 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:87-129 (43 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:45-65 (21 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:205-270 (66 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:76-114 (39 line(s)): `sample unavailable`

10. `_load_callable` — 7 duplicate(s)
    - orchestrators/run_fault_diagnostics_overview.py:308-336 (29 line(s)): `sample unavailable`
    - orchestrators/run_monkey_patch_oversight.py:483-513 (31 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_available_scripts_oversight.py:364-392 (29 line(s)): `def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[..., Any]:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:597-625 (29 line(s)): `def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[..., Any]:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:629-659 (31 line(s)): `def _load_callable(`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:308-336 (29 line(s)): `def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str] | None], Any]:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:483-513 (31 line(s)): `def _load_callable(script_path: Path, module_name: str, attribute: str) -> Callable[[Sequence[str] | None], Any]:`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.

<!-- markdownlint-enable MD013 -->
