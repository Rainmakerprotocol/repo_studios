# Script Inventory Architecture

<!--
	Purpose: this template inventories Repo Studios scripts by functional role so
	agents can migrate legacy assets, document dependencies, and prepare YAML
	catalog entries. Fill sections as you classify each script. Keep formatting
	consistent so automated tooling can parse it later.
-->

## Document Metadata

- **Status:** _Draft_
- **Owner:** _repo_studios_ai_
- **Last Updated:** _2025-10-23_
- **Scope:** `.repo_studios/scripts/`
- **Command Center Reference:** Before updating this blueprint, review `.repo_studios/command_center/README.md` for the current library-integration protocol, guardrails, and duplicate remediation workflow. Link that README in handoffs so agents always land in the command center first.

> Once sections stabilize, convert each completed table to YAML blocks using the
> provided field names. Until then, maintain this Markdown as the human-editable
> source of truth.

### Refactor Loop Blueprint

Use this repeatable micro-cycle for every script remediation pass:

1. **Select & Snapshot** – choose one script, update its entry in this file with current gaps.
2. **Refactor & Harden** – add pruning (cap artifacts at 10 by default), tighten error handling, confirm output paths, and wire or refresh a dedicated Make target in `.repo_studios/Makefile`.
3. **Execute & Validate** – run the script, inspect generated artifacts for formatting, metadata, and agent readability.
4. **Test** – add or extend a matching monolithic test in `.repo_studios/tests/tests_<tier>/` and run it locally.
5. **Document & Log** – refresh this inventory, update supporting docs, and capture notable decisions in `memory-bank/decisionLog.md`.
6. **Repeat** – move on only when the script satisfies pruning, testing, and documentation expectations.

## How to Use This Template

1. Identify the script category (producers, consumers, aggregators, orchestrators, summarizers, utilities).
2. Copy the per-script table skeleton into the category section and populate the
   fields. Leave `TODO` markers for unknown data.
3. Record follow-up actions in the category’s “Next Actions” list to keep
   migration work visible.
4. When ready to export to YAML, reuse the field names exactly as shown.

### Per-Script Table Fields

| Field | Description |
| --- | --- |
| `Script Path` | New canonical location under `.repo_studios/scripts/`. |
| `Description` | One-line summary of responsibilities. |
| `Needed` | `yes/no`; whether the script remains in scope. |
| `Wired` | Current Make target or CLI entry point, if any. |
| `Dependencies` | Internal modules, external tools, or data inputs. |
| `Testing Coverage` | Referenced test modules or `TODO`. |
| `Entry Points` | Invocation patterns (manual, orchestrator, scheduled). |
| `Migration Target` | Planned folder/name after refactor. |
| `Conformance Review` | Standards or lint checks required. |
| `Duplicates` | Related scripts to deduplicate or merge. |
| `Notes` | Miscellaneous context or open questions. |

---

## 1. Script Producers

**Category Purpose:** Baseline data/log generators that gather raw artifacts for downstream analysis.

### Producer Remediation Tracker

| Script | Pruning | Test | Docs | Notes |
| --- | --- | --- | --- | --- |
| analyze_standards_index_gaps.py | DONE | DONE | DONE | Structured artifacts, pruning, tests, Make target, and documentation completed. |
| check_inventory_health.py | DONE | DONE | DONE | Structured JSON/MD/log artifacts with pruning, pytest coverage, and inventory documentation updates. |
| diff_standards_index.py | DONE | DONE | DONE | Status, pruning, tests, and automation doc aligned; fail policy behavior documented. |
| extract_standards_rules.py | N/A | DONE | DONE | Severity normalization + pytest coverage complete; automation doc published 2025-10-23. |
| generate_anchor_inventory.py | DONE | DONE | DONE | Structured report emitter with pruning, Make wiring, and tests now live. |
| generate_dependency_hygiene_report.py | DONE | DONE | DONE | Structured artifacts emit JSON/MD/log bundles with pruning, pytest coverage, automation doc, and Make wiring completed. |
| generate_import_graph_report.py | DONE | DONE | DONE | Structured artifacts emit JSON/MD/log with graph snapshots and pruning; default owned set now `.repo_studios` + `legacy`, docs refreshed. |
| generate_lizard_report.py | DONE | DONE | DONE | Structured artifacts emit under producer reports with pruning and published docs under `docs/automation/generate_lizard_report.md`. JSON extension now vendored at `.repo_studios/vendor/lizard_ext/lizardjson.py`; requirements pin upgraded to lizard 1.18.0 for compatibility. |
| generate_standards_index.py | DONE | DONE | DONE | Structured artifacts with pruning, refreshed pytest, and automation doc now published. |
| generate_typecheck_report.py | DONE | DONE | DONE | Structured artifacts now land under `producer_reports/typecheck_reports/` with pruning, latest links, pytest coverage, and automation doc published. |
| analyze_test_hardening.py | DONE | DONE | DONE | Structured artifacts with pruning in place, pytest `tests/tests_producers/test_analyze_test_hardening.py` covers core flows, Make target `studio-analyze-test-hardening` wired, automation doc at `docs/automation/analyze_test_hardening.md`, CI step in `studio-inventory.yml`. |
| render_inventory_views.py | DONE | DONE | DONE | Structured artifacts now emit under `producer_reports/render_inventory_views/` with pruning, tests, docs, and refreshed legacy stubs. |
| scan_code_placeholders.py | DONE | DONE | DONE | Structured producer emits JSON/MD/log artifacts with pruning, allowlist, and tests/docs landed on 2025-10-23. |
| scan_monkey_patches.py | DONE | DONE | DONE | Structured producer emits JSON/MD/log/matches with pruning & latest links; pytest `tests/tests_producers/test_scan_monkey_patches.py`, Make target, and automation doc landed 2025-10-23. |
| seed_standards_prompts.py | DONE | DONE | DONE | Structured bundle now emits JSON/MD/log/seed artifacts with pruning, pytest coverage, automation doc, and Make target; standards docs aligned with referenced anchors. |
| validate_import_boundaries.py | DONE | DONE | DONE | Structured bundle now emits JSON/MD/log/violations artifacts with pruning, latest links, pytest coverage, automation doc, and wired Make target (`studio-validate-import-boundaries`). |
| validate_inventory.py | DONE | DONE | DONE | Structured validator now emits run bundles with pruning/latest pointers, repo-root path resolution, pytest coverage, and automation doc. |
| validate_markdown_anchors.py | DONE | DONE | TODO | Pruning + tests implemented; document updates still pending. |
| validate_metrics_anchor_stubs.py | DONE | DONE | DONE | Structured bundle now emits JSON/MD/log/missing artifacts with pruning, latest pointers, pytest coverage, automation doc, and Make target (`studio-validate-metrics-anchor-stubs`). |
| verify_docs_integrity.py | DONE | DONE | DONE | Structured docs integrity bundle emits JSON/MD/log/matches artifacts with pruning, pytest coverage, automation doc, and Make target wired. |

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/producers/analyze_standards_index_gaps.py | Scans standards sources for directive-like lines missing from the index. | yes | manual CLI; make studio-analyze-standards-index-gaps | PyYAML; standards_categories.yaml; repo_standards_index.yaml | tests/tests_producers/test_analyze_standards_index_gaps.py | manual | scripts/producers/analyze_standards_index_gaps.py | TODO | none | Emits JSON/MD/TSV artifacts with pruning and legacy JSON compatibility. |
| .repo_studios/scripts/producers/diff_standards_index.py | Diffs two standards index YAML snapshots and classifies rule-level changes. | yes | manual CLI (--fail-on) | PyYAML | TODO | manual | scripts/producers/diff_standards_index.py | TODO | none | Consider wiring to standards CI gate. |
| .repo_studios/scripts/producers/extract_standards_rules.py | Extracts standards rule candidates from markdown marker blocks and headings. | yes | library (imported) | stdlib only; `docs/standards/` markdown corpus | tests/tests_producers/test_extract_standards_rules.py | orchestrated by standards extraction | scripts/producers/extract_standards_rules.py | std-global-python-engineering.md | none | Remediated 2025-10-23: severity normalization, diagnostics, pytest coverage, and automation doc now live. |
| .repo_studios/scripts/producers/generate_standards_index.py | Builds repo_standards_index.yaml with optional heuristic rule ingestion. | yes | manual CLI; env flags | PyYAML; standards_categories.yaml; standards_seed.yaml | tests/tests_producers/test_generate_standards_index.py | manual | scripts/producers/generate_standards_index.py | TODO | none | Emits structured runs (JSON/MD/log/index/raw) with pruning, extraction telemetry, and doc at `docs/automation/generate_standards_index.md`. Local docs stubs added for validation. |
| .repo_studios/scripts/producers/validate_markdown_anchors.py | Validates markdown links and anchors across curated docs. | yes | manual CLI (--glob) | stdlib only | TODO | manual | scripts/producers/validate_markdown_anchors.py | TODO | none | Align slug logic with GitHub renderer. |
| .repo_studios/scripts/producers/generate_anchor_inventory.py | Enumerates H1/H2 markdown slugs and highlights cross-file duplicates. | yes | manual CLI (--json-out); make studio-generate-anchor-inventory | docs tree; optional allowlist file | tests/tests_producers/test_generate_anchor_inventory.py | manual | scripts/producers/generate_anchor_inventory.py | TODO | none | Emits structured JSON/MD/TSV reports with pruning and latest symlinks. |
| .repo_studios/scripts/producers/seed_standards_prompts.py | Produces condensed high-severity standards prompt seeds in text/yaml/json. | yes | manual CLI (--include-warn/--artifact-formats); make studio-seed-standards-prompts | PyYAML; repo_standards_index.yaml | tests/tests_producers/test_seed_standards_prompts.py | manual; Make target | scripts/producers/seed_standards_prompts.py | std-global-python-engineering.md | none | Structured bundles now emit JSON/MD/log/seed artifacts with pruning/history controls and refreshed automation doc. |
| .repo_studios/scripts/producers/generate_dependency_hygiene_report.py | Audits requirements and pyproject deps for pins, VCS refs, and duplicates. | yes | manual CLI (--repo-root/--output-base); make studio-generate-dependency-hygiene | tomllib; requirements*.txt; pyproject.toml | tests/tests_producers/test_generate_dependency_hygiene_report.py | manual | scripts/producers/generate_dependency_hygiene_report.py | std-global-python-engineering.md | none | Structured JSON/MD/log reports land in `.repo_studios/reports/producer_reports/dependency_hygiene_reports/` with pruning, latest pointers, and automation doc coverage. |
| .repo_studios/scripts/producers/generate_import_graph_report.py | Builds adjacency graph of owned packages, surfacing cycles and fan-in/out hotspots. | yes | manual CLI (--owned) | python stdlib; repo source tree | tests/tests_producers/test_generate_import_graph_report.py | manual | scripts/producers/generate_import_graph_report.py | TODO | none | Default owned roots now `.repo_studios` and `legacy`; emits JSON/MD/log artifacts with latest pointers and graph.json under `.repo_studios/reports/producer_reports/import_graph_reports/<ts>/`. |
| .repo_studios/scripts/producers/generate_lizard_report.py | Runs `python -m lizard` with repo thresholds and records offender summaries. | yes | manual CLI (--targets/--ts) | lizard module; repo source tree | tests/tests_producers/test_generate_lizard_report.py | manual | scripts/producers/generate_lizard_report.py | TODO | none | Emits JSON/MD/log plus raw artifacts under `producer_reports/lizard_reports/` with pruning, latest pointers, and doc at `docs/automation/generate_lizard_report.md`. |
| .repo_studios/scripts/producers/generate_typecheck_report.py | Drives mypy runs with repo configs and captures failing snapshots. | yes | make typecheck | mypy; pyproject settings; env toggles | tests/tests_producers/test_generate_typecheck_report.py | manual; orchestrate_health_suite | scripts/producers/generate_typecheck_report.py | std-global-python-engineering.md | none | Outputs structured JSON/MD/log/raw bundles with pruning under `producer_reports/typecheck_reports/` plus latest symlinks and doc at `docs/automation/generate_typecheck_report.md`. |
| .repo_studios/scripts/producers/analyze_test_hardening.py | Evaluates test modules for hardening gaps (missing asserts, mocks, long tests). | yes | CLI (--repo-root); make studio-analyze-test-hardening; GitHub Actions `studio-inventory` workflow | stdlib ast/json/re; repo tests tree | tests/tests_producers/test_analyze_test_hardening.py | manual; Make target; CI | scripts/producers/analyze_test_hardening.py | std-global-python-engineering.md | none | Emits JSON/MD/log bundles under `.repo_studios/reports/producer_reports/test_hardening_reports/` with pruning/latest pointers; automation doc: `docs/automation/analyze_test_hardening.md`. |
| .repo_studios/scripts/producers/scan_code_placeholders.py | Greps source files for placeholder comments like TODO/FIXME to surface debt hotspots. | yes | manual CLI (`--repo-root/--root` options); make studio-scan-code-placeholders | stdlib `argparse`, `json`, `pathlib`, `re` | tests/tests_producers/test_scan_code_placeholders.py | manual | scripts/producers/scan_code_placeholders.py | std-global-python-engineering.md | none | Structured producer (JSON/MD/log/matches TSV) with pruning, allowlist support, automation doc (`docs/automation/scan_code_placeholders.md`), and wired Make target. |
| .repo_studios/scripts/producers/scan_monkey_patches.py | AST + regex inventory of monkey patches with CSV/JSON summaries. | yes | make studio-scan-monkey-patches; manual CLI (--repo-root) | stdlib; optional git blame | tests/tests_producers/test_scan_monkey_patches.py | manual | scripts/producers/scan_monkey_patches.py | std-global-python-engineering.md | none | Remediated 2025-10-23: structured JSON/MD/log/matches TSV bundle under `producer_reports/monkey_patch_scans/` with pruning and latest pointers, pytest coverage, automation doc (`docs/automation/scan_monkey_patches.md`), and Make wiring. |
| .repo_studios/scripts/producers/validate_import_boundaries.py | Enforces layering rules using import graph snapshots and static scans. | yes | manual CLI (--repo-root); legacy alias `check_import_boundaries.py` | `.repo_studios/reports/producer_reports/import_graph_reports/*/graph.json`; `import_rules_allowlist.json`; repo source tree | tests/tests_producers/test_validate_import_boundaries.py | manual; make studio-validate-import-boundaries | scripts/producers/validate_import_boundaries.py | std-global-python-engineering.md | none | Emits structured JSON/MD/log/violations bundle with pruning, latest pointers, pytest coverage, and automation doc (`docs/automation/validate_import_boundaries.md`). |
| .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py | Checks orchestrator metrics links for missing legacy anchor stubs. | yes | manual; make studio-validate-metrics-anchor-stubs | repo markdown tree; docs/api/metrics_orchestrator.md; optional allowlist JSON | tests/tests_producers/test_validate_metrics_anchor_stubs.py | manual; make studio-validate-metrics-anchor-stubs | scripts/producers/validate_metrics_anchor_stubs.py | std-global-markdown-authoring.md | none | Structured JSON/MD/log/missing bundle with pruning + latest pointers, allowlist support, pytest coverage, automation doc (`docs/automation/validate_metrics_anchor_stubs.md`), and Make target created 2025-10-23. |
| .repo_studios/scripts/producers/verify_docs_integrity.py | Verifies governed docs JSON hashes and regenerates navigation tables. | yes | manual CLI (--update); make studio-verify-docs-integrity | stdlib json/hashlib; docs index markdown and governed docs | tests/tests_producers/test_verify_docs_integrity.py | manual | scripts/producers/verify_docs_integrity.py | std-global-markdown-authoring.md | none | Structured run bundles under `.repo_studios/reports/producer_reports/docs_integrity_reports/` (JSON/MD/log/mismatches) with pruning, latest pointers, and automation doc alignment. |
| .repo_studios/scripts/producers/check_inventory_health.py | Validates inventory summary metrics against CI thresholds and baseline deltas. | yes | manual CLI (--summary); make studio-check-inventory-health | inventory summary JSON; `.repo_studios/config/ci_inventory_thresholds.json` | tests/tests_producers/test_check_inventory_health.py | manual; make studio-check-inventory-health | scripts/producers/check_inventory_health.py | std-global-markdown-authoring.md | none | Emits structured JSON/MD/log artifacts with pruning and latest pointers. |
| .repo_studios/scripts/producers/render_inventory_views.py | Renders canonical inventory YAML/Markdown views for quick review. | yes | manual CLI (--schema-root/--output-dir) | PyYAML; inventory schema | tests/tests_producers/test_render_inventory_views.py | manual | scripts/producers/render_inventory_views.py | std-global-markdown-authoring.md | none | Writes run bundles under `.repo_studios/reports/producer_reports/render_inventory_views/` (JSON/MD/log/raw) and refreshes legacy view stubs for downstream compatibility. |
| .repo_studios/scripts/producers/validate_inventory.py | Lightweight schema checks applied to Repo Studios inventory files. | yes | manual CLI (--json) | PyYAML; inventory schema; validator_config.yaml; enums.yaml | tests/tests_producers/test_validate_inventory.py | manual | scripts/producers/validate_inventory.py | std-global-python-engineering.md | none | Emits validation runs in `.repo_studios/reports/producer_reports/validate_inventory/` (JSON/MD/log/issues) with pruning & latest pointers; legacy `--json` continues to surface consolidated findings. |

- **Next Actions:**
- TODO: Backfill testing references for legacy producers that still list `TODO` coverage (e.g., `diff_standards_index.py`).
- TODO: Capture CI wiring for remaining manual-only producers (e.g., `diff_standards_index.py`, `generate_dependency_hygiene_report.py`).
- ACTIVE: Transition documentation updates for `validate_markdown_anchors.py` to close the final docs gap.
- ACTIVE: Audit `extract_standards_rules.py` consumer integrations for pruning needs (if any).
- DONE: Completed refactor loop for `validate_metrics_anchor_stubs.py` (structured artifacts, pruning, tests, docs, automation wiring).
- DONE: Completed refactor loop for `verify_docs_integrity.py` (structured artifacts, pruning, tests, docs, Make target).
- TODO: Evaluate CI gating for `studio-scan-code-placeholders` once placeholder baselines stabilize.

---

## 2. Script Consumers

**Category Purpose:** Single-hop analyzers that operate on a producer’s output to deliver targeted insights.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/consumers/classify_monkey_patches.py | Buckets monkey-patch findings into HIGH/MODERATE/SAFE risk and writes JSON/MD summaries. | yes | manual CLI; orchestrator | `.repo_studios/monkey_patch/*/report.json` | TODO | manual; orchestrate_health_suite | scripts/consumers/classify_monkey_patches.py | TODO | none | Emits `RISK_SUMMARY.(json & md)` beside latest scan. |
| .repo_studios/scripts/consumers/generate_anchor_health_report.py | Captures duplicate H1/H2 anchor slugs across docs tree and writes JSON/MD snapshots. | yes | manual CLI | docs markdown tree; anchor baseline JSON | TODO | manual | scripts/consumers/generate_anchor_health_report.py | TODO | none | Maintains `.repo_studios/anchor_health/` artifacts and latest symlinks. |
| .repo_studios/scripts/consumers/generate_fault_artifacts.py | Converts faulthandler stacks into CSV/MD/manifest artifacts for triage. | yes | manual CLI (--outdir) | `.repo_studios/faulthandler/<ts>/stacks.log`; stdlib csv/json | TODO | manual; orchestrate_health_suite | scripts/consumers/generate_fault_artifacts.py | TODO | none | Normalizes signatures and writes SUMMARY.md plus manifest patches. |
| .repo_studios/scripts/consumers/generate_test_log_health_report.py | Summarizes pytest logs for warnings, slow tests, and JUnit stats. | yes | manual CLI (--logs-dir/--output-base) | `.repo_studios/pytest_logs/*`; defusedxml | TODO | manual; orchestrate_health_suite | scripts/consumers/generate_test_log_health_report.py | TODO | none | Writes report JSON/MD under `.repo_studios/test_health/<ts>/`. |

- **Next Actions:**
- TODO: Record which producers feed each consumer to clarify data lineage before refactoring.

---

## 3. Script Aggregators

**Category Purpose:** Multi-source combiners that blend several producer/consumer artifacts into higher-order insights.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py | Compares latest monkey-patch scan outputs and publishes trend deltas plus markdown summaries. | yes | manual CLI (--base-dir); orchestrator | `.repo_studios/monkey_patch/*/report.json` | TODO | manual; orchestrate_health_suite | scripts/aggregators/analyze_monkey_patch_trends.py | TODO | none | Needs alias or symlink for legacy `compare_monkey_patch_trends.py` step. |
| .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py | Scores files by git churn, AST complexity, and failure density to flag risky hotspots. | yes | manual CLI (--window/--logs-dir); orchestrator | git cli; defusedxml; `.repo_studios/pytest_logs/` | TODO | manual; orchestrate_health_suite | scripts/aggregators/generate_churn_complexity_heatmap.py | TODO | none | Outputs JSON and markdown heatmap in `.repo_studios/churn_complexity/<ts>/`. |

- **Next Actions:**
- TODO: Map each aggregator’s upstream producer/consumer dependencies before we rewire orchestrators.

---

## 4. Script Orchestrators

**Category Purpose:** Entry-point runners that coordinate multiple tiers and manage artifact lifecycles.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/orchestrators/run_batch_cleanup.py | Coordinates Ruff formatting, lint, pytest, and markdown cleanup passes with logging artifacts. | yes | manual CLI (--mode/--target) | Ruff; mypy; pytest; markdownlint-cli | TODO | manual; health suite | scripts/orchestrators/run_batch_cleanup.py | TODO | none | Writes logs to `.repo_studios/cleanup_logs/clean_<ts>.txt`; supports dry-run and refresh-only. |
| .repo_studios/scripts/orchestrators/run_pytest_log_capture.py | Runs pytest with capture, writes per-run logs and summaries, and retries serially on hangs. | yes | manual CLI (pass-through after --) | pytest; defusedxml; optional xdist/cov plugins | TODO | manual; health suite | scripts/orchestrators/run_pytest_log_capture.py | TODO | none | Stores full logs, failure/skip summaries, and manifests under `.repo_studios/pytest_logs/`. |
| .repo_studios/scripts/orchestrators/run_standards_index_cli.py | Exposes repo_standards_index.yaml via list/search/show/stats subcommands. | yes | manual CLI (subcommands) | PyYAML; repo_standards_index.yaml | TODO | manual | scripts/orchestrators/run_standards_index_cli.py | TODO | none | Supports severity/category filters and canonicalizes legacy aliases. |
| .repo_studios/scripts/orchestrators/orchestrate_health_suite.py | Chains health scripts sequentially, recording per-step logs, manifests, and status summaries. | yes | manual CLI (--timestamp/--live) | orchestrated scripts under `.repo_studios`; stdlib subprocess | TODO | manual; CI planned | scripts/orchestrators/orchestrate_health_suite.py | TODO | none | Emits run output under `.repo_studios/health_suite/logs/<ts>/` and never aborts mid-chain. |

- **Next Actions:**
- TODO: Capture orchestrator automation hooks (Make targets, CI jobs) and expected success criteria.

---

## 5. Script Summarizers

**Category Purpose:** Narrative synthesizers that condense suite outputs into executive-ready briefs.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/summarizers/summarize_health_suite.py | Collates health artifacts into a single markdown summary with key deltas. | yes | manual CLI (--timestamp); orchestrator | `.repo_studios/*` artifact directories; JSON/MD reports | TODO | orchestrate_health_suite | scripts/summarizers/summarize_health_suite.py | TODO | none | Writes summary markdown to `.repo_studios/health_suite/health_suite_<ts>.md`. |
| .repo_studios/scripts/summarizers/summarize_standards.py | Logs standards index counts and pending extraction status for pipelines. | yes | manual CLI (--label) | PyYAML; repo_standards_index.yaml; repo_standards_pending.yaml | TODO | manual | scripts/summarizers/summarize_standards.py | TODO | none | Used by standards sync tasks for quick telemetry. |

- **Next Actions:**
- TODO: Define output schema guarantees so downstream agents can parse summaries safely.

---

## 6. Script Utilities

**Category Purpose:** Shared helpers that configure runtime hooks or refresh baseline artifacts.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/utilities/configure_faulthandler_runtime.py | Sitecustomize shim that standardizes FAULT_* environment defaults and warning filters. | yes | sitecustomize import | stdlib only | TODO | import hook | scripts/utilities/configure_faulthandler_runtime.py | TODO | none | Creates faulthandler run dirs and enables stack logging with locking. |
| .repo_studios/scripts/utilities/dump_faulthandler_snapshot.py | One-time faulthandler dump helper that best-effort captures thread stacks. | yes | orchestrate_health_suite step | stdlib faulthandler | TODO | manual; orchestrate_health_suite | scripts/utilities/dump_faulthandler_snapshot.py | TODO | none | Exits zero even if dumps fail to avoid masking original errors. |
| .repo_studios/scripts/utilities/refresh_mypy_baselines.py | Refreshes stored mypy output snapshots for agents and monitoring scopes. | yes | manual CLI | mypy; python interpreter | TODO | manual | scripts/utilities/refresh_mypy_baselines.py | TODO | none | Overwrites baseline text files with latest mypy run plus timestamp footer. |

- **Next Actions:**
- TODO: Scope shared helpers like the planned `prune_logs` utility.
- TODO: Capture default Make/CI wiring for the migrated utilities as they come online.

---

## 7. Script Undefined / Triage

**Category Purpose:** Scripts whose roles are unclear or pending
classification—capture them here before routing to a category above.

| Script Path | Legacy Name | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ | _TODO_ |

- **Next Actions:**
- TODO: Identify automation hooks for guardrail scripts (Make targets, CI checks).
- TODO: Determine baseline regression suites for guardrail utilities.

---

## Cross-Cutting Follow-Ups

- TODO: Document YAML export process once first category is complete.
- TODO: Link populated tables to inventory catalog entries.

## Open Questions

- TODO: Decide on baseline testing expectations per category.

## Appendix: YAML Mapping Placeholder

> When ready, replicate the table headers as YAML keys. Example skeleton:
>
> ```yaml
> - script_path: .repo_studios/scripts/producers/example.py
>   legacy_name: repo_scripts/example_producer.py
>   description: Baseline metrics producer.
>   needed: true
>   wired: make studio-example
>   dependencies:
>     internal_paths: []
>     external_tools: []
>   testing_coverage: tests/example/test_example_collector.py
>   entry_points:
>     - manual
>   migration_target: scripts/producers/example.py
>   conformance_review: std-global-python-engineering.md
>   duplicates: []
>   notes: Pending log pruning helper.
> ```
