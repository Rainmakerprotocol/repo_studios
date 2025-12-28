---
title: "How-To — Authoring Tier-2 Pipeline Documents"
tier: guidance
audience:
  - Copilot
  - Repo_Studios
  - Pipeline maintainers
owners:
  - Docs Guild
role:
  - How-To Guide
status: draft
version: v0.1.0
updated_at: 2025-12-11
tags:
  - pipeline
  - tier-2
  - templates
related_files:
  - .repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_template.md
  - <pending_progress>
  - <pending_progress>
  - <pending_progress>
  - <pending_progress>
---

<!-- markdownlint-disable-next-line MD025 -->
# How-To — Authoring Tier-2 Pipeline Documents

> This guide distills the structure, tone, and behavioral expectations observed in the
> Stage 2/3/6/7 Tier-2 docs and the telemetry-hybrid verticals. Use it with the
> `tier2_pipeline_template.md` file whenever you spin up a new vertical.

---

## 1. Goals

1. Provide a repeatable checklist for creating Tier-2 verticals that stay in sync with
   Tier-1 and Tier-3 artifacts.
1. Capture the formatting conventions demonstrated by real Tier-2 docs in other projects.
1. Reinforce telemetry/evidence expectations (doc-index refresh, checkbox gating,
   transport parity evidence) so every Tier-2 doc can flip Tier-1 stop-gates confidently.

---

## 2. Tier-2 Format Snapshot

| Section | Purpose | Evidence in Live Docs |
| --- | --- | --- |
| YAML Front Matter | Declares identity metadata (title, tier, audience, owners, status, tags, related_files). | Every existing Tier-2 file; aligns with `MD-L1` standard. |
| Instruction Block | Reminds editors of tier rules, telemetry obligations, and doc-index requirements. | Stage 2 transport + voice Stage 3 doc top sections. |
| Goals | Defines the measurable outcomes for the vertical. | All four LLM Tier-2 docs list numbered goals at the top. |
| System Context | Explains upstream/downstream alignment, Tier-3 dependencies, current coverage status. | Stage 2 "System Context" + telemetry-hybrid Decision Envelope doc. |
| Workstreams / Stage Narratives | Organizes work by substage or thematic workstream with scope/evidence/status/checklists. | `Stage 2.A/B/C`, `Workstream A–D`, `Model Selection Stages 1–7`. |
| Signals & Telemetry | Lists regression suites, telemetry endpoints, CLI harnesses required before closing work. | Voice Stage 3 "Signals & Evidence" block. |
| Dependencies & Stop-Gates | Summarizes Tier-1 checkboxes blocked, Tier-3 placeholders needed, rollout flags. | Stage 3 doc + Stage 7 Guardrail plan. |
| Agent Automation Block | YAML block for automated enforcement (section order, doc-index timestamps, tier alignment). | Stage 3 "Agent Automation" footer, telemetry-hybrid docs. |
| Update Log | Records doc-index timestamps, regression suites, authorship notes. | Present in every Tier-2/telemetry doc. |

---

## 3. Step-by-Step Authoring Workflow

### Step 1 — Duplicate the Template

1. Copy `.repo_studios/docs/pipeline/pipeline_templates/tier2_pipeline_template.md` into
   the target pipeline folder (for example,
   `.repo_studios/docs/pipeline/<pipeline_name>/tier2_<stage>_<topic>.md`).
1. Rename the file/title to match the Tier-1 stage (e.g., "Tier-2 Vertical — Stage 5
   Retrieval & Context Assembly").

### Step 2 — Update Front Matter

- Fill in `audience`, `owners`, `status`, `version`, `updated_at`, `tags`, and
  `related_files`. Include the Tier-1 spine plus any Tier-3 dependencies.
- Add any supporting ADRs or code paths under `related_files` so doc-index consumers
  can jump straight to evidence.

### Step 3 — Customize the Instruction Block

- Explicitly state which Tier-1 stage and transports are covered.
- Document required regression suites (copy from existing Tier-2 docs or analysis
  plans as references).
- Remind editors to refresh the doc-index (via make target or platform-equivalent) and
  capture the timestamp in the Update Log.

### Step 4 — Define Goals & System Context

- Write 3–5 numbered goals that include implementation and telemetry commitments
  (mirroring existing Tier-2 docs).
- Under **Stage Alignment**, cite the upstream/downstream stages plus Tier-3 horizontals
  (e.g., `tier3_prune_logs.yaml`, `tier3_cli.yaml`). Note: Tier-3 uses YAML format for
  agent tool calling.
- Populate a **Coverage Snapshot** table. Use `TODO/In Progress/Partial/Complete`
  statuses for each modality.

### Step 5 — Lay Out Workstreams or Substages

- If the work is sequential, keep numbered `Stage X.Y` sections with
  Scope/Evidence/Status + `[ ]` checklists.
- If the work is thematic, title each workstream and include implementation checkpoints
  with evidence + test/doc-index reminders.
- Always cite concrete files/tests per checkpoint (`.repo_studios/scripts/...`,
  `tests/...`).

### Step 6 — Capture Signals, Dependencies, and Automation

- Under **Signals & Telemetry**, list regression suites, telemetry endpoints, and manual
  harnesses.
- Add a **Dependencies & Stop-Gates** section summarizing Tier-1 checkboxes blocked,
  Tier-3 placeholders required, and rollout flags.
- Keep the **Agent Automation Block** (YAML inside `<!-- agents:begin ... -->`) and
  update the task IDs/titles if the vertical needs extra enforcement.

### Step 7 — Maintain the Update Log

- Every edit must append a row with date, summary, author, doc-index timestamp, and
  relevant regression suites.
- If a checklist flips from `[ ]` to `[x]`, ensure the Update Log references the
  doc-index run triggered afterward.

---

## 4. Behavior Expectations

1. **Telemetry linkage:** Any mention of telemetry/history/correlation work must cite
   the matching plan or implementation file.
1. **Doc-index discipline:** Refresh the doc-index (via the `doc-index` make target or
   platform-equivalent command) after edits and paste the timestamp into the Update Log.
1. **Evidence-first checklists:** Each `[ ]` item should cite concrete files—
   "`.repo_studios/scripts/producers/...` emits metrics—run `pytest -q tests/...` and
   refresh doc-index before marking complete."
1. **Transport parity tables:** Use tables when multiple transports need coverage.
1. **Agent automation:** Keep YAML agent blocks so automation can enforce deliverables,
   especially doc-index timestamps and Tier-3 dependency declarations.
1. **Stop-gate mirroring:** When a Tier-2 doc changes status, immediately mirror that
   status in the Tier-1 stage section (per Tier instructions) and note the sync in the
   Update Log.

---

## 5. Quick Reference Checklist

- [ ] Duplicate `tier2_pipeline_template.md` and rename appropriately.
- [ ] Replace front-matter placeholders with real metadata and Tier references.
- [ ] Update the Instruction Block with stage-specific editing guidance.
- [ ] Populate Goals, System Context, and Coverage Snapshot tables.
- [ ] Define workstreams/stage narratives with evidence-backed checklists.
- [ ] List regression suites, telemetry endpoints, and manual harnesses.
- [ ] Record Tier-1 stop-gates, Tier-3 dependencies, and feature flags.
- [ ] Embed/update the agent automation block.
- [ ] Refresh the doc-index (via the `doc-index` make target or platform-equivalent
  command) and log the timestamp.
- [ ] Cross-link the new doc from Tier-1 and any relevant Tier-3 horizontals.

---

## 6. Update Log

| Date | Change | Author | Notes |
| --- | --- | --- | --- |
| 2025-12-11 | Initial how-to created | Copilot | Derived from Stage 2/3/6/7 Tier-2 docs and telemetry hybrid plans |
