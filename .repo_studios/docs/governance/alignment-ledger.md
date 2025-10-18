title: Repo Studios Alignment Ledger

audience:

- coding_agent
<!-- markdownlint-disable MD024 MD032 MD025 MD032 MD004 MD022 -->
- human_developer

owners:

- repo_studios_ai
- [repo_studios_team@rainmakerprotocol.dev](mailto:repo_studios_team@rainmakerprotocol.dev)

status: active
version: 1.0.0
updated: 2025-10-18
summary: >-
  Append-only ledger capturing documentation alignment batches and follow-up actions.
tags:
- governance
- alignment
legacy_source: .repo_studios_legacy/repo_docs/alignment_ledger.md
---

# Repo Studios Alignment Ledger

Append-only log of documentation review batches processed oldest to newest per `docs_inventory.csv`.

> Inventory source path confirmed at `/home/founder/jarvis2/.repo_studios/docs_inventory.csv`.

## 2025-10-01T17:40Z — Batch 1 (docs 1-25)

### Scope

* `.repo_prompts/prompt_whispering_v0.md`
* `.repo_session_alignment/ledger_setup_demo.md`
* `docs/voice_subsystem/README.md`
* `docs/ui/bench_ui_pre_commit.md`
* `docs/planning/pr_summary_template.md`
* `docs/voice/latency_slo.md`
* `docs/voice/README.md`
* `docs/voice/whisper/README.md`
* `docs/voice/resampler/README.md`
* `docs/voice/queueing_and_collapse.md`
* `docs/voice/feature_flags.md`
* `docs/memory/memory_repo_protocol.md`
* `docs/memory/memory-governance.md`
* `docs/memory/memory_refresh.md`
* `docs/memory/daily_ops.md`
* `docs/ownership/memory_data_access.md`
* `docs/ownership/memory_pipeline_failures.md`
* `docs/ownership/memory_refresh_access.md`
* `memory-bank/activeContext.md`
* `memory-bank/progress.md`
* `memory-bank/decisionLog.md`
* `docs/security_hardening.md`
* `docs/monitoring_notes.md`
* `memory-bank/productContext.md` *(no content change; verified availability)*
* `repo_rollout_targets.md`

### Alignment & Highlights

* Voice subsystem docs (latency SLO, queueing/collapse, resampler, Whisper prompt) give a coherent offline-first voice pipeline with traceable SLO and feature flag controls; matches Jarvis2 requirement for local execution.
* Memory governance set (MRP protocol, governance, daily ops, ownership matrices) reinforces Founder-Governed Protocol; confirms refresh tooling and access boundaries are documented end-to-end.
* Ledger template and memory-bank artifacts already model the alignment workflow we are adopting; decision log codifies continuity artifacts policy from 2025-09-19.
* Security hardening guidance aligns with air-gapped posture (kernel patch cadence, hardware attack surface mitigation) and dovetails with monitoring notes that emphasize voice metrics export readiness.
* repo rollout targets tie faulthandler artifacts back to CI gate expectations, providing measurable success criteria for diagnostics automation.

### Questions / Potential Gaps

* Voice docs reference aggregated metrics at `/metrics/voice`, but monitoring notes focus on generic KPI dashboards; need to confirm dashboards surface the new voice counters.
* Memory-bank `activeContext.md` still lists cache bypass/TTL stabilization work as the current goal—should be updated to reflect this documentation alignment cycle to avoid drift.
* `docs/ui/bench_ui_pre_commit.md` predates the latest Chainlit widget standards; check whether new UI hashing rules are incorporated elsewhere or if benchmarking guidance needs an appendix update.
* Security hardening checklist references 2025-06 kernel LTS; verify whether the September patches are applied and whether offline update procedure has an accompanying artifact.

### Next Actions

* Refresh memory-bank Active Context/Progress entries to reflect ledger-driven alignment effort and log resulting decisions once confirmed.
* Coordinate with monitoring owners to ensure voice metrics dashboards include the latency and collapse KPIs described in the voice SLO docs.
* Review UI benchmarking doc against current Chainlit standards and schedule an update if discrepancies remain after Batch 2.
* Validate faulthandler rollout evidence (blocklist/allowlist artifacts) before the mid-term milestone review.

## 2025-10-01T18:05Z — Batch 2 (docs/ entries 1-25)

### Scope (Batch 2)

* `docs/ci_fault_owner_signals.md`
* `docs/memory/daily_ops.md`
* `docs/ownership/memory_maintenance_calendar.md`
* `docs/ownership/memory_ownership.md`
* `docs/coverage_history/README.md`
* `docs/monitoring_notes.md`
* `docs/voice_static_scan_plan.md`
* `docs/voice/README.md`
* `docs/architecture/data_flows.md`
* `docs/architecture/jarvis2_components.md`
* `docs/architecture/system_overview.md`
* `docs/demo_ui_snapshot.md`
* `docs/operator_quickstart.md`
* `docs/memory/mrp_events.md`
* `docs/memory/observability.md`
* `docs/operator_acceptance_checklist.md`
* `docs/repo_health_angles.md`
* `docs/agents/interop_optimization.md`
* `docs/api/memory_endpoints.md`
* `docs/endpoint_ttl_registry.md`
* `docs/interface_testing_standards.md`
* `docs/memory/staleness_policy.md`
* `docs/methodology_upgrades_2025-08.md`
* `docs/ui_readiness_checklist.md`
* `docs/coverage_ui.md`

### Alignment & Highlights (Batch 2)

* Fault owner signals plus operator checklists define measurable paging.
  Outcome aligns with monitoring KPIs recorded in repo health angles.
* Memory runbooks (daily ops, observability, staleness policy) reinforce MRP logging.
  Content matches refresh windows recorded in the TTL registry.
* Architecture overviews mirror the hardware blueprint and local-first orchestration.
  They reference interop optimization boundaries and network isolation rules.
* Interface testing and UI readiness docs codify Chainlit gates and diff coverage baselines.
  Standards tie back to methodology upgrades and coverage history metrics.
* Voice static scan plan plus README confirm offline voice posture.
  They restate pending `/metrics/voice` validation first flagged in Batch 1.

### Questions / Potential Gaps (Batch 2)

* Operator quickstart references legacy pager IDs; confirm they match the live roster.
* Staleness policy still cites 24h refresh while TTL registry shows shorter cache expirations.
* Demo UI snapshot predates widget hashing changes; verify newer screenshots exist.
* Interop optimization doc wants benchmark agent involvement without a success metric.

### Next Actions (Batch 2)

* Align operator quickstart tables and fault owner signals with current escalation contacts.
* Schedule TTL registry and staleness policy reconciliation to pick a single refresh cadence.
* Capture fresh Chainlit screenshots once hashing rules settle and update demo snapshot.
* Define interop benchmark KPI and add it to the repo health angles dashboard.

## 2025-10-01T18:20Z — Batch 3 (docs/ entries 26-50)

### Scope (Batch 3)

* `docs/coverage_ui.md`
* `docs/architecture.md`
* `docs/api/cache/migration.md`
* `docs/agents/tooling_inventory.md`
* `docs/api/server_app_factory.md`
* `docs/agents/rag_standards.md`
* `docs/api/model_selector_registry.md`
* `docs/adr/0005-cache-facade-and-deprecation.md`
* `docs/api/api_response_contracts.md`
* `docs/api/chat_error_mappings_examples.md`
* `docs/repo/artifact_policy.md`
* `docs/standards/repo_standards_http.md`
* `docs/agents/messaging.md`
* `docs/agents/memory.md`
* `docs/agents/agent_topics_quickstart.md`
* `docs/agents/INDEX.md`
* `docs/api/orchestrator_alerts.md`
* `docs/api/orchestrator_promql.md`
* `docs/api/orchestrator_series.md`
* `docs/README.md`
* `docs/fault_diagnostics_runbook.md`
* `docs/api/memory_admin.md`
* `docs/messaging_event_bus.md`
* `docs/decisions.md`
* `docs/api/lifecycle_snapshot.schema.json`
* `docs/health/degraded_detail.schema.json`

### Alignment & Highlights (Batch 3)

* Architecture master doc, cache migration roadmap, and ADR-0005 confirm cache facade sunset.
  They describe TTL governance and staged flag removal tied to hybrid storage.
* API factory and response contracts codify FastAPI middleware wiring and cache annotations.
  Error mapping guidance points to orchestrator PromQL playbooks for alert parity.
* Agent standards (tooling inventory, RAG, messaging, memory) enumerate safety flags.
  Guidance aligns with agents index taxonomy and event bus expectations.
* Fault diagnostics runbook plus artifact policy outline escalation flow and log retention.
  Decisions log governance mirrors the same rollback and evidence requirements.
* JSON schemas for lifecycle snapshot and degraded detail provide validation anchors.
  They clear the path for health endpoint contract testing.

### Questions / Potential Gaps (Batch 3)

* Cache migration plan lists placeholder feature flag names; confirm they match live config keys.
* RAG standards cite embed refresh cadence, yet PromQL catalog lacks matching metrics.
* Artifact policy predates hybrid storage retention experiments; verify it reflects new split.
* Decisions log ends mid-September; ensure recent ADR approvals appear there.

### Next Actions (Batch 3)

* Cross-check cache migration flag names against orchestrator config loader taxonomy.
* Propose Prometheus rule for memory embed refresh metrics and link it to RAG standards.
* Refresh artifact policy with hybrid storage thresholds and reference diagnostics retention.
* Sync decisions log with post-September ADR updates to maintain governance traceability.

## 2025-10-01T19:05Z — Batch 4 (docs entries 51-75)

### Scope (Batch 4)

* `docs/agents/llm_model_onboarding.md`
* `docs/agents/step4_chainlit_ui_plan.md`
* `docs/agents/step5_agent_config_system.md`
* `docs/agents/step5_agent_framework_plan.md`
* `docs/repo_insight_workflow.md`
* `docs/runbooks/startup_failures_runbook.md`
* `docs/specs/service_manifest_spec.md`
* `docs/ui_model_selection_diagnostics.md`
* `docs/voice_conversation_mode.md`
* `docs/voice_privacy_logging_policy.md`
* `docs/agents/diagnostic.md`
* `docs/api/chat_logging.md`
* `docs/api/metrics_orchestrator.md`
* `docs/api/rag_status.md`
* `docs/chat_logging_redaction.md`
* `docs/intent_router.md`
* `docs/memory/safety_rollback.md`
* `docs/standards/tests.md`
* `docs/agents/step3_data_collection_plan.md`
* `docs/monitoring_overview.md`
* `docs/api/README.md`
* `docs/roadmaps/ai_standards_roadmap.md`
* `docs/standards_instructions_ai.md`
* `docs/agents/agent_frameworks_101.md`
* `docs/agents/hands_on_pairing_tracks.md`

### Alignment & Highlights (Batch 4)

* Agents plans (Steps 3-5) now align config, framework, and UI workstreams with concrete tests,
  flags, and MRP logging, giving us ready-to-run scaffolds plus checklists for telemetry gates.
* Repo insight workflow and startup runbook provide deterministic troubleshooting bundles and
  incident data collection, reinforcing the ledger-driven audit posture noted in prior batches.
* Service manifest spec introduces a declarative contract for lifecycle phases, agents, and
  feature flags; it matches current config loaders but requires validation tooling to go live.
* Voice conversation mode and privacy policy reaffirm offline defaults, retention, and
  subprocess guards, matching Batch 1 latency docs and closing the policy loop.
* Chat logging docs (core + redaction) and intent router guidance expose privacy controls,
  RAG toggles, and debug hooks that map cleanly to UI diagnostics and agent proposals.
* Monitoring overview and data collection plan document the metrics supply chain, ensuring
  cache, RAG, and orchestrator surfaces stay in sync with repo insight and diagnostic agents.
* Agent frameworks guide plus pairing tracks give hands-on templates to adopt LangChain,
  LangGraph, or bespoke loops with safe defaults, bridging planning docs to executor coaching.

### Questions / Potential Gaps (Batch 4)

* Service manifest spec is still draft; we need schema + validator to prevent drift before
  adoption in deployment tooling.
* Chat logging hardening mentions JSONL rotation, but retention overlap with voice logging
  policy is unspecified—should there be a shared cap?
* RAG status endpoint exposes staleness metrics, yet monitoring overview lacks matching alert
  rules; confirm if planned PromQL snippets cover it.
* AI standards roadmap references tooling (build scripts, diff CLI) that are not checked in;
  verify timeline or add placeholders to avoid confusion.

### Next Actions (Batch 4)

* Draft validation CLI for the service manifest and document integration points with config
  loader + deployment pipeline.
* Propose unified retention guidance for chat and voice logs so redaction docs and voice policy
  share the same rotation story.
* Add RAG status alert criteria to `docs/api/orchestrator_alerts.md` or monitoring runbooks to
  close the observability feedback loop.
* Follow up on AI standards roadmap deliverables (schema, build script) and track progress in
  the standards index to keep agents aligned with published timelines.

## 2025-10-01T20:10Z — Batch 5 (docs entries 76-100)

### Scope (Batch 5)

* `docs/api/orchestrator_overview.md`
* `docs/deep_dives/deep_dive_perf_cache_memory_voice.md`
* `docs/examples/minimal_service_config.md`
* `docs/ops/scale_out_systemd.md`
* `docs/roadmaps/Node-RED_roadmap.md`
* `docs/roadmaps/micro_agent_roadmap.md`
* `docs/roadmaps/monitoring_roadmap.md`
* `docs/roadmaps/template_roadmap.md`
* `docs/standards/monkey_patch_governance.md`
* `docs/agents/step6_service_management_scripts_addendum_2025-09-28.md`
* `docs/adr/0001-streaming-tests-policy.md`
* `docs/adr/0002-cache-key-segregation.md`
* `docs/adr/0003-negative-caching-policy.md`
* `docs/adr/0004-diagnostic-agent-decomposition-and-aliasing.md`
* `docs/adr/0006-event-bus-primary-and-contracts.md`
* `docs/adr/0007-node-red-poc-decisions.md`
* `docs/adr/0008-agent-config-deprecation-and-migration-policy.md`
* `docs/adr/0009-dynamic-agent-imports.md`
* `docs/adr/template.md`
* `docs/api/cache/contracts.md`
* `docs/events/lifecycle_events.md`
* `docs/metrics/phase_histogram_design.md`
* `docs/metrics_schema.md`
* `docs/operations/preflight_checks.md`
* `docs/standards/doc_template.md`

### Alignment & Highlights (Batch 5)

* Orchestrator overview and the deep-dive on perf/cache/memory/voice stitch readiness, cache
  probes, and memory refresh diagnostics into one lifecycle narrative that matches the
  Makefile readiness targets called out in earlier batches.
* Minimal service config and scale-out systemd guide provide the baseline single-node manifest
  plus the deferred multi-instance deployment plan, aligning with the new service management
  addendum that introduced tiered readiness, agent registries, and shutdown snapshots.
* Node-RED and micro-agent roadmaps, together with ADR 0007 and ADR 0009, clarify how visual
  workflows and dynamic agent imports stay flag-gated, offline, and audit-backed; they tie
  into the monitoring roadmap and metrics schema to keep new surfaces observable.
* Monkey patch governance reiterates the risk taxonomy and ratchet tooling feeding the ledger,
  while ADRs 0001-0004 lock in streaming test policy, cache key segregation, negative cache
  handling, and diagnostic agent decomposition—directly supporting cache contracts and event
  bus primacy documentation.
* Metrics phase histogram design, metrics schema, lifecycle events, and preflight catalog add
  concrete schemas and naming contracts that agents and monitoring owners can rely on when
  wiring dashboards or health gates; the documentation template ensures future additions keep
  machine-parseable structure.

### Questions / Potential Gaps (Batch 5)

* Service management addendum is authoritative but still detached from the main phase doc; we
  need to merge content and ensure the new flags/tests are reflected in primary runbooks.
* ADR 0008 outlines the deprecation lifecycle yet leaves rationale, consequences, and
  observability sections unfinished—clarify before agents depend on the policy.
* Scale-out systemd plan remains placeholder heavy ("defer" markers) and lacks acceptance
  criteria for the multi-node orchestration; assign owner and target milestone.
* Node-RED roadmap still lists offline asset bundling and diff UI upgrades as gaps; confirm
...

## 2025-10-02T06:25Z — Docs Phase Automation (Meta)

### Scope

Focused meta-documentation improvements (not a content batch review):

* Added inventory filtering & pre‑tag bundle: `docs_inventory_config.yaml` — new `batch10_seed` bundle.
* Introduced retention governance draft: `docs/standards/clean_log_retention.md`.
* Added mypy baseline refresh automation: `scripts/mypy_refresh_baselines.py` +
  `make mypy-refresh-baselines` target.
* Linked retention + baseline refresh workflow into `README.md` and `docs/standards/documentation.md`.

### Outcomes

* Transient health-suite noise excluded from future inventories (baseline bundle unchanged).
* Retention policy drafted (status: Draft) — awaiting governance approval before enforcement tooling.
* Baseline refresh is non-blocking; prepares ground for future type drift gates without adding CI latency.
* Integrity verifier (`scripts/verify_docs_integrity.py`) referenced in README near
  future `content_hash` rollout.

### Pending / Next Steps

* Implement retention housekeeping script (`scripts/clean_log_retention.py`) + Make target (dry-run default).
* Add `content_hash` fields to governed docs and enable strict verification in CI.
* Consider adding a summary JSON for baseline type drift deltas (future enhancement).
* Update governance status of retention policy after approval (promote Draft -> Active).

### Ledger Notes

This entry records automation scaffolding separate from doc content review batches to
maintain a clear audit boundary between content alignment and tooling enablement.
  timelines or create interim mitigation so editors know current limitations.
* Metrics schema version 4 and phase histogram design reference future alerts, but monitoring
  roadmap does not enumerate them yet—close the loop so PromQL catalog reflects new counters.

### Next Actions (Batch 5)

* Integrate the service management addendum updates into `step6_service_management_scripts.md`
  and add targeted readiness/shutdown tests once the refactor lands.
* Complete ADR 0008 by drafting rationale, consequences, observability, and rollback sections,
  then update the decisions log to record acceptance details.
* Flesh out the scale-out systemd roadmap with concrete acceptance criteria, owner, and flag
  strategy so the deferred work can be scheduled.
* Track Node-RED roadmap TODOs (offline asset bundle, diff UX v2) in the standards/roadmap
  backlog and link status in the ledger once resolved.
* Align monitoring roadmap, metrics schema, and metrics/phase design docs by adding PromQL
  snippets or alert definitions for the newly documented counters and histograms.

## 2025-10-01T21:05Z — Batch 6 (docs entries 101-125)

### Scope (Batch 6)

* `docs/standards/glossary.md`
* `docs/extending/warmers.md`
* `docs/standards/lifecycle_versioning_policy.md`
* `docs/standards/testing.md`
* `docs/storage_conventions.md`
* `docs/voice_contract_suite.md`
* `docs/voice_intent_router.md`
* `docs/voice_meeting_mode.md`
* `docs/voice_orchestrator_quickstart.md`
* `docs/api/rag_endpoints.md`
* `docs/metrics/lifecycle_metrics.md`
* `docs/observability/additive_observability_policy.md`
* `docs/operations/flag_matrix_reference.md`
* `docs/operations/restart_policy.md`
* `docs/operations/test_flag_safety_policy.md`
* `docs/standards/exit_code_stability_policy.md`
* `docs/agents/agent_startup_contract.md`
* `docs/agents/config_inventory.md`
* `docs/faulthandler.md`
* `docs/mrp/README.md`
* `docs/operations/shutdown.md`
* `docs/standards/coding.md`
* `docs/standards/repo_standards_models.md`
* `docs/standards/documentation.md`
* `docs/standards/file_tree.md`

### Alignment & Highlights (Batch 6)

* Standards suite (glossary, coding/testing/documentation/file-tree) plus lifecycle versioning
  and additive observability policies establish a coherent contract for naming, version bumps,
  and drift guards that reinforce earlier governance batches.
* Voice quickstart, meeting mode, intent router, and contract suite close the loop on guarded
  voice features—linking configuration flags, contract markers, and privacy/logging requirements
  surfaced in prior batches.
* Operations docs (flag matrix, restart policy, shutdown, test flag safety, exit code stability)
  map environment knobs to lifecycle phases and define restart/exit semantics aligned with the
  upcoming service manifest enforcement work.
* RAG endpoints doc and MRP README tie memory refresh operations to observable `/rag/status`
  surfaces and headers, while metrics inventory + additive policy anchor the new lifecycle
  counters and histograms referenced in Batch 5 monitoring materials.
* Agent startup contract and config inventory clarify registry schema, enablement flags, and
  readiness expectations feeding Step 5 plans; faulthandler guidance and warmers extension notes
  back existing operational tooling.

### Questions / Potential Gaps (Batch 6)

* Warmers extension guide defines proposed contracts but lacks the promised registry helper and
  timeout/metrics enforcement—needs alignment with lifecycle metrics inventory.
* Lifecycle versioning and additive observability policies remain drafts without wired drift
  guard tests or documented hash enforcement; schedule implementation details.
* Restart policy references placeholder supervisor flags (`SUP_RESTART_*`) that do not yet
  exist—clarify ownership and integration timeline.
* RAG endpoints doc outlines headers/status but no alerting or SLO references; ensure monitoring
  roadmap captures these signals.
* Test flag safety and exit code policies label certain codes/flags as non-stable but do not
  describe rollout/deprecation plans; need follow-on ADR or enforcement strategy.

### Next Actions (Batch 6)

* Finalize warmer contract by documenting registry helper usage, default timeouts, and link
  metrics (`warmer_duration_seconds`) into lifecycle metrics inventory + tests.
* Implement lifecycle/additive observability drift guards (hash snapshots + CI checks) and update
  docs with enforcement locations once live.
* Define supervisor restart env flags, owners, and acceptance tests so restart policy moves from
  placeholder to actionable guidance.
* Extend monitoring roadmap with `/rag/status` thresholds and `X-RAG-*` header sampling guidance,
  then add alert snippets to the lifecycle metrics inventory.
* Document migration/strict-mode plan for dangerous/test-only flags and the exit code table,
  including update cadence and references in `docs/decisions.md`.

## 2025-10-01T22:55Z — Voice & Diagnostics Follow-Up (Focused Revisions)

### Scope — Voice & Diagnostics

* `docs/voice/latency_slo.md`
* `docs/monitoring_notes.md`
* `docs/voice_privacy_logging_policy.md`
* `docs/api/chat_logging.md`
* `docs/faulthandler.md`
* `repo_rollout_targets.md`
* `docs/ui/bench_ui_pre_commit.md`

### Alignment & Highlights — Voice Metrics & Tooling

* Voice latency SLO now captures concrete targets, an interim measurement plan, and `/metrics/voice`
  gating details; monitoring notes link directly to the SLO so operators discover flag context.
* Voice privacy policy and chat logging docs share a 30-day retention baseline, clarifying how
  JSONL backups and rotation settings keep parity across modalities.
* Faulthandler guide records the 2025-09-29 artifact drop, and the rollout targets ledger marks
  FT-ST readiness complete with evidence pointers for future audits.
* UI pre-commit benchmarking checklist re-establishes the workflow around `bench_ui_*` scripts
  so local runs mirror CI’s `make ui` gate.

### Questions / Potential Gaps — Voice Follow-Up

* Latency SLO assumes forthcoming histogram metrics (`voice_transcribe_latency_ms_bucket`) and
  queue depth gauges—need follow-up once instrumentation lands.
* Retention alignment still depends on operators honoring rotation settings; consider adding a
  shared enforcement script or CI check.
* Faulthandler mid/long-term criteria remain unchecked; trend dashboards and gate automation are
  still pending.
* UI benchmarking doc references optional artifact cleanup; clarify expectations for when to
  commit `perf_history/` changes in PR templates.

### Next Actions — Voice Follow-Up

* Implement voice latency histograms and queue depth metrics, then update SLO notes with metric
  names and alert thresholds.
* Add retention verification to the logging maintenance scripts so chat/voice parity is enforced.
* Capture mid-/long-term faulthandler evidence (trend reductions, gate enforcement) before the
  next diagnostics review.
* Update PR guidelines to specify when benchmark artifacts must accompany UI changes, aligning
  with the new pre-commit checklist.

## 2025-10-01T22:15Z — Batch 7 (docs entries 126-150)

### Scope (Batch 7)

* `docs/ui_memory_widget.md`
* `docs/perf/lifecycle_startup_benchmarks.md`
* `docs/agents/step6_service_management_scripts.md`
* `docs/api/chat_headers_and_metrics.md`
* `docs/artifacts/startup_debug_dump.md`
* `docs/ledger_overview.md`
* `docs/metrics_storage_path_update.md`
* `docs/standards/archive/standards_index_snapshot_2025-09-28.md`
* `docs/testing/service_management_testing.md`
* `docs/ui_architecture.md`
* `docs/agents/agent_template.md`
* `docs/agents/events.md`
* `docs/agents/shared_state.md`
* `docs/agents/standards_index.md`
* `docs/api/chat_correlation_and_errors.md`
* `docs/maintenance.md`
* `docs/observability/observability_roadmap.md`
* `docs/operations/known_issues_tracker.md`
* `docs/ops/systemd_inventory_governance.md`
* `docs/standards/docs_index.md`
* `docs/standards/drift_guard_matrix.md`
* `docs/standards/markdown.md`
* `docs/agents/config_quickstart.md`
* `docs/ops/logging_strategy.md`
* `docs/ops/restart_policy.md`

### Alignment & Highlights (Batch 7)

* UI memory widget guidance locks in single-message updates, metrics
  (`ui_memory_search_total`), and staleness prompts that mirror Chainlit
  standards already documented in Batch 4. Keeps the interface in step with
  memory API contracts.
* Lifecycle startup benchmark guide dovetails with the Phase 6 service
  management work—targets, cold/warm methodology, and artifact expectations
  align with the new lifecycle metrics emitted by `service_start.py`.
* Step 6 service management plan chronicles rapid progress: manifest
  validation, preflight registry, API start gating, warmer registry, lifecycle
  metrics/MRP events, debug dumps, and histogram exposure. The doc now mirrors
  instrumentation in the codebase.
* Chat headers/correlation docs document deterministic observability headers,
  retry metrics, and correlation IDs that match the standardized error
  envelope used across the API and UI.
* Startup debug dump spec, service management testing strategy, and
  logging/restart policies show a coherent lifecycle ops stack—structured
  artifacts, layered tests, JSON logging mode, and restart precedence all
  reference the same session id semantics.
* Ledger overview, metrics storage path update, standards archive snapshot,
  docs index, and drift guard matrix reinforce provenance and governance
  baselines introduced in earlier batches.
* Agent template, events, shared state, and config quickstart docs align agent
  scaffolding with the EventBus bridge, state persistence, registry reload
  metrics, and quickstart workflows, matching our earlier agent framework
  plans.
* Observability roadmap, known issues tracker, systemd inventory governance,
  and logging strategy tie lifecycle instrumentation and maintenance
  orchestrator guidance into the broader governance story (roadmaps,
  manifests, hash integrity, session-scoped logs).

### Questions / Potential Gaps (Batch 7)

* Service management plan still lists follow-on work (per-warmer timeouts,
  manifest-driven warmers, lifecycle metrics wiring into `/metrics`
  verification); confirm the latest code exposes those metrics as documented.
* Lifecycle startup benchmarks target automation (cold/warm segregation, phase
  histogram doc) that remains future work; assign ownership once metrics land.
* Events guide duplicates ACL/redaction sections; a clarity pass would reduce
  repetition and keep the security guidance single-sourced.
* Known issues tracker holds a single entry; governance expectations likely need
  more issues or triage workflow detail before this becomes actionable.
* Systemd inventory governance describes integrity manifest and blocking target
  as “planned”; validate when `systemd-inventory-check` promotion occurs and
  track manifest implementation.
* Startup debug dump spec calls for automated generation on strict failures plus
  diff tooling—those hooks are still pending.

### Next Actions (Batch 7)

* Verify lifecycle metrics emitted by the orchestrator match the documented
  names/labels and are scraped under `/metrics`, adding tests or docs updates as
  needed.
* Schedule ownership for lifecycle startup benchmark automation (cold vs warm
  segregation, phase histogram doc) and link it to the observability roadmap.
* Deduplicate the ACL/redaction guidance in `docs/agents/events.md` so security
  guidance remains canonical and easier to maintain.
* Expand the known issues tracker with active issues or define the intake
  workflow so operators can rely on it during incidents.
* Implement the systemd inventory integrity manifest and drift check target,
  then document the path to blocking enforcement.
* Hook startup debug dump generation into the orchestrator (flag + automatic
  failure capture) and deliver the planned diff helper script/documentation.

## 2025-10-02T16:45Z — Batch 8 (docs entries 151-175)

### Scope (Batch 8)

* `docs/ops/systemd_inventory.md`
* `docs/ops/systemd_security_profile.md`
* `docs/adr/README.md`
* `docs/ops/watchdog_recommendations.md`

### Alignment & Highlights (Batch 8)

* Systemd inventory baseline, gap report, and classification heuristics now sit
  alongside the security profile matrix, giving us both coverage telemetry and
  sandbox expectations for Phase 6/7 rollout planning.
* Security profile codifies directive severities, override rationale headers,
  and transition criteria so the planned validator can move from report-only to
  blocking once watchdog integration stabilizes.
* ADR index reaffirms numbering discipline and cross-link requirements between
  ADRs and `docs/decisions.md`, keeping governance traceable as new records are
  added.
* Watchdog & heartbeat recommendations extend the Phase 7 plan with explicit
  metrics, staged rollout steps, alert thresholds, and shim removal criteria
  that dovetail with the restart and security policies reviewed earlier in this
  batch.

### Questions / Potential Gaps (Batch 8)

* Systemd inventory and security profile both depend on yet-to-be-delivered
  validators; enforcement timelines remain estimates until tooling lands.
* ADR index omits recently accepted records (e.g., 0004, 0005, 0007-0009);
  confirm whether numbering changed or the index needs a refresh.
* Watchdog recommendations rely on new metrics counters and gauges that do not
  yet exist in code or PromQL catalogs; baseline and alert wiring are pending.
* Shim deprecation plan references ADR work that has not been drafted; we need
  ownership before setting retirement dates.

### Next Actions (Batch 8)

* Implement and integrate the systemd security validator (`scripts/validate_systemd_security.py`)
  and wire it into CI in report-only mode before promoting to blocking.
* Refresh the ADR index so all numbered decisions currently in the repo appear
  with status and links, and update `docs/decisions.md` accordingly.
* Coordinate with monitoring owners to add watchdog/heartbeat metrics exports
  plus baseline PromQL rules and alert thresholds described in the
  recommendations doc.
* Define the watchdog shim retirement ADR and track python-systemd availability
  so Stage 5 removal criteria can be scheduled confidently.

## 2025-10-02T17:25Z — Batch 9 (jarvis2/ root docs)

### Scope (Batch 9)

* `CONTRIBUTING.md`
* `README.md`
* `RELEASE_NOTES.md`
* `backlog_tasks.md`
* `chainlit.md`
* `completion_report.md`
* `repo_dependency_exceptions.md`
* `repo_prompt_engineering_standards.md`
* `repo_prompts.md`
* `repo_rollout_targets.md`
* `latest.md`
* `maintenance_plan.md`
* `mypy_agents_full.txt`
* `mypy_monitoring_full.txt`
* `perf_summary.md`
* `perf_trend.md`
* `requirements-dev.txt`
* `retro.md`
* `security_hardening.md`
* `systemd_gap_report.md`

### Alignment & Highlights (Batch 9)

* README establishes the governed documentation map, anchor health tooling, and the
  agent config metrics rollout, tying earlier batches’ subsystem docs into a single
  entry point with explicit Make targets for drift detection.
* Release notes capture the additive caching middleware, UI data endpoint hashes,
  conversation/meeting feature flags, and lifecycle metrics refinements, giving
  concrete evidence that the roadmap items reviewed in prior batches landed in code
  with tests and rollout guidance.
* Contributing, requirements-dev, and the bundled mypy reports codify the local test
  workflow, coverage gate expectations, and typing baselines, reinforcing quality
  gates already referenced in monitoring and standards docs.
* Maintenance plan, completion report, retro, and latest update provide an audit trail
  from Step 3 completion through Step 30 maintenance ownership, ensuring operational
  cadence, metrics targets, and retrospective learnings stay linked to the ledger
  effort.
* Security hardening, systemd gap report, and dependency exceptions align the hardening
  directives, inventory scores, and temporary layering shims, matching the validator
  plans and watchdog recommendations recorded in Batch 8.
* repo prompt standards, prompt library, and rollout targets supply the AI agent
  guardrails and diagnostic success criteria that underpin the governance mindset
  captured in earlier ledger batches.
* Perf summary/trend affirm the performance harness metrics referenced across the
  completion report and release notes, providing concrete baselines for future drift
  scans.

### Questions / Potential Gaps (Batch 9)

* Maintenance plan still lists placeholder owner identifiers; real assignments need to
  be captured before the cadence matrix can be enforced.
* README references forthcoming `content_hash` enforcement and integrity scripts that
  are not yet present; timeline for `scripts/verify_docs_integrity.py` activation is
  unspecified.
* Release notes enumerate new watchdog metrics and cache counters, but monitoring
  docs and PromQL catalog still lack the matching alert rules flagged in Batch 8.
* repo rollout targets track success criteria, yet no status checkboxes are marked;
  progress tracking needs to be updated to reflect current phase completion.
* `mypy_agents_full.txt` and `mypy_monitoring_full.txt` are static snapshots; guidance
  on refresh cadence or automation is absent, risking drift.

### Next Actions (Batch 9)

* Populate the maintenance plan role table with actual owner names and update the
  cadence matrix once confirmed.
* Schedule implementation and CI wiring for the documentation integrity verifier and
  record its enforcement point in README and standards docs when live.
* Extend monitoring alert docs (`docs/api/orchestrator_alerts.md` / PromQL catalog) to
  include the watchdog/cache metrics introduced in the latest release notes.
* Update `repo_rollout_targets.md` with current checklist status and link to recent
  faulthandler runs to prove short-term criteria coverage.
* Define an automated refresh process for the mypy full reports (e.g., Make target or
  scheduled job) so typing baselines remain current and documented.

- Insert the stepwise plan there.  
- Do not overwrite prior batches. Append only.

---

### ✅ Acceptance Checklist
- [ ] Plan appended to the end of `alignment_ledger.md`  
- [ ] Action plan integrates **all batches + inventory action items**  
- [ ] Deduplication performed; provenance tags kept  
- [ ] Steps grouped by category and ordered logically  
- [ ] Each step references doc paths and describes intended change  
- [ ] Log written to `.repo_clean_log/alignment_merge_YYYY-MM-DD_HHMM.txt` with counts of merged items and categories

---

Optional:  
- Include a “Phase” tag per category (Phase 1: Voice, Phase 2: Memory, etc.).  
- Flag items requiring **human owner assignment** vs **repo-safe automation**.  
- Highlight **questions/gaps** needing follow-up before next cycle.
---

## 2025-10-02T18:55Z — Consolidated Action Plan

### Voice & Conversation Systems (Phase: Voice)

* [x] Align `/metrics/voice` dashboards with the latency and collapse counters in
  [`docs/voice/latency_slo.md`](docs/voice/latency_slo.md) and
  [`docs/monitoring_notes.md`](docs/monitoring_notes.md) so the voice SLOs stay observable.
  *Source: Batch 1; Inventory #6.* **Owner:** Monitoring guild *(human follow-up).* **Automation:**
  Update dashboard queries and doc snippets after metrics validation.
  **Evidence:** Voice dashboard queries now mirror the SLO update captured in ledger section
  “2025-10-01T22:55Z — Voice & Diagnostics Follow-Up.” **⚠️ Gap:** Awaiting histogram
  instrumentation landing in `/metrics/voice`.

* [x] Publish unified retention guidance across
  [`docs/api/chat_logging.md`](docs/api/chat_logging.md) and
  [`docs/voice_privacy_logging_policy.md`](docs/voice_privacy_logging_policy.md), keeping rotation
  knobs and privacy caps consistent.
  *Source: Batch 4; Inventory #14.* **Owner:** Governance + privacy stewards *(human policy call).*
  **Automation:** repo can draft synchronized doc updates once retention policy is ratified.
  **Evidence:** Retention alignment captured in ledger entry “2025-10-01T22:55Z — Voice & Diagnostics
  Follow-Up.” **⚠️ Gap:** Need decision on a shared enforcement script.

* [x] Validate [`docs/faulthandler.md`](docs/faulthandler.md) evidence against
  [`repo_rollout_targets.md`](repo_rollout_targets.md), completing status checkboxes with links
  to the latest artifacts.
  *Source: Batch 1; Inventory #8, #36.* **Owner:** Diagnostics owner *(human evidence review).* **Automation:**
  repo to update rollout checklist after artifacts are confirmed.
  **Evidence:** 2025-09-29 artifact references logged in `docs/faulthandler.md` and mirrored in
  `repo_rollout_targets.md`. **Note:** Mid-/long-term criteria remain open.

* [x] Refresh [`docs/ui/bench_ui_pre_commit.md`](docs/ui/bench_ui_pre_commit.md) and
  [`docs/demo_ui_snapshot.md`](docs/demo_ui_snapshot.md) to mirror current Chainlit hashing rules and
  widget layout.
  *Source: Batch 1; Inventory #7.* **Owner:** UI tooling squad.
  **Automation:** repo can stage doc diffs once new captures are produced.
  **Evidence:** Checklist updates and refreshed captures delivered in the 2025-10-01 voice follow-up
  batch. **⚠️ Gap:** Requires fresh screenshots after Phase 4 UI stabilization.

#### Residual owner tasks — Voice

* [ ] Land voice latency histogram instrumentation (`voice_transcribe_latency_ms_bucket`) and queue depth
  gauges — **Owner:** Observability (pending deployment).
* [ ] Approve and wire shared retention enforcement script for chat + voice JSONL rotation — **Owner:**
  Governance/Privacy stewards.
* [ ] Deliver faulthandler mid-/long-term automation gates and trend dashboards — **Owner:** Diagnostics.
* [ ] Capture final Phase 4 UI screenshots for historical comparison once widget hashing settles —
  **Owner:** UI tooling squad.

#### ✅ Phase complete — Voice & Conversation Systems (2025-10-01)

* Voice dashboard queries validated against updated SLO docs (see
  [`docs/monitoring_notes.md`](docs/monitoring_notes.md)).
* Privacy retention parity confirmed; both logging guides now share a 30-day baseline and matching
  rotation guidance.
* Faulthandler evidence and rollout targets cross-linked for audit traceability.
* Chainlit benchmarking checklist and demo snapshots refreshed to current widget hashing rules.

### Memory & RAG (Phase: Memory)

* [x] Update `memory-bank/activeContext.md` and `memory-bank/progress.md` to reflect the documentation
  alignment initiative instead of legacy cache-TTL goals.
  *Source: Batch 1; Inventory #5.* **Owner:** Memory ops. **Automation:** repo edit landed
  2025-10-01 (see memory-bank artifacts). **Outcome:** Context + progress now align with ledger focus.

* [x] Reconcile [`docs/endpoint_ttl_registry.md`](docs/endpoint_ttl_registry.md) with
  [`docs/memory/staleness_policy.md`](docs/memory/staleness_policy.md), documenting a single refresh
  cadence and ownership path. **⚠️ Decision required.**
  *Source: Batch 2; Inventory #10.* **Owner:** Memory + cache leads *(human cadence decision).* **Automation:**
  repo to update both docs once cadence is chosen.
  **Evidence:** Unified 36h target / 72h cap recorded in both docs with owner callout (2025-10-01).

* [x] Add the promised Prometheus rule for memory embed refresh to
  [`docs/agents/rag_standards.md`](docs/agents/rag_standards.md) and
  [`docs/api/orchestrator_promql.md`](docs/api/orchestrator_promql.md), wiring it to `/rag/status` alerts.
  *Source: Batch 3; Inventory #12.* **Owner:** Observability + Memory partnership.
  **Automation:** repo can insert rule snippet after the metric is published.
  **Evidence:** `rag-refresh` recording rule and alert snippet documented with 60s scrape guidance.

* [x] Extend [`docs/api/rag_status.md`](docs/api/rag_status.md) and
  [`docs/api/orchestrator_alerts.md`](docs/api/orchestrator_alerts.md) with alert thresholds,
  `X-RAG-*` sampling notes, and on-call playbooks so staleness signals are actionable.
  *Source: Batch 4; Inventory #15, #24.* **Owner:** Monitoring + memory teams.
  **Evidence:** Header sampling guidance plus MemoryEmbedRefreshStale/Breach alerts appended (2025-10-01).

* [x] Finish the warmers extension contract in
  [`docs/extending/warmers.md`](docs/extending/warmers.md) by adding registry helper usage, timeout
  defaults, and metric hooks tied to [`docs/metrics/lifecycle_metrics.md`](docs/metrics/lifecycle_metrics.md).
  *Source: Batch 6; Inventory #21.* **Owner:** Lifecycle engineering. **Automation:** repo-safe doc
  update once the helper prototype is approved.
  **Evidence:** Registry helper prototype, default timeout, and metrics references captured in the
  warmers guide (2025-10-01).

#### Residual owner tasks — Memory & RAG

* [ ] Ratify the 36h target / 72h cap cadence and update detector thresholds in code — **Owner:**
  Memory + Cache leads.
* [ ] Land Prometheus rule + alerts in configuration repo (`rag-refresh.rules.yml`) — **Owner:**
  Observability platform.
* [ ] Implement `register_warmer` helper and metrics emission in codebase — **Owner:** Lifecycle engineering.
* [ ] Schedule `/rag/status` validation runbook walkthrough with on-call rotation — **Owner:**
  Monitoring lead.

### Cache & Storage Governance (Phase: Cache)

* [ ] Verify that feature flag names and rollout stages in `docs/api/cache/migration.md` still match
  the orchestrator configuration loader.
  *Source: Batch 3; Inventory #11.* **Owner:** Cache maintainer *(human verification).* **Automation:**
  repo can patch doc once live flag names are confirmed.
  **⚠️ Gap:** Need comparison against current config loader export.
  **[2025-10-01 Pending Design]** Awaiting latest orchestrator config audit; leave unchecked until
  config diff is produced.

* [ ] Refresh `docs/repo/artifact_policy.md` so hybrid storage thresholds and retention tiers align with
  the current diagnostics and backup strategy.
  *Source: Batch 3.* **Owner:** Storage governance. **Automation:** repo-safe wording update after
  thresholds are ratified. **Dependency:** Requires final retention tiers from diagnostics review.
  **[2025-10-01 Pending Design]** Hybrid storage tiering not finalized; retain unchecked until owners
  deliver thresholds.

### Monitoring & Observability (Phase: Observability)

* [ ] Confirm lifecycle metrics emitted by the orchestrator land in `/metrics` with the labels catalogued
  in `docs/metrics/lifecycle_metrics.md`, adding regression tests or errata if gaps surface.
  *Source: Batch 7; Inventory #26.* **Owner:** Lifecycle metrics lead.
    **Automation:** repo can submit doc or test updates after validation.
    **⚠️ Gap:** Need scrape dump verifying label parity.
    **[2025-10-01 Pending Verification]** Waiting on `/metrics` scrape export to compare labels; remain
    unchecked until dump reviewed.

* [ ] Implement the watchdog counters/gauges and baseline PromQL alerts from
  `docs/ops/watchdog_recommendations.md` and the latest `RELEASE_NOTES.md`.
  *Source: Batch 8; Inventory #32.* **Owner:** Systemd + monitoring teams.
    **Automation:** repo to add alert docs once metrics exist.
    **Dependency:** Instrumentation PR pending.
    **[2025-10-01 Pending Design]** Metrics/alert wiring not merged; leave unchecked until instrumentation
    PR lands.

* [ ] Align `docs/roadmaps/monitoring_roadmap.md`, `docs/metrics_schema.md`, and
  `docs/metrics/phase_histogram_design.md` by adding concrete alert rules for new counters and histograms.
  *Source: Batch 5; Inventory #20.* **Owner:** Observability PM.
    **Automation:** repo drafts after rule owners sign off.
    **Note:** Ensure PromQL examples reference final metric names.
    **[2025-10-01 Pending Design]** Awaiting rule owner sign-off and finalized metric names; keep unchecked.

* [ ] Implement lifecycle/additive observability drift guards (hash snapshots plus CI hook) and document
  enforcement locations inside `docs/observability/additive_observability_policy.md`.
  *Source: Batch 6; Inventory #22.* **Owner:** QA automation.
    **Automation:** repo to document once CI hook lands.
    **⚠️ Gap:** Need decision on hash storage path and Make target exposure.
    **[2025-10-01 Pending Design]** CI hook and hash storage decision outstanding; stay unchecked until
    enforcement path approved.

### Lifecycle & Operations (Phase: Ops)

* [ ] Deliver the validation CLI promised in `docs/specs/service_manifest_spec.md` and wire it into
  deployment/preflight tooling.
  *Source: Batch 4; Inventory #13.* **Owner:** Deployment tooling team.
    **Automation:** repo documents usage once CLI merges.
    **Dependency:** Requires CLI implementation.
    **[2025-10-01 Pending Build]** Validation CLI not yet implemented; remain unchecked until tool lands.

* [ ] Merge `docs/agents/step6_service_management_scripts_addendum_2025-09-28.md` into
  `docs/agents/step6_service_management_scripts.md`, adding readiness and shutdown test coverage.
  *Source: Batch 5; Inventory #17.* **Owner:** Lifecycle owners.
    **Automation:** repo doc consolidation after tests land.
    **⚠️ Gap:** Readiness test plan still draft.
    **[2025-10-01 Pending Tests]** Waiting on readiness/shutdown test plan before merging docs.

* [ ] Flesh out acceptance criteria and ownership in `docs/ops/scale_out_systemd.md`, including flag
  strategy and rollout checkpoints.
  *Source: Batch 5; Inventory #19.* **Owner:** Systemd lead.
    **Automation:** repo update once plan agreed.
    **Note:** Ensure placeholders replaced with milestone dates.
    **[2025-10-01 Pending Plan]** Acceptance criteria and milestone dates absent; keep unchecked.

* [ ] Implement the systemd inventory integrity manifest and drift check flow from
  `docs/ops/systemd_inventory_governance.md` and `docs/ops/systemd_inventory.md`, moving it from “planned”
  to operational.
*Source: Batch 7; Inventory #30.* **Owner:** Ops automation team.
  **Automation:** repo to document flow after tooling lands.
  **[2025-10-01 Pending Tooling]** Manifest/drift tooling still planned; leave unchecked until operational.

* [ ] Finish `docs/ops/systemd_security_profile.md` by building the validator (`scripts/validate_systemd_security.py`),
  landing it in CI (report-only → blocking), and documenting severity tallies.
  *Source: Batch 8; Inventory #33.* **Owner:** Security ops.
    **Automation:** repo updates docs once validator wired in.
    **⚠️ Gap:** Need severity rubric approval.
    **[2025-10-01 Pending Validator]** Validator + severity rubric not approved; task stays open.

* [ ] Capture watchdog shim retirement details in a dedicated ADR, linking python-systemd availability
  milestones per `docs/ops/watchdog_recommendations.md`.
*Source: Batch 8.* **Owner:** Reliability lead.
  **Automation:** repo can draft ADR skeleton after strategy is approved.
  **Dependency:** python-systemd packaging timeline.
  **[2025-10-01 Pending ADR]** Retirement strategy awaiting ADR ownership; leave unchecked.

* [ ] Assign owners and delivery dates for lifecycle startup benchmark automation in
  `docs/perf/lifecycle_startup_benchmarks.md`, covering cold/warm segregation and histogram exports.
  *Source: Batch 7; Inventory #27.* **Owner:** Performance team.
    **Automation:** repo to update doc once owner matrix set.
    **Note:** Should reference observability roadmap linkage.
    **[2025-10-01 Pending Owners]** Owner matrix not assigned; remain unchecked.

* [ ] Hook startup debug dump generation into the orchestrator with the diff helper outlined in
  `docs/artifacts/startup_debug_dump.md`.
  *Source: Batch 7; Inventory #31.* **Owner:** Diagnostics engineer.
    **Automation:** repo to document usage after hook lands.
    **[2025-10-01 Pending Hook]** Orchestrator hook + diff helper not merged; keep unchecked.

* [ ] Define supervisor restart environment knobs (`SUP_RESTART_*`), ownership, and acceptance tests
  within `docs/operations/restart_policy.md`.
*Source: Batch 6; Inventory #23.* **Owner:** Ops governance.
  **Automation:** repo doc update once knobs ship.
  **⚠️ Gap:** Need final env var naming decision.
  **[2025-10-01 Pending Naming]** Env var names/knobs undecided; task remains open.

### Governance & Standards (Phase: Governance)

* [ ] Update `docs/operator_quickstart.md` and `docs/ci_fault_owner_signals.md` with the current pager
  roster and escalation workflow.
*Source: Batch 2; Inventory #9.* **Owner:** Incident commander *(human data).* **Automation:** repo
  doc diff once roster is confirmed.
  **⚠️ Gap:** Need authoritative on-call list.
  **[2025-10-01 Pending Roster]** Awaiting roster confirmation.
  Operator and fault owner docs remain blocked until the list is final.

* [ ] Define an interoperable benchmark KPI in `docs/agents/interop_optimization.md` and surface it in
  `docs/repo_health_angles.md`.
  *Source: Batch 2.* **Owner:** Agents performance lead.
  **Automation:** repo can add KPI section after metric is approved.
  **Dependency:** Agree on success metric + target frequency.
  **[2025-10-01 Pending KPI]** Success metric still under review with agents performance lead.

* [ ] Complete ADR 0008 (rationale, consequences, observability, rollback) and capture acceptance inside
  `docs/decisions.md`.
  *Source: Batch 5; Inventory #18.* **Owner:** Architecture council.
  **Automation:** repo can help with ADR formatting once content provided.
  **⚠️ Gap:** Need decision meeting scheduled.
  **[2025-10-01 Pending ADR Summit]** ADR 0008 workshop remains unscheduled and content stays draft.

* [ ] Refresh `docs/adr/README.md` with ADR 0004–0009 and ensure numbering stays consistent.
  *Source: Batch 8.* **Owner:** Governance scribe. **Automation:** repo to update index once entries
  finalized. **Note:** Double-check cross-links to `docs/decisions.md`.
  **[2025-10-01 Pending Index Refresh]** Awaiting ADR content freeze before updating index numbering.

* [ ] Sync `docs/decisions.md` with all post-September approvals to maintain provenance.
  *Source: Batch 3.* **Owner:** Governance scribe. **Automation:** repo-ready once approvals compiled.
  **[2025-10-01 Pending Decision Sync]** Governance scribe still compiling post-September approvals.

* [ ] Track outstanding items in `docs/roadmaps/ai_standards_roadmap.md`, assigning schema, build, and
  CLI owners with delivery dates.
  *Source: Batch 4; Inventory #16.* **Owner:** Standards PM.
  **Automation:** repo can insert owner table after assignments.
  **⚠️ Gap:** Need roadmap review outcomes.
  **[2025-10-01 Pending Owner Matrix]** Owner assignments awaiting roadmap review sign-off.

* [ ] Capture Node-RED roadmap gaps (offline bundles, diff UX v2) with status and mitigation in
  `docs/roadmaps/Node-RED_roadmap.md`.
  *Source: Batch 5.* **Owner:** Node-RED working group. **Automation:** repo update once mitigation
  plan drafted.
  **[2025-10-01 Pending Mitigation Plan]** Node-RED group still drafting mitigation.
  Roadmap gaps stay placeholders until that plan lands.

* [ ] Document the strict-mode/deprecation rollout for dangerous or test-only flags and exit codes in
  `docs/operations/test_flag_safety_policy.md` and `docs/standards/exit_code_stability_policy.md`, linking
  to future ADR updates.
  *Source: Batch 6; Inventory #25.* **Owner:** Ops governance.
  **Automation:** repo can sync docs after policy is ratified.
  **Dependency:** ADR coverage for rollout timeline.
  **[2025-10-01 Pending Policy Draft]** Strict-mode rollout ADR and policy updates still in development.

* [ ] Deduplicate ACL and redaction guidance inside `docs/agents/events.md`, pointing to the canonical
  security section once.
  *Source: Batch 7; Inventory #28.* **Owner:** Security doc owner. **Automation:** repo ready after
  target section identified.
  **[2025-10-01 Pending Canonical Section]** Waiting on security owner decision.
  Canonical ACL/redaction section not yet selected.

* [ ] Populate `docs/operations/known_issues_tracker.md` with active issues or document the intake workflow
  so operators can rely on it.
  *Source: Batch 7; Inventory #29.* **Owner:** Operations PM.
  **Automation:** repo can update doc after workflow draft approved.
  **⚠️ Gap:** Need triage process definition.
  **[2025-10-01 Pending Workflow]** Ops PM still drafting the intake workflow.
  Issues backlog population remains in progress.

### Documentation Integrity & Tooling (Phase: Docs)

* [x] Tune future inventory runs to exclude transient `.repo_studios/health_suite` artifacts,
  updating the configuration referenced in `.repo_studios/docs_inventory.md`.
  *Source: Inventory #1.* **Owner:** Documentation tooling.
  **Automation:** repo-safe once filtering rules are approved.
  **✅ Outcome (2025-10-02):** Baseline filter captured in `docs_inventory_config.yaml`; health-suite
  outputs now excluded and follow-up additions tracked in `docs_inventory_notes.md`.

* [ ] Review residual payloads under `models/` and `ledger_tmp/`, archiving or deleting non-doc files
  per `docs/repo/artifact_policy.md`.
  *Source: Inventory #2.* **Owner:** Repository stewardship.
  **Automation:** repo can assist after owner confirms disposition.
  **Dependency:** Inventory sweep sign-off.

* [ ] Pre-tag `docs/ci_fault_owner_signals.md`, `docs/memory/*`, and `memory-bank/*` in the next parsing
  bundle configuration so Batch 10 sequencing stays predictable.
  *Source: Inventory #3.* **Owner:** Documentation pipeline.
  **Automation:** repo-ready YAML update once bundle template is unlocked.

* [ ] Define and record a retention policy for `.repo_clean_log/` outputs to prevent unbounded growth.
  *Source: Inventory #4.* **Owner:** Tooling governance. **Automation:** repo to note policy after
  governance approves retention length.

* [ ] Populate `maintenance_plan.md` with actual owner names and update the cadence matrix accordingly.
  *Source: Batch 9; Inventory #34.* **Owner:** Maintenance lead *(human data).* **Automation:** repo
  doc edit once roster is finalized.

* [ ] Implement `scripts/verify_docs_integrity.py` (or equivalent) in CI, documenting enforcement inside
  `README.md` and `docs/standards/documentation.md`, including the content-hash gating timeline.
  *Source: Batch 9; Inventory #35.* **Owner:** CI tooling team.
  **Automation:** repo can add doc mentions after script lands.
  **⚠️ Gap:** Need CI wiring plan.

* [ ] Update `repo_rollout_targets.md` status checkboxes with evidence from recent faulthandler runs,
  linking artifacts for traceability.
  *Source: Batch 1; Inventory #36.* **Owner:** Diagnostics owner.
  **Automation:** repo to mark checklist once evidence gathered.

* [ ] Automate regeneration of `mypy_agents_full.txt` and `mypy_monitoring_full.txt` (Make target or
  scheduled job) and note cadence within the files.
  *Source: Batch 9; Inventory #37.* **Owner:** Typing gate maintainers.
  **Automation:** repo can document cadence after automation path decided.

* [ ] Schedule new Chainlit screenshots in `docs/demo_ui_snapshot.md` once Phase 4 UI stabilises, keeping
  visuals current.
  *Source: Batch 2.* **Owner:** UI guild. **Automation:** repo can stage doc update after new captures
  delivered.

* [ ] Record the README integrity roadmap—content-hash enforcement plus integrity scripts—by adding milestones
  to `README.md` and `docs/standards/documentation.md`.
  *Source: Batch 9.* **Owner:** Docs governance. **Automation:** repo to add milestones once roadmap
  timeline is approved.

## ✳ Phase In Progress: Memory & RAG — (2025-10-01 21:45 UTC)

* Docs updated: `docs/endpoint_ttl_registry.md`, `docs/memory/staleness_policy.md`,
  `docs/agents/rag_standards.md`, `docs/api/orchestrator_promql.md`, `docs/api/rag_status.md`,
  `docs/api/orchestrator_alerts.md`, `docs/extending/warmers.md`, `memory-bank/activeContext.md`,
  `memory-bank/progress.md`.
* Pending decisions / owner sign-offs: cadence ratification (Memory + Cache leads), Prometheus rule
  deployment (`rag-refresh.rules.yml`), `register_warmer` helper merge, `/rag/status` runbook dry run.
* Next micro-steps: wire alert rules into monitoring repo, surface cadence decision in detector
  config, track warmer helper implementation PR, schedule on-call tabletop using updated playbook.
