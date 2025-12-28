# Tier‑1 Pipeline Document Template

> **Purpose:** This template defines a reusable Tier‑1 structure for documenting any
> pipeline in Repo Studios (command center, doc validation, report generation, analysis
> aggregation, etc.). Replace bracketed text and stage names with pipeline‑specific content.

---

## 0. Instruction Block for Editors & AI Assistants

- This document is **Tier‑1**: it describes **system‑level behavior**, not code internals.
- All statements must be **backed by repo evidence** (code, tests, ADRs, design docs).
- Structure (H2s/H3s) should be preserved; add/remove major sections deliberately, then
  renumber **all** top-level headings (Stages, Snapshot, Contradiction Registry, etc.)
  so numbering stays contiguous.
- During Phase 0 seeding, create the blank **Update Log & Evidence Tracking** table
  before drafting stage content so evidence capture is ready from the first edit.
- Use the Working Notes section only as temporary scratch space; move resolved items
  into the Update Log once evidence (doc-index timestamp + regression suites) is recorded.
- When hardening, follow the **Pass A / Pass B / Pass C** evidence cycle per stage, as
  described in the how‑to guide, and log each doc-index run/regression suite in
  **Section <NN. Update Log & Evidence Tracking>**.
- Before calling any Tier‑1 edit complete, refresh the doc-index (via the `doc-index`
  make target or platform-equivalent command), execute the validating regression suites,
  and only then log the evidence in **Section <NN. Update Log & Evidence Tracking>**;
  that section is mandatory and should never be skipped.
- Editors must follow `.github/instructions/markdown.instructions.md` and `.github/instructions/pipeline_doc_tiers.instructions.md`.

You can optionally add pipeline‑specific notes here.

---

## 1. 5W1H – Purpose & Context

### 1.1 Who

- Primary stakeholders (teams, roles).  
- Secondary stakeholders (operators, users, AI agents).

### 1.2 What

- What this pipeline does at a high level.  
- What kinds of inputs it accepts and outputs it produces.

### 1.3 Why

- Why this pipeline exists and what problems it solves.  
- What guarantees or SLAs it’s meant to provide.

### 1.4 Where

- Where this pipeline lives in the architecture.  
- Which systems call into it and which systems depend on it.

### 1.5 When

- When the pipeline is invoked (triggers, schedules, events).  
- When it’s considered idle, active, degraded, or failed.

### 1.6 How

- A short description of how the pipeline runs from BEGIN → END.  
- Mention the stages by name, but keep details for the stage sections.

---

## 2. Document Metadata

- **Version:** `v0.1.0`  
- **Last Updated:** `YYYY‑MM‑DD`  
- **Owner / Steward:** `Team / Role`  
- **Overall Status:** `Draft | In Progress | Hardened | Frozen`

Optional: add a *Freeze Note* once the document is frozen.

---

## 3. Global Pipeline Overview

### 3.1 Narrative Summary

A short paragraph that describes the pipeline from input to output in plain language.

### 3.2 High‑Level Stage List

List your major stages in order. For example:

1. Stage 1 – `<Stage Name>`
1. Stage 2 – `<Stage Name>`
1. Stage 3 – `<Stage Name>`
1. …

The names here should match the H2 stage sections below.

---

## 3.3 How to Read This Template

- Start with Sections 1–3 for context and the global map.  
- Then read the stages in order from Stage 1 to the last Stage.  
- Use the Snapshot and Stage Matrix near the bottom to see status at a glance.  
- Use links to Tier‑2 docs/tests for implementation details.

---

## 3.4 Global Spine (Shared Backbone)

> Rename this to match your pipeline (e.g., “History & Retry Spine”, “Job Lifecycle Spine”).

Explain:

- What the spine is (e.g., shared event/logging/lifecycle backbone).  
- Which components participate (services, modules, logging subsystems).  
- How every request or event eventually passes through it.  
- Why downstream stages can assume its guarantees.  
- Evidence links (code, tests, docs).

---

## 3.5 Global Envelope (Shared Payload)

> Rename this to fit your pipeline (e.g., “Inference Envelope”, “Job Envelope”).

Explain:

- What the envelope contains (IDs, metadata, status, results).  
- Where it is first created/stamped.  
- How it is enriched at later stages (decisions, context, outputs).  
- How it is surfaced to callers or downstream systems.  
- Evidence links.

You can add a bullet list of envelope fields. For example:

- Request ID  
- Caller / tenant info  
- Policy / routing hints  
- Context / retrieval info  
- Completion status (success/error/timeout)  
- Result / output pointer

---

## 3.6 Template Fallback Modes, Session Lifecycle, and Global Controls

Explain:

- **Fallback modes** – how the pipeline responds when primary paths fail.  
- **Session lifecycle** – how start → continue → retry/reconnect → end is modeled.  
- **Global controls** – env flags, feature toggles, control‑plane knobs that affect behavior.

List key flags/controls as bullets. For example:

- `FLAG_A` – governs which backend is used.  
- `FLAG_B` – enables/disables a specific adapter.  
- `FLAG_C` – forces offline mode.

---

## 3.7 Template Assumptions & Guarantees

List:

- **Guarantees:** behaviors the pipeline always provides, with evidence.  
- **Assumptions:** conditions the pipeline relies on but does not enforce itself.

Example (adapt to your pipeline):

- Guarantees:
  - Every request is logged with a unique ID.
  - Retries reuse the same request ID and recorded history.
- Assumptions:
  - Upstream caller handles authentication.
  - External store enforces durability.

---

## <NN. Stage Walkthrough (Per‑Stage Sections)>

For each stage in the pipeline, copy this structure and adjust. Replace the placeholder
numbering (`<Stage N – Name>`) with sequential heading numbers once you know how many
stages exist. Lint tools expect the H2 numbering to be contiguous (no gaps between 4, 5,
6, …), so renumber the stage headings—and every subsequent top-level section—after the
stage list is finalized.

## <Stage N – Name>

> **Purpose:** One sentence describing what this stage does.

### Primary Path (e.g., Chat / Main Flow)

- **Overview / Summary**  
  Short paragraph explaining behavior at this stage on the primary path.
- **Inputs**  
  - Bullet list describing what enters this stage (envelope fields, flags, context, signals).  
- **Outputs / Downstream Dependencies**  
  - Bullet list describing what leaves this stage and where it goes next.  
- **Internal Systems (Tier‑1)**  
  - Bullet list naming the major components/services (no deep internals).  

### Secondary Path / Other Modalities (if applicable)

Mirror the above structure for other modalities (e.g., Voice, Batch, CLI).

### Status & Notes

- **Status:** `TODO | In Progress | Partial | Complete`.  
- **Known Gaps / Future Components:**  
  - Bullets describing missing behaviors or planned work.  
- **Evidence Links:**  
  - List of relevant code files, tests, and docs.  
- **Contradictions / Issues:**  
  - Any known inconsistencies with other sections.  
- **Notes for Future Passes:**  
  - What to revisit when new features land.

Repeat this pattern for every stage, renumbering the H2 headings (`## 5`, `## 6`, …)
sequentially when your stage inventory is locked in. Once stages are numbered, update
the remaining H2 sections (Snapshot, Contradiction Registry, Tier‑2 Index, Working Notes,
Update Log, etc.) so the document numbering stays continuous.

---

## <NN. Snapshot & Stage Matrix>

> Adjust numbering as needed. Replace `<NN>` (and `<NN.x>`) with the next contiguous
> numbers once the stage inventory is locked so lint tools see a continuous sequence.

### <NN.1 Pipeline Snapshot>

A short paragraph summarizing:

- Which stages are complete vs partial.  
- Key gaps (e.g., parity for certain transports).  
- Current high‑level risks or contradictions.

### <NN.2 Stage Matrix>

> Use the placeholders below as-is until you lock the stage count. Once the Stage
> Walkthrough headings are renumbered, update the Stage column (and any references in
> the Top Gap text) so this table mirrors the final numbering exactly. Each row must
> call out the Tier‑2/Tier‑3 evidence (docs/tests) that proves the stage status—either
> link them inline in the "Evidence" column or reference the Tier‑2 Index section, and
> replace the placeholder `docs/...` / `tests/...` strings with real file paths.

| Stage | Name | Paths Covered | Status | Top Gap | Evidence |
| --- | --- | --- | --- | --- | --- |
| `<Stage #>` | `<Stage Name>` | `HTTP, WebSocket` | `Complete` | `–` | `docs/...`, `tests/...` |
| `<Stage #>` | `<Stage Name>` | `Voice, Batch` | `Partial` | `Missing X for Y` | `docs/...`, `tests/...` |
| … | … | … | … | … | … |

Populate this table based on the hardened stage content after syncing with the Stage Walkthrough.

---

## <NN. Contradiction Registry>

| ID | Description | Sections Affected | Reality Source | Next Step |
| --- | --- | --- | --- | --- |
| CR‑001 | `<Description>` | `Stage N, Section X.Y` | `Code / Test / Doc` | `<Plan>` |

Only track **true contradictions** here (not normal gaps).

---

## <NN. Tier‑2 Document Index>

List the deeper docs for this pipeline:

- `docs/...` – architecture details.  
- `tests/...` – validation suites.  
- `docs/observability/...` – metrics/telemetry spec.  
- Any other major ADRs.

---

## <NN. Working / Future Notes>

Use this section for **future‑looking reminders only**—it is not an audit trail. Keep
the bullets actionable and reference the stage or section that will need revision.
For example:

- “When feature X lands, update Stage Y and the Stage Matrix row Z.”  
- “When transport W reaches parity, close CR‑00N and update Snapshot.”  
- “When telemetry Q is implemented, revise the Cross‑Cutting Concerns section.”

Once the document is frozen, this section should not contain missing content—only planned
follow‑ups. As soon as an item ships, add a row to **Section <NN. Update Log & Evidence
Tracking>** with the doc-index timestamp and regression suites before deleting or revising
the bullet here so Working Notes stays forward-looking.

---

## <NN. Update Log & Evidence Tracking>

Record every Tier‑1 doc edit here, including the doc-index run (which refreshes the
checkbox report) and any regression suites executed to validate the change. Populate
the **Author / Steward** column so auditors can trace who gathered the evidence. Do not
mark Tier‑1 stop-gates complete unless the evidence is captured in this table.

| Date | Author / Steward | Change | Doc-index timestamp | Regression suites |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | `<Name / Team>` | `<Summary of update>` | `<YYYY-MM-DDTHH:MM:SSZ doc-index run>` | ``pytest -q tests/...`` |

---

This template can be reused for any major pipeline in the Repo Studios project:

- Command Center pipeline,
- Doc validation pipeline,
- Report generation pipeline,
- Analysis aggregation pipeline,
- or any other BEGIN → END flow you want to document at Tier‑1.
