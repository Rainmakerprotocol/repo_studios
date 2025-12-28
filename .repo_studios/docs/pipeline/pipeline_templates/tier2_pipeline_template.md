---
title: "Tier-2 Pipeline Document Template"
tier: tier-2
audience:
  - <update-with-primary-audience>
owners:
  - <update-with-owner>
role:
  - tier-2-vertical-template
status: template
version: v0.1.0
updated_at: 2025-12-11
tags:
  - pipeline
  - tier-2
  - template
related_files:
  - <pending_progress>
  - <pending_progress>
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-2 Pipeline Document Template

> **Purpose:** Copy this file when authoring a new Tier-2 vertical. Replace every
> bracketed placeholder, cite real evidence, and follow
> `.github/instructions/markdown.instructions.md` plus
> `.github/instructions/pipeline_doc_tiers.instructions.md` before submitting changes.

---

## 0. Instruction Block for Editors & AI Assistants

- Declare explicitly which Tier-1 stage this document inherits.
- Keep the section order defined in the Tier rules (Goals → System Context → Stage
  Narratives → Signals & Telemetry → Dependencies → Agent Instructions → Update Log).
- Every checklist item must cite evidence (code/tests/docs) and include doc-index + test
  obligations (for example, "run checkbox report generator after checking this box").
- Surface Tier-3 dependencies whenever the stage leans on a reusable horizontal; add
  placeholders if the Tier-3 doc does not exist yet.
- Run checkbox report generator
  (`python .repo_studios/docs/pipeline/checkbox_report/checkbox_report.py --verbose`)
  after meaningful edits and capture the timestamp in the Update Log.
- Mention targeted test suites that must stay green before flipping Tier-1 stop-gates,
  and document how Tier-1 will be updated when this vertical's status changes (log the
  sync in the Update Log).

Add any stage-specific editing rules here.

---

## 1. Goals & Success Criteria

1. `<Goal statement #1 – describe the end state for this stage/vertical>`
1. `<Goal statement #2 – telemetry or guardrail objective>`
1. `<Goal statement #3 – documentation/automation requirement>`

Explain how success will be measured (for example, Tier-1 checkbox flips, telemetry
parity, coverage thresholds).

---

## 2. System Context

### 2.1 Tier Alignment

- **Tier-1 Stage:** `<Stage name + link>`
- **Tier-3 Dependencies:** `<List docs such as tier3_prune_logs.md, tier3_cli.md>`
  (cite shared library docs in `.repo_studios/command_center/scripts/libraries/` whenever
  library dependencies are referenced.)
- **Upstream Inputs:** `<Brief bullets describing what arrives from prior stages>`
- **Downstream Outputs:** `<What this stage hands off + consumers>`

### 2.2 Current Coverage Snapshot

| Path | Status | Notes |
| --- | --- | --- |
| HTTP / Primary | `TODO/Partial/Complete` | `<Evidence link + telemetry plan>` |
| WebSocket / Streaming | `TODO/Partial/Complete` | `<Evidence link + telemetry plan>` |
| Companion Voice / Secondary | `TODO/Partial/Complete` | `<Evidence link + telemetry plan>` |

Add other modalities as needed (batch, agents, cron, etc.).

### 2.3 Risks, Gaps, and Assumptions

- **Risks:** `<List of known risks with mitigation references>`
- **Gaps:** `<Outstanding work blocking Tier-1 closure>`
- **Assumptions:** `<What this Tier-2 doc relies on but does not implement>`

---

## 3. Workstreams or Stage Narratives

> Pick whichever structure fits best. Use "Workstream" when effort is organized by
> thematic threads (e.g., Inspector Adoption). Use "Stage X.Y" when the Tier-2 doc
> mirrors substages. Always include Scope, Evidence, Status, and a checklist.

### 3.A Workstream Template (copy per workstream)

- **Scope:** `<One-sentence summary of the workstream>`
- **Evidence:** `<Key files/tests/docs>`
- **Status:** `TODO | In Progress | Partial | Complete`

Implementation checkpoints:

- [ ] `<Action item with evidence + test/doc-index reminder>`
- [ ] `<Action item>`

### 3.B Stage Narrative Template (use if needed)

#### Stage `<Number/Letter>` — `<Name>`

- **Scope:** `<Systems touched>`
- **Evidence:** `<Files/tests>`
- **Status:** `TODO | In Progress | Partial | Complete`

Implementation checkpoints:

- [ ] `<Checkpoint referencing implementation detail>`
- [ ] `<Checkpoint>`

> **Reminder:** Keep Voice/CLI/agent parity noted explicitly if applicable. You can
> include subsections per transport like the Stage 2 transport doc does.

---

## 4. Signals & Telemetry

- **Regression Suites:**
  - `pytest -q <path>` (covers `<behavior>`)
  - `<Other suites>`
- **Telemetry Endpoints:** `/metrics`, `/metrics/model-selection`, `<custom endpoints>`
  (reference the matching telemetry hybrid plan when documenting these.)
- **Manual Harnesses / CLIs:** `python scripts/<tool>.py --flag`
- **Doc-Index / Checkbox Evidence:** `make doc-index` last run `<timestamp>`

Add guidance for how to validate instrumentation before marking any checklist item complete.

---

## 5. Dependencies & Stop-Gates

- **Tier-1 Stop-Gates Blocked by This Doc:** `<List Stage sections + bullets>`
- **Tier-3 YAML Files Required:** `<List tier3_<script_name>.yaml files or "None">`
  (Note: Tier-3 uses YAML format for agent tool calling)
- **Release / Feature Flags:** `<FLAG_NAME description>`

State the conditions required before Tier-1 checkboxes can flip (tests, telemetry parity,
documentation, approvals).

> **Tier-1 Sync Reminder:** When this Tier-2 document changes status, update the
> corresponding Tier-1 stage immediately and record the sync (with doc-index timestamp +
> regression suites) in the Update Log.

---

## 6. Instruction Block (Required by Tier Rules)

1. Editors must follow `.github/instructions/markdown.instructions.md` and
   `.github/instructions/pipeline_doc_tiers.instructions.md`.
1. Keep this template's section order intact; add custom subsections beneath the provided
   headings.
1. Every time you change checkboxes, refresh the doc-index (via the `doc-index` make
   target or platform-equivalent command) and note the timestamp in the Update Log.
1. When adding reusable semantics, also update/create the relevant Tier-3 doc and link
   it under Tier Alignment.
1. Before declaring a workstream complete, ensure targeted regression suites and
   telemetry probes have run.

Update or extend these instructions as the vertical matures.

---

## 7. Agent Automation Block

<!-- agents:begin:tier2-template -->
```yaml
audience: [Copilot, Repo_Studios]
tasks:
  - id: ensure-section-order
    title: Verify canonical Tier-2 section order
    severity: error
  - id: checklist-evidence-links
    title: Require evidence + doc-index reminder for each checklist item
    severity: warn
  - id: tier-alignment
    title: Confirm Tier-1 stage + Tier-3 dependencies are declared
    severity: error
  - id: doc-index-run
    title: Ensure Update Log records latest doc-index timestamp
    severity: warn
```
<!-- agents:end:tier2-template -->

---

## 8. Update Log

Record every Tier-2 edit here. For each row, rerun `make doc-index`, execute the
validating regression suites, and capture both artifacts so Tier-1 stop-gates have
traceable evidence.

| Date | Change | Author | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| 2025-12-11 | Template created | Copilot | `<YYYY-MM-DDTHH:MM:SSZ>` | ``pytest -q ...`` |
| YYYY-MM-DD | `<Describe change>` | `<Name>` | `<timestamp>` | ``pytest -q tests/...`` |
