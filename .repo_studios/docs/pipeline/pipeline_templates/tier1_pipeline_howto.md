# Tier‑1 Pipeline Document – How‑To Guide

This guide captures the process for building and hardening **Tier‑1 pipeline documents** in Repo Studios. It is a **repeatable playbook** for any future Tier‑1 pipeline doc (for example: command center pipeline, doc validation pipeline, report generation pipeline, etc.).

It is **not** about AI agents talking to each other. It is a human‑oriented method: what to do, in what order, and what each pass is for.

---

## 1. What a Tier‑1 Pipeline Document Is

A Tier‑1 pipeline document is the **canonical, system‑level map** of a single pipeline:

* It describes **what** happens, **in what order**.
* It focuses on **stages**, shared **spines**, and shared **envelopes**, not function bodies.
* It links to real code, tests, and ADRs as evidence.
* It is the primary reference for:
  * new developers,
  * AI assistants (Copilot, GitHub Copilot, Repo Studios agents),
  * and design decisions.

Tier‑1 is **architecture narrative plus evidence**, not implementation detail.

---

## 2. Overall Process – Phases

The work breaks down into **four main phases**:

1. **Phase 0 – Seeding**  
2. **Phase 1 – Structure & Global Concepts**  
3. **Phase 2 – Stage‑by‑Stage Hardening**  
4. **Phase 3 – Consolidation & Freeze**  

Each phase has a clear purpose and its own passes.

---

## 3. Phase 0 – Seeding the Document

### Goal

Get a **first, complete skeleton** of the pipeline from BEGIN → END.

### Steps

1. **Name the pipeline** and create a `.md` file for it.
2. Add high‑level sections:
   * Instruction block (how this doc should be edited).
   * 5W1H (Who, What, Why, Where, When, How).
   * Metadata (version, last updated, owner, status).
   * Update Log & Evidence Tracking stub (blank table ready for future doc-index timestamps + regression suites).
3. Draft a **Global Overview**:
   * A short narrative of the full pipeline (input → system → output).
   * A numbered list of high‑level stages.
4. For each stage, add an H2 placeholder:
   * `## <Stage N – Name>` while the inventory is still fluid.
   * Under it, add a **standard sub-structure** (see template file).
   * Once the stage list is locked, renumber every H2 (stages and the downstream `<NN.` sections) so the document has a continuous numeric spine.
5. Don’t chase perfection in Phase 0; focus on **coverage and order**.

Result: a **rough but complete** BEGIN → END skeleton.

---

## 4. Phase 1 – Structure & Global Concepts

### Goal

Turn the rough skeleton into a **coherent Tier‑1 structure** with shared concepts and anchors.

### Typical Global Concepts

Most pipelines benefit from three global H2 sections:

1. A **Spine** – shared backbone that all flows use  
   (e.g., History & Retry Spine, Job Lifecycle Spine).
2. An **Envelope** – shared payload structure  
   (e.g., Inference Envelope, Job Envelope).
3. **Fallback / Sessions / Global Controls** – how resilience, lifecycle, and flags influence the pipeline.

### Steps

1. Insert global H2 sections **before** the stage walkthrough:
   * Spine, Envelope, Fallback/Sessions/Controls.
2. Define each in 2–4 short paragraphs:
   * What it is.
   * Which components participate.
   * How it ties into BEGIN → END.
   * Which code/tests/docs are evidence.
3. Add a brief **“How to Read This Document”** section:
   * Explain the reading order (context → globals → stages → snapshot/matrix).
4. Add two global roll-ups near the bottom (they use the `<NN.` placeholder numbering until you finalize the stage list):
   * **Pipeline Snapshot** – a paragraph summarizing stage status.
   * **Stage Matrix** – a table listing stage, paths covered, status, top gap, and an **Evidence** column that links to the Tier-2/Tier-3 docs or tests validating each row.
5. Add a **Contradiction Registry** for cross‑stage inconsistencies.
6. Add a **Working / Future Notes** section at the end (used as scratch space during hardening).

Result: a **Tier‑1 scaffold** with shared language and global anchors.

---

## 5. Phase 2 – Stage‑by‑Stage Hardening (Pass A/B/C)

Phase 2 is where each stage is brought into alignment with **real code and tests**.

For each stage you run the same three mini‑passes:

### 5.1 Pass A – Evidence Scan

For the current stage:

* Scan the relevant:
  * python files,
  * tests,
  * ADRs / design docs,
  * metrics / observability docs.
* List what you see:
  * behaviors the stage is missing,
  * mismatches between doc and code,
  * details that belong at Tier‑1,
  * anything that looks inconsistent.

**No edits yet.** Just gather reality.

### 5.2 Pass B – Tier‑1 Update

Using the Pass A findings:

* Adjust the stage’s **Overview / Inputs / Outputs / Notes**.
* Keep changes **small and scoped** to that stage.
* Ensure everything you add is **evidence‑backed**.
* Keep the stage format/template intact.
* Link to the right code + tests.

You are not rewriting the stage; you are **aligning it with the repo**.

### 5.3 Pass C – Local Polish

After the content is correct:

* Smooth the wording.
* Make sure the stage:
  * mentions the spine/envelope where appropriate,
  * references global controls (fallback/session/flags) if needed,
  * transitions cleanly from the prior stage and into the next.
* Remove small redundancies inside the stage.

Then move to the **next stage** and repeat A → B → C.

Result: every stage is **accurate, consistent, and cross‑linked**.

---

## 6. Phase 3 – Consolidation & Freeze

Once all stages are hardened, Phase 3 brings the entire document into a **final, stable state**.

Use **three full‑document passes**:

### 6.1 Pass A – Continuity & Structure Check

* Read the file top‑to‑bottom and note:
  * incorrect stage references,
  * broken transitions,
  * missing or incorrect cross‑references to global sections,
  * Stage Matrix vs. prose mismatches,
  * outdated contradictions,
  * formatting/heading inconsistencies.
* Do **not** edit yet; just list the issues.

### 6.2 Pass B – Corrections & Tone Polish

Apply small, surgical edits:

* Fix stage‑number references and cross‑links.
* Correct Stage Matrix and Snapshot to match hardened content.
* Replace any remaining `<NN.` placeholders with contiguous heading numbers once the stage inventory is final.
* Normalize headings and subheadings.
* Update Contradiction Registry to reflect current truth.
* Clean up minor phrasing issues and redundancies.

Keep everything **local and Tier‑1**. No structural rewrites.

### 6.3 Pass C – Freeze & Readiness

Final pass:

* Confirm all cross‑references resolve cleanly.
* Confirm global sections and Stage Matrix align with stage content.
* Confirm Contradiction Registry is accurate.
* Trim the Working Notes section down to **future‑looking reminders only**.
* Make only tiny clause‑level edits if needed.

At the end of Pass C, **freeze the document** as the canonical Tier‑1 reference for that pipeline.

### 6.4 Evidence Logging & Update Log

When Pass C is complete (or whenever you make a substantive Tier‑1 edit):

1. Refresh the doc-index (via the `doc-index` make target or platform-equivalent command) so the checkbox report reflects the latest headings.
2. Execute any regression suites that validate the change set.
3. Add a row to **Section `<NN. Update Log & Evidence Tracking>`** capturing:
   * the date,
   * the author/steward,
   * a short description of the change,
   * the doc-index timestamp,
   * and the regression suites you ran.

That table is the audit trail—do not mark a pass “done” until its evidence is recorded there.

---

## 7. Working Notes Section – How to Use It Safely

During early passes, a “Working Notes”/“Conversation Notes” section is useful to park:

* insights,
* TODOs,
* open questions,
* patterns observed in code/tests.

Rules:

* Do **not** treat it as permanent storage.  
* After hardening and consolidation, either:
   * fold relevant notes into the right sections, or
   * reduce the section to a few **future reminders only**—and whenever you resolve a bullet, log the evidence in Section `<NN. Update Log & Evidence Tracking>` before deleting it here.

A frozen Tier‑1 doc should **not** rely on Working Notes for required content.

---

## 8. Using This Process for New Tier‑1 Docs

1. Copy the Tier‑1 template (see `tier1_pipeline_template.md`).
2. Fill Phase 0 (skeleton) quickly, from BEGIN → END.
3. Add global sections and Stage Matrix (Phase 1).
4. Do Stage‑by‑Stage hardening using Pass A/B/C per stage (Phase 2).
5. Run the three whole‑doc passes (Phase 3) until the doc is coherent, accurate, and stable.
6. Freeze the document and treat it as the **canonical Tier‑1 map** of that pipeline.

This same process can be used for any major pipeline in Repo Studios:

* Command Center pipeline  
* Doc validation pipeline  
* Report generation pipeline  
* Analysis aggregation pipeline  
* <pending_progress>  
* <pending_progress>  

This file is the **how‑to**. The template file is your **starting point**.

Likely Tier-1 Pipelines in Repo Studios

You could reasonably have a Tier-1 doc for each of these:

1. **Command Center Pipeline**
   - Script inventory → analysis → duplicate scan → report generation
   - Producer/consumer/aggregator/orchestrator/summarizer coordination
   - Artifact management, pruning, and retention

2. **Doc Validation Pipeline**
   - Markdown scanning → checkbox detection → integrity checks → report output
   - Doc-index generation and refresh cycles
   - Cross-reference validation and broken link detection

3. **<pending_progress>**

4. **<pending_progress>**

5. **<pending_progress>**

6. **<pending_progress>**

You could also split some of these further, but a reasonable first wave is ~4–6 Tier-1 pipelines total.

That's enough to cover the major flows without fragmenting too much.
