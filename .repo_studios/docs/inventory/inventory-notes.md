---
title: Documentation Inventory Notes
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_ai
status: draft
version: 0.2.0
updated: 2025-10-18
summary: >-
  Field notes capturing findings, action items, concerns, and gaps from the latest Repo Studios documentation inventory sweep.
tags:
  - inventory
  - notes
legacy_source: .repo_studios_legacy/repo_docs/docs_inventory_notes.md
---

<!-- markdownlint-disable MD025 -->
# Documentation Inventory Notes

Date: 2025-10-01 | Status: Draft | Phase: Discovery

These notes summarize the October 2025 sweep across Repo Studios documentation surfaces, highlighting scope metrics, detailed observations, prioritized action items, and follow-on investigations.

---

## Summary Metrics

- Inventory includes 2,738 documentation artifacts in scope.
- Exclusions cover `external/`, `src/`, `libraries/`, and any `logs` directories.
- Oldest doc: `models/whisper/voice_input.wav.txt` (2025-07-18).
- Newest doc: `.repo_studios/docs_inventory.md` (2025-10-01).
- Total footprint is about 1.27 GiB across Markdown, text, notebooks, and JSON content.
- `.repo_studios/` contributes roughly 84% of entries.

## Observations

- `.repo_studios/health_suite/` runs create many status artifacts with limited long-term value.
- `docs/` (170 files) and `mrp/` (93 files) appear current through September 2025.
- `memory-bank/` governance content covers 31 focused items for review.
- Voice subsystem docs document latency, queue smoothing, prompt policy, and feature flags; all align with offline-first design but require metric verification.
- `artifacts/` and `.github/` still anchor historical tracking data.
- Operator quickstart and fault owner signal docs give measurable escalation paths but still cite legacy pager IDs needing roster review.
- TTL registry refresh windows and memory staleness policy disagree, signalling a pending decision on authoritative cadence.
- Architecture and cache migration docs confirm cache facade sunset yet leave feature flag naming placeholders to verify.
- RAG standards outline embed refresh cadence without a matching Prometheus metric.
- Agents Step 3-5 plans and the agent frameworks guide document ready scaffolds with flags, metrics, and MRP integration complementing orchestrator work.
- Service manifest spec proposes a declarative rollout contract but lacks validator or schema enforcement tooling.
- Voice conversation and privacy policies reiterate offline-first expectations and retention controls that should align with chat logging guidance.
- Monitoring overview, repo insight workflow, and startup runbook describe troubleshooting flows that can feed the alignment ledger audit trail.
- Orchestrator overview plus perf/cache/memory/voice deep dives connect readiness probes, cache TTL validation, and memory health instrumentation behind recent Make targets.
- Node-RED, micro-agent, monitoring, and AI standards roadmaps supply governance docs that depend on pending follow-ups (offline bundles, build scripts, rollout metrics).
- Service management addendum extends readiness orchestration with new flags and registries yet remains unsynced with base phase documentation.
- ADR set (0001-0009) codifies streaming policy, cache segmentation, diagnostics decomposition, event bus primacy, and dynamic agent imports; ADR 0008 still needs rationale and consequence sections.
- Metrics schema v4, phase histogram design, lifecycle events, and doc templates formalize data contracts and documentation structure but require matching alerts and template adoption.
- Core standards set (glossary, coding, testing, documentation, file tree) clusters with lifecycle versioning and additive observability policies, giving a single governance surface for naming, drift guards, and change control.
- Voice orchestration docs (contract suite, intent router, meeting mode, quickstart) consolidate flag behavior, privacy guardrails, and CI contract coverage for conversation/meeting rollouts.
- Operations playbooks (flag matrix, restart policy, shutdown guide, test flag safety, exit code stability) define lifecycle supervision but still depend on unimplemented flags and deprecation sequencing.
- RAG endpoints and MRP README pair runtime observability with refresh operations, yet monitoring docs lack matching alerts; warmers extension remains conceptual without registry helper wiring.
- Batch 7 (docs 126-150) confirms lifecycle instrumentation is widely documented: UI memory widget guidance matches Chainlit standards, service management plan mirrors recent code progress, and logging/restart policies align with lifecycle metrics and debug artifacts. Several docs still flag pending automation (startup benchmarks, debug dumps, systemd manifest).
- Events guide repeats ACL/redaction sections; consolidating the guidance would simplify maintenance while keeping security advice authoritative.
- Known issues tracker, observability roadmap, and systemd inventory governance are in scaffold mode; each calls for operational follow-up (issue intake, roadmap execution, manifest checks).
- Systemd inventory and security profile drafts couple classification heuristics with directive severity enforcement but hinge on validators pending implementation.
- Watchdog rollout recommendations lay out metrics, staged rollout, and shim retirement gates that depend on new instrumentation and python-systemd availability.
- Root-level docs (README, release notes, maintenance plan, retros) provide governance anchors but still depend on integrity tooling, owner assignments, and metrics alerts to close the loop.

## Action Items

1. Limit future inventories by excluding generated `.repo_studios/` artifacts when appropriate; baseline filter now captured in `docs_inventory_config.yaml` to drop health-suite outputs.
2. Review residual docs in `models/` and `ledger_tmp/`; archive or drop non-doc payloads.
3. Tag `docs/ci_fault_owner_signals.md`, `docs/memory/*`, and `memory-bank/*` for the next parsing slice.
4. Define a retention policy for `.repo_clean_log` entries created by automated runs.
5. Update `memory-bank/activeContext.md` and `memory-bank/progress.md` once the alignment ledger cycle supersedes cache TTL work statements.
6. Confirm monitoring dashboards expose `/metrics/voice` counters to close the loop with voice latency and collapse docs.
7. Revisit `docs/ui/bench_ui_pre_commit.md` against current Chainlit widget standards and plan revisions if hashing guidance shifted.
8. Validate faulthandler blocklist/allowlist artifacts against `repo_rollout_targets.md` milestones ahead of the mid-term review.
9. Reconcile operator quickstart pager IDs and fault owner signals with the current on-call roster and escalation sequence.
10. Decide on a unified refresh cadence satisfying TTL registry windows and the memory staleness policy, then document it.
11. Verify cache migration feature flag names and update the artifact policy with hybrid storage retention thresholds.
12. Draft a Prometheus recording rule for memory embed refresh to close the gap in the RAG standards observability section.
13. Stand up service manifest validation tooling (schema plus CLI) before treating the spec as authoritative for deployments.
14. Align chat logging retention knobs with voice logging policy to keep rotation and privacy guidance consistent.
15. Document RAG status alerting guidance in monitoring docs so staleness signals are actionable.
16. Track AI standards roadmap deliverables (schema, build script, CLI) and note missing artifacts for follow-up.
17. Merge the service management addendum back into the base Step 6 doc and plan verification tests for the new readiness metrics and shutdown snapshot features.
18. Finish ADR 0008 sections (rationale, consequences, observability, rollback) so deprecation policy is actionable, updating `docs/decisions.md` accordingly.
19. Expand the scale-out systemd roadmap with concrete acceptance criteria, owners, and a flag rollout plan before scheduling multi-node work.
20. Capture monitoring alert rules or PromQL snippets for metrics introduced in `docs/metrics_schema.md` and `docs/metrics/phase_histogram_design.md` to close observability gaps.
21. Flesh out the warmers extension guide with concrete registry helper usage, timeout defaults, and metric hooks tied to lifecycle metrics tests.
22. Implement lifecycle/additive observability drift guard enforcement (hash snapshots plus CI) and document the guard location once active.
23. Define supervisor restart environment knobs (`SUP_RESTART_*`), assign ownership, and add acceptance tests so the restart policy is actionable.
24. Add monitoring roadmap entries for `/rag/status` thresholds and `X-RAG-*` header sampling, then publish alert snippets in lifecycle metrics inventory.
25. Outline a strict-mode/deprecation rollout for dangerous or test-only flags and exit codes, referencing updates in `docs/decisions.md` and exit code policy.
26. Verify lifecycle metrics emitted by the orchestrator match documented names/labels and land in `/metrics`; add targeted tests or doc updates if mismatches surface.
27. Assign ownership for lifecycle startup benchmark automation (cold versus warm segregation, histogram guide) and tie deliverables to the observability roadmap.
28. Deduplicate ACL/redaction guidance in `docs/agents/events.md` to keep the security section single-sourced.
29. Expand `docs/operations/known_issues_tracker.md` with current issues or document the intake workflow so the tracker becomes actionable.
30. Implement the planned systemd inventory integrity manifest and drift check target before promoting to blocking enforcement.
31. Wire startup debug dump generation into the orchestrator (flag plus automatic failure capture) and ship the diff helper script promised in the artifact spec.
32. Implement watchdog counters/gauges plus baseline PromQL alerts per `docs/ops/watchdog_recommendations.md`, ensuring metrics land in `/metrics` before rollout.
33. Finish the systemd inventory and security validator tooling, hook it into CI, and report on severity tallies so directive enforcement moves from draft to blocking.
34. Replace placeholder owner identifiers in `maintenance_plan.md` with the active rotation and document the cadence review workflow.
35. Wire the documentation integrity verifier (`scripts/verify_docs_integrity.py`) into CI and update README or standards once enforcement is active.
36. Update `repo_rollout_targets.md` status checkboxes using the latest faulthandler artifact runs and link to evidence.
37. Add an automated refresh (Make target or scheduled job) for `mypy_agents_full.txt` and `mypy_monitoring_full.txt` so typing baselines stay current and documented.

## Concerns

- Instruction-heavy logs may mask strategic docs unless filtered.
- Each inventory run writes new `.txt` summaries, expanding scope without guardrails.
- Large `.ipynb` notebooks in `docs/` could inflate parsing cost; pre-rendering may help.

## Gaps to Investigate

- No consolidated index ties `docs/` and `.repo_studios/` yet, so cross-linking remains undefined.
- Retention or archival policy is undocumented, especially for generated health-suite outputs.
- Owner metadata is missing; filenames alone do not show stewardship.

## Next Steps

- Use the CSV inventory as the machine-parsable source for downstream bundling.
- Draft a filtering configuration (YAML or JSON) mapping directories and files to each analysis bundle.
- Prepare a follow-up report after proposing the bundling taxonomy; keep updates in this notes file.

<!-- markdownlint-enable MD025 -->
