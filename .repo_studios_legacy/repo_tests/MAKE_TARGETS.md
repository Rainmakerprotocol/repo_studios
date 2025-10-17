# Make Targets Reference — Jarvis2

Date: 2025-09-24
Status: Stable
Phase: Developer Operations

This document catalogs the most useful Make targets in this repo, grouped by area. Use
`make help` to list targets that include inline docs (## comments) and refer to the Makefile for
full details. Commands honor the active Python on PATH unless overridden with `PYTHON=/path`.

Note: Paths for artifacts are relative to the repo root.

## Health, Insight, and Trends

* health-suite — One-shot orchestrator. Writes:
  * .repo_studios/health_suite/health_suite_{ts}.md
  * .repo_studios/health_suite/logs/{ts}/*.log
* repo-insight — Cleanup → pytest logs → monkey-patch scan (strict) + trends.
* pytest-logs — Run pytest and capture logs/JUnit under .repo_studios/pytest_logs/.
* scan-monkey-patches — AST-first scan; outputs under .repo_studios/monkey_patch/{ts}/.
* classify-monkey-patches — Risk summary for latest scan.
* monkey-ratchet — CI ratchet to prevent increasing monkey-patch counts.
* anchor-health — Generate duplicate heading report (H1/H2).
  Artifacts under `.repo_studios/anchor_health/anchor_health-<ts>/`:
  `anchor_report.json`, `anchor_report.md`, `clusters.tsv` plus `anchor_report_latest.json`.
  Env:
  * `RUN_ANCHOR_TEST=1` — also run uniqueness pytest
  * `FAIL_ON_DUPES=1` — non-zero exit on disallowed duplicates or baseline regression
* dep-health — Dependency hygiene report → .repo_studios/dep_health/.
* import-graph — Import graph report → .repo_studios/import_graph/.
* test-health — Test log health report → .repo_studios/test_health/{ts}/.
* churn-complexity — Churn × complexity heatmap → .repo_studios/churn_complexity/.
* soft-ci-gates — Best-effort gates (deps/test warnings/monkey-patch); non-fatal.

## Lint, Types, Coverage

* lint — Ruff fix on key packages (api, agents/*); non-fatal on fix attempt.
* lint-extra — Adds deprecated adapter import checks.
* lint-ui — Ruff for Chainlit UI code; excludes UI tests.
* lint-ui-tests — Focused lint (F, E4) for UI tests only.
* typecheck — Mypy with config from pyproject.toml.
* typecheck-focused — Same as typecheck with explicit mypy detection.
* typecheck-report — Timestamped artifacts under .repo_studios/typecheck/{ts}/.
* qa — lint + typecheck + test.
* cover-full — Full pytest with coverage artifacts (xml/json) without strict gate.
* coverage-ci — Fast core coverage gate (>=90%) + UI gate + Node-RED readiness; writes artifacts.
* diff-coverage — Diff coverage report for UI (requires coverage-ui.json from `make ui`).

## UI Readiness and Benchmarks

* ui — Lint + run Chainlit interface tests with coverage; emits coverage-ui.{json,xml}.
* ui-pre-post-assert — CI assertion of pre/post UI perf labels.
* ui-latency-assert — Checks perf_history/ui_endpoints.json thresholds.
* bench-ui-snapshot, bench-ui-snapshot-pre — Snapshot endpoint benches (pre/post caching).
* bench-ui-catalog, bench-ui-catalog-pre — Catalog endpoint benches (pre/post caching).
* bench-ui-pre-post — Pre vs post compare for sidebar snapshot.
* bench-ui-{report,dashboard,plot} — Reporting helpers.
* ui-cover — Generate HTML coverage report for UI tests (htmlcov-ui).

## Cache Health and TTL

* cache-neg-ttl — Run negative TTL self-check (JSON output).
* cache-pos-ttl — Positive TTL self-check.
* cache-ttl-check — Runs both negative and positive self-checks.
* cache-health-gate — Enforce cache SLOs over a window (env: INPUT, MAX_CACHED_TTFB_MS, etc.).
* cache-health-trend — Trend summary at logs/maintenance/cache_health_summary.md.

## Performance

* perf — Quick load gen (rate/duration). No gates.
* perf-ci — Load gen with latency/drift gates (CI-friendly).
* perf-report — Generate perf_samples.csv and print path.
* perf-baseline — Write perf_baseline.json for later comparison.
* perf-compare — Compare vs baseline with p50/p90/p99.
* perf-baseline-update — Update baseline (intended for protected main branches).
* perf-ci-report — Write perf_summary.md, perf_trend.md, perf_last.json, and history.
* perf-graph — Render perf_last.json to perf_graph.png.

## Dev Servers and Smokes

* back-end — Start FastAPI (uvicorn) in background; logs to tmp_backend.log.
* stop-back-end — Stop by PID file or port; cleans tmp_backend.pid.
* restart-back-end — Stop then start.
* front-end — Start Chainlit UI in background; logs to tmp_chainlit.log.
* start-jarvis — Start both backend and frontend.
* smoke-ws — Quick WS happy-path test with STREAM_CHAT_ENABLE/CLIENT_STREAM_ENABLE.
* smoke-ws-all — Full WS test file (auth, rate-limit, timeouts).
* smoke-ws-llama — Llama backend stub WS smoke.
* run-stream-server — Start backend with streaming enabled (manual testing).

## Jarvis API (lightweight)

* run-jarvis-api — Start agents.core.jarvis_api on 127.0.0.1:8020 (bg); log at tmp_jarvis_api.log.
* probe-jarvis-api — Probe /health.

## Agents

* scaffold-agent — Generate a new agent from template (NAME, FORCE env).
* agents-list — List known agents and enable flags.
* agent-run — Run a single agent (dry-run=1 by default); accepts NAME.
* agent-test — Run targeted tests for one agent.
* agents-ci — Run all enabled agents (report-only) → artifacts/agents.
* agents-ready — Quick lint/type/test for agent codepaths (non-fatal).

## Node-RED

* nodered-ready — Lint UI and run Node-RED targeted tests; writes artifacts/nodered_ready_*.{md,txt}.

## Memory (RAG)

* memory-summary — Print current goals, Doing/Next, last 3 decisions (hardened contract).
* memory-validate-{files,headers,content,decisions,style,coherence,summary,all} — Validators.
* memory-refresh — Embed training docs; logs to tmp_embed_monitoring.log.
* memory-health — Prints entries count and last refresh (reads .stamp or index.json).
* memory-archive — Echo-only rotation preview (no writes).
* memory-housekeeping — Clean stale tmp artifacts (AGE_HOURS, STRICT).
* memory-refresh-now — POST /internal/memory/refresh (HOST, API_KEY, DRY_RUN).
* memory-refresh-cli — Same via Python helper (HOST, API_KEY, DRY_RUN).

## Intent Router and Maintenance

* intent-config-validate — Validate intent router config (env-driven or sample file).
* maint-once — Run maintenance orchestrator once (resource_sync, audit, qa_quick, cache health,
  promote_audit_todos).
* maint-schedule — Start maintenance scheduler in foreground.
* smoke-langgraph — LangGraph smoke test.

## Releases and Contracts

* release-notes-draft — Generate draft release notes.
* release-cut — Cut release (env: VERSION, LOGICAL, STORAGE).
* contract-artifacts — Contract pytest + static scan; writes artifacts/*.
* contract-orch-ui — Orchestrator/UI contract suite; writes artifacts/* with status line.

## Misc Operations

* help — List documented targets.
* bak-report — List legacy api/*.bak files (dry run).
* bak-clean — Delete legacy api/*.bak files (destructive).
* state-snapshot-now — POST /internal/state/persist (HOST, namespaces env).
* demo-backfill — Backfill perf JSON into metrics.db (dry-run by default).
* tickets-sync — Sync audit tickets to GitHub/Jira (provider/env driven).
* tickets-sync-dry — Dry-run variant.
* db-vacuum-now — Create trigger file for on-demand DB vacuum.

## Standards Tooling (Index, Gaps, Enforcement, Seeds)

* standards-index-build — Build consolidated standards index only.
* standards-index-test — Build then run schema/hash validation tests.
* standards-index — Convenience: build + tests (success banner on pass).
* standards-index-cli — Query index (ARGS="stats" default; list|search <q>|show <id>).
* standards-index-diff — Diff two index YAMLs (OLD, NEW env; FAIL kinds list).
* standards-index-gap — Gap detector; writes JSON to GAP_JSON (default .repo_studios/standards_gap_report.json).
* standards-enforce — Phase 1 enforcement stub (ENFORCE_JSON output; FAIL_ON=error threshold).
* standards-prompt-seed — Generate condensed high-severity prompt seed (SEED_FORMAT=text|yaml|json; SEED_OUT optional).

Notes:
* Diff fail kinds default: severity_changed,added,removed.
* Enforcement currently checks a minimal subset (dependency pinning, bare except, print logging, wildcard imports, multiple H1, empty headings, builtin patch attempts).
* Prompt seed includes error+critical (add warn with --include-warn).
* All tools rely on integrity_hash for quick drift detection.

## Tips

* Many targets write timestamped artifacts under `.repo_studios/<tool>/<ts>/`.
  Prefer running through Make to keep outputs organized and reproducible.
* Set PYTHON to a specific interpreter if needed (e.g., `make PYTHON=./.venv/bin/python ui`).
* Use environment flags described in `README.md` for feature toggles (caching, events, agents).
