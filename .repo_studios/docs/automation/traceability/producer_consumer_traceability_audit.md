# Producer → Consumer Traceability Audit (Draft 2025-11-24)

**Last updated:** 2025-11-24
<!-- markdownlint-disable MD013 -->

## Overview

- Confirm which producer bundles feed hardened consumers and document the traceability metadata each stage preserves.
- Surface producers that currently lack a downstream consumer so we can plan targeted summaries ahead of the aggregator refactor pass.
- Provide recommendations for how aggregators should source data now that consumer bundles expose provenance.

## Evidence Sources

- `.repo_studios/scripts/script_inventory_architecture.md` producer/consumer catalog (2025-11-24).
- Hardened consumer implementations and tests under `.repo_studios/scripts/consumers/` and `.repo_studios/tests/tests_consumers/`.
- Structured producer bundles within `.repo_studios/reports/producer_reports/` generated during the recent remediation loop.

## Active Producer → Consumer Pairings

| Producer Script & Artifact Root | Consumer Script & Outputs | Traceability Controls | Notes |
| --- | --- | --- | --- |
| `.repo_studios/scripts/producers/scan_monkey_patches.py` → `.repo_studios/reports/producer_reports/monkey_patch_scans/<run>/matches.json` | `.repo_studios/scripts/consumers/classify_monkey_patches.py` → `.repo_studios/reports/consumer_reports/monkey_patch_risk/monkey_patch_risk-<ts>/{summary.json, SUMMARY.md, bundle_summary.json}` (legacy `RISK_SUMMARY.*` mirrored into the scan directory) | Consumer reuses structured `matches.json`, threads producer metadata into `run_metadata`, records provenance in `bundle_summary.json`, and updates `latest_*.json/md` pointers with retention pruning (`--artifacts-to-keep`). | Falls back to legacy `.repo_studios/monkey_patch/<run>/report.json` when structured bundles are unavailable while keeping compatibility copies in the scan directory. |
| `.repo_studios/scripts/producers/generate_anchor_inventory.py` → `.repo_studios/reports/producer_reports/anchor_inventory_reports/` (`report.json`, `latest_report.json`) | `.repo_studios/scripts/consumers/generate_anchor_health_report.py` → `anchor_report.json`, `anchor_report.md`, `clusters.tsv`, `runs.log`, plus latest hardlinks | `anchor_report.json` records `source="inventory"` and `inventory_report` path, while markdown output adds Source References and the run log captures each execution timestamp. | Default retention keeps 10 timestamped runs via `--artifacts-to-keep`; full fallback docs scan is retained as `source="scan"` when inventories are missing. |
| `.repo_studios/scripts/producers/collect_faulthandler_reports.py` → `.repo_studios/reports/producer_reports/faulthandler_reports/<run>/report.json` | `.repo_studios/scripts/consumers/generate_fault_artifacts.py` → `summary.json`, `SUMMARY.md`, `stacks.csv`, `dumps/combined.txt` under `.repo_studios/reports/consumer_reports/fault_artifacts/<bundle>/` | Consumer bundle embeds `source` (`producer` or `legacy`), `source_report`, and `run_dir` in `summary.json`; markdown summary appends Source References to every emitted artifact. | Retention enforced via `--artifacts-to-keep` (default 10). Bundled outputs store resolved paths so aggregators can dereference raw stacks when needed. |
| `.repo_studios/scripts/producers/collect_test_log_reports.py` → `.repo_studios/reports/producer_reports/test_log_reports/<run>/report.json` | `.repo_studios/scripts/consumers/generate_test_log_health_report.py` → `report.json`, `report.md`, `bundle_summary.json` under `.repo_studios/reports/consumer_reports/test_log_health_reports/<ts>/` | `bundle_summary.json` captures `source`, `producer_report`, resolved logs directory, and artifact locations; markdown builds a Source References section mirroring the metadata. | Defaults to keeping 10 runs via `--artifacts-to-keep`. Falls back to raw logs when producer bundles are absent, recording the discovered log path in the metadata. |

## Unpaired Producers & Proposed Consumers

| Producer Script | Current Output Focus | Observation | Proposed Consumer Concept |
| --- | --- | --- | --- |
| `.repo_studios/scripts/producers/generate_dependency_hygiene_report.py` | Flags unpinned, VCS, and duplicate dependencies with JSON/MD/log bundles. | No consumer converts the detailed findings into an actionable triage summary. | `summarize_dependency_hygiene.py` — rank high-risk packages, highlight remediation owners, emit dashboard-ready markdown. |
| `.repo_studios/scripts/producers/generate_import_graph_report.py` | Provides `graph.json` plus hotspot stats for owned packages. | Aggregators currently skip import fan-in/out surfacing, leaving topology drift unmonitored. | `summarize_import_hotspots.py` — surface top fan-in/out modules, cycles, and new edges for governance review. |
| `.repo_studios/scripts/producers/generate_lizard_report.py` | Captures complexity deltas and offender lists. | Complexity data never gets condensed for operators; only raw producer bundles exist. | `generate_complexity_health_report.py` — identify highest-complexity modules, trend against previous runs, and attach refactoring guidance. |
| `.repo_studios/scripts/producers/generate_test_coverage_inventory.py` | Emits per-file function coverage metrics. | Coverage gaps remain buried in CSV/JSON, limiting fast regression detection. | `summarize_test_coverage_gaps.py` — flag modules below thresholds, list uncovered functions, and attach delegate actions. |
| `.repo_studios/scripts/producers/analyze_test_hardening.py` | Scores tests for asserts, mocks, and latency issues. | Consumers/aggregators do not expose the findings, so hardening regressions lack visibility. | `generate_test_hardening_report.py` — grade modules by hardening score, bubble up top offenders, and log suggested remediations. |
| `.repo_studios/scripts/producers/scan_code_placeholders.py` | Captures placeholder totals, allowlist counts, and zero-match baselines in JSON/MD/log bundles. | Weekly governance entries track results, but no consumer summarizes deltas or allowlist churn for operators. | `summarize_placeholder_debt.py` — diff successive runs, flag new placeholders, highlight expiring allowlist entries, and embed enforcement readiness cues. |
| `.repo_studios/scripts/producers/generate_doc_index.py` | Planned repo-wide documentation index capturing headings, links, and descriptions per markdown file. | Implementation pending; no consumer yet, but output will underpin AI documentation navigation. | Future consumer TBD — likely `summarize_doc_index_usage.py` to surface top navigation queries and stale descriptions once the producer ships. |

## Recommendations

1. Treat the four hardened consumer bundles as the canonical inputs for upcoming aggregator rewires; aggregators should ingest the consumer summary JSON (`summary.json`, `anchor_report.json`, `bundle_summary.json`, `RISK_SUMMARY.json`) instead of raw producer data.
1. Schedule design spikes for the six proposed consumers so each high-signal producer has an operator-facing summary before aggregator modernization begins; fold the placeholder debt summary into the same review so governance metrics stay synchronized.
1. Consider adding explicit history pruning to `classify_monkey_patches.py` (or relocating consumer outputs into the consumer_reports tree) to mirror the retention guarantees implemented in the other consumers.
1. Once the new consumers are scoped, update `.repo_studios/scripts/script_inventory_architecture.md` and the decision log with ownership, testing expectations, and wiring plans to keep traceability current, threading placeholder scan governance milestones into the same ledger.

<!-- markdownlint-enable MD013 -->
