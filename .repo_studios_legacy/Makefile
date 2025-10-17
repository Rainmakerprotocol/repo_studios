# Documentation integrity & lint
.PHONY: docs-integrity
docs-integrity:
	@echo "[docs-integrity] Verifying governed documentation hashes..."
	@python scripts/verify_docs_integrity.py --index docs/standards/docs_index.md || (echo "Hash verification failed" && exit 1)
	@echo "[docs-integrity] Running markdown lint (subset) ..."
	@grep -R --include='*.md' -n '<<<<<<<' . >/dev/null 2>&1 && (echo 'Merge conflict markers present in docs' && exit 1) || true
	@echo "[docs-integrity] Complete"

# Refresh mypy baselines (captures current full outputs for agents + monitoring scopes)
.PHONY: mypy-refresh-baselines
mypy-refresh-baselines:
	@echo "[mypy-baseline] Refreshing mypy baseline artifacts..."; \
	TS=$$(date +"%Y-%m-%d_%H%M%S"); \
	OUT1=mypy_agents_full.txt; OUT2=mypy_monitoring_full.txt; \
	echo "[mypy-baseline] Writing $$OUT1"; \
	$(PYTHON) -m mypy --hide-error-context --no-error-summary agents > $$OUT1 2>&1 || true; \
	echo "[mypy-baseline] Writing $$OUT2"; \
	$(PYTHON) -m mypy --hide-error-context --no-error-summary agents/core/monitoring > $$OUT2 2>&1 || true; \
	printf "# Refreshed: %s\n" "$$TS" >> $$OUT1; \
	printf "# Refreshed: %s\n" "$$TS" >> $$OUT2; \
	echo "[mypy-baseline] Done (timestamp $$TS)"

# ---------------------------------------------------------------------------
# Standards index (schema + rules consolidation)
#   make standards-index          Build and run validation tests
#   make standards-index-build    Build only
#   make standards-index-test     Build then run tests
#   make standards-index-cli      Run query CLI (ARGS="list|stats|search <q>|show <id>")
#   make standards-index-diff     Diff two index files (OLD=path NEW=path [FAIL=severity_changed,added,...])
#   make standards-index-gap      Run gap detector (GAP_JSON=path for JSON)
#   make standards-enforce        Run enforcement stub (ENFORCE_JSON=path FAIL_ON=error)
#   make standards-prompt-seed    Generate prompt seed (SEED_FORMAT=text|yaml|json SEED_OUT=path)
#   make standards-metrics        Scrape /metrics and print standards_* lines (dev helper)
#   make standards-grow           Single-step extraction (ACCEPT=1 to auto-accept, TEST=0 to skip tests)
# ---------------------------------------------------------------------------
.PHONY: standards-index standards-index-build standards-index-test standards-index-cli standards-index-diff standards-index-gap standards-enforce standards-prompt-seed standards-metrics standards-grow
standards-index-build:
	@echo "[standards-index] Building consolidated standards index..."; \
	$(PYTHON) .repo_studios/build_standards_index.py

standards-index-test: standards-index-build
	@echo "[standards-index] Running standards index tests..."; \
	$(PYTHON) -m pytest -q tests/test_standards_index.py

standards-index: standards-index-test
	@echo "[standards-index] Complete"

standards-index-cli: ## Query standards index (ARGS="list|stats|search <q>|show <id>")
	@ARGS=$${ARGS:-stats}; \
	echo "[standards-cli] Running '$$ARGS'"; \
	PYTHONPATH=. $(PYTHON) scripts/standards_index_cli.py $$ARGS

standards-index-diff: ## Diff two index YAMLs (OLD=path NEW=path FAIL=commaKinds)
	@OLD=$${OLD:?Set OLD=<old_index.yaml>}; \
	NEW=$${NEW:?Set NEW=<new_index.yaml>}; \
	FAIL_ON=$${FAIL:-severity_changed,added,removed}; \
	echo "[standards-diff] Comparing $$OLD vs $$NEW (failOn=$$FAIL_ON)"; \
	PYTHONPATH=. $(PYTHON) scripts/standards_index_diff.py --old $$OLD --new $$NEW --fail-on $$FAIL_ON

standards-index-gap: ## Detect candidate directives missing from index (GAP_JSON optional)
	@OUT=$${GAP_JSON:-.repo_studios/standards_gap_report.json}; \
	mkdir -p .repo_studios || true; \
	echo "[standards-gap] Scanning for uncovered directives (json=$$OUT)"; \
	PYTHONPATH=. $(PYTHON) scripts/standards_index_gap.py --json $$OUT || true; \
	echo "[standards-gap] Report: $$OUT"

standards-enforce: ## Run enforcement stub across repo (ENFORCE_JSON optional, FAIL_ON=error|warn)
	@OUT=$${ENFORCE_JSON:-.repo_studios/standards_enforce_report.json}; \
	FAIL_ON=$${FAIL_ON:-error}; \
	mkdir -p .repo_studios || true; \
	echo "[standards-enforce] Enforcing (threshold=$$FAIL_ON)"; \
	PYTHONPATH=. $(PYTHON) scripts/standards_enforce_stub.py --json $$OUT --fail-on $$FAIL_ON || RC=$$?; \
	RC=$${RC:-0}; \
	echo "[standards-enforce] Report: $$OUT (rc=$$RC)"; \
	exit $$RC

standards-prompt-seed: ## Generate condensed prompt seed (SEED_FORMAT=text|yaml|json; SEED_OUT optional)
	@FMT=$${SEED_FORMAT:-text}; \
	OUT=$${SEED_OUT:-}; \
	CMD="$(PYTHON) scripts/standards_prompt_seed.py --format $$FMT"; \
	if [ -n "$$OUT" ]; then CMD="$$CMD --out $$OUT"; fi; \
	echo "[standards-seed] Format=$$FMT Output=$${OUT:-stdout}"; \
	PYTHONPATH=. eval "$$CMD"

standards-metrics: ## Scrape running /metrics endpoint (best-effort) and echo standards lines
	@HOST=$${STANDARDS_METRICS_HOST:-127.0.0.1}; \
	PORT=$${STANDARDS_METRICS_PORT:-8010}; \
	echo "[standards-metrics] Scraping http://$$HOST:$$PORT/metrics"; \
	$(PYTHON) -c "import http.client,os,sys;h=os.environ.get('STANDARDS_METRICS_HOST','127.0.0.1');p=int(os.environ.get('STANDARDS_METRICS_PORT','8010'));\ntry:\n\tc=http.client.HTTPConnection(h,p,timeout=2);c.request('GET','/metrics');r=c.getresponse();data=r.read().decode();found=False\n\n\tfor line in data.splitlines():\n\t\tif line.startswith('standards_'): print(line);found=True\n\n\tif not found: print('# no standards_* lines found (server not running or integration failed)')\nexcept Exception as e: print('# warning: could not scrape /metrics:',e); sys.exit(0)"

# ---- Systemd verification helper -------------------------------------------------
.PHONY: systemd-verify
systemd-verify: ## Run 'systemd-analyze verify' on orchestrator + target (skips if tool absent)
	@which systemd-analyze >/dev/null 2>&1 || { echo "[systemd-verify][SKIP] systemd-analyze not installed"; exit 0; }
	@echo "[systemd-verify] Verifying systemd/jarvis-orchestrator.service"; \
	systemd-analyze verify systemd/jarvis-orchestrator.service || { echo "[systemd-verify][FAIL] orchestrator"; exit 1; }; \
	if [ -f systemd/jarvis.target ]; then echo "[systemd-verify] Verifying systemd/jarvis.target"; systemd-analyze verify systemd/jarvis.target || { echo "[systemd-verify][FAIL] target"; exit 1; }; fi; \
	echo "[systemd-verify] OK"

standards-grow: ## One-shot standards extraction (ACCEPT=1 auto-accept; TEST=0 skip tests)
	@ACCEPT=$${ACCEPT:-0}; TEST=$${TEST:-1}; \
	echo "[standards-grow] Starting (auto_accept=$$ACCEPT tests=$$TEST)"; \
	ENABLE_STANDARDS_EXTRACTION=1 AUTO_ACCEPT_EXTRACTED=$$ACCEPT $(PYTHON) .repo_studios/build_standards_index.py || { echo "[standards-grow][FATAL] build failed"; exit 1; }; \
	if [ "$$ACCEPT" = "0" ]; then \
	  if [ -f repo_standards_pending.yaml ]; then echo "[standards-grow] Pending: repo_standards_pending.yaml"; else echo "[standards-grow][WARN] No pending file produced"; fi; \
	fi; \
	if [ "$$TEST" = "1" ]; then \
	  $(PYTHON) -m pytest -q tests/test_standards_extraction.py || echo "[standards-grow][WARN] extraction tests failed"; \
	fi; \
	$(PYTHON) scripts/standards_summary.py --label grow || true; \
	echo "[standards-grow] Done"

# Convenience wrapper: build + auto-accept extraction + tests + summary in ONE command
.PHONY: standards-sync
standards-sync: ## Build + auto-accept extraction + run extraction tests + concise summary
	@echo "[standards-sync] Starting full sync (auto-accept + tests)"; \
	ENABLE_STANDARDS_EXTRACTION=1 AUTO_ACCEPT_EXTRACTED=1 $(PYTHON) .repo_studios/build_standards_index.py || { echo "[standards-sync][FATAL] build failed"; exit 1; }; \
	$(PYTHON) -m pytest -q tests/test_standards_extraction.py || echo "[standards-sync][WARN] extraction tests failed"; \
	$(PYTHON) scripts/standards_summary.py --label sync || true; \
	echo "[standards-sync] Done"

# Minimal single-command helpers (thin wrappers around existing standards-grow / standards-sync)
.PHONY: standards-extract standards-extract-accept standards-extract-summary
standards-extract: ## Run heuristic extraction (no auto-accept) + summary (alias of standards-grow)
	@$(MAKE) --no-print-directory standards-grow ACCEPT=0 TEST=$${TEST:-1}

standards-extract-accept: ## Run heuristic extraction with auto-accept + summary (alias of standards-sync)
	@$(MAKE) --no-print-directory standards-sync

standards-extract-summary: ## Print concise summary of current index extraction metadata
	@$(PYTHON) scripts/standards_summary.py --label summary || true

# Systemd inventory integrity (report-only)
.PHONY: systemd-inventory-manifest systemd-inventory-check
systemd-inventory-manifest: ## Generate inventory + integrity manifest (report-only)
	@echo "[systemd-inventory] Generating inventory + manifest"; \
	$(PYTHON) scripts/systemd_inventory.py --dir systemd --out-dir . --write-integrity || { echo "[systemd-inventory][FATAL] generation failed"; exit 1; }

systemd-inventory-check: ## Regenerate inventory & compare against existing manifest (report-only; exit 0 always)
	@BASE=$${BASELINE:-inventory_integrity.json}; \
	if [ ! -f "$$BASE" ]; then echo "[systemd-inventory-check][WARN] Baseline $$BASE missing (run make systemd-inventory-manifest)"; fi; \
	echo "[systemd-inventory-check] Regenerating & comparing (baseline=$$BASE)"; \
	$(PYTHON) scripts/systemd_inventory.py --dir systemd --out-dir . --compare-integrity $$BASE || true; \
	echo "[systemd-inventory-check] Done (non-blocking)"

.PHONY: systemd-security-validate
systemd-security-validate: ## Run security hardening validator (report-only) -> outputs security_report.json + security_report.md
	@echo "[systemd-security] Validating security directives (report-only)"; \
	$(PYTHON) scripts/validate_systemd_security.py --dir systemd --format json > security_report.json; \
	$(PYTHON) scripts/validate_systemd_security.py --dir systemd --format markdown > security_report.md; \
	echo "[systemd-security] Summary:"; \
	cat security_report.json | grep -E 'severity_counts' -q || cat security_report.json; \
	echo "[systemd-security] Done (see security_report.*)"

.PHONY: systemd-inventory-all
systemd-inventory-all: ## Generate manifest + summary JSON and compare against baseline if present (report-only)
	@BASE=$${BASELINE:-inventory_integrity.json}; TMP_BASE=.inventory_integrity.prev.json; \
	if [ -f "$$BASE" ]; then cp "$$BASE" "$$TMP_BASE"; echo "[systemd-inventory-all] Preserved baseline -> $$TMP_BASE"; fi; \
	SUMMARY=inventory_summary.json; \
	echo "[systemd-inventory-all] Generating inventory, manifest, summary"; \
	$(PYTHON) scripts/systemd_inventory.py --dir systemd --out-dir . --write-integrity --summary-json $$SUMMARY || { echo "[systemd-inventory-all][FATAL] generation failed"; rm -f "$$TMP_BASE"; exit 1; }; \
	if [ -f "$$TMP_BASE" ]; then \
	  echo "[systemd-inventory-all] Comparing against preserved baseline"; \
	  $(PYTHON) scripts/systemd_inventory.py --dir systemd --out-dir . --compare-integrity $$TMP_BASE --summary-json $$SUMMARY || true; \
	  rm -f "$$TMP_BASE"; \
	else \
	  echo "[systemd-inventory-all][INFO] No existing baseline to compare"; \
	fi; \
	echo "[systemd-inventory-all] Done (non-blocking)"

# Codacy integration helpers (best-effort local invocation)
.PHONY: codacy-analyze codacy-analyze-file
codacy-analyze: ## Run Codacy CLI analysis for full repo (if available)
	@if command -v codacy >/dev/null 2>&1; then \
	  echo "[codacy] Running full analysis"; \
	  codacy analyze || echo "[codacy][WARN] analysis returned non-zero"; \
	else \
	  echo "[codacy][WARN] codacy CLI not installed (skip). Install via extension or 'codacy-cli' binary."; \
	fi

codacy-analyze-file: ## Run Codacy CLI analysis for a single file (FILE=path)
	@FILE=$${FILE:?Set FILE=<path/to/file>}; \
	if command -v codacy >/dev/null 2>&1; then \
	  echo "[codacy] Analyzing $$FILE"; \
	  codacy analyze --filename "$$FILE" || echo "[codacy][WARN] file analysis returned non-zero"; \
	else \
	  echo "[codacy][WARN] codacy CLI not installed (skip)"; \
	fi
# Root build / test convenience targets
# Default to the active Python on PATH; override with `make PYTHON=/path/to/python ...` if needed.
PYTHON?=python

# Nightly git automation (manual + cron helpers)
NIGHTLY_COMMIT_SCRIPT:=scripts/nightly_commit.py
NIGHTLY_BRANCH?=main
NIGHTLY_MAX_FILES?=200
NIGHTLY_LINT?=ruff check
NIGHTLY_TEST?=
NIGHTLY_LOG_DIR?=artifacts
NIGHTLY_FAILURE_LOG?=artifacts/nightly_commit_failures.log
NIGHTLY_EXTRA_ARGS?=

.PHONY: nightly-commit nightly-commit-dry nightly-commit-review git git-plan

nightly-commit: ## Run full nightly commit workflow (requires clean repo; pushes on success)
	@$(PYTHON) $(NIGHTLY_COMMIT_SCRIPT) run \
		--branch "$(NIGHTLY_BRANCH)" \
		--max-files $(NIGHTLY_MAX_FILES) \
		--lint-target "$(NIGHTLY_LINT)" \
		$(if $(strip $(NIGHTLY_TEST)),--test-command "$(NIGHTLY_TEST)",) \
		--log-dir "$(NIGHTLY_LOG_DIR)" \
		--failure-log "$(NIGHTLY_FAILURE_LOG)" \
		--use-real-secret-scan \
		$(NIGHTLY_EXTRA_ARGS)

nightly-commit-dry: ## Preview nightly commit workflow without writing commits
	@$(PYTHON) $(NIGHTLY_COMMIT_SCRIPT) run \
		--dry-run \
		--show-diff \
		--branch "$(NIGHTLY_BRANCH)" \
		--max-files $(NIGHTLY_MAX_FILES) \
		--lint-target "$(NIGHTLY_LINT)" \
		$(if $(strip $(NIGHTLY_TEST)),--test-command "$(NIGHTLY_TEST)",) \
		--log-dir "$(NIGHTLY_LOG_DIR)" \
		--failure-log "$(NIGHTLY_FAILURE_LOG)" \
		--use-real-secret-scan \
		$(NIGHTLY_EXTRA_ARGS)
	@echo "[nightly-commit] Preview finished; launching manual approval flow (make git)."
	@$(MAKE) --no-print-directory git

nightly-commit-review: ## Show grouping plan for current changes (no checks)
	@$(PYTHON) $(NIGHTLY_COMMIT_SCRIPT) review \
		--branch "$(NIGHTLY_BRANCH)" \
		--max-files $(NIGHTLY_MAX_FILES) \
		--show-diff

git: ## Manual safeguarded commit that requires explicit approval (prompts "approve")
	@$(PYTHON) $(NIGHTLY_COMMIT_SCRIPT) run \
		--branch "$(NIGHTLY_BRANCH)" \
		--max-files $(NIGHTLY_MAX_FILES) \
		--lint-target "$(NIGHTLY_LINT)" \
		$(if $(strip $(NIGHTLY_TEST)),--test-command "$(NIGHTLY_TEST)",) \
		--log-dir "$(NIGHTLY_LOG_DIR)" \
		--failure-log "$(NIGHTLY_FAILURE_LOG)" \
		--use-real-secret-scan \
		--require-approval \
		--approval-prompt "Type 'approve' to land these commits (or anything else to abort): " \
		--show-diff \
		$(NIGHTLY_EXTRA_ARGS)

git-plan: ## Approval preview for manual flow (no commits)
	@$(PYTHON) $(NIGHTLY_COMMIT_SCRIPT) run \
		--dry-run \
		--branch "$(NIGHTLY_BRANCH)" \
		--max-files $(NIGHTLY_MAX_FILES) \
		--lint-target "$(NIGHTLY_LINT)" \
		$(if $(strip $(NIGHTLY_TEST)),--test-command "$(NIGHTLY_TEST)",) \
		--log-dir "$(NIGHTLY_LOG_DIR)" \
		--failure-log "$(NIGHTLY_FAILURE_LOG)" \
		--use-real-secret-scan \
		--require-approval \
		--approval-prompt "Type 'approve' to land these commits (dry run; nothing will happen): " \
		--show-diff \
		$(NIGHTLY_EXTRA_ARGS)

# --- Benchmark agent helpers -------------------------------------------------
# Usage examples:
#   make bench-agent-consume SUITE=api-fast JUNIT=.repo_studios/pytest_logs/junit_2025-09-25_1405.xml
#   make bench-agent-run SUITE=api-fast ARGS="tests/api -k smoke"
bench-agent-consume:
	@python agents/benchmark/agent.py --suite "$(SUITE)" --from-junit "$(JUNIT)" --mrp-dir mrp/benchmark

# Service management orchestrator focused tests (startup/shutdown/agents)
.PHONY: service-start-tests
service-start-tests:
	@echo "Running service management focused tests"; \
	$(PYTHON) -m pytest -q tests/agents/service_management/test_service_start_metrics_tier.py \
	  tests/agents/service_management/test_service_start_shutdown_snapshot.py \
	  tests/agents/service_management/test_service_start_dynamic_agent_registry.py

bench-agent-run:
	@python agents/benchmark/agent.py --suite "$(SUITE)" --run-subset -- $(ARGS)

# Convenience: run API fast suite via Benchmark agent (default subset)
.PHONY: bench-fast-api
bench-fast-api:
	@SUITE=$${SUITE:-api-fast}; \
	 ARGS=$${ARGS:-"api/tests -k 'not heavy and not slow'"}; \
	 echo "[bench] Running $$SUITE with ARGS=$$ARGS"; \
	 python agents/benchmark/agent.py --suite "$$SUITE" --run-subset -- $$ARGS

.PHONY: test
test:
	$(PYTHON) -m pytest -q

.PHONY: perf
perf:
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 5

.PHONY: perf-ci
perf-ci:
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 5 --max-avg-latency-ms 100 --max-p95-latency-ms 150 --max-avg-drift-ms 5 --max-p95-drift-ms 20

.PHONY: perf-report
perf-report:
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 10 --csv-output perf_samples.csv
	@echo "CSV written to perf_samples.csv"

.PHONY: perf-baseline
perf-baseline:
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 5 --json-output perf_baseline.json > /dev/null
	@echo "Baseline written to perf_baseline.json"

.PHONY: perf-compare
perf-compare:
	@test -f perf_baseline.json || (echo "Missing perf_baseline.json; run make perf-baseline first" && exit 1)
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 5 --baseline-json perf_baseline.json --percentiles 50,90,99

.PHONY: perf-baseline-update
perf-baseline-update:
	# Update baseline only when thresholds pass (use on protected main branch)
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 5 --json-output perf_baseline.new.json --percentiles 50,90,99
	@mv perf_baseline.new.json perf_baseline.json
	@echo "Baseline updated (perf_baseline.json)"

.PHONY: perf-ci-report
perf-ci-report:
	@mkdir -p perf_history
	$(PYTHON) tests/perf/generate_metrics.py --rate 500 --duration 5 --percentiles 50,90,99 --md-output perf_summary.md --save-history-dir perf_history --json-output perf_last.json --include-raw
	$(PYTHON) tests/perf/aggregate_history.py --history-dir perf_history --output perf_trend.md
	@echo "Generated perf_summary.md and perf_trend.md"

.PHONY: perf-graph
perf-graph:
	@test -f perf_last.json || (echo "Need perf_last.json (run perf-ci-report or harness)" && exit 1)
	$(PYTHON) tests/perf/render_graph.py --input perf_last.json --output perf_graph.png
	@echo "Graph at perf_graph.png"

# Repo health add-ons: dependency hygiene and import graph
.PHONY: dep-health import-graph
dep-health:
	@echo "Generating dependency hygiene report..."
	$(PYTHON) .repo_studios/dep_hygiene_report.py --repo-root . --output-base .repo_studios/dep_health
	@echo "Done (see .repo_studios/dep_health)"

import-graph:
	@echo "Generating import graph report..."
	$(PYTHON) .repo_studios/import_graph_report.py --repo-root . --output-base .repo_studios/import_graph
	@echo "Done (see .repo_studios/import_graph)"

# ------------------------------------------------------------
# Models onboarding convenience
#   models-refresh    Re-scan models dir and persist registry.json
#   models-list       Print JSON list of models (name/family/quant/ctx)
#   models-health     Generate health report JSON (also saves diagnostics)
#   model-run         Run a quick inference via llama-cli pipeline
# ------------------------------------------------------------
.PHONY: models-refresh models-list models-health model-run models-benchmark models-optimize

models-refresh:
	@PYTHONPATH=. $(PYTHON) scripts/models_cli.py --models-dir /home/founder/jarvis2/models --registry /home/founder/jarvis2/models/registry.json refresh

models-list:
	@PYTHONPATH=. $(PYTHON) scripts/models_cli.py --models-dir /home/founder/jarvis2/models --registry /home/founder/jarvis2/models/registry.json list

models-health:
	@PYTHONPATH=. $(PYTHON) scripts/models_cli.py --models-dir /home/founder/jarvis2/models --registry /home/founder/jarvis2/models/registry.json health

# Usage: make model-run NAME=<model_name_without_suffix> SYSTEM="You are helpful." USER="hi"
model-run:
	@NAME=$${NAME:?Set NAME=model_stem_without_.gguf}; \
	 SYS=$${SYSTEM:-You are a helpful assistant.}; \
	 USR=$${USER:-Hello}; \
	 PYTHONPATH=. $(PYTHON) scripts/models_cli.py --models-dir /home/founder/jarvis2/models --registry /home/founder/jarvis2/models/registry.json run --name "$$NAME" --system "$$SYS" --user "$$USR"

# Usage: make models-benchmark NAME=<model_name> [PROMPTS=prompts.json]
models-benchmark:
	@NAME=$${NAME:?Set NAME=model_stem_without_.gguf}; \
	 PR=$${PROMPTS:-}; \
	 PYTHONPATH=. $(PYTHON) scripts/models_cli.py --models-dir /home/founder/jarvis2/models --registry /home/founder/jarvis2/models/registry.json benchmark --name "$$NAME" $${PR:+--prompts "$$PR"}

# Usage: make models-optimize [VRAM=12000]
models-optimize:
	@VRAM=$${VRAM:-}; \
	 PYTHONPATH=. $(PYTHON) scripts/models_cli.py --models-dir /home/founder/jarvis2/models --registry /home/founder/jarvis2/models/registry.json optimize $${VRAM:+--vram "$$VRAM"}

# Faulthandler CI enforcement gate
.PHONY: fault-ci-gate
fault-ci-gate:
	@echo "Running faulthandler CI gate..."
	$(PYTHON) scripts/ci_faulthandler_gate.py
	@echo "Gate completed"

# Fault diagnostics artifact generation
.PHONY: fault-artifacts
fault-artifacts:
	@echo "Generating fault artifacts (auto-select latest FAULT_OUTDIR if not set)"
	$(PYTHON) .repo_studios/generate_fault_artifacts.py || true

.PHONY: check-imports
check-imports: import-graph ## Generate graph and enforce layering/cycles (fails on violations)
	@echo "Checking import boundaries..."
	$(PYTHON) .repo_studios/check_import_boundaries.py || (echo "Import boundary violations detected" && exit 1)

# Additional health angles: test-log health and churn×complexity heatmap
.PHONY: test-health
test-health:
	@echo "Generating test log health report..."
	$(PYTHON) .repo_studios/test_log_health_report.py --logs-dir .repo_studios/pytest_logs --output-base .repo_studios/test_health
	@echo "Done (see .repo_studios/test_health)"

.PHONY: churn-complexity
churn-complexity:
	@echo "Generating churn × complexity heatmap..."
	$(PYTHON) .repo_studios/churn_complexity_heatmap.py --repo-root . --output-base .repo_studios/churn_complexity --logs-dir .repo_studios/pytest_logs
	@echo "Done (see .repo_studios/churn_complexity)"

# Combined Health Suite: repo insight + dep health + import graph + summary
.PHONY: health-suite
health-suite: ## Run health suite with tolerant orchestrator (continues on errors; per-step logs)
	@TS=$${TS:-$$(date +"%Y-%m-%d_%H%M")}; ACCEPT=$${EXTRACT_ACCEPT:-0}; TEST_EXTRACT=$${EXTRACT_TEST:-1}; \
	echo "Running health suite orchestrator (TS=$$TS)..."; \
	$(PYTHON) .repo_studios/health_suite_orchestrator.py --timestamp $$TS $(if $(LIVE),--live,) || true; \
	echo "[health-suite] Running standards extraction (accept=$$ACCEPT test=$$TEST_EXTRACT)"; \
	if [ "$$ACCEPT" = "1" ]; then $(MAKE) --no-print-directory standards-extract-accept || true; else $(MAKE) --no-print-directory standards-extract TEST=$$TEST_EXTRACT || true; fi; \
	$(MAKE) --no-print-directory standards-extract-summary || true; \
	echo "Health suite orchestrator finished. See .repo_studios/health_suite/logs/$$TS and summary under .repo_studios/health_suite/health_suite_$${TS}.md (if generated)."

.PHONY: health-suite-legacy
health-suite-legacy: repo-insight dep-health import-graph test-health churn-complexity classify-monkey-patches
	@echo "Composing health suite summary (legacy chain)..."
	@TS=$$(date +"%Y-%m-%d_%H%M"); \
	 $(PYTHON) .repo_studios/health_suite_summary.py --repo-root . --output-dir .repo_studios/health_suite --timestamp $$TS; \
	 echo "Health suite complete (summary at .repo_studios/health_suite/health_suite_$${TS}.md)";

.PHONY: soft-ci-gates
soft-ci-gates:
	@echo "Running soft CI gates (deps/test-warns/monkey-patch)..."
	$(PYTHON) scripts/soft_ci_gates.py || true

.PHONY: perf-diff
perf-diff:
	@test -f perf_baseline.json -a -f perf_last.json || (echo "Need perf_baseline.json and perf_last.json" && exit 1)
	$(PYTHON) tests/perf/diff_perf.py --old perf_baseline.json --new perf_last.json --output perf_diff.md
	@echo "Diff written to perf_diff.md"

# Intent Router config validation
.PHONY: intent-config-validate
intent-config-validate: ## Validate intent router config (env-driven; falls back to sample)
	@PATH_P=$${INTENT_ROUTER_PATTERNS_PATH:-}; \
	 JSON_P=$${INTENT_ROUTER_PATTERNS_JSON:-}; \
	 if [ -n "$$JSON_P" ]; then \
	   INTENT_ROUTER_PATTERNS_JSON="$$JSON_P" PYTHONPATH=. $(PYTHON) scripts/validate_intent_router_config.py; \
	 elif [ -n "$$PATH_P" ]; then \
	   INTENT_ROUTER_PATTERNS_PATH="$$PATH_P" PYTHONPATH=. $(PYTHON) scripts/validate_intent_router_config.py; \
	 else \
	   PYTHONPATH=. $(PYTHON) scripts/validate_intent_router_config.py --path manifests/intent_router_config.v1.sample.json; \
	 fi

.PHONY: metrics-ui-ready
metrics-ui-ready:
	@echo "Verifying metrics UI readiness..."
	$(PYTHON) scripts/verify_metrics_ui_readiness.py

# Developer helper: seed schema_meta (if missing) and start the local metrics exporter
# on a non-conflicting port (defaults to 9101). Override with METRICS_DB_PATH and
# EXPORTER_PORT as needed.
.PHONY: metrics-exporter-dev
metrics-exporter-dev:
	@DB=$${METRICS_DB_PATH:-/tmp/metrics.db}; \
	 PORT=$${EXPORTER_PORT:-9101}; \
	 echo "Preparing $$DB (ensure schema_meta exists with >=1 row)..."; \
	 $(PYTHON) - <<-PY
	import os, sqlite3, time
	p = os.environ.get('METRICS_DB_PATH', '/tmp/metrics.db')
	conn = sqlite3.connect(p)
	cur = conn.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS schema_meta(version INTEGER NOT NULL, applied_at INTEGER NOT NULL)")
	cur.execute("SELECT COUNT(*) FROM schema_meta")
	if (cur.fetchone() or [0])[0] == 0:
	    cur.execute("INSERT INTO schema_meta(version, applied_at) VALUES (?,?)", (1, int(time.time()*1000)))
	    conn.commit()
	conn.close()
	print("DB ready:", p)
	PY
	@echo "Starting exporter on 127.0.0.1:$$PORT (Ctrl+C to stop)"; \
	 $(PYTHON) -m agents.core.monitoring.exporter --db $$DB --host 127.0.0.1 --port $$PORT

# UI benchmark targets
.PHONY: bench-ui-snapshot
bench-ui-snapshot:
	BENCH_ENDPOINT?=http://localhost:8010/ui/sidebar/snapshot ; \
	BENCH_LABEL?=snapshot-post-caching ; \
	$(PYTHON) scripts/bench_ui_snapshot.py

.PHONY: bench-ui-snapshot-pre
bench-ui-snapshot-pre:
	BENCH_ENDPOINT?=http://localhost:8010/ui/sidebar/snapshot ; \
	BENCH_LABEL=snapshot-pre-caching UI_DISABLE_SIDEBAR_CACHE=1 DISABLE_API_CACHE=1 $(PYTHON) scripts/bench_ui_snapshot.py

.PHONY: bench-ui-catalog
bench-ui-catalog:
	BENCH_ENDPOINT?=http://localhost:8010/ui/metrics/catalog ; \
	BENCH_LABEL?=catalog-post-caching ; \
	$(PYTHON) scripts/bench_ui_catalog.py

.PHONY: bench-ui-catalog-pre
bench-ui-catalog-pre:
	BENCH_ENDPOINT?=http://localhost:8010/ui/metrics/catalog ; \
	BENCH_LABEL=catalog-pre-caching DISABLE_API_CACHE=1 $(PYTHON) scripts/bench_ui_catalog.py

.PHONY: bench-ui-plot
bench-ui-plot:
	$(PYTHON) scripts/plot_ui_bench.py

.PHONY: bench-ui-report
bench-ui-report:
	$(PYTHON) scripts/generate_ui_bench_report.py

.PHONY: bench-ui-dashboard
bench-ui-dashboard:
	$(PYTHON) scripts/generate_ui_dashboard.py

.PHONY: ui-pre-post-assert
ui-pre-post-assert:
	$(PYTHON) scripts/ci_assert_ui_pre_post.py

.PHONY: bench-ui-pre-post
bench-ui-pre-post:
	ENDPOINT?=http://localhost:8010/ui/sidebar/snapshot ; \
	$(PYTHON) scripts/bench_ui_pre_post_compare.py

# Heavy snapshot benchmark (mixed heavy/light calls)
.PHONY: bench-ui-snapshot-heavy
bench-ui-snapshot-heavy:
	HEAVY_ENDPOINT?=http://localhost:8010/ui/sidebar/snapshot ; \
	HEAVY_LABEL?=snapshot-heavy-mixed ; \
	$(PYTHON) scripts/bench_ui_snapshot_heavy.py

.PHONY: ui-latency-assert
ui-latency-assert:
	@test -f perf_history/ui_endpoints.json || (echo "No perf_history/ui_endpoints.json; run benchmark first" && exit 1)
	$(PYTHON) scripts/ci_assert_ui_latency.py --label snapshot-pre-caching:2.0 --label post-caching:2.5 --label catalog-pre-caching:2.0 --label catalog-post-caching:2.5

# Release notes automation
.PHONY: release-notes-draft
release-notes-draft:
	$(PYTHON) scripts/release_notes.py draft

.PHONY: release-cut
# Usage: make release-cut VERSION=0.3.1 LOGICAL=5 STORAGE=9
release-cut:
	$(PYTHON) scripts/release_notes.py cut --version $(VERSION) --schema-logical $(LOGICAL) --schema-storage $(STORAGE)

.PHONY: ui-ready
ui-ready:
	$(PYTHON) scripts/verify_ui_readiness.py

# Cache TTL self-checks (negative + positive)
.PHONY: cache-neg-ttl
cache-neg-ttl:
	PYTHONPATH=. $(PYTHON) scripts/cache_negative_ttl_selfcheck.py --json

.PHONY: cache-pos-ttl
cache-pos-ttl:
	PYTHONPATH=. $(PYTHON) scripts/cache_positive_ttl_selfcheck.py

.PHONY: cache-ttl-check
cache-ttl-check: cache-neg-ttl cache-pos-ttl

# Cache health SLO gate
.PHONY: cache-health-gate
cache-health-gate:
	@INPUT=$${INPUT:-logs/maintenance/cache_health.jsonl}; \
	MAX=$${MAX_CACHED_TTFB_MS:-300}; \
	IMPROVE=$${MIN_HIT_IMPROVEMENT:-0.15}; \
	MIN_EPS=$${MIN_ENDPOINTS:-3}; \
	WINDOW=$${WINDOW_MINUTES:-1440}; \
	PYTHONPATH=. $(PYTHON) scripts/cache_health_gate.py --input $$INPUT --max-cached-ttfb-ms $$MAX --min-hit-improvement $$IMPROVE --min-endpoints $$MIN_EPS --window-minutes $$WINDOW

.PHONY: cache-health-trend
cache-health-trend:
	@echo "Generating cache health trend summary..."
	@mkdir -p logs/maintenance
	PYTHONPATH=. $(PYTHON) scripts/cache_health_trend.py --input logs/maintenance/cache_health.jsonl --output logs/maintenance/cache_health_summary.md --window-minutes $${WINDOW_MINUTES:-1440}
	@echo "Summary written to logs/maintenance/cache_health_summary.md"

.PHONY: lint
lint:
	# Prefer venv ruff if available to avoid PATH/environment issues; fall back gracefully
	@set -eu; \
	if [ -x ./.venv/bin/ruff ]; then \
		ruff_cmd=./.venv/bin/ruff; \
	elif command -v ruff >/dev/null 2>&1; then \
		ruff_cmd=$$(command -v ruff); \
	else \
		ruff_cmd="$(PYTHON) -m ruff"; \
	fi; \
	echo "Using ruff: $$ruff_cmd"; \
	if [ "$$ruff_cmd" = "$(PYTHON) -m ruff" ]; then \
		$(PYTHON) -m ruff check --config pyproject.toml --fix api agents/interface/chainlit agents/core/monitoring/visualization || true; \
	else \
		$$ruff_cmd check --config pyproject.toml --fix api agents/interface/chainlit agents/core/monitoring/visualization || true; \
	fi
	@echo "(base lint complete)"
	@python_cmd=$${PYTHON_CMD:-$(PYTHON)}; \
	if [ -x ./.venv/bin/python ]; then \
		python_cmd=./.venv/bin/python; \
	fi; \
	echo "Verifying lizard module availability (using $$python_cmd)..."; \
	if ! $$python_cmd -c "import importlib; importlib.import_module('lizard')" >/dev/null 2>&1; then \
		echo "Lizard not installed. Install with 'pip install lizard==1.17.31'"; \
		exit 1; \
	fi; \
	echo "Running lizard complexity check (CCN<=15, length<=80)..."; \
	$$python_cmd -m lizard -C 15 -L 80 agents api scripts

# Maintenance automation orchestrator
.PHONY: maint-once
maint-once:
	@echo "Running maintenance orchestrator once (resource_sync + audit + qa_quick)"
	PYTHONPATH=. $(PYTHON) scripts/maintenance_orchestrator.py --once --jobs resource_sync audit qa_quick cache_health promote_audit_todos

.PHONY: maint-schedule
maint-schedule:
	@echo "Starting maintenance scheduler (background)"
	PYTHONPATH=. $(PYTHON) scripts/maintenance_orchestrator.py --schedule

.PHONY: smoke-langgraph
smoke-langgraph:
	@echo "Running LangGraph smoke test"
	PYTHONPATH=. $(PYTHON) scripts/smoke_langgraph.py

# On-demand DB vacuum trigger (the scheduler will pick it up within ~1 minute)
.PHONY: db-vacuum-now
db-vacuum-now:
	@mkdir -p logs/maintenance/triggers
	@echo "$(DB)" > logs/maintenance/triggers/db_vacuum_$$RANDOM.trigger
	@echo "Requested DB vacuum (path: '$(DB)' if provided)."

.PHONY: lint-extra
lint-extra: lint check-doc-anchors
	@echo "Checking deprecated adapter imports"
	$(PYTHON) -m .lint.deprecated_imports
# Documentation anchor drift check
.PHONY: check-doc-anchors
check-doc-anchors:
	@echo "Checking legacy orchestrator metrics anchor stubs..."; \
	PYTHONPATH=. $(PYTHON) scripts/check_doc_anchors.py --write-report .repo_studios/anchor_report.json || (echo "Anchor drift detected" && exit 1)
	@echo "Anchor drift check complete (report at .repo_studios/anchor_report.json)"

# Global markdown H1/H2 slug baseline ratchet (fail on regressions, log improvements)
.PHONY: anchor-baseline-check
anchor-baseline-check:
	@echo "Running anchor baseline ratchet check..."; \
	PYTHONPATH=. $(PYTHON) scripts/check_anchor_baseline.py || (echo "Anchor baseline regression detected" && exit 1)
	@echo "Anchor baseline check complete"

# Generate timestamped anchor health artifacts + run uniqueness test (non-fatal unless FAIL_ON_DUPES=1)
.PHONY: anchor-health
anchor-health:
	@echo "[anchor-health] Generating anchor health report..."; \
	PYTHONPATH=. $(PYTHON) .repo_studios/anchor_health_report.py || (echo "Anchor health script error" && exit 1); \
	if [ "$$RUN_ANCHOR_TEST" = "1" ]; then \
	  echo "[anchor-health] Running pytest anchor uniqueness test"; \
	  $(PYTHON) -m pytest -q tests/docs/test_global_anchors.py || { \
	    if [ "$$FAIL_ON_DUPES" = "1" ]; then \
	      echo "[anchor-health] Anchor test failed (FAIL_ON_DUPES=1)"; exit 1; \
	    else \
	      echo "[anchor-health] Anchor test failed (non-fatal)"; \
	    fi; \
	  }; \
	fi; \
	echo "[anchor-health] Latest artifacts: .repo_studios/anchor_health/anchor_report_latest.json";

# Codacy diff analysis (changed files vs base branch; set BASE_BRANCH and ANALYZE=1 to run per-file Codacy CLI)
.PHONY: codacy-diff
codacy-diff:
	@BASE=$${BASE_BRANCH:-main-clean}; echo "Computing diff vs $$BASE"; \
	PYTHONPATH=. $(PYTHON) scripts/codacy_diff.py --base $$BASE $${ANALYZE:+--analyze} || (echo "Codacy diff script failed" && exit 1)

# ---------------------------------------------------------------------------
# Systemd Inventory & Classification (Step 6 Phase 1 support)
# Usage:
#   make systemd-inventory            # regenerate inventory_report.json, dot, gap report
#   make systemd-inventory-check      # regenerate + fail if unknown classifications present
#   make systemd-inventory-svg        # regenerate + produce systemd_graph.svg (requires dot)
#
# NOTE: Fail-on-unknown becomes enforced after Phase 3 begins (aggregate target work).
# ---------------------------------------------------------------------------
.PHONY: systemd-inventory systemd-inventory-check systemd-inventory-svg
systemd-inventory:
	@echo "[systemd] Generating inventory artifacts"; \
	$(PYTHON) scripts/systemd_inventory.py --dir systemd --out-dir . || exit 1; \
	ls -1 inventory_report.json systemd_graph.dot systemd_gap_report.md 2>/dev/null | sed 's/^/[systemd] artifact: /'

systemd-inventory-check: systemd-inventory
	@echo "[systemd] Checking for unknown classifications"; \
	$(PYTHON) scripts/systemd_inventory.py --dir systemd --out-dir . --fail-on-unknown || (echo "Unknown unit classification detected" && exit 1)

systemd-inventory-svg: systemd-inventory
	@command -v dot >/dev/null 2>&1 || { echo "Graphviz 'dot' not installed"; exit 1; }; \
	dot -Tsvg systemd_graph.dot -o systemd_graph.svg; \
	echo "[systemd] Wrote systemd_graph.svg"

.PHONY: lint-ui
lint-ui:
	ruff check --fix agents/interface/chainlit --exclude agents/interface/chainlit/tests || true

.PHONY: typecheck
typecheck:
	# Use pyproject.toml config (files=...) to scope type checking to the intended modules
	mypy

# Focused type gate (explicit name for CI/docs); identical scope to [tool.mypy].files
.PHONY: typecheck-focused
typecheck-focused:
	@MYPY=$$(
		if [ -x ./.venv/bin/mypy ]; then echo ./.venv/bin/mypy; \
		elif command -v mypy >/dev/null 2>&1; then command -v mypy; \
		else echo "$(PYTHON) -m mypy"; fi
	); \
	 echo "Using mypy: $$MYPY"; \
	 $$MYPY

# Staged typing for model modules (non-blocking; run manually)
.PHONY: typecheck-models
typecheck-models:
	@if [ -x ./.venv/bin/mypy ]; then \
		MYPY=./.venv/bin/mypy; \
	elif command -v mypy >/dev/null 2>&1; then \
		MYPY=$$(command -v mypy); \
	else \
		MYPY="$(PYTHON) -m mypy"; \
	fi; \
	echo "Using mypy: $$MYPY"; \
	$$MYPY agents/core/model_catalog.py scripts/models_cli.py agents/core/model_registry.py || true

.PHONY: typecheck-report
typecheck-report: ## Run mypy via reporter and emit timestamped artifacts
	@TS=$${TS:-$$(date +"%Y-%m-%d_%H%M")}; \
	 echo "Running typecheck report (TS=$$TS)"; \
	 $(PYTHON) .repo_studios/typecheck_report.py --repo-root . --output-base .repo_studios/typecheck --timestamp $$TS || true; \
	 echo "Typecheck artifacts: .repo_studios/typecheck/$$TS/{raw.txt,report.json,report.md}"

.PHONY: docs-anchors
docs-anchors: ## Run markdown anchor/link checker (README + key agent docs)
	@echo "[docs] Checking markdown anchors & links"; \
	PYTHONPATH=. $(PYTHON) scripts/check_markdown_anchors.py --root . \
	  --glob README.md \
	  --glob docs/agents/config_quickstart.md \
	  --glob docs/agents/step5_agent_config_system.md || (echo "[docs] Anchor check FAILED" && exit 1)
	@echo "[docs] Anchor check passed"

.PHONY: qa
qa: lint typecheck test docs-anchors
	@echo "QA complete"

.PHONY: lint-ui-tests
lint-ui-tests:
	# Incremental test linting: now enforce F + E4 (imports/whitespace). E5 (line length) deferred.
	ruff check --select F,E4 agents/interface/chainlit/tests || true

.PHONY: install-hooks
install-hooks:
	@bash scripts/install_hooks.sh
	@echo "Git hooks installed"

.PHONY: ui
ui: lint-ui lint-ui-tests
	# Run only interface tests for faster feedback
	@if command -v coverage >/dev/null 2>&1; then \
		coverage run -m pytest -q agents/interface/chainlit/tests && \
		coverage report --fail-under=82 --omit='*/site-packages/*,agents/system/*' --skip-covered && \
		coverage json -o coverage-ui.json >/dev/null 2>&1 || true; \
		coverage xml -o coverage-ui.xml || true; \
	else \
		$(PYTHON) -m pytest -q agents/interface/chainlit/tests; \
	fi
	@# Non-enforcing diff coverage (base origin/main) prints summary
	@ if [ -f coverage-ui.json ]; then \
	  python scripts/diff_coverage.py --coverage coverage-ui.json --base-ref origin/main || true; \
	fi
	@echo "UI quality gate complete"

# Batch cleanup helpers (Ruff/Mypy/Pytest/Markdown)
.PHONY: batch-clean
batch-clean:
	@echo "Running batch cleanup on core dirs (agents, api, scripts)"
	./.venv/bin/python ./.repo_studios/batch_clean.py -t agents -t api -t scripts

# Monkey patch scan (writes timestamped reports under .repo_studios/monkey_patch)
.PHONY: scan-monkey-patches
scan-monkey-patches:
	@echo "Scanning for monkey patches..."
	$(PYTHON) ./.repo_studios/scan_monkey_patches.py --repo-root . --with-git --verbose --strict
	@echo "Computing monkey patch trends..."
	$(PYTHON) ./.repo_studios/compare_monkey_patch_trends.py || true

.PHONY: classify-monkey-patches
classify-monkey-patches: ## Classify latest scan by risk and write RISK_SUMMARY
	@echo "Classifying monkey patches by risk..."
	$(PYTHON) scripts/monkey_patch_classify.py || true

.PHONY: monkey-ratchet
monkey-ratchet: ## Enforce non-increasing monkey-patch count (initialize baseline if missing)
	@echo "Running monkey-patch CI ratchet..."
	$(PYTHON) scripts/ci_monkey_patch_ratchet.py

# Pytest log runner (captures full logs and summaries under .repo_studios/pytest_logs)
.PHONY: pytest-logs
pytest-logs:
	@echo "Running pytest with log capture..."
	$(PYTHON) ./.repo_studios/pytest_log_runner.py --

# UI control metrics test (Py3.13 EBADF override)
.PHONY: ui-control-metrics-override
ui-control-metrics-override: ## Run UI control metrics test with EBADF override (Py3.13)
	@echo "[ui] Running UI control metrics test with UI_CONTROL_METRICS_EBADF_STRICT=1"
	UI_CONTROL_METRICS_EBADF_STRICT=1 $(PYTHON) -m pytest -q tests/api/ui/test_ui_control_metrics_and_status.py -q

# One-shot repo insight: cleanup → tests with logs → monkey-patch scan
.PHONY: repo-insight
repo-insight: batch-clean pytest-logs scan-monkey-patches
	@echo "Repo insight complete (cleanup, test logs, monkey patch reports)."

.PHONY: batch-clean-md
batch-clean-md:
	@echo "Running markdown-only cleanup across repo"
	BATCH_CLEAN_ONLY=markdown ./.venv/bin/python ./.repo_studios/batch_clean.py -t .

# Centralized coverage runs for CI
.PHONY: cover-full
cover-full:
	# Full suite with coverage; artifact-only (no strict gate due to legacy modules)
	@if command -v coverage >/dev/null 2>&1; then \
		coverage erase; \
		coverage run -m pytest -q || true; \
		coverage report --omit='*/site-packages/*' --skip-covered || true; \
		coverage xml -o coverage-hybrid-1.xml || true; \
		coverage json -o coverage-core.json || true; \
	else \
		$(PYTHON) -m pytest -q; \
	fi

.PHONY: coverage-ci
coverage-ci:
	@echo "Running fast core coverage gate (>=90%) and generating artifacts..."
	@if command -v coverage >/dev/null 2>&1; then \
		coverage erase; \
		coverage run -m pytest -q \
			tests/api/test_diagnostic_agent_metrics.py \
			tests/api/test_diagnostic_metrics_exposure.py \
			agents/core/autonomy/tests/test_policy_loop.py \
			tests/agents/core/test_events_filter.py \
			tests/agents/core/test_events_filter_additional.py \
			tests/agents/core/test_subscriber.py \
			tests/agents/core/test_context.py \
			tests/agents/core/test_context_events_bridge.py \
			|| true; \
		coverage report --fail-under=90 --include='api/server.py,agents/core/events.py,agents/core/subscriber.py' --skip-covered; \
		coverage xml -o coverage-core.xml --include='api/server.py,agents/core/events.py,agents/core/subscriber.py' || true; \
		coverage json -o coverage-core.json --pretty-print || true; \
		$(MAKE) ui; \
		# Run Node-RED readiness as part of coverage-ci (non-fatal)
		$(MAKE) nodered-ready || true; \
		$(MAKE) cover-full; \
	else \
		$(PYTHON) -m pytest -q; \
	fi

.PHONY: contract-artifacts
contract-artifacts: ## Generate local contract artifacts (pytest + static scan)
	@mkdir -p artifacts
	$(PYTHON) -m pytest -q -m "contract and not heavy" | tee artifacts/contract_pytest_output.txt || true
	$(PYTHON) scripts/static_scan_voice_subprocess.py | tee artifacts/static_scan_voice.txt || true
	@# Generate fault artifacts (best-effort) and copy run folder into artifacts/fault
	@echo "Generating fault artifacts (best-effort)";
	@$(PYTHON) .repo_studios/generate_fault_artifacts.py || true;
	@mkdir -p artifacts/fault; \
	OUTDIR=$${FAULT_OUTDIR:-$$(ls -dt .repo_studios/faulthandler/*/ 2>/dev/null | head -n1 | sed 's:/*$::')}; \
	if [ -n "$$OUTDIR" ] && [ -d "$$OUTDIR" ]; then \
	  echo "Copying $$OUTDIR → artifacts/fault"; \
	  cp -r "$$OUTDIR" artifacts/fault/ || true; \
	else \
	  echo "No FAULT_OUTDIR detected; skipping copy"; \
	fi
	@echo '# Contract Suite Status'            >  artifacts/contract_suite_status.md
	@echo ''                                  >> artifacts/contract_suite_status.md
	@echo '| Check | Status |'                >> artifacts/contract_suite_status.md
	@echo '|------|--------|'                 >> artifacts/contract_suite_status.md
	@echo '| Contract tests | local |'        >> artifacts/contract_suite_status.md
	@echo '| Static scan (voice) | see static_scan_voice.txt |' >> artifacts/contract_suite_status.md
	@echo "Artifacts written to ./artifacts"

.PHONY: contract-orch-ui
contract-orch-ui: ## Run orchestrator UI contract suite locally and emit a status line + artifacts
	@mkdir -p artifacts
	@STATUS=PASS; \
	 $(PYTHON) -m pytest -q -m "contract and not heavy" | tee artifacts/contract_pytest_output.txt || STATUS=FAIL; \
	 $(PYTHON) scripts/static_scan_voice_subprocess.py | tee artifacts/static_scan_voice.txt || true; \
	 echo "Generating fault artifacts (best-effort)"; \
	 $(PYTHON) .repo_studios/generate_fault_artifacts.py || true; \
	 mkdir -p artifacts/fault; \
	 OUTDIR=$${FAULT_OUTDIR:-$$(ls -dt .repo_studios/faulthandler/*/ 2>/dev/null | head -n1 | sed 's:/*$::')}; \
	 if [ -n "$$OUTDIR" ] && [ -d "$$OUTDIR" ]; then \
	   echo "Copying $$OUTDIR → artifacts/fault"; \
	   cp -r "$$OUTDIR" artifacts/fault/ || true; \
	 else \
	   echo "No FAULT_OUTDIR detected; skipping copy"; \
	 fi; \
	 echo '# Contract Suite Status'            >  artifacts/contract_suite_status.md; \
	 echo ''                                  >> artifacts/contract_suite_status.md; \
	 echo "Orchestrator Integration & UI (contract) — $$STATUS" >> artifacts/contract_suite_status.md; \
	 echo "Phase 7 Orchestrator & UI — $$STATUS" >> artifacts/contract_suite_status.md; \
	 if command -v git >/dev/null 2>&1; then echo "Commit: $$(git rev-parse --short HEAD)" >> artifacts/contract_suite_status.md; fi; \
	 echo ''                                  >> artifacts/contract_suite_status.md; \
	 echo '| Check | Status |'                >> artifacts/contract_suite_status.md; \
	 echo '|------|--------|'                 >> artifacts/contract_suite_status.md; \
	 echo "| Contract tests | $$STATUS |"    >> artifacts/contract_suite_status.md; \
	 echo '| Static scan (voice) | see static_scan_voice.txt |' >> artifacts/contract_suite_status.md; \
	 echo "Artifacts written to ./artifacts";

.PHONY: diff-coverage
diff-coverage:
	@test -f coverage-ui.json || (echo "Run 'make ui' (with coverage) first" && exit 1)
	python scripts/diff_coverage.py --coverage coverage-ui.json --base-ref origin/main --threshold 0.9 $(ARGS)

.PHONY: ui-cover
ui-cover: lint-ui
	coverage run -m pytest -q agents/interface/chainlit/tests
	coverage html -d htmlcov-ui || true
	coverage report --omit='*/site-packages/*'
	@echo "UI coverage report generated (htmlcov-ui)"

##
## Memory RAG convenience
##   memory-refresh   Embed training docs and regenerate indexes (writes tmp_embed_monitoring.log)
##   memory-health    Print memory entry count and last refresh timestamp
.PHONY: memory-summary
memory-summary: ## Show active goals, Doing/Next, and last 3 decisions (hardened contract)
	@bash scripts/memory_summary.sh
	@# Sample outputs (for reference only):
	@# 1) Clean
	@# Active Goals:
	@# * Item A
	@# * Item B
	@# Progress:
	@# Doing:
	@# * Work 1
	@# Next:
	@# * Work 2
	@# Recent decisions:
	@# | 2025-08-20 | Enable X | accepted | rationale | link |
	@# | 2025-08-18 | Migrate Y | proposed | rationale | link |
	@# | 2025-08-17 | Retire Z | superseded | rationale | link |
	@#
	@# 2) Header mismatch (fuzzy match + WARN)
	@# WARN: fuzzy header match for Goals in memory-bank/activeContext.md (expected '## Current Goals')
	@# Active Goals:
	@# (none)
	@# Progress:
	@# Doing:
	@# (none)
	@# Next:
	@# (none)
	@# Recent decisions:
	@# (none)
	@#
	@# 3) Truncation / overflow
	@# Active Goals:
	@# * g1
	@# * g2
	@# ... (+8 more)
	@# Progress:
	@# Doing:
	@# * d1
	@# ... (+9 more)
	@# Next:
	@# * n1
	@# ... (+9 more)
	@# Recent decisions:
	@# | 2025-08-29 | Decide A | accepted | why | ref |
	@# | 2025-08-28 | Decide B | proposed | why | ref |
	@# | 2025-08-27 | Decide C | superseded | why | ref |
	@# ... (+4 more)
.PHONY: memory-validate-files
memory-validate-files: ## Validate presence of memory files
	@bash scripts/memory_validate/files_and_headers.sh | sed 's/^/  /'
.PHONY: memory-validate-headers
memory-validate-headers: ## Validate required headers in memory-bank files
	@bash scripts/memory_validate/files_and_headers.sh | sed 's/^/  /'
.PHONY: memory-validate-content
memory-validate-content: ## Validate content posture (bullets or (none))
	@bash scripts/memory_validate/content_posture.sh | sed 's/^/  /'
.PHONY: memory-validate-decisions
memory-validate-decisions: ## Validate decisionLog rows (date/status/refs)
	@bash scripts/memory_validate/decisions_schema.sh | sed 's/^/  /'
.PHONY: memory-validate-style
memory-validate-style: ## Validate style (tabs/line-endings/trailing WS)
	@bash scripts/memory_validate/style_checks.sh | sed 's/^/  /'
.PHONY: memory-validate-coherence
memory-validate-coherence: ## Validate duplicates and soft caps in progress
	@bash scripts/memory_validate/coherence_checks.sh | sed 's/^/  /'
.PHONY: memory-validate-summary
memory-validate-summary: ## Dry-check that memory-summary can extract sections
	@bash scripts/memory_validate/summary_drycheck.sh | sed 's/^/  /'
.PHONY: memory-validate-all
memory-validate-all: ## Run all memory validators and print a PASS/FAIL status line (style/coherence=WARN)
	@FAIL=0; \
	 ERR=0; WARN=0; TOTAL=3; \
	 echo "[1/7] files+headers"; bash scripts/memory_validate/files_and_headers.sh; rc=$$?; if [ $$rc -ne 0 ]; then echo "[FATAL] files+headers failed ($$rc)"; FAIL=1; ERR=$$((ERR+1)); fi; \
	 echo "[2/7] content"; bash scripts/memory_validate/content_posture.sh; rc=$$?; if [ $$rc -ne 0 ]; then echo "[FATAL] content failed ($$rc)"; FAIL=1; ERR=$$((ERR+1)); fi; \
	 echo "[3/7] decisions"; bash scripts/memory_validate/decisions_schema.sh; rc=$$?; if [ $$rc -ne 0 ]; then echo "[FATAL] decisions failed ($$rc)"; FAIL=1; ERR=$$((ERR+1)); fi; \
	 echo "[4/7] style"; bash scripts/memory_validate/style_checks.sh; rc=$$?; \
	   if [ $$rc -ne 0 ]; then \
	     if [ "$${STRICT:-0}" = "1" ]; then \
	       echo "[FATAL] style checks failed under STRICT=1 ($$rc)"; FAIL=1; ERR=$$((ERR+1)); \
	     else \
	       echo "[WARN] style checks returned $$rc (non-fatal)"; WARN=$$((WARN+1)); \
	     fi; \
	   fi; \
	 echo "[5/7] coherence"; bash scripts/memory_validate/coherence_checks.sh; rc=$$?; if [ $$rc -ne 0 ]; then echo "[WARN] coherence checks returned $$rc (non-fatal)"; WARN=$$((WARN+1)); fi; \
	 echo "[6/7] summary"; bash scripts/memory_validate/summary_drycheck.sh; rc=$$?; if [ $$rc -ne 0 ]; then echo "[FATAL] summary drycheck failed ($$rc)"; FAIL=1; ERR=$$((ERR+1)); fi; \
	 echo "[7/7] memory-summary (preview)"; $(MAKE) --no-print-directory memory-summary >/dev/null 2>&1 || true; \
	 if [ $$FAIL -eq 0 ]; then STATUS=PASS; else STATUS=FAIL; fi; \
	echo "VALIDATION_STATUS: $$STATUS"; \
	echo "VALIDATION_JSON: {\"status\":\"$$STATUS\",\"files\":$$TOTAL,\"errors\":$$ERR,\"warns\":$$WARN}"; \
	if [ $$FAIL -ne 0 ]; then exit 1; fi
.PHONY: memory-refresh
memory-refresh:
		@echo "Embedding training docs (see tmp_embed_monitoring.log for details)"
		./.venv/bin/python scripts/embed_training_docs.py > tmp_embed_monitoring.log 2>&1 || true

.PHONY: memory-health
memory-health:
		@bash scripts/memory_health/staleness_check.sh || true
		@echo "Entries count:"
		@if [ -f mrp/vector_db/entries.jsonl ]; then \
			grep -c "\"path\":\|\"source_path\":" mrp/vector_db/entries.jsonl || true; \
		else \
			echo 0; \
		fi
		@echo "Last refresh:"
		@if [ -f mrp/vector_db/index.json ] && command -v jq >/dev/null 2>&1; then \
			jq -r '.last_refresh // "unknown"' mrp/vector_db/index.json 2>/dev/null || echo unknown; \
		elif [ -f mrp/vector_db/.last_refresh.stamp ]; then \
			date -u -d "@$$(( $$(stat -c %Y mrp/vector_db/.last_refresh.stamp 2>/dev/null || echo 0) ))" +%Y-%m-%dT%H:%M:%SZ || echo unknown; \
		else \
			echo unknown; \
		fi

.PHONY: memory-archive
memory-archive: ## Preview archive rotation (echo-only; no file changes)
	@echo "[archive] Previewing rotation per ARCHIVE_POLICY.md (no writes)";
	@set -e; \
	DATE=$$(date +%F); YEAR=$$(date +%Y); MONTH=$$(date +%m); \
	MONTH_NUM=$${MONTH#0}; if [ -z "$$MONTH_NUM" ]; then MONTH_NUM=0; fi; \
	Q=$$(( ( (MONTH_NUM - 1) / 3 ) + 1 )); QUARTER=Q$$Q; \
	PROG_SRC=memory-bank/progress.md; \
	DEC_SRC=memory-bank/decisionLog.md; \
	CTX_SRC=memory-bank/activeContext.md; \
	PROG_DST_DIR=memory-bank/archive/progress/$$YEAR-$$MONTH; \
	DEC_DST_DIR=memory-bank/archive/decisions/$$YEAR-$$QUARTER; \
	CTX_DST_DIR=memory-bank/archive/activeContext/$$YEAR-$$MONTH; \
	PROG_DST_FILE=$$PROG_DST_DIR/progress_DONE_$$YEAR-$$MONTH.md; \
	DEC_DST_FILE=$$DEC_DST_DIR/decisions_$$YEAR-$$QUARTER.md; \
	CTX_DST_FILE=$$CTX_DST_DIR/goals_$$YEAR-$$MONTH.md; \
	echo "[progress] Would create dir $$PROG_DST_DIR"; \
	echo "[decisions] Would create dir $$DEC_DST_DIR"; \
	echo "[activeContext] Would create dir $$CTX_DST_DIR"; \
	if [ -f "$$PROG_SRC" ]; then \
	  DONE_COUNT=$$(awk '/^## Done/{flag=1;next}/^## Doing/{flag=0}flag && /^(\*|-) /{print}' "$$PROG_SRC" | wc -l | tr -d ' '); \
	  echo "[progress] Would move $$DONE_COUNT Done item(s) → $$PROG_DST_FILE"; \
	else echo "[progress] Skipped (missing $$PROG_SRC)"; fi; \
	if [ -f "$$DEC_SRC" ]; then \
	  DEC_COUNT=$$(awk '/^\|[[:space:]]*[0-9]{4}-[0-9]{2}-[0-9]{2}[[:space:]]*\|/{print}' "$$DEC_SRC" | wc -l | tr -d ' '); \
	  echo "[decisions] Would snapshot $$DEC_COUNT row(s) → $$DEC_DST_FILE"; \
	else echo "[decisions] Skipped (missing $$DEC_SRC)"; fi; \
	if [ -f "$$CTX_SRC" ]; then \
	  GOAL_COUNT=$$(awk '/^## Current Goals/{flag=1;next}/^## /{flag=0}flag && /^(\*|-) /{print}' "$$CTX_SRC" | wc -l | tr -d ' '); \
	  echo "[activeContext] Would snapshot $$GOAL_COUNT goal(s) → $$CTX_DST_FILE"; \
	else echo "[activeContext] Skipped (missing $$CTX_SRC)"; fi; \
	echo "[archive] Last rotated: $$DATE; preview only (no files written)";

.PHONY: memory-housekeeping
memory-housekeeping: ## Clean stale tmp artifacts under memory-bank (AGE_HOURS, STRICT env supported)
	@AGE=$${AGE_HOURS:-24}; STRICT=$${STRICT:-0}; echo "Running housekeeping (AGE_HOURS=$$AGE, STRICT=$$STRICT)"; \
	 bash scripts/memory_update/housekeeping.sh

##
## Memory admin endpoint helpers
##   memory-refresh-now   POST /internal/memory/refresh (env: HOST, API_KEY, DRY_RUN)
##   memory-refresh-cli   Call the same using a small Python helper
.PHONY: memory-refresh-now
memory-refresh-now:
	@HOST=$${HOST:-http://127.0.0.1:8010}; \
	 PATH_P=/internal/memory/refresh; \
	 API_KEY=$${API_KEY:-}; \
	 DRY=$${DRY_RUN:-0}; \
	 URL="$$HOST$$PATH_P"; \
	 if [ "$$DRY" = "1" ] || [ "$$DRY" = "true" ] || [ "$$DRY" = "yes" ] || [ "$$DRY" = "on" ]; then URL="$$URL?dry_run=1"; fi; \
	 HDR_API=; \
	 if [ -n "$$API_KEY" ]; then HDR_API="-H 'X-API-Key: $$API_KEY'"; fi; \
	 echo "POST $$URL"; \
	 eval "curl -fsS -X POST $$HDR_API $$URL" || (echo "Request failed" && exit 1)

.PHONY: memory-refresh-cli
memory-refresh-cli:
	@MEMORY_HOST=$${HOST:-http://127.0.0.1:8010} \
	 MEMORY_API_KEY=$${API_KEY:-} \
	 MEMORY_DRY_RUN=$${DRY_RUN:-0} \
	 $(PYTHON) scripts/memory_refresh_cli.py $${DRY_RUN:+--dry-run}

##
## Help (lists documented targets)
.PHONY: help
help:
		@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z0-9_-]+:.*##/ {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

# Optional helper: remove stale __pycache__ directories (can mitigate schema hash mismatches
# caused by import-order interacting with outdated bytecode). Non-destructive.
.PHONY: clean-pyc
clean-pyc: ## Remove Python bytecode caches under agents/orchestrator/config
	@echo "Removing __pycache__ under agents/orchestrator/config (if present)..."
	@find agents/orchestrator/config -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "Done (pyc caches cleared)."

# .bak cleanup helpers
.PHONY: bak-report bak-clean

bak-report: ## List legacy .bak files under api/ (dry run)
	@echo "[cleanup] Scanning for .bak files under api/ (dry-run)"; \
	$(PYTHON) scripts/cleanup_bak_files.py --dry-run --api-dir api || true

bak-clean: ## Delete legacy .bak files under api/ (destructive)
	@echo "[cleanup] Deleting .bak files under api/"; \
	$(PYTHON) scripts/cleanup_bak_files.py --api-dir api

# On-demand shared-state snapshot
.PHONY: state-snapshot-now
state-snapshot-now:
	@HOST=$${STATE_HOST:-http://localhost:8010}; \
	PATH_P=/internal/state/persist; \
	NS=$${STATE_PERSIST_NAMESPACES:-}; \
	API_KEY=$${INTERNAL_API_KEY:-}; \
	URL="$$HOST$$PATH_P"; \
	if [ -n "$$NS" ]; then URL="$$URL?namespaces=$$NS"; fi; \
	HDR_API=; \
	if [ -n "$$API_KEY" ]; then HDR_API="-H 'X-API-Key: $$API_KEY'"; fi; \
	echo "Triggering on-demand state persistence at $$URL"; \
	eval "curl -fsS -X POST $$HDR_API $$URL" || (echo "Request failed" && exit 1)

# Backfill perf JSON artifacts into metrics_raw
.PHONY: demo-backfill
demo-backfill:
	@DB_PATH=$${METRICS_DB_PATH:-data/metrics.db}; \
	FILES=$$(ls perf_history/*.json 2>/dev/null || true); \
	if [ -z "$$FILES" ]; then \
	  echo "No perf_history/*.json files found. Run 'make perf-ci-report' first"; exit 1; \
	fi; \
	DRY_FLAG=--dry-run; \
	if [ "$$DEMO_BACKFILL_WRITE" = "1" ]; then DRY_FLAG=; fi; \
	echo "Backfilling into $$DB_PATH (dry=$${DRY_FLAG:+yes}) from $$(echo $$FILES | wc -w) file(s)..."; \
	$(PYTHON) scripts/backfill_perf_json.py --db "$$DB_PATH" $$DRY_FLAG $$FILES || exit 1; \
	echo "Done. Set DEMO_BACKFILL_WRITE=1 to commit inserts. Override METRICS_DB_PATH to change target DB."

# Ticket sync convenience targets
.PHONY: tickets-sync tickets-sync-dry
tickets-sync:
	@PROVIDER=$${TICKETS_PROVIDER:-github}; \
	LABELS=$${TICKETS_LABELS:-maintenance,audit,auto}; \
	MAX=$${TICKETS_MAX:-50}; \
	PATTERN=$${TICKETS_PATTERN:-'(stampede|polling|websocket)'}; \
	if [ "$$PROVIDER" = "github" ]; then \
	  REPO=$${TICKETS_GITHUB_REPO:?Set TICKETS_GITHUB_REPO=org/repo}; \
	  echo "Syncing audit tickets to GitHub repo '$$REPO' (dry-run=0)"; \
	  PYTHONPATH=. $(PYTHON) scripts/audit_ticket_sync.py --provider github --repo "$$REPO" --labels "$$LABELS" --max "$$MAX" --pattern "$$PATTERN"; \
	elif [ "$$PROVIDER" = "jira" ]; then \
	  BASE=$${TICKETS_JIRA_BASE_URL:?Set TICKETS_JIRA_BASE_URL=https://your.atlassian.net}; \
	  PROJ=$${TICKETS_JIRA_PROJECT_KEY:?Set TICKETS_JIRA_PROJECT_KEY=ABC}; \
	  echo "Syncing audit tickets to Jira project '$$PROJ' at '$$BASE' (dry-run=0)"; \
	  PYTHONPATH=. $(PYTHON) scripts/audit_ticket_sync.py --provider jira --base-url "$$BASE" --project-key "$$PROJ" --labels "$$LABELS" --max "$$MAX" --pattern "$$PATTERN"; \
	else \
	  echo "Unknown provider '$$PROVIDER'. Set TICKETS_PROVIDER=github|jira"; exit 1; \
	fi

tickets-sync-dry:
	@PROVIDER=$${TICKETS_PROVIDER:-github}; \
	LABELS=$${TICKETS_LABELS:-maintenance,audit,auto}; \
	MAX=$${TICKETS_MAX:-50}; \
	PATTERN=$${TICKETS_PATTERN:-'(stampede|polling|websocket)'}; \
	if [ "$$PROVIDER" = "github" ]; then \
	  REPO=$${TICKETS_GITHUB_REPO:?Set TICKETS_GITHUB_REPO=org/repo}; \
	  echo "Syncing audit tickets to GitHub repo '$$REPO' (dry-run=1)"; \
	  PYTHONPATH=. $(PYTHON) scripts/audit_ticket_sync.py --provider github --repo "$$REPO" --labels "$$LABELS" --max "$$MAX" --pattern "$$PATTERN" --dry-run; \
	elif [ "$$PROVIDER" = "jira" ]; then \
	  BASE=$${TICKETS_JIRA_BASE_URL:?Set TICKETS_JIRA_BASE_URL=https://your.atlassian.net}; \
	  PROJ=$${TICKETS_JIRA_PROJECT_KEY:?Set TICKETS_JIRA_PROJECT_KEY=ABC}; \
	  echo "Syncing audit tickets to Jira project '$$PROJ' at '$$BASE' (dry-run=1)"; \
	  PYTHONPATH=. $(PYTHON) scripts/audit_ticket_sync.py --provider jira --base-url "$$BASE" --project-key "$$PROJ" --labels "$$LABELS" --max "$$MAX" --pattern "$$PATTERN" --dry-run; \
	else \
	  echo "Unknown provider '$$PROVIDER'. Set TICKETS_PROVIDER=github|jira"; exit 1; \
	fi

# ------------------------------------------------------------
# WebSocket Streaming Smokes
# ------------------------------------------------------------
.PHONY: smoke-ws smoke-ws-all run-stream-server

# Quick happy-path WS smoke using in-repo test client; enables required flags
smoke-ws:
	@echo "[smoke] WS happy-path with STREAM_CHAT_ENABLE=1, CLIENT_STREAM_ENABLE=1"
	API_KEY= STREAM_CHAT_ENABLE=1 CLIENT_STREAM_ENABLE=1 pytest -q tests/api/test_ws_chat.py::test_ws_chat_stream_happy_path -q

# Full WS test file (auth, rate-limit parity, idle/session timeouts)
smoke-ws-all:
	@echo "[smoke] WS full suite with STREAM_CHAT_ENABLE=1, CLIENT_STREAM_ENABLE=1"
	API_KEY= STREAM_CHAT_ENABLE=1 CLIENT_STREAM_ENABLE=1 pytest -q tests/api/test_ws_chat.py -q

# Llama backend smoke using stubbed subprocess (no real llama binary needed)
.PHONY: smoke-ws-llama
smoke-ws-llama:
	@echo "[smoke] WS llama stub happy-path"
	STREAM_CHAT_ENABLE=1 pytest -q tests/api/test_ws_chat_llama_stub.py::test_ws_llama_stub_ack_delta_done -q

# Optionally run the adapter with WS enabled for manual testing
run-stream-server:
	@echo "[dev] Starting server with STREAM_CHAT_ENABLE=1 at http://0.0.0.0:8010"
	STREAM_CHAT_ENABLE=1 python -m uvicorn api.server:app --host 0.0.0.0 --port 8010

# ------------------------------------------------------------
# Lightweight Jarvis API (agents.core.jarvis_api)
# ------------------------------------------------------------
.PHONY: run-jarvis-api probe-jarvis-api

run-jarvis-api:
	@echo "[dev] Starting jarvis_api at http://127.0.0.1:8020 (log: tmp_jarvis_api.log)"
	STREAM_CHAT_ENABLE=1 ./.venv/bin/python -m uvicorn agents.core.jarvis_api:app --host 127.0.0.1 --port 8020 > tmp_jarvis_api.log 2>&1 & echo $$! > tmp_jarvis_api.pid; disown || true; sleep 1; tail -n 5 tmp_jarvis_api.log || true

probe-jarvis-api:
	@echo "[dev] Probing jarvis_api /health"
	PYTHONPATH=. ./.venv/bin/python scripts/ping_jarvis_api.py http://127.0.0.1:8020

# ------------------------------------------------------------
# Dev servers: backend (FastAPI) and frontend (Chainlit)
# ------------------------------------------------------------
.PHONY: back-end front-end start-jarvis stop-back-end restart-back-end

back-end: ## Start FastAPI backend (uvicorn) in background at 0.0.0.0:8010
	@HOST=$${BACKEND_HOST:-0.0.0.0}; \
	 PORT=$${BACKEND_PORT:-8010}; \
	 LOG=$${BACKEND_LOG:-tmp_backend.log}; \
	 PID=$${BACKEND_PID:-tmp_backend.pid}; \
	 echo "[dev] Starting backend at http://$$HOST:$$PORT (log: $$LOG)"; \
	 $(PYTHON) -m uvicorn api.server:app --host $$HOST --port $$PORT > "$$LOG" 2>&1 & echo $$! > "$$PID"; disown || true; \
	 sleep 1; tail -n 5 "$$LOG" || true

stop-back-end: ## Stop FastAPI backend using PID file or port scan
	@PID=$${BACKEND_PID:-tmp_backend.pid}; \
	 PORT=$${BACKEND_PORT:-8010}; \
	 if [ -f "$$PID" ]; then \
	   K=$$(cat "$$PID" 2>/dev/null || true); \

	   if [ -n "$$K" ]; then \
	     echo "[dev] Stopping backend via PID file (pid=$$K)"; \
	     kill $$K 2>/dev/null || true; sleep 1; \
	     if kill -0 $$K 2>/dev/null; then echo "[dev] Force killing $$K"; kill -9 $$K 2>/dev/null || true; fi; \
	   fi; \
	 fi; \
	 # Fallback: kill any process listening on PORT (parse ss output without parentheses)
	 PIDS=$$(ss -ltnp 2>/dev/null | awk -v p=":$$PORT" '$$4 ~ p {print}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u); \
	 for P in $$PIDS; do \
	   echo "[dev] Killing listener on :$$PORT (pid=$$P)"; kill $$P 2>/dev/null || true; sleep 1; \
	   if kill -0 $$P 2>/dev/null; then echo "[dev] Force killing $$P"; kill -9 $$P 2>/dev/null || true; fi; \
	 done; \
	 rm -f "$$PID" || true; \
	 ss -ltnp 2>/dev/null | awk -v p=":$$PORT" '$$4 ~ p {print $$0}' || true

restart-back-end: ## Restart backend (stop then start)
	$(MAKE) stop-back-end || true
	$(MAKE) back-end

front-end: ## Start Chainlit UI in background at 0.0.0.0:8000
	@HOST=$${FRONTEND_HOST:-0.0.0.0}; \
	 PORT=$${FRONTEND_PORT:-8000}; \
	 LOG=$${FRONTEND_LOG:-tmp_chainlit.log}; \
	 PID=$${FRONTEND_PID:-tmp_chainlit.pid}; \
	 echo "[dev] Starting Chainlit at http://$$HOST:$$PORT (log: $$LOG)"; \
	 PYTHONPATH=. chainlit run agents/interface/chainlit/main.py --host $$HOST --port $$PORT > "$$LOG" 2>&1 & echo $$! > "$$PID"; disown || true; \
	 sleep 1; tail -n 5 "$$LOG" || true

start-jarvis: back-end front-end ## Start backend and frontend (both in background)
	@echo "Jarvis started: backend (8010) and frontend (8000). Override ports via BACKEND_PORT/FRONTEND_PORT."

# ------------------------------------------------------------
# Agent scaffolding helper
# ------------------------------------------------------------
.PHONY: scaffold-agent
scaffold-agent: ## Generate a new agent from the template (NAME=my_agent [FORCE=1])
	@NAME=$${NAME:?Set NAME=my_agent}; \
	 FORCE=$${FORCE:-0}; \
	 echo "[scaffold] Generating agent '$$NAME' (force=$$FORCE)"; \
	 $(PYTHON) scripts/scaffold_agent.py --name "$$NAME" $$( [ "$$FORCE" = "1" ] && echo --force )

# ------------------------------------------------------------
# Agents convenience targets (list, run, test, CI, readiness)
# ------------------------------------------------------------
.PHONY: agents-list agent-run agent-test agents-ci agents-ready

agents-list: ## List known agents and their enable flags
	PYTHONPATH=. $(PYTHON) scripts/agents_list.py $(ARGS)

# Usage: make agent-run NAME=CacheInspectorAgent [DRY=1]
agent-run: ## Run a single agent in dry-run/report mode by default (NAME=<AgentName>)
	@NAME=$${NAME:?Set NAME=<AgentName>}; \
	 DRY=$${DRY:-1}; \
	 echo "[agents] Running $$NAME (dry=$$DRY)"; \
	 PYTHONPATH=. $(PYTHON) scripts/agent_run.py --name "$$NAME" $$( [ "$$DRY" = "1" ] && echo --dry-run )

# Usage: make agent-test NAME=CacheInspectorAgent
agent-test: ## Run targeted tests for a single agent (fast subset)
	@NAME=$${NAME:?Set NAME=<AgentName>}; \
	 echo "[agents] Testing $$NAME"; \
	 PYTHONPATH=. $(PYTHON) scripts/agent_test.py --name "$$NAME"

agents-ci: ## Run all enabled agents in report-only mode and emit artifacts under artifacts/agents
	PYTHONPATH=. $(PYTHON) scripts/agents_ci.py

agents-ready: ## Quick lint/type/test gate for agent codepaths (stub)
	PYTHONPATH=. $(PYTHON) scripts/agents_ready.py || true

# ------------------------------------------------------------
# repo instructions tools tests (hidden folder helpers)
# ------------------------------------------------------------
.PHONY: repo-tools-tests repo-tools-cover

repo-tools-tests: ## Run tests under .repo_studios/tests
	@echo "[repo] Running tests under .repo_studios/tests"
	$(PYTHON) -m pytest -q .repo_studios/tests

repo-tools-cover: ## Run .repo_studios tests with coverage and emit a focused report
	@echo "[repo] Running tests with coverage for .repo_studios/*.py"
	@if command -v coverage >/dev/null 2>&1; then \
		coverage erase >/dev/null 2>&1 || true; \
		coverage run -m pytest -q .repo_studios/tests || true; \
		coverage report --include='.repo_studios/*.py' --skip-covered || true; \
		coverage html -d htmlcov-repo || true; \
	else \
		$(PYTHON) -m pytest -q .repo_studios/tests; \
	fi

# ------------------------------------------------------------
# Node-RED readiness: lint + targeted tests
# ------------------------------------------------------------
.PHONY: nodered-ready
nodered-ready:
	@echo "[nodered] Linting and running targeted Node-RED tests"
	$(MAKE) lint-ui || true
	@mkdir -p artifacts
	@STATUS=PASS; \
	  OUT=artifacts/nodered_ready_pytest.txt; \
	  if command -v coverage >/dev/null 2>&1; then \
		coverage erase >/dev/null 2>&1 || true; \
		coverage run -m pytest -q \
			api/tests/test_nodered_router.py \
			api/tests/test_nodered_proxy.py \
			api/tests/test_nodered_proxy_timeouts.py \
			api/tests/test_nodered_proxy_headers_streaming.py \
			api/tests/test_nodered_flows_endpoint.py \
			api/tests/test_nodered_backup_rotation.py \
			api/tests/test_nodered_backup_retention_order.py \
			api/tests/test_nodered_git_snapshot.py \
			api/tests/test_nodered_mrp_and_metrics.py \
			| tee $$OUT || STATUS=FAIL; \
		coverage report --omit='*/site-packages/*' --skip-covered || true; \
	  else \
		$(PYTHON) -m pytest -q \
			api/tests/test_nodered_router.py \
			api/tests/test_nodered_proxy.py \
			api/tests/test_nodered_proxy_timeouts.py \
			api/tests/test_nodered_proxy_headers_streaming.py \
			api/tests/test_nodered_flows_endpoint.py \
			api/tests/test_nodered_backup_rotation.py \
			api/tests/test_nodered_backup_retention_order.py \
			api/tests/test_nodered_git_snapshot.py \
			api/tests/test_nodered_mrp_and_metrics.py \
			| tee $$OUT || STATUS=FAIL; \
	  fi; \
	  echo '# Node-RED Readiness — ' $$STATUS > artifacts/nodered_ready_status.md; \
	  echo '' >> artifacts/nodered_ready_status.md; \
	  echo "This gate is non-blocking and is invoked from 'make coverage-ci'." >> artifacts/nodered_ready_status.md; \
	  echo '' >> artifacts/nodered_ready_status.md; \
	  if command -v git >/dev/null 2>&1; then echo "Commit: $$(git rev-parse --short HEAD)" >> artifacts/nodered_ready_status.md; fi; \
	  echo '' >> artifacts/nodered_ready_status.md; \
	  echo '| Check | Status |' >> artifacts/nodered_ready_status.md; \
	  echo '|------|--------|' >> artifacts/nodered_ready_status.md; \
	  echo '| Node-RED targeted tests |' $$STATUS '|' >> artifacts/nodered_ready_status.md; \
	  echo '' >> artifacts/nodered_ready_status.md; \
	  echo "[nodered] status: $$STATUS (see artifacts/nodered_ready_status.md; logs in $$OUT)"; \
	  true
