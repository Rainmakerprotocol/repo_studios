# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/scripts`
- Python files scanned: 35
- Functions analysed: 611
- Scanner groups detected: 44
- Producer groups referenced: 53
- Scanner groups matched to producers: 31
- Scanner-only groups: 13

## Inputs

- Analysis dataset: `.repo_studios/scripts/scripts_index/scripts_analysis-2025-10-27.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `prune_old_runs` — 20 duplicate(s)
    - producers/check_inventory_health.py:124-140 (17 line(s)): `sample unavailable`
    - producers/diff_standards_index.py:83-99 (17 line(s)): `sample unavailable`
    - producers/generate_dependency_hygiene_report.py:272-288 (17 line(s)): `sample unavailable`
    - producers/generate_import_graph_report.py:173-186 (14 line(s)): `sample unavailable`
    - producers/generate_lizard_report.py:167-183 (17 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:408-424 (17 line(s)): `sample unavailable`
    - producers/generate_typecheck_report.py:78-90 (13 line(s)): `sample unavailable`
    - producers/render_inventory_views.py:75-87 (13 line(s)): `sample unavailable`
    - producers/validate_inventory.py:195-207 (13 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/analyze_standards_index_gaps.py:258-277 (20 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:`
    - .repo_studios/scripts/producers/generate_anchor_inventory.py:274-293 (20 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:`
    - .repo_studios/scripts/producers/check_inventory_health.py:124-140 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:272-288 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:167-183 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/render_inventory_views.py:75-87 (13 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/validate_inventory.py:195-207 (13 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/diff_standards_index.py:83-99 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/generate_import_graph_report.py:173-186 (14 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/generate_standards_index.py:408-424 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/generate_typecheck_report.py:78-90 (13 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`

2. `configure_logging` — 19 duplicate(s)
    - producers/analyze_test_hardening.py:107-108 (2 line(s)): `sample unavailable`
    - producers/check_inventory_health.py:274-276 (3 line(s)): `sample unavailable`
    - producers/diff_standards_index.py:453-455 (3 line(s)): `sample unavailable`
    - producers/generate_dependency_hygiene_report.py:327-329 (3 line(s)): `sample unavailable`
    - producers/generate_import_graph_report.py:360-362 (3 line(s)): `sample unavailable`
    - producers/generate_lizard_report.py:603-605 (3 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:623-625 (3 line(s)): `sample unavailable`
    - producers/generate_typecheck_report.py:370-371 (2 line(s)): `sample unavailable`
    - producers/scan_code_placeholders.py:347-348 (2 line(s)): `sample unavailable`
    - producers/scan_monkey_patches.py:1187-1188 (2 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:87-88 (2 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:91-92 (2 line(s)): `sample unavailable`
    - producers/validate_metrics_anchor_stubs.py:81-82 (2 line(s)): `sample unavailable`
    - producers/verify_docs_integrity.py:120-121 (2 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/check_inventory_health.py:274-276 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/diff_standards_index.py:453-455 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:327-329 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:603-605 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_standards_index.py:623-625 (3 line(s)): `def configure_logging(level: str) -> None:`

3. `_copy_latest` — 16 duplicate(s)
    - producers/diff_standards_index.py:102-108 (7 line(s)): `sample unavailable`
    - producers/generate_dependency_hygiene_report.py:263-269 (7 line(s)): `sample unavailable`
    - producers/generate_import_graph_report.py:164-170 (7 line(s)): `sample unavailable`
    - producers/generate_lizard_report.py:158-164 (7 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:427-433 (7 line(s)): `sample unavailable`
    - producers/generate_typecheck_report.py:356-362 (7 line(s)): `sample unavailable`
    - producers/render_inventory_views.py:277-283 (7 line(s)): `sample unavailable`
    - producers/validate_inventory.py:210-216 (7 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/diff_standards_index.py:102-108 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:263-269 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/generate_import_graph_report.py:164-170 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:158-164 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/generate_standards_index.py:427-433 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/generate_typecheck_report.py:356-362 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/render_inventory_views.py:277-283 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`
    - .repo_studios/scripts/producers/validate_inventory.py:210-216 (7 line(s)): `def _copy_latest(src: Path, dest: Path) -> None:`

4. `main` — 14 duplicate(s)
    - aggregators/analyze_monkey_patch_trends.py:259-290 (32 line(s)): `sample unavailable`
    - consumers/generate_fault_artifacts.py:314-346 (33 line(s)): `sample unavailable`
    - orchestrators/run_pytest_log_capture.py:376-633 (258 line(s)): `sample unavailable`
    - orchestrators/run_standards_index_cli.py:197-216 (20 line(s)): `sample unavailable`
    - producers/analyze_standards_index_gaps.py:353-382 (30 line(s)): `sample unavailable`
    - producers/diff_standards_index.py:458-559 (102 line(s)): `sample unavailable`
    - producers/generate_lizard_report.py:608-663 (56 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:660-709 (50 line(s)): `sample unavailable`
    - producers/generate_typecheck_report.py:391-469 (79 line(s)): `sample unavailable`
    - producers/scan_code_placeholders.py:376-378 (3 line(s)): `sample unavailable`
    - producers/scan_monkey_patches.py:1270-1277 (8 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:400-402 (3 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:470-472 (3 line(s)): `sample unavailable`
    - producers/validate_metrics_anchor_stubs.py:381-383 (3 line(s)): `sample unavailable`

5. `main` — 12 duplicate(s)
    - orchestrators/orchestrate_health_suite.py:578-668 (91 line(s)): `sample unavailable`
    - producers/analyze_test_hardening.py:594-596 (3 line(s)): `sample unavailable`
    - producers/generate_anchor_inventory.py:343-376 (34 line(s)): `sample unavailable`
    - producers/generate_dependency_hygiene_report.py:332-411 (80 line(s)): `sample unavailable`
    - producers/generate_import_graph_report.py:365-428 (64 line(s)): `sample unavailable`
    - producers/validate_inventory.py:528-614 (87 line(s)): `sample unavailable`
    - producers/verify_docs_integrity.py:590-592 (3 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:400-402 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:470-472 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:381-383 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/analyze_test_hardening.py:594-596 (3 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/verify_docs_integrity.py:590-592 (3 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`

6. `_parse_timestamp` — 11 duplicate(s)
    - producers/analyze_standards_index_gaps.py:294-300 (7 line(s)): `sample unavailable`
    - producers/generate_anchor_inventory.py:326-332 (7 line(s)): `sample unavailable`
    - producers/generate_dependency_hygiene_report.py:249-255 (7 line(s)): `sample unavailable`
    - producers/generate_import_graph_report.py:150-156 (7 line(s)): `sample unavailable`
    - producers/render_inventory_views.py:52-58 (7 line(s)): `sample unavailable`
    - producers/validate_markdown_anchors.py:247-253 (7 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/analyze_standards_index_gaps.py:294-300 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_anchor_inventory.py:326-332 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/validate_markdown_anchors.py:247-253 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:249-255 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_import_graph_report.py:150-156 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

7. `prune_history` — 10 duplicate(s)
    - producers/scan_code_placeholders.py:335-344 (10 line(s)): `sample unavailable`
    - producers/scan_monkey_patches.py:1004-1014 (11 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:310-320 (11 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:363-379 (17 line(s)): `sample unavailable`
    - producers/validate_metrics_anchor_stubs.py:315-331 (17 line(s)): `sample unavailable`
    - producers/verify_docs_integrity.py:520-540 (21 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:363-379 (17 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:315-331 (17 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`
    - .repo_studios/scripts/producers/scan_monkey_patches.py:1004-1014 (11 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:310-320 (11 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`

8. `_write_latest_artifacts` — 8 duplicate(s)
    - producers/scan_code_placeholders.py:319-332 (14 line(s)): `sample unavailable`
    - producers/scan_monkey_patches.py:943-956 (14 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:274-288 (15 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:329-341 (13 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:319-332 (14 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`
    - .repo_studios/scripts/producers/scan_monkey_patches.py:943-956 (14 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:274-288 (15 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:329-341 (13 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`

9. `_sanitize_slug` — 7 duplicate(s)
    - producers/generate_lizard_report.py:152-155 (4 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:394-398 (5 line(s)): `sample unavailable`
    - producers/generate_typecheck_report.py:65-69 (5 line(s)): `sample unavailable`
    - producers/render_inventory_views.py:65-66 (2 line(s)): `sample unavailable`
    - producers/validate_inventory.py:173-174 (2 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/generate_standards_index.py:394-398 (5 line(s)): `def _sanitize_slug(slug: str) -> str:`
    - .repo_studios/scripts/producers/generate_typecheck_report.py:65-69 (5 line(s)): `def _sanitize_slug(slug: str) -> str:`

10. `build_paths` — 7 duplicate(s)
    - producers/analyze_test_hardening.py:93-97 (5 line(s)): `sample unavailable`
    - producers/scan_code_placeholders.py:115-119 (5 line(s)): `sample unavailable`
    - producers/scan_monkey_patches.py:1191-1201 (11 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:91-109 (19 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:95-119 (25 line(s)): `sample unavailable`
    - producers/validate_metrics_anchor_stubs.py:85-111 (27 line(s)): `sample unavailable`
    - producers/verify_docs_integrity.py:124-138 (15 line(s)): `sample unavailable`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
