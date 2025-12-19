---
title: HealthView HOP Implementation Plan
tier: tier-2
audience:
  - coding_agent
  - human_developer
owners:
  - repo_studios_team@rainmakerprotocol.dev
role:
  - implementation-plan
status: draft
version: 0.1.0
updated_at: 2025-12-18
tags:
  - pipeline
  - healthview
  - hop
  - implementation
  - refactor
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/tier1_healthview_orchestration_pipeline.md
  - .repo_studios/docs/pipeline/healthview_orchestrastion_pipeline/hop_alignment.md
  - .repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_template.md
  - .github/instructions/markdown.instructions.md
  - .github/instructions/pipeline_doc_tiers.instructions.md
  - .github/instructions/tier_doc_operating_model.instructions.md
  - REPORT_NAMING_STANDARDS.md
---

<!-- markdownlint-disable-next-line MD025 -->
# HealthView HOP Implementation Plan

> **Purpose:** This Tier-2 document converts the HealthView HOP alignment decisions into an executable,
> checklist-driven plan (docs first, then code). It is the authoritative replacement for
> `hop_alignment.md`.
>
> See `.github/instructions/markdown.instructions.md` (reviewed 2025-12-18) and
> `.github/instructions/pipeline_doc_tiers.instructions.md` (reviewed 2025-12-18).

---

## 0. Instruction Block for Editors & AI Assistants

* This is a **Tier-2** implementation plan that inherits the stage ordering and terminology from
  `tier1_healthview_orchestration_pipeline.md`.
* Keep the canonical section order intact (Goals → System Context → Stage Narratives →
  Signals & Telemetry → Dependencies & Stop-Gates → Instruction Block → Agent Automation →
  Update Log).
* This doc must stay **checklist-driven** and **decision-backed**:
  * Put only stable decisions under “HOP Decisions (Locked)”.
  * Record uncertainties as explicit checkboxes with an owner and exit criteria.
* Do not add inline transcripts or “Answer captured” prose; preserve history via git.
* After meaningful edits (especially checkbox changes), rerun `make doc-index` and record the
  timestamp in the Update Log.
* Implementation phase sequencing is intentional:
  * First: Tier-1 sanity + contradiction pass (harden Tier-1 Sections 1–3).
  * Then: author Tier-2 verticals (starting Stage 1.1) and only later begin code migrations.

---

## 1. Goals & Success Criteria

1. Establish a single, reviewable implementation plan for HealthView HOP hardening.
2. Convert the agreed alignment decisions into enforceable checklists and stop-gates.
3. Drive a deterministic work order:
  Tier-1 sanity (Sections 1–3) → Stage 1.1 Tier-2 vertical hardening → remaining Tier-2 seeding →
  later code migrations.

**Success criteria:**

* `hop_alignment.md` is no longer the active planning surface; it points to this doc.
* This document contains:
  * Locked decisions, open stop-gates, and the ordered workstreams.
  * A clear “definition of done” checklist for future per-script migrations.
* The next Tier-2 vertical document for **Stage 1.1: Test Execution Telemetry** can be drafted
  without re-litigating naming, retention, telemetry, or overlap policies.

---

## 2. System Context

### 2.1 Tier Alignment

* **Tier-1 Spine:** `tier1_healthview_orchestration_pipeline.md`
* **Primary scope:** HealthView orchestration pipeline refactor/hardening planning.
* **Non-goals (this doc):** code changes, new viewer UX, or retrofitting CommandView in full.

### 2.2 HOP Decisions (Locked)

These decisions are treated as “stop-gates resolved” and should not be reopened without updating the
Tier-1 contradiction registry.

* **HealthView canonical output root:** `.repo_studios/reports/healthview/<class>/<topic>/<timestamp>/`
* **Bundle shape:** exactly `manifest.json`, `summary.md`, `telemetry.json` per run.
* **No mutable pointers:** do not create `latest_*`, `current_*`, or similar aliases.
* **Retention default:** history mode with `keep=5` unless explicitly justified as overwrite.
* **DB toggle standard:** `REPO_STUDIOS_DB_ENABLED`.
* **DB error behavior:** failures logged at `WARNING`; DB writes are best-effort and do not block
  filesystem artifact writing.
* **DB callsite markers:** every persistence callsite must include `DB_INTEGRATION_MARKER:` directly
  above it.
* **Cross-view overlap policy:** add HealthView outputs only when a CommandView script is part of a
  HealthView orchestrator dependency chain; do not change legacy CommandView output locations.
* **Telemetry baseline:** accept `items_total` as the universal primary count (for now) with
  script-specific details under `extra`.
* **Registry preference:** machine-first registry format (YAML), HealthView-only first.
* **Chain hardening order:** start at the first orchestrator listed after meta-orchestrator:
  **Stage 1.1: Test Execution Telemetry**.
* **Adapter policy:** prefer one-shot migrations; allow time-boxed adapters only with an explicit
  removal checklist captured in the relevant Tier-2 vertical.
* **Manifest schema posture:** strict baseline keys required; extras allowed and encouraged.

### 2.3 Implementation Considerations (From Recent Alignment)

These items are not new decisions, but they are critical constraints that shaped the plan.

* **Producer vs helper classification:** if a module is a helper (not a CLI entry point), standardize
  the consuming producer/orchestrator rather than forcing the helper to emit bundles.
* **Bundle discipline:** each run produces exactly three artifacts and no extra per-run files.
* **Pruning discipline:** pruning must use shared helpers and must protect `current_run`.
* **DB discipline:** DB writes are best-effort and must never block filesystem artifact creation.
* **Top-down hardening order:** this pass starts at a chain owner (Stage 1.1 orchestrator) and walks
  down dependencies rather than refactoring producers in isolation.
* **Adapters are exceptions:** prefer one-shot migrations; allow a time-boxed adapter only when
  blocked, with an explicit removal checklist in the Tier-2 vertical.
* **Tier-2 promotion bar:** a Tier-2 vertical is “authoritative” only after it has (at minimum)
  Goals + System Context + Stage Narratives, an inputs/outputs inventory, stop-gates/checklists,
  and an Update Log row with doc-index evidence + regression suites.

### 2.4 Known Contradictions / Reconciliation Targets

* Tier-1 currently describes HealthView output roots under `.repo_studios/command_center/reports/...`.
  This must be reconciled with the locked decision above (class-scoped `.repo_studios/reports/...`).

---

## 3. Stage Narratives (Workstreams)

### 3.A Workstream A — Convert Alignment → Implementation Surface

* **Scope:** Make `hop_implementation.md` the single source of truth for the HOP execution plan.
* **Evidence:** This doc, the Tier-2 template, and the historical `hop_alignment.md`.
* **Status:** Complete

Implementation checkpoints:

* [x] Create `hop_implementation.md` as a Tier-2, template-compliant implementation plan.
* [x] Convert `hop_alignment.md` into a non-authoritative redirect + short decision summary.
* [x] Confirm both docs have correct front matter + single H1.

### 3.B Workstream B — Tier-1 Sanity + Contradiction Pass (Sections 1–3)

* **Scope:** Update the Tier-1 doc’s global narrative (Sections 1–3) so it is internally consistent
  and aligned with the locked HOP decisions, then log contradictions/stop-gates explicitly.
* **Evidence:** `tier1_healthview_orchestration_pipeline.md` and its Contradiction Registry.
* **Status:** TODO

Implementation checkpoints:

* [x] Harden Tier-1 Sections 1–3 to remove ambiguity about:
  * output roots and discovery
  * bundle invariants (3 artifacts, no pointers)
  * retention default (keep=5)
  * best-effort DB dual-write semantics
* [x] Update the Tier-1 contradiction registry with any intentional mismatches (for example, if the
  Tier-1 output-root narrative must lag the new canonical root temporarily).
* [x] Sanity-check that Tier-1 Sections 3.4–3.7 (spine/envelope/controls/guarantees) match the locked
  decisions listed in this doc.
* [x] Record evidence in the Tier-1 Update Log (doc-index timestamp + regression suites).

### 3.C Workstream C — Extract Stage 1.1 Definition Into Tier-2 Vertical

* **Scope:** Use the Tier-1 Stage 1.1 section as the authoritative source for chain inventory (for
  now), then translate it into a Tier-2 vertical with inspection tables and stop-gates.
* **Evidence:** Tier-1 stage text + Stage 1.1 orchestrator code and tests (later).
* **Status:** TODO

Implementation checkpoints:

* [ ] Create the Stage 1.1 Tier-2 doc using the Tier-2 template, including:
  * chain dependency list (orchestrator → summarizer/aggregator/consumer → producers)
  * inputs/outputs inventory (current state + target canonical state)
  * per-script inspection table (v1)
  * adapter exception removal checklist template
  * Tier-3 dependency placeholders for shared horizontals

### 3.D Workstream D — Seed Remaining Tier-2 Verticals (Tier-1 Order)

* **Scope:** Create placeholder Tier-2 docs for the remaining HealthView stages in Tier-1 order.
* **Evidence:** Tier-1 stage list and the Stage 1.1 Tier-2 format.
* **Status:** TODO

Implementation checkpoints:

* [ ] Create one Tier-2 stub per stage with consistent headings, stop-gates, and update log.
* [ ] Add explicit TODO checklists for “inventory chain”, “confirm output root”, and “validate gates”.

### 3.E Workstream E — Convert Tier-2 Docs → Execution Checklists (Later Code Phase)

* **Scope:** Turn doc checklists into code-level implementation work that can be executed per chain.
* **Evidence:** Stage 1.1 Tier-2 vertical doc and validated scripts.
* **Status:** TODO

Implementation checkpoints:

* [ ] Define the per-script “definition of done” checklist used by every migration.
* [ ] Add “doc-index + regression suite” evidence requirements per completed script.

---

## 4. Signals & Telemetry

**When code work begins, each chain migration must record evidence for at least:**

* **Regression suites:** `pytest` (targeted), `mypy` (touched scripts), and coverage when applicable.
* **Artifact inspection:** verify the three artifacts exist and no pointer files are created.
* **Retention verification:** confirm pruning mode keeps `current_run` and honors `keep=5` default.
* **DB marker audit:** verify `DB_INTEGRATION_MARKER:` presence at each persistence callsite.
* **Doc evidence:** rerun `make doc-index` and log the timestamp in the Update Log.

---

## 5. Dependencies & Stop-Gates

* **Tier-1 stop-gates blocked by this doc:**
  * Tier-1 reconciliation (output root and retention narrative must match locked decisions).

* **Tier-3 horizontals required (placeholders until created):**
  * `tier3_cli` (shared CLI config builders)
  * `tier3_prune_logs` (retention + current_run protection)
  * `tier3_database_integration` (DB facade + dual-write patterns)
  * `tier3_artifacts` (bundle shape + discovery semantics)
  * `tier3_healthview_registry` (machine-first YAML registry, HealthView-only)

---

## 6. Instruction Block (Required by Tier Rules)

1. Editors must follow `.github/instructions/markdown.instructions.md` and
   `.github/instructions/pipeline_doc_tiers.instructions.md`.
2. Keep this doc’s section order intact; add new content under the existing headings.
3. Every time you change checkboxes, refresh the doc-index (`make doc-index`) and record the
   timestamp in the Update Log.
4. When reusable semantics emerge (pruning policy, DB schema, artifact naming), capture them as Tier-3
   horizontals (or add explicit placeholders here) and link them from the relevant Tier-2 vertical.
5. Before marking any workstream “Complete”, run the relevant regression suites and record the
   evidence in the Update Log.

---

## 7. Agent Automation Block

<!-- agents:begin:healthview_hop_implementation -->
```yaml
audience: [Copilot, Repo_Studios]
intent: planning
rules:
  - require_front_matter: true
  - require_single_h1: true
  - no_inline_chat_transcripts: true
  - require_language_fences: true
  - require_update_log: true
next_actions:
  - id: hop-impl-001
    title: Ensure hop_alignment redirects to hop_implementation
    exit_criteria:
      - hop_alignment_is_redirect: true
  - id: hop-impl-002
    title: Draft Stage 1.1 Tier-2 vertical doc using locked decisions
    exit_criteria:
      - stage_1_1_tier2_doc_created: true
      - tier3_placeholders_listed: true
  - id: hop-impl-003
    title: Regenerate doc-index after checklist edits
    command_hint: make doc-index
```
<!-- agents:end:healthview_hop_implementation -->

---

## 8. Update Log

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-19 | Fixed Tier-1 placeholder/evidence links to satisfy targeted anchor validation for HealthView pipeline docs. | repo_studios_ai | 20251219-0124 | markdown anchor validation (bundle 20251219-0123) |
| 2025-12-18 | Created implementation plan (authoritative replacement for hop_alignment). | repo_studios_ai | Not run. | None |
| 2025-12-18 | Completed Workstream B checkpoint: hardened Tier-1 Sections 1–3 and populated Tier-1 Contradiction Registry entries (current vs target contract). | repo_studios_ai | 20251218-2328 | Doc-index producer; markdown anchor validation (bundle 20251218-2337) |
