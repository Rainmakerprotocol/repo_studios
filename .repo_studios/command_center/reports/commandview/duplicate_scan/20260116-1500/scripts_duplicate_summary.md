<!-- markdownlint-disable MD013 -->

# Duplicate Scan Summary

## Overview

- Target directory: `.repo_studios/scripts`
- Python files scanned: 44
- Functions analysed: 884
- Scanner groups detected: 55
- Producer groups referenced: 53
- Scanner groups matched to producers: 36
- Scanner-only groups: 19

## Inputs

- Analysis dataset: `.repo_studios/scripts/scripts_index/scripts_analysis-20260116-0206.json`
- Run generated with scan_duplicates CLI

## Top Duplicate Offenders

1. `configure_logging` — 17 duplicate(s)
    - producers/generate_typecheck_report.py:758-764 (7 line(s)): `sample unavailable`
    - producers/scan_code_placeholders.py:702-708 (7 line(s)): `sample unavailable`
    - .repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py:76-78 (3 line(s)): `def _configure_logging(log_level: str) -> None:`
    - .repo_studios/scripts/utilities/validate_healthview_agent_workflow_spec.py:42-44 (3 line(s)): `def _configure_logging(log_level: str) -> None:`
    - .repo_studios/scripts/producers/analyze_test_hardening.py:251-257 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:181-187 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/check_inventory_health.py:368-370 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/diff_standards_index.py:474-476 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:616-618 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_standards_index.py:639-641 (3 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/aggregators/aggregate_docs_health_signals.py:266-275 (10 line(s)): `def _configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/collect_faulthandler_reports.py:193-199 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_undocumented_logic_report.py:222-230 (9 line(s)): `def _configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:377-384 (8 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_import_graph_report.py:591-598 (8 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/generate_typecheck_report.py:758-764 (7 line(s)): `def configure_logging(level: str) -> None:`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:702-708 (7 line(s)): `def configure_logging(level: str) -> None:`

2. `main` — 16 duplicate(s)
    - producers/generate_lizard_report.py:621-839 (219 line(s)): `sample unavailable`
    - producers/validate_inventory.py:693-775 (83 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:466-468 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:520-522 (3 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/aggregators/aggregate_docs_health_signals.py:1182-1192 (11 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/consumers/generate_fault_artifacts.py:755-765 (11 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/consumers/generate_test_log_health_report.py:823-835 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/collect_faulthandler_reports.py:603-613 (11 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/generate_anchor_inventory.py:1092-1104 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/generate_code_doc_churn_report.py:902-914 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/generate_doc_index.py:1269-1281 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/generate_undocumented_logic_report.py:991-1003 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:794-804 (11 line(s)): `def main(argv: list[str] | None = None) -> int:`
    - .repo_studios/scripts/utilities/refresh_mypy_baselines.py:615-625 (11 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/analyze_test_hardening.py:1118-1130 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`
    - .repo_studios/scripts/producers/verify_docs_integrity.py:987-999 (13 line(s)): `def main(argv: Sequence[str] | None = None) -> int:`

3. `prune_history` — 13 duplicate(s)
    - producers/seed_standards_prompts.py:359-373 (15 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:407-421 (15 line(s)): `sample unavailable`
    - producers/validate_inventory.py:235-249 (15 line(s)): `sample unavailable`
    - .repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py:508-536 (29 line(s)): `def _prune_history(base: Path, current: Path, keep: int, *, logger: logging.Logger | None) -> list[Path]:`
    - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py:655-681 (27 line(s)): `def _prune_history(base: Path, current: Path, keep: int, *, logger: logging.Logger | None) -> list[Path]:`
    - .repo_studios/scripts/consumers/classify_monkey_patches.py:574-604 (31 line(s)): `def _prune_history(base: Path, *, keep: int | None, current: Path, logger: logging.Logger | None) -> list[Path]:`
    - .repo_studios/scripts/consumers/generate_fault_artifacts.py:565-593 (29 line(s)): `def _prune_history(root: Path, keep: int | None, current: Path, *, logger: logging.Logger | None) -> list[Path]:`
    - .repo_studios/scripts/consumers/generate_test_log_health_report.py:672-699 (28 line(s)): `def _prune_history(base: Path, keep: int | None, current: Path, *, logger: logging.Logger | None) -> list[Path]:`
    - .repo_studios/scripts/producers/analyze_test_hardening.py:1007-1033 (27 line(s)): `def prune_history(`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:573-597 (25 line(s)): `def prune_history(`
    - .repo_studios/scripts/producers/seed_standards_prompts.py:359-373 (15 line(s)): `def prune_history(`
    - .repo_studios/scripts/producers/validate_import_boundaries.py:407-421 (15 line(s)): `def prune_history(`
    - .repo_studios/scripts/producers/validate_inventory.py:235-249 (15 line(s)): `def prune_history(`

4. `_parse_timestamp` — 12 duplicate(s)
    - producers/scan_code_placeholders.py:593-613 (21 line(s)): `sample unavailable`
    - utilities/refresh_mypy_baselines.py:178-198 (21 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/generate_dependency_hygiene_report.py:360-374 (15 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_import_graph_report.py:329-343 (15 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/summarizers/summarize_health_suite.py:144-153 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/summarizers/summarize_standards.py:151-160 (10 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/check_inventory_health.py:214-220 (7 line(s)): `def parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_lizard_report.py:145-151 (7 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_anchor_inventory.py:836-853 (18 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/generate_doc_index.py:925-945 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:593-613 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`
    - .repo_studios/scripts/utilities/refresh_mypy_baselines.py:178-198 (21 line(s)): `def _parse_timestamp(raw: str | None) -> datetime:`

5. `build_paths` — 11 duplicate(s)
    - producers/validate_markdown_anchors.py:514-523 (10 line(s)): `sample unavailable`
    - producers/verify_docs_integrity.py:286-295 (10 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/generate_typecheck_report.py:850-859 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/utilities/refresh_mypy_baselines.py:300-309 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/analyze_test_hardening.py:226-235 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/collect_faulthandler_reports.py:162-171 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:250-259 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/scan_monkey_patches.py:1836-1847 (12 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/validate_markdown_anchors.py:514-523 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py:190-199 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`
    - .repo_studios/scripts/producers/verify_docs_integrity.py:286-295 (10 line(s)): `def build_paths(args: argparse.Namespace) -> Paths:`

6. `configure_logging` — 8 duplicate(s)
    - producers/check_inventory_health.py:368-370 (3 line(s)): `sample unavailable`
    - producers/diff_standards_index.py:474-476 (3 line(s)): `sample unavailable`
    - producers/generate_lizard_report.py:616-618 (3 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:639-641 (3 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:158-159 (2 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:150-151 (2 line(s)): `sample unavailable`
    - summarizers/summarize_health_suite.py:173-174 (2 line(s)): `sample unavailable`
    - summarizers/summarize_standards.py:163-164 (2 line(s)): `sample unavailable`

7. `main` — 8 duplicate(s)
    - orchestrators/healthview/run_healthview_agent_loop.py:441-452 (12 line(s)): `sample unavailable`
    - producers/check_inventory_health.py:385-493 (109 line(s)): `sample unavailable`
    - producers/diff_standards_index.py:479-586 (108 line(s)): `sample unavailable`
    - producers/generate_standards_index.py:699-771 (73 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:466-468 (3 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:520-522 (3 line(s)): `sample unavailable`
    - utilities/dump_faulthandler_snapshot.py:251-269 (19 line(s)): `sample unavailable`
    - utilities/validate_healthview_agent_workflow_spec.py:184-204 (21 line(s)): `sample unavailable`

8. `build_paths` — 7 duplicate(s)
    - producers/check_inventory_health.py:373-374 (2 line(s)): `sample unavailable`
    - producers/render_inventory_views.py:425-426 (2 line(s)): `sample unavailable`
    - producers/seed_standards_prompts.py:162-174 (13 line(s)): `sample unavailable`
    - producers/validate_import_boundaries.py:154-168 (15 line(s)): `sample unavailable`
    - producers/validate_inventory.py:645-680 (36 line(s)): `sample unavailable`
    - summarizers/summarize_health_suite.py:177-178 (2 line(s)): `sample unavailable`
    - summarizers/summarize_standards.py:167-168 (2 line(s)): `sample unavailable`

9. `_timestamp_slug` — 6 duplicate(s)
    - producers/generate_lizard_report.py:154-155 (2 line(s)): `sample unavailable`
    - summarizers/summarize_health_suite.py:156-157 (2 line(s)): `sample unavailable`
    - .repo_studios/scripts/producers/collect_faulthandler_reports.py:212-223 (12 line(s)): `def _timestamp_slug(moment: datetime) -> str:`
    - .repo_studios/scripts/producers/scan_code_placeholders.py:616-627 (12 line(s)): `def _timestamp_slug(moment: datetime) -> str:`
    - .repo_studios/scripts/producers/generate_test_coverage_inventory.py:198-207 (10 line(s)): `def _timestamp_slug(timestamp: datetime) -> str:`
    - .repo_studios/scripts/producers/validate_markdown_anchors.py:226-235 (10 line(s)): `def _format_run_slug(ts: datetime) -> str:`

10. `_write_json` — 6 duplicate(s)
    - utilities/configure_faulthandler_runtime.py:260-264 (5 line(s)): `sample unavailable`
    - utilities/dump_faulthandler_snapshot.py:244-248 (5 line(s)): `sample unavailable`
    - .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py:641-652 (12 line(s)): `def _write_json(path: Path, payload: dict[str, Any]) -> Path:`
    - .repo_studios/scripts/producers/collect_test_log_reports.py:367-370 (4 line(s)): `def _write_json(path: Path, payload: dict[str, object]) -> Path:`
    - .repo_studios/scripts/utilities/configure_faulthandler_runtime.py:260-264 (5 line(s)): `def _write_json(path: Path, payload: Dict[str, object]) -> None:`
    - .repo_studios/scripts/utilities/dump_faulthandler_snapshot.py:244-248 (5 line(s)): `def _write_json(path: Path, payload: Dict[str, object]) -> None:`

## Next Steps

- Review scanner-only groups to decide whether they warrant new producer tracking.
- Prioritise groups with high duplicate counts or similarity for extraction.

<!-- markdownlint-enable MD013 -->
