<!-- markdownlint-disable MD013 -->

# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/command_center/scripts`
- Python files scanned: 41
- Functions analysed: 681
- Scanner groups detected: 49
- Producer groups referenced: 40
- Scanner groups matched to producers: 25
- Scanner-only groups: 24

## Inputs

- Analysis dataset: `.repo_studios/command_center/scripts/scripts_index/scripts_analysis-20260124-1349.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `_parse_timestamp` — 16 duplicate(s)
    - orchestrators/run_monkey_patch_oversight.py:366-388 (23 line(s)): `sample unavailable`
    - summarizers/summarize_monkey_patch_overview.py:193-215 (23 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:101-110 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:84-93 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/cc_producers/audit_helper_adoption.py:105-114 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_automation_dry_run.py:75-84 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:273-282 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:214-234 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:222-242 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:366-388 (23 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:193-215 (23 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/cc_producers/analyze_standards_index_gaps.py:163-172 (10 line(s)): `def _resolve_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:161-170 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:475-495 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:547-567 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:391-411 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

2. `configure_logging` — 13 duplicate(s)
    - orchestrators/run_test_execution_telemetry.py:462-468 (7 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:275-281 (7 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/aggregators/generate_automation_manifest.py:209-211 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/aggregators/generate_metrics_summary.py:137-139 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:464-472 (9 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:285-293 (9 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:462-468 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:275-281 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/cc_producers/audit_helper_adoption.py:117-119 (3 line(s)): `def _configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_inventory_update.py:60-62 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:588-594 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:616-625 (10 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:303-309 (7 line(s)): `def configure_logging(level: str) -> None:`

3. `_relativize` — 12 duplicate(s)
    - orchestrators/run_docs_health_overview.py:661-676 (16 line(s)): `sample unavailable`
    - orchestrators/run_test_execution_telemetry.py:534-549 (16 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py:246-252 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py:365-371 (7 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:669-684 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:661-676 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:339-354 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:508-525 (18 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:534-549 (16 line(s)): `def _relativize(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:329-344 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:369-386 (18 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:310-325 (16 line(s)): `def _normalize_relative(path: Path | None, repo_root: Path) -> str | None:`

4. `configure_logging` — 10 duplicate(s)
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

5. `main` — 10 duplicate(s)
    - orchestrators/orchestrate_full_diagnostic.py:545-546 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:472-473 (2 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:888-889 (2 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py:1515-1524 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:2203-2212 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:1001-1007 (7 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:1216-1224 (9 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py:1599-1608 (10 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:751-757 (7 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:864-872 (9 line(s)): `def main(argv: Sequence[str] | None = None) -> None:`

6. `build_paths` — 8 duplicate(s)
    - orchestrators/run_test_execution_telemetry.py:414-432 (19 line(s)): `sample unavailable`
    - summarizers/summarize_test_execution_telemetry.py:284-293 (10 line(s)): `sample unavailable`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:570-579 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py:411-422 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_monkey_patch_overview.py:238-249 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_test_execution_telemetry.py:284-293 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py:255-265 (11 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py:263-273 (11 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

7. `latest_churn` — 8 duplicate(s)
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1465-1475 (11 line(s)): `def _latest_anchor_inventory(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1478-1488 (11 line(s)): `def _latest_anchor_validation(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1491-1501 (11 line(s)): `def _latest_docs_integrity(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1504-1514 (11 line(s)): `def _latest_metrics_stub(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1517-1527 (11 line(s)): `def _latest_churn(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1530-1540 (11 line(s)): `def _latest_undocumented(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1543-1552 (10 line(s)): `def _latest_placeholder(paths: Paths) -> Path:`
    - .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py:1555-1564 (10 line(s)): `def _latest_monkey_patch(paths: Paths) -> Path:`

8. `build_paths` — 7 duplicate(s)
    - aggregators/scan_duplicates.py:254-273 (20 line(s)): `sample unavailable`
    - cc_producers/generate_commandview_inventory.py:857-886 (30 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:198-199 (2 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:132-139 (8 line(s)): `sample unavailable`
    - orchestrators/run_command_center_pipeline.py:86-94 (9 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:294-295 (2 line(s)): `sample unavailable`
    - summarizers/generate_function_analysis.py:120-151 (32 line(s)): `sample unavailable`

9. `run` — 7 duplicate(s)
    - aggregators/generate_automation_manifest.py:261-382 (122 line(s)): `sample unavailable`
    - aggregators/generate_metrics_summary.py:201-256 (56 line(s)): `sample unavailable`
    - cc_producers/audit_helper_adoption.py:396-455 (60 line(s)): `sample unavailable`
    - orchestrators/orchestrate_full_diagnostic.py:304-542 (239 line(s)): `sample unavailable`
    - orchestrators/run_automation_dry_run.py:329-469 (141 line(s)): `sample unavailable`
    - orchestrators/run_inventory_update.py:73-99 (27 line(s)): `sample unavailable`
    - orchestrators/run_standards_integrity.py:649-885 (237 line(s)): `sample unavailable`

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

<!-- markdownlint-enable MD013 -->
