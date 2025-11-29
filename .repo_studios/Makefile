PYTHON ?= python3
REPO_ROOT := $(abspath $(CURDIR)/..)

ifneq ($(filter ./% ../% .venv/%,$(PYTHON)),)
	override PYTHON := $(abspath $(REPO_ROOT)/$(PYTHON))
endif

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
	$(PYTHON) .repo_studios/scripts/producers/collect_faulthandler_reports.py --runs-dir .repo_studios/reports/orchestrator_logs/faulthandler_logs --output-dir .repo_studios/reports/producer_reports/faulthandler_reports --artifacts-to-keep 10 --log-level INFO

.PHONY: studio-generate-fault-artifacts
studio-generate-fault-artifacts:
	$(PYTHON) .repo_studios/scripts/consumers/generate_fault_artifacts.py --output-dir .repo_studios/reports/consumer_reports/fault_artifacts --command-center-dir .repo_studios/command_center/reports/fault_artifacts_consumer --artifacts-to-keep 10 --log-level INFO

.PHONY: studio-run-fault-pipeline
studio-run-fault-pipeline:
	cd "$(REPO_ROOT)" && $(PYTHON) ".repo_studios/scripts/orchestrators/run_fault_pipeline.py" --repo-root "$(REPO_ROOT)" --artifacts-to-keep 10 --producer-artifacts-to-keep 10 --consumer-artifacts-to-keep 10 --log-level INFO

.PHONY: studio-configure-faulthandler-runtime-smoke
studio-configure-faulthandler-runtime-smoke:
	$(PYTHON) "$(CURDIR)/scripts/utilities/configure_faulthandler_runtime.py"

.PHONY: studio-dump-faulthandler-snapshot-smoke
studio-dump-faulthandler-snapshot-smoke:
	$(PYTHON) "$(CURDIR)/scripts/utilities/dump_faulthandler_snapshot.py"

.PHONY: studio-collect-test-log-reports
studio-collect-test-log-reports:
	$(PYTHON) .repo_studios/scripts/producers/collect_test_log_reports.py --logs-dir .repo_studios/reports/orchestrator_logs/pytest_log_capture_logs --output-dir .repo_studios/reports/producer_reports/test_log_reports --artifacts-to-keep 10 --log-level INFO

.PHONY: studio-generate-test-log-health-report
studio-generate-test-log-health-report:
	$(PYTHON) .repo_studios/scripts/consumers/generate_test_log_health_report.py --logs-dir .repo_studios/reports/orchestrator_logs/pytest_log_capture_logs --output-base .repo_studios/reports/consumer_reports/test_log_health_reports --producer-report .repo_studios/reports/producer_reports/test_log_reports/latest_report.json --artifacts-to-keep 5 --log-level INFO

.PHONY: studio-diff-standards-index
studio-diff-standards-index:
	$(PYTHON) .repo_studios/scripts/producers/diff_standards_index.py "$(old)" "$(new)" --repo-root . --output-dir .repo_studios/reports/producer_reports/standards_index_diff_reports --artifacts-to-keep 10 --fail-on any --log-level INFO

.PHONY: studio-generate-dependency-hygiene
studio-generate-dependency-hygiene:
	$(PYTHON) .repo_studios/scripts/producers/generate_dependency_hygiene_report.py --repo-root . --output-dir .repo_studios/reports/producer_reports/dependency_hygiene_reports --log-level INFO

.PHONY: studio-generate-code-doc-churn-report
studio-generate-code-doc-churn-report:
	$(PYTHON) .repo_studios/scripts/producers/generate_code_doc_churn_report.py --repo-root . --output-dir .repo_studios/reports/producer_reports/code_doc_churn_reports --git-window "30 days" --artifacts-to-keep 5 --log-level INFO

.PHONY: studio-generate-undocumented-logic-report
studio-generate-undocumented-logic-report:
	$(PYTHON) "$(REPO_ROOT)/.repo_studios/scripts/producers/generate_undocumented_logic_report.py" --repo-root "$(REPO_ROOT)" --output-dir "$(REPO_ROOT)/.repo_studios/reports/producer_reports/undocumented_logic_reports" --include-command-center --log-level INFO

.PHONY: studio-aggregate-docs-health
studio-aggregate-docs-health:
	$(PYTHON) "$(REPO_ROOT)/.repo_studios/scripts/aggregators/aggregate_docs_health_signals.py" --repo-root "$(REPO_ROOT)" --output-dir "$(REPO_ROOT)/.repo_studios/reports/aggregator_reports/docs_health_signals" --log-level INFO

.PHONY: studio-generate-function-index
studio-generate-function-index:
	@$(PYTHON) -c "import sys; sys.exit(0 if '$(path)' else 1)" || (echo "path variable required (make studio-generate-function-index path=...)" && exit 1)
	$(PYTHON) scripts/producers/generate_commandview_inventory.py --repo-root .. "$(path)"
	$(PYTHON) scripts/producers/generate_function_analysis.py --repo-root .. "$(path)"

