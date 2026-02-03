---
title: "Phase 1: Bootstrap + Setup"
tier: metaprompt
audience:
  - coding_agent
  - human_operator
phase: 1
checkpoints:
  - CHECKPOINT-0
  - CHECKPOINT-1
version: 1.0.0
updated_at: 2026-02-02
related_files:
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/BOOTSTRAP.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/common/review_metaprompts.md
  - .repo_studios/docs/pipeline/healthview_orchestration_pipeline/stage12_templates/producer/build_template.md
---

# PHASE 1: BOOTSTRAP + SETUP

> **HOP_ROOT:** `.repo_studios/docs/pipeline/healthview_orchestration_pipeline/`
>
> All paths in this document are relative to repository root unless noted.

---

## Purpose

Phase 1 initializes the inspection workflow. It discovers the script, creates the build document,
and captures the script's identity. This phase MUST complete before any analysis work begins.

**Why a separate phase?**
- Forces human verification of correct Record ID assignment
- Catches roster/working_docs conflicts early
- Prevents downstream errors from incorrect build doc setup

---

## SCOPE

This phase covers two prompts:

| Prompt | Purpose | Checkpoint |
|--------|---------|------------|
| PROMPT-00-BOOTSTRAP | Discover script, assign stage, create build doc | CHECKPOINT-0 |
| PROMPT-01-SETUP | Capture script identity, verify inputs | CHECKPOINT-1 |

**NOT in scope:** Analysis, gap detection, evidence capture, or external file updates.

---

## PREREQUISITES

Before starting Phase 1, you need:

| Requirement | Example |
|-------------|---------|
| Script path | `.repo_studios/scripts/producers/generate_anchor_inventory.py` |
| Repository access | Can read files, create folders |
| BOOTSTRAP.md loaded | `{HOP_ROOT}/stage12_templates/BOOTSTRAP.md` |

That's it. Phase 1 discovers everything else.

---

## DELIVERABLES

When Phase 1 completes, the following will exist:

| Artifact | Location |
|----------|----------|
| Build document | `{HOP_ROOT}/tier2_roster/working_docs/stage_{X_X}/{RECORD_ID}_{script_stem}_build.md` |
| Section 1 filled | Script identity captured in build doc |
| CHECKPOINT-0 signal | Emitted to confirm bootstrap complete |
| CHECKPOINT-1 signal | Emitted to confirm setup complete |

---

## INSTRUCTIONS

### Step 1: Load Required References

Read these files before proceeding:

```text
1. {HOP_ROOT}/stage12_templates/BOOTSTRAP.md
   → Full bootstrap algorithm (Steps 1-5)
   
2. {HOP_ROOT}/stage12_templates/common/review_metaprompts.md
   → PROMPT-01-SETUP section (for identity capture)
```

### Step 2: Execute BOOTSTRAP (PROMPT-00-BOOTSTRAP)

Follow BOOTSTRAP.md exactly:

1. **Validate** — Confirm script exists and is Python
2. **Classify** — Determine script class (producer/consumer/aggregator/orchestrator)
3. **Check existing** — Search working_docs for existing build doc
4. **Assign stage & ID:**
   - Match script to stage using `stage_prefix_index.yaml`
   - **CHECK ROSTER FIRST** (Step 4D) — Look for pre-existing assignment
   - If roster has assignment → USE THAT ID
   - If no roster entry → Generate next ID (Step 4E)
5. **Create build document** — Copy template, replace placeholders

**Output after Step 2:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-0: BOOTSTRAP COMPLETE
═══════════════════════════════════════════════════════════════════
BUILD_DOC_PATH: {full path to created build document}
RECORD_ID: {assigned ID, e.g., S21R-003}
SCRIPT_CLASS: {producer|consumer|aggregator|orchestrator}
TARGET_STAGE: {e.g., 2.1}
ID_SOURCE: {ROSTER_HIT|GENERATED}

BOOTSTRAP COMPLETE — Ready for PROMPT-01-SETUP
═══════════════════════════════════════════════════════════════════
```

### Step 3: Execute PROMPT-01-SETUP

Now capture the script's identity by following `review_metaprompts.md` → PROMPT-01-SETUP:

1. Open the script file at `SCRIPT_PATH`
2. Count total lines
3. Extract module docstring (first `"""..."""` block)
4. Fill **Section 1: Script Identity** in the build document:
   - Script name
   - Full path
   - Line count
   - Module docstring
   - Category (producer/consumer/aggregator/orchestrator)

**Output after Step 3:**

```text
═══════════════════════════════════════════════════════════════════
CHECKPOINT-1: SETUP COMPLETE
═══════════════════════════════════════════════════════════════════
SCRIPT_NAME: {e.g., generate_anchor_inventory.py}
LINE_COUNT: {e.g., 312}
DOCSTRING_CAPTURED: {yes|no}
SECTION_1_STATUS: FILLED

SETUP COMPLETE — Phase 1 finished
═══════════════════════════════════════════════════════════════════
```

---

## COMPLETION SIGNALS

Emit BOTH checkpoint signals before stopping:

```text
═══════════════════════════════════════════════════════════════════
PHASE 1 COMPLETE
═══════════════════════════════════════════════════════════════════
CHECKPOINT-0: BOOTSTRAP COMPLETE ✓
CHECKPOINT-1: SETUP COMPLETE ✓

Build Document: {BUILD_DOC_PATH}
Record ID: {RECORD_ID}
ID Source: {ROSTER_HIT|GENERATED}
Script Identity: Captured in Section 1

PHASE 1 DELIVERABLES READY — AWAITING HUMAN VERIFICATION
═══════════════════════════════════════════════════════════════════
```

---

## ════════════════════════════════════════════════════════════════
## STOP — AWAIT HUMAN VERIFICATION
## ════════════════════════════════════════════════════════════════

**DO NOT PROCEED TO PHASE 2.**

After emitting the completion signals above, **STOP** and wait for the human operator.

### What human will verify:

| Check | How to verify |
|-------|---------------|
| **Record ID correct** | If `ID_SOURCE: ROSTER_HIT` — confirm ID matches roster entry |
| | If `ID_SOURCE: GENERATED` — confirm script is NOT already in roster |
| **Build doc exists** | Open `BUILD_DOC_PATH` and confirm file was created |
| **Section 1 filled** | Verify script identity fields are populated (not placeholders) |
| **Correct stage** | Confirm `TARGET_STAGE` is appropriate for this script |

### Human decision:

| Outcome | Action |
|---------|--------|
| All checks pass | Human delivers Phase 2 prompt |
| Record ID conflict | Human resolves manually, then re-runs Phase 1 |
| Wrong stage assigned | Human updates stage, regenerates build doc |
| Build doc missing | Troubleshoot and re-run Phase 1 |

---

## Troubleshooting

### "ROSTER_HIT but ID seems wrong"

The roster is authoritative. If the roster says `S21R-003 = generate_anchor_inventory.py`,
that IS the correct ID. If you believe the roster is wrong, escalate to human — do NOT
override the roster assignment.

### "Build doc already exists"

BOOTSTRAP Step 3 handles this. Options:
- **(C)ontinue** — Resume existing inspection
- **(R)estart** — Delete existing and start fresh

### "No stage match found"

Script will be assigned to Stage 11.1 (ASR — Ad-hoc Scripts). Complete the inspection,
then request human reclassification if ASR is incorrect.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-02 | Initial phase extraction from monolithic workflow |
