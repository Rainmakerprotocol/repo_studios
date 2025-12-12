---
title: "Tier-3 Horizontal Document Template"
tier: tier-3
audience:
  - <update-with-primary-audience>
owners:
  - <update-with-owner>
role:
  - tier-3-horizontal-template
status: template
version: v0.1.0
updated_at: 2025-12-11
tags:
  - pipeline
  - tier-3
  - template
related_files:
  - .repo_studios/docs/pipeline/pipeline_templates/tier1_pipeline_template.md
  - .repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_template.md
  - <pending_progress>
---

<!-- markdownlint-disable-next-line MD025 -->
# Tier-3 Horizontal Document Template

> **Purpose:** Copy this file when authoring a Tier-3 horizontal (safety envelopes, autonomy guardrails, telemetry horizontals, transport contracts, rollback semantics, etc.). Replace every placeholder, cite concrete evidence, and follow `.github/instructions/markdown.instructions.md`, `.github/instructions/pipeline_doc_tiers.instructions.md`, and `.github/instructions/tier_doc_operating_model.instructions.md` before submitting changes.

---

## 0. Instruction Block for Editors & AI Assistants

* Tier-3 docs define **reusable semantics**; do not embed implementation specifics that belong in Tier-2.
* List every Tier-2/Tier-1 document that *consumes* this horizontal and keep reciprocity: dependents must link back here.
* Preserve this section order (Goals → System Context → Horizontal Contracts → Signals & Telemetry → Dependencies → Agent Block → Update Log). Add custom subsections under the provided headings only.
* Every checklist entry must cite evidence (files/tests/docs) *and* call out doc-index obligations ("refresh doc-index after completing this box").
* Record doc-index timestamps, regression suites, and cross-tier sync status in the Update Log whenever this file changes.
* When introducing a new reusable concept, refresh the doc-index (via the `doc-index` make target or platform-equivalent command).
* If this horizontal affects telemetry/history/propagation, reference the relevant implementation files and note which Tier-1 stop-gates are blocked.

Add domain-specific editing notes here (for example, "voice transports must cite limiter telemetry files").

---

## 1. Mission & Goals

Explain **why** this horizontal exists and which problems it solves. Provide 3–5 concrete goals tied to adoption evidence.

1. `<Goal statement #1 – e.g., unify limiter telemetry semantics across transports>`
2. `<Goal statement #2 – e.g., guarantee autonomy maturity gates>`
3. `<Goal statement #3 – e.g., enforce rollback audit trails>`

Add success criteria (Tier-1 checkbox flips, telemetry parity proof, governance acceptance, etc.).

---

## 2. System Context & Scope

### 2.1 Audience & Consumers

* **Primary Consumers (Tier-2/Tier-1):** `<List docs + sections>`
* **Runtime Surfaces:** `<Brief bullets describing APIs/services affected>`
* **Out-of-Scope:** `<Call out items intentionally excluded>`

### 2.2 Architectural Anchors

Describe the systems, data stores, and telemetry feeds that provide the evidence for this horizontal. Link to code/tests/ADRs.

### 2.3 Preconditions & Assumptions

* `<Assumption #1>`
* `<Assumption #2>`
* `<Assumption #3>`

---

## 3. Horizontal Contracts & Adoption State

Use the subsections below to articulate the reusable logic this Tier-3 doc owns. Duplicate/rename subsections as needed (taxonomies, maturity models, contract tables, matrices, etc.).

### 3.1 Canonical Contract / Taxonomy

Describe the contract, maturity ladder, taxonomy, or semantic rules. Use tables where useful.

| Dimension | Requirement | Evidence | Notes |
| --- | --- | --- | --- |
| `<Example: Script Validation>` | `<Rule>` | `.repo_studios/scripts/...` | `<Doc/Test link>` |

### 3.2 Adoption Matrix

Summarize how each dependent transport/stage/adaptor complies with the contract.

| Dependent | Status | Evidence | Outstanding Gaps |
| --- | --- | --- | --- |
| `<Stage or transport>` | `Complete/Partial/TODO` | `tests/...` | `<Gap>` |

### 3.3 Implementation Checkpoints

Use actionable checklists; keep them close to the relevant subsection rather than in a single blob.

* [ ] `<Checkpoint with evidence + "run make doc-index" reminder>`
* [ ] `<Checkpoint referencing regression suite>`
* [ ] `<Checkpoint citing Tier-1 sync requirement>`

Include additional subsections (for example, **Safety Envelope Rules**, **Autonomy Maturity Levels**, **Rollback Semantics**) as the horizontal demands.

---

## 4. Signals, Telemetry & Validation

* **Regression Suites:**
  * `pytest -q <path>` – `<behavior validated>`
  * `<Add suites or smoke harnesses>`
* **Telemetry / Metrics:** Describe metrics, dashboards, and how they prove compliance.
* **Manual Harnesses:** CLI scripts or smoke drivers that validate the contract.
* **Doc-index & Checkbox Evidence:** Note the latest doc-index timestamp (from running the `doc-index` make target or platform-equivalent) and mention if the checkbox report entries were updated.

Note any verification gaps or TODOs if telemetry coverage is incomplete.

---

## 5. Dependencies, Reciprocal Links & Stop-Gates

### 5.1 Dependent Documents & Sections

List every Tier-1/Tier-2/TEMP doc relying on this horizontal, with anchors.

* `<Doc path + section>` — `<Dependency description>`
* `<Another doc>` — `<How this Tier-3 doc blocks it>`

### 5.2 Required Follow-Ups

* `<Describe Tier-1/Tier-2 sync that must happen before considering this contract stable>`
* `<List feature flags, rollout gates, governance approvals>`

### 5.3 Placeholder Tracking

Document any related Tier-3 placeholders (for example, future horizontals) and the plan to author them.

---

## 6. Agent Automation Block

<!-- agents:begin:tier3-template -->
```yaml
audience: [Copilot, Repo_Studios]
tasks:
  - id: tier3-section-order
    title: Maintain Tier-3 canonical section order
    severity: error
  - id: reciprocal-links
    title: Verify dependent Tier-1/Tier-2 docs are listed with anchors
    severity: error
  - id: checklist-evidence
    title: Ensure every checklist cites evidence + doc-index reminder
    severity: warn
  - id: doc-index-log
    title: Require latest doc-index timestamp in Update Log
    severity: warn
```
<!-- agents:end:tier3-template -->

---

## 7. Update Log & Evidence Tracking

Record every change, including doc-index timestamps and regression suites. Do not mark Tier-1/Tier-2 stop-gates complete without logging the evidence here.

| Date | Change | Author | Doc-index timestamp | Regression suites / telemetry |
| --- | --- | --- | --- | --- |
| 2025-12-11 | Template created | Copilot | `<YYYY-MM-DDTHH:MM:SSZ>` | ``pytest -q ...`` |
| YYYY-MM-DD | `<Describe change>` | `<Name>` | `<timestamp>` | ``pytest -q tests/...`` |

Add rows for subsequent edits.
