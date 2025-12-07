# Script Inventory Architecture

<!--
	Purpose: this template inventories Repo Studios scripts by functional role so
	agents can migrate legacy assets, document dependencies, and prepare YAML
	catalog entries. Fill sections as you classify each script. Keep formatting
	consistent so automated tooling can parse it later.

	Alignment Notes:
	- Advance remediation strictly in tier order: producers → consumers → aggregators → orchestrators
	(then summarizers when applicable) so downstream tables always reference hardened upstream assets.
	- Touch one script at a time per tier. Snapshot current gaps, refactor, test, document, and only
	then proceed to the next script to prevent partial migrations.
	- While refactoring, prioritize artifact pruning, schema cleanliness, and markdown lint health
	to keep generated outputs readable and debt-free.
	- When adding new needs, capture them here first, then thread them into the refactor loop so
	the source remains the authoritative backlog.
	- Preserve compatibility shims until the successor artifacts have passed validation and handoff
	reviews.
	- Only after a script’s remediation checklist is satisfied do we run it end-to-end, inspect the
	generated artifacts against expectations, and capture deltas for follow-up.
	- After each validation run, request human review of the outputs and gather feedback—many reports
	target human stakeholders, so operator sign-off remains essential.
-->

<!-- markdownlint-disable MD010 MD013 MD029 -->

## Document Metadata

- **Status:** _Draft_
- **Owner:** _repo_studios_ai_
- **Last Updated:** _2025-12-05_
- **Scope:** `.repo_studios/scripts/`
- **Command Center Reference:** Before updating this blueprint, review
  `.repo_studios/command_center/README.md` for the current library-integration protocol,
  guardrails, and duplicate remediation workflow. Link that README in handoffs so agents always
  land in the command center first.

> Once sections stabilize, convert each completed table to YAML blocks using the
> provided field names. Until then, maintain this Markdown as the human-editable
> source of truth.

### Refactor Loop Blueprint

Use this repeatable micro-cycle for every script remediation pass:

1. **Select & Snapshot** – choose one script, update its entry in this file with current gaps.
2. **Refactor & Harden** – add pruning (cap artifacts at 10 by default), tighten error handling,
  confirm output paths, and wire or refresh a dedicated Make target in `.repo_studios/Makefile`.
3. **Execute & Validate** – run the script, inspect generated artifacts for formatting, metadata,
  and agent readability.
4. **Test** – add or extend a matching monolithic test in `.repo_studios/tests/tests_<tier>/` and
  run it locally.
5. **Document & Log** – refresh this inventory, update supporting docs, and capture notable
  decisions in `.repo_studios/command_center/docs/decision_log.md`.
6. **Repeat** – move on only when the script satisfies pruning, testing, and documentation expectations.

## How to Use This Template

1. Identify the script category (producers, consumers, aggregators, orchestrators, summarizers,
utilities).
2. Copy the per-script table skeleton into the category section and populate the
fields. Leave `TODO` markers for unknown data.
3. Record follow-up actions in the category’s “Next Actions” list to keep
migration work visible.
4. When ready to export to YAML, reuse the field names exactly as shown.

### YAML Export Process

Follow this checklist once a section’s tables are fully populated:

1. **Snapshot Markdown** – Confirm the table reflects the latest remediation status, standards references, and notes. Resolve any lingering `TODO` markers or annotate them with explicit follow-up owners/dates.
2. **Normalize Field Names** – Ensure column headers match the canonical keys in the appendix (`script_path`, `description`, `needed`, etc.) so Markdown → YAML translation is lossless.
3. **Generate YAML Draft** – Copy the appendix skeleton, duplicate the row for each script, and transpose the table values verbatim. Preserve booleans (`true/false`) and lists (`[]`) without additional prose.
4. **Validate Structure** – Run a YAML linter or paste into an editor with YAML validation to catch indentation and quoting issues. Verify multi-line notes are pipe-indented (`|`) when needed.
5. **Stage Sidecar File** – Save the YAML alongside this document (for example `script_inventory_architecture.yaml`) and link it in the relevant category’s “Next Actions” or status update so orchestration tooling can locate it.
6. **Backfill History** – Note the export in this Markdown (date + filename) and flag any automation or CI steps that should ingest the new YAML artifact.

Repeat the process whenever a category’s content materially changes so the YAML stays aligned with the Markdown source of truth.

### Inventory Catalog Linkage

Use these steps to keep this inventory aligned with the canonical entries in `.repo_studios/inventory_schema/scripts/`:

1. **Locate the Catalog Record** – Search the appropriate catalog file (`health_reports.yaml`, `standards.yaml`, `utilities.yaml`, etc.) for the script’s `path` value and capture the associated `id`.
2. **Annotate Table Notes** – Append `Catalog: <catalog_id>.` to the script’s `Notes` cell so readers (and automation) can trace directly back to the inventory schema.
3. **Flag Gaps Explicitly** – When a script lacks a catalog record, note `Catalog: pending` (optionally include the intended namespace) to keep the backlog visible.
4. **Sync After Updates** – Anytime the catalog entry changes (new id, status, or metadata), refresh the note here so the Markdown table mirrors the YAML source of truth.

This lightweight linkage keeps the Markdown tables navigable for humans while maintaining parity with the structured inventory.

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
| generate_doc_index.py | DONE | DONE | DONE | Repo-wide documentation index now emits metrics/advisories, JSON + Markdown bundle with YAML/CSV sections, standalone CSV pointer, retention=1, and database sink placeholder logging. |
| generate_dependency_hygiene_report.py | DONE | DONE | DONE | Structured artifacts emit JSON/MD/log bundles with pruning, pytest coverage, automation doc, and Make wiring completed. |
| collect_faulthandler_reports.py | DONE | DONE | DONE | Structured faulthandler bundle emits JSON/MD/CSV alongside combined logs with pruning, latest pointers, automation doc (`docs/automation/collect_faulthandler_reports.md`), and Make target `studio-collect-faulthandler-reports`. |
| collect_test_log_reports.py | DONE | DONE | DONE | Structured pytest log producer emits JSON/MD/CSV/log bundles with pruning, latest pointers, pytest coverage (`tests/tests_producers/test_collect_test_log_reports.py`), automation doc (`docs/automation/collect_test_log_reports.md`), and Make target `studio-collect-test-log-reports`. |
| generate_import_graph_report.py | DONE | DONE | DONE | Structured artifacts emit JSON/MD/log with graph snapshots and pruning; default owned set now `.repo_studios` + `legacy`, docs refreshed. |
| generate_lizard_report.py | DONE | DONE | DONE | Structured artifacts emit under producer reports with pruning and published docs under `docs/automation/generate_lizard_report.md`. JSON extension now vendored at `.repo_studios/vendor/lizard_ext/lizardjson.py`; requirements pin upgraded to lizard 1.18.0 for compatibility. |
| generate_standards_index.py | DONE | DONE | DONE | Structured artifacts with pruning, refreshed pytest, and automation doc now published. |
| generate_typecheck_report.py | DONE | DONE | DONE | Structured artifacts now land under `producer_reports/typecheck_reports/` with pruning, latest links, pytest coverage, and automation doc published. |
| generate_test_coverage_inventory.py | DONE | DONE | DONE | Coverage XML ingester emits per-file function coverage bundles (JSON/Markdown/CSV/log) with pruning, pytest coverage, and automation doc dated 2025-11-23. |
| analyze_test_hardening.py | DONE | DONE | DONE | Structured artifacts with pruning in place, pytest `tests/tests_producers/test_analyze_test_hardening.py` covers core flows, Make target `studio-analyze-test-hardening` wired, automation doc at `docs/automation/analyze_test_hardening.md`, CI step in `studio-inventory.yml`. |
| render_inventory_views.py | DONE | DONE | DONE | Structured artifacts now emit under `producer_reports/render_inventory_views/` with pruning, tests, docs, and refreshed legacy stubs. |
| scan_code_placeholders.py | DONE | DONE | DONE | Structured producer emits JSON/MD/log artifacts with pruning, allowlist, and tests/docs landed on 2025-10-23. |
| scan_monkey_patches.py | DONE | DONE | DONE | Structured producer emits JSON/MD/log/matches with pruning & latest links; pytest `tests/tests_producers/test_scan_monkey_patches.py`, Make target, and automation doc landed 2025-10-23. |
| seed_standards_prompts.py | DONE | DONE | DONE | Structured bundle now emits JSON/MD/log/seed artifacts with pruning, pytest coverage, automation doc, and Make target; standards docs aligned with referenced anchors. |
| validate_import_boundaries.py | DONE | DONE | DONE | Structured bundle now emits JSON/MD/log/violations artifacts with pruning, latest links, pytest coverage, automation doc, and wired Make target (`studio-validate-import-boundaries`). |
| validate_inventory.py | DONE | DONE | DONE | Structured validator now emits run bundles with pruning/latest pointers, repo-root path resolution, pytest coverage, and automation doc. |
| validate_markdown_anchors.py | DONE | DONE | DONE | Pruning + tests implemented; documentation published at `docs/automation/validate_markdown_anchors.md`. |
| validate_metrics_anchor_stubs.py | DONE | DONE | DONE | Structured bundle now emits JSON/MD/log/missing artifacts with pruning, latest pointers, pytest coverage, automation doc, and Make target (`studio-validate-metrics-anchor-stubs`). |
| verify_docs_integrity.py | DONE | DONE | DONE | Structured docs integrity bundle emits JSON/MD/log/matches artifacts with pruning, pytest coverage, automation doc, and Make target wired. |
| generate_code_doc_churn_report.py | DONE | DONE | DONE | Structured JSON/MD/TSV bundle with retention and latest pointers, git metadata enrichment, pytest coverage, and automation doc at `docs/automation/generate_code_doc_churn_report.md`; Make wiring TBD. |

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/producers/analyze_standards_index_gaps.py | Scans standards sources for directive-like lines missing from the index. | yes | manual CLI; make studio-analyze-standards-index-gaps | PyYAML; standards_categories.yaml; reports/producer_reports/standards_index_reports/latest_index.yaml | tests/tests_producers/test_analyze_standards_index_gaps.py | manual | scripts/producers/analyze_standards_index_gaps.py | TODO | none | Emits JSON/MD/TSV artifacts with pruning and legacy JSON compatibility. Catalog: scripts.standards.index_gap. |
| .repo_studios/scripts/producers/diff_standards_index.py | Diffs two standards index YAML snapshots and classifies rule-level changes. | yes | manual CLI (--fail-on); make studio-diff-standards-index (requires `old=<path>` `new=<path>` variables) | PyYAML | tests/tests_producers/test_diff_standards_index.py | manual; Make target | scripts/producers/diff_standards_index.py | TODO | none | Make target added 2025-11-23; production wiring should supply snapshot paths. Consider wiring to standards CI gate. Catalog: scripts.standards.index_diff. |
| .repo_studios/scripts/producers/extract_standards_rules.py | Extracts standards rule candidates from markdown marker blocks and headings. | yes | library (imported) | stdlib only; `docs/standards/` markdown corpus | tests/tests_producers/test_extract_standards_rules.py | orchestrated by standards extraction | scripts/producers/extract_standards_rules.py | std-global-python-engineering.md | none | Remediated 2025-10-23: severity normalization, diagnostics, pytest coverage, and automation doc now live; consumer audit 2025-11-23 confirmed `generate_standards_index.py` run pruning covers artifacts and `summarize_standards.py` is read-only. Catalog: scripts.standards.extraction. |
| .repo_studios/scripts/producers/generate_standards_index.py | Builds the standards index bundle and refreshes `latest_index.yaml`, with optional heuristic rule ingestion. | yes | manual CLI; env flags | PyYAML; standards_categories.yaml; standards_seed.yaml | tests/tests_producers/test_generate_standards_index.py | manual | scripts/producers/generate_standards_index.py | TODO | none | Emits structured runs (JSON/MD/log/index/raw) with pruning, extraction telemetry, and doc at `docs/automation/generate_standards_index.md`. Local docs stubs added for validation; canonical pointer lives at `reports/producer_reports/standards_index_reports/latest_index.yaml`. Catalog: scripts.standards.build_index. |
| .repo_studios/scripts/producers/validate_markdown_anchors.py | Validates markdown links and anchors across curated docs. | yes | manual CLI (--glob) | stdlib only | tests/tests_producers/test_validate_markdown_anchors.py | manual | scripts/producers/validate_markdown_anchors.py | TODO | none | Align slug logic with GitHub renderer. Catalog: scripts.utilities.check_markdown_anchors. |
| .repo_studios/scripts/producers/generate_anchor_inventory.py | Enumerates H1/H2 markdown slugs, highlights cross-file duplicates, and surfaces per-document anchor coverage gaps. | yes | manual CLI (--json-out); make studio-generate-anchor-inventory | docs tree; optional allowlist file | tests/tests_producers/test_generate_anchor_inventory.py | manual | scripts/producers/generate_anchor_inventory.py | std-global-markdown-authoring.md | none | Structured JSON/MD/TSV/CSV bundle with retention pruning, latest pointers, per-document metrics, and automation doc at `.repo_studios/docs/automation/generate_anchor_inventory.md`. Catalog: scripts.health.anchor_inventory. |
| .repo_studios/scripts/producers/seed_standards_prompts.py | Produces condensed high-severity standards prompt seeds in text/yaml/json. | yes | manual CLI (--include-warn/--artifact-formats); make studio-seed-standards-prompts | PyYAML; reports/producer_reports/standards_index_reports/latest_index.yaml | tests/tests_producers/test_seed_standards_prompts.py | manual; Make target | scripts/producers/seed_standards_prompts.py | std-global-python-engineering.md | none | Structured bundles now emit JSON/MD/log/seed artifacts with pruning/history controls and refreshed automation doc. Catalog: scripts.standards.prompt_seed. |
| .repo_studios/scripts/producers/generate_dependency_hygiene_report.py | Audits requirements and pyproject deps for pins, VCS refs, and duplicates. | yes | manual CLI (--repo-root/--output-base); make studio-generate-dependency-hygiene | tomllib; requirements*.txt; pyproject.toml | tests/tests_producers/test_generate_dependency_hygiene_report.py | manual; Make target | scripts/producers/generate_dependency_hygiene_report.py | std-global-python-engineering.md | none | Structured JSON/MD/log reports land in `.repo_studios/reports/producer_reports/dependency_hygiene_reports/` with pruning, latest pointers, and automation doc coverage. Catalog: scripts.health.dep_hygiene_report. |
| .repo_studios/scripts/producers/collect_faulthandler_reports.py | Collects faulthandler run directories into structured JSON/MD/CSV/log bundles with pruning and latest pointers. | yes | manual CLI (--runs-dir/--output-dir); make studio-collect-faulthandler-reports | `.repo_studios/faulthandler/<ts>/` runs; `utilities.fault_run_analysis` | tests/tests_producers/test_collect_faulthandler_reports.py | manual; orchestrate_health_suite | scripts/producers/collect_faulthandler_reports.py | TODO | none | Automation doc `docs/automation/collect_faulthandler_reports.md` published; Make target `studio-collect-faulthandler-reports` mirrors producer output into `.repo_studios/reports/producer_reports/faulthandler_reports/`. Catalog: scripts.health.collect_faulthandler_reports. |
| .repo_studios/scripts/producers/collect_test_log_reports.py | Collects pytest log runs into structured JSON/MD/CSV/log bundles with retention pruning and latest pointers. | yes | manual CLI (--logs-dir/--logs-run); make studio-collect-test-log-reports; orchestrate_health_suite | command_center.scripts.libraries.test_log_analysis; command_center.scripts.libraries.prune_run_directories; `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs` | tests/tests_producers/test_collect_test_log_reports.py | manual; orchestrate_health_suite; run_pytest_log_capture | scripts/producers/collect_test_log_reports.py | std-global-python-engineering.md | none | Emits run bundles under `.repo_studios/reports/producer_reports/test_log_reports/` with latest hardlinks, legacy pytest log fallback, combined log copies, and summary metrics for downstream consumers. |
| .repo_studios/scripts/producers/generate_import_graph_report.py | Builds adjacency graph of owned packages, surfacing cycles and fan-in/out hotspots. | yes | manual CLI (--owned) | python stdlib; repo source tree | tests/tests_producers/test_generate_import_graph_report.py | manual | scripts/producers/generate_import_graph_report.py | TODO | none | Default owned roots now `.repo_studios` and `legacy`; emits JSON/MD/log artifacts with latest pointers and graph.json under `.repo_studios/reports/producer_reports/import_graph_reports/<ts>/`. Catalog: scripts.health.import_graph_report. |
| .repo_studios/scripts/producers/generate_lizard_report.py | Runs `python -m lizard` with repo thresholds and records offender summaries. | yes | manual CLI (--targets/--ts) | lizard module; repo source tree | tests/tests_producers/test_generate_lizard_report.py | manual | scripts/producers/generate_lizard_report.py | TODO | none | Emits JSON/MD/log plus raw artifacts under `producer_reports/lizard_reports/` with pruning, latest pointers, and doc at `docs/automation/generate_lizard_report.md`. Catalog: scripts.health.lizard_report. |
| .repo_studios/scripts/producers/generate_typecheck_report.py | Drives mypy runs with repo configs and captures failing snapshots. | yes | make typecheck | mypy; pyproject settings; env toggles | tests/tests_producers/test_generate_typecheck_report.py | manual; orchestrate_health_suite | scripts/producers/generate_typecheck_report.py | std-global-python-engineering.md | none | Outputs structured JSON/MD/log/raw bundles with pruning under `producer_reports/typecheck_reports/` plus latest symlinks and doc at `docs/automation/generate_typecheck_report.md`. Catalog: scripts.health.typecheck_report. |
| .repo_studios/scripts/producers/generate_test_coverage_inventory.py | Summarizes Coverage.py XML into per-file function coverage metrics. | yes | manual CLI (--coverage-xml) | Coverage.py XML report; repo source tree; `ast` | tests/tests_producers/test_generate_test_coverage_inventory.py | manual | scripts/producers/generate_test_coverage_inventory.py | std-global-python-engineering.md | none | Emits JSON/Markdown/CSV/log bundles under `producer_reports/test_coverage_reports/` with pruning, latest pointers, and automation doc at `docs/automation/generate_test_coverage_inventory.md`; Make target TBD once coverage generation workflow is standardized. Catalog: scripts.health.test_coverage_inventory. |
| .repo_studios/scripts/producers/analyze_test_hardening.py | Evaluates test modules for hardening gaps (missing asserts, mocks, long tests). | yes | CLI (--repo-root); make studio-analyze-test-hardening; GitHub Actions `studio-inventory` workflow | stdlib ast/json/re; repo tests tree | tests/tests_producers/test_analyze_test_hardening.py | manual; Make target; CI | scripts/producers/analyze_test_hardening.py | std-global-python-engineering.md | none | Emits JSON/MD/log bundles under `.repo_studios/reports/producer_reports/test_hardening_reports/` with pruning/latest pointers; automation doc: `docs/automation/analyze_test_hardening.md`. Catalog: scripts.health.analyze_test_hardening. |
| .repo_studios/scripts/producers/scan_code_placeholders.py | Greps source files for placeholder comments like TODO/FIXME to surface debt hotspots. | yes | manual CLI (`--repo-root/--root` options); make studio-scan-code-placeholders | stdlib `argparse`, `json`, `pathlib`, `re` | tests/tests_producers/test_scan_code_placeholders.py | manual | scripts/producers/scan_code_placeholders.py | std-global-python-engineering.md | none | Structured producer (JSON/MD/log/matches TSV) with pruning, allowlist support, automation doc (`docs/automation/scan_code_placeholders.md`), and wired Make target; remediation plan at `.repo_studios/command_center/docs/phase_7/PLACEHOLDER_DEBT_PLAN.md` tracks zero-match baseline (observation run `placeholder_scan-20251123_211100`) and weekly cadence evidence. Catalog: scripts.utilities.find_placeholders. |
| .repo_studios/scripts/producers/scan_monkey_patches.py | AST + regex inventory of monkey patches with CSV/JSON summaries. | yes | make studio-scan-monkey-patches; manual CLI (--repo-root) | stdlib; optional git blame | tests/tests_producers/test_scan_monkey_patches.py | manual | scripts/producers/scan_monkey_patches.py | std-global-python-engineering.md | none | Remediated 2025-10-23: structured JSON/MD/log/matches TSV bundle under `producer_reports/monkey_patch_scans/` with pruning and latest pointers, pytest coverage, automation doc (`docs/automation/scan_monkey_patches.md`), and Make wiring. Catalog: scripts.health.scan_monkey_patches. |
| .repo_studios/scripts/producers/validate_import_boundaries.py | Enforces layering rules using import graph snapshots and static scans. | yes | manual CLI (--repo-root); legacy alias `check_import_boundaries.py` | `.repo_studios/reports/producer_reports/import_graph_reports/*/graph.json`; `import_rules_allowlist.json`; repo source tree | tests/tests_producers/test_validate_import_boundaries.py | manual; make studio-validate-import-boundaries | scripts/producers/validate_import_boundaries.py | std-global-python-engineering.md | none | Emits structured JSON/MD/log/violations bundle with pruning, latest pointers, pytest coverage, and automation doc (`docs/automation/validate_import_boundaries.md`). Catalog: scripts.utilities.check_import_boundaries. |
| .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py | Checks orchestrator metrics links for missing legacy anchor stubs. | yes | manual; make studio-validate-metrics-anchor-stubs | repo markdown tree; docs/api/metrics_orchestrator.md; optional allowlist JSON | tests/tests_producers/test_validate_metrics_anchor_stubs.py | manual; make studio-validate-metrics-anchor-stubs | scripts/producers/validate_metrics_anchor_stubs.py | std-global-markdown-authoring.md | none | Structured JSON/MD/log/missing bundle with pruning + latest pointers, allowlist support, pytest coverage, automation doc (`docs/automation/validate_metrics_anchor_stubs.md`), and Make target created 2025-10-23. Catalog: scripts.utilities.check_doc_anchors. |
| .repo_studios/scripts/producers/verify_docs_integrity.py | Verifies governed docs JSON hashes and regenerates navigation tables. | yes | manual CLI (--update); make studio-verify-docs-integrity | stdlib json/hashlib; docs index markdown and governed docs | tests/tests_producers/test_verify_docs_integrity.py | manual | scripts/producers/verify_docs_integrity.py | std-global-markdown-authoring.md | none | Structured run bundles under `.repo_studios/reports/producer_reports/docs_integrity_reports/` (JSON/MD/log/mismatches) with pruning, latest pointers, and automation doc alignment. Catalog: scripts.utilities.verify_docs_integrity. |
| .repo_studios/scripts/producers/check_inventory_health.py | Validates inventory summary metrics against CI thresholds and baseline deltas. | yes | manual CLI (--summary); make studio-check-inventory-health | inventory summary JSON; `.repo_studios/config/ci_inventory_thresholds.json` | tests/tests_producers/test_check_inventory_health.py | manual; make studio-check-inventory-health | scripts/producers/check_inventory_health.py | std-global-markdown-authoring.md | none | Emits structured JSON/MD/log artifacts with pruning and latest pointers. Catalog: scripts.inventory.check_inventory_health. |
| .repo_studios/scripts/producers/render_inventory_views.py | Renders canonical inventory YAML/Markdown views for quick review. | yes | manual CLI (--schema-root/--output-dir) | PyYAML; inventory schema | tests/tests_producers/test_render_inventory_views.py | manual | scripts/producers/render_inventory_views.py | std-global-markdown-authoring.md | none | Writes run bundles under `.repo_studios/reports/producer_reports/render_inventory_views/` (JSON/MD/log/raw) and refreshes legacy view stubs for downstream compatibility. Catalog: scripts.inventory.render_inventory_views. |
| .repo_studios/scripts/producers/validate_inventory.py | Lightweight schema checks applied to Repo Studios inventory files. | yes | manual CLI (--json) | PyYAML; inventory schema; validator_config.yaml; enums.yaml | tests/tests_producers/test_validate_inventory.py | manual | scripts/producers/validate_inventory.py | std-global-python-engineering.md | none | Emits validation runs in `.repo_studios/reports/producer_reports/validate_inventory/` (JSON/MD/log/issues) with pruning & latest pointers; legacy `--json` continues to surface consolidated findings. Catalog: scripts.inventory.validate_inventory. |
| .repo_studios/scripts/producers/generate_doc_index.py | Builds repo-wide documentation index bundle with metrics/advisories plus JSON/YAML/CSV views and optional database sink placeholder metadata. | yes | manual CLI (--repo-root/--output-dir/--db-target/--log-level) | stdlib; PyYAML | tests/tests_producers/test_generate_doc_index.py | manual | scripts/producers/generate_doc_index.py | std-global-markdown-authoring.md | none | Outputs JSON, Markdown bundle, and standalone CSV under `.repo_studios/reports/producer_reports/doc_index/` with sanitized front matter, retention=1, metrics/advisories sections, database placeholder logging, and automation doc `docs/automation/generate_doc_index.md`. Catalog: scripts.docs.generate_doc_index. |
| .repo_studios/scripts/producers/generate_code_doc_churn_report.py | Flags source directories changed within a git window that lack matching docs updates. | yes | manual CLI (--repo-root/--git-window); Make target TBD | git CLI; `.repo_studios/reports/producer_reports/doc_index/` metadata; `.repo_studios/reports/producer_reports/anchor_inventory_reports/` enrichment | tests/tests_producers/test_generate_code_doc_churn_report.py | manual | scripts/producers/generate_code_doc_churn_report.py | std-global-python-engineering.md | none | Structured JSON/MD/TSV + bundle summary with retention=5, latest pointers, markdownlint exemption for doc-update section, and automation doc at `.repo_studios/docs/automation/generate_code_doc_churn_report.md`. Catalog: scripts.docs.code_doc_churn_report. |
| .repo_studios/scripts/producers/generate_undocumented_logic_report.py | Highlights modules/functions that should have documentation anchors but do not. | yes | manual CLI (--include-command-center/--code-root) | doc index JSON; anchor inventory JSON; allowlist | tests/tests_producers/test_generate_undocumented_logic_report.py | manual | scripts/producers/generate_undocumented_logic_report.py | std-global-python-engineering.md | none | Structured JSON/MD/TSV bundle with retention=5, allowlist + extra code root support, doc/anchor enrichment, and automation doc at `docs/automation/generate_undocumented_logic_report.md`. Catalog: scripts.docs.undocumented_logic_report. |

- **Next Actions:**
- [x] Backfilled testing references for legacy producers that listed `TODO` coverage (diff_standards_index.py, validate_markdown_anchors.py) on 2025-11-23.
- [x] Captured CI wiring references for `diff_standards_index.py` and `generate_dependency_hygiene_report.py` on 2025-11-23.
- [x] Completed documentation updates for `validate_markdown_anchors.py` (docs/automation/validate_markdown_anchors.md) on 2025-11-23.
- DONE: Audited `extract_standards_rules.py` consumer integrations on 2025-11-23; `generate_standards_index.py` handles run directory pruning and `summarize_standards.py` is read-only, so no additional cleanup needed.
- DONE: Completed refactor loop for `validate_metrics_anchor_stubs.py` (structured artifacts, pruning, tests, docs, automation wiring).
- DONE: Completed refactor loop for `verify_docs_integrity.py` (structured artifacts, pruning, tests, docs, Make target).
- [x] Draft placeholder remediation plan (allowlist + debt burn-down targets) before revisiting CI gating for `studio-scan-code-placeholders` (2025-11-23).
- [x] Prepare owner outreach + allowlist guidance for `studio-scan-code-placeholders` remediation campaign (2025-11-23).
- [x] Propose `.venv/` exclusion defaults for placeholder scans prior to re-running CI evaluation (2025-11-23).
- [x] Implement `--exclude-prefix` support + `.venv/` default in `scan_code_placeholders.py` with pytest coverage (2025-11-23).
- [x] Update remediation plan + automation docs after exclusion support lands, then resume weekly burn-down tracking (2025-11-23).
- [x] Re-run producer + metrics ledger after exclusion rollout to capture zero-match baseline (2025-11-23).
- [x] Prototype `placeholder-scan` CI workflow in warning mode and document rollout checkpoints (2025-11-23).
- todo (done 2025-11-24): Monitored `placeholder-scan` workflow results and captured the 2025-11-24 scan artifacts.
  Published the blocking-mode transition brief (`.repo_studios/command_center/docs/phase_7/placeholder_scan_blocking_transition_brief.md`) to guide the enforcement review.
- [x] Implemented `generate_doc_index.py` (repo-wide documentation index bundle with database placeholder logging) and shipped tests/docs on 2025-11-24.

**Status Update (2025-11-24):** Completed the monkey-patch, anchor health, faulthandler, and test-log consumer hardening passes—each now prefers structured producer bundles, enforces retention pruning, exposes CLI logging controls, and ships with pytest coverage plus refreshed inventory notes. Placeholder remediation remains steady with weekly scans staged, CI still in warning mode, and outreach artifacts live. Immediate focus is documenting the latest consumer decision, re-running the placeholder metrics ledger after the next scan window, and kicking off the producer→consumer traceability audit ahead of aggregator planning.

**Status Update (2025-11-24 follow-up):** Past — Landed the pytest log producer/consumer chain, carried the faulthandler refactor through docs and Make wiring, and wrapped the monkey-patch, anchor, faulthandler, and test-log consumer uplifts with regression tests and retention pruning. Present — Recording governance updates, launching the producer→consumer traceability audit, and prepping notes for the aggregator modernization plan. Future — Finish the consumer backlog audit, align aggregator input expectations with the new summaries, and expand governance reporting once the aggregator handoff ships.

**Status Update (2025-11-24 readiness):** Past — Logged observation week 2 for the placeholder scan guardrail and generated the blocking-mode transition brief. Present — Maintaining weekly monitoring evidence and capturing metrics/CI rollout updates in tandem. Future — Collect two additional clean observation runs, secure stakeholder approval, and then promote the workflow to blocking enforcement.

---

## 2. Script Consumers

**Category Purpose:** Single-hop analyzers that operate on a producer’s output to deliver targeted insights.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/consumers/classify_monkey_patches.py | Buckets monkey-patch findings into HIGH/MODERATE/SAFE risk and writes JSON/MD summaries. | yes | manual CLI; orchestrator | `scan_monkey_patches.py` producer runs under `.repo_studios/reports/producer_reports/monkey_patch_scans/` with fallback to legacy alias | tests/tests_consumers/test_classify_monkey_patches.py | manual; orchestrate_health_suite | scripts/consumers/classify_monkey_patches.py | std-global-monkey-patching.md | none | Shared helper aligns consumer/aggregator risk mapping; automation doc lives at `.repo_studios/docs/automation/classify_monkey_patches.md`. Catalog: scripts.health.monkey_patch_classify. |
| .repo_studios/scripts/consumers/generate_anchor_health_report.py | Captures duplicate H1/H2 anchor slugs across docs tree and writes JSON/MD snapshots. | yes | manual CLI | `generate_anchor_inventory.py` outputs (`.repo_studios/reports/producer_reports/anchor_inventory_reports/latest_report.json`) plus docs baseline (`tests/docs/anchor_slug_baseline.json`) | tests/tests_consumers/test_generate_anchor_health_report.py | manual | scripts/consumers/generate_anchor_health_report.py | std-global-markdown-authoring.md | none | Structured bundles now emit `summary.json`, `SUMMARY.md`, and `bundle_summary.json` alongside legacy `anchor_report.*` artifacts with latest pointers, retention=5, inventory fallback, database placeholder stub, and automation doc at `.repo_studios/docs/automation/generate_anchor_health_report.md`. Catalog: scripts.health.anchor_health_report. |
| .repo_studios/scripts/consumers/generate_fault_artifacts.py | Converts faulthandler stacks into CSV/MD/manifest artifacts for triage. | yes | manual CLI (--outdir); make studio-generate-fault-artifacts | `collect_faulthandler_reports.py` runs (`.repo_studios/reports/producer_reports/faulthandler_reports/latest_report.json`) with fallback to `.repo_studios/faulthandler/<ts>/stacks.log`; `utilities.fault_run_analysis` | tests/tests_consumers/test_generate_fault_artifacts.py | manual; Make target; orchestrate_health_suite | scripts/consumers/generate_fault_artifacts.py | std-global-python-engineering.md | none | Prefers structured producer reports with fallback scan analysis, writes consumer bundles to `.repo_studios/reports/consumer_reports/fault_artifacts/` with retention controls (`--artifacts-to-keep`), enriched provenance summaries, and configurable logging. Catalog: scripts.health.generate_fault_artifacts. |
| .repo_studios/scripts/consumers/generate_test_log_health_report.py | Summarizes pytest logs for warnings, slow tests, and JUnit stats. | yes | manual CLI (--logs-dir/--output-base) | `collect_test_log_reports.py` bundle (`.repo_studios/reports/producer_reports/test_log_reports/latest_report.json`) with fallback to raw pytest log directories; defusedxml | tests/tests_consumers/test_generate_test_log_health_report.py | manual; orchestrate_health_suite | scripts/consumers/generate_test_log_health_report.py | std-global-python-engineering.md | none | Writes JSON/MD/CSV bundles with bundle summaries under `.repo_studios/reports/consumer_reports/test_log_health_reports/<ts>/`, appends source references, computes pass-rate deltas vs. the previous run, defaults retention to 5 (`--artifacts-to-keep`), and surfaces configurable logging while preferring structured producer artifacts with raw log fallback. Catalog: scripts.health.test_log_health_report. |

- **Next Actions:**
- [x] Record which producers feed each consumer to clarify data lineage before refactoring.
- [x] Collapse monkey-patch consumer path drift by exposing producer_reports/monkey_patch_scans through a supported alias.
- [x] Evaluate reusing `generate_anchor_inventory.py` artifacts directly to avoid redundant markdown rescans during consumer runs.
- [x] Assess whether faulthandler/test log collectors need dedicated producers for consistency before orchestrator rewires (2025-11-23); confirmed faulthandler producer in service and queued pytest log producer design.
- [x] Publish automation doc and Make target for `collect_faulthandler_reports.py` once orchestrator wiring reuses the structured bundle (2025-11-23); see `docs/automation/collect_faulthandler_reports.md` and Make target `studio-collect-faulthandler-reports`.
- [x] Implement `collect_test_log_reports.py` to emit structured bundles with pruning, tests, docs, and Make wiring (2025-11-23).
- [x] Draft pytest log producer blueprint (`collect_test_log_reports.py`) leveraging `command_center.scripts.libraries.test_log_analysis` ahead of the consumer refactor (2025-11-23); see `command_center/docs/phase_7/COLLECT_TEST_LOG_REPORTS_BLUEPRINT.md`.
- [x] Rewire `generate_test_log_health_report.py` to consume `collect_test_log_reports.py` artifacts by default while preserving fallback behaviour (2025-11-23).
- [x] Add pytest coverage for `generate_test_log_health_report.py` covering producer and fallback flows (2025-11-23).
- [x] Update monkey-patch consumer to ingest summary + matches schema without relying on the alias after refactor loop hardening (2025-11-24).
- [x] Harden `generate_fault_artifacts.py` with retention pruning, consumer bundle outputs, CLI logging controls, and refreshed pytest coverage (2025-11-24).
- [x] Harden `generate_test_log_health_report.py` with retention pruning, bundle metadata, source references, and configurable logging (2025-11-24).
- [x] Completed consumer refactors; ready to proceed with aggregator sequencing per blueprint.
- [x] Review producer → consumer pairings to spot orphaned artifacts, document traceability expectations, and propose new consumers when a focused topic lacks coverage. See `.repo_studios/docs/automation/traceability/producer_consumer_traceability_audit.md`.

---

## 3. Script Aggregators

**Category Purpose:** Multi-source combiners that blend several producer/consumer artifacts into higher-order insights.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/aggregators/analyze_monkey_patch_trends.py | Aggregates monkey-patch risk bundles into trend JSON/Markdown with provenance and retention. | yes | manual CLI (--consumer-base/--output-base); orchestrator | `.repo_studios/reports/consumer_reports/monkey_patch_risk/monkey_patch_risk-*/summary.json`; fallback `.repo_studios/reports/producer_reports/monkey_patch_scans/*/report.json` | tests/tests_aggregators/test_analyze_monkey_patch_trends.py | manual; orchestrate_health_suite | scripts/aggregators/analyze_monkey_patch_trends.py | std-global-python-engineering.md | none | Emits `.repo_studios/reports/aggregator_reports/monkey_patch_trends/monkey_patch_trends-<ts>/` bundles with `trend.json`, `trend.md`, `bundle_summary.json`, latest pointers, and mirrors the markdown into the newest consumer bundle; exposes retention and logging controls. Catalog: scripts.health.compare_monkey_patch_trends. |
| .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py | Scores files by git churn, AST complexity, and failure density to flag risky hotspots. | yes | manual CLI (--window/--logs-dir/--test-log-summary/--metrics-source); orchestrator | git cli; `.repo_studios/reports/consumer_reports/test_log_health_reports/`; optional defusedxml | tests/tests_aggregators/test_generate_churn_complexity_heatmap.py | manual; orchestrate_health_suite | scripts/aggregators/generate_churn_complexity_heatmap.py | std-global-python-engineering.md | none | Emits timestamped bundles with `heatmap.json`, `heatmap.md`, and `bundle_summary.json`, maintains `latest_*.json/md` pointers, accepts precomputed metrics, records git/JUnit provenance, and prunes history (default keep=10). Catalog: scripts.health.churn_complexity_heatmap. |
| .repo_studios/scripts/aggregators/aggregate_docs_health_signals.py | Blend churn, coverage, structure, integrity, and hygiene signals into a docs health bundle with provenance and retention. | yes | Make target `studio-aggregate-docs-health`; manual CLI (`--skip-hygiene`, `--artifacts-to-keep`, `--log-level`) | Latest producer bundles from `generate_code_doc_churn_report.py`, `generate_undocumented_logic_report.py`, `generate_anchor_inventory.py`, `validate_markdown_anchors.py`, `verify_docs_integrity.py`, optional `scan_code_placeholders.py`/`scan_monkey_patches.py` | tests/tests_aggregators/test_aggregate_docs_health_signals.py | Make target; manual CLI; future orchestrator hop | scripts/aggregators/aggregate_docs_health_signals.py | std-global-markdown-authoring.md | none | Emits timestamped JSON/MD/TSV/CSV bundles with `latest_*` pointers, weighted scoring, schema-version provenance map, and MD032-compliant summaries; design spec at `.repo_studios/docs/automation/aggregate_docs_health_signals.md`. Catalog: scripts.docs.aggregate_docs_health_signals. |
| .repo_studios/command_center/scripts/aggregators/scan_duplicates.py | Merges CommandView inventory and analysis bundles into duplicate function matrices and summaries. | yes | manual CLI; command center pipeline (`run_command_center_pipeline.py`) | `generate_commandview_inventory.py`; `generate_function_analysis.py`; command_center libraries (`write_report_artifacts`, `slugify_relative`) | tests/tests_library_integration/duplicates/test_scan_duplicates.py | manual; command center orchestrator | command_center/scripts/aggregators/scan_duplicates.py | std-global-python-engineering.md | none | Emits viewer/topic/timestamp bundles under `.repo_studios/command_center/reports/commandview/duplicate_scan/<ts>/` with mirrored index artifacts and retention (keep=3) via `write_report_artifacts`; CLI exposes `run()` helper for import safety. |

- **Next Actions:**
- todo (done 2025-11-24): Completed aggregator modernization sequence once consumer hardening shipped; trend script now consumes consumer bundles with fallback and provenance.
- todo (done 2025-11-24): Revisited monkey-patch trend aggregator inputs after consumer format finalization; verified lineage to producer matches and documented outputs.
- todo (done 2025-11-24): Map each aggregator’s upstream producer/consumer dependencies, validate traceability to the underlying producers, and document gaps before rewiring orchestrators. See `.repo_studios/docs/automation/traceability/aggregator_dependency_audit.md`.
- todo (done 2025-11-24): Draft modernization plan for `analyze_monkey_patch_trends.py` (see `.repo_studios/docs/automation/traceability/analyze_monkey_patch_trends_modernization_plan.md`).
- todo (done 2025-11-24): Draft modernization plan for `generate_churn_complexity_heatmap.py` (see `.repo_studios/docs/automation/traceability/generate_churn_complexity_heatmap_modernization_plan.md`).
- todo (done 2025-11-24): Execute `analyze_monkey_patch_trends.py` modernization once consumer output location is finalized.
- todo (done 2025-11-24): Execute `generate_churn_complexity_heatmap.py` modernization after plan review and helper decisions; aggregator now threads consumer bundle provenance, optional metrics sources, git/JUnit metadata, retention pruning, and pytest coverage.
- [x] Documented Command Center duplicate scan aggregator migration and viewer/topic outputs (2025-11-30).

**Status Update (2025-11-24):** Past — Rebuilt both aggregators with consumer-first ingestion, provenance-rich bundle summaries, and pytest regression suites. Present — Validating command center notes and Make wiring to ensure orchestrators can adopt the new churn × complexity bundle without regressions. Future — Revisit metrics extraction helper feasibility once additional aggregators surface shared needs and document orchestrator integration criteria.

**Status Update (2025-11-24 supplemental):** Past — Updated the `analyze_monkey_patch_trends.py` catalog entry with finalized migration target and conformance review coverage. Present — Monitoring orchestrator sequencing so consumer bundles precede aggregator runs. Future — Decide whether to extend aggregator outputs with CSV exports after the orchestrator review concludes.

**Status Update (2025-11-24 orchestrators):** Past — Implemented `run_batch_cleanup.py` modernization with structured bundles, pruning, latest pointers, and pytest coverage (`tests/tests_orchestrators/test_run_batch_cleanup.py`). Present — Updating automation hooks + governance docs to reflect the new CLI/outputs. Future — Align remaining orchestrators with the refactored cleanup helper and kick off `run_pytest_log_capture.py` planning once documentation catches up.

**Status Update (2025-11-27 orchestrators):** Past — Completed `run_pytest_log_capture.py` modernization with Command Center path/option builders, structured artifact bundles, and pytest coverage (`tests/tests_orchestrators/test_run_pytest_log_capture.py`). Present — Folding documentation and inventory notes into automation guides. Future — Evaluate wiring into the health suite orchestrator for default retention of five runs and summary-mode reuse in CI post-processing flows.

---

## 4. Script Orchestrators

**Category Purpose:** Entry-point runners that coordinate multiple tiers and manage artifact lifecycles.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/orchestrators/run_batch_cleanup.py | Coordinates Ruff formatting, lint, pytest, and markdown cleanup passes with structured bundles and retention. | yes | manual CLI (`--mode/--target/--output-base/--artifacts-to-keep/--log-level`); see `docs/automation/orchestrator_automation_hooks.md` | Ruff; mypy; pytest; markdownlint-cli (npx fallback) | tests/tests_orchestrators/test_run_batch_cleanup.py | manual; health suite | scripts/orchestrators/run_batch_cleanup.py | std-global-python-engineering.md | none | Emits timestamped bundles (`cleanup_summary.json`, `cleanup_log.txt`, `bundle_summary.json`) with latest pointers, supports an import-safe `run(argv=None)` helper, prunes history via `--artifacts-to-keep`, records tree-refresh metadata, and surfaces per-command status including markdownlint tooling availability. Catalog: scripts.utilities.batch_clean. |
| .repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py | Coordinates the faulthandler producer, consumer, and overview summarizer into a Command Center bundle. | yes | manual CLI (`--repo-root/--runs-dir/--run-dir/--reuse-report/--skip-*` + retention knobs); make studio-orchestrate-fault-diagnostics (alias studio-run-fault-pipeline) | `collect_faulthandler_reports.py`; `generate_fault_artifacts.py`; `command_center/scripts/summarizers/summarize_fault_diagnostics_overview.py`; command_center libraries (`cli`, `artifacts`) | tests/tests_command_center/fault_diagnostics/test_run_fault_diagnostics_overview.py | manual; Make target | command_center/scripts/orchestrators/run_fault_diagnostics_overview.py | std-global-python-engineering.md | none | Emits viewer/topic/timestamp bundles under `.repo_studios/command_center/reports/commandview/fault_diagnostics/<slug>/` (`manifest.json`, `summary.md`, `telemetry.json`), mirrors producer/consumer outputs into their Command Center directories, enforces per-step retention, and registers catalog metadata for telemetry. Catalog: scripts.health.fault_diagnostics_overview. |
| .repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py | Coordinates docs health producers, the aggregator, and Healthview manifest emission under the command center guardrails. | yes | make studio-orchestrate-docs-health; `make -C .repo_studios command-center COMMAND_CENTER_TARGET=command_center/scripts/orchestrators/run_docs_health_overview.py` | `generate_doc_index.py`; `generate_anchor_inventory.py`; `validate_markdown_anchors.py`; `verify_docs_integrity.py`; `aggregate_docs_health_signals.py`; command_center libraries (`build_topic_pipeline`, `guardrails.enforce_report_naming`) | tests/tests_command_center/docs_health/test_run_docs_health_overview.py | manual; Make target; command center pipeline | command_center/scripts/orchestrators/run_docs_health_overview.py | std-global-python-engineering.md | none | Emits Healthview viewer/topic bundles with retention-per-step, mirrors refreshed producer/aggregator artifacts, and aborts when `reports_naming_audit.py` flags non-compliant paths. Catalog: scripts.health.docs_health_overview. |
| .repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py | Threads dependency hygiene, import graph, placeholder scan, batch cleanup dry run, typecheck, and optional mypy baseline refresh into a Healthview hygiene bundle. | yes | make studio-orchestrate-dependency-import-hygiene | `generate_dependency_hygiene_report.py`; `generate_import_graph_report.py`; `scan_code_placeholders.py`; `run_batch_cleanup.py`; `generate_typecheck_report.py`; `refresh_mypy_baselines.py`; command_center libraries (`build_topic_pipeline`) | tests/tests_command_center/dependency_import_hygiene/test_run_dependency_import_hygiene.py | manual; Make target | command_center/scripts/orchestrators/run_dependency_import_hygiene.py | std-global-python-engineering.md | none | Emits dependency/import hygiene viewer/topic bundles with measured provenance, retention budgets per step, placeholder allowlist threading, and optional mypy baseline refresh outcomes. Catalog: scripts.health.dependency_import_hygiene. |
| .repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py | Publishes the standards integrity Healthview bundle by chaining index regeneration, prompt exports, anchor audits, and dependent guardrails. | yes | make studio-orchestrate-standards; `make -C .repo_studios command-center COMMAND_CENTER_TARGET=command_center/scripts/orchestrators/run_standards_integrity.py` | `generate_standards_index.py`; `generate_anchor_inventory.py`; `validate_markdown_anchors.py`; `generate_dependency_hygiene_report.py`; command_center libraries (`build_topic_pipeline`, `guardrails.enforce_report_naming`) | tests/tests_command_center/standards_integrity/test_run_standards_integrity.py | manual; Make target; CI (`.github/workflows/studio-inventory.yml`) | command_center/scripts/orchestrators/run_standards_integrity.py | std-global-python-engineering.md | none | Emits standards integrity viewer/topic bundles, mirrors catalog registration, enforces per-step retention, and fails fast when `reports_naming_audit.py` identifies schema drift. Catalog: scripts.health.standards_integrity_overview. |
| .repo_studios/command_center/scripts/orchestrators/run_command_center_pipeline.py | Meta-runner that chains CommandView inventory, analysis, and duplicate scan with shared logging and failure short-circuiting. | yes | `make -C .repo_studios command-center COMMAND_CENTER_TARGET=command_center/scripts/orchestrators/run_command_center_pipeline.py` | `generate_commandview_inventory.py`; `command_center/scripts/summarizers/generate_function_analysis.py`; `command_center/scripts/aggregators/scan_duplicates.py` | tests/tests_orchestrators/test_command_center_pipeline.py | manual; command center pipeline entry | command_center/scripts/orchestrators/run_command_center_pipeline.py | std-global-python-engineering.md | none | Dynamically imports each step’s `run()` helper, threads fresh analysis artifacts into the duplicate scan, mirrors shared log level, and aborts on first failure to prevent partial rebuilds. Catalog: scripts.health.command_center_pipeline. |
| .repo_studios/scripts/orchestrators/run_pytest_log_capture.py | Runs pytest with structured bundle emission, legacy summary refresh, and optional serial fallback when xdist terminates. | yes | manual CLI (pytest passthrough); see `docs/automation/orchestrator_automation_hooks.md` | pytest; defusedxml; optional xdist/cov plugins; command_center libraries (`cli`, `artifacts`) | tests/tests_orchestrators/test_run_pytest_log_capture.py | manual; health suite | scripts/orchestrators/run_pytest_log_capture.py | std-global-python-engineering.md | none | Produces JSON/Markdown/CSV/text bundles via `write_report_artifacts`, mirrors `latest_*` pointers, honors `--artifacts-to-keep` (default five), supports `--from-log/--from-junit` summarize mode, and now stages raw logs under `.repo_studios/reports/orchestrator_logs/pytest_log_capture_logs/` with a legacy pointer for docs. Catalog: scripts.health.pytest_log_runner. |
| .repo_studios/scripts/orchestrators/run_standards_gap_suite.py | Coordinates standards index regeneration followed by gap analysis with shared retention budgets and legacy fallbacks. | yes | manual CLI (--repo-root/--skip-index/--timestamp/--legacy-json); standards handoff pipeline | `.repo_studios/scripts/producers/generate_standards_index.py`; `.repo_studios/scripts/producers/analyze_standards_index_gaps.py`; command_center.scripts.libraries (PathsConfig/OptionsConfig) | tests/tests_orchestrators/test_run_standards_gap_suite.py | manual; standards refresh pipeline | scripts/orchestrators/run_standards_gap_suite.py | std-global-python-engineering.md | none | Threads command center path/option builders, propagates shared logging and retention controls, falls back to legacy index snapshots, and emits structured status payloads without writing new artifacts. |
| .repo_studios/scripts/orchestrators/run_standards_index_cli.py | Exposes the standards index bundle (via `latest_index.yaml`) through list/search/show/stats subcommands. | yes | manual CLI (subcommands); see `docs/automation/orchestrator_automation_hooks.md` | PyYAML; command_center `cli`/`artifacts` libraries; reports/producer_reports/standards_index_reports/latest_index.yaml | tests/tests_orchestrators/test_run_standards_index_cli.py | manual | scripts/orchestrators/run_standards_index_cli.py | std-global-python-engineering.md | none | Emits structured bundles (`report.json`, `report.md`, `bundle_summary.json`, `stdout.txt`) with retention controls, retains stdout compatibility, documents usage in `docs/automation/run_standards_index_cli.md`, and surfaces errors in summary payloads. Catalog: scripts.standards.index_cli. |
| .repo_studios/scripts/orchestrators/orchestrate_health_suite.py | Chains health scripts sequentially, recording per-step logs, manifests, and status summaries. | yes | manual CLI (--timestamp/--live); see `docs/automation/orchestrator_automation_hooks.md` | orchestrated scripts under `.repo_studios`; stdlib subprocess | TODO | manual; CI planned | scripts/orchestrators/orchestrate_health_suite.py | TODO | none | Emits run output under `.repo_studios/reports/orchestrator_logs/health_suite_logs/<ts>/` (mirrors status into the legacy folder for compatibility), never aborts mid-chain, and now wires the pytest log capture → `collect_test_log_reports.py` → `generate_test_log_health_report.py` sequence so the consumer always sees structured bundles; success criteria captured in `docs/automation/orchestrator_automation_hooks.md`. Catalog: scripts.health.health_suite_orchestrator. |

- **Next Actions:**
- [x] Align health suite orchestrator with the test log producer + consumer chain (2025-11-23).
- [x] Capture orchestrator automation hooks (Make targets, CI jobs) and expected success criteria (`docs/automation/orchestrator_automation_hooks.md`).
- todo (done 2025-11-24): Snapshotted `run_batch_cleanup.py` gaps (logging retention, missing `run()` shim, structured outputs) and refreshed catalog metadata.
- todo (done 2025-11-24): Draft modernization plan for `run_batch_cleanup.py` covering structured artifacts, retention, and orchestrator-friendly entry point (`docs/automation/traceability/run_batch_cleanup_modernization_plan.md`).
- todo (done 2025-11-24): Execute `run_batch_cleanup.py` modernization per approved plan; structured bundles, retention pruning, latest pointers, pytest coverage, and `run()` shim now live. Documentation/governance updates underway.
- [x] Draft faulthandler aggregator blueprint once the orchestrator stabilizes; record scope under `.repo_studios/docs/automation/traceability/fault_pipeline_aggregator_plan.md` (2025-11-26).
- [x] Snapshot `run_standards_index_cli.py` modernization plan (2025-11-27); see `.repo_studios/docs/automation/traceability/run_standards_index_cli_modernization_plan.md`.

---

## 5. Script Summarizers

**Category Purpose:** Narrative synthesizers that condense suite outputs into executive-ready briefs.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/summarizers/summarize_health_suite.py | Collates health artifacts into a single markdown summary with key deltas. | yes | manual CLI (--timestamp); orchestrator | `.repo_studios/*` artifact directories; JSON/MD reports | TODO | orchestrate_health_suite | scripts/summarizers/summarize_health_suite.py | TODO | none | Writes summary markdown to `.repo_studios/reports/summarizer_reports/health_suite_summary_reports/health_suite_<ts>.md` while mirroring a copy into the legacy folder for downstream readers. Catalog: scripts.health.health_suite_summary. |
| .repo_studios/scripts/summarizers/summarize_standards.py | Logs standards index counts and pending extraction status for pipelines. | yes | manual CLI (--label) | PyYAML; reports/producer_reports/standards_index_reports/latest_index.yaml; repo_standards_pending.yaml | tests/tests_summarizers/test_summarize_standards.py | manual | scripts/summarizers/summarize_standards.py | TODO | none | Emits log-only telemetry for standards orchestration; documentation lives at `docs/automation/summarize_standards.md`. Catalog: scripts.standards.summary. |
| .repo_studios/command_center/scripts/summarizers/generate_function_analysis.py | Converts CommandView inventories into duplicate-focused findings for downstream remediation. | yes | manual CLI; command center pipeline (`run_command_center_pipeline.py`) | `generate_commandview_inventory.py`; command_center libraries (`write_report_artifacts`, `slugify_relative`) | tests/tests_producers/test_generate_function_analysis.py | manual; command center orchestrator | command_center/scripts/summarizers/generate_function_analysis.py | std-global-python-engineering.md | none | Emits viewer/topic/timestamp bundles under `.repo_studios/command_center/reports/commandview/function_analysis/<ts>/`, mirrors analysis JSON into `<target>_index`, retains the latest run (keep=1), and exposes `run()` for import-safe orchestration. |

- **Next Actions:**
- TODO: Define output schema guarantees so downstream agents can parse summaries safely.
- [x] Recorded Command Center function analysis summarizer migration and viewer/topic rollout (2025-11-30).

---

## 6. Script Utilities

**Category Purpose:** Shared helpers that configure runtime hooks or refresh baseline artifacts.

| Script Path | Description | Needed | Wired | Dependencies | Testing Coverage | Entry Points | Migration Target | Conformance Review | Duplicates | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| .repo_studios/scripts/utilities/configure_faulthandler_runtime.py | Sitecustomize shim that standardizes FAULT_* environment defaults and warning filters. | yes | sitecustomize import | stdlib only | tests/tests_utilities/test_configure_faulthandler_runtime.py | import hook | scripts/utilities/configure_faulthandler_runtime.py | std-global-python-engineering.md | none | Emits structured orchestrator-log runs with MANIFEST.json + bundle_summary.json, retention pruning, and doc coverage at `.repo_studios/docs/automation/configure_faulthandler_runtime.md`. Catalog: scripts.health.faulthandler_module. |
| .repo_studios/scripts/utilities/dump_faulthandler_snapshot.py | One-time faulthandler dump helper that captures stack snapshots into structured bundles. | yes | manual CLI; make studio-dump-faulthandler-snapshot-smoke; orchestrate_health_suite | stdlib faulthandler | tests/tests_utilities/test_dump_faulthandler_snapshot.py | manual; orchestrate_health_suite | scripts/utilities/dump_faulthandler_snapshot.py | std-global-python-engineering.md | none | Emits `snapshot.txt` + MANIFEST/bundle summary under orchestrator logs with retention + legacy fallback; automation doc at `.repo_studios/docs/automation/dump_faulthandler_snapshot.md`. Catalog: scripts.health.dump_faulthandler_once. |
| .repo_studios/scripts/utilities/fault_run_analysis.py | Shared faulthandler stack parser that aggregates signatures and stabilizes manifests for producer/consumer reuse. | yes | library (imported) | stdlib only | tests/tests_utilities/test_fault_run_analysis.py | library import | scripts/utilities/fault_run_analysis.py | std-global-python-engineering.md | none | Powers `collect_faulthandler_reports.py` and `generate_fault_artifacts.py` with manifest bootstrap, salt hashing, and severity buckets for repeat offenders. |
| .repo_studios/scripts/utilities/monkey_patch_risk.py | Risk classification helper returning HIGH/MODERATE/SAFE buckets for monkey patch findings. | yes | library (imported) | stdlib only | tests/tests_utilities/test_monkey_patch_risk.py | library import | scripts/utilities/monkey_patch_risk.py | std-global-python-engineering.md | none | Aligns severity rules with `std-global-monkey-patching.md` so consumers/aggregators share identical risk mapping. |
| .repo_studios/command_center/scripts/libraries/test_log_analysis.py | Parses pytest logs and JUnit XML into structured health reports plus Markdown summaries. | yes | library (imported) | defusedxml (optional); stdlib | tests/tests_utilities/test_test_log_analysis.py | library import | command_center/scripts/libraries/test_log_analysis.py | std-global-python-engineering.md | none | Supplies log selection, warning aggregation, slow-test extraction, and markdown rendering for the pytest log producer/consumer chain; legacy `scripts/utilities/test_log_analysis.py` now re-exports this module. |
| .repo_studios/scripts/utilities/refresh_mypy_baselines.py | Refreshes stored mypy output snapshots for agents and monitoring scopes. | yes | manual CLI; make studio-refresh-mypy-baselines | mypy; python interpreter | tests/tests_utilities/test_refresh_mypy_baselines.py | manual; Make target; orchestrate_health_suite (planned) | scripts/utilities/refresh_mypy_baselines.py | std-global-python-engineering.md | none | Emits structured bundles under `.repo_studios/reports/orchestrator_runs/mypy_baselines/` with retention, latest pointers, automation doc at `.repo_studios/docs/automation/refresh_mypy_baselines.md`, and Make wiring (`studio-refresh-mypy-baselines`) for local runs; failed invocations skip pointer updates. Catalog: scripts.health.mypy_refresh_baselines. |
| .repo_studios/command_center/scripts/libraries/guardrails.py | Guardrail helpers that load automation constraints and expose `enforce_report_naming()` for orchestrators. | yes | library (imported) | PyYAML; `.repo_studios/command_center/docs/guardrails/automation_config.yaml`; `reports_naming_audit.py` | TODO | library import | command_center/scripts/libraries/guardrails.py | std-global-python-engineering.md | none | Supplies guardrail config loading, constraint enforcement, and report-naming validation reused by Docs Health and Standards Integrity orchestrators; add pytest coverage mirroring the manifest helper tests. |
| .repo_studios/scripts/utilities/reports_naming_audit.py | Scans `/reports/` artifacts, decomposes paths into the approved viewer/topic/timestamp schema, and surfaces violations. | yes | manual CLI; library import | stdlib only | TODO | manual; documentation orchestrator (planned) | scripts/utilities/reports_naming_audit.py | std-global-python-engineering.md | none | Emits JSON + Markdown summaries, flags `latest_*` aliases, and returns non-zero when compliance thresholds are breached. |

- **Next Actions:**
- DONE (2025-11-29): Introduced the shared `prune_run_directories` helper under
	`command_center/scripts/libraries/` so utilities (and future tiers) share
	consistent retention pruning.
- DONE (2025-11-28): Captured default Make wiring for migrated utilities (`studio-refresh-mypy-baselines` now covers the mypy refresh helper).
- DONE (2025-11-28): Validated `configure_faulthandler_runtime.py` via pytest + smoke target, published automation doc, and wired `studio-configure-faulthandler-runtime-smoke` Make target.
- DONE (2025-11-28): Refactored `dump_faulthandler_snapshot.py` with structured artifacts, retention, pytest coverage, documentation, and smoke Make target.

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

- [x] Document YAML export process once first category is complete (2025-11-26).
- [x] Link populated tables to inventory catalog entries (2025-11-26).

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

<!-- markdownlint-enable MD010 MD013 MD029 -->
