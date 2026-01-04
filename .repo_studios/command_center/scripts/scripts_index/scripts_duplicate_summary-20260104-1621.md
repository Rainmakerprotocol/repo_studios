# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 40
- Functions analysed: 664
- Scanner groups detected: 50
- Producer groups referenced: 39
- Scanner groups matched to producers: 25
- Scanner-only groups: 25

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-20260104-1621.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_parse_timestamp` — 16 duplicate(s)
    - orchestrators/run_monkey_patch_oversight.py:336-358 (23 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:179-201 (23 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:101-110 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:84-93 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:244-253 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:105-114 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:211-231 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:213-233 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:336-358 (23 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:179-201 (23 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:161-170 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/producers/analyze_standards_index_gaps.py:180-189 (10 line(s)): `def _resolve_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:433-453 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:537-557 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:391-411 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

2. `configure_logging` — 14 duplicate(s)
    - orchestrators/run_test_execution_telemetry.py:462-468 (7 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:275-281 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:292-298 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:292-298 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:434-442 (9 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:271-279 (9 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:462-468 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:275-281 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:521-527 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:606-615 (10 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_inventory_update.py:60-62 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/producers/audit_helper_adoption.py:117-119 (3 line(s)): `def _configure_logging(level: str) -> None:`

3. `_relativize` — 12 duplicate(s)
    - orchestrators/run_docs_health_overview.py:651-666 (16 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:534-549 (16 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:246-252 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:336-342 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:602-617 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:651-666 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:332-347 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:478-495 (18 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:534-549 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:318-333 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:341-358 (18 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:310-325 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`

4. `main` — 11 duplicate(s)
    - orchestrators/run_command_center_pipeline.py:269-270 (2 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:102-103 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:2969-2970 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:413-414 (2 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:1448-1457 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1795-1804 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:797-803 (7 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:1005-1013 (9 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:1598-1607 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:711-717 (7 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:696-704 (9 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`

5. `configure_logging` — 10 duplicate(s)
    - aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `sample unavailable`
    - aggregators/scan_duplicates.py:245-246 (2 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:146-147 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:147-148 (2 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:72-73 (2 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:60-62 (3 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:291-292 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:894-895 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:159-160 (2 line(s)): `sample unavailable`

6. `build_paths` — 9 duplicate(s)
    - orchestrators/run_test_execution_telemetry.py:414-432 (19 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:284-293 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:456-465 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:560-569 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:381-392 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:224-235 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:284-293 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:252-262 (11 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:254-264 (11 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

7. `latest_churn` — 8 duplicate(s)
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1125-1135 (11 line(s)): `def _latest_anchor_inventory(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1138-1148 (11 line(s)): `def _latest_anchor_validation(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1151-1161 (11 line(s)): `def _latest_docs_integrity(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1164-1174 (11 line(s)): `def _latest_metrics_stub(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1177-1187 (11 line(s)): `def _latest_churn(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1190-1200 (11 line(s)): `def _latest_undocumented(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1203-1212 (10 line(s)): `def _latest_placeholder(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1215-1224 (10 line(s)): `def _latest_monkey_patch(paths: Paths) -> Path:`

8. `build_paths` — 7 duplicate(s)
    - aggregators/scan_duplicates.py:249-268 (20 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:198-199 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:132-139 (8 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:86-94 (9 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:265-266 (2 line(s)): `sample unavailable`
    - producers/generate_commandview_inventory.py:857-886 (30 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:120-151 (32 line(s)): `sample unavailable`

9. `run` — 7 duplicate(s)
    - aggregators/generate_automation_manifest.py:261-382 (122 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:201-256 (56 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:304-542 (239 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:329-469 (141 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:73-99 (27 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:586-814 (229 line(s)): `sample unavailable`
    - producers/audit_helper_adoption.py:396-455 (60 line(s)): `sample unavailable`

10. `PathSpec.__post_init__` — 6 duplicate(s)
    - libraries/cli.py:25-26 (2 line(s)): `sample unavailable`
    - libraries/cli.py:36-37 (2 line(s)): `sample unavailable`
    - libraries/manifest.py:26-28 (3 line(s)): `sample unavailable`
    - libraries/manifest.py:76-91 (16 line(s)): `sample unavailable`
    - libraries/metrics.py:24-28 (5 line(s)): `sample unavailable`
    - libraries/metrics.py:50-63 (14 line(s)): `sample unavailable`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
