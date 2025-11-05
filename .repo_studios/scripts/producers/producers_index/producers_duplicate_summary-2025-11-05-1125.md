# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/scripts/producers`
- Python files scanned: 20
- Functions analysed: 444
- Scanner groups detected: 30
- Producer groups referenced: 42
- Scanner groups matched to producers: 21
- Scanner-only groups: 9

## Inputs

- Analysis dataset: `.repo_studios/scripts/producers/producers_index/producers_analysis-2025-11-05.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `configure_logging` — 19 duplicate(s)
    - analyze_test_hardening.py:153-154 (2 line(s)): `sample unavailable`
    - check_inventory_health.py:285-287 (3 line(s)): `sample unavailable`
    - diff_standards_index.py:458-460 (3 line(s)): `sample unavailable`
    - generate_dependency_hygiene_report.py:268-270 (3 line(s)): `sample unavailable`
    - generate_import_graph_report.py:346-348 (3 line(s)): `sample unavailable`
    - generate_lizard_report.py:562-564 (3 line(s)): `sample unavailable`
    - generate_standards_index.py:626-628 (3 line(s)): `sample unavailable`
    - generate_typecheck_report.py:323-324 (2 line(s)): `sample unavailable`
    - scan_code_placeholders.py:404-405 (2 line(s)): `sample unavailable`
    - scan_monkey_patches.py:1246-1247 (2 line(s)): `sample unavailable`
    - seed_standards_prompts.py:149-150 (2 line(s)): `sample unavailable`
    - validate_import_boundaries.py:147-148 (2 line(s)): `sample unavailable`
    - validate_metrics_anchor_stubs.py:128-129 (2 line(s)): `sample unavailable`
    - verify_docs_integrity.py:175-176 (2 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/check_inventory_health.py:285-287 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/diff_standards_index.py:458-460 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:268-270 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:562-564 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_standards_index.py:626-628 (3 line(s)): `def configure_logging(level: str) -> None:`

2. `_parse_timestamp` — 14 duplicate(s)
    - analyze_standards_index_gaps.py:294-300 (7 line(s)): `sample unavailable`
    - generate_anchor_inventory.py:326-332 (7 line(s)): `sample unavailable`
    - generate_dependency_hygiene_report.py:259-265 (7 line(s)): `sample unavailable`
    - generate_import_graph_report.py:160-166 (7 line(s)): `sample unavailable`
    - generate_lizard_report.py:141-147 (7 line(s)): `sample unavailable`
    - render_inventory_views.py:75-81 (7 line(s)): `sample unavailable`
    - validate_markdown_anchors.py:319-325 (7 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/analyze_standards_index_gaps.py:294-300 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_anchor_inventory.py:326-332 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/validate_markdown_anchors.py:319-325 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:259-265 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_import_graph_report.py:160-166 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/check_inventory_health.py:181-187 (7 line(s)): `def parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:141-147 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

3. `build_options` — 12 duplicate(s)
    - analyze_test_hardening.py:148-150 (3 line(s)): `sample unavailable`
    - check_inventory_health.py:294-299 (6 line(s)): `sample unavailable`
    - generate_typecheck_report.py:382-387 (6 line(s)): `sample unavailable`
    - render_inventory_views.py:434-439 (6 line(s)): `sample unavailable`
    - seed_standards_prompts.py:157-168 (12 line(s)): `sample unavailable`
    - validate_inventory.py:665-672 (8 line(s)): `sample unavailable`
    - validate_markdown_anchors.py:332-340 (9 line(s)): `sample unavailable`
    - validate_metrics_anchor_stubs.py:136-137 (2 line(s)): `sample unavailable`
    - verify_docs_integrity.py:183-190 (8 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/check_inventory_health.py:294-299 (6 line(s)): `def build_options(args: argparse.Namespace) -> Options:`
    - .repo_studios/scripts/producers/generate_typecheck_report.py:382-387 (6 line(s)): `def build_options(args: argparse.Namespace) -> Options:`
    - .repo_studios/scripts/producers/render_inventory_views.py:434-439 (6 line(s)): `def build_options(args: argparse.Namespace) -> Options:`

4. `build_paths` — 12 duplicate(s)
    - analyze_test_hardening.py:144-145 (2 line(s)): `sample unavailable`
    - check_inventory_health.py:290-291 (2 line(s)): `sample unavailable`
    - generate_typecheck_report.py:378-379 (2 line(s)): `sample unavailable`
    - render_inventory_views.py:430-431 (2 line(s)): `sample unavailable`
    - scan_code_placeholders.py:175-176 (2 line(s)): `sample unavailable`
    - scan_monkey_patches.py:1250-1251 (2 line(s)): `sample unavailable`
    - seed_standards_prompts.py:153-154 (2 line(s)): `sample unavailable`
    - validate_import_boundaries.py:151-162 (12 line(s)): `sample unavailable`
    - validate_inventory.py:627-662 (36 line(s)): `sample unavailable`
    - validate_markdown_anchors.py:328-329 (2 line(s)): `sample unavailable`
    - validate_metrics_anchor_stubs.py:132-133 (2 line(s)): `sample unavailable`
    - verify_docs_integrity.py:179-180 (2 line(s)): `sample unavailable`

5. `main` — 12 duplicate(s)
    - analyze_test_hardening.py:640-642 (3 line(s)): `sample unavailable`
    - generate_anchor_inventory.py:343-376 (34 line(s)): `sample unavailable`
    - generate_dependency_hygiene_report.py:273-373 (101 line(s)): `sample unavailable`
    - generate_import_graph_report.py:351-414 (64 line(s)): `sample unavailable`
    - generate_lizard_report.py:567-745 (179 line(s)): `sample unavailable`
    - validate_inventory.py:675-747 (73 line(s)): `sample unavailable`
    - verify_docs_integrity.py:633-635 (3 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:446-448 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:513-515 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:403-405 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/analyze_test_hardening.py:640-642 (3 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/verify_docs_integrity.py:633-635 (3 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`

6. `main` — 11 duplicate(s)
    - analyze_standards_index_gaps.py:353-382 (30 line(s)): `sample unavailable`
    - check_inventory_health.py:302-411 (110 line(s)): `sample unavailable`
    - diff_standards_index.py:463-564 (102 line(s)): `sample unavailable`
    - generate_standards_index.py:663-712 (50 line(s)): `sample unavailable`
    - generate_typecheck_report.py:390-494 (105 line(s)): `sample unavailable`
    - scan_code_placeholders.py:434-436 (3 line(s)): `sample unavailable`
    - scan_monkey_patches.py:1322-1329 (8 line(s)): `sample unavailable`
    - seed_standards_prompts.py:446-448 (3 line(s)): `sample unavailable`
    - validate_import_boundaries.py:513-515 (3 line(s)): `sample unavailable`
    - validate_markdown_anchors.py:343-425 (83 line(s)): `sample unavailable`
    - validate_metrics_anchor_stubs.py:403-405 (3 line(s)): `sample unavailable`

7. `prune_history` — 10 duplicate(s)
    - scan_code_placeholders.py:392-401 (10 line(s)): `sample unavailable`
    - scan_monkey_patches.py:1063-1073 (11 line(s)): `sample unavailable`
    - seed_standards_prompts.py:356-366 (11 line(s)): `sample unavailable`
    - validate_import_boundaries.py:406-422 (17 line(s)): `sample unavailable`
    - validate_metrics_anchor_stubs.py:337-353 (17 line(s)): `sample unavailable`
    - verify_docs_integrity.py:563-583 (21 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:406-422 (17 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:337-353 (17 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`
    - .repo_studios/scripts/producers/scan_monkey_patches.py:1063-1073 (11 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:356-366 (11 line(s)): `def prune_history(base_dir: Path, keep: int) -> None:`

8. `_write_latest_artifacts` — 8 duplicate(s)
    - scan_code_placeholders.py:376-389 (14 line(s)): `sample unavailable`
    - scan_monkey_patches.py:1002-1015 (14 line(s)): `sample unavailable`
    - seed_standards_prompts.py:320-334 (15 line(s)): `sample unavailable`
    - validate_import_boundaries.py:372-384 (13 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:376-389 (14 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`
    - .repo_studios/scripts/producers/scan_monkey_patches.py:1002-1015 (14 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:320-334 (15 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:372-384 (13 line(s)): `def _write_latest_artifacts(run_dir: Path, output_dir: Path) -> None:`

9. `prune_old_runs` — 8 duplicate(s)
    - diff_standards_index.py:94-110 (17 line(s)): `sample unavailable`
    - generate_standards_index.py:417-433 (17 line(s)): `sample unavailable`
    - validate_inventory.py:223-235 (13 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/analyze_standards_index_gaps.py:258-277 (20 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:`
    - .repo_studios/scripts/producers/generate_anchor_inventory.py:274-293 (20 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> list[Path]:`
    - .repo_studios/scripts/producers/diff_standards_index.py:94-110 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/generate_standards_index.py:417-433 (17 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`
    - .repo_studios/scripts/producers/validate_inventory.py:223-235 (13 line(s)): `def prune_old_runs(output_dir: Path, *, keep: int, current_run: Path) -> None:`

10. `compose_payload` — 7 duplicate(s)
    - scan_code_placeholders.py:271-297 (27 line(s)): `sample unavailable`
    - scan_monkey_patches.py:885-930 (46 line(s)): `sample unavailable`
    - seed_standards_prompts.py:382-404 (23 line(s)): `sample unavailable`
    - validate_import_boundaries.py:425-454 (30 line(s)): `sample unavailable`
    - validate_inventory.py:480-515 (36 line(s)): `sample unavailable`
    - validate_metrics_anchor_stubs.py:224-260 (37 line(s)): `sample unavailable`
    - verify_docs_integrity.py:405-477 (73 line(s)): `sample unavailable`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.
