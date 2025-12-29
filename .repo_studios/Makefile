REPO_ROOT := $(abspath $(CURDIR)/..)

ifeq ($(OS),Windows_NT)
ifneq ($(wildcard $(REPO_ROOT)/.venv/Scripts/python.exe),)
PYTHON ?= .venv/Scripts/python.exe
else
PYTHON ?= python
endif
else
ifneq ($(wildcard $(REPO_ROOT)/.venv/bin/python),)
PYTHON ?= .venv/bin/python
else
PYTHON ?= python3
endif
endif
LOG_LEVEL ?= INFO
FAIL_ON ?= any

ifneq ($(filter ./% ../% .venv/%,$(PYTHON)),)
	override PYTHON := $(abspath $(REPO_ROOT)/$(PYTHON))
endif

ifeq ($(OS),Windows_NT)
PYTHONPATH_EXPORT := set "PYTHONPATH=$(CURDIR)" &&
else
PYTHONPATH_EXPORT := PYTHONPATH="$(CURDIR)"
endif

.PHONY: command-center
command-center:
ifeq ($(strip $(COMMAND_CENTER_TARGET)),)
	$(error COMMAND_CENTER_TARGET variable required (make command-center COMMAND_CENTER_TARGET=...))
endif
	$(PYTHON) "$(CURDIR)/command_center/scripts/orchestrators/run_command_center_pipeline.py" --repo-root "$(REPO_ROOT)" "$(COMMAND_CENTER_TARGET)"

.PHONY: studio-render-views
studio-render-views:
	$(PYTHON) scripts/producers/render_inventory_views.py

.PHONY: studio-validate-inventory
studio-validate-inventory:
	$(PYTHON) scripts/producers/validate_inventory.py

studio-check-inventory-health: studio-render-views
	$(PYTHON) scripts/producers/check_inventory_health.py --repo-root .. --output-dir command_center/reports

.PHONY: studio-validate-markdown-anchors
studio-validate-markdown-anchors:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) ".repo_studios/scripts/producers/validate_markdown_anchors.py" --repo-root "$(REPO_ROOT)" --output-dir ".repo_studios/reports/producer_reports" --log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-anchor-inventory
studio-generate-anchor-inventory:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) ".repo_studios/scripts/producers/generate_anchor_inventory.py" --repo-root "$(REPO_ROOT)" --docs-root docs --output-dir ".repo_studios/reports/producer_reports" --log-level "$(LOG_LEVEL)"

.PHONY: studio-analyze-standards-index-gaps
studio-analyze-standards-index-gaps:
	$(PYTHON) .repo_studios/scripts/producers/analyze_standards_index_gaps.py --output-dir .repo_studios/reports/producer_reports/standards_gap_reports

.PHONY: studio-scan-code-placeholders
studio-scan-code-placeholders:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/scan_code_placeholders.py" \
		--repo-root . \
		--output-dir .repo_studios/reports/producer_reports \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-scan-monkey-patches
studio-scan-monkey-patches:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/scan_monkey_patches.py" \
		--repo-root . \
		--output-dir .repo_studios/reports/producer_reports \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-seed-standards-prompts
studio-seed-standards-prompts:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/seed_standards_prompts.py" \
		--repo-root . \
		--output-dir .repo_studios/reports/producer_reports \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-validate-import-boundaries
studio-validate-import-boundaries:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/validate_import_boundaries.py" \
		--repo-root . \
		--output-dir .repo_studios/reports/producer_reports \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-import-graph
studio-generate-import-graph:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/generate_import_graph_report.py" \
		--repo-root . \
		--output-dir .repo_studios/reports/producer_reports \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-lizard-report
studio-generate-lizard-report:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/generate_lizard_report.py" \
		--repo-root . \
		--output-dir .repo_studios/reports/producer_reports \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-typecheck-report
studio-generate-typecheck-report:
	cd "$(CURDIR)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		"scripts/producers/generate_typecheck_report.py" \
		--repo-root .. \
		--all \
		--output-dir .repo_studios/reports/producer_reports \
		--artifacts-to-keep 10 \
		--log-level "$(LOG_LEVEL)"

.PHONY: typecheck
typecheck: studio-generate-typecheck-report

.PHONY: studio-validate-metrics-anchor-stubs
studio-validate-metrics-anchor-stubs:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/validate_metrics_anchor_stubs.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/producer_reports" \
		--artifacts-to-keep 10 \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-analyze-test-hardening
studio-analyze-test-hardening:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/analyze_test_hardening.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/healthview" \
		--tests-dir ".repo_studios/tests" \
		--artifacts-to-keep 5 \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-verify-docs-integrity
studio-verify-docs-integrity:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/verify_docs_integrity.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/producer_reports" \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-collect-faulthandler-reports
studio-collect-faulthandler-reports:
	$(PYTHON) scripts/producers/collect_faulthandler_reports.py --runs-dir .repo_studios/command_center/reports/rawview/fault_diagnostics_runs --output-dir .repo_studios/command_center/reports --artifacts-to-keep 10 --log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-fault-artifacts
studio-generate-fault-artifacts:
	$(PYTHON) .repo_studios/scripts/consumers/generate_fault_artifacts.py --output-dir .repo_studios/reports/consumer_reports/fault_artifacts --command-center-dir .repo_studios/command_center/reports/fault_artifacts_consumer --artifacts-to-keep 10 --log-level INFO

.PHONY: studio-orchestrate-fault-diagnostics
studio-orchestrate-fault-diagnostics:
	@echo Running fault diagnostics orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/run_fault_diagnostics_overview.py" \
		--repo-root "$(REPO_ROOT)" --artifacts-to-keep 10 --producer-artifacts-to-keep 10 \
		--consumer-artifacts-to-keep 10 --summarizer-artifacts-to-keep 10 --log-level "$(LOG_LEVEL)"

.PHONY: studio-orchestrate-docs-health
studio-orchestrate-docs-health:
	@echo Running docs health orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/run_docs_health_overview.py" \
		--repo-root "$(REPO_ROOT)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-run-fault-pipeline
studio-run-fault-pipeline: studio-orchestrate-fault-diagnostics

.PHONY: studio-orchestrate-standards
studio-orchestrate-standards:
	@echo Running standards integrity orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/run_standards_integrity.py" \
		--repo-root "$(REPO_ROOT)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-orchestrate-test-execution-telemetry
studio-orchestrate-test-execution-telemetry:
	@echo Running test execution telemetry orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/run_test_execution_telemetry.py" \
		--repo-root "$(REPO_ROOT)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-orchestrate-dependency-import-hygiene
studio-orchestrate-dependency-import-hygiene:
	@echo Running dependency and import hygiene orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/run_dependency_import_hygiene.py" \
		--repo-root "$(REPO_ROOT)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-orchestrate-monkey-patch-oversight
studio-orchestrate-monkey-patch-oversight:
	@echo Running monkey patch oversight orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/run_monkey_patch_oversight.py" \
		--repo-root "$(REPO_ROOT)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-orchestrate-full-diagnostic
studio-orchestrate-full-diagnostic:
	@echo Running full diagnostic orchestrator with log level $(LOG_LEVEL). Override via LOG_LEVEL=DEBUG for verbose output.
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/command_center/scripts/orchestrators/orchestrate_full_diagnostic.py" \
		--repo-root "$(REPO_ROOT)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-configure-faulthandler-runtime-smoke
studio-configure-faulthandler-runtime-smoke:
	$(PYTHON) "$(CURDIR)/scripts/utilities/configure_faulthandler_runtime.py"

.PHONY: studio-dump-faulthandler-snapshot-smoke
studio-dump-faulthandler-snapshot-smoke:
	$(PYTHON) "$(CURDIR)/scripts/utilities/dump_faulthandler_snapshot.py"

.PHONY: studio-refresh-mypy-baselines
studio-refresh-mypy-baselines:
	cd "$(REPO_ROOT)" && $(PYTHON) ".repo_studios/scripts/utilities/refresh_mypy_baselines.py" --repo-root "$(REPO_ROOT)" --log-level INFO

.PHONY: studio-collect-test-log-reports
studio-collect-test-log-reports:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/collect_test_log_reports.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/healthview" \
		--artifacts-to-keep 10 \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-test-log-health-report
studio-generate-test-log-health-report:
	$(PYTHON) .repo_studios/scripts/consumers/generate_test_log_health_report.py --logs-dir .repo_studios/command_center/reports/rawview/test_execution_runs --output-base .repo_studios/reports/healthview/consumer_reports/test_log_health_reports --producer-reports-root .repo_studios/reports/healthview/rawview/test_log_reports --artifacts-to-keep 5 --log-level INFO

.PHONY: studio-diff-standards-index
studio-diff-standards-index:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) ".repo_studios/scripts/producers/diff_standards_index.py" "$(abspath $(old))" "$(abspath $(new))" --repo-root "$(REPO_ROOT)" --output-dir ".repo_studios/command_center/reports" --artifacts-to-keep 10 --fail-on "$(FAIL_ON)" --log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-dependency-hygiene
studio-generate-dependency-hygiene:
	$(PYTHON) .repo_studios/scripts/producers/generate_dependency_hygiene_report.py --repo-root . --output-dir .repo_studios/reports/producer_reports --log-level INFO

.PHONY: studio-generate-doc-index
studio-generate-doc-index:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) ".repo_studios/scripts/producers/generate_doc_index.py" --repo-root "$(REPO_ROOT)" --output-dir ".repo_studios/reports/producer_reports" --artifacts-to-keep 1 --log-level "$(LOG_LEVEL)"

.PHONY: doc-index
doc-index:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) ".repo_studios/scripts/producers/generate_doc_index.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/producer_reports" \
		--artifacts-to-keep 1 \
		--refresh-checkbox-report \
		--refresh-tier3-index \
		--log-level "$(LOG_LEVEL)"

HEALTHVIEW_AGENT_WORKFLOW_SPEC ?= .repo_studios/docs/pipeline/healthview_orchestration_pipeline/workflows/healthview_agent_execution_loop.v1.yaml

.PHONY: healthview-agent-validate-workflow
healthview-agent-validate-workflow:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/utilities/validate_healthview_agent_workflow_spec.py" \
		--spec "$(HEALTHVIEW_AGENT_WORKFLOW_SPEC)" \
		--log-level "$(LOG_LEVEL)"

.PHONY: healthview-agent-next
healthview-agent-next: healthview-agent-validate-workflow
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py" \
		--repo-root "$(REPO_ROOT)" \
		--spec "$(HEALTHVIEW_AGENT_WORKFLOW_SPEC)" \
		--log-level "$(LOG_LEVEL)"

.PHONY: healthview-agent-next-compact
healthview-agent-next-compact: healthview-agent-validate-workflow
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/orchestrators/healthview/run_healthview_agent_loop.py" \
		--repo-root "$(REPO_ROOT)" \
		--spec "$(HEALTHVIEW_AGENT_WORKFLOW_SPEC)" \
		--log-level "$(LOG_LEVEL)" \
		--compact

.PHONY: studio-generate-test-coverage-inventory
studio-generate-test-coverage-inventory:
	@echo Running test coverage inventory producer with log level $(LOG_LEVEL).
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/generate_test_coverage_inventory.py" \
		--repo-root "$(REPO_ROOT)" \
		--coverage-xml ".repo_studios/tmp_cli_probe/coverage_repo.xml" \
		--refresh-coverage-xml \
		--refresh-continue-on-error \
		--refresh-omit-tests \
		--refresh-cov-target "." \
		--refresh-tests \
			".repo_studios/tests" \
		--output-dir ".repo_studios/reports/healthview" \
		--artifacts-to-keep 5 \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-churn-complexity-heatmap
studio-generate-churn-complexity-heatmap:
	$(PYTHON) .repo_studios/scripts/aggregators/generate_churn_complexity_heatmap.py --repo-root . --output-base .repo_studios/reports/healthview/aggregator_reports/churn_complexity_heatmap --test-log-summary .repo_studios/reports/healthview/consumer_reports/test_log_health_reports --artifacts-to-keep 5 --log-level INFO

.PHONY: studio-generate-code-doc-churn-report
studio-generate-code-doc-churn-report:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/generate_code_doc_churn_report.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/producer_reports" \
		--git-window "30 days" \
		--artifacts-to-keep 5 \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-undocumented-logic-report
studio-generate-undocumented-logic-report:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/producers/generate_undocumented_logic_report.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/producer_reports" \
		--include-command-center \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-aggregate-docs-health
studio-aggregate-docs-health:
	cd "$(REPO_ROOT)" && $(PYTHONPATH_EXPORT) $(PYTHON) \
		".repo_studios/scripts/aggregators/aggregate_docs_health_signals.py" \
		--repo-root "$(REPO_ROOT)" \
		--output-dir ".repo_studios/reports/aggregator_reports/docs_health_signals" \
		--log-level "$(LOG_LEVEL)"

.PHONY: studio-generate-function-index
studio-generate-function-index:
	@$(PYTHON) -c "import sys; sys.exit(0 if '$(path)' else 1)" || (echo "path variable required (make studio-generate-function-index path=...)" && exit 1)
	$(PYTHON) scripts/producers/generate_commandview_inventory.py --repo-root .. "$(path)"
	$(PYTHON) scripts/producers/generate_function_analysis.py --repo-root .. "$(path)"

