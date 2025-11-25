PYTHON ?= python3
REPO_ROOT := $(abspath $(CURDIR)/..)

.PHONY: command-center
command-center:
ifeq ($(strip $(COMMAND_CENTER_TARGET)),)
	$(error COMMAND_CENTER_TARGET variable required (make command-center COMMAND_CENTER_TARGET=...))
endif
	$(PYTHON) "$(CURDIR)/command_center/scripts/orchestrators/run_command_center_pipeline.py" --repo-root "$(REPO_ROOT)" "$(COMMAND_CENTER_TARGET)"

.PHONY: studio-render-views
studio-render-views:
	$(PYTHON) .repo_studios/scripts/producers/render_inventory_views.py

.PHONY: studio-validate-inventory
studio-validate-inventory:
	$(PYTHON) .repo_studios/scripts/producers/validate_inventory.py

studio-check-inventory-health: studio-render-views
	$(PYTHON) .repo_studios/scripts/producers/check_inventory_health.py --output-dir .repo_studios/reports/producer_reports/inventory_health_reports

.PHONY: studio-validate-markdown-anchors
studio-validate-markdown-anchors:
	$(PYTHON) .repo_studios/scripts/producers/validate_markdown_anchors.py --root . --output-dir .repo_studios/reports/producer_reports/markdown_anchor_validation_reports

.PHONY: studio-generate-anchor-inventory
studio-generate-anchor-inventory:
	$(PYTHON) .repo_studios/scripts/producers/generate_anchor_inventory.py --docs-root docs --output-dir .repo_studios/reports/producer_reports/anchor_inventory_reports

.PHONY: studio-analyze-standards-index-gaps
studio-analyze-standards-index-gaps:
	$(PYTHON) .repo_studios/scripts/producers/analyze_standards_index_gaps.py --output-dir .repo_studios/reports/producer_reports/standards_gap_reports

.PHONY: studio-scan-code-placeholders
studio-scan-code-placeholders:
	$(PYTHON) .repo_studios/scripts/producers/scan_code_placeholders.py --repo-root .

.PHONY: studio-scan-monkey-patches
studio-scan-monkey-patches:
	$(PYTHON) .repo_studios/scripts/producers/scan_monkey_patches.py --repo-root .

.PHONY: studio-seed-standards-prompts
studio-seed-standards-prompts:
	$(PYTHON) .repo_studios/scripts/producers/seed_standards_prompts.py --repo-root .

.PHONY: studio-validate-import-boundaries
studio-validate-import-boundaries:
	$(PYTHON) .repo_studios/scripts/producers/validate_import_boundaries.py --repo-root .

.PHONY: studio-validate-metrics-anchor-stubs
studio-validate-metrics-anchor-stubs:
	$(PYTHON) .repo_studios/scripts/producers/validate_metrics_anchor_stubs.py --repo-root .

.PHONY: studio-analyze-test-hardening
studio-analyze-test-hardening:
	$(PYTHON) .repo_studios/scripts/producers/analyze_test_hardening.py --repo-root . --output-dir .repo_studios/reports/producer_reports/test_hardening_reports

.PHONY: studio-verify-docs-integrity
studio-verify-docs-integrity:
	$(PYTHON) .repo_studios/scripts/producers/verify_docs_integrity.py --repo-root . --output-dir .repo_studios/reports/producer_reports/docs_integrity_reports

.PHONY: studio-collect-faulthandler-reports
studio-collect-faulthandler-reports:
	$(PYTHON) .repo_studios/scripts/producers/collect_faulthandler_reports.py --runs-dir .repo_studios/faulthandler --output-dir .repo_studios/reports/producer_reports/faulthandler_reports --artifacts-to-keep 10 --log-level INFO

.PHONY: studio-collect-test-log-reports
studio-collect-test-log-reports:
	$(PYTHON) .repo_studios/scripts/producers/collect_test_log_reports.py --logs-dir .repo_studios/pytest_logs --output-dir .repo_studios/reports/producer_reports/test_log_reports --artifacts-to-keep 10 --log-level INFO

.PHONY: studio-diff-standards-index
studio-diff-standards-index:
	$(PYTHON) .repo_studios/scripts/producers/diff_standards_index.py "$(old)" "$(new)" --repo-root . --output-dir .repo_studios/reports/producer_reports/standards_index_diff_reports --artifacts-to-keep 10 --fail-on any --log-level INFO

.PHONY: studio-generate-dependency-hygiene
studio-generate-dependency-hygiene:
	$(PYTHON) .repo_studios/scripts/producers/generate_dependency_hygiene_report.py --repo-root . --output-dir .repo_studios/reports/producer_reports/dependency_hygiene_reports --log-level INFO

.PHONY: studio-generate-code-doc-churn-report
studio-generate-code-doc-churn-report:
	$(PYTHON) .repo_studios/scripts/producers/generate_code_doc_churn_report.py --repo-root . --output-dir .repo_studios/reports/producer_reports/code_doc_churn_reports --git-window "30 days" --artifacts-to-keep 5 --log-level INFO

.PHONY: studio-generate-function-index
studio-generate-function-index:
	@$(PYTHON) -c "import sys; sys.exit(0 if '$(path)' else 1)" || (echo "path variable required (make studio-generate-function-index path=...)" && exit 1)
	$(PYTHON) scripts/producers/generate_commandview_inventory.py --repo-root .. "$(path)"
	$(PYTHON) scripts/producers/generate_function_analysis.py --repo-root .. "$(path)"

