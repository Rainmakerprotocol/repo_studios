PYTHON ?= python3

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

.PHONY: studio-generate-function-index
studio-generate-function-index:
	@$(PYTHON) -c "import sys; sys.exit(0 if '$(path)' else 1)" || (echo "path variable required (make studio-generate-function-index path=...)" && exit 1)
	$(PYTHON) .repo_studios/scripts/producers/generate_function_inventory.py --repo-root . "$(path)"
	$(PYTHON) .repo_studios/scripts/producers/generate_function_analysis.py --repo-root . "$(path)"
